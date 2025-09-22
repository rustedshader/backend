from sqlmodel import Field, SQLModel
from typing import Any
import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column


class LocationHistory(SQLModel, table=True):
    __tablename__ = "location_histories"

    model_config = {"arbitrary_types_allowed": True}

    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    trip_id: int = Field(foreign_key="trips.id", index=True)
    location: Any = Field(
        sa_column=Column(Geometry(geometry_type="POINT", srid=4326), index=True)
    )
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )
