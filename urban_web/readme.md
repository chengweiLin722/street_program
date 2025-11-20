# Urban Web

一個用於展示街景分析結果的 Flask 網頁介面。可從資料庫讀取資料並在地圖上顯示圖片、人行道資訊等內容。

## 📁 專案結構

* `app.py`: Flask 主程式
* `templates/map.html`: 主頁面 HTML 模板
* `static/output/`: **放置輸出圖片的資料夾**
* `static/style.css`: 網頁樣式

## ⚙️ 參數設定

1.  **設定資料庫**
    在 `app.py` 中修改以下變數指向您的資料庫：
    ```python
    DB_PATH = "your_database_path.db"
    ```

2.  **放入圖片**
    將需要展示的圖片檔案放入 `static/output/` 資料夾中。

## 🚀 執行方式

1.  **啟動伺服器**
    ```bash
    python app.py
    ```

2.  **開啟網頁**
    在瀏覽器網址列輸入：
    [http://127.0.0.1:8888/](http://127.0.0.1:8888/)

即可看到地圖介面與圖片展示。