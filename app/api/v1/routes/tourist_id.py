from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.models.database.base import get_db
from app.models.database.user import User
from app.api.deps import get_current_active_user
from app.services.tourist_id import TouristIDService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/tourist-id", tags=["tourist-id"])


class TouristIDInfoResponse(BaseModel):
    kyc_hash: str
    itinerary_hash: str
    valid_until: int
    is_revoked: bool
    is_valid: bool


class TouristIDStatusResponse(BaseModel):
    has_tourist_id: bool
    tourist_id_token: Optional[int] = None
    transaction_hash: Optional[str] = None
    is_valid: bool = False
    info: Optional[TouristIDInfoResponse] = None


@router.get("/status", response_model=TouristIDStatusResponse)
async def get_tourist_id_status(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get the current user's tourist ID status and information."""
    service = TouristIDService()

    if not current_user.tourist_id_token:
        return TouristIDStatusResponse(has_tourist_id=False, is_valid=False)

    is_valid = service.is_tourist_id_valid(current_user)
    info = service.get_tourist_id_info(current_user)

    info_response = None
    if info:
        info_response = TouristIDInfoResponse(
            kyc_hash=info.kycHash,
            itinerary_hash=info.itineraryHash,
            valid_until=info.validUntil,
            is_revoked=info.isRevoked,
            is_valid=is_valid,
        )

    return TouristIDStatusResponse(
        has_tourist_id=True,
        tourist_id_token=current_user.tourist_id_token,
        transaction_hash=current_user.tourist_id_transaction_hash,
        is_valid=is_valid,
        info=info_response,
    )


# Note: Tourist ID issuance/reissuance is now handled exclusively by admins
# via the admin endpoints at entry points for security compliance


@router.post("/revoke")
async def revoke_tourist_id(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Revoke the current user's tourist ID."""
    if not current_user.tourist_id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a tourist ID to revoke",
        )

    service = TouristIDService()

    try:
        success = service.revoke_tourist_id(current_user, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke tourist ID",
            )

        return {"message": "Tourist ID revoked successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking tourist ID: {str(e)}",
        )
