# Streetview Crawler

一個用於爬取 Google Street View 資料的自動化工具。

## 🛠️ 使用步驟

1.  **設定參數 (`config.py`)**
    開啟 `config.py` 設定核心參數：
    * `API_KEY`: Google Maps API 金鑰
    * `RADIUS`: 搜尋半徑
    * `STEP`: 步長
    * `OUTPUT_DIR`: 輸出目錄

2.  **設定座標 (`main.py`)**
    在 `main.py` 中修改起始座標變數（Latitude, Longitude）。

3.  **執行爬蟲**
    在終端機執行：
    ```bash
    python main.py
    ```

即可開始爬取街景資料至指定目錄。