from fastapi import APIRouter, Depends, status, HTTPException
from deps import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])


# This would be device metadata like device id, its api key using which it will send us the live location data to our api in an authenticated way
@router.post("/add-trek-tracking-device")
async def add_treck_tracking_device(admin_user=Depends(get_current_admin_user)):
    pass
