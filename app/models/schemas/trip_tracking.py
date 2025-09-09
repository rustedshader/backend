"""
Enhanced schemas for trip tracking and GPS data.
"""

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
import datetime


class TripTypeEnum(str, Enum):
    TREK_DAY = "trek_day"
    TOUR_DAY = "tour_day"


class LocationSourceEnum(str, Enum):
    MOBILE_GPS = "mobile_gps"
    TRACKING_DEVICE = "tracking_device"
    MANUAL = "manual"


class TrekPhaseEnum(str, Enum):
    TO_TREK_START = "to_trek_start"  # Mobile GPS: Hotel → Trek Start
    TREK_ACTIVE = "trek_active"  # Tracking Device: Trek Start → Trek End
    FROM_TREK_END = "from_trek_end"  # Mobile GPS: Trek End → Hotel


class TourPhaseEnum(str, Enum):
    TO_DESTINATION = "to_destination"  # Mobile GPS: Hotel → Tourist Location
    AT_DESTINATION = "at_destination"  # Mobile GPS: At tourist location
    TO_HOTEL = "to_hotel"  # Mobile GPS: Tourist Location → Hotel


class TripStatusEnum(str, Enum):
    ASSIGNED = "assigned"
    STARTED = "started"  # Day started, going to destination
    VISITING = "visiting"  # At tourist location/trek
    RETURNING = "returning"  # Coming back to hotel
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LocationPoint(BaseModel):
    """A single GPS location point."""

    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    bearing: Optional[float] = None
    timestamp: int
    source: LocationSourceEnum
    device_id: Optional[str] = None
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None


class LocationBatch(BaseModel):
    """Batch of location points for efficient upload."""

    trip_id: int
    user_id: int
    trip_phase: Optional[str] = None  # Can be TrekPhaseEnum or TourPhaseEnum
    locations: List[LocationPoint]
    notes: Optional[str] = None


class DeviceLinkRequest(BaseModel):
    """Request to link tracking device for trek."""

    trip_id: int
    device_id: str
    device_type: str = "gps_tracker"


class StartDayRequest(BaseModel):
    """Request to start the day (tour or trek)."""

    trip_id: int
    trip_type: TripTypeEnum
    hotel_coordinates: tuple[float, float]
    hotel_name: str
    destination_coordinates: Optional[tuple[float, float]] = None
    destination_name: Optional[str] = None


class StartTrekRequest(BaseModel):
    """Request to start trek with linked device."""

    trip_id: int
    device_id: str
    trek_start_coordinates: tuple[float, float]


class EndTrekRequest(BaseModel):
    """Request to end trek and get return route."""

    trip_id: int
    trek_end_coordinates: tuple[float, float]


class RequestReturnRouteRequest(BaseModel):
    """Request route back to hotel."""

    trip_id: int
    current_coordinates: tuple[float, float]


class TrekPathData(BaseModel):
    """Pre-made trek path information."""

    id: int
    trek_id: int
    name: str
    description: Optional[str] = None
    total_distance_meters: float
    estimated_duration_hours: float
    elevation_gain_meters: Optional[float] = None
    difficulty_rating: Optional[int] = None
    waypoints: Optional[List[dict]] = None  # Important points along the route
    safety_notes: Optional[str] = None


class TripTrackingUpdate(BaseModel):
    """Update trip tracking status."""

    trip_id: int
    current_phase: Optional[TrekPhaseEnum] = None
    is_tracking_active: bool
    hotel_coordinates: Optional[tuple[float, float]] = None
    destination_coordinates: Optional[tuple[float, float]] = None


class RouteSegmentData(BaseModel):
    """Route segment information."""

    id: int
    trip_id: int
    segment_type: str
    start_timestamp: int
    end_timestamp: Optional[int] = None
    start_coordinates: tuple[float, float]
    end_coordinates: Optional[tuple[float, float]] = None
    total_distance_meters: Optional[float] = None
    total_duration_seconds: Optional[int] = None
    is_completed: bool


class TripTrackingStats(BaseModel):
    """Trip tracking statistics."""

    trip_id: int
    total_distance_meters: float
    total_duration_seconds: int
    avg_speed_ms: float
    max_speed_ms: float
    locations_recorded: int
    segments_completed: int
    current_phase: Optional[TrekPhaseEnum] = None
    tracking_started_at: Optional[datetime.datetime] = None
    tracking_ended_at: Optional[datetime.datetime] = None


class LiveLocationUpdate(BaseModel):
    """Real-time location update for live tracking."""

    trip_id: int
    user_id: int
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    bearing: Optional[float] = None
    timestamp: int
    source: LocationSourceEnum = LocationSourceEnum.MOBILE_GPS
    trip_phase: Optional[str] = None  # Can be TrekPhaseEnum or TourPhaseEnum
    emergency: bool = False


class TripRouteResponse(BaseModel):
    """Complete trip route information."""

    trip_id: int
    trip_type: TripTypeEnum
    segments: List[RouteSegmentData]
    total_stats: TripTrackingStats
    trek_path: Optional[TrekPathData] = None
    location_history: List[LocationPoint]
