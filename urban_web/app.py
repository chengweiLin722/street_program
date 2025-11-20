from flask import Flask, render_template, send_from_directory, jsonify
import sqlite3
import os

DB_PATH = r"C:\Homework\urban_vision\streetview.db"   # ★ 你的 SQLite 位置
OUTPUT_DIR = os.path.join("static", "output")

app = Flask(__name__, static_folder="static", template_folder="templates")


# -------------------------
#  API: 回傳所有座標點資料
# -------------------------
@app.route("/api/points")
def api_points():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("SELECT * FROM streetview_points").fetchall()
    conn.close()

    data = []
    for row in rows:
        point = dict(row)

        # ---- 建立 scene dict ----
        point["scene"] = {
            "0": point.get("scene0"),
            "90": point.get("scene90"),
            "180": point.get("scene180"),
            "270": point.get("scene270")
        }

        # ---- 建立 score dict (你的 confidence score) ----
        point["score"] = {
            "0": point.get("score0"),
            "90": point.get("score90"),
            "180": point.get("score180"),
            "270": point.get("score270")
        }

        # 將 Windows 路徑轉成 /output/... 網頁可用路徑
        for angle in ["0", "90", "180", "270"]:
            img = point.get(f"img{angle}")
            seg = point.get(f"seg{angle}")

            if img:
                point[f"img{angle}"] = "/output/" + os.path.basename(img)
            if seg:
                point[f"seg{angle}"] = "/output/" + os.path.basename(seg)

        data.append(point)

    return jsonify(data)


# -------------------------
# 提供 segmentation/raw 圖片
# -------------------------
@app.route("/output/<path:filename>")
def static_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# -------------------------
# Leaflet 地圖首頁
# -------------------------
@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM streetview_points").fetchall()
    conn.close()

    # 把資料轉成可用格式
    points = []
    for r in rows:
        p = dict(r)
        # ---- 建立 scene dict ----
        p["scene"] = {
            "0": p.get("scene0"),
            "90": p.get("scene90"),
            "180": p.get("scene180"),
            "270": p.get("scene270")
        }

        # ---- 建立 score dict (你的 confidence score) ----
        p["score"] = {
            "0": p.get("score0"),
            "90": p.get("score90"),
            "180": p.get("score180"),
            "270": p.get("score270")
        }        
        
        p["images"] = {
            "0":  {"raw": "/output/" + os.path.basename(p["img0"] or ""),  "seg": "/output/" + os.path.basename(p["seg0"] or "")},
            "90": {"raw": "/output/" + os.path.basename(p["img90"] or ""), "seg": "/output/" + os.path.basename(p["seg90"] or "")},
            "180":{"raw": "/output/" + os.path.basename(p["img180"] or ""),"seg": "/output/" + os.path.basename(p["seg180"] or "")},
            "270":{"raw": "/output/" + os.path.basename(p["img270"] or ""),"seg": "/output/" + os.path.basename(p["seg270"] or "")}
        }

        # 計算人行道角度數
        p["sidewalk_count"] = sum([
            p.get("sidewalk0",0),
            p.get("sidewalk90",0),
            p.get("sidewalk180",0),
            p.get("sidewalk270",0),
        ])

        points.append(p)

    return render_template("map.html", points_json=points)

if __name__ == "__main__":
    print("Running urban_web on http://localhost:8888")
    app.run(host="0.0.0.0", port=8888, debug=True)
