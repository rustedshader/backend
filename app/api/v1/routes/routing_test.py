"""
Test endpoints for geofencing integration with routing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.api.deps import get_current_user, get_db
from app.models.database.user import User
from app.models.schemas.routing_test import RoutingTestRequest

router = APIRouter(prefix="/routing-test", tags=["routing-test"])


@router.post("/test-route-with-geofencing")
async def test_route_with_geofencing(
    request: RoutingTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test route generation with geofencing integration.
    Returns a GeoJSON Feature with route geometry and properties.

    Example usage:
    POST /routing-test/test-route-with-geofencing
    {
        "start_lat": 26.166653,
        "start_lon": 91.779409,
        "end_lat": 26.171218,
        "end_lon": 91.83634,
        "profile": "car"
    }

    Returns:
    {
        "type": "Feature",
        "properties": {
            "distance_meters": 5432.1,
            "distance_km": 5.43,
            "time_seconds": 1234,
            "time_minutes": 20.6,
            "profile": "car"
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [[lon1, lat1], [lon2, lat2], ...]
        }
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

        # Create GeoJSON Feature for the route
        return {
            "type": "Feature",
            "properties": {
                "distance_meters": summary.get("distance_meters", 0),
                "distance_km": summary.get("distance_km", 0),
                "time_seconds": summary.get("time_seconds", 0),
                "time_minutes": summary.get("time_minutes", 0),
                "profile": request.profile,
            },
            "geometry": summary.get(
                "geometry", {"type": "LineString", "coordinates": []}
            ),
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


@router.get("/debug/check-database", include_in_schema=False)
async def debug_check_database(db: Session = Depends(get_db)):
    """
    Debug endpoint to check database connection and table status.
    No authentication required for debugging.
    """
    try:
        from sqlalchemy import text

        # Check if restricted_areas table exists and has data
        result = db.execute(
            text("""
                SELECT COUNT(*) as total_count,
                       COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) as active_count,
                       COUNT(CASE WHEN boundary IS NOT NULL THEN 1 END) as with_geometry_count
                FROM restricted_areas
            """)
        ).first()

        # Get a sample of restricted areas
        sample_areas = db.execute(
            text("""
                SELECT id, name, area_type, status, 
                       ST_AsText(boundary) as wkt_geometry,
                       valid_from, valid_until
                FROM restricted_areas 
                LIMIT 5
            """)
        ).fetchall()

        return {
            "database_status": "connected",
            "restricted_areas_stats": {
                "total": result.total_count if result else 0,
                "active": result.active_count if result else 0,
                "with_geometry": result.with_geometry_count if result else 0,
            },
            "sample_areas": [
                {
                    "id": area.id,
                    "name": area.name,
                    "area_type": area.area_type,
                    "status": area.status,
                    "has_geometry": bool(area.wkt_geometry),
                    "wkt_preview": area.wkt_geometry[:100] + "..."
                    if area.wkt_geometry and len(area.wkt_geometry) > 100
                    else area.wkt_geometry,
                    "valid_from": str(area.valid_from) if area.valid_from else None,
                    "valid_until": str(area.valid_until) if area.valid_until else None,
                }
                for area in sample_areas
            ],
        }

    except Exception as e:
        return {
            "database_status": "error",
            "error": str(e),
            "message": "Failed to connect to database or query restricted areas",
        }


@router.post("/test-route-simple", include_in_schema=False)
async def test_route_simple(
    request: RoutingTestRequest,
    db: Session = Depends(get_db),
):
    """
    Simple route test without authentication for debugging purposes.
    """
    try:
        from app.services.routing import graphhopper_service
        from app.services.geofencing import get_active_restricted_areas_for_routing

        # Get blocked areas first for debugging
        blocked_areas = await get_active_restricted_areas_for_routing(db)

        print(f"DEBUG: Found {len(blocked_areas)} blocked areas")
        for i, area in enumerate(blocked_areas[:3]):
            print(f"DEBUG: Blocked area {i + 1}: {area[:100]}...")

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
            return {
                "error": "No route found",
                "blocked_areas_count": len(blocked_areas),
                "blocked_areas": blocked_areas[:2],
                "request": {
                    "start": [request.start_lat, request.start_lon],
                    "end": [request.end_lat, request.end_lon],
                    "profile": request.profile,
                },
            }

        summary = graphhopper_service.extract_route_summary(route_data)

        return {
            "success": True,
            "geojson": {
                "type": "Feature",
                "properties": {
                    "distance_km": summary.get("distance_km", 0),
                    "time_minutes": summary.get("time_minutes", 0),
                    "blocked_areas_count": len(blocked_areas),
                },
                "geometry": summary.get(
                    "geometry", {"type": "LineString", "coordinates": []}
                ),
            },
            "debug": {
                "blocked_areas_count": len(blocked_areas),
                "route_points_count": len(summary.get("coordinates", [])),
                "graphhopper_payload_sent": {
                    "profile": request.profile,
                    "points": [
                        [request.start_lon, request.start_lat],
                        [request.end_lon, request.end_lat],
                    ],
                    "block_areas_count": len(blocked_areas),
                    "block_areas_sample": blocked_areas[:1] if blocked_areas else [],
                },
            },
        }

    except Exception as e:
        print(f"Error in simple route test: {e}")
        return {
            "error": str(e),
            "request": {
                "start": [request.start_lat, request.start_lon],
                "end": [request.end_lat, request.end_lon],
                "profile": request.profile,
            },
        }
