from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RoutingTestRequest(BaseModel):
    start_lat: float = Field(..., description="Starting latitude", ge=-90, le=90)
    start_lon: float = Field(..., description="Starting longitude", ge=-180, le=180)
    end_lat: float = Field(..., description="Ending latitude", ge=-90, le=90)
    end_lon: float = Field(..., description="Ending longitude", ge=-180, le=180)
    profile: str = Field(default="car", description="Transportation profile")


class GeoJSONGeometry(BaseModel):
    type: str
    coordinates: List[List[float]]


class RoutingTestResponse(BaseModel):
    geojson: Dict[str, Any]
    route_summary: Dict[str, Any]
    blocked_areas_count: int
    blocked_areas: List[str]
    request_details: Dict[str, Any]
    debug_info: Optional[Dict[str, Any]] = None
