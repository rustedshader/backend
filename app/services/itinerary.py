from sqlmodel import Session, select
from app.models.database.itinerary import (
    Itinerary,
    ItineraryDay,
    ItineraryStatusEnum,
    ItineraryTypeEnum,
)
from app.models.database.trips import Trips, TripStatusEnum, TripTypeEnum
from app.models.database.places import Place
from app.models.database.treks import Trek
from app.models.schemas.itinerary import ItineraryCreate, ItineraryUpdate
from typing import List, Optional
import datetime


async def create_itinerary(
    user_id: int, itinerary_data: ItineraryCreate, db: Session
) -> Itinerary:
    """Create a new itinerary for either treks or places (city tours) with accommodation and daily planning, and automatically create a trip."""
    try:
        # Validate based on itinerary type
        if (
            itinerary_data.itinerary_type == ItineraryTypeEnum.TREK
            and itinerary_data.trek_id
        ):
            # Verify trek exists
            trek_statement = select(Trek).where(Trek.id == itinerary_data.trek_id)
            trek = db.exec(trek_statement).first()
            if not trek:
                raise ValueError(f"Trek with ID {itinerary_data.trek_id} not found")

        if (
            itinerary_data.itinerary_type == ItineraryTypeEnum.CITY_TOUR
            and itinerary_data.primary_place_id
        ):
            # Verify place exists
            place_statement = select(Place).where(
                Place.id == itinerary_data.primary_place_id
            )
            place = db.exec(place_statement).first()
            if not place:
                raise ValueError(
                    f"Place with ID {itinerary_data.primary_place_id} not found"
                )

        # Calculate total duration
        total_duration = (itinerary_data.end_date - itinerary_data.start_date).days + 1

        # Create main itinerary and set status to ACTIVE (no approval needed)
        itinerary = Itinerary(
            user_id=user_id,
            itinerary_type=itinerary_data.itinerary_type,
            trek_id=itinerary_data.trek_id,
            primary_place_id=itinerary_data.primary_place_id,
            title=itinerary_data.title,
            description=itinerary_data.description,
            destination_city=itinerary_data.destination_city,
            destination_state=itinerary_data.destination_state,
            destination_country=itinerary_data.destination_country,
            start_date=itinerary_data.start_date,
            end_date=itinerary_data.end_date,
            total_duration_days=total_duration,
            estimated_budget=itinerary_data.estimated_budget,
            number_of_travelers=itinerary_data.number_of_travelers,
            purpose_of_visit=itinerary_data.purpose_of_visit,
            emergency_contact_name=itinerary_data.emergency_contact_name,
            emergency_contact_phone=itinerary_data.emergency_contact_phone,
            emergency_contact_relation=itinerary_data.emergency_contact_relation,
            preferred_language=itinerary_data.preferred_language,
            special_requirements=itinerary_data.special_requirements,
            status=ItineraryStatusEnum.ACTIVE,  # Set directly to ACTIVE
            approved_at=int(datetime.datetime.utcnow().timestamp()),  # Auto-approved
        )

        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)

        # Create itinerary days (accommodation and daily planning)
        for day_data in itinerary_data.itinerary_days:
            itinerary_day = ItineraryDay(
                itinerary_id=itinerary.id,
                day_number=day_data.day_number,
                date=day_data.date,
                day_type=day_data.day_type,
                trek_id=day_data.trek_id,
                primary_place_id=day_data.primary_place_id,
                planned_activities=day_data.planned_activities,
                estimated_time_start=day_data.estimated_time_start,
                estimated_time_end=day_data.estimated_time_end,
                accommodation_name=day_data.accommodation_name,
                accommodation_type=day_data.accommodation_type,
                accommodation_address=day_data.accommodation_address,
                accommodation_contact=day_data.accommodation_contact,
                accommodation_latitude=day_data.accommodation_latitude,
                accommodation_longitude=day_data.accommodation_longitude,
                transport_mode=day_data.transport_mode,
                transport_details=day_data.transport_details,
                safety_notes=day_data.safety_notes,
                special_instructions=day_data.special_instructions,
            )
            db.add(itinerary_day)

        db.commit()

        # Auto-create a trip for this itinerary with rich data
        try:
            # Extract accommodation and destination info from first day if available
            hotel_name = None
            hotel_latitude = None
            hotel_longitude = None
            destination_name = (
                f"{itinerary_data.destination_city}, {itinerary_data.destination_state}"
            )
            destination_latitude = None
            destination_longitude = None

            # Get accommodation details from the first itinerary day
            if itinerary_data.itinerary_days and len(itinerary_data.itinerary_days) > 0:
                first_day = itinerary_data.itinerary_days[0]
                hotel_name = first_day.accommodation_name
                hotel_latitude = first_day.accommodation_latitude
                hotel_longitude = first_day.accommodation_longitude

            # Try to get primary place coordinates for destination
            if itinerary_data.primary_place_id:
                primary_place = db.exec(
                    select(Place).where(Place.id == itinerary_data.primary_place_id)
                ).first()
                if primary_place:
                    destination_latitude = primary_place.latitude
                    destination_longitude = primary_place.longitude
                    destination_name = (
                        f"{primary_place.name}, {itinerary_data.destination_city}"
                    )

            new_trip = Trips(
                user_id=user_id,
                itinerary_id=itinerary.id,
                trek_id=itinerary_data.trek_id,
                start_date=itinerary_data.start_date,
                end_date=itinerary_data.end_date,
                status=TripStatusEnum.ASSIGNED,
                trip_type=TripTypeEnum.TOUR_DAY,
                # Populate accommodation details
                hotel_name=hotel_name,
                hotel_latitude=hotel_latitude,
                hotel_longitude=hotel_longitude,
                # Populate destination details
                destination_name=destination_name,
                destination_latitude=destination_latitude,
                destination_longitude=destination_longitude,
                # Set current phase for tour
                current_phase="tour_planning",
            )
            db.add(new_trip)
            db.commit()
            db.refresh(new_trip)
            print(
                f"✅ Successfully created trip ID: {new_trip.id} for itinerary ID: {itinerary.id} with accommodation: {hotel_name} and destination: {destination_name}"
            )
        except Exception as e:
            print(f"❌ Error creating trip: {str(e)}")
            db.rollback()
            # Continue anyway since itinerary creation was successful

        return itinerary

    except Exception as e:
        db.rollback()
        raise e


