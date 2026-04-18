from pydantic import BaseModel
from typing import Optional

class GPSPing(BaseModel):
    bus_id: str = "BUS-01"
    lat: float
    lng: float
    speed: float
    heading: float
    gps_active: bool
    passengers: Optional[int] = 0

class BusState(BaseModel):
    bus_id: str
    lat: float
    lng: float
    speed: float
    heading: float
    gps_active: bool
    last_update: float
    status: str
    passengers: int = 0