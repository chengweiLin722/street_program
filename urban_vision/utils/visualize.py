import numpy as np
from PIL import Image
from scipy.ndimage import label, find_objects
from PIL import ImageDraw, ImageFont
import os

# ======== 類別 ID 與名稱對應 ========
CLASS_ID_MAP = {
    0: "road",
    1: "sidewalk",
    2: "building",
    3: "wall",
    4: "fence",
    5: "pole",
    6: "traffic light",
    7: "traffic sign",
    8: "vegetation",
    9: "terrain",
    10: "sky",
    11: "person",
    12: "rider",
    13: "car",
    14: "truck",
    15: "bus",
    16: "train",
    17: "motorcycle",
    18: "bicycle"
}

# ======== 固定顏色設定 ========
FIXED_CLASS_COLORS = {
    "road": (128, 64, 128),
    "sidewalk": (244, 35, 232),
    "building": (70, 70, 70),
    "wall": (102, 102, 156),
    "fence": (190, 153, 153),
    "pole": (153, 153, 153),
    "traffic light": (250, 170, 30),
    "traffic sign": (220, 220, 0),
    "vegetation": (107, 142, 35),
    "terrain": (152, 251, 152),
    "sky": (70, 130, 180),
    "person": (220, 20, 60),
    "rider": (255, 0, 0),
    "car": (0, 0, 142),
    "truck": (0, 0, 70),
    "bus": (0, 60, 100),
    "train": (0, 80, 100),
    "motorcycle": (0, 0, 230),
    "bicycle": (119, 11, 32),
}

def has_sidewalk(mask, threshold=0.01):
    sidewalk_area = np.sum(mask == 1) / mask.size
    return sidewalk_area > threshold

def visualize_segmentation(image, mask, scene_type, output_path, alpha=0.5):

    # --- 1. 保證 image 是 PIL ---
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image.astype(np.uint8))
    image = image.convert("RGB")

    # --- 2. 保證 mask 與 image 尺寸一致（關鍵） ---
    mask = np.array(Image.fromarray(mask.astype(np.uint8)).resize(
        (image.width, image.height),
        resample=Image.NEAREST
    ))

    # --- 3. 建立彩色 mask ---
    mask_colored = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)

    for class_id, class_name in CLASS_ID_MAP.items():
        color = FIXED_CLASS_COLORS.get(class_name, (255, 255, 255))
        mask_colored[mask == class_id] = color

    # --- 4. 套疊 ---
    overlay = Image.blend(
        image,
        Image.fromarray(mask_colored),
        alpha=float(alpha)
    )

    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    # --- 5. 場景分類 ---
    draw.text((10, 10), f"Scene: {scene_type}", fill=(0,0,0), font=font)

    if np.sum(mask == 1) != 0:
        sidewalk_ratio_val = np.sum(mask == 1) / mask.size
        draw.text(
            (10, 40),
            f"Sidewalk ratio: {sidewalk_ratio_val * 100:.2f}%",
            fill=(0, 0, 0),
            font=font
        )
    else:
        draw.text(
            (10, 40),
            "Sidewalk ratio: 0%",
            fill=(0, 0, 0),
            font=font
        )



    overlay.save(output_path)
    print(f"[完成] 已輸出 {output_path}")
