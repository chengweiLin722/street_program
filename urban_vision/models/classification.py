import os
import torch
from torch import nn
from torchvision import models, transforms
from PIL import Image
import requests

class SceneClassifier:
    def __init__(self, model_dir="models_places365", device=None):
        """
        model_dir: 模型與標籤存放路徑
        device: "cpu" 或 "cuda"
        """
        self.device = device or ("cpu")
        os.makedirs(model_dir, exist_ok=True)

        # ------------------------
        # 1️⃣ 下載 Places365 標籤
        # ------------------------
        label_path = os.path.join(model_dir, "categories_places365.txt")
        if not os.path.exists(label_path):
            print("📥 下載 Places365 標籤...")
            url = "https://raw.githubusercontent.com/csailvision/places365/master/categories_places365.txt"
            r = requests.get(url)
            with open(label_path, "w", encoding="utf-8") as f:
                f.write(r.text)

        with open(label_path) as f:
            labels_text = f.read().splitlines()
        self.classes = [line.split(" ")[0][3:] for line in labels_text]

        # ------------------------
        # 2️⃣ 下載 Places365 預訓練 ResNet18
        # ------------------------
        model_path = os.path.join(model_dir, "resnet18_places365.pth.tar")
        if not os.path.exists(model_path):
            print("📥 下載 Places365 ResNet18 預訓練模型...")
            url = "http://places2.csail.mit.edu/models_places365/resnet18_places365.pth.tar"
            r = requests.get(url, stream=True)
            with open(model_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

        # ------------------------
        # 3️⃣ 建立模型
        # ------------------------
        self.model = models.resnet18(num_classes=365)
        checkpoint = torch.load(model_path, map_location=self.device)

        # 移除 module. 前綴
        state_dict = checkpoint['state_dict']
        new_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}

        self.model.load_state_dict(new_state_dict)
        self.model.eval().to(self.device)

        # ------------------------
        # 4️⃣ 圖片前處理
        # ------------------------
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485,0.456,0.406],
                                 std=[0.229,0.224,0.225])
        ])

        print(f"📌 分類標籤數量: {len(self.classes)}")

    def classify(self, image_input):
            """輸入圖片路徑或 PIL.Image，回傳場景分類文字"""
            if isinstance(image_input, str):
                image = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, Image.Image):
                image = image_input.convert("RGB")
            else:
                raise ValueError("classify() 需要傳入圖片路徑或 PIL.Image 物件")

            input_tensor = self.transform(image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                output = self.model(input_tensor)
                _, pred = output.max(1)

            label = self.classes[pred.item()]
            print(f"🎯 Scene → {label}")
            return label
