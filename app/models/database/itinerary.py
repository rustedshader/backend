from sqlmodel import SQLModel, Field, Relationship
from enum import Enum as PyEnum
from typing import Optional, List
import datetime


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
    trek_id: int = Field(foreign_key="treks.id", index=True)  # Link to predefined trek
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    start_date: datetime.date = Field(index=True)
    end_date: datetime.date = Field(index=True)
    total_duration_days: int = Field(index=True)
    estimated_budget: Optional[float] = Field(default=None)
    number_of_travelers: int = Field(default=1)
    purpose_of_visit: str = Field(
        default="tourism"
    )  # tourism, business, pilgrimage, etc.
    status: ItineraryStatusEnum = Field(default=ItineraryStatusEnum.DRAFT, index=True)

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
    submitted_at: Optional[int] = Field(default=None)
    approved_at: Optional[int] = Field(default=None)


class ItineraryDay(SQLModel, table=True):
    __tablename__ = "itinerary_days"

    id: int = Field(default=None, primary_key=True, index=True)
    itinerary_id: int = Field(foreign_key="itineraries.id", index=True)
    day_number: int = Field(index=True)
    date: datetime.date = Field(index=True)

    # Daily planning for the trek
    planned_activities: str  # What they plan to do on this day of the trek
    estimated_time_start: Optional[str] = Field(default=None)  # HH:MM format
    estimated_time_end: Optional[str] = Field(default=None)  # HH:MM format

    # Accommodation planning (where they'll stay during the trek)
    accommodation_name: Optional[str] = Field(default=None)
    accommodation_type: Optional[AccommodationTypeEnum] = Field(default=None)
    accommodation_address: Optional[str] = Field(default=None)
    accommodation_contact: Optional[str] = Field(default=None)

    # Transportation planning (how they'll get around during trek)
    transport_mode: Optional[TransportModeEnum] = Field(default=None)
    transport_details: Optional[str] = Field(
        default=None
    )  # flight number, train number, etc.
    estimated_time_end: Optional[str] = Field(default=None)  # HH:MM format

    # Accommodation
    accommodation_name: Optional[str] = Field(default=None)
    accommodation_type: Optional[AccommodationTypeEnum] = Field(default=None)
    accommodation_address: Optional[str] = Field(default=None)
    accommodation_contact: Optional[str] = Field(default=None)

    # Transportation
    transport_mode: Optional[TransportModeEnum] = Field(default=None)
    transport_details: Optional[str] = Field(
        default=None
    )  # flight number, train number, etc.

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
