from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from app.api.deps import get_current_admin_user
from app.models.database.base import get_db
from app.models.database.user import User

from app.models.schemas.auth import (
    BlockchainIDRequest,
    BlockchainIDResponse,
)

from app.services.admin import (
    get_active_trips,
    get_latest_location_all_trips,
    issue_blockchain_id_at_entry_point,
)

from fastapi import Query
from typing import Optional

from app.models.database.user import UserRoleEnum
from app.models.schemas.auth import (
    UserResponse,
    UserListResponse,
    UserStatsResponse,
    UserStatusUpdateRequest,
)
from app.services.users import UserService


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
    Automatically sets KYC verified to true when blockchain ID is issued.
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


@router.get("/active-trips")
async def fetch_active_trips(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Fetch all active (ongoing) trips"""
    try:
        trips = await get_active_trips(db)
        return {"active_trips": trips, "count": len(trips)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch active trips: {e}",
        )


@router.get("/latest-trip-locations")
async def fetch_latest_trip_locations(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Fetch the latest location for all ongoing trips"""
    try:
        trip_locations = await get_latest_location_all_trips(db)
        return {"trip_locations": trip_locations, "count": len(trip_locations)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch latest trip locations: {e}",
        )


@router.get("/admin/stats", response_model=UserStatsResponse)
async def get_user_statistics(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get comprehensive user statistics (Admin only).

    Returns statistical information about users including:
    - Total user count
    - Breakdown by role
    - Verification statistics
    - Active/inactive users
    """
    return await UserService.get_user_stats(db)


@router.get("/unverified", response_model=UserListResponse)
async def get_unverified_users(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get list of unverified users (Admin only).

    Convenience endpoint to quickly access users who need KYC verification.
    """
    users = await UserService.get_all_users(
        db=db,
        is_verified_filter=False,
        limit=limit,
        offset=offset,
    )

    # Get total unverified count
    all_unverified = await UserService.get_all_users(
        db=db,
        is_verified_filter=False,
        limit=10000,
        offset=0,
    )

    return UserListResponse(
        users=users,
        total_count=len(all_unverified),
        offset=offset,
        limit=limit,
    )


@router.get("/users/list", response_model=UserListResponse)
async def list_all_users(
    role_filter: Optional[UserRoleEnum] = Query(
        None, description="Filter by user role"
    ),
    is_active_filter: Optional[bool] = Query(
        None, description="Filter by active status"
    ),
    is_verified_filter: Optional[bool] = Query(
        None, description="Filter by verification status"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    List all users with optional filtering (Admin only).

    This endpoint allows administrators to view all users in the system with various filters:
    - Filter by role (admin, tourist, guide, super_admin)
    - Filter by active status
    - Filter by verification status
    - Pagination support
    """
    try:
        users = await UserService.get_all_users(
            db=db,
            role_filter=role_filter,
            is_active_filter=is_active_filter,
            is_verified_filter=is_verified_filter,
            limit=limit,
            offset=offset,
        )

        # Get total count for pagination info
        # Note: In production, you might want to optimize this with a separate count query
        all_users = await UserService.get_all_users(
            db=db,
            role_filter=role_filter,
            is_active_filter=is_active_filter,
            is_verified_filter=is_verified_filter,
            limit=10000,  # Large limit to get total count
            offset=0,
        )

        return UserListResponse(
            users=users,
            total_count=len(all_users),
            offset=offset,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}",
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_information(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed user information by ID (Admin only).

    Returns complete user profile including:
    - Personal information
    - Contact details
    - Verification status
    - Role and permissions
    - Blockchain information
    """
    return await UserService.get_user_by_id(db, user_id)


@router.put("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    status_update: UserStatusUpdateRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Update user active status (Admin only).

    Allows administrators to activate or deactivate user accounts.
    Deactivated users cannot log in or use the system.
    """
    return await UserService.update_user_status(
        db, user_id, status_update.is_active, admin_user.id
    )
