import requests
import os
import math
from config import API_KEY, IMAGE_DIR, SEARCH_RADIUS_METERS


def streetview_metadata_by_location(lat, lng):
    """
    用座標查附近最近的街景 pano metadata。
    加上 radius，for 台灣比較可靠。
    """
    url = (
        "https://maps.googleapis.com/maps/api/streetview/metadata"
        f"?location={lat},{lng}"
        f"&radius={SEARCH_RADIUS_METERS}"
        f"&key={API_KEY}"
    )
    return requests.get(url).json()


def streetview_image_url(lat, lng, heading):
    return (
        "https://maps.googleapis.com/maps/api/streetview"
        f"?size=640x640&location={lat},{lng}"
        f"&heading={heading}&pitch=0&key={API_KEY}"
    )


def download_image(url, filename):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    path = os.path.join(IMAGE_DIR, filename)
    resp = requests.get(url)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)
    return path


def offset_point(lat, lng, distance_m, bearing_deg):
    """
    給定起點(lat,lng) + 距離(公尺) + 方位角(度)，回傳新座標。
    """
    R = 6378137.0  # 地球半徑 (m)
    br = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lng1 = math.radians(lng)

    lat2 = math.asin(math.sin(lat1) * math.cos(distance_m / R) +
                     math.cos(lat1) * math.sin(distance_m / R) * math.cos(br))

    lng2 = lng1 + math.atan2(
        math.sin(br) * math.sin(distance_m / R) * math.cos(lat1),
        math.cos(distance_m / R) - math.sin(lat1) * math.sin(lat2)
    )

    return math.degrees(lat2), math.degrees(lng2)
