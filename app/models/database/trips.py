from sqlmodel import Field, SQLModel
import datetime
from enum import Enum as PyEnum


class TripStatusEnum(str, PyEnum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Trips(SQLModel, table=True):
    __tablename__ = "trips"

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    status: TripStatusEnum = Field(default=TripStatusEnum.UPCOMING, index=True)
    blockchain_id: str = Field(index=True)
    blockchain_transaction_hash: str = Field(index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
