from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import Optional
from app.api.deps import get_db, get_current_user, get_current_admin_user
from app.models.database.user import User
from app.models.schemas.accommodation import (
    AccommodationCreate,
    AccommodationUpdate,
    AccommodationResponse,
    AccommodationListResponse,
    AccommodationDataResponse,
    AccommodationSearchQuery,
)
from app.services import accommodation as accommodation_service

router = APIRouter(prefix="/accommodations", tags=["accommodations"])


@router.post("/", response_model=AccommodationResponse)
async def create_accommodation(
    accommodation_data: AccommodationCreate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a new accommodation."""
    try:
        accommodation = await accommodation_service.create_accommodation(
            accommodation_data, db
        )
        return AccommodationResponse(**accommodation)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create accommodation: {str(e)}"
        )


@router.get("/", response_model=AccommodationDataResponse)
async def get_accommodations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    name: Optional[str] = Query(None, description="Filter by name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    latitude: Optional[float] = Query(
        None, ge=-90, le=90, description="Latitude for location search"
    ),
    longitude: Optional[float] = Query(
        None, ge=-180, le=180, description="Longitude for location search"
    ),
    radius_km: Optional[float] = Query(
        None, ge=0, le=1000, description="Search radius in kilometers"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get accommodations with optional filtering and pagination."""
    try:
        accommodations, total_count = await accommodation_service.get_accommodations(
            db=db,
            page=page,
            page_size=page_size,
            name=name,
            city=city,
            state=state,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        accommodation_responses = [
            AccommodationResponse(**accommodation) for accommodation in accommodations
        ]

        list_response = AccommodationListResponse(
            accommodations=accommodation_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

        return AccommodationDataResponse(
            success=True,
            data=list_response,
            message="Accommodations retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch accommodations: {str(e)}"
        )


@router.get("/search/name", response_model=AccommodationDataResponse)
async def search_accommodations_by_name(
    name: str = Query(..., description="Search term for accommodation name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search accommodations by name with pagination."""
    try:
        search_query = AccommodationSearchQuery(name=name)

        accommodations, total_count = await accommodation_service.search_accommodations(
            search_query=search_query,
            db=db,
            page=page,
            page_size=page_size,
        )

        accommodation_responses = [
            AccommodationResponse(**accommodation) for accommodation in accommodations
        ]

        list_response = AccommodationListResponse(
            accommodations=accommodation_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

        return AccommodationDataResponse(
            success=True,
            data=list_response,
            message="Accommodations found successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search accommodations by name: {str(e)}"
        )


@router.get("/{accommodation_id}", response_model=AccommodationResponse)
async def get_accommodation(
    accommodation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific accommodation by ID."""
    try:
        accommodation = await accommodation_service.get_accommodation_by_id(
            accommodation_id, db
        )
        if not accommodation:
            raise HTTPException(status_code=404, detail="Accommodation not found")

        return AccommodationResponse(**accommodation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch accommodation: {str(e)}"
        )


@router.put("/{accommodation_id}", response_model=AccommodationResponse)
async def update_accommodation(
    accommodation_id: int,
    update_data: AccommodationUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Update an accommodation."""
    try:
        accommodation = await accommodation_service.update_accommodation(
            accommodation_id, update_data, db
        )
        if not accommodation:
            raise HTTPException(status_code=404, detail="Accommodation not found")

        return AccommodationResponse(**accommodation)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to update accommodation: {str(e)}"
        )


@router.delete("/{accommodation_id}")
async def delete_accommodation(
    accommodation_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete an accommodation."""
    try:
        deleted = await accommodation_service.delete_accommodation(accommodation_id, db)
        if not deleted:
            raise HTTPException(status_code=404, detail="Accommodation not found")

        return {"message": "Accommodation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to delete accommodation: {str(e)}"
        )


@router.post("/search", response_model=AccommodationDataResponse)
async def search_accommodations(
    search_query: AccommodationSearchQuery,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search accommodations based on criteria."""
    try:
        accommodations, total_count = await accommodation_service.search_accommodations(
            search_query, db, page, page_size
        )

        accommodation_responses = [
            AccommodationResponse(**accommodation) for accommodation in accommodations
        ]

        list_response = AccommodationListResponse(
            accommodations=accommodation_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

        return AccommodationDataResponse(
            success=True,
            data=list_response,
            message="Accommodation search completed successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search accommodations: {str(e)}"
        )
