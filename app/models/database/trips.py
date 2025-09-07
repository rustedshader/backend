from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Text
from typing import Any


class TripStatusEnum(str, PyEnum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Trips(SQLModel, table=True):
    __tablename__ = "trips"
    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    trek_id: int = Field(foreign_key="treks.id", index=True)
    guide_id: Optional[int] = Field(foreign_key="guides.id", index=True)
    tracking_deivce_id: Optional[int] = Field(
        foreign_key="tracking_devices.id", index=True
    )
    start_date: datetime.date = Field(index=True)
    end_date: datetime.date = Field(index=True)
    status: TripStatusEnum = Field(default=TripStatusEnum.ASSIGNED, index=True)


class LocationHistory(SQLModel, table=True):
    __tablename__ = "location_history"
    id: int = Field(default=None, primary_key=True, index=True)
    trip_id: int = Field(foreign_key="trips.id", index=True)
    timestamp: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    location: Any = Field(sa_column=Column(Geometry(geometry_type="POINT", srid=4326)))


class AlertTypeEnum(str, PyEnum):
    DEVIATION = "deviation"
    EMERGENCY = "emergency"
    WEATHER = "weather"
    OTHER = "other"


class AlertStatusEnum(str, PyEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alerts(SQLModel, table=True):
    __tablename__ = "alerts"
    id: int = Field(default=None, primary_key=True, index=True)
    trip_id: int = Field(foreign_key="trips.id", index=True)
    timestamp: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    alert_type: AlertTypeEnum = Field(index=True)
    description: Optional[str] = Field(default=None)
    location: Any = Field(sa_column=Column(Geometry(geometry_type="POINT", srid=4326)))
    status: AlertStatusEnum = Field(default=AlertStatusEnum.NEW, index=True)
