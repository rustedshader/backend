from typing import Optional, List
from fastapi import APIRouter, Depends, status, HTTPException, Query
from app.api.deps import get_current_admin_user, get_current_user
from app.models.database.base import get_db
from app.models.database.user import User
from sqlmodel import Session
from app.services.offline_activities import (
    create_offline_activity,
    get_offline_activity_by_id,
    get_offline_activities_with_filters,
    get_geojson_route_data,
    delete_offline_activity,
    update_offline_activity,
    update_offline_activity_route_data,
    _get_offline_activity_raw_by_id,
)
from app.models.schemas.offline_activity import (
    OfflineActivityCreate,
    OfflineActivityUpdate,
    OfflineActivityResponse,
    OfflineActivityDataResponse,
    OfflineActivityDataUpdate,
)

router = APIRouter(prefix="/offline_activities", tags=["offline_activities"])


@router.get("/", response_model=List[OfflineActivityResponse])
async def get_offline_activities_endpoint(
    state: Optional[str] = Query(None, description="Filter by state"),
    difficulty: Optional[str] = Query(
        None, description="Filter by difficulty level (easy, medium, hard)"
    ),
    city: Optional[str] = Query(None, description="Filter by city"),
    district: Optional[str] = Query(None, description="Filter by district"),
    limit: int = Query(default=100, le=1000, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get offline activities with optional filters."""
    try:
        offline_activities = await get_offline_activities_with_filters(
            db,
            state=state,
            difficulty=difficulty,
            city=city,
            district=district,
            limit=limit,
        )
        return offline_activities
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch offline activities",
        ) from e


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_offline_activity_endpoint(
    offline_activity_create: OfflineActivityCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a new offline activity (admin only)."""
    try:
        offline_activity = await create_offline_activity(
            created_by_id=admin_user.id,
            offline_activity_create_data=offline_activity_create,
            db=db,
        )
        return offline_activity
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create offline activity",
        ) from e


@router.put("/{offline_activity_id}")
async def update_offline_activity_endpoint(
    offline_activity_id: int,
    offline_activity_update: OfflineActivityUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update an existing offline activity (admin only)."""
    try:
        # Check if activity exists
        existing_activity = await _get_offline_activity_raw_by_id(
            offline_activity_id, db
        )
        if not existing_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline activity not found",
            )

        # Check if admin created this activity
        if existing_activity.created_by != admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update activities that you created",
            )

        updated_activity = await update_offline_activity(
            activity_id=offline_activity_id,
            activity_update_data=offline_activity_update,
            db=db,
        )

        if not updated_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline activity not found",
            )

        return updated_activity
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update offline activity",
        ) from e


# This would return basic trek information like name, location, duration, difficulty level, etc.
@router.get("/{offline_activity_id}/information")
async def get_offline_activity_information(
    offline_activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        offline_activity = await get_offline_activity_by_id(offline_activity_id, db)
        if not offline_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline Activity not found",
            )
        return offline_activity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Offline Activity information",
        ) from e


# This data would be list of coordinates format
@router.post("/route-data", response_model=OfflineActivityDataResponse)
async def add_offline_activity_route_data(
    offline_activity_route_data: OfflineActivityDataUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Add or update route data for an offline activity (admin only)."""
    try:
        # Check if activity exists
        activity = await _get_offline_activity_raw_by_id(
            offline_activity_route_data.offline_activity_id, db
        )
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline activity not found",
            )

        # Check if admin created this activity
        if activity.created_by != admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update route data for activities that you created",
            )

        offline_activity_route = await update_offline_activity_route_data(
            offline_activity_route_data, db
        )
        if not offline_activity_route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline activity not found",
            )

        return OfflineActivityDataResponse(
            offline_activity_id=offline_activity_route.id,
            created_at=int(offline_activity_route.created_at.timestamp()),
            updated_at=int(offline_activity_route.updated_at.timestamp()),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add offline activity route data",
        ) from e


@router.get("/{offline_activity_id}/route")
async def get_offline_activity_route(
    offline_activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get route data (GeoJSON) for a specific offline activity."""
    try:
        # Check if activity exists
        activity = await get_offline_activity_by_id(offline_activity_id, db)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline activity not found",
            )

        geojson_data = await get_geojson_route_data(offline_activity_id, db)
        if not geojson_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Route data not found for this activity",
            )

        return geojson_data
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch offline activity route data",
        ) from e


@router.delete("/{offline_activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offline_activity_endpoint(
    offline_activity_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete an offline activity (admin only)."""
    try:
        existing_activity = await _get_offline_activity_raw_by_id(
            offline_activity_id, db
        )
        if not existing_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offline activity not found",
            )

        if existing_activity.created_by != admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete activities that you created",
            )

        success = await delete_offline_activity(offline_activity_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete offline activity",
            )

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete offline activity",
        ) from e
