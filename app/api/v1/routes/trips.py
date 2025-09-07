# Here api routes for user trips
from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import get_current_admin_user, get_current_user
from app.models.database.base import get_db


router = APIRouter(prefix="/trips", tags=["trips"])


# User can create a trip
@router.post("/create-trip")
async def create_trip():
    pass


# User can get all trips
@router.get("/all-trips")
async def get_all_trips():
    pass


# User can get a specific trip by id
@router.get("/{trip_id}")
async def get_trip_by_id(trip_id: int):
    pass


# User can update a specific trip by id
@router.put("/{trip_id}")
async def update_trip_by_id(trip_id: int):
    pass


# Link tracking device to a trip
@router.post("/{trip_id}/link-device")
async def link_device_to_trip(trip_id: int):
    pass
