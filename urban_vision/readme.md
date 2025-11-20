urban_vision

一套整合街景影像分割、分類、分析及視覺化的影像處理工具。

📁 專案結構與功能說明
main.py

專案主程式。
請先在檔案內設定必要路徑：

DB_PATH = "你的資料庫檔案路徑"
IMAGE_OUTPUT_DIR = "輸出圖片資料夾路徑"

segmentation.py

使用語意分割模型對街景圖片進行分割。

classification.py

使用 Places365 模型對圖片進行場景分類。

visualize.py

將分割結果或分類結果可視化。

analyze_sidewalk.py

分析圖片中人行道相關資訊（像素比重、權重等）。

🚀 使用方法

設定必要參數
在 main.py 中設定：

DB_PATH

IMAGE_OUTPUT_DIR

執行主程式

python main.py

⚠️ 注意事項（VSCode 執行問題）

在 VSCode 中可能會遇到某些函式庫或環境無法開啟的問題。
建議直接在 CMD 或終端機 中啟動 conda 環境後執行：

conda activate urban
python main.py
