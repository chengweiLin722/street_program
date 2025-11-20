import sqlite3

DB_NAME = "streetview.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode=WAL;")
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS streetview_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pano_id TEXT UNIQUE,
        lat REAL,
        lng REAL,
        date TEXT,

        -- 原始街景圖片 (路徑或網址)
        img0 TEXT,
        img90 TEXT,
        img180 TEXT,
        img270 TEXT,

        -- Scene Type (Places365 or 自訓模型) ★ 新增
        scene0 TEXT,
        scene90 TEXT,
        scene180 TEXT,
        scene270 TEXT,

        -- segmentation 結果 (路徑或 BLOB)
        seg0 TEXT,
        seg90 TEXT,
        seg180 TEXT,
        seg270 TEXT,

        -- 是否有人行道 (0/1)
        sidewalk0 INTEGER,
        sidewalk90 INTEGER,
        sidewalk180 INTEGER,
        sidewalk270 INTEGER,

        -- 人行道信心分數 0~1
        score0 REAL,
        score90 REAL,
        score180 REAL,
        score270 REAL,

        -- 是否已做完 segmentation/type 判斷
        processed INTEGER DEFAULT 0
    );
    ''')
    conn.commit()
    return conn


def insert_point(conn, meta, imgs):
    """
    meta: Street View metadata dict
    imgs: dict {heading: path_or_url}
    """

    conn.execute('''
    INSERT OR IGNORE INTO streetview_points
    (pano_id, lat, lng, date,
     img0, img90, img180, img270,
     scene0, scene90, scene180, scene270,
     seg0, seg90, seg180, seg270,
     sidewalk0, sidewalk90, sidewalk180, sidewalk270,
     score0, score90, score180, score270,
     processed)
    VALUES (?, ?, ?, ?,
            ?, ?, ?, ?,
            NULL, NULL, NULL, NULL,
            NULL, NULL, NULL, NULL,
            NULL, NULL, NULL, NULL,
            NULL, NULL, NULL, NULL,
            0)
    ''', (
        meta["pano_id"],
        meta["location"]["lat"],
        meta["location"]["lng"],
        meta.get("date", None),

        imgs.get(0),
        imgs.get(90),
        imgs.get(180),
        imgs.get(270)
    ))
    
    conn.commit()
