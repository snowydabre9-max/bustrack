import math
from typing import List, Dict

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def predict_position(lat, lng, speed_kmh, heading_deg, elapsed_sec):
    if elapsed_sec <= 0 or speed_kmh <= 0:
        return lat, lng
    distance_km = (speed_kmh / 3600) * elapsed_sec
    heading_rad = math.radians(heading_deg)
    new_lat = lat + (distance_km * math.cos(heading_rad)) / 111.0
    new_lng = lng + (distance_km * math.sin(heading_rad)) / (
        111.0 * math.cos(math.radians(lat))
    )
    return new_lat, new_lng

def calculate_eta(current_lat, current_lng, speed_kmh, stops: List[Dict]):
    if speed_kmh <= 0:
        speed_kmh = 30.0
    results = []
    for stop in stops:
        dist_km = haversine_km(current_lat, current_lng,
                               stop["lat"], stop["lng"])
        eta_min = (dist_km / speed_kmh) * 60
        if eta_min < 1:
            eta_text = "Arriving now"
        elif eta_min < 60:
            eta_text = f"{int(eta_min)} min"
        else:
            h = int(eta_min // 60)
            m = int(eta_min % 60)
            eta_text = f"{h}h {m}m"
        results.append({
            "name": stop["name"],
            "distance_km": round(dist_km, 2),
            "eta_minutes": round(eta_min, 1),
            "eta_text": eta_text,
        })
    return results