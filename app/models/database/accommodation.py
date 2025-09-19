from sqlmodel import SQLModel, Field
from typing import Any
from geoalchemy2 import Geometry
from sqlalchemy import Column


class Accommodation(SQLModel, table=True):
    __tablename__ = "accommodations"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    address: str = Field(index=True)
    city: str = Field(index=True)
    state: str = Field(index=True)
    postal_code: str = Field(index=True)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), index=True)
    )
