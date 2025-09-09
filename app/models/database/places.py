from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional
import datetime


class PlaceTypeEnum(str, PyEnum):
    TREK = "trek"
    CITY_TOUR = "city_tour"
    HISTORICAL_SITE = "historical_site"
    TEMPLE = "temple"
    MUSEUM = "museum"
    PARK = "park"
    BEACH = "beach"
    HILL_STATION = "hill_station"
    ADVENTURE_SPORT = "adventure_sport"
    CULTURAL_SITE = "cultural_site"
    RESTAURANT = "restaurant"
    SHOPPING = "shopping"
    NIGHTLIFE = "nightlife"
    OTHER = "other"


class Place(SQLModel, table=True):
    __tablename__ = "places"

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    place_type: PlaceTypeEnum = Field(index=True)

    # Location details
    city: str = Field(index=True)
    state: str = Field(index=True)
    country: str = Field(default="India", index=True)
    address: Optional[str] = Field(default=None)

    # Coordinates
    latitude: float = Field(index=True)
    longitude: float = Field(index=True)

    # Additional details
    duration_hours: Optional[int] = Field(
        default=None
    )  # Expected time to visit/complete
    entry_fee: Optional[float] = Field(default=None)
    best_season: Optional[str] = Field(
        default=None
    )  # e.g., "Winter", "Summer", "Monsoon", "Year-round"

    # Accessibility and safety
    wheelchair_accessible: bool = Field(default=False)
    safety_rating: Optional[int] = Field(default=None, ge=1, le=5)  # 1-5 scale

    # Contact and timing
    contact_number: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    opening_time: Optional[str] = Field(default=None)  # HH:MM format
    closing_time: Optional[str] = Field(default=None)  # HH:MM format

    # Status
    is_active: bool = Field(default=True, index=True)
    is_featured: bool = Field(default=False, index=True)

    # Metadata
    created_by_admin_id: int = Field(foreign_key="users.id", index=True)
    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
