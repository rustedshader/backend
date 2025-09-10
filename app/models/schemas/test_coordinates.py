from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TestCoordinatesCreate(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude coordinate", ge=-180, le=180)
    device_id: Optional[str] = Field(None, description="Optional device identifier")


class TestCoordinatesResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    timestamp: datetime
    device_id: Optional[str] = None

    class Config:
        from_attributes = True