async def get_user_itineraries(user_id: int, db: Session) -> List[Itinerary]:
    """Get all itineraries for a user."""
    statement = select(Itinerary).where(Itinerary.user_id == user_id)
    itineraries = db.exec(statement).all()
    return list(itineraries)


async def get_itinerary_by_id(
    itinerary_id: int, user_id: int, db: Session
) -> Optional[Itinerary]:
    """Get a specific itinerary by ID, ensuring it belongs to the user."""
    statement = select(Itinerary).where(
        Itinerary.id == itinerary_id, Itinerary.user_id == user_id
    )
    return db.exec(statement).first()


async def get_itinerary_days(itinerary_id: int, db: Session) -> List[ItineraryDay]:
    """Get all days for a specific itinerary."""
    statement = (
        select(ItineraryDay)
        .where(ItineraryDay.itinerary_id == itinerary_id)
        .order_by(ItineraryDay.day_number)
    )
    return list(db.exec(statement).all())


async def update_itinerary(
    itinerary_id: int, user_id: int, update_data: ItineraryUpdate, db: Session
) -> Optional[Itinerary]:
    """Update an itinerary."""
    try:
        # Get existing itinerary
        itinerary = await get_itinerary_by_id(itinerary_id, user_id, db)
        if not itinerary:
            return None

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(itinerary, field, value)

        # Recalculate duration if dates changed
        if update_data.start_date or update_data.end_date:
            total_duration = (itinerary.end_date - itinerary.start_date).days + 1
            itinerary.total_duration_days = total_duration

        itinerary.updated_at = int(datetime.datetime.utcnow().timestamp())

        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)

        return itinerary

    except Exception as e:
        db.rollback()
        raise e


async def delete_itinerary(itinerary_id: int, user_id: int, db: Session) -> bool:
    """Delete an itinerary and its associated days and trips."""
    try:
        itinerary = await get_itinerary_by_id(itinerary_id, user_id, db)
        if not itinerary:
            return False

        # Delete associated trips first
        from app.models.database.trips import Trips
        from sqlmodel import delete

        # Delete trips associated with this itinerary
        trip_delete_statement = delete(Trips).where(Trips.itinerary_id == itinerary_id)
        db.exec(trip_delete_statement)

        # Delete itinerary days associated with this itinerary
        days_delete_statement = delete(ItineraryDay).where(
            ItineraryDay.itinerary_id == itinerary_id
        )
        db.exec(days_delete_statement)

        # Delete the itinerary itself
        db.delete(itinerary)
        db.commit()

        return True

    except Exception as e:
        db.rollback()
        raise e
