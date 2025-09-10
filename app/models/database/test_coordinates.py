from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class TestCoordinates(SQLModel, table=True):
    __tablename__ = "test_coordinates"

    id: Optional[int] = Field(default=None, primary_key=True)
    latitude: float = Field(description="Latitude coordinate")
    longitude: float = Field(description="Longitude coordinate")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the coordinates were recorded",
    )
    device_id: Optional[str] = Field(
        default=None, description="Optional device identifier"
    )
