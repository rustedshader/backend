from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum as PyEnum


class RestrictedAreaStatusEnum(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TEMPORARILY_DISABLED = "temporarily_disabled"


class RestrictedAreaTypeEnum(str, PyEnum):
    RESTRICTED_ZONE = "restricted_zone"
    DANGER_ZONE = "danger_zone"
    PRIVATE_PROPERTY = "private_property"
    PROTECTED_AREA = "protected_area"
    MILITARY_ZONE = "military_zone"
    SEASONAL_CLOSURE = "seasonal_closure"


class PolygonCoordinate(BaseModel):
    """Single coordinate point [longitude, latitude]"""

    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")


class RestrictedAreaCreate(BaseModel):
    """Schema for creating a new restricted area"""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the restricted area"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Description of why this area is restricted"
    )
    area_type: RestrictedAreaTypeEnum = Field(
        ..., description="Type of restricted area"
    )

    # Polygon coordinates - array of coordinate points forming the boundary
    boundary_coordinates: List[PolygonCoordinate] = Field(
        ...,
        min_items=3,
        description="Array of coordinate points forming the polygon boundary (minimum 3 points)",
    )

    severity_level: int = Field(
        1, ge=1, le=5, description="Severity level from 1 (low) to 5 (high)"
    )
    restriction_reason: Optional[str] = Field(
        None, max_length=1000, description="Detailed reason for restriction"
    )
    contact_info: Optional[str] = Field(
        None, max_length=500, description="Contact information for queries"
    )

    # Validity period
    valid_from: Optional[datetime] = Field(
        None, description="When the restriction becomes active"
    )
    valid_until: Optional[datetime] = Field(
        None, description="When the restriction expires (null = permanent)"
    )

    # Enforcement settings
    send_warning_notification: bool = Field(
        True, description="Send warning when tourists approach this area"
    )
    auto_alert_authorities: bool = Field(
        False, description="Automatically alert authorities if tourists enter"
    )
    buffer_distance_meters: Optional[int] = Field(
        100, ge=0, le=10000, description="Warning buffer distance in meters"
    )


class RestrictedAreaUpdate(BaseModel):
    """Schema for updating an existing restricted area"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    area_type: Optional[RestrictedAreaTypeEnum] = None
    status: Optional[RestrictedAreaStatusEnum] = None

    boundary_coordinates: Optional[List[PolygonCoordinate]] = Field(None, min_items=3)

    severity_level: Optional[int] = Field(None, ge=1, le=5)
    restriction_reason: Optional[str] = Field(None, max_length=1000)
    contact_info: Optional[str] = Field(None, max_length=500)

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    send_warning_notification: Optional[bool] = None
    auto_alert_authorities: Optional[bool] = None
    buffer_distance_meters: Optional[int] = Field(None, ge=0, le=10000)


class RestrictedAreaResponse(BaseModel):
    """Schema for restricted area responses"""

    id: int
    name: str
    description: Optional[str]
    area_type: RestrictedAreaTypeEnum
    status: RestrictedAreaStatusEnum

    # Convert geometry to coordinate list for frontend
    boundary_coordinates: List[PolygonCoordinate]

    created_by_admin_id: int
    severity_level: int
    restriction_reason: Optional[str]
    contact_info: Optional[str]

    valid_from: Optional[datetime]
    valid_until: Optional[datetime]

    send_warning_notification: bool
    auto_alert_authorities: bool
    buffer_distance_meters: Optional[int]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RestrictedAreaSummary(BaseModel):
    """Simplified schema for listing restricted areas"""

    id: int
    name: str
    area_type: RestrictedAreaTypeEnum
    status: RestrictedAreaStatusEnum
    severity_level: int
    created_at: datetime

    class Config:
        from_attributes = True


class GeofenceCheckRequest(BaseModel):
    """Schema for checking if a location is within restricted areas"""

    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    user_id: Optional[int] = Field(None, description="User ID for logging violations")


class GeofenceCheckResponse(BaseModel):
    """Schema for geofence check results"""

    is_restricted: bool
    restricted_areas: List[RestrictedAreaSummary] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    severity_level: int = Field(
        0, description="Highest severity level of affected areas"
    )


class GeofenceViolationResponse(BaseModel):
    """Schema for geofence violation responses"""

    id: int
    user_id: int
    restricted_area_id: int
    trip_id: Optional[int]
    violation_type: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    notification_sent: bool
    authorities_alerted: bool
    severity_score: int
    notes: Optional[str]

    # Include restricted area details
    restricted_area_name: str
    restricted_area_type: RestrictedAreaTypeEnum

    class Config:
        from_attributes = True
