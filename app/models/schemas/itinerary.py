from pydantic import BaseModel
from typing import Optional, List
import datetime
from app.models.database.itinerary import (
    ItineraryStatusEnum,
    TransportModeEnum,
    AccommodationTypeEnum,
)


class ItineraryDayCreate(BaseModel):
    day_number: int
    date: datetime.date
    planned_activities: str  # What they plan to do on this day of the trek
    estimated_time_start: Optional[str] = None
    estimated_time_end: Optional[str] = None
    accommodation_name: Optional[str] = None
    accommodation_type: Optional[AccommodationTypeEnum] = None
    accommodation_address: Optional[str] = None
    accommodation_contact: Optional[str] = None
    transport_mode: Optional[TransportModeEnum] = None
    transport_details: Optional[str] = None
    safety_notes: Optional[str] = None
    special_instructions: Optional[str] = None


class ItineraryDayResponse(BaseModel):
    id: int
    itinerary_id: int
    day_number: int
    date: datetime.date
    planned_activities: str
    estimated_time_start: Optional[str] = None
    estimated_time_end: Optional[str] = None
    accommodation_name: Optional[str] = None
    accommodation_type: Optional[AccommodationTypeEnum] = None
    accommodation_address: Optional[str] = None
    accommodation_contact: Optional[str] = None
    transport_mode: Optional[TransportModeEnum] = None
    transport_details: Optional[str] = None
    safety_notes: Optional[str] = None
    special_instructions: Optional[str] = None
    created_at: int
    updated_at: int

    class Config:
        from_attributes = True


class ItineraryCreate(BaseModel):
    trek_id: int  # Select from predefined treks
    title: str
    description: Optional[str] = None
    start_date: datetime.date
    end_date: datetime.date
    estimated_budget: Optional[float] = None
    number_of_travelers: int = 1
    purpose_of_visit: str = "tourism"
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relation: str = "family"
    preferred_language: Optional[str] = "english"
    special_requirements: Optional[str] = None
    itinerary_days: List[ItineraryDayCreate]


class ItineraryUpdate(BaseModel):
    trek_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    estimated_budget: Optional[float] = None
    number_of_travelers: Optional[int] = None
    purpose_of_visit: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    preferred_language: Optional[str] = None
    special_requirements: Optional[str] = None
    status: Optional[ItineraryStatusEnum] = None


class ItineraryResponse(BaseModel):
    id: int
    user_id: int
    trek_id: int
    title: str
    description: Optional[str] = None
    start_date: datetime.date
    end_date: datetime.date
    total_duration_days: int
    estimated_budget: Optional[float] = None
    number_of_travelers: int
    purpose_of_visit: str
    status: ItineraryStatusEnum
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relation: str
    preferred_language: Optional[str] = None
    special_requirements: Optional[str] = None
    created_at: int
    updated_at: int
    submitted_at: Optional[int] = None
    approved_at: Optional[int] = None
    itinerary_days: List[ItineraryDayResponse] = []

    class Config:
        from_attributes = True


class ItineraryListResponse(BaseModel):
    itineraries: List[ItineraryResponse]
    total: int


class ItineraryStatusUpdate(BaseModel):
    status: ItineraryStatusEnum
