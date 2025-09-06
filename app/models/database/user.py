from sqlmodel import SQLModel, Field, Relationship
from enum import Enum as PyEnum
from typing import Optional, List, TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from .trek import Trek


class UserRoleEnum(str, PyEnum):
    ADMIN = "admin"
    USER = "user"
    SUPER_ADMIN = "super_admin"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    first_name: str = Field(index=True)
    middle_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    email: str = Field(unique=True, index=True)
    password_hash: str
    country_code: str = Field(index=True)
    phone_number: str = Field(unique=True, index=True)
    indian_citizenship: bool = Field(default=False)
    aadhar_number_hash: Optional[str] = Field(default=None)
    passport_number_hash: Optional[str] = Field(default=None)
    blockchain_address: Optional[str] = Field(default=None)
    is_kyc_verified: bool = Field(default=False)
    is_email_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    role: UserRoleEnum = Field(default=UserRoleEnum.USER)

    # Relationships
    treks: List["Trek"] = Relationship(back_populates="created_by")


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(index=True)
    token: str = Field(unique=True, index=True)
    is_revoked: bool = Field(default=False)
    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp())
    )
    expires_at: int
