from fastapi import APIRouter, Depends, status, HTTPException
from app.api.deps import get_current_admin_user, get_current_user
from app.models.schemas.treks import (
    TrekCreate,
    TrekUpdate,
    TrekDataUpdate,
    TrekDataResponse,
)
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.database.treks import Trek
from sqlmodel import Session
from app.services.treks import (
    create_trecks,
    get_trek_by_id,
    get_all_treks,
    get_treks_by_difficulty,
    get_treks_by_state,
    get_treks_by_duration,
    update_trek,
    update_trek_route_data,
    get_geojson_route_data,
    delete_trek,
)

router = APIRouter(prefix="/trek", tags=["trek"])


# Get all treks
@router.get("/list", response_model=list[Trek])
async def get_all_treks_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all available treks."""
    try:
        treks = await get_all_treks(db)
        return treks
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch treks",
        ) from e


# Get treks by difficulty level
@router.get("/difficulty/{difficulty}", response_model=list[Trek])
async def get_treks_by_difficulty_endpoint(
    difficulty: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get treks filtered by difficulty level (easy, medium, hard)."""
    try:
        treks = await get_treks_by_difficulty(difficulty, db)
        return treks
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch treks by difficulty",
        ) from e


# Get treks by state
@router.get("/state/{state}", response_model=list[Trek])
async def get_treks_by_state_endpoint(
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get treks filtered by state."""
    try:
        treks = await get_treks_by_state(state, db)
        return treks
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch treks by state",
        ) from e


# Get treks by duration range
@router.get("/duration", response_model=list[Trek])
async def get_treks_by_duration_endpoint(
    min_duration: int = None,
    max_duration: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get treks filtered by duration range (in hours)."""
    try:
        treks = await get_treks_by_duration(min_duration, max_duration, db)
        return treks
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch treks by duration",
        ) from e


# This would be trek metadata like name, location, etc.
@router.post("/add-trek", response_model=Trek)
async def add_treck(
    admin_user: User = Depends(get_current_admin_user),
    trek_create_data: TrekCreate = None,
    db: Session = Depends(get_db),
):
    if trek_create_data is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Trek data is required"
        )
    try:
        treck = await create_trecks(
            created_by_id=admin_user.id, treck_create_data=trek_create_data, db=db
        )

        return treck
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trek",
        ) from e


# Update trek details like name, location, duration, difficulty level, etc.
@router.put("/{trek_id}/update", response_model=Trek)
async def update_trek_details(
    trek_id: int,
    trek_update_data: TrekUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    try:
        # Check if trek exists
        existing_trek = await get_trek_by_id(trek_id, db)
        if not existing_trek:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )

        # Check if the admin user is the one who created the trek
        if existing_trek.created_by_id != admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update treks that you created",
            )

        # Update the trek
        updated_trek = await update_trek(trek_id, trek_update_data, db)
        if not updated_trek:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update trek",
            )

        return updated_trek
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update trek details",
        ) from e


# This would return basic trek information like name, location, duration, difficulty level, etc.
@router.get("/{trek_id}/information")
async def get_trek_information(
    trek_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        trek = await get_trek_by_id(trek_id, db)
        if not trek:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )
        return trek
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trek information",
        ) from e


# This data would be list of cordinates format (Later)
@router.post("/add-trek-data", response_model=TrekDataResponse)
async def add_treck_data(
    treck_data: TrekDataUpdate,
    admin_user=Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    try:
        trek_route_data = await update_trek_route_data(treck_data, db)
        if not trek_route_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )

        return TrekDataResponse(
            trek_id=trek_route_data.trek_id,
            created_at=trek_route_data.created_at,
            updated_at=trek_route_data.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add trek data",
        ) from e


# Edit/Update trek route data coordinates
@router.put("/edit-trek-data", response_model=TrekDataResponse)
async def edit_trek_route_data(
    trek_data: TrekDataUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    try:
        # Check if trek exists
        existing_trek = await get_trek_by_id(trek_data.trek_id, db)
        if not existing_trek:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )

        # Check if the admin user is the one who created the trek
        if existing_trek.created_by_id != admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit trek data for treks that you created",
            )

        # Update the trek route data
        updated_trek_route_data = await update_trek_route_data(trek_data, db)
        if not updated_trek_route_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update trek route data",
            )

        return TrekDataResponse(
            trek_id=updated_trek_route_data.trek_id,
            created_at=updated_trek_route_data.created_at,
            updated_at=updated_trek_route_data.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit trek route data",
        ) from e


# This would return the geojson data for the trek route (Later)
@router.get("/{trek_id}/route")
async def get_trek_route(
    trek_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        geojson_data = await get_geojson_route_data(trek_id, db)
        return geojson_data
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch trek route data",
        ) from e


# Delete a trek (admin only, creator only)
@router.delete("/{trek_id}")
async def delete_trek_endpoint(
    trek_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    try:
        # Check if trek exists
        existing_trek = await get_trek_by_id(trek_id, db)
        if not existing_trek:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trek not found"
            )

        # Check if the admin user is the one who created the trek
        if existing_trek.created_by_id != admin_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete treks that you created",
            )

        # Delete the trek
        success = await delete_trek(trek_id, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete trek",
            )

        return {"message": "Trek deleted successfully", "trek_id": trek_id}
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trek",
        ) from e
