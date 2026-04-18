import requests, time, math, random

SERVER_URL = "http://localhost:8000/api/gps"

# Three different routes for three buses
ROUTES = {
    "BUS-01": [
        (12.9716, 77.5946), (12.9730, 77.6010), (12.9755, 77.6072),
        (12.9770, 77.6200), (12.9784, 77.6408), (12.9700, 77.6390),
        (12.9622, 77.6387), (12.9500, 77.6310), (12.9352, 77.6245),
        (12.9250, 77.6180), (12.9166, 77.6101), (12.9250, 77.5980),
        (12.9400, 77.5900), (12.9600, 77.5920), (12.9716, 77.5946),
    ],
    "BUS-02": [
        (12.9850, 77.5800), (12.9870, 77.5900), (12.9890, 77.6000),
        (12.9910, 77.6100), (12.9930, 77.6200), (12.9900, 77.6300),
        (12.9860, 77.6350), (12.9800, 77.6300), (12.9750, 77.6200),
        (12.9700, 77.6100), (12.9680, 77.6000), (12.9700, 77.5900),
        (12.9750, 77.5850), (12.9800, 77.5820), (12.9850, 77.5800),
    ],
    "BUS-03": [
        (12.9600, 77.5700), (12.9620, 77.5800), (12.9650, 77.5900),
        (12.9680, 77.6000), (12.9700, 77.6100), (12.9720, 77.6200),
        (12.9700, 77.6300), (12.9670, 77.6250), (12.9640, 77.6150),
        (12.9610, 77.6050), (12.9580, 77.5950), (12.9560, 77.5850),
        (12.9570, 77.5750), (12.9590, 77.5720), (12.9600, 77.5700),
    ],
}

PING_INTERVAL     = 2
GPS_DROP_EVERY    = 25
GPS_DROP_DURATION = 8

def compute_heading(lat1, lng1, lat2, lng2):
    d_lng = math.radians(lng2 - lng1)
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    x = math.sin(d_lng) * math.cos(lat2r)
    y = (math.cos(lat1r) * math.sin(lat2r)
         - math.sin(lat1r) * math.cos(lat2r) * math.cos(d_lng))
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def interpolate(waypoints, steps=15):
    pts = []
    for i in range(len(waypoints) - 1):
        lat1, lng1 = waypoints[i]
        lat2, lng2 = waypoints[i+1]
        for s in range(steps):
            t = s / steps
            pts.append((lat1 + t*(lat2-lat1), lng1 + t*(lng2-lng1)))
    return pts

# Build interpolated routes and state for each bus
bus_states = {}
for bus_id, waypoints in ROUTES.items():
    bus_states[bus_id] = {
        "route":        interpolate(waypoints),
        "ping_count":   random.randint(0, 30),  # stagger start positions
        "gps_dropped":  False,
        "drop_counter": 0,
        "passengers":   random.randint(10, 45),
    }

print("Multi-bus simulator started.")
print(f"Running {len(ROUTES)} buses simultaneously.")
print("-" * 50)

while True:
    for bus_id, state in bus_states.items():
        route       = state["route"]
        n           = len(route)
        ping_count  = state["ping_count"]

        idx = ping_count % n
        lat, lng = route[idx]
        next_lat, next_lng = route[(idx+1) % n]
        heading = compute_heading(lat, lng, next_lat, next_lng)

        # Vary speed per bus
        base_speed = {"BUS-01": 35, "BUS-02": 30, "BUS-03": 40}[bus_id]
        speed = base_speed + random.uniform(-8, 8)

        # GPS drop logic
        if ping_count > 0 and ping_count % GPS_DROP_EVERY == 0:
            state["gps_dropped"]  = True
            state["drop_counter"] = 0
            print(f"\n*** {bus_id} GPS LOST at ping {ping_count} ***\n")

        if state["gps_dropped"]:
            state["drop_counter"] += 1
            gps_active = False
            if state["drop_counter"] >= GPS_DROP_DURATION:
                state["gps_dropped"] = False
                print(f"\n*** {bus_id} GPS RESTORED ***\n")
        else:
            gps_active = True
            lat += random.uniform(-0.0002, 0.0002)
            lng += random.uniform(-0.0002, 0.0002)

        # Slowly vary passenger count
        state["passengers"] = max(0, min(60,
            state["passengers"] + random.randint(-3, 3)))

        payload = {
            "bus_id":     bus_id,
            "lat":        round(lat, 6),
            "lng":        round(lng, 6),
            "speed":      round(speed, 1),
            "heading":    round(heading, 1),
            "gps_active": gps_active,
            "passengers": state["passengers"],
        }

        label = "LIVE" if gps_active else "GPS LOST"
        print(f"{bus_id} | [{label}] "
              f"lat={lat:.4f} lng={lng:.4f} "
              f"spd={speed:.0f}km/h pax={state['passengers']}")

        try:
            requests.post(SERVER_URL, json=payload, timeout=3)
        except Exception as e:
            print(f"  Could not reach server: {e}")

        state["ping_count"] += 1

    time.sleep(PING_INTERVAL)