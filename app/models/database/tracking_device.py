from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional
import datetime


class TrackingDeviceStatusEnum(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class TrackingDevice(SQLModel, table=True):
    __tablename__ = "tracking_devices"

    id: int = Field(default=None, primary_key=True, index=True)
    api_key: str = Field(index=True)
    status: TrackingDeviceStatusEnum = Field(
        default=TrackingDeviceStatusEnum.INACTIVE, index=True
    )
    last_latitude: Optional[float] = Field(default=None, index=True)
    last_longitude: Optional[float] = Field(default=None, index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
