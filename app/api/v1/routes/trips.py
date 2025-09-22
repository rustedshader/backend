# Here api routes for user trips
from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import (
    get_current_user,
    authenticate_tracking_device,
)
from app.models.database.base import get_db
from app.models.schemas.trips import (
    LocationUpdate,
)
from app.models.database.user import User
from sqlmodel import Session
from app.services.trips import (
    get_user_trips,
    get_trip_by_id,
    save_location_data,
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


@router.post("/{trip_id}/live-data")
async def receive_live_data(
    trip_id: int,
    location_data: LocationUpdate,
    tracking_device=Depends(authenticate_tracking_device),
    db: Session = Depends(get_db),
):
    """Receive live location data from tracking device."""
    try:
        location_history = await save_location_data(
            trip_id,
            location_data.latitude,
            location_data.longitude,
            tracking_device,
            db,
        )

        # TODO: Add logic here to check if user is in safe area or deviated
        # For now, just return success with basic status

        return {
            "status": "success",
            "message": "Location data received",
            "location_id": location_history.id,
            "timestamp": location_history.timestamp,
            "safety_status": "safe",  # TODO: Implement actual safety checking
            "deviation_status": "on_track",  # TODO: Implement actual deviation checking
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process location data",
        ) from e
