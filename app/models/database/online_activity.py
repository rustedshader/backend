from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional, Any
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column


class PlaceTypeEnum(str, PyEnum):
    HISTORICAL_SITE = "historical_site"
    TEMPLE = "temple"
    MUSEUM = "museum"
    PARK = "park"
    ADVENTURE_SPORT = "adventure_sport"
    CULTURAL_SITE = "cultural_site"
    RESTAURANT = "restaurant"
    SHOPPING = "shopping"
    NIGHTLIFE = "nightlife"


class OnlineActivity(SQLModel, table=True):
    __tablename__ = "online_activities"

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    place_type: PlaceTypeEnum = Field(index=True)
    city: str = Field(index=True)
    state: str = Field(index=True)
    address: Optional[str] = Field(default=None)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326)), index=True
    )
    cost_per_person: Optional[float] = Field(default=None, index=True)
    wheelchair_accessible: bool = Field(default=False)
    safety_rating: Optional[int] = Field(default=None, ge=1, le=5)  # 1-5 scale
    contact_number: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    opening_time: datetime.time = Field(default=None)
    closing_time: datetime.time = Field(default=None)
    is_active: bool = Field(default=True, index=True)
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
