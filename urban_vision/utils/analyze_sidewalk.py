import numpy as np
import cv2

SIDEWALK = 1
ROAD = 0

def sidewalk_confidence(mask, image,
                        min_component=80,
                        large_component_ref=5000,
                        ratio_ref=0.02,
                        bottom_ref=0.02,
                        min_ratio=0.005,     # 0.5%
                        max_ratio=0.05):    # 5%
    """
    改進後邏輯：
    1. 若人行道面積占比 == 0 → 直接回傳 0
    2. 若比例 < min_ratio → 很可能是誤判 → 直接回傳低分
    3. 若 min_ratio <= ratio <= max_ratio → 進入完整評估流程
    """

    mask_np = np.array(mask)
    img_np = np.array(image)
    h, w = mask_np.shape

    debug = {}

    # ==========================================================
    # (0) 基礎比例偵測
    # ==========================================================
    sidewalk_mask = (mask_np == SIDEWALK).astype(np.uint8)
    ratio = sidewalk_mask.mean()
    debug["raw_ratio"] = ratio

    # 0% → 直接回傳零
    if ratio == 0: 
        return False, 0.0, debug

    # 比例太低 → 模型通常把 fence / curb / planter 當作 sidewalk
    if ratio < min_ratio:
        debug["early_exit"] = "ratio < min_ratio"
        return False, float(ratio / min_ratio * 0.2), debug  # 最多給 0.2 的分數

    # ==========================================================
    # (1) Connected Components（決定是否為有效人行道）
    # ==========================================================
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(sidewalk_mask)

    largest_component = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > largest_component:
            largest_component = area

    largest_component_score = min(largest_component / large_component_ref, 1.0)
    debug["largest_component_score"] = largest_component_score

    # ==========================================================
    # (2) Texture Score（檢查質地是否像地面）
    # ==========================================================
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    texture = cv2.Laplacian(gray, cv2.CV_64F)
    texture_var = texture.var()

    texture_score = min(texture_var / 2000, 1.0)
    debug["texture_score"] = texture_score

    # ==========================================================
    # (3) 邊界偵測（人行道通常有平行邊界）
    # ==========================================================
    edges = cv2.Canny(gray, 60, 120)
    lines = cv2.HoughLines(edges, 1, np.pi/180, 60)

    parallel_count = 0
    if lines is not None:
        for line in lines:
            try:
                r, theta = line[0]
                if abs(theta - np.pi/2) < (np.pi/36):
                    parallel_count += 1
            except:
                continue

    boundary_edge_score = min(parallel_count / 10, 1.0)
    debug["boundary_edge_score"] = boundary_edge_score

    # ==========================================================
    # (4) Bottom Score（底部是關鍵）
    # ==========================================================
    bottom = mask_np[int(h * 0.65):, :]
    bottom_ratio = np.mean(bottom == SIDEWALK)
    bottom_score = min(bottom_ratio / bottom_ref, 1.0)
    debug["bottom_score"] = bottom_score

    # ==========================================================
    # (5) Width Continuity（人行道需連續寬度）
    # ==========================================================
    col_sum = np.sum(sidewalk_mask, axis=0)
    width_continuity = np.max(col_sum) / h
    width_continuity_score = min(width_continuity / 0.10, 1.0)
    debug["width_continuity_score"] = width_continuity_score

    # ==========================================================
    # FINAL SCORE（重新分配權重；bottom 提高）
    # ==========================================================
    score = (
        bottom_score            * 0.35 +   # ⬆ 強調底部人行道的重要性
        largest_component_score * 0.25 +
        width_continuity_score  * 0.20 +
        texture_score           * 0.10 +
        boundary_edge_score     * 0.10
    )

    score = float(score)
    debug["final_score"] = score
    debug["ratio_stage"] = "full_evaluation"

    has_sidewalk = (score > 0.60)

    return has_sidewalk, score, debug
