from pydantic import BaseModel
from app.models.database.treks import DifficultyLevelEnum
from typing import Optional


class TrekCreate(BaseModel):
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


class TrekUpdate(BaseModel):
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
