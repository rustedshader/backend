from sqlmodel import Session, select
from app.models.database.trips import Trips
from typing import Sequence


async def get_trip_by_id(trip_id: int, db: Session) -> Trips | None:
    statement = select(Trips).where(Trips.id == trip_id)
    trip = db.exec(statement).first()
    return trip


async def get_user_trips(user_id: int, db: Session) -> Sequence[Trips] | None:
    statement = select(Trips).where(Trips.user_id == user_id)
    trips = db.exec(statement).all()
    return trips
