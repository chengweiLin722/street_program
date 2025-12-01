# vlm_qwen.py

import json
import re
from typing import List, Dict, Any
from PIL import Image


import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

class SidewalkQwenVLM:

    def __init__(self, model_name: str = "Qwen/Qwen2.5-VL-3B-Instruct"):
        print(f"🧠 載入模型：{model_name}")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.processor = AutoProcessor.from_pretrained(
            model_name,
            use_fast=False,
        )

        # 建議先用 bfloat16（3070 支援），若有問題就改成 float32
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
        ).to("cuda")

        # 🔒 關掉預設 sampling
        gen_cfg = self.model.generation_config
        gen_cfg.do_sample = False
        gen_cfg.temperature = 0.0
        gen_cfg.top_p = 1.0
        gen_cfg.top_k = 50

        print(next(self.model.parameters()).device)
        print("✔ Model loaded on", self.device)


    def _build_prompt(self) -> str:
        prompt = """
You will receive four images of the same location from different angles and must judge them collectively as one continuous scene.

Determine if a physically separated pedestrian walkway exists.

Rules:
- Base judgment strictly on visible features.
- Look only for physical separation such as height change, curb, edge boundary, or clearly different pavement.
- Do not infer intent or usage.

Decision:
- true → clear separation visible
- false → ground visually continuous with road
- uncertain → insufficient visual proof

sidewalk_confidence represents how visually strong the separation evidence is:
- high (0.8–1.0) when separation is clearly visible
- mid (0.4–0.7) when ambiguous
- low (0–0.3) when unclear or obstructed

If unsure, prefer "false" over "true".

You must output only one JSON object with:
- sidewalk_exists: true, false, or "uncertain"  
- scene_type: "sidewalk", "road", "indoors", "trail", or "other"  
- sidewalk_confidence: 0–1  
- reason: refer to specific visible properties (ex: edge line, elevation discontinuity, barrier presence)
"""
        return prompt.strip()


    def _extract_json(self, text: str) -> Dict[str, Any]:
        try:
            # 去掉 markdown code fence
            text = text.replace("```json", "").replace("```", "")

            # 找出 JSON 區塊
            match = re.search(r"\{[\s\S]*?\}", text)
            if not match:
                raise ValueError("無 JSON 區塊")

            json_text = match.group(0).strip()

            return json.loads(json_text)

        except Exception as e:
            return {
                "sidewalk_exists": "uncertain",
                "scene_type": "other",
                "sideawalk_confidence": 0,
                "reason": f"JSON解析失敗: {text}"
            }



    def evaluate_images(self, image_paths: List[str]) -> Dict[str, Any]:
        images = []
        for p in image_paths:
            if p:
                try:
                    images.append(Image.open(p).convert("RGB"))
                except:
                    pass

        if not images:
            return {
                "sidewalk_exists": None,
                "scene_type": "other",
                "sidewalk_confidence": 0.0,
                "reason": "沒有可用圖片",
            }

        prompt = self._build_prompt()

        messages = [
            {
                "role": "user",
                "content": [
                    *[{"type": "image"} for _ in images],
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        model_inputs = self.processor(
            text=[text],
            images=images,
            return_tensors="pt"
        )
        model_inputs = {k: v.to("cuda") for k, v in model_inputs.items()}

        with torch.no_grad():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=256,   # 先縮短一點，避免沒必要的長輸出
                do_sample=False,      # 🔒 再次強制關掉 sampling
                temperature=0.0,
                top_p=None,
                top_k=None,
            )



        output_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]

        try:
            return self._extract_json(output_text)
        except:
            return {
                "sidewalk_exists": None,
                "scene_type": "other",
                "sidewalk_confidence": 0.0,
                "reason": f"解析錯誤: {output_text}",
            }
