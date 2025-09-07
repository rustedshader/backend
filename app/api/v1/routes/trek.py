from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import get_current_admin_user, get_current_user
from app.models.schemas.treks import TrekCreate
from app.models.database.base import get_db
from app.models.database.user import User
from sqlmodel import Session
from app.services.treks import create_trecks, get_trek_by_id

router = APIRouter(prefix="/trek", tags=["trek"])


# This would be trek metadata like name, location, etc.
@router.post("/add-trek")
async def add_treck(
    admin_user: User = Depends(get_current_admin_user),
    trek_create_data: TrekCreate = None,
    db: Session = Depends(get_db),
):
    if trek_create_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Trek data is required"
        )
    try:
        await create_trecks(admin_user.id, trek_create_data, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trek",
        ) from e


# This data would be list of cordinates format
@router.post("/add-trek-data")
async def add_treck_data(admin_user=Depends(get_current_admin_user)):
    pass


# This would return basic trek information like name, location, duration, difficulty level, etc.
@router.get("/{trek_id}/information")
async def get_trek_information(
    trek_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        trek = await get_trek_by_id(trek_id, db)
        if not trek:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )
        return trek
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trek information",
        ) from e


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


# Here trecking device will post live location data to our api
@router.post("/{trek_id}/trekking-device/{device_id}/post-location")
async def post_trekking_device_location(trek_id: int, device_id: int):
    pass
