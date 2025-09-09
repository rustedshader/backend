"""
Schemas for routing API endpoints.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class RouteProfileEnum(str, Enum):
    CAR = "car"
    FOOT = "foot"
    BIKE = "bike"


class RoutePoint(BaseModel):
    """A point with coordinates and optional metadata."""

    latitude: float
    longitude: float
    name: Optional[str] = None
    type: Optional[str] = None  # "hotel", "place", "trek_start", etc.


class RouteSegment(BaseModel):
    """A route segment between two points."""

    from_point: RoutePoint
    to_point: RoutePoint
    distance_meters: float
    distance_km: float
    time_seconds: int
    time_minutes: float
    time_hours: float
    geojson: Optional[Dict[str, Any]] = None  # Direct GeoJSON for easy integration
    coordinates: List[List[float]]  # Raw coordinates for backward compatibility
    instructions: List[Dict[str, Any]]
    bbox: List[float]
    segment_type: Optional[str] = None  # "outbound", "return", "transfer"


class ItineraryRouteRequest(BaseModel):
    """Request to generate routes for an itinerary."""

    itinerary_id: int
    profile: RouteProfileEnum = RouteProfileEnum.CAR
    include_coordinates: bool = True
    include_instructions: bool = True


class DayRoute(BaseModel):
    """Routes for a specific day of the itinerary."""

    day_number: int
    date: str
    day_type: str
    routes: List[RouteSegment]
    total_distance_km: float
    total_time_hours: float
    waypoints: List[RoutePoint]


class ItineraryRouteResponse(BaseModel):
    """Response containing all routes for an itinerary."""

    itinerary_id: int
    total_days: int
    total_distance_km: float
    total_time_hours: float
    profile: str
    day_routes: List[DayRoute]
