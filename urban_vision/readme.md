
# Urban Vision

一套整合街景影像分割、分類、分析及視覺化的影像處理工具。

## 📁 檔案說明

* **`main.py`**: 主程式，**需先設定內部路徑參數**。
* **`segmentation.py`**: 使用語意分割模型處理街景。
* **`classification.py`**: 使用 Places365 模型進行分類。
* **`visualize.py`**: 產出視覺化結果圖片。
* **`analyze_sidewalk.py`**: 分析人行道資訊（像素比重、權重）。

## 🚀 執行步驟

1.  **設定路徑**
    開啟 `main.py` 修改以下變數：
    ```python
    DB_PATH = "你的資料庫檔案路徑"
    IMAGE_OUTPUT_DIR = "輸出圖片資料夾路徑"
    ```

2.  **啟動程式**
    ```bash
    python main.py
    ```

## ⚠️ 重要注意事項

**VSCode 使用者請注意**：
若在 VSCode 中遇到函式庫無法載入或環境錯誤，請改用 **CMD / Terminal** 手動執行：
