"""
Database models for location sharing with emergency contacts.
"""

from sqlmodel import SQLModel, Field
import datetime
from typing import Optional


class LocationShareHistory(SQLModel, table=True):
    """History of location shares with emergency contacts."""

    __tablename__ = "location_share_history"

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(index=True, description="User who shared the location")

    # Location data
    latitude: float = Field(description="Shared latitude")
    longitude: float = Field(description="Shared longitude")
    location_accuracy: Optional[float] = Field(
        default=None, description="GPS accuracy in meters"
    )

    # Sharing details
    shared_with_contacts: str = Field(description="JSON string of contacts shared with")
    message: str = Field(description="Message included with the share")
    emergency_level: str = Field(
        default="normal",
        description="Emergency level: normal, warning, urgent, emergency",
    )

    # Trip context (optional)
    trip_id: Optional[int] = Field(
        default=None, description="Associated trip ID if any"
    )
    trip_info: Optional[str] = Field(
        default=None, description="JSON string of trip details"
    )

    # Metadata
    share_method: str = Field(
        default="manual",
        description="How share was triggered: manual, automatic, emergency",
    )
    device_info: Optional[str] = Field(default=None, description="Device information")

    # Timestamps
    timestamp: int = Field(description="When location was recorded")
    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()),
        description="When share was created",
    )

    # Status tracking
    delivery_status: str = Field(
        default="pending",
        description="Delivery status: pending, sent, delivered, failed",
    )
    delivery_attempts: int = Field(default=0, description="Number of delivery attempts")
    last_delivery_attempt: Optional[int] = Field(
        default=None, description="Last delivery attempt timestamp"
    )
