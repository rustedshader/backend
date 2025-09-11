"""
Test endpoints for geofencing integration with routing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.api.deps import get_current_user, get_db
from app.models.database.user import User
from app.models.schemas.routing_test import RoutingTestRequest, RoutingTestResponse

router = APIRouter(prefix="/routing-test", tags=["routing-test"])


@router.post("/test-route-with-geofencing", response_model=RoutingTestResponse)
async def test_route_with_geofencing(
    request: RoutingTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test route generation with geofencing integration.

    This endpoint allows testing the routing functionality with restricted areas
    automatically included as block_areas in the GraphHopper request.

    Example usage:
    POST /routing-test/test-route-with-geofencing
    {
        "start_lat": 26.166653,
        "start_lon": 91.779409,
        "end_lat": 26.171218,
        "end_lon": 91.83634,
        "profile": "car"
    }
    """
    try:
        from app.services.routing import graphhopper_service

        route_data = await graphhopper_service.get_route(
            start_lat=request.start_lat,
            start_lon=request.start_lon,
            end_lat=request.end_lat,
            end_lon=request.end_lon,
            profile=request.profile,
            db=db,
            include_block_areas=True,
        )

        if not route_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No route could be generated between the specified points",
            )

        # Extract route summary for easier consumption
        summary = graphhopper_service.extract_route_summary(route_data)

        # Get the list of blocked areas that were used
        from app.services.geofencing import get_active_restricted_areas_for_routing

        blocked_areas = await get_active_restricted_areas_for_routing(db)

        return {
            "route_summary": summary,
            "raw_route_data": route_data,
            "blocked_areas_count": len(blocked_areas),
            "blocked_areas": blocked_areas[:5]
            if blocked_areas
            else [],  # Show first 5 for debugging
            "request_details": {
                "start": {
                    "latitude": request.start_lat,
                    "longitude": request.start_lon,
                },
                "end": {"latitude": request.end_lat, "longitude": request.end_lon},
                "profile": request.profile,
                "geofencing_enabled": True,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error testing route with geofencing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test route: {str(e)}",
        )


@router.get("/debug/active-restricted-areas")
async def debug_get_active_restricted_areas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Debug endpoint to see all active restricted areas that would be used for routing.
    """
    try:
        from app.services.geofencing import get_active_restricted_areas_for_routing

        blocked_areas = await get_active_restricted_areas_for_routing(db)

        return {
            "active_restricted_areas_count": len(blocked_areas),
            "active_restricted_areas": blocked_areas,
            "example_graphhopper_payload": {
                "profile": "car",
                "points_encoded": False,
                "points": [[91.779409, 26.166653], [91.83634, 26.171218]],
                "block_areas": blocked_areas[:3]
                if blocked_areas
                else [],  # Show first 3 as example
            },
        }

    except Exception as e:
        print(f"Error fetching active restricted areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch restricted areas: {str(e)}",
        )
