from pydantic import BaseModel, Field
from typing import Optional
import datetime


class LocationSharingCreate(BaseModel):
    """Schema for creating a location sharing request"""

    trip_id: int
    expires_in_hours: Optional[int] = Field(
        default=24, ge=1, le=168
    )  # 1 hour to 1 week


class LocationSharingResponse(BaseModel):
    """Schema for location sharing response"""

    id: int
    trip_id: int
    user_id: int
    share_code: str
    is_active: bool
    expires_at: Optional[datetime.datetime]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class SharedLocationResponse(BaseModel):
    """Schema for shared location data response"""

    user_id: int
    trip_id: int
    current_location: Optional[dict] = None  # {"latitude": float, "longitude": float}
    last_updated: Optional[datetime.datetime] = None
    trip_status: str


class LocationSharingUpdate(BaseModel):
    """Schema for updating location sharing settings"""

    is_active: Optional[bool] = None
    expires_in_hours: Optional[int] = Field(default=None, ge=1, le=168)


class ShareCodeValidation(BaseModel):
    """Schema for validating share codes"""

    share_code: str
