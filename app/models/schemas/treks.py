from pydantic import BaseModel, EmailStr
from app.models.database.treks import Trek, DifficultyLevelEnum
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
