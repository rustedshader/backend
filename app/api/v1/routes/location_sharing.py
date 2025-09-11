"""
API endpoints for location sharing with emergency contacts.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.api.deps import get_current_user, get_db
from app.models.database.user import User
from app.models.schemas.location_sharing import (
    ShareLocationRequest,
    ShareLocationWithContactRequest,
    LocationShareResponse,
)
from app.services.location_sharing import LocationSharingService

router = APIRouter(prefix="/location-sharing", tags=["Location Sharing"])


@router.post("/share-with-emergency-contacts", response_model=LocationShareResponse)
async def share_location_with_emergency_contacts(
    request: ShareLocationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Share current location with all emergency contacts from active itinerary.

    This endpoint allows users to quickly share their location with all emergency
    contacts listed in their active itinerary. Useful for check-ins and safety updates.

    Emergency levels:
    - normal: Regular check-in
    - warning: Something concerning but not urgent
    - urgent: Situation needs attention soon
    - emergency: Immediate assistance required
    """
    service = LocationSharingService(db)

    result = await service.share_location_with_emergency_contacts(
        user_id=current_user.id, request=request
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.post("/share-with-contact", response_model=LocationShareResponse)
async def share_location_with_specific_contact(
    request: ShareLocationWithContactRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Share current location with a specific contact.

    This endpoint allows users to share their location with any phone number,
    not just emergency contacts from their itinerary. Useful for sharing with
    friends, family, or other contacts on an ad-hoc basis.
    """
    service = LocationSharingService(db)

    result = await service.share_location_with_contact(
        user_id=current_user.id, request=request
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.post("/emergency-share", response_model=LocationShareResponse)
async def emergency_location_share(
    latitude: float,
    longitude: float,
    emergency_message: str = "EMERGENCY: Need immediate assistance!",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Emergency location share - High priority sharing with all emergency contacts.

    This is a simplified endpoint for emergency situations where the user needs
    to quickly share their location. It automatically uses emergency priority
    and includes trip details.
    """
    service = LocationSharingService(db)

    result = await service.create_emergency_location_share(
        user_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        emergency_message=emergency_message,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.get("/history")
async def get_location_sharing_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's location sharing history.

    Returns a list of recent location shares made by the user,
    including delivery status and contact information.
    """
    service = LocationSharingService(db)

    history = await service.get_user_location_shares(
        user_id=current_user.id, limit=limit
    )

    return {"success": True, "total_shares": len(history), "shares": history}


@router.get("/emergency-contacts")
async def get_emergency_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's emergency contacts from their active itinerary.

    Useful for displaying available emergency contacts in the mobile app
    before sharing location.
    """
    service = LocationSharingService(db)

    contacts = await service._get_user_emergency_contacts(current_user.id)

    return {
        "success": True,
        "contacts": [
            {"name": contact.name, "phone": contact.phone, "relation": contact.relation}
            for contact in contacts
        ],
    }


# Admin endpoint to view all location shares (for monitoring/support)
@router.get("/admin/all-shares")
async def get_all_location_shares(
    limit: int = 100,
    emergency_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to view all location shares for monitoring and support.

    Requires admin role. Useful for:
    - Monitoring emergency situations
    - Support and troubleshooting
    - Analytics on location sharing usage
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Implementation would get all shares with filters
    # For now, return placeholder
    return {
        "success": True,
        "message": "Admin location shares endpoint - implementation needed",
        "filters": {"limit": limit, "emergency_only": emergency_only},
    }
