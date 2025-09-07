from app.models.schemas.trips import TripCreate
from sqlmodel import Session, select
from app.models.database.trips import Trips
from typing import Sequence


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
