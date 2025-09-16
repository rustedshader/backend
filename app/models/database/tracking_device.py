from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column
from typing import Any


class TrackingDeviceStatusEnum(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class TrackingDevice(SQLModel, table=True):
    __tablename__ = "tracking_devices"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    api_key: str = Field(index=True)
    status: TrackingDeviceStatusEnum = Field(
        default=TrackingDeviceStatusEnum.INACTIVE, index=True
    )
    last_known_location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), index=True),
        default=None,
    )
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
