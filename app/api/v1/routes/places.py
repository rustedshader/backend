from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List
from app.api.deps import get_db, get_current_admin_user, get_current_user
from app.models.database.user import User
from app.models.schemas.places import (
    PlaceCreate,
    PlaceUpdate,
    PlaceResponse,
    PlaceSearchQuery,
    PlaceListResponse,
)
from app.services import places as places_service

router = APIRouter(prefix="/places", tags=["places"])


# Public endpoints for users to browse places
@router.get("/", response_model=PlaceListResponse)
async def get_places(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    city: str = Query(None),
    state: str = Query(None),
    place_type: str = Query(None),
    is_featured: bool = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get places with filtering and pagination."""
    try:
        search_query = PlaceSearchQuery(
            city=city,
            state=state,
            place_type=place_type,
            is_featured=is_featured,
        )

        places, total_count = await places_service.search_places(
            search_query=search_query, page=page, page_size=page_size, db=db
        )

        place_responses = [PlaceResponse.model_validate(place) for place in places]

        return PlaceListResponse(
            places=place_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch places: {str(e)}",
        )


@router.get("/featured", response_model=List[PlaceResponse])
async def get_featured_places(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get featured places."""
    try:
        places = await places_service.get_featured_places(db=db, limit=limit)
        return [PlaceResponse.model_validate(place) for place in places]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch featured places: {str(e)}",
        )


@router.get("/search", response_model=List[PlaceResponse])
async def search_places_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, ge=0.1, le=100),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search places within a radius of given coordinates."""
    try:
        places = await places_service.get_nearby_places(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            db=db,
            limit=limit,
        )
        return [PlaceResponse.model_validate(place) for place in places]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search nearby places: {str(e)}",
        )


@router.get("/type/{place_type}", response_model=List[PlaceResponse])
async def get_places_by_type(
    place_type: str,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get places by type."""
    try:
        places = await places_service.get_places_by_type(
            place_type=place_type, db=db, limit=limit
        )
        return [PlaceResponse.model_validate(place) for place in places]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch places by type: {str(e)}",
        )


@router.get("/city/{city}", response_model=List[PlaceResponse])
async def get_places_by_city(
    city: str,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get places in a specific city."""
    try:
        places = await places_service.get_places_by_city(city=city, db=db, limit=limit)
        return [PlaceResponse.model_validate(place) for place in places]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch places by city: {str(e)}",
        )


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(
    place_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific place by ID."""
    try:
        place = await places_service.get_place_by_id(place_id=place_id, db=db)

        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
            )

        return PlaceResponse.model_validate(place)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch place: {str(e)}",
        )


# Admin endpoints for managing places
@router.post(
    "/admin/", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED
)
async def create_place(
    place_data: PlaceCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a new place (admin only)."""
    try:
        place = await places_service.create_place(
            place_data=place_data, admin_id=current_admin.id, db=db
        )

        return PlaceResponse.model_validate(place)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create place: {str(e)}",
        )


@router.patch("/admin/{place_id}", response_model=PlaceResponse)
async def update_place(
    place_id: int,
    update_data: PlaceUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update a place (admin only)."""
    try:
        place = await places_service.update_place(
            place_id=place_id, update_data=update_data, db=db
        )

        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
            )

        return PlaceResponse.model_validate(place)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update place: {str(e)}",
        )


@router.delete("/admin/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    place_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete a place (admin only)."""
    try:
        success = await places_service.delete_place(place_id=place_id, db=db)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete place: {str(e)}",
        )
