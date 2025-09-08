from app.models.schemas.trips import TripCreate, TripUpdate, LocationUpdate
from sqlmodel import Session, select
from app.models.database.trips import Trips, LocationHistory, TripStatusEnum
from app.models.database.tracking_device import TrackingDevice
from typing import Sequence, Optional
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import datetime


async def create_new_trip(create_trip_data: TripCreate, db: Session) -> Trips:
    try:
        Trips.model_validate(create_trip_data)
        trip = Trips(**create_trip_data.model_dump())
        db.add(trip)
        db.commit()
        db.refresh(trip)
        return trip
    except Exception as e:
        db.rollback()
        raise e


async def get_trip_by_id(trip_id: int, db: Session) -> Trips | None:
    statement = select(Trips).where(Trips.id == trip_id)
    trip = db.exec(statement).first()
    return trip


async def get_user_trips(user_id: int, db: Session) -> Sequence[Trips] | None:
    statement = select(Trips).where(Trips.user_id == user_id)
    trips = db.exec(statement).all()
    return trips


async def link_tracking_device_to_trip(
    trip_id: int, device_id: str, user_id: int, db: Session
) -> Trips:
    """Link a tracking device to a trip."""
    try:
        # Get the trip and verify it belongs to the user
        trip_statement = select(Trips).where(
            Trips.id == trip_id, Trips.user_id == user_id
        )
        trip = db.exec(trip_statement).first()

        if not trip:
            raise ValueError("Trip not found or doesn't belong to user")

        # Get the tracking device by device_id
        device_statement = select(TrackingDevice).where(
            TrackingDevice.device_id == device_id
        )
        tracking_device = db.exec(device_statement).first()

        if not tracking_device:
            raise ValueError("Tracking device not found")

        # Check if device is available (not linked to another active trip)
        active_trip_statement = select(Trips).where(
            Trips.tracking_deivce_id == tracking_device.id,
            Trips.status.in_([TripStatusEnum.ASSIGNED, TripStatusEnum.IN_PROGRESS]),
        )
        active_trip = db.exec(active_trip_statement).first()

        if active_trip and active_trip.id != trip_id:
            raise ValueError("Tracking device is already linked to another active trip")

        # Link the device to the trip
        trip.tracking_deivce_id = tracking_device.id
        db.add(trip)
        db.commit()
        db.refresh(trip)

        return trip

    except Exception as e:
        db.rollback()
        raise e


async def start_trip(trip_id: int, user_id: int, db: Session) -> Trips:
    """Start a trip by changing its status to IN_PROGRESS."""
    try:
        trip_statement = select(Trips).where(
            Trips.id == trip_id, Trips.user_id == user_id
        )
        trip = db.exec(trip_statement).first()

        if not trip:
            raise ValueError("Trip not found or doesn't belong to user")

        if trip.status != TripStatusEnum.ASSIGNED:
            raise ValueError("Trip must be in ASSIGNED status to start")

        if not trip.tracking_deivce_id:
            raise ValueError("No tracking device linked to this trip")

        trip.status = TripStatusEnum.IN_PROGRESS
        db.add(trip)
        db.commit()
        db.refresh(trip)

        return trip

    except Exception as e:
        db.rollback()
        raise e


async def stop_trip(trip_id: int, user_id: int, db: Session) -> Trips:
    """Stop a trip by changing its status to COMPLETED."""
    try:
        trip_statement = select(Trips).where(
            Trips.id == trip_id, Trips.user_id == user_id
        )
        trip = db.exec(trip_statement).first()

        if not trip:
            raise ValueError("Trip not found or doesn't belong to user")

        if trip.status != TripStatusEnum.IN_PROGRESS:
            raise ValueError("Trip must be in IN_PROGRESS status to stop")

        trip.status = TripStatusEnum.COMPLETED
        db.add(trip)
        db.commit()
        db.refresh(trip)

        return trip

    except Exception as e:
        db.rollback()
        raise e


async def save_location_data(
    trip_id: int,
    latitude: float,
    longitude: float,
    tracking_device: TrackingDevice,
    db: Session,
) -> LocationHistory:
    """Save location data for a trip."""
    try:
        # Verify the tracking device is linked to this trip
        trip_statement = select(Trips).where(
            Trips.id == trip_id,
            Trips.tracking_deivce_id == tracking_device.id,
            Trips.status == TripStatusEnum.IN_PROGRESS,
        )
        trip = db.exec(trip_statement).first()

        if not trip:
            raise ValueError(
                "Trip not found, device not linked, or trip not in progress"
            )

        # Create Point geometry for the location
        point = Point(longitude, latitude)
        location_geom = from_shape(point, srid=4326)

        # Save location data
        location_history = LocationHistory(
            trip_id=trip_id,
            location=location_geom,
            timestamp=int(datetime.datetime.utcnow().timestamp()),
        )

        db.add(location_history)
        db.commit()
        db.refresh(location_history)

        return location_history

    except Exception as e:
        db.rollback()
        raise e


async def get_trip_locations(
    trip_id: int, user_id: int, db: Session
) -> Sequence[LocationHistory]:
    """Get all location history for a trip."""
    try:
        # Verify trip belongs to user
        trip_statement = select(Trips).where(
            Trips.id == trip_id, Trips.user_id == user_id
        )
        trip = db.exec(trip_statement).first()

        if not trip:
            raise ValueError("Trip not found or doesn't belong to user")

        # Get location history
        location_statement = (
            select(LocationHistory)
            .where(LocationHistory.trip_id == trip_id)
            .order_by(LocationHistory.timestamp)
        )

        locations = db.exec(location_statement).all()
        return locations

    except Exception as e:
        raise e
