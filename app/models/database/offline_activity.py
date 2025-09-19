from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional, Any
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column


class DifficultyLevelEnum(str, PyEnum):
    EASY = "easy"
    MEDIUM = "moderate"
    HARD = "hard"


class OfflineActivity(SQLModel, table=True):
    __tablename__ = "offline_activities"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), index=True)
    )
    city: str = Field(index=True)
    district: str = Field(index=True)
    state: str = Field(index=True)
    duration: Optional[int] = Field(default=None, index=True)  # in hours
    altitude: Optional[int] = Field(default=None, index=True)  # in meters
    nearest_town: Optional[str] = Field(default=None)
    best_season: Optional[str] = Field(default=None)
    permits_required: Optional[str] = Field(default=None)
    equipment_needed: Optional[str] = Field(default=None)
    safety_tips: Optional[str] = Field(default=None)
    minimum_age: Optional[int] = Field(default=None)
    maximum_age: Optional[int] = Field(default=None)
    guide_required: bool = Field(default=True)
    minimum_people: Optional[int] = Field(default=None)
    maximum_people: Optional[int] = Field(default=None)
    cost_per_person: Optional[float] = Field(default=None)
    difficulty_level: DifficultyLevelEnum = Field(index=True)
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )


class OfflineActivityRouteData(SQLModel, table=True):
    __tablename__ = "offline_activity_route_data"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    offline_activity_id: int = Field(foreign_key="offline_activities.id", index=True)
    route: Any = Field(
        sa_column=Column(Geometry(geometry_type="LINESTRING", srid=4326), index=True),
        default=None,
    )
    route_data: Optional[str] = Field(default=None)  # Store route as JSON string
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
