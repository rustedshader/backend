from sqlmodel import Field, SQLModel
import datetime
from typing import Optional
import secrets
import string


class LocationSharing(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)
    trip_id: int = Field(foreign_key="trips.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    share_code: str = Field(unique=True, index=True)
    is_active: bool = Field(default=True, index=True)
    expires_at: Optional[datetime.datetime] = Field(default=None, index=True)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    @classmethod
    def generate_share_code(cls, length: int = 12) -> str:
        """Generate a unique share code for location sharing"""
        characters = string.ascii_letters + string.digits
        return "".join(secrets.choice(characters) for _ in range(length))
