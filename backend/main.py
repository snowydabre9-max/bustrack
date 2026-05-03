from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import asyncio, time
from typing import List, Dict

from database import init_db, save_gps_ping, get_recent_pings
from predictor import calculate_eta
from models import GPSPing, BusState

app = FastAPI(title="BusTrack")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

connected_clients: List[WebSocket] = []

bus_states: Dict[str, BusState] = {
    "BUS-01": BusState(bus_id="BUS-01", lat=12.9716, lng=77.5946,
                       speed=30.0, heading=90.0, gps_active=True,
                       last_update=time.time(), status="live", passengers=20),
    "BUS-02": BusState(bus_id="BUS-02", lat=12.9850, lng=77.5800,
                       speed=30.0, heading=90.0, gps_active=True,
                       last_update=time.time(), status="live", passengers=15),
    "BUS-03": BusState(bus_id="BUS-03", lat=12.9600, lng=77.5700,
                       speed=30.0, heading=90.0, gps_active=True,
                       last_update=time.time(), status="live", passengers=35),
}

ROUTE_STOPS = [
    {"name": "Central Station",  "lat": 12.9716, "lng": 77.5946},
    {"name": "MG Road",          "lat": 12.9755, "lng": 77.6072},
    {"name": "Indiranagar",      "lat": 12.9784, "lng": 77.6408},
    {"name": "Domlur",           "lat": 12.9622, "lng": 77.6387},
    {"name": "Koramangala",      "lat": 12.9352, "lng": 77.6245},
    {"name": "BTM Layout",       "lat": 12.9166, "lng": 77.6101},
]

SCHEDULE = {
    "BUS-01": ["06:00","06:30","07:00","07:30","08:00","08:30",
               "09:00","12:00","15:00","18:00","20:00","22:00"],
    "BUS-02": ["06:15","06:45","07:15","07:45","08:15","08:45",
               "09:15","12:15","15:15","18:15","20:15","22:15"],
    "BUS-03": ["06:30","07:00","07:30","08:00","08:30","09:00",
               "09:30","12:30","15:30","18:30","20:30","22:30"],
}

# ── Page routes ──────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.get("/landing.html")
async def landing():
    return FileResponse("../frontend/landing.html")

@app.get("/login.html")
async def login_page():
    return FileResponse("../frontend/login.html")

@app.get("/admin.html")
async def admin_page():
    return FileResponse("../frontend/admin.html")

@app.get("/driver.html")
async def driver_page():
    return FileResponse("../frontend/driver.html")

@app.get("/analytics.html")
async def analytics_page():
    return FileResponse("../frontend/analytics.html")

@app.get("/settings.html")
async def settings_page():
    return FileResponse("../frontend/settings.html")

# ── API routes ───────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    init_db()

@app.post("/api/gps")
async def receive_gps(ping: GPSPing):
    save_gps_ping(ping)
    state = bus_states.get(ping.bus_id)
    if state:
        state.lat         = ping.lat
        state.lng         = ping.lng
        state.speed       = ping.speed
        state.heading     = ping.heading
        state.gps_active  = ping.gps_active
        state.last_update = time.time()
        state.status      = "live" if ping.gps_active else "predicted"
        state.passengers  = ping.passengers or 0

    etas = calculate_eta(ping.lat, ping.lng, ping.speed, ROUTE_STOPS)
    payload = {
        "type":       "bus_update",
        "bus_id":     ping.bus_id,
        "lat":        ping.lat,
        "lng":        ping.lng,
        "speed":      ping.speed,
        "heading":    ping.heading,
        "gps_active": ping.gps_active,
        "status":     "live" if ping.gps_active else "predicted",
        "timestamp":  time.time(),
        "passengers": ping.passengers or 0,
        "etas":       etas,
        "stops":      ROUTE_STOPS,
    }
    await broadcast(payload)
    return {"ok": True}

@app.get("/api/state")
async def get_state():
    all_states = []
    for bus_id, state in bus_states.items():
        etas = calculate_eta(state.lat, state.lng, state.speed, ROUTE_STOPS)
        all_states.append({**state.dict(), "etas": etas, "stops": ROUTE_STOPS})
    return {"buses": all_states, "schedule": SCHEDULE}

@app.get("/api/history")
async def get_history():
    return {"history": get_recent_pings(50)}

@app.get("/api/schedule")
async def get_schedule():
    return {"schedule": SCHEDULE, "stops": ROUTE_STOPS}

# ── WebSocket ────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        await websocket.send_json({"type": "connected"})
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def broadcast(payload: dict):
    dead = []
    for client in connected_clients:
        try:
            await client.send_json(payload)
        except:
            dead.append(client)
    for d in dead:
        connected_clients.remove(d)