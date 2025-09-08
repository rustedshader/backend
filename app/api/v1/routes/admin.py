from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from app.api.deps import get_current_admin_user
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.schemas.auth import (
    BlockchainIDRequest,
    BlockchainIDResponse,
    UserVerificationProfile,
)
from app.services.auth import (
    issue_blockchain_id_at_entry_point,
    get_user_profile_for_verification,
)
from app.services.itinerary import (
    approve_itinerary_and_create_trips,
    reject_itinerary,
)
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/user/{user_id}/verification-profile", response_model=UserVerificationProfile
)
async def get_user_for_verification(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get user profile for verification at entry points.
    Used by officials to verify tourist information before issuing blockchain ID.
    """
    try:
        profile = await get_user_profile_for_verification(user_id, db)
        return UserVerificationProfile(**profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile",
        )


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
            detail="Failed to issue blockchain ID",
        )


@router.get("/pending-verifications")
async def get_pending_verifications(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get list of users who have registered but don't have blockchain IDs yet.
    For officials to see who needs verification at entry points.
    """
    try:
        from sqlmodel import select

        # Get users without blockchain IDs
        statement = select(User).where(User.tourist_id_token.is_(None))
        users = db.exec(statement).all()

        pending_users = []
        for user in users:
            pending_users.append(
                {
                    "id": user.id,
                    "name": f"{user.first_name} {user.last_name or ''}".strip(),
                    "email": user.email,
                    "country_code": user.country_code,
                    "phone_number": user.phone_number,
                    "indian_citizenship": user.indian_citizenship,
                    "is_kyc_verified": user.is_kyc_verified,
                    "created_at": user.id,  # You might want to add created_at field to User model
                }
            )

        return {
            "pending_verifications": pending_users,
            "total_count": len(pending_users),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending verifications",
        )


class ItineraryApprovalResponse(BaseModel):
    message: str
    itinerary_id: int
    trips_created: List[dict]


class ItineraryRejectionRequest(BaseModel):
    reason: str


@router.post(
    "/itinerary/{itinerary_id}/approve", response_model=ItineraryApprovalResponse
)
async def approve_itinerary(
    itinerary_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Approve an itinerary and automatically create trips based on itinerary days.
    This creates individual trips for each location group in the itinerary.
    """
    try:
        trips = await approve_itinerary_and_create_trips(
            itinerary_id, db, admin_user.id
        )

        trips_data = []
        for trip in trips:
            trips_data.append(
                {
                    "id": trip.id,
                    "start_date": trip.start_date.isoformat(),
                    "end_date": trip.end_date.isoformat(),
                    "trek_id": trip.trek_id,
                    "status": trip.status.value,
                }
            )

        return ItineraryApprovalResponse(
            message=f"Itinerary approved successfully. {len(trips)} trips created.",
            itinerary_id=itinerary_id,
            trips_created=trips_data,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve itinerary",
        )


@router.post("/itinerary/{itinerary_id}/reject")
async def reject_itinerary_endpoint(
    itinerary_id: int,
    request: ItineraryRejectionRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Reject an itinerary and provide feedback to the tourist.
    """
    try:
        itinerary = await reject_itinerary(itinerary_id, db, request.reason)

        return {
            "message": "Itinerary rejected successfully",
            "itinerary_id": itinerary_id,
            "reason": request.reason,
            "status": itinerary.status.value,
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject itinerary",
        )


class BlockchainReissueRequest(BaseModel):
    user_id: int
    reason: str  # Reason for reissuance (expired, lost, etc.)


@router.post("/reissue-blockchain-id", response_model=BlockchainIDResponse)
async def reissue_blockchain_id(
    request: BlockchainReissueRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Reissue blockchain ID for a tourist (admin only).
    Used for renewal, replacement of lost/expired IDs, etc.
    """
    try:
        # Get user
        from sqlmodel import select

        user_statement = select(User).where(User.id == request.user_id)
        user = db.exec(user_statement).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Get user's latest approved itinerary for blockchain data
        from app.models.database.itinerary import Itinerary, ItineraryStatusEnum

        itinerary_statement = (
            select(Itinerary)
            .where(
                Itinerary.user_id == request.user_id,
                Itinerary.status == ItineraryStatusEnum.APPROVED,
            )
            .order_by(Itinerary.approved_at.desc())
            .limit(1)
        )

        itinerary = db.exec(itinerary_statement).first()

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No approved itinerary found for this user",
            )

        # Reissue blockchain ID using the same function as initial issuance
        blockchain_data = await issue_blockchain_id_at_entry_point(
            user_id=request.user_id,
            itinerary_id=itinerary.id,
            entry_point=f"REISSUE_BY_ADMIN_{admin_user.id}",
            reason=f"REISSUE: {request.reason}",
            db=db,
        )

        return BlockchainIDResponse(**blockchain_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reissue blockchain ID",
        )
