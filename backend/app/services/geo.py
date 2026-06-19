"""
Tiện ích tính khoảng cách địa lý phục vụ chấm công geofence.
"""

import math

EARTH_RADIUS_M = 6371000.0  # bán kính Trái Đất (mét)


def haversine_meters(lat1, lng1, lat2, lng2):
    """Khoảng cách (mét) giữa 2 điểm toạ độ theo công thức Haversine."""
    lat1, lng1, lat2, lng2 = map(float, (lat1, lng1, lat2, lng2))
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def nearest_location(locations, lat, lng):
    """Trả về (location, distance_m) của địa điểm gần nhất trong danh sách.
    Nếu danh sách rỗng trả về (None, None)."""
    best_loc = None
    best_dist = None
    for loc in locations:
        dist = haversine_meters(loc.latitude, loc.longitude, lat, lng)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_loc = loc
    return best_loc, best_dist
