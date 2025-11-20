import numpy as np
import cv2

SIDEWALK = 1
ROAD = 0

def sidewalk_confidence(mask,
                        min_component=80,
                        large_component_ref=5000,
                        adjacency_ref=300,
                        bottom_ref=0.02,
                        ratio_ref=0.02):
    """
    回傳：
    (score: float 0~1,
     has_sidewalk: bool,
     debug: dict)
    """

    mask_np = np.array(mask)
    h, w = mask_np.shape

    sidewalk_mask = (mask_np == SIDEWALK).astype(np.uint8)
    road_mask = (mask_np == ROAD).astype(np.uint8)

    debug = {}

    # -----------------------------------------
    # Connected Components
    # -----------------------------------------
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(sidewalk_mask)

    largest_component = 0
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area > largest_component:
            largest_component = area

    large_component_score = min(largest_component / large_component_ref, 1.0)
    debug["largest_component"] = largest_component
    debug["large_component_score"] = large_component_score

    # -----------------------------------------
    # Adjacency with Road
    # -----------------------------------------
    kernel = np.ones((7, 7), np.uint8)
    road_dilated = cv2.dilate(road_mask, kernel, iterations=2)

    touching_pixels = np.logical_and(road_dilated, sidewalk_mask).sum()
    adjacency_score = min(touching_pixels / adjacency_ref, 1.0)
    debug["touching_pixels"] = touching_pixels
    debug["adjacency_score"] = adjacency_score

    # -----------------------------------------
    # Bottom Region
    # -----------------------------------------
    bottom = mask_np[int(h * 0.6):, :]
    bottom_ratio = np.mean(bottom == SIDEWALK)
    bottom_score = min(bottom_ratio / bottom_ref, 1.0)
    debug["bottom_ratio"] = bottom_ratio
    debug["bottom_score"] = bottom_score

    # -----------------------------------------
    # Cleaned Ratio (remove small components)
    # -----------------------------------------
    cleaned = sidewalk_mask.copy()
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] < min_component:
            cleaned[labels == i] = 0

    cleaned_ratio = cleaned.sum() / (h * w)
    ratio_score = min(cleaned_ratio / ratio_ref, 1.0)
    debug["cleaned_ratio"] = cleaned_ratio
    debug["ratio_score"] = ratio_score

    # -----------------------------------------
    # Weighted Confidence Score
    # -----------------------------------------
    score = (
        large_component_score * 0.35 +
        adjacency_score        * 0.30 +
        bottom_score           * 0.20 +
        ratio_score            * 0.15
    )

    score = float(score)
    debug["final_score"] = score

    # Sidewalk 判定（可調）
    has_sidewalk = (score >= 0.7)

    return has_sidewalk, score, debug
