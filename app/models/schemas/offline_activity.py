# Renamed from treks.py
from pydantic import BaseModel
from app.models.database.offline_activity import DifficultyLevelEnum
from typing import Optional, List, Tuple


class OfflineActivityCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location: str
    city: str
    district: str
    state: str
    duration: int  # duration in hours
    altitude: Optional[int] = None  # in meters
    nearest_town: Optional[str] = None
    best_season: Optional[str] = None
    permits_required: Optional[str] = None
    equipment_needed: Optional[str] = None
    safety_tips: Optional[str] = None
    minimum_age: Optional[int] = None
    maximum_age: Optional[int] = None
    guide_required: bool = True
    minimum_people: Optional[int] = None
    maximum_people: Optional[int] = None
    cost_per_person: Optional[float] = None
    difficulty_level: DifficultyLevelEnum


class OfflineActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    duration: Optional[int] = None  # duration in hours
    altitude: Optional[int] = None  # in meters
    nearest_town: Optional[str] = None
    best_season: Optional[str] = None
    permits_required: Optional[str] = None
    equipment_needed: Optional[str] = None
    safety_tips: Optional[str] = None
    minimum_age: Optional[int] = None
    maximum_age: Optional[int] = None
    guide_required: Optional[bool] = None
    minimum_people: Optional[int] = None
    maximum_people: Optional[int] = None
    cost_per_person: Optional[float] = None
    difficulty_level: Optional[DifficultyLevelEnum] = None


class OfflineActivityDataUpdate(BaseModel):
    offline_activity_id: int
    route_data: List[
        Tuple[float, float]
    ]  # List of (latitude, longitude) points representing the route


class OfflineActivityDataResponse(BaseModel):
    offline_activity_id: int
    created_at: int
    updated_at: int
    message: str = "Offline activity route data updated successfully"
