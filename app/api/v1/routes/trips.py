# Here api routes for user trips
from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import (
    get_current_user,
    authenticate_tracking_device,
)
from app.models.database.base import get_db
from app.models.database.tracking_device import TrackingDevice
from app.models.schemas.trips import (
    LocationUpdate,
)
from app.models.schemas.location_sharing import (
    LocationSharingCreate,
    LocationSharingResponse,
    SharedLocationResponse,
    ShareCodeValidation,
)
from app.models.database.user import User
from sqlmodel import Session
from app.services.trips import (
    get_user_trips,
    get_trip_by_id,
    save_location_data,
)
from app.services.location_sharing import (
    create_location_sharing,
    get_shared_location,
    update_location_sharing,
    get_user_location_shares,
)
from typing import Sequence
from app.models.database.trips import Trips

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("/all-trips", response_model=Sequence[Trips])
async def get_all_trips(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    try:
        trips = await get_user_trips(current_user.id, db)
        return trips
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trips: {e}",
        ) from e


@router.get("/location-shares", response_model=list[LocationSharingResponse])
async def get_user_trip_location_shares(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all location sharing entries for the current user."""
    try:
        location_shares = await get_user_location_shares(current_user.id, db)
        return location_shares

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch location shares",
        ) from e


@router.get("/{trip_id}", response_model=Trips)
async def get_trip_from_id(trip_id: int, db: Session = Depends(get_db)):
    try:
        trip = await get_trip_by_id(trip_id, db)
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )
        return trip
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trip: {e}",
        ) from e


@router.post("/{trip_id}/live-location")
async def receive_live_location(
    trip_id: int,
    location_data: LocationUpdate,
    tracking_device: TrackingDevice = Depends(authenticate_tracking_device),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Receive live location data of the user in a trip."""
    # Check if at least one of tracking_device or current_user is available
    if not tracking_device and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: either tracking device or user must be present.",
        )

    try:
        location_history = await save_location_data(
            trip_id,
            location_data.latitude,
            location_data.longitude,
            db,
        )

        return {
            "status": "success",
            "message": "Location data received",
            "location_id": location_history.id,
            "timestamp": location_history.timestamp,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process location data",
        ) from e


# Location Sharing Endpoints


@router.post("/{trip_id}/share-location", response_model=LocationSharingResponse)
async def create_trip_location_sharing(
    trip_id: int,
    location_sharing_data: LocationSharingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a location sharing code for a trip."""
    try:
        # Override trip_id from URL parameter
        location_sharing_data.trip_id = trip_id

        location_sharing = await create_location_sharing(
            current_user.id, location_sharing_data, db
        )

        return location_sharing

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create location sharing",
        ) from e


@router.get("/shared-location/{share_code}", response_model=SharedLocationResponse)
async def get_trip_shared_location(
    share_code: str,
    db: Session = Depends(get_db),
):
    """Get live location using share code - no authentication required."""
    try:
        shared_location = await get_shared_location(share_code, db)
        return shared_location

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get shared location",
        ) from e


@router.patch("/{trip_id}/share-location/toggle")
async def toggle_trip_location_sharing(
    trip_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enable or disable location sharing for a trip."""
    try:
        location_sharing = await update_location_sharing(
            current_user.id, trip_id, is_active, db
        )

        if not location_sharing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location sharing not found",
            )

        return {
            "status": "success",
            "message": f"Location sharing {'enabled' if is_active else 'disabled'}",
            "is_active": location_sharing.is_active,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update location sharing",
        ) from e
