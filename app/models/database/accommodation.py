from sqlmodel import SQLModel, Field
from typing import Optional


class Accommodation(SQLModel, table=True):
    __tablename__ = "accommodations"

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    address: str = Field(index=True)
    city: str = Field(index=True)
    state: str = Field(index=True)
    postal_code: str = Field(index=True)
    latitude: Optional[float] = Field(default=None, index=True)
    longitude: Optional[float] = Field(default=None, index=True)
