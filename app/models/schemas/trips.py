from pydantic import BaseModel
from typing import Optional
import datetime


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


class TripCreate(BaseModel):
    itinerary_id: int
    expires_in_days: Optional[int] = 7  # Default 7 days for location sharing


class TripCreateResponse(BaseModel):
    trip_id: int
    user_id: int
    itinerary_id: int
    status: str
    tourist_id: Optional[str]
    blockchain_transaction_hash: Optional[str]
    share_code: str
    share_expires_at: datetime.datetime
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TripWithShareCodeResponse(BaseModel):
    id: int
    user_id: int
    itinerary_id: int
    status: str
    tourist_id: Optional[str]
    blockchain_transaction_hash: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # Location sharing info
    share_code: Optional[str] = None
    share_expires_at: Optional[datetime.datetime] = None
    share_is_active: Optional[bool] = None

    class Config:
        from_attributes = True
