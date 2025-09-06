from sqlmodel import SQLModel, Field, Relationship
from enum import Enum as PyEnum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class DifficultyLevelEnum(str, PyEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Trek(SQLModel, table=True):
    __tablename__ = "treks"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    location: str = Field(index=True)
    city: str = Field(index=True)
    district: str = Field(index=True)
    state: str = Field(index=True)
    duration_days: int
    difficulty_level: DifficultyLevelEnum = Field(index=True)

    created_by_id: int = Field(foreign_key="users.id")
    created_by: Optional["User"] = Relationship(back_populates="treks")
