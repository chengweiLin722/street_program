from collections import deque
import math
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

def compute_bearing(lat1, lng1, lat2, lng2):
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dLng = math.radians(lng2 - lng1)

    y = math.sin(dLng) * math.cos(lat2)
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLng)

    brng = math.atan2(y, x)
    brng = math.degrees(brng)
    return (brng + 360) % 360

def directional_search_angles(p_prev, p_curr, max_turn=45):
    if p_prev is None:
        # 起始點：360° 全部試
        return list(range(0, 360, 45))

    lat1, lng1 = p_prev
    lat2, lng2 = p_curr

    road_dir = compute_bearing(lat1, lng1, lat2, lng2)

    return [
        (road_dir - max_turn) % 360,
        road_dir % 360,
        (road_dir + max_turn) % 360
    ]

def geo_distance(lat1, lng1, lat2, lng2):
    """
    回傳兩座標距離（公尺）
    """
    R = 6378137.0
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    lng1, lng2 = math.radians(lng1), math.radians(lng2)
    dlat = lat2 - lat1
    dlng = lng2 - lng1

    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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
    prev_location = None
    visited_positions = []  # list of (lat, lng)
    DIST_THRESH = 25  # 公尺


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
            
        # === 距離去重 ===
        too_close = False
        for (vlat, vlng) in visited_positions:
            if geo_distance(lat, lng, vlat, vlng) < DIST_THRESH:
                too_close = True
                break

        if too_close:
            # 距離小於 25 m，視為重複點
            continue

        # === 加入 visited（新點）===
        visited_positions.append((lat, lng))

        # === 方向限制 ===
        if prev_location is None:
            search_angles = list(range(0, 360, 45))
        else:
            search_angles = directional_search_angles(prev_location, (lat, lng))

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
        for hd in search_angles:
            nlat, nlng = offset_point(lat, lng, STEP_METERS, hd)

            nmeta = streetview_metadata_by_location(nlat, nlng)
            if nmeta.get("status") == "OK":
                npano = nmeta["pano_id"]
                if npano not in visited_pano:
                    q.append(nmeta)
        prev_location = (lat, lng)


    print("BFS 完成，共處理節點數 =", count)
