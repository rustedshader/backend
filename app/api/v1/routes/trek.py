from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import get_current_admin_user


router = APIRouter(prefix="/trek", tags=["trek"])


# This would be trek metadata like name, location, etc.
@router.post("/add-trek")
async def add_treck(admin_user=Depends(get_current_admin_user)):
    pass


# This data would be geojson format
@router.post("/add-trek-data")
async def add_treck_data(admin_user=Depends(get_current_admin_user)):
    pass


# This would return basic trek information like name, location, duration, difficulty level, etc.
@router.get("/{trek_id}/information")
async def get_trek_information(trek_id: int):
    pass


# This would return the geojson data for the trek route
@router.get("/{trek_id}/route")
async def get_trek_route(trek_id: int):
    pass


# This would return live location of all the trekkers on this trek
@router.get("/{trek_id}/live-locations")
async def get_trek_live_locations(trek_id: int):
    pass


# This would return status of the trek like not started, in progress, completed, cancelled, etc.
@router.get("/{trek_id}/status")
async def get_trek_status(trek_id: int):
    pass


# This would return historical location data of a specific trekker on this trek
@router.get("/{trek_id}/trekker/{trekker_id}/location-history")
async def get_trekker_location_history(trek_id: int, trekker_id: int):
    pass
