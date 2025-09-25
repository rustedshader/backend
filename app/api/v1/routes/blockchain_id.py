from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from sqlmodel import Session

from app.api.deps import get_current_user, get_current_admin_user, get_db
from app.models.schemas.blockchain_id import (
    BlockchainApplicationRequest,
    ApplicationSearchQuery,
    ApplicationListResponse,
    BlockchainIDIssueRequest,
    BlockchainStatistics,
    APIResponse,
)
from app.models.database.user import User
from app.models.database.blockchain_id import BlockchainApplicationStatusEnum
from app.services.blockchain_id import (
    apply_for_blockchain_id,
    search_applications,
    get_all_applications,
    issue_blockchain_id,
    reject_application,
    get_blockchain_statistics,
)

# ✅ NEW UNIFIED BLOCKCHAIN ID SYSTEM
# This replaces the deprecated /admin/issue-blockchain-id endpoint
#
# Migration Guide:
# OLD: POST /admin/issue-blockchain-id (DEPRECATED)
# NEW: 1. POST /blockchain-id/apply (create application)
#      2. POST /blockchain-id/applications/{id}/issue (issue from application)
#
# Benefits of new system:
# - Single source of truth for all blockchain ID issuance
# - Complete audit trail with application records
# - Unified workflow for online and entry point scenarios
# - Better admin management and statistics

router = APIRouter()


# Tourist Endpoints
@router.post("/apply", response_model=APIResponse)
async def apply_for_blockchain_tourist_id(
    request: BlockchainApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tourist applies for blockchain ID using their itinerary ID.

    - **itinerary_id**: ID of the user's travel itinerary
    - Only one pending/issued application per user allowed
    - Application status starts as PENDING
    """
    try:
        result = await apply_for_blockchain_id(request, current_user.id, db)

        return APIResponse(
            success=True, message="Application submitted successfully!", data=result
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {e}",
        )


# Admin Endpoints
@router.get("/applications", response_model=ApplicationListResponse)
async def get_blockchain_applications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[BlockchainApplicationStatusEnum] = Query(
        None, description="Filter by status"
    ),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Admin gets all blockchain ID applications with pagination and optional status filter.

    - **page**: Page number (starts from 1)
    - **page_size**: Number of applications per page (max 100)
    - **status**: Optional status filter (pending, issued, rejected)
    - Returns applications with user information
    """
    try:
        applications, total_count = await get_all_applications(
            page=page, page_size=page_size, status=status, db=db
        )

        return ApplicationListResponse(
            applications=applications,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {e}",
        )


@router.post("/applications/search", response_model=ApplicationListResponse)
async def search_blockchain_applications(
    search_query: ApplicationSearchQuery,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Admin searches blockchain ID applications with advanced filters.

    - **query**: Universal search across application number, user info
    - **status**: Filter by application status
    - **date_from**: Filter applications from this date
    - **date_to**: Filter applications up to this date
    - Supports pagination
    """
    try:
        applications, total_count = await search_applications(
            search_query=search_query, page=page, page_size=page_size, db=db
        )

        return ApplicationListResponse(
            applications=applications,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search applications: {e}",
        )


@router.post("/applications/{application_id}/issue", response_model=APIResponse)
async def issue_blockchain_tourist_id(
    application_id: int,
    issue_request: BlockchainIDIssueRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Admin directly issues blockchain ID from pending application.

    - **application_id**: ID of the pending application
    - **validity_days**: Number of days the ID will be valid (1-3650 days)
    - **admin_notes**: Optional notes from admin
    - Application status changes from PENDING to ISSUED
    - Creates blockchain ID record with QR code data
    """
    try:
        # Set the application_id from URL parameter
        issue_request.application_id = application_id

        result = await issue_blockchain_id(
            issue_request=issue_request, admin_id=current_admin.id, db=db
        )

        return APIResponse(
            success=True,
            message="Blockchain Tourist ID issued successfully!",
            data=result,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue blockchain ID: {e}",
        )


@router.put("/applications/{application_id}/reject", response_model=APIResponse)
async def reject_blockchain_application(
    application_id: int,
    admin_notes: str = Query(..., description="Reason for rejection"),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Admin rejects a pending blockchain ID application.

    - **application_id**: ID of the pending application
    - **admin_notes**: Required reason for rejection
    - Application status changes from PENDING to REJECTED
    - User will be notified of rejection with reason
    """
    try:
        result = await reject_application(
            application_id=application_id,
            admin_id=current_admin.id,
            admin_notes=admin_notes,
            db=db,
        )

        return APIResponse(
            success=True, message="Application rejected successfully.", data=result
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject application: {e}",
        )


@router.get("/statistics", response_model=BlockchainStatistics)
async def get_blockchain_id_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get blockchain ID statistics for admin dashboard.

    Returns:
    - Total applications count
    - Pending applications count
    - Issued IDs count
    - Rejected applications count
    - Applications submitted today
    - IDs issued today
    """
    try:
        statistics = await get_blockchain_statistics(db=db)
        return statistics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {e}",
        )


# Tourist Status Check Endpoint
@router.get("/my-application", response_model=APIResponse)
async def get_my_blockchain_application(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tourist checks their own blockchain ID application status.

    Returns:
    - Current application status
    - Application details if exists
    - Blockchain ID information if issued
    """
    try:
        from sqlmodel import select
        from app.models.database.blockchain_id import (
            BlockchainApplication,
            BlockchainID,
        )

        # Get user's application
        application = db.exec(
            select(BlockchainApplication).where(
                BlockchainApplication.user_id == current_user.id
            )
        ).first()

        if not application:
            return APIResponse(
                success=True,
                message="No application found. You can apply for a blockchain ID.",
                data={"has_application": False},
            )

        response_data = {
            "has_application": True,
            "application_id": application.id,
            "application_number": application.application_number,
            "status": application.status,
            "applied_at": application.applied_at,
            "admin_notes": application.admin_notes,
        }

        # If issued, get blockchain ID details
        if application.status == BlockchainApplicationStatusEnum.ISSUED:
            blockchain_id = db.exec(
                select(BlockchainID).where(
                    BlockchainID.application_id == application.id
                )
            ).first()

            if blockchain_id:
                response_data.update(
                    {
                        "blockchain_id": blockchain_id.blockchain_id,
                        "issued_date": blockchain_id.issued_date,
                        "expiry_date": blockchain_id.expiry_date,
                        "is_active": blockchain_id.is_active,
                        "qr_code_data": blockchain_id.qr_code_data,
                    }
                )

        status_messages = {
            "pending": "Your application is being reviewed by the admin.",
            "issued": "Congratulations! Your blockchain Tourist ID has been issued.",
            "rejected": f"Your application was rejected. Reason: {application.admin_notes or 'No reason provided.'}",
        }

        return APIResponse(
            success=True,
            message=status_messages.get(
                application.status, "Application status unknown."
            ),
            data=response_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve application status: {e}",
        )
