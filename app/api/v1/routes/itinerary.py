from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.database.user import User
from app.models.schemas.itinerary import (
    ItineraryCreate,
    ItineraryUpdate,
    ItineraryResponse,
    ItineraryListResponse,
    ItineraryDayCreate,
    ItineraryDayUpdate,
    ItineraryDayResponse,
)
from app.services import itinerary as itinerary_service

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("/", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def create_itinerary(
    itinerary_data: ItineraryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new itinerary for the current user.
    """
    try:
        # Validate dates
        if itinerary_data.start_date >= itinerary_data.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date",
            )

        # Calculate duration and validate
        duration = (itinerary_data.end_date - itinerary_data.start_date).days + 1
        if duration != itinerary_data.total_duration_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Total duration days ({itinerary_data.total_duration_days}) doesn't match date range ({duration} days)",
            )

        itinerary = await itinerary_service.create_itinerary(
            itinerary_data=itinerary_data, user_id=current_user.id, db=db
        )

        # Get the complete itinerary with days
        complete_itinerary = await itinerary_service.get_itinerary_by_id_with_days(
            itinerary_id=itinerary.id, user_id=current_user.id, db=db
        )

        if not complete_itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to retrieve created itinerary",
            )

        return complete_itinerary

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        print(f"Error creating itinerary: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create itinerary: {str(e)}",
        )


@router.get("/", response_model=List[ItineraryListResponse])
async def get_user_itineraries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all itineraries for the current user.
    """
    try:
        itineraries = await itinerary_service.get_itineraries_by_user(
            user_id=current_user.id, db=db
        )
        return itineraries

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve itineraries",
        )


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific itinerary by ID (must belong to current user).
    """
    try:
        itinerary = await itinerary_service.get_itinerary_by_id_with_days(
            itinerary_id=itinerary_id, user_id=current_user.id, db=db
        )

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        return itinerary

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve itinerary",
        )


@router.put("/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: int,
    itinerary_data: ItineraryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing itinerary (must belong to current user).
    """
    try:
        # Validate dates if both are provided
        if itinerary_data.start_date and itinerary_data.end_date:
            if itinerary_data.start_date >= itinerary_data.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Start date must be before end date",
                )

        updated_itinerary = await itinerary_service.update_itinerary(
            itinerary_id=itinerary_id,
            itinerary_data=itinerary_data,
            user_id=current_user.id,
            db=db,
        )

        if not updated_itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        return updated_itinerary

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update itinerary",
        )


@router.delete("/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an itinerary (must belong to current user).

    Note: Cannot delete itineraries that have active (ongoing/upcoming) trips.
    Complete or cancel those trips first.
    """
    try:
        success = await itinerary_service.delete_itinerary(
            itinerary_id=itinerary_id, user_id=current_user.id, db=db
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        print(f"Error deleting itinerary: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete itinerary: {str(e)}",
        )


# Itinerary Days endpoints
@router.post(
    "/{itinerary_id}/days",
    response_model=List[ItineraryDayResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_itinerary_days(
    itinerary_id: int,
    days_data: List[ItineraryDayCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add days to an existing itinerary.
    """
    try:
        # Verify itinerary belongs to current user
        itinerary = await itinerary_service.get_itinerary_by_id(
            itinerary_id=itinerary_id, user_id=current_user.id, db=db
        )

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        days = await itinerary_service.create_itinerary_days(
            itinerary_id=itinerary_id, days_data=days_data, db=db
        )

        return days

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add itinerary days",
        )


@router.get("/{itinerary_id}/days", response_model=List[ItineraryDayResponse])
async def get_itinerary_days(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all days for a specific itinerary.
    """
    try:
        # Verify itinerary belongs to current user
        itinerary = await itinerary_service.get_itinerary_by_id(
            itinerary_id=itinerary_id, user_id=current_user.id, db=db
        )

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        days = await itinerary_service.get_itinerary_days(
            itinerary_id=itinerary_id, db=db
        )

        return days

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve itinerary days",
        )


@router.put("/{itinerary_id}/days/{day_id}", response_model=ItineraryDayResponse)
async def update_itinerary_day(
    itinerary_id: int,
    day_id: int,
    day_data: ItineraryDayUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a specific itinerary day.
    """
    try:
        # Verify itinerary belongs to current user
        itinerary = await itinerary_service.get_itinerary_by_id(
            itinerary_id=itinerary_id, user_id=current_user.id, db=db
        )

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        updated_day = await itinerary_service.update_itinerary_day(
            day_id=day_id, itinerary_id=itinerary_id, day_data=day_data, db=db
        )

        if not updated_day:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary day not found"
            )

        return updated_day

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update itinerary day",
        )


@router.delete("/{itinerary_id}/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary_day(
    itinerary_id: int,
    day_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a specific itinerary day.
    """
    try:
        # Verify itinerary belongs to current user
        itinerary = await itinerary_service.get_itinerary_by_id(
            itinerary_id=itinerary_id, user_id=current_user.id, db=db
        )

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        success = await itinerary_service.delete_itinerary_day(
            day_id=day_id, itinerary_id=itinerary_id, db=db
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary day not found"
            )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete itinerary day",
        )
