from sqlmodel import Session, select
from app.models.database.itinerary import (
    Itinerary,
    ItineraryDay,
)
from app.models.schemas.itinerary import (
    ItineraryCreate,
    ItineraryDayCreate,
    ItineraryUpdate,
    ItineraryDayUpdate,
)
from typing import List, Optional
import datetime


async def create_itinerary(
    itinerary_data: ItineraryCreate, user_id: int, db: Session
) -> Itinerary:
    try:
        new_itinerary = Itinerary(
            user_id=user_id,
            title=itinerary_data.title,
            description=itinerary_data.description,
            destination_city=itinerary_data.destination_city,
            destination_state=itinerary_data.destination_state,
            start_date=itinerary_data.start_date,
            end_date=itinerary_data.end_date,
            total_duration_days=itinerary_data.total_duration_days,
        )
        db.add(new_itinerary)
        db.commit()
        db.refresh(new_itinerary)

        # Create itinerary days if provided
        for day in itinerary_data.itinerary_days or []:
            new_day = ItineraryDay(
                itinerary_id=new_itinerary.id,
                accommodation_id=day.accommodation_id,
                day_number=day.day_number,
                offline_activity_id=day.offline_activity_id,
                online_activity_id=day.online_activity_id,
            )
            db.add(new_day)
        db.commit()

        return new_itinerary
    except Exception as e:
        db.rollback()
        print(e)
        raise e


async def get_itinerary_by_id(
    itinerary_id: int, user_id: int, db: Session
) -> Optional[Itinerary]:
    try:
        statement = select(Itinerary).where(
            Itinerary.id == itinerary_id, Itinerary.user_id == user_id
        )
        result = db.exec(statement).first()
        return result
    except Exception as e:
        print(e)
        raise e


async def get_itinerary_by_id_with_days(
    itinerary_id: int, user_id: int, db: Session
) -> Optional[dict]:
    """Get itinerary with its associated days for response"""
    try:
        # Get the itinerary
        itinerary = await get_itinerary_by_id(itinerary_id, user_id, db)
        if not itinerary:
            return None

        # Get the itinerary days
        days = await get_itinerary_days(itinerary_id, db)

        # Convert to dict format for response
        itinerary_dict = {
            "id": itinerary.id,
            "user_id": itinerary.user_id,
            "title": itinerary.title,
            "description": itinerary.description,
            "destination_city": itinerary.destination_city,
            "destination_state": itinerary.destination_state,
            "start_date": itinerary.start_date,
            "end_date": itinerary.end_date,
            "total_duration_days": itinerary.total_duration_days,
            "created_at": itinerary.created_at,
            "updated_at": itinerary.updated_at,
            "itinerary_days": [
                {
                    "id": day.id,
                    "itinerary_id": day.itinerary_id,
                    "accommodation_id": day.accommodation_id,
                    "day_number": day.day_number,
                    "offline_activity_id": day.offline_activity_id,
                    "online_activity_id": day.online_activity_id,
                }
                for day in days
            ],
        }

        return itinerary_dict
    except Exception as e:
        print(e)
        raise e


async def get_itineraries_by_user(user_id: int, db: Session) -> List[Itinerary]:
    try:
        statement = select(Itinerary).where(Itinerary.user_id == user_id)
        results = db.exec(statement).all()
        return results
    except Exception as e:
        print(e)
        raise e


async def create_itinerary_days(
    itinerary_id: int, days_data: List[ItineraryDayCreate], db: Session
) -> List[ItineraryDay]:
    created_days = []
    try:
        for day_data in days_data:
            new_day = ItineraryDay(
                itinerary_id=itinerary_id,
                accommodation_id=day_data.accommodation_id,
                day_number=day_data.day_number,
                offline_activity_id=day_data.offline_activity_id,
                online_activity_id=day_data.online_activity_id,
            )
            db.add(new_day)
            created_days.append(new_day)
        db.commit()
        for day in created_days:
            db.refresh(day)
        return created_days
    except Exception as e:
        db.rollback()
        print(e)
        raise e


async def get_itinerary_days(itinerary_id: int, db: Session) -> List[ItineraryDay]:
    try:
        statement = (
            select(ItineraryDay)
            .where(ItineraryDay.itinerary_id == itinerary_id)
            .order_by(ItineraryDay.day_number)
        )
        results = db.exec(statement).all()
        return results
    except Exception as e:
        print(e)
        raise e


async def update_itinerary(
    itinerary_id: int, itinerary_data: ItineraryUpdate, user_id: int, db: Session
) -> Optional[dict]:
    """Update an existing itinerary"""
    try:
        # Get the existing itinerary
        existing_itinerary = await get_itinerary_by_id(itinerary_id, user_id, db)
        if not existing_itinerary:
            return None

        # Update fields that are provided
        update_data = itinerary_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_itinerary, field, value)

        # Update the updated_at timestamp
        existing_itinerary.updated_at = datetime.datetime.now(datetime.timezone.utc)

        db.add(existing_itinerary)
        db.commit()
        db.refresh(existing_itinerary)

        # Return the updated itinerary with days
        return await get_itinerary_by_id_with_days(itinerary_id, user_id, db)

    except Exception as e:
        db.rollback()
        print(e)
        raise e


async def delete_itinerary(itinerary_id: int, user_id: int, db: Session) -> bool:
    """Delete an itinerary and all its associated days"""
    try:
        # Get the itinerary to ensure it exists and belongs to the user
        itinerary = await get_itinerary_by_id(itinerary_id, user_id, db)
        if not itinerary:
            return False

        # Delete all associated itinerary days first
        days_statement = select(ItineraryDay).where(
            ItineraryDay.itinerary_id == itinerary_id
        )
        days = db.exec(days_statement).all()
        for day in days:
            db.delete(day)

        # Delete the itinerary
        db.delete(itinerary)
        db.commit()

        return True

    except Exception as e:
        db.rollback()
        print(e)
        raise e


async def update_itinerary_day(
    day_id: int, itinerary_id: int, day_data: ItineraryDayUpdate, db: Session
) -> Optional[ItineraryDay]:
    """Update a specific itinerary day"""
    try:
        # Get the existing day
        statement = select(ItineraryDay).where(
            ItineraryDay.id == day_id, ItineraryDay.itinerary_id == itinerary_id
        )
        existing_day = db.exec(statement).first()

        if not existing_day:
            return None

        # Update fields that are provided
        update_data = day_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_day, field, value)

        db.add(existing_day)
        db.commit()
        db.refresh(existing_day)

        return existing_day

    except Exception as e:
        db.rollback()
        print(e)
        raise e


async def delete_itinerary_day(day_id: int, itinerary_id: int, db: Session) -> bool:
    """Delete a specific itinerary day"""
    try:
        # Get the day to ensure it exists and belongs to the itinerary
        statement = select(ItineraryDay).where(
            ItineraryDay.id == day_id, ItineraryDay.itinerary_id == itinerary_id
        )
        day = db.exec(statement).first()

        if not day:
            return False

        db.delete(day)
        db.commit()

        return True

    except Exception as e:
        db.rollback()
        print(e)
        raise e
