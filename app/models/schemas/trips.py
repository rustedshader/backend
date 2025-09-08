from pydantic import BaseModel
from typing import Optional
import datetime


class TripCreate(BaseModel):
    itinerary_id: int
    treck_id: int
    guide_id: Optional[int]
    start_date: datetime.date
    end_date: datetime.date


class TripUpdate(BaseModel):
    guide_id: Optional[int]
    tracking_device_id: Optional[int]
    start_date: Optional[datetime.date]
    end_date: Optional[datetime.date]
    status: Optional[str]


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float


class LinkDeviceRequest(BaseModel):
    device_id: str


class TripResponse(BaseModel):
    id: int
    user_id: int
    trek_id: int
    guide_id: Optional[int]
    tracking_deivce_id: Optional[int]
    start_date: datetime.date
    end_date: datetime.date
    status: str

    class Config:
        from_attributes = True


class LocationHistoryResponse(BaseModel):
    id: int
    trip_id: int
    timestamp: int
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
