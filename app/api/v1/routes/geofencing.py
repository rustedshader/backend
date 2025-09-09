from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from app.api.deps import get_current_admin_user, get_current_user
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.schemas.geofencing import (
    RestrictedAreaCreate,
    RestrictedAreaUpdate,
    RestrictedAreaResponse,
    RestrictedAreaSummary,
    GeofenceCheckRequest,
    GeofenceCheckResponse,
    RestrictedAreaStatusEnum,
    RestrictedAreaTypeEnum,
)
from app.services.geofencing import (
    create_restricted_area,
    get_restricted_area_by_id,
    get_all_restricted_areas,
    update_restricted_area,
    delete_restricted_area,
    check_location_restrictions,
)

router = APIRouter(prefix="/geofencing", tags=["geofencing"])


@router.post("/restricted-areas", response_model=RestrictedAreaResponse)
async def create_restricted_area_endpoint(
    area_data: RestrictedAreaCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Create a new restricted area (Admin only).

    This endpoint allows administrators to define geographic areas where tourists
    should not enter or should receive warnings when approaching.

    The boundary_coordinates should form a closed polygon with at least 3 points.
    Coordinates should be in WGS84 format (longitude, latitude).
    """
    return await create_restricted_area(area_data, admin_user.id, db)


@router.get("/restricted-areas", response_model=List[RestrictedAreaSummary])
async def get_restricted_areas(
    status_filter: Optional[RestrictedAreaStatusEnum] = Query(
        None, description="Filter by status"
    ),
    area_type_filter: Optional[RestrictedAreaTypeEnum] = Query(
        None, description="Filter by area type"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get all restricted areas with optional filtering (Admin only).

    Returns a summary list of all restricted areas with basic information.
    Use the individual endpoint to get full details including coordinates.
    """
    return await get_all_restricted_areas(
        db=db,
        status_filter=status_filter.value if status_filter else None,
        area_type_filter=area_type_filter.value if area_type_filter else None,
        limit=limit,
        offset=offset,
    )


@router.get("/restricted-areas/{area_id}", response_model=RestrictedAreaResponse)
async def get_restricted_area(
    area_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific restricted area (Admin only).

    Returns full details including the polygon coordinates for the area boundary.
    """
    return await get_restricted_area_by_id(area_id, db)


@router.put("/restricted-areas/{area_id}", response_model=RestrictedAreaResponse)
async def update_restricted_area_endpoint(
    area_id: int,
    area_data: RestrictedAreaUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing restricted area (Admin only).

    Allows administrators to modify any aspect of a restricted area,
    including its boundaries, status, and enforcement settings.
    """
    return await update_restricted_area(area_id, area_data, db)


@router.delete("/restricted-areas/{area_id}")
async def delete_restricted_area_endpoint(
    area_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Delete a restricted area (Admin only).

    Permanently removes a restricted area from the system.
    This action cannot be undone.
    """
    success = await delete_restricted_area(area_id, db)
    if success:
        return {"message": "Restricted area deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete restricted area",
        )


@router.post("/check-location", response_model=GeofenceCheckResponse)
async def check_location_endpoint(
    location_data: GeofenceCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check if a location is within any restricted areas.

    This endpoint can be used by mobile applications to check if a user's
    current location or planned destination is within a restricted area.

    If user_id is provided, violations will be logged for tracking purposes.
    """
    return await check_location_restrictions(
        longitude=location_data.longitude,
        latitude=location_data.latitude,
        db=db,
        user_id=location_data.user_id or current_user.id,
    )


@router.get(
    "/check-location/{longitude}/{latitude}", response_model=GeofenceCheckResponse
)
async def check_coordinates_endpoint(
    longitude: float,
    latitude: float,
    log_violations: bool = Query(
        True, description="Whether to log violations for the current user"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check if specific coordinates are within any restricted areas.

    Alternative endpoint for checking coordinates via URL parameters instead of request body.
    Useful for simple GET requests from frontend applications.
    """
    # Validate coordinate ranges
    if not (-180 <= longitude <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180",
        )
    if not (-90 <= latitude <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90",
        )

    return await check_location_restrictions(
        longitude=longitude,
        latitude=latitude,
        db=db,
        user_id=current_user.id if log_violations else None,
    )


# Public endpoint for basic area information (without detailed coordinates)
@router.get("/public/restricted-areas", response_model=List[RestrictedAreaSummary])
async def get_public_restricted_areas(
    area_type_filter: Optional[RestrictedAreaTypeEnum] = Query(
        None, description="Filter by area type"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """
    Get basic information about active restricted areas (Public access).

    This endpoint provides general information about restricted areas without
    requiring authentication. It only returns basic details and does not
    include precise boundary coordinates for security reasons.
    """
    return await get_all_restricted_areas(
        db=db,
        status_filter="active",  # Only return active areas
        area_type_filter=area_type_filter.value if area_type_filter else None,
        limit=min(limit, 100),  # Cap at 100 for public endpoint
        offset=offset,
    )


@router.get("/admin/area-types")
async def get_area_types(
    admin_user: User = Depends(get_current_admin_user),
):
    """
    Get all available restricted area types (Admin only).

    Returns the list of available area types that can be used when creating
    restricted areas.
    """
    return {
        "area_types": [
            {
                "value": area_type.value,
                "label": area_type.value.replace("_", " ").title(),
                "description": _get_area_type_description(area_type),
            }
            for area_type in RestrictedAreaTypeEnum
        ]
    }


@router.get("/admin/status-types")
async def get_status_types(
    admin_user: User = Depends(get_current_admin_user),
):
    """
    Get all available restricted area status types (Admin only).

    Returns the list of available status types for restricted areas.
    """
    return {
        "status_types": [
            {
                "value": status_type.value,
                "label": status_type.value.replace("_", " ").title(),
                "description": _get_status_type_description(status_type),
            }
            for status_type in RestrictedAreaStatusEnum
        ]
    }


def _get_area_type_description(area_type: RestrictedAreaTypeEnum) -> str:
    """Get description for area type"""
    descriptions = {
        RestrictedAreaTypeEnum.RESTRICTED_ZONE: "General restricted area where access is limited",
        RestrictedAreaTypeEnum.DANGER_ZONE: "Area with potential safety hazards",
        RestrictedAreaTypeEnum.PRIVATE_PROPERTY: "Private property where trespassing is prohibited",
        RestrictedAreaTypeEnum.PROTECTED_AREA: "Environmentally protected area with access restrictions",
        RestrictedAreaTypeEnum.MILITARY_ZONE: "Military installation or security-sensitive area",
        RestrictedAreaTypeEnum.SEASONAL_CLOSURE: "Area closed during specific seasons or periods",
    }
    return descriptions.get(area_type, "No description available")


def _get_status_type_description(status_type: RestrictedAreaStatusEnum) -> str:
    """Get description for status type"""
    descriptions = {
        RestrictedAreaStatusEnum.ACTIVE: "Area restriction is currently active and enforced",
        RestrictedAreaStatusEnum.INACTIVE: "Area restriction is not currently active",
        RestrictedAreaStatusEnum.TEMPORARILY_DISABLED: "Area restriction is temporarily disabled for maintenance or other reasons",
    }
    return descriptions.get(status_type, "No description available")
