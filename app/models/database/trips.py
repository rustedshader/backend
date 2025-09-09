from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column
from typing import Any


class TripStatusEnum(str, PyEnum):
    ASSIGNED = "assigned"
    STARTED = "started"  # Day started, going to destination
    VISITING = "visiting"  # At tourist location/trek
    RETURNING = "returning"  # Coming back to hotel
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TripTypeEnum(str, PyEnum):
    TREK_DAY = "trek_day"
    TOUR_DAY = "tour_day"


class LocationSourceEnum(str, PyEnum):
    MOBILE_GPS = "mobile_gps"
    TRACKING_DEVICE = "tracking_device"
    MANUAL = "manual"


class TrekPhaseEnum(str, PyEnum):
    TO_TREK_START = "to_trek_start"  # Mobile GPS: Hotel → Trek Start
    TREK_ACTIVE = "trek_active"  # Tracking Device: Trek Start → Trek End
    FROM_TREK_END = "from_trek_end"  # Mobile GPS: Trek End → Hotel


class TourPhaseEnum(str, PyEnum):
    TO_DESTINATION = "to_destination"  # Mobile GPS: Hotel → Tourist Location
    AT_DESTINATION = "at_destination"  # Mobile GPS: At tourist location
    TO_HOTEL = "to_hotel"  # Mobile GPS: Tourist Location → Hotel


class Trips(SQLModel, table=True):
    __tablename__ = "trips"
    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    itinerary_id: Optional[int] = Field(foreign_key="itineraries.id", index=True)
    trek_id: Optional[int] = Field(foreign_key="treks.id", index=True, default=None)
    guide_id: Optional[int] = Field(foreign_key="guides.id", index=True)
    tracking_deivce_id: Optional[int] = Field(
        foreign_key="tracking_devices.id", index=True
    )
    start_date: datetime.date = Field(index=True)
    end_date: datetime.date = Field(index=True)
    status: TripStatusEnum = Field(default=TripStatusEnum.ASSIGNED, index=True)

    # New fields for enhanced tracking
    trip_type: TripTypeEnum = Field(index=True)
    current_phase: Optional[str] = Field(
        default=None, index=True
    )  # Can be TrekPhaseEnum or TourPhaseEnum
    hotel_latitude: Optional[float] = Field(default=None, index=True)
    hotel_longitude: Optional[float] = Field(default=None, index=True)
    hotel_name: Optional[str] = Field(default=None)
    destination_latitude: Optional[float] = Field(default=None, index=True)
    destination_longitude: Optional[float] = Field(default=None, index=True)
    destination_name: Optional[str] = Field(default=None)

    # Trek-specific fields
    trek_start_latitude: Optional[float] = Field(default=None, index=True)
    trek_start_longitude: Optional[float] = Field(default=None, index=True)
    trek_end_latitude: Optional[float] = Field(default=None, index=True)
    trek_end_longitude: Optional[float] = Field(default=None, index=True)

    # Tracking status
    tracking_started_at: Optional[datetime.datetime] = Field(default=None, index=True)
    tracking_ended_at: Optional[datetime.datetime] = Field(default=None, index=True)
    is_tracking_active: bool = Field(default=False, index=True)

    # Device linking for treks
    linked_device_id: Optional[str] = Field(default=None, index=True)
    device_linked_at: Optional[datetime.datetime] = Field(default=None, index=True)


class LocationHistory(SQLModel, table=True):
    __tablename__ = "location_history"
    id: int = Field(default=None, primary_key=True, index=True)
    trip_id: int = Field(foreign_key="trips.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    timestamp: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    location: Any = Field(sa_column=Column(Geometry(geometry_type="POINT", srid=4326)))

    # Enhanced tracking fields
    latitude: float = Field(index=True)
    longitude: float = Field(index=True)
    altitude: Optional[float] = Field(default=None)
    accuracy: Optional[float] = Field(default=None)  # GPS accuracy in meters
    speed: Optional[float] = Field(default=None)  # speed in m/s
    bearing: Optional[float] = Field(default=None)  # direction in degrees

    # Source and context
    source: LocationSourceEnum = Field(index=True)
    trip_phase: Optional[str] = Field(
        default=None, index=True
    )  # Can be TrekPhaseEnum or TourPhaseEnum
    device_id: Optional[str] = Field(default=None, index=True)

    # Battery and signal info
    battery_level: Optional[int] = Field(default=None)  # percentage
    signal_strength: Optional[int] = Field(default=None)  # signal strength

    # Additional metadata
    notes: Optional[str] = Field(default=None)
    is_waypoint: bool = Field(default=False, index=True)  # Important location marker


class TrekPath(SQLModel, table=True):
    __tablename__ = "trek_paths"
    id: int = Field(default=None, primary_key=True, index=True)
    trek_id: int = Field(foreign_key="treks.id", index=True)
    name: str = Field(index=True)  # e.g., "Main Route", "Alternative Route"
    description: Optional[str] = Field(default=None)

    # Path data
    path_coordinates: Any = Field(
        sa_column=Column(Geometry(geometry_type="LINESTRING", srid=4326))
    )
    total_distance_meters: float = Field(index=True)
    estimated_duration_hours: float = Field(index=True)
    elevation_gain_meters: Optional[float] = Field(default=None)
    difficulty_rating: Optional[int] = Field(default=None)  # 1-10 scale

    # Waypoints along the trek
    waypoints: Optional[str] = Field(default=None)  # JSON string of important points
    safety_notes: Optional[str] = Field(default=None)

    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    is_active: bool = Field(default=True, index=True)


class RouteSegment(SQLModel, table=True):
    __tablename__ = "route_segments"
    id: int = Field(default=None, primary_key=True, index=True)
    trip_id: int = Field(foreign_key="trips.id", index=True)

    # Segment information
    segment_type: str = Field(
        index=True
    )  # "hotel_to_trek", "trek_route", "trek_to_hotel", "tour_route"
    start_timestamp: int = Field(index=True)
    end_timestamp: Optional[int] = Field(default=None, index=True)

    # Geographic data
    start_latitude: float = Field(index=True)
    start_longitude: float = Field(index=True)
    end_latitude: Optional[float] = Field(default=None, index=True)
    end_longitude: Optional[float] = Field(default=None, index=True)

    # Route statistics
    total_distance_meters: Optional[float] = Field(default=None)
    total_duration_seconds: Optional[int] = Field(default=None)
    max_speed_ms: Optional[float] = Field(default=None)
    avg_speed_ms: Optional[float] = Field(default=None)

    # Trek-specific data
    trek_path_id: Optional[int] = Field(
        foreign_key="trek_paths.id", index=True, default=None
    )

    # Status
    is_completed: bool = Field(default=False, index=True)
    notes: Optional[str] = Field(default=None)


class AlertTypeEnum(str, PyEnum):
    DEVIATION = "deviation"
    EMERGENCY = "emergency"
    WEATHER = "weather"
    OTHER = "other"


class AlertStatusEnum(str, PyEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alerts(SQLModel, table=True):
    __tablename__ = "alerts"
    id: int = Field(default=None, primary_key=True, index=True)
    trip_id: int = Field(foreign_key="trips.id", index=True)
    timestamp: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    alert_type: AlertTypeEnum = Field(index=True)
    description: Optional[str] = Field(default=None)
    location: Any = Field(sa_column=Column(Geometry(geometry_type="POINT", srid=4326)))
    status: AlertStatusEnum = Field(default=AlertStatusEnum.NEW, index=True)
