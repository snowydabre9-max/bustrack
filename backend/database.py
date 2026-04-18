import sqlite3
import time
from models import GPSPing

DB_PATH = "bustrack.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gps_pings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id      TEXT    NOT NULL,
            lat         REAL    NOT NULL,
            lng         REAL    NOT NULL,
            speed       REAL    NOT NULL,
            heading     REAL    NOT NULL,
            gps_active  INTEGER NOT NULL,
            timestamp   REAL    NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Database ready.")

def save_gps_ping(ping: GPSPing):
    conn = get_conn()
    conn.execute(
        """INSERT INTO gps_pings
           (bus_id, lat, lng, speed, heading, gps_active, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ping.bus_id, ping.lat, ping.lng, ping.speed,
         ping.heading, int(ping.gps_active), time.time())
    )
    conn.commit()
    conn.close()

def get_recent_pings(limit: int = 50):
    conn = get_conn()
    rows = conn.execute(
        """SELECT lat, lng, speed, heading, gps_active, timestamp
           FROM gps_pings
           ORDER BY timestamp DESC LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [
        {"lat": r[0], "lng": r[1], "speed": r[2],
         "heading": r[3], "gps_active": bool(r[4]), "timestamp": r[5]}
        for r in reversed(rows)
    ]