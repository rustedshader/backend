from pydantic import BaseModel, Field


class RoutingTestRequest(BaseModel):
    start_lat: float = Field(..., description="Starting latitude", ge=-90, le=90)
    start_lon: float = Field(..., description="Starting longitude", ge=-180, le=180)
    end_lat: float = Field(..., description="Ending latitude", ge=-90, le=90)
    end_lon: float = Field(..., description="Ending longitude", ge=-180, le=180)
    profile: str = Field(default="car", description="Transportation profile")
