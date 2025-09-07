from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.models.database.base import get_db
from app.api.deps import get_current_admin_user


router = APIRouter(prefix="/tracking-device", tags=["tracking-device"])


# This would be to create a tracking device which can be linked to a trip later
@router.post("/create-device")
async def create_tracking_device(
    admin_user=Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    pass
