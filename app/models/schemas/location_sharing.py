"""
Schemas for location sharing with emergency contacts.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class ShareLocationRequest(BaseModel):
    """Request to share location with emergency contacts."""

    latitude: float = Field(..., description="Current latitude")
    longitude: float = Field(..., description="Current longitude")
    message: Optional[str] = Field(
        default="Sharing my current location with you for safety.",
        description="Custom message to include with location",
    )
    include_trip_details: bool = Field(
        default=True, description="Whether to include current trip information"
    )
    emergency_level: str = Field(
        default="normal",
        description="Emergency level: normal, warning, urgent, emergency",
    )


class ShareLocationWithContactRequest(BaseModel):
    """Request to share location with specific contact(s)."""

    latitude: float = Field(..., description="Current latitude")
    longitude: float = Field(..., description="Current longitude")
    contact_phone: str = Field(..., description="Emergency contact phone number")
    contact_name: Optional[str] = Field(default=None, description="Contact name")
    message: Optional[str] = Field(
        default="Sharing my current location with you for safety.",
        description="Custom message to include with location",
    )
    include_trip_details: bool = Field(
        default=True, description="Whether to include current trip information"
    )
    emergency_level: str = Field(
        default="normal",
        description="Emergency level: normal, warning, urgent, emergency",
    )


class LocationShareResponse(BaseModel):
    """Response after sharing location."""

    success: bool
    message: str
    shared_with: List[str]  # List of contact names/phones
    location: dict  # Shared location data
    timestamp: int
    share_id: Optional[str] = None  # For tracking the share


class EmergencyContactInfo(BaseModel):
    """Emergency contact information."""

    name: str
    phone: str
    relation: str


class UserLocationInfo(BaseModel):
    """User location information for sharing."""

    user_id: int
    user_name: str
    user_phone: str
    latitude: float
    longitude: float
    location_accuracy: Optional[float] = None
    timestamp: int
    emergency_level: str
    message: str
    trip_info: Optional[dict] = None


class LocationShareHistory(BaseModel):
    """Historical location share record."""

    id: int
    user_id: int
    shared_with_contacts: List[str]
    latitude: float
    longitude: float
    message: str
    emergency_level: str
    timestamp: int
    created_at: int
