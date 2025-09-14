from pydantic import BaseModel, Field
from typing import Optional
from app.models.database.online_activity import PlaceTypeEnum


class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    place_type: PlaceTypeEnum
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="India", max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    duration_hours: Optional[int] = Field(None, ge=0, le=720)  # Max 30 days
    entry_fee: Optional[float] = Field(None, ge=0)
    best_season: Optional[str] = Field(None, max_length=100)
    wheelchair_accessible: bool = Field(default=False)
    safety_rating: Optional[int] = Field(None, ge=1, le=5)
    contact_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    opening_time: Optional[str] = Field(
        None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    closing_time: Optional[str] = Field(
        None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    is_featured: bool = Field(default=False)


class PlaceCreate(PlaceBase):
    pass


class PlaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    place_type: Optional[PlaceTypeEnum] = None
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    duration_hours: Optional[int] = Field(None, ge=0, le=720)
    entry_fee: Optional[float] = Field(None, ge=0)
    best_season: Optional[str] = Field(None, max_length=100)
    wheelchair_accessible: Optional[bool] = None
    safety_rating: Optional[int] = Field(None, ge=1, le=5)
    contact_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    website: Optional[str] = None
    opening_time: Optional[str] = Field(
        None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    closing_time: Optional[str] = Field(
        None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    )
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class PlaceResponse(PlaceBase):
    id: int
    is_active: bool
    created_by_admin_id: int
    created_at: int
    updated_at: int

    class Config:
        from_attributes = True


class PlaceSearchQuery(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    place_type: Optional[PlaceTypeEnum] = None
    is_featured: Optional[bool] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, ge=0, le=1000)  # Search within radius


class PlaceListResponse(BaseModel):
    places: list[PlaceResponse]
    total_count: int
    page: int
    page_size: int
