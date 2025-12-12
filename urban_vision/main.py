import sqlite3
import os
from PIL import Image
import requests
from io import BytesIO
import numpy as np

from models.segmentation import SegformerB2Cityscapes
from models.classification import SceneClassifier
from models.vlm_qwen import SidewalkQwenVLM
from utils.visualize import visualize_segmentation
from utils.analyze_sidewalk import sidewalk_confidence

DB_PATH = r"C:\Homework\urban_vision\streetview.db"
IMAGE_OUTPUT_DIR = r"C:\Homework\urban_vision\output"

ANGLES = ["0", "90", "180", "270"]


# 產出路徑，如果路徑不存在就建立
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

def load_image_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"❌ 無法讀取圖片 URL: {url}")
        print("原因:", e)
        return None


def load_unprocessed_points():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT *
        FROM streetview_points
        WHERE processed = 0
    """).fetchall()

    conn.close()
    return rows


def update_point_to_db(pid, angle, scene, sidewalk, score, raw_path, seg_path):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(f"""
        UPDATE streetview_points
        SET 
            scene{angle} = ?,
            sidewalk{angle} = ?,
            score{angle} = ?,
            img{angle} = ?,
            seg{angle} = ?
        WHERE id = ?
    """, (scene, sidewalk, score, raw_path, seg_path, pid))

    conn.commit()
    conn.close()

def update_vlm_to_db(pid, vlm_result):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE streetview_points
        SET 
            vlm_sidewalk = ?,
            vlm_scene_type = ?,
            vlm_confidence = ?,
            vlm_reason = ?
        WHERE id = ?
    """, (
        vlm_result["sidewalk_exists"],
        vlm_result["scene_type"],
        vlm_result["sidewalk_confidence"],
        vlm_result["reason"],
        pid
    ))

    conn.commit()
    conn.close()


def mark_processed(pid):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE streetview_points
        SET processed = 1
        WHERE id = ?
    """, (pid,))

    conn.commit()
    conn.close()


def process_point(row, seg_model, cls_model, vlm_model):
    pid = row["id"]
    print(f"\n⚡ 正在處理 point id={pid}")

    scores = {}   # <--- 新增，用來存每張角度的分數

    for angle in ANGLES:

        raw_url = row[f"img{angle}"]
        if not raw_url:
            print(f" - angle {angle}: 沒有圖片 URL，跳過")
            continue

        image = load_image_from_url(raw_url)
        if image is None:
            continue

        # Scene 分類
        scene = cls_model.classify(image)

        # 分割
        mask = seg_model.segment(image)

        # Sidewalk mask
        has_sidewalk, score, debug = sidewalk_confidence(mask, image)

        scores[angle] = score   # <--- 新增

        print(f" - angle={angle}, scene={scene}, sidewalk={has_sidewalk}, score={score:.4f}")

        # ========== 儲存圖片 ==========
        raw_output = os.path.join(IMAGE_OUTPUT_DIR, f"{pid}_raw_{angle}.png")
        seg_output = os.path.join(IMAGE_OUTPUT_DIR, f"{pid}_seg_{angle}.png")

        image.save(raw_output)
        vis = visualize_segmentation(image, mask, scene, seg_output, alpha=0.5)

        update_point_to_db(
            pid,
            angle,
            scene,
            has_sidewalk,
            float(score),
            raw_output,
            seg_output
        )


    print("🧠 使用 Qwen-VL 進行四視角語義判斷 ...")

    # 根據 sidewalk score 排序圖片
    sorted_angles = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    print(f"📸 排序後圖片順序（高→低）： {sorted_angles}")

    image_paths = []
    for angle in sorted_angles:
        raw_output = os.path.join(IMAGE_OUTPUT_DIR, f"{pid}_raw_{angle}.png")
        image_paths.append(raw_output if os.path.exists(raw_output) else None)

    # 呼叫 VLM
    vlm_result = vlm_model.evaluate_images(image_paths)
    print("   VLM 結果：", vlm_result)

    update_vlm_to_db(pid, vlm_result)
    mark_processed(pid)




def main():
    print("📌 載入模型中 ...")
    seg_model = SegformerB2Cityscapes()
    cls_model = SceneClassifier()
    vlm_model = SidewalkQwenVLM()


    points = load_unprocessed_points()
    print(f"📌 一共找到 {len(points)} 個未處理座標點")

    for row in points:
        process_point(row, seg_model, cls_model, vlm_model)

    print("\n🎉 全部處理完成！")


if __name__ == "__main__":
    main()
