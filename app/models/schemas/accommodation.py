from pydantic import BaseModel, Field
from typing import Optional


class AccommodationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class AccommodationCreate(AccommodationBase):
    pass


class AccommodationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=1, max_length=20)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)


class AccommodationResponse(AccommodationBase):
    id: int

    class Config:
        from_attributes = True


class AccommodationSearchQuery(BaseModel):
    query: Optional[str] = Field(
        None,
        description="Universal search query - searches across name, city, and state",
    )
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, ge=0, le=1000)  # Search within radius


class AccommodationListResponse(BaseModel):
    accommodations: list[AccommodationResponse]
    total_count: int
    page: int
    page_size: int


class AccommodationDataResponse(BaseModel):
    success: bool
    data: AccommodationListResponse
    message: str
