from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional
import datetime


class ItineraryTypeEnum(str, PyEnum):
    TREK = "trek"
    CITY_TOUR = "city_tour"
    MIXED = "mixed"  # Can include both places and trekking


class DayTypeEnum(str, PyEnum):
    TREK_DAY = "trek_day"  # Whole day dedicated to trekking
    PLACE_VISIT_DAY = "place_visit_day"  # Whole day visiting tourist places/attractions


class ItineraryStatusEnum(str, PyEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransportModeEnum(str, PyEnum):
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAR = "car"
    TAXI = "taxi"
    WALKING = "walking"
    OTHER = "other"


class AccommodationTypeEnum(str, PyEnum):
    HOTEL = "hotel"
    GUEST_HOUSE = "guest_house"
    HOMESTAY = "homestay"
    CAMPING = "camping"
    HOSTEL = "hostel"
    RESORT = "resort"
    OTHER = "other"


class Itinerary(SQLModel, table=True):
    __tablename__ = "itineraries"

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Itinerary can be either trek-based, place-based, or mixed
    itinerary_type: ItineraryTypeEnum = Field(index=True)
    trek_id: Optional[int] = Field(
        foreign_key="treks.id", index=True, default=None
    )  # For trek-based itineraries
    primary_place_id: Optional[int] = Field(
        foreign_key="places.id", index=True, default=None
    )  # For place-based itineraries

    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)

    # Destination details
    destination_city: str = Field(index=True)
    destination_state: str = Field(index=True)
    destination_country: str = Field(default="India", index=True)

    start_date: datetime.date = Field(index=True)
    end_date: datetime.date = Field(index=True)
    total_duration_days: int = Field(index=True)
    estimated_budget: Optional[float] = Field(default=None)
    number_of_travelers: int = Field(default=1)
    purpose_of_visit: str = Field(
        default="tourism"
    )  # tourism, business, pilgrimage, etc.
    status: ItineraryStatusEnum = Field(default=ItineraryStatusEnum.ACTIVE, index=True)

    # Emergency contacts
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relation: str = Field(default="family")

    # Travel preferences
    preferred_language: Optional[str] = Field(default="english")
    special_requirements: Optional[str] = Field(default=None)  # medical, dietary, etc.

    # Timestamps
    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    approved_at: Optional[int] = Field(default=None)  # Auto-approved now


class ItineraryDay(SQLModel, table=True):
    __tablename__ = "itinerary_days"

    id: int = Field(default=None, primary_key=True, index=True)
    itinerary_id: int = Field(foreign_key="itineraries.id", index=True)
    day_number: int = Field(index=True)
    date: datetime.date = Field(index=True)

    # Day type - either trek or place visit for the whole day
    day_type: DayTypeEnum = Field(index=True)

    # For TREK_DAY: reference to trek being done that day
    trek_id: Optional[int] = Field(foreign_key="treks.id", index=True, default=None)

    # For PLACE_VISIT_DAY: reference to primary place to visit
    primary_place_id: Optional[int] = Field(
        foreign_key="places.id", index=True, default=None
    )

    # General day planning
    planned_activities: str  # What they plan to do on this day
    estimated_time_start: Optional[str] = Field(default=None)  # HH:MM format
    estimated_time_end: Optional[str] = Field(default=None)  # HH:MM format

    # Accommodation planning with coordinates (where they'll stay that night)
    accommodation_name: Optional[str] = Field(default=None)
    accommodation_type: Optional[AccommodationTypeEnum] = Field(default=None)
    accommodation_address: Optional[str] = Field(default=None)
    accommodation_contact: Optional[str] = Field(default=None)
    accommodation_latitude: Optional[float] = Field(default=None)
    accommodation_longitude: Optional[float] = Field(default=None)

    # Transportation to/from the day's activities
    transport_mode: Optional[TransportModeEnum] = Field(default=None)
    transport_details: Optional[str] = Field(default=None)

    # Safety and notes
    risk_level: str = Field(default="low")  # low, medium, high
    safety_notes: Optional[str] = Field(default=None)
    special_instructions: Optional[str] = Field(default=None)

    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
