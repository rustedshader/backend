"""
API routes for itinerary routing functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from app.api.deps import get_current_user, get_db
from app.models.database.user import User
from app.models.schemas.routing import (
    ItineraryRouteRequest,
    ItineraryRouteResponse,
    RouteProfileEnum,
)
from app.services.itinerary_routing import itinerary_routing_service
from app.models.database.itinerary import Itinerary
from sqlmodel import select

router = APIRouter(prefix="/routing", tags=["routing"])


@router.get("/itinerary/{itinerary_id}", response_model=ItineraryRouteResponse)
async def get_itinerary_routes(
    itinerary_id: int,
    profile: RouteProfileEnum = Query(
        RouteProfileEnum.CAR, description="Transportation profile"
    ),
    include_coordinates: bool = Query(True, description="Include route coordinates"),
    include_instructions: bool = Query(
        True, description="Include turn-by-turn instructions"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate routes for an entire itinerary.

    This endpoint calculates routes between:
    - Previous day's accommodation to current day's destination
    - Current day's destination to current day's accommodation

    For trek days: Routes to trek starting point
    For place visit days: Routes to tourist locations
    """
    try:
        # Verify itinerary exists and belongs to user
        itinerary = db.exec(
            select(Itinerary).where(
                Itinerary.id == itinerary_id, Itinerary.user_id == current_user.id
            )
        ).first()

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Itinerary not found or access denied",
            )

        # Generate routes
        routes = await itinerary_routing_service.generate_itinerary_routes(
            itinerary_id=itinerary_id,
            db=db,
            profile=profile.value,
            include_coordinates=include_coordinates,
            include_instructions=include_instructions,
        )

        if not routes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No routes could be generated for this itinerary",
            )

        return routes

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating itinerary routes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate routes",
        )


@router.post("/itinerary/generate", response_model=ItineraryRouteResponse)
async def generate_itinerary_routes(
    request: ItineraryRouteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate routes for an itinerary using POST request with detailed options.

    This is an alternative to the GET endpoint that allows for more complex
    routing configurations in the future.
    """
    try:
        # Verify itinerary exists and belongs to user
        itinerary = db.exec(
            select(Itinerary).where(
                Itinerary.id == request.itinerary_id,
                Itinerary.user_id == current_user.id,
            )
        ).first()

        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Itinerary not found or access denied",
            )

        # Generate routes
        routes = await itinerary_routing_service.generate_itinerary_routes(
            itinerary_id=request.itinerary_id,
            db=db,
            profile=request.profile.value,
            include_coordinates=request.include_coordinates,
            include_instructions=request.include_instructions,
        )

        if not routes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No routes could be generated for this itinerary",
            )

        return routes

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating itinerary routes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate routes",
        )
