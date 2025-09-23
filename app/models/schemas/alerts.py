from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.database.alerts import AlertTypeEnum, AlertStatusEnum


class AlertBase(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    alert_type: AlertTypeEnum
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    status: AlertStatusEnum
    created_by: int
    created_at: datetime
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertSearchQuery(BaseModel):
    alert_type: Optional[AlertTypeEnum] = None
    status: Optional[AlertStatusEnum] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, ge=0, le=100)
    is_active_only: bool = Field(default=True)


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total_count: int
    page: int
    page_size: int


class AlertStatsResponse(BaseModel):
    total_alerts: int
    active_alerts: int
    alerts_by_type: dict
    alerts_by_status: dict
