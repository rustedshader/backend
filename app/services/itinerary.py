from sqlmodel import Session, select
from app.models.database.itinerary import Itinerary, ItineraryDay, ItineraryStatusEnum
from app.models.database.trips import Trips, TripStatusEnum
from app.models.database.treks import Trek
from app.models.schemas.itinerary import ItineraryCreate, ItineraryUpdate
from typing import List, Optional
import datetime


async def create_itinerary(
    user_id: int, itinerary_data: ItineraryCreate, db: Session
) -> Itinerary:
    """Create a new itinerary for a selected trek with accommodation and daily planning."""
    try:
        # Verify trek exists
        trek_statement = select(Trek).where(Trek.id == itinerary_data.trek_id)
        trek = db.exec(trek_statement).first()
        if not trek:
            raise ValueError(f"Trek with ID {itinerary_data.trek_id} not found")

        # Calculate total duration
        total_duration = (itinerary_data.end_date - itinerary_data.start_date).days + 1

        # Create main itinerary
        itinerary = Itinerary(
            user_id=user_id,
            trek_id=itinerary_data.trek_id,
            title=itinerary_data.title,
            description=itinerary_data.description,
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
            status=ItineraryStatusEnum.DRAFT,
        )

        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)

        # Create itinerary days (accommodation and daily planning for the trek)
        for day_data in itinerary_data.itinerary_days:
            itinerary_day = ItineraryDay(
                itinerary_id=itinerary.id,
                day_number=day_data.day_number,
                date=day_data.date,
                planned_activities=day_data.planned_activities,
                estimated_time_start=day_data.estimated_time_start,
                estimated_time_end=day_data.estimated_time_end,
                accommodation_name=day_data.accommodation_name,
                accommodation_type=day_data.accommodation_type,
                accommodation_address=day_data.accommodation_address,
                accommodation_contact=day_data.accommodation_contact,
                transport_mode=day_data.transport_mode,
                transport_details=day_data.transport_details,
                safety_notes=day_data.safety_notes,
                special_instructions=day_data.special_instructions,
            )
            db.add(itinerary_day)

        db.commit()
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


async def submit_itinerary(
    itinerary_id: int, user_id: int, db: Session
) -> Optional[Itinerary]:
    """Submit itinerary for approval."""
    try:
        itinerary = await get_itinerary_by_id(itinerary_id, user_id, db)
        if not itinerary:
            return None

        if itinerary.status != ItineraryStatusEnum.DRAFT:
            raise ValueError("Only draft itineraries can be submitted")

        itinerary.status = ItineraryStatusEnum.SUBMITTED
        itinerary.submitted_at = int(datetime.datetime.utcnow().timestamp())
        itinerary.updated_at = int(datetime.datetime.utcnow().timestamp())

        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)

        return itinerary

    except Exception as e:
        db.rollback()
        raise e


async def delete_itinerary(itinerary_id: int, user_id: int, db: Session) -> bool:
    """Delete an itinerary and its associated days."""
    try:
        itinerary = await get_itinerary_by_id(itinerary_id, user_id, db)
        if not itinerary:
            return False

        # Delete associated days first
        statement = select(ItineraryDay).where(
            ItineraryDay.itinerary_id == itinerary_id
        )
        days = db.exec(statement).all()
        for day in days:
            db.delete(day)

        # Delete itinerary
        db.delete(itinerary)
        db.commit()

        return True

    except Exception as e:
        db.rollback()
        raise e


# Admin functions
async def get_all_itineraries(db: Session) -> List[Itinerary]:
    """Get all itineraries (admin only)."""
    statement = select(Itinerary)
    return list(db.exec(statement).all())


async def get_pending_itineraries(db: Session) -> List[Itinerary]:
    """Get itineraries pending approval (admin only)."""
    statement = select(Itinerary).where(
        Itinerary.status == ItineraryStatusEnum.SUBMITTED
    )
    return list(db.exec(statement).all())


