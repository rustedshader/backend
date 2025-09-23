from sqlmodel import Session, select, desc
from app.models.database.location_sharing import LocationSharing
from app.models.database.location_history import LocationHistory
from app.models.database.trips import Trips
from app.models.schemas.location_sharing import (
    LocationSharingCreate,
    SharedLocationResponse,
)
from fastapi import HTTPException, status
from typing import Optional
import datetime
from geoalchemy2.functions import ST_X, ST_Y


def ensure_timezone_aware(
    dt: Optional[datetime.datetime],
) -> Optional[datetime.datetime]:
    """Ensure datetime is timezone-aware, assuming UTC if naive"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt


async def create_location_sharing(
    user_id: int, location_sharing_data: LocationSharingCreate, db: Session
) -> LocationSharing:
    """Create a new location sharing entry for a trip"""

    # Check if trip exists and belongs to user
    trip = db.exec(
        select(Trips).where(
            (Trips.id == location_sharing_data.trip_id) & (Trips.user_id == user_id)
        )
    ).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or doesn't belong to user",
        )

    # Check if active sharing already exists for this trip
    existing_sharing = db.exec(
        select(LocationSharing).where(
            (LocationSharing.trip_id == location_sharing_data.trip_id)
            & (LocationSharing.user_id == user_id)
            & LocationSharing.is_active
        )
    ).first()

    if existing_sharing:
        # Update existing sharing
        existing_sharing.share_code = LocationSharing.generate_share_code()
        if location_sharing_data.expires_in_hours:
            existing_sharing.expires_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(hours=location_sharing_data.expires_in_hours)
        existing_sharing.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.add(existing_sharing)
        db.commit()
        db.refresh(existing_sharing)
        return existing_sharing

    # Create new location sharing
    expires_at = None
    if location_sharing_data.expires_in_hours:
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            hours=location_sharing_data.expires_in_hours
        )

    location_sharing = LocationSharing(
        trip_id=location_sharing_data.trip_id,
        user_id=user_id,
        share_code=LocationSharing.generate_share_code(),
        is_active=True,
        expires_at=expires_at,
    )

    db.add(location_sharing)
    db.commit()
    db.refresh(location_sharing)

    return location_sharing


async def get_location_sharing_by_code(
    share_code: str, db: Session
) -> Optional[LocationSharing]:
    """Get location sharing by share code"""
    return db.exec(
        select(LocationSharing).where(LocationSharing.share_code == share_code)
    ).first()


async def validate_share_code(share_code: str, db: Session) -> bool:
    """Validate if share code is active and not expired"""
    location_sharing = await get_location_sharing_by_code(share_code, db)

    if not location_sharing:
        return False

    if not location_sharing.is_active:
        return False

    if location_sharing.expires_at:
        # Ensure timezone-aware comparison
        expires_at = ensure_timezone_aware(location_sharing.expires_at)
        current_time = datetime.datetime.now(datetime.timezone.utc)
        if expires_at and expires_at < current_time:
            # Mark as inactive if expired
            location_sharing.is_active = False
            db.add(location_sharing)
            db.commit()
            return False

    return True


async def get_shared_location(share_code: str, db: Session) -> SharedLocationResponse:
    """Get current live location using share code"""

    # Validate share code first
    if not await validate_share_code(share_code, db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired share code",
        )

    location_sharing = await get_location_sharing_by_code(share_code, db)

    if not location_sharing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location sharing not found"
        )

    # Get trip details
    trip = db.exec(select(Trips).where(Trips.id == location_sharing.trip_id)).first()

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )

    # Get latest location from location history
    latest_location = db.exec(
        select(
            LocationHistory,
            ST_X(LocationHistory.location),
            ST_Y(LocationHistory.location),
        )
        .where(LocationHistory.trip_id == location_sharing.trip_id)
        .order_by(desc(LocationHistory.timestamp))
        .limit(1)
    ).first()

    current_location = None
    last_updated = None

    if latest_location:
        location_record, longitude, latitude = latest_location
        current_location = {"latitude": float(latitude), "longitude": float(longitude)}
        # Ensure timezone-aware timestamp
        last_updated = ensure_timezone_aware(location_record.timestamp)

    return SharedLocationResponse(
        user_id=location_sharing.user_id,
        trip_id=location_sharing.trip_id,
        current_location=current_location,
        last_updated=last_updated,
        trip_status=trip.status.value,
    )


async def update_location_sharing(
    user_id: int, trip_id: int, is_active: bool, db: Session
) -> Optional[LocationSharing]:
    """Update location sharing status"""

    location_sharing = db.exec(
        select(LocationSharing).where(
            (LocationSharing.trip_id == trip_id) & (LocationSharing.user_id == user_id)
        )
    ).first()

    if not location_sharing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location sharing not found"
        )

    location_sharing.is_active = is_active
    location_sharing.updated_at = datetime.datetime.now(datetime.timezone.utc)

    db.add(location_sharing)
    db.commit()
    db.refresh(location_sharing)

    return location_sharing


async def get_user_location_shares(user_id: int, db: Session) -> list[LocationSharing]:
    """Get all location sharing entries for a user"""
    result = db.exec(
        select(LocationSharing)
        .where(LocationSharing.user_id == user_id)
        .order_by(desc(LocationSharing.created_at))
    ).all()
    return list(result)
