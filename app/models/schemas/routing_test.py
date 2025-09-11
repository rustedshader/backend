from pydantic import BaseModel, Field


class RoutingTestRequest(BaseModel):
    start_lat: float = Field(..., description="Starting latitude", ge=-90, le=90)
    start_lon: float = Field(..., description="Starting longitude", ge=-180, le=180)
    end_lat: float = Field(..., description="Ending latitude", ge=-90, le=90)
    end_lon: float = Field(..., description="Ending longitude", ge=-180, le=180)
    profile: str = Field(default="car", description="Transportation profile")


class RoutingTestResponse(BaseModel):
    route_summary: dict
    raw_route_data: dict
    blocked_areas_count: int
    blocked_areas: list
    request_details: dict
