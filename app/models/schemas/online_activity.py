# Renamed from places.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, time
from app.models.database.online_activity import OnlineActivityTypeEnum


class OnlineActivityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    place_type: OnlineActivityTypeEnum
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    cost_per_person: Optional[float] = Field(None, ge=0)
    wheelchair_accessible: bool = Field(default=False)
    safety_rating: Optional[int] = Field(None, ge=1, le=5)
    contact_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    opening_time: Optional[time] = Field(default=None)
    closing_time: Optional[time] = Field(default=None)


class OnlineActivityCreate(OnlineActivityBase):
    pass


class OnlineActivityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    place_type: Optional[OnlineActivityTypeEnum] = None
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    cost_per_person: Optional[float] = Field(None, ge=0)
    wheelchair_accessible: Optional[bool] = None
    safety_rating: Optional[int] = Field(None, ge=1, le=5)
    contact_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    website: Optional[str] = None
    opening_time: Optional[time] = Field(default=None)
    closing_time: Optional[time] = Field(default=None)
    is_active: Optional[bool] = None


class OnlineActivityResponse(OnlineActivityBase):
    id: int
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OnlineActivitySearchQuery(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Universal search query - searches across name, city, and state",
    )
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    place_type: Optional[OnlineActivityTypeEnum] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, ge=0, le=1000)  # Search within radius


class OnlineActivityListResponse(BaseModel):
    online_activities: list[OnlineActivityResponse]
    total_count: int
    page: int
    page_size: int
