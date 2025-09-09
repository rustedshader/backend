from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.database.user import User
from app.models.schemas.itinerary import (
    ItineraryCreate,
    ItineraryUpdate,
    ItineraryResponse,
    ItineraryDayResponse,
)
from app.services import itinerary as itinerary_service

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("/", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
async def create_itinerary(
    itinerary_data: ItineraryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new itinerary for the authenticated user. A trip will be automatically created and assigned."""
    try:
        itinerary = await itinerary_service.create_itinerary(
            user_id=current_user.id, itinerary_data=itinerary_data, db=db
        )

        # Get itinerary days for response
        days = await itinerary_service.get_itinerary_days(itinerary.id, db)
        day_responses = [ItineraryDayResponse.model_validate(day) for day in days]

        itinerary_response = ItineraryResponse.model_validate(itinerary)
        itinerary_response.itinerary_days = day_responses

        return itinerary_response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create itinerary: {str(e)}",
        )


@router.get("/", response_model=List[ItineraryResponse])
async def get_my_itineraries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all itineraries for the authenticated user."""
    try:
        itineraries = await itinerary_service.get_user_itineraries(
            user_id=current_user.id, db=db
        )

        response_list = []
        for itinerary in itineraries:
            days = await itinerary_service.get_itinerary_days(itinerary.id, db)
            day_responses = [ItineraryDayResponse.model_validate(day) for day in days]

            itinerary_response = ItineraryResponse.model_validate(itinerary)
            itinerary_response.itinerary_days = day_responses
            response_list.append(itinerary_response)

        return response_list

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch itineraries: {str(e)}",
        )


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(
    itinerary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific itinerary by ID."""
    try:
        itinerary = await itinerary_service.get_itinerary_by_id(
            itinerary_id=itinerary_id, user_id=current_user.id, db=db
        )

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        days = await itinerary_service.get_itinerary_days(itinerary.id, db)
        day_responses = [ItineraryDayResponse.model_validate(day) for day in days]

        itinerary_response = ItineraryResponse.model_validate(itinerary)
        itinerary_response.itinerary_days = day_responses

        return itinerary_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch itinerary: {str(e)}",
        )


@router.patch("/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: int,
    update_data: ItineraryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an itinerary."""
    try:
        itinerary = await itinerary_service.update_itinerary(
            itinerary_id=itinerary_id,
            user_id=current_user.id,
            update_data=update_data,
            db=db,
        )

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
            )

        days = await itinerary_service.get_itinerary_days(itinerary.id, db)
        day_responses = [ItineraryDayResponse.model_validate(day) for day in days]

        itinerary_response = ItineraryResponse.model_validate(itinerary)
        itinerary_response.itinerary_days = day_responses

        return itinerary_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update itinerary: {str(e)}",
        )


@router.delete("/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary(
    itinerary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an itinerary."""
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete itinerary: {str(e)}",
        )
