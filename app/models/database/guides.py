from sqlmodel import SQLModel, Field, Relationship
from enum import Enum as PyEnum
import datetime
from typing import Optional, List


class GuideSpecialtyEnum(str, PyEnum):
    MOUNTAIN_TREKKING = "mountain_trekking"
    WILDLIFE_SAFARI = "wildlife_safari"
    CULTURAL_HERITAGE = "cultural_heritage"
    HISTORICAL_SITES = "historical_sites"
    NATURE_WALKS = "nature_walks"
    PHOTOGRAPHY = "photography"
    SPIRITUAL_TOURS = "spiritual_tours"


class GuideCertificationLevelEnum(str, PyEnum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Guides(SQLModel, table=True):
    __tablename__ = "guides"

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    specialties: Optional[str] = Field(
        default=None, description="Comma-separated list of specialties"
    )
    years_of_experience: Optional[int] = Field(default=None)
    certification_level: Optional[GuideCertificationLevelEnum] = Field(
        default=GuideCertificationLevelEnum.BASIC
    )
    certification_number: Optional[str] = Field(default=None)
    languages_spoken: Optional[str] = Field(
        default=None, description="Comma-separated list of languages"
    )
    preferred_trek_regions: Optional[str] = Field(
        default=None, description="Comma-separated list of regions"
    )
    max_group_size: Optional[int] = Field(default=None)
    daily_rate: Optional[float] = Field(default=None)
    license_number: Optional[str] = Field(default=None)
    insurance_valid_until: Optional[datetime.date] = Field(default=None)
    emergency_contact_name: Optional[str] = Field(default=None)
    emergency_contact_phone: Optional[str] = Field(default=None)
    average_rating: Optional[float] = Field(default=0.0)
    total_reviews: int = Field(default=0)
    total_treks_completed: int = Field(default=0)
    is_available: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    profile_completion_percentage: Optional[int] = Field(default=0)
    created_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp())
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp())
    )
    treks: List["GuideTrek"] = Relationship(back_populates="guide")


class GuideTrek(SQLModel, table=True):
    """Junction table for many-to-many relationship between guides and treks"""

    __tablename__ = "guide_treks"

    id: int = Field(default=None, primary_key=True, index=True)
    guide_id: int = Field(foreign_key="guides.id", index=True)
    trek_id: int = Field(foreign_key="treks.id", index=True)
    assigned_at: int = Field(
        default_factory=lambda: int(datetime.datetime.utcnow().timestamp()), index=True
    )
    is_active: bool = Field(default=True, index=True)
    status: Optional[str] = Field(
        default="assigned"
    )  # assigned, in_progress, completed, cancelled
    notes: Optional[str] = Field(default=None)
    guide: "Guides" = Relationship(back_populates="treks")
