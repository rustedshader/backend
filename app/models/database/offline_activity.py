from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column
from typing import Any


class DifficultyLevelEnum(str, PyEnum):
    EASY = "easy"
    MEDIUM = "moderate"
    HARD = "hard"


class Trek(SQLModel, table=True):
    __tablename__ = "treks"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), index=True)
    )
    city: str = Field(index=True)
    state: str = Field(index=True)
    duration: Optional[int] = Field(default=None, index=True)  # in hours
    altitude: Optional[int] = Field(default=None, index=True)  # in meters
    nearest_town: Optional[str] = Field(default=None, index=True)
    best_season: Optional[str] = Field(default=None)
    permits_required: Optional[str] = Field(default=None)
    equipment_needed: Optional[str] = Field(default=None)
    safety_tips: Optional[str] = Field(default=None)
    minimum_age: Optional[int] = Field(default=None, index=True)
    maximum_age: Optional[int] = Field(default=None, index=True)
    guide_required: bool = Field(default=True, index=True)
    cost_per_person: Optional[float] = Field(default=None, index=True)
    difficulty_level: DifficultyLevelEnum = Field(index=True)
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )


class TrekRouteData(SQLModel, table=True):
    __tablename__ = "trek_routes"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    trek_id: int = Field(foreign_key="treks.id", index=True)
    route: Any = Field(
        sa_column=Column(Geometry(geometry_type="LINESTRING", srid=4326))
    )
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
