from sqlmodel import SQLModel, Field
from typing import Optional
import datetime


class Itinerary(SQLModel, table=True):
    __tablename__ = "itineraries"

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    destination_city: str = Field(index=True)
    destination_state: str = Field(index=True)
    start_date: datetime.date = Field(index=True)
    end_date: datetime.date = Field(index=True)
    total_duration_days: int = Field(index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )


class ItineraryDay(SQLModel, table=True):
    __tablename__ = "itinerary_days"

    id: int = Field(default=None, primary_key=True, index=True)
    itinerary_id: int = Field(foreign_key="itineraries.id", index=True)
    accommodation_id: int = Field(
        default=None, foreign_key="accommodations.id", index=True
    )
    day_number: int = Field(index=True)
    trek_id: Optional[int] = Field(default=None, foreign_key="treks.id", index=True)
