# Renamed from treks.py
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.database.offline_activity import DifficultyLevelEnum
from typing import Optional, List, Tuple


class OfflineActivityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    city: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    duration: Optional[int] = Field(None, ge=1)  # duration in hours
    altitude: Optional[int] = Field(None, ge=0)  # in meters
    nearest_town: Optional[str] = Field(None, max_length=100)
    best_season: Optional[str] = Field(None, max_length=100)
    permits_required: Optional[str] = Field(None, max_length=500)
    equipment_needed: Optional[str] = Field(None, max_length=500)
    safety_tips: Optional[str] = Field(None, max_length=1000)
    minimum_age: Optional[int] = Field(None, ge=1, le=100)
    maximum_age: Optional[int] = Field(None, ge=1, le=100)
    guide_required: bool = Field(default=True)
    minimum_people: Optional[int] = Field(None, ge=1)
    maximum_people: Optional[int] = Field(None, ge=1)
    cost_per_person: Optional[float] = Field(None, ge=0)
    difficulty_level: DifficultyLevelEnum


class OfflineActivityCreate(OfflineActivityBase):
    pass


class OfflineActivityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    district: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    duration: Optional[int] = Field(None, ge=1)  # duration in hours
    altitude: Optional[int] = Field(None, ge=0)  # in meters
    nearest_town: Optional[str] = Field(None, max_length=100)
    best_season: Optional[str] = Field(None, max_length=100)
    permits_required: Optional[str] = Field(None, max_length=500)
    equipment_needed: Optional[str] = Field(None, max_length=500)
    safety_tips: Optional[str] = Field(None, max_length=1000)
    minimum_age: Optional[int] = Field(None, ge=1, le=100)
    maximum_age: Optional[int] = Field(None, ge=1, le=100)
    guide_required: Optional[bool] = None
    minimum_people: Optional[int] = Field(None, ge=1)
    maximum_people: Optional[int] = Field(None, ge=1)
    cost_per_person: Optional[float] = Field(None, ge=0)
    difficulty_level: Optional[DifficultyLevelEnum] = None


class OfflineActivityDataUpdate(BaseModel):
    offline_activity_id: int
    route_data: List[
        Tuple[float, float]
    ]  # List of (latitude, longitude) points representing the route


class OfflineActivityResponse(OfflineActivityBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OfflineActivitySearchQuery(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Universal search query - searches across name, city, and state",
    )
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    difficulty_level: Optional[DifficultyLevelEnum] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, ge=0, le=1000)  # Search within radius


class OfflineActivityListResponse(BaseModel):
    activities: List[OfflineActivityResponse]
    total_count: int
    page: int
    page_size: int


class OfflineActivityDataResponse(BaseModel):
    offline_activity_id: int
    created_at: datetime
    updated_at: datetime
    message: str = "Offline activity route data updated successfully"
