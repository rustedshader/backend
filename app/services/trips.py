from sqlmodel import Session, select
from app.models.database.trips import Trips
from app.models.database.location_history import LocationHistory
from typing import Sequence
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import datetime


async def get_trip_by_id(trip_id: int, db: Session) -> Trips | None:
    statement = select(Trips).where(Trips.id == trip_id)
    trip = db.exec(statement).first()
    return trip


async def get_user_trips(user_id: int, db: Session) -> Sequence[Trips] | None:
    statement = select(Trips).where(Trips.user_id == user_id)
    trips = db.exec(statement).all()
    return trips


async def save_location_data(
    trip_id: int,
    latitude: float,
    longitude: float,
    tracking_device,
    db: Session,
) -> LocationHistory:
    """Save location data to location history."""
    try:
        # Create a Point geometry from latitude and longitude
        point = Point(
            longitude, latitude
        )  # Note: longitude first, then latitude for Point

        # Get the trip to validate it exists and get user_id
        trip = await get_trip_by_id(trip_id, db)
        if not trip:
            raise ValueError(f"Trip with id {trip_id} not found")

        # Create location history record
        location_history = LocationHistory(
            user_id=trip.user_id,
            trip_id=trip_id,
            location=from_shape(point, srid=4326),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )

        db.add(location_history)
        db.commit()
        db.refresh(location_history)

        return location_history

    except Exception as e:
        db.rollback()
        raise e
