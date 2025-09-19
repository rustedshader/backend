from sqlmodel import SQLModel, Field
import datetime


class TrackingDevice(SQLModel, table=True):
    __tablename__ = "tracking_devices"

    id: int = Field(default=None, primary_key=True, index=True)
    api_key: str = Field(index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
