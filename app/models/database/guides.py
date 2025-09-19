from sqlmodel import SQLModel, Field, Relationship
from enum import Enum as PyEnum
import datetime
from typing import Optional, List


class Guides(SQLModel, table=True):
    __tablename__ = "guides"

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
