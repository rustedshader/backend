from sqlmodel import Session, select, desc
from app.models.database.trips import Trips, TripStatusEnum
from app.models.database.location_history import LocationHistory
from app.models.database.location_sharing import LocationSharing
from typing import Sequence, Optional
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


async def get_user_trips_with_share_codes(user_id: int, db: Session) -> list[dict]:
    """Get user trips with their location sharing information"""

    # First get all user trips
    trips = db.exec(
        select(Trips).where(Trips.user_id == user_id).order_by(desc(Trips.created_at))
    ).all()

    trips_with_sharing = []

    for trip in trips:
        # Get location sharing for this trip
        location_sharing = db.exec(
            select(LocationSharing)
            .where(LocationSharing.trip_id == trip.id)
            .where(LocationSharing.user_id == user_id)
        ).first()

        trip_data = {
            "id": trip.id,
            "user_id": trip.user_id,
            "itinerary_id": trip.itinerary_id,
            "status": trip.status.value,
            "tourist_id": trip.tourist_id,
            "blockchain_transaction_hash": trip.blockchain_transaction_hash,
            "created_at": trip.created_at,
            "updated_at": trip.updated_at,
            "share_code": location_sharing.share_code if location_sharing else None,
            "share_expires_at": location_sharing.expires_at
            if location_sharing
            else None,
            "share_is_active": location_sharing.is_active if location_sharing else None,
        }
        trips_with_sharing.append(trip_data)

    return trips_with_sharing


async def save_location_data(
    trip_id: int,
    latitude: float,
    longitude: float,
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


async def create_trip_with_location_sharing(
    user_id: int,
    itinerary_id: int,
    db: Session,
    status: TripStatusEnum = TripStatusEnum.UPCOMING,
    tourist_id: Optional[str] = None,
    blockchain_transaction_hash: Optional[str] = None,
    expires_in_days: int = 7,  # Default 7 days
) -> dict:
    """Create a new trip with automatic location sharing code generation"""
    try:
        # Create the trip
        new_trip = Trips(
            user_id=user_id,
            itinerary_id=itinerary_id,
            status=status,
            tourist_id=tourist_id,
            blockchain_transaction_hash=blockchain_transaction_hash,
        )

        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)

        # Create location sharing code for the new trip
        location_sharing = LocationSharing(
            trip_id=new_trip.id,
            user_id=user_id,
            share_code=LocationSharing.generate_share_code(),
            is_active=True,
            expires_at=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=expires_in_days),
        )

        db.add(location_sharing)
        db.commit()
        db.refresh(location_sharing)

        return {
            "trip": new_trip,
            "location_sharing": location_sharing,
            "share_code": location_sharing.share_code,
            "expires_at": location_sharing.expires_at,
        }

    except Exception as e:
        db.rollback()
        raise e
