from collections import deque
from config import (
    MAX_NODES, SAVE_IMAGES,
    STEP_METERS, LAT_MIN, LAT_MAX, LNG_MIN, LNG_MAX
)
from google_api import (
    streetview_metadata_by_location,
    streetview_image_url,
    download_image,
    offset_point
)
from db import init_db, insert_point


def in_bounds(lat, lng):
    if LAT_MIN is not None and lat < LAT_MIN:
        return False
    if LAT_MAX is not None and lat > LAT_MAX:
        return False
    if LNG_MIN is not None and lng < LNG_MIN:
        return False
    if LNG_MAX is not None and lng > LNG_MAX:
        return False
    return True


def find_start_meta(lat, lng):
    """
    用你給的起點座標，找一個最近的有街景 pano。
    找不到就丟例外。
    """
    meta = streetview_metadata_by_location(lat, lng)
    if meta.get("status") != "OK":
        raise Exception("起點附近找不到任何街景 pano（status != OK）")
    return meta


def crawl_tw(start_lat, start_lng):
    conn = init_db()

    start_meta = find_start_meta(start_lat, start_lng)
    start_pano = start_meta["pano_id"]
    print("起點 pano:", start_pano,
          "loc=", start_meta["location"],
          "date=", start_meta.get("date"))

    # BFS queue 裡面直接放 metadata dict
    q = deque([start_meta])

    visited_pano = set()
    count = 0

    while q and count < MAX_NODES:
        meta = q.popleft()
        pano_id = meta["pano_id"]

        if pano_id in visited_pano:
            continue
        visited_pano.add(pano_id)

        loc = meta["location"]
        lat = loc["lat"]
        lng = loc["lng"]
        date = meta.get("date", "unknown")

        if not in_bounds(lat, lng):
            continue

        print(f"[{count}] pano={pano_id} ({lat:.6f}, {lng:.6f}) date={date}")

        # 下載 / 紀錄 4 個方向
        imgs = {}
        for heading in [0, 90, 180, 270]:
            url = streetview_image_url(lat, lng, heading)
            if SAVE_IMAGES:
                filename = f"{count}_{heading}.jpg"
                path = download_image(url, filename)
                imgs[heading] = path
            else:
                imgs[heading] = url

        # 存入 DB（segmentation、人行道欄位先留空，之後 AI 填）
        insert_point(conn, meta, imgs)
        count += 1

        # === 產生鄰居候選點（用距離步進，而不是 links） ===
        # 8 個方向：每個 STEP_METERS
        for neighbor_heading in range(0, 360, 45):
            nlat, nlng = offset_point(lat, lng, STEP_METERS, neighbor_heading)

            if not in_bounds(nlat, nlng):
                continue

            # 在這個新位置附近找最近的街景 pano
            nmeta = streetview_metadata_by_location(nlat, nlng)
            if nmeta.get("status") != "OK":
                continue

            npano = nmeta.get("pano_id")
            if not npano:
                continue

            if npano in visited_pano:
                continue

            # 放進 BFS queue
            q.append(nmeta)

    print("BFS 完成，共處理節點數 =", count)
