from sqlmodel import SQLModel, Field, Relationship
from enum import Enum as PyEnum
import datetime
from typing import Optional, List


class TrackingDeviceStatusEnum(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class TrackingDevice(SQLModel, table=True):
    __tablename__ = "tracking_devices"

    id: int = Field(default=None, primary_key=True, index=True)
    device_id: str = Field(unique=True, index=True)
    api_key: str = Field(index=True)  # Hardcoded API key for device authentication
    treck_id: Optional[int] = Field(
        foreign_key="treks.id", index=True
    )  # Associated trek
    status: TrackingDeviceStatusEnum = Field(
        default=TrackingDeviceStatusEnum.INACTIVE, index=True
    )
    last_known_location: Optional[str] = Field(default=None)
    battery_level: Optional[float] = Field(default=None)  # Percentage
    signal_strength: Optional[float] = Field(default=None)  # dBm
    activated_at: Optional[int] = Field(default=None)  # Timestamp
    deactivated_at: Optional[int] = Field(default=None)  # Timestamp
    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
