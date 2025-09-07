from pydantic import BaseModel
from typing import Optional
import datetime


class TripCreate(BaseModel):
    treck_id: int
    guide_id: Optional[int]
    start_date: datetime.date
    end_date: datetime.date


class TripUpdate(BaseModel):
    guide_id: Optional[int]
    tracking_device_id: Optional[int]
    start_date: Optional[datetime.date]
    end_date: Optional[datetime.date]
    status: Optional[str]
