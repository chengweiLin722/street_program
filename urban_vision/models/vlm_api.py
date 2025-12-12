import base64
import requests
import json
import os

class SidewalkVLM_API:
    def __init__(self, model_name, hf_token):
        self.model_name = model_name
        self.token = hf_token
        self.api_url = "https://router.huggingface.co"

    # 移除 encode_image，改用 open_image 傳回二進位資料
    def open_image(self, path):
        """開啟圖片並傳回二進位資料"""
        try:
            with open(path, "rb") as f:
                return f.read()
        except IOError as e:
            print(f"❌ 無法讀取圖片檔案 {path}: {e}")
            return None

    # 將方法名稱從 evaluate_images 改為 evaluate_image
    # 並且只接受單張圖片路徑 (image_path)
    def evaluate_images(self, image_path, prompt):
        # 檢查圖片路徑
        if not image_path or not os.path.exists(image_path):
            return {
                "sidewalk_exists": "error",
                "reason": "Image file not found or path is empty."
            }

        # 讀取圖片的二進位資料
        image_bytes = self.open_image(image_path)
        if image_bytes is None:
            return {
                "sidewalk_exists": "error",
                "reason": "Failed to read image bytes."
            }

        try:
            # 1. 設定 Headers
            # Content-Type 會由 requests.post 處理 multipart/form-data 時自動設定
            headers = {
                "Authorization": f"Bearer {self.token}",
            }
            
            # 2. 設定 Payload - 圖片作為 files 參數
            files = {
                # Hugging Face API 接受的圖片欄位名稱通常為 "image" 或任意
                'image': ('image_file', image_bytes, 'image/jpeg') 
            }
            
            # 3. 設定 Payload - 文字提示作為 data 參數
            # 提示應作為 JSON 字串發送，或者直接傳送文字，視模型而定。
            # 這裡使用最通用的方式：將 prompt 放在 'text' 欄位中
            data = {
                "text": prompt
            }

            response = requests.post(
                self.api_url, 
                headers=headers, 
                files=files, # 傳送圖片
                data=data,   # 傳送文字
                timeout=120
            )

            print("\n=== RAW RESPONSE ===\n", response.text, "\n")

            # 檢查 HTTP 狀態碼
            response.raise_for_status()
            
            data = response.json()

            # Hugging Face VLM API 回應通常是一個清單，包含一個字典
            if isinstance(data, list) and len(data) > 0 and 'generated_text' in data[0]:
                result_text = data[0]["generated_text"]
                return self.parse_vlm_output(result_text)
            else:
                 # 處理 API 回傳非預期格式的情況，例如錯誤訊息
                 return {
                    "sidewalk_exists": "uncertain",
                    "reason": f"API response format error or empty: {data}"
                }


        except requests.exceptions.RequestException as req_e:
            print(f"❌ VLM Request exception: {req_e}")
            return {
                "sidewalk_exists": "uncertain",
                "scene_type": "other",
                "sidewalk_confidence": 0.0,
                "reason": f"VLM Request exception: {req_e}"
            }
        except Exception as e:
            print(f"❌ VLM general exception: {e}")
            return {
                "sidewalk_exists": "uncertain",
                "scene_type": "other",
                "sidewalk_confidence": 0.0,
                "reason": f"VLM general exception: {e}"
            }

    def parse_vlm_output(self, text):
        # 保持此方法不變，用於解析模型輸出的 JSON 字串
        try:
            # 假設 VLM 會輸出一個 JSON 字串，例如：Some text {"key": "value"}
            start = text.find("{")
            end = text.rfind("}") + 1
            json_str = text[start:end]
            return json.loads(json_str)
        except:
            return {
                "sidewalk_exists": "uncertain",
                "scene_type": "other",
                "sidewalk_confidence": 0.0,
                "reason": f"JSON parse failed from: {text[:50]}..."
            }