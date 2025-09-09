from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum as PyEnum


class AlertTypeEnum(str, PyEnum):
    DEVIATION = "deviation"
    EMERGENCY = "emergency"
    WEATHER = "weather"
    OTHER = "other"


class AlertStatusEnum(str, PyEnum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class AlertCreate(BaseModel):
    trip_id: int = Field(..., description="ID of the trip this alert belongs to")
    alert_type: AlertTypeEnum = Field(..., description="Type of alert")
    description: Optional[str] = Field(None, description="Description of the alert")
    location: AlertCoordinates = Field(..., description="Location where alert occurred")


class AlertUpdate(BaseModel):
    alert_type: Optional[AlertTypeEnum] = Field(None, description="Type of alert")
    description: Optional[str] = Field(None, description="Description of the alert")
    status: Optional[AlertStatusEnum] = Field(None, description="Status of the alert")


class AlertResponse(BaseModel):
    id: int
    trip_id: int
    timestamp: int
    alert_type: AlertTypeEnum
    description: Optional[str]
    location: AlertCoordinates
    status: AlertStatusEnum

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    per_page: int


class AlertStatsResponse(BaseModel):
    total_alerts: int
    new_alerts: int
    acknowledged_alerts: int
    resolved_alerts: int
    emergency_alerts: int
    deviation_alerts: int
    weather_alerts: int
    other_alerts: int
