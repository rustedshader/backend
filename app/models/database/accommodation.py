from geoalchemy2 import Geometry
from sqlmodel import SQLModel, Field


class Accommodation(SQLModel, table=True):
    __tablename__ = "accommodations"

    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True)
    address: str = Field(index=True)
    city: str = Field(index=True)
    state: str = Field(index=True)
    postal_code: str = Field(index=True)
    location: Geometry = Field(
        sa_column=Geometry(geometry_type="POINT", srid=4326), index=True
    )
