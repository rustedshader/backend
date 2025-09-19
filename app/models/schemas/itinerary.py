from pydantic import BaseModel, Field
from typing import Optional, List
import datetime


class ItineraryDayCreate(BaseModel):
    accommodation_id: int
    day_number: int
    offline_activity_id: Optional[int] = None
    online_activity_id: Optional[int] = None


class ItineraryDayUpdate(BaseModel):
    accommodation_id: Optional[int] = None
    day_number: Optional[int] = None
    offline_activity_id: Optional[int] = None
    online_activity_id: Optional[int] = None


class ItineraryDayResponse(BaseModel):
    id: int
    itinerary_id: int
    accommodation_id: int
    day_number: int
    offline_activity_id: Optional[int] = None
    online_activity_id: Optional[int] = None


class ItineraryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    destination_city: str = Field(..., min_length=1, max_length=100)
    destination_state: str = Field(..., min_length=1, max_length=100)
    start_date: datetime.date
    end_date: datetime.date
    total_duration_days: int = Field(..., gt=0, le=365)
    itinerary_days: Optional[List[ItineraryDayCreate]] = []


class ItineraryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    destination_city: Optional[str] = Field(None, min_length=1, max_length=100)
    destination_state: Optional[str] = Field(None, min_length=1, max_length=100)
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    total_duration_days: Optional[int] = Field(None, gt=0, le=365)


class ItineraryResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    destination_city: str
    destination_state: str
    start_date: datetime.date
    end_date: datetime.date
    total_duration_days: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    itinerary_days: Optional[List[ItineraryDayResponse]] = []


class ItineraryListResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    destination_city: str
    destination_state: str
    start_date: datetime.date
    end_date: datetime.date
    total_duration_days: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
