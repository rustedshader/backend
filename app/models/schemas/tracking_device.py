from pydantic import BaseModel
from app.models.database.tracking_device import TrackingDeviceStatusEnum
from typing import Optional


class TrackingDeviceCreate(BaseModel):
    device_id: str
    treck_id: Optional[int] = None


class TrackingDeviceResponse(BaseModel):
    id: int
    device_id: str
    api_key: str
    status: TrackingDeviceStatusEnum
    treck_id: Optional[int] = None
    created_at: int

    class Config:
        from_attributes = True


class TrackingDeviceUpdate(BaseModel):
    status: Optional[TrackingDeviceStatusEnum] = None
    treck_id: Optional[int] = None
    last_known_location: Optional[str] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None


class TrackingDeviceApiKeyResponse(BaseModel):
    device_id: str
    api_key: str

    class Config:
        from_attributes = True


class TrackingDeviceStatusUpdate(BaseModel):
    status: TrackingDeviceStatusEnum


class TrackingDeviceUpdateRequest(BaseModel):
    status: Optional[TrackingDeviceStatusEnum] = None
    treck_id: Optional[int] = None
    last_known_location: Optional[str] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None


class TrackingDeviceListResponse(BaseModel):
    devices: list[TrackingDeviceResponse]
    total: int
