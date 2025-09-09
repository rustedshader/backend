from pydantic import BaseModel, model_validator
from typing import Optional, List
import datetime
from app.models.database.itinerary import (
    ItineraryStatusEnum,
    ItineraryTypeEnum,
    DayTypeEnum,
    TransportModeEnum,
    AccommodationTypeEnum,
)


class ItineraryDayCreate(BaseModel):
    day_number: int
    date: datetime.date
    day_type: DayTypeEnum  # Either TREK_DAY or PLACE_VISIT_DAY

    # For TREK_DAY
    trek_id: Optional[int] = None  # Required if day_type is TREK_DAY

    # For PLACE_VISIT_DAY
    primary_place_id: Optional[int] = None  # Required if day_type is PLACE_VISIT_DAY

    planned_activities: str  # What they plan to do on this day
    estimated_time_start: Optional[str] = None
    estimated_time_end: Optional[str] = None
    accommodation_name: Optional[str] = None
    accommodation_type: Optional[AccommodationTypeEnum] = None
    accommodation_address: Optional[str] = None
    accommodation_contact: Optional[str] = None
    accommodation_latitude: Optional[float] = None
    accommodation_longitude: Optional[float] = None
    transport_mode: Optional[TransportModeEnum] = None
    transport_details: Optional[str] = None
    safety_notes: Optional[str] = None
    special_instructions: Optional[str] = None

    @model_validator(mode="after")
    def validate_day_type(self):
        if self.day_type == DayTypeEnum.TREK_DAY:
            if not self.trek_id:
                raise ValueError("trek_id is required for TREK_DAY")
            # Clear primary_place_id for trek days
            self.primary_place_id = None
        elif self.day_type == DayTypeEnum.PLACE_VISIT_DAY:
            if not self.primary_place_id:
                raise ValueError("primary_place_id is required for PLACE_VISIT_DAY")
            # Clear trek_id for place visit days
            self.trek_id = None
        return self


class ItineraryDayResponse(BaseModel):
    id: int
    itinerary_id: int
    day_number: int
    date: datetime.date
    day_type: DayTypeEnum
    trek_id: Optional[int] = None
    primary_place_id: Optional[int] = None
    planned_activities: str
    estimated_time_start: Optional[str] = None
    estimated_time_end: Optional[str] = None
    accommodation_name: Optional[str] = None
    accommodation_type: Optional[AccommodationTypeEnum] = None
    accommodation_address: Optional[str] = None
    accommodation_contact: Optional[str] = None
    accommodation_latitude: Optional[float] = None
    accommodation_longitude: Optional[float] = None
    transport_mode: Optional[TransportModeEnum] = None
    transport_details: Optional[str] = None
    safety_notes: Optional[str] = None
    special_instructions: Optional[str] = None
    created_at: int
    updated_at: int

    class Config:
        from_attributes = True


class ItineraryCreate(BaseModel):
    itinerary_type: ItineraryTypeEnum
    trek_id: Optional[int] = None  # Required if itinerary_type is TREK
    primary_place_id: Optional[int] = None  # Required if itinerary_type is CITY_TOUR
    title: str
    description: Optional[str] = None
    destination_city: str
    destination_state: str
    destination_country: str = "India"
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

    @model_validator(mode="after")
    def validate_itinerary_type(self):
        if self.itinerary_type == ItineraryTypeEnum.TREK and not self.trek_id:
            raise ValueError("trek_id is required for TREK type itineraries")
        if (
            self.itinerary_type == ItineraryTypeEnum.CITY_TOUR
            and not self.primary_place_id
        ):
            raise ValueError(
                "primary_place_id is required for CITY_TOUR type itineraries"
            )
        if self.itinerary_type == ItineraryTypeEnum.MIXED and not (
            self.trek_id or self.primary_place_id
        ):
            raise ValueError(
                "Either trek_id or primary_place_id (or both) required for MIXED type itineraries"
            )
        return self


class ItineraryUpdate(BaseModel):
    itinerary_type: Optional[ItineraryTypeEnum] = None
    trek_id: Optional[int] = None
    primary_place_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    destination_city: Optional[str] = None
    destination_state: Optional[str] = None
    destination_country: Optional[str] = None
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
    itinerary_type: ItineraryTypeEnum
    trek_id: Optional[int] = None
    primary_place_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    destination_city: str
    destination_state: str
    destination_country: str
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