async def approve_itinerary(itinerary_id: int, db: Session) -> Optional[Itinerary]:
    """Approve an itinerary (admin only)."""
    try:
        statement = select(Itinerary).where(Itinerary.id == itinerary_id)
        itinerary = db.exec(statement).first()

        if not itinerary:
            return None

        if itinerary.status != ItineraryStatusEnum.SUBMITTED:
            raise ValueError("Only submitted itineraries can be approved")

        itinerary.status = ItineraryStatusEnum.APPROVED
        itinerary.approved_at = int(datetime.datetime.utcnow().timestamp())
        itinerary.updated_at = int(datetime.datetime.utcnow().timestamp())

        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)

        return itinerary

    except Exception as e:
        db.rollback()
        raise e


async def get_itinerary_for_blockchain(itinerary_id: int, db: Session) -> str:
    """Generate itinerary data string for blockchain storage."""
    try:
        statement = select(Itinerary).where(Itinerary.id == itinerary_id)
        itinerary = db.exec(statement).first()

        if not itinerary:
            raise ValueError("Itinerary not found")

        days = await get_itinerary_days(itinerary_id, db)

        # Create concise itinerary string for blockchain
        itinerary_string = f"{itinerary.title}|{itinerary.destination_state}|{itinerary.destination_city}|"
        itinerary_string += f"{itinerary.start_date}|{itinerary.end_date}|{itinerary.total_duration_days}days|"
        itinerary_string += (
            f"{itinerary.emergency_contact_name}:{itinerary.emergency_contact_phone}|"
        )

        # Add key locations
        locations = [day.location_name for day in days[:5]]  # First 5 locations
        itinerary_string += "->".join(locations)

        return itinerary_string

    except Exception as e:
        raise e


async def approve_itinerary_and_create_trips(
    itinerary_id: int, db: Session, approved_by_admin_id: int
) -> List[Trips]:
    """
    Approve an itinerary and automatically create trips based on itinerary days.
    Groups consecutive days in the same location into single trips.
    """
    try:
        # Get the itinerary
        statement = select(Itinerary).where(Itinerary.id == itinerary_id)
        itinerary = db.exec(statement).first()

        if not itinerary:
            raise ValueError("Itinerary not found")

        if itinerary.status != ItineraryStatusEnum.SUBMITTED:
            raise ValueError("Only submitted itineraries can be approved")

        # Update itinerary status to approved
        itinerary.status = ItineraryStatusEnum.APPROVED
        itinerary.approved_at = int(datetime.datetime.utcnow().timestamp())

        # Get all itinerary days sorted by date
        days_statement = (
            select(ItineraryDay)
            .where(ItineraryDay.itinerary_id == itinerary_id)
            .order_by(ItineraryDay.date)
        )
        itinerary_days = db.exec(days_statement).all()

        if not itinerary_days:
            raise ValueError("No itinerary days found")

        # Since itinerary is for a specific trek, create a single trip for the entire itinerary
        trip = Trips(
            user_id=itinerary.user_id,
            itinerary_id=itinerary.id,
            trek_id=itinerary.trek_id,  # Use the predefined trek from itinerary
            start_date=itinerary.start_date,
            end_date=itinerary.end_date,
            status=TripStatusEnum.ASSIGNED,
        )

        db.add(trip)
        db.flush()  # Get the trip ID without committing
        trips = [trip]

        db.commit()
        return trips

    except Exception as e:
        db.rollback()
        raise e


async def reject_itinerary(
    itinerary_id: int, db: Session, rejection_reason: str
) -> Itinerary:
    """
    Reject a submitted itinerary and provide feedback.
    """
    try:
        statement = select(Itinerary).where(Itinerary.id == itinerary_id)
        itinerary = db.exec(statement).first()

        if not itinerary:
            raise ValueError("Itinerary not found")

        if itinerary.status != ItineraryStatusEnum.SUBMITTED:
            raise ValueError("Only submitted itineraries can be rejected")

        # Reset to draft status with rejection reason
        itinerary.status = ItineraryStatusEnum.DRAFT
        itinerary.special_requirements = f"REJECTION: {rejection_reason}"
        itinerary.updated_at = int(datetime.datetime.utcnow().timestamp())

        db.commit()
        db.refresh(itinerary)
        return itinerary

    except Exception as e:
        db.rollback()
        raise e
