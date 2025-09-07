# Here api routes for user trips
from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import get_current_admin_user, get_current_user
from app.models.database.base import get_db
from app.models.schemas.trips import TripCreate
from app.models.database.user import User
from sqlmodel import Session
from app.services.trips import create_new_trip, get_user_trips, get_trip_by_id
from typing import Sequence
from app.models.database.trips import Trips

router = APIRouter(prefix="/trips", tags=["trips"])


# User can create a trip
@router.post("/create-trip")
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        trip = await create_new_trip(trip_data, db)
        return trip
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trip",
        ) from e


# User can get all trips
@router.get("/all-trips", response_model=Sequence[Trips])
async def get_all_trips(current_user: User = Depends(get_current_user)):
    try:
        trips = await get_user_trips(current_user.id)
        return trips
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trips",
        ) from e


# User can get a specific trip by id
@router.get("/{trip_id}", response_model=Trips)
async def get_trip_from_id(trip_id: int):
    try:
        trip = await get_trip_by_id(trip_id)
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
            )
        return trip
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trip",
        ) from e


# User can update a specific trip by id
@router.put("/{trip_id}")
async def update_trip_by_id(trip_id: int):
    pass


# Link tracking device to a trip
@router.post("/{trip_id}/link-device")
async def link_device_to_trip(trip_id: int):
    pass
