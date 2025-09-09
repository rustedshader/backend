from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column
from typing import Any


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


class RestrictedAreas(SQLModel, table=True):
    __tablename__ = "restricted_areas"

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True, description="Name of the restricted area")
    description: Optional[str] = Field(
        default=None, description="Description of why this area is restricted"
    )
    area_type: RestrictedAreaTypeEnum = Field(
        index=True, description="Type of restricted area"
    )
    status: RestrictedAreaStatusEnum = Field(
        default=RestrictedAreaStatusEnum.ACTIVE, index=True
    )

    # Geographic polygon boundary - using POLYGON geometry type
    boundary: Any = Field(
        sa_column=Column(
            Geometry(
                geometry_type="POLYGON",
                srid=4326,
                dimension=2,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            )
        ),
        description="Polygon boundary of the restricted area",
    )

    # Administrative details
    created_by_admin_id: int = Field(
        foreign_key="users.id",
        index=True,
        description="Admin who created this restricted area",
    )
    severity_level: int = Field(
        default=1, ge=1, le=5, description="Severity level from 1 (low) to 5 (high)"
    )

    # Additional metadata
    restriction_reason: Optional[str] = Field(
        default=None, description="Detailed reason for restriction"
    )
    contact_info: Optional[str] = Field(
        default=None, description="Contact information for queries about this area"
    )
    valid_from: Optional[datetime.datetime] = Field(
        default=None, description="When the restriction becomes active"
    )
    valid_until: Optional[datetime.datetime] = Field(
        default=None, description="When the restriction expires (null = permanent)"
    )

    # Timestamps
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        index=True,
        description="When this restricted area was created",
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        index=True,
        description="When this restricted area was last updated",
    )

    # Enforcement options
    send_warning_notification: bool = Field(
        default=True, description="Send warning when tourists approach this area"
    )
    auto_alert_authorities: bool = Field(
        default=False, description="Automatically alert authorities if tourists enter"
    )
    buffer_distance_meters: Optional[int] = Field(
        default=100, description="Warning buffer distance in meters"
    )


class GeofenceViolations(SQLModel, table=True):
    __tablename__ = "geofence_violations"

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    restricted_area_id: int = Field(foreign_key="restricted_areas.id", index=True)
    trip_id: Optional[int] = Field(foreign_key="trips.id", index=True)

    # Violation details
    violation_type: str = Field(
        index=True,
        description="Type of violation: 'entry', 'approach_warning', 'prolonged_stay'",
    )
    violation_location: Any = Field(
        sa_column=Column(
            Geometry(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            )
        ),
        description="Exact location where violation occurred",
    )

    # Timestamps
    detected_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        index=True,
        description="When the violation was detected",
    )
    resolved_at: Optional[datetime.datetime] = Field(
        default=None, description="When the violation was resolved"
    )

    # Response details
    notification_sent: bool = Field(
        default=False, description="Whether notification was sent to user"
    )
    authorities_alerted: bool = Field(
        default=False, description="Whether authorities were alerted"
    )
    severity_score: int = Field(
        default=1, ge=1, le=5, description="Calculated severity score"
    )

    # Additional context
    notes: Optional[str] = Field(
        default=None, description="Additional notes about the violation"
    )
    resolved_by_admin_id: Optional[int] = Field(
        foreign_key="users.id",
        default=None,
        description="Admin who resolved the violation",
    )
