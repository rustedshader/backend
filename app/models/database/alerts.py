from sqlmodel import SQLModel, Field
from enum import Enum as PyEnum
from typing import Optional, Any
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column


class AlertTypeEnum(str, PyEnum):
    EMERGENCY = "emergency"
    HELP_NEEDED = "help_needed"
    SAFETY_CONCERN = "safety_concern"
    LOST = "lost"
    MEDICAL = "medical"
    ACCIDENT = "accident"


class AlertStatusEnum(str, PyEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    message: str = Field(max_length=500)  # Simple message from user
    alert_type: AlertTypeEnum = Field(index=True)
    status: AlertStatusEnum = Field(default=AlertStatusEnum.ACTIVE, index=True)

    # Location information (required)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), index=True)
    )

    # User who created the alert
    created_by: int = Field(foreign_key="users.id", index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    # Admin who resolved (optional)
    resolved_by: Optional[int] = Field(default=None, foreign_key="users.id")
    resolved_at: Optional[datetime.datetime] = Field(default=None)
