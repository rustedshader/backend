from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import get_current_admin_user, get_current_user
from app.models.schemas.treks import OfflineActivityCreate
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.database.offline_activity import OfflineActivity
from sqlmodel import Session
from app.services.offline_activities import (
    create_offline_activity,
    get_offline_activity_by_id,
    get_all_offline_activities,
    get_offline_activities_by_difficulty,
    get_offline_activities_by_state,
    get_geojson_route_data,
    delete_offline_activity,
    update_offline_activity_route_data,
)
from app.models.schemas.offline_activity import (
    OfflineActivityDataResponse,
    OfflineActivityDataUpdate,
)
from typing import List

router = APIRouter(prefix="/offline_activities", tags=["offline_activities"])


@router.get("/list", response_model=List[OfflineActivity])
async def list_all_offline_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all available offline activities."""
    try:
        offline_activities = await get_all_offline_activities(db)
        return offline_activities
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch offline activities",
        ) from e


@router.get("/difficulty/{difficulty}", response_model=List[OfflineActivity])
async def get_offline_activity_by_endpoint(
    difficulty: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get offline activities filtered by difficulty level (easy, medium, hard)."""
    try:
        offline_activities = await get_offline_activities_by_difficulty(difficulty, db)
        return offline_activities
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch offline activities by difficulty",
        ) from e


@router.get("/state/{state}", response_model=List[OfflineActivity])
async def get_offline_activity_by_state(
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get offline activities filtered by state."""
    try:
        offline_activities = await get_offline_activities_by_state(state, db)
        return offline_activities
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch offline activities by state",
        ) from e


@router.post("create-offline-activity", response_model=OfflineActivity)
async def create_offline_activity_endpoint(
    admin_user: User = Depends(get_current_admin_user),
    offline_activity_create: OfflineActivityCreate = None,
    db: Session = Depends(get_db),
):
    if offline_activity_create is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offline Activity Create data is required",
        )
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


# This data would be list of cordinates format (Later)
@router.post("/add-offline-activity-route", response_model=OfflineActivityDataResponse)
async def add_treck_data(
    offline_activity_route_data: OfflineActivityDataUpdate,
    admin_user=Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    try:
        offline_activity_route = await update_offline_activity_route_data(
            offline_activity_route_data, db
        )
        if not offline_activity_route:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )

        return OfflineActivityDataResponse(
            offline_activity_id=offline_activity_route.id,
            created_at=offline_activity_route.created_at,
            updated_at=offline_activity_route.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add trek data",
        ) from e


@router.get("/{offline_activity_id}/route")
async def get_offline_activity_route(
    offline_activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        geojson_data = await get_geojson_route_data(offline_activity_id, db)
        return geojson_data
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trek route data",
        ) from e


@router.delete("/{offline_activity_id}")
async def delete_offline_activity_endpoint(
    offline_activity_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    try:
        existing_trek = await get_offline_activity_by_id(offline_activity_id, db)
        if not existing_trek:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )

        if existing_trek.created_by != admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete treks that you created",
            )

        success = await delete_offline_activity(offline_activity_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete trek",
            )

        return {"message": "Trek deleted successfully", "trek_id": offline_activity_id}
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trek",
        ) from e
