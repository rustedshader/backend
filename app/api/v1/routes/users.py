from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlmodel import Session
from typing import Optional

from app.api.deps import get_current_admin_user
from app.models.database.base import get_db
from app.models.database.user import User, UserRoleEnum
from app.models.schemas.auth import (
    UserResponse,
    UserListResponse,
    BlockchainInfoResponse,
    UserStatsResponse,
    UserStatusUpdateRequest,
)
from app.services.users import UserService

router = APIRouter(prefix="/users", tags=["user-management"])


# IMPORTANT: Specific string routes MUST come before parameterized routes
# to avoid route conflicts with FastAPI path parameter matching


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
    - Blockchain ID issuance count
    """
    return await UserService.get_user_stats(db)


@router.get("/admin/unverified", response_model=UserListResponse)
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


@router.get("/list", response_model=UserListResponse)
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


@router.get("/{user_id}", response_model=UserResponse)
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


@router.get("/{user_id}/blockchain-id", response_model=BlockchainInfoResponse)
async def get_user_blockchain_id(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get blockchain ID information for a specific user (Admin only).

    Returns blockchain-related information including:
    - Blockchain address
    - Tourist ID token
    - Transaction hash
    - Verification status
    """
    return await UserService.get_user_blockchain_info(db, user_id)


@router.put("/{user_id}/status", response_model=UserResponse)
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
