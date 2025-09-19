from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List
from app.api.deps import get_db, get_current_admin_user, get_current_user
from app.models.database.user import User

from app.models.schemas.online_activity import (
    OnlineActivityCreate,
    OnlineActivityUpdate,
    OnlineActivityResponse,
    OnlineActivitySearchQuery,
    OnlineActivityListResponse,
)
from app.services import online_activity as online_activity_service

router = APIRouter(prefix="/online-activities", tags=["online_activities"])


# Public endpoints for users to browse online activities
@router.get("/", response_model=OnlineActivityListResponse)
async def get_online_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: str = Query(None),
    state: str = Query(None),
    place_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get online activities with optional filters and pagination.

    Available filters:
    - city: Filter by city name (partial match)
    - state: Filter by state name (partial match)
    - place_type: Filter by place type
    - page: Page number for pagination (default: 1)
    - page_size: Number of results per page (default: 20, max: 100)
    """
    try:
        search_query = OnlineActivitySearchQuery(
            city=city,
            state=state,
            place_type=place_type,
        )

        (
            activities,
            total_count,
        ) = await online_activity_service.search_online_activities(
            search_query=search_query, page=page, page_size=page_size, db=db
        )

        activity_responses = [
            OnlineActivityResponse.model_validate(activity) for activity in activities
        ]

        return OnlineActivityListResponse(
            online_activities=activity_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch online activities: {str(e)}",
        )


@router.get("/search", response_model=List[OnlineActivityResponse])
async def search_online_activities_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, ge=0.1, le=100),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search online activities within a radius of given coordinates."""
    try:
        activities = await online_activity_service.get_nearby_online_activities(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            db=db,
            limit=limit,
        )
        return [
            OnlineActivityResponse.model_validate(activity) for activity in activities
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search nearby online activities: {str(e)}",
        )


@router.get("/{activity_id}", response_model=OnlineActivityResponse)
async def get_online_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific online activity by ID."""
    try:
        activity = await online_activity_service.get_online_activity_by_id(
            online_activity_id=activity_id, db=db
        )

        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Online activity not found",
            )

        return OnlineActivityResponse.model_validate(activity)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch online activity: {str(e)}",
        )


# Admin endpoints for managing online activities
@router.post(
    "/",
    response_model=OnlineActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_online_activity(
    activity_data: OnlineActivityCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a new online activity (admin only)."""
    try:
        activity = await online_activity_service.create_online_activity(
            online_activity_data=activity_data, admin_id=current_admin.id, db=db
        )

        return OnlineActivityResponse.model_validate(activity)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create online activity: {str(e)}",
        )


@router.put("/{activity_id}", response_model=OnlineActivityResponse)
async def update_online_activity(
    activity_id: int,
    update_data: OnlineActivityUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update an online activity (admin only)."""
    try:
        activity = await online_activity_service.update_online_activity(
            online_activity_id=activity_id, update_data=update_data, db=db
        )

        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Online activity not found",
            )

        return OnlineActivityResponse.model_validate(activity)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update online activity: {str(e)}",
        )


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_online_activity(
    activity_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete an online activity (admin only)."""
    try:
        success = await online_activity_service.delete_online_activity(
            online_activity_id=activity_id, db=db
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Online activity not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete online activity: {str(e)}",
        )
