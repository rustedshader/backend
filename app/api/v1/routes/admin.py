from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from app.api.deps import get_current_admin_user
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.schemas.auth import (
    BlockchainIDRequest,
    BlockchainIDResponse,
)
from app.services.auth import (
    issue_blockchain_id_at_entry_point,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/issue-blockchain-id", response_model=BlockchainIDResponse)
async def issue_blockchain_id(
    request: BlockchainIDRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Issue blockchain ID to a tourist at entry point.
    This should only be called after physical verification of documents.
    Only authorized officials can call this endpoint.
    """
    try:
        result = await issue_blockchain_id_at_entry_point(
            user_id=request.user_id,
            itinerary_id=request.itinerary_id,
            validity_days=request.validity_days,
            official_id=admin_user.id,
            db=db,
        )
        return BlockchainIDResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue blockchain ID: {e}",
        )
