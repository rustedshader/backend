from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import get_current_guide_user, get_current_user

router = APIRouter(prefix="/guide", tags=["guide"])


# Add Basic guide details like experience , cerifications , which areas they can guide in etc.
@router.post("/add-guide-details")
async def add_guide_details():
    pass
