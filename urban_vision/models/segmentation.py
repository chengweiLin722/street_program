import torch
import numpy as np
from PIL import Image
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation

class SegformerB2Cityscapes:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print("[SegFormer-B2] device:", self.device)

        # 載入 NVIDIA 官方 Cityscapes SegFormer-B2
        self.processor = SegformerImageProcessor.from_pretrained(
            "nvidia/segformer-b2-finetuned-cityscapes-1024-1024"
        )
        self.model = SegformerForSemanticSegmentation.from_pretrained(
            "nvidia/segformer-b2-finetuned-cityscapes-1024-1024"
        ).to(self.device)

        # Cityscapes 19 類 mapping
        self.id2label = self.model.config.id2label

    @torch.no_grad()
    def segment(self, image: Image.Image) -> np.ndarray:
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        outputs = self.model(**inputs)
        logits = outputs.logits  # (1, 19, H/4, W/4)

        # 上採樣回原始大小
        upsampled = torch.nn.functional.interpolate(
            logits,
            size=image.size[::-1],
            mode="bilinear",
            align_corners=False
        )

        mask = upsampled.argmax(dim=1)[0].cpu().numpy()
        return mask
