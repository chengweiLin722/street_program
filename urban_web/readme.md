urban_web

一個用於展示街景分析結果的 Flask 網頁介面。
可從資料庫讀取資料並在地圖上顯示圖片、人行道資訊等內容。

📁 專案結構
urban_web/
│── app.py               # Flask 主程式
│
├── templates/
│     └── map.html       # 主頁面 HTML 模板
│
├── static/
│     ├── output/        # 放置輸出圖片的資料夾
│     └── style.css      # 網頁樣式

⚙️ 參數設定

在 app.py 裡設定資料庫位置：

DB_PATH = "your_database_path.db"


將需要展示的圖片放入：

static/output/

🚀 執行方式

啟動網頁伺服器：

python app.py


開啟瀏覽器並進入：

http://127.0.0.1:8888/


即可看到地圖介面與圖片展示。