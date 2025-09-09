"""
Enhanced API endpoints for button-driven trip tracking workflow.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import Optional
import datetime
from app.api.deps import get_current_user, get_session
from app.models.database.user import User
from app.models.schemas.trip_tracking import LiveLocationUpdate, TripTypeEnum
from app.services.trip_tracking import TripTrackingService

router = APIRouter(prefix="/trip", tags=["Trip Workflow"])


# ================== BUTTON-DRIVEN WORKFLOW ENDPOINTS ==================


@router.post("/{trip_id}/start-day")
async def start_day(
    trip_id: int,
    trip_type: TripTypeEnum,
    hotel_lat: float,
    hotel_lon: float,
    hotel_name: str,
    destination_lat: Optional[float] = None,
    destination_lon: Optional[float] = None,
    destination_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    🟢 START DAY BUTTON
    Tourist presses this button to start their day.
    For trek days: Gets route from hotel to trek start.
    For tour days: Gets route from hotel to tourist destination.
    """
    service = TripTrackingService(db)

    result = await service.start_day(
        trip_id=trip_id,
        trip_type=trip_type,
        hotel_lat=hotel_lat,
        hotel_lon=hotel_lon,
        hotel_name=hotel_name,
        destination_lat=destination_lat,
        destination_lon=destination_lon,
        destination_name=destination_name,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/{trip_id}/visiting")
async def set_visiting_status(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    🟡 VISITING BUTTON
    Tourist presses this when they reach the destination (tour location).
    Status changes to 'visiting'.
    """
    service = TripTrackingService(db)

    result = await service.set_visiting_status(trip_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/{trip_id}/link-device")
async def link_tracking_device(
    trip_id: int,
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    🔗 LINK DEVICE BUTTON (Trek Days Only)
    Tourist links their tracking device before starting trek.
    """
    service = TripTrackingService(db)

    result = await service.link_tracking_device(trip_id, device_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/{trip_id}/start-trek")
async def start_trek(
    trip_id: int,
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    🥾 START TREK BUTTON (Trek Days Only)
    Tourist starts the trek with linked tracking device.
    Gets offline trek data and switches to device tracking.
    """
    service = TripTrackingService(db)

    result = await service.start_trek(trip_id, device_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/{trip_id}/end-trek")
async def end_trek(
    trip_id: int,
    trek_end_lat: float,
    trek_end_lon: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    🏁 END TREK BUTTON (Trek Days Only)
    Tourist ends the trek and requests route back to hotel.
    Mobile GPS tracking resumes.
    """
    service = TripTrackingService(db)

    result = await service.end_trek(trip_id, trek_end_lat, trek_end_lon)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/{trip_id}/return-to-hotel")
async def request_return_route(
    trip_id: int,
    current_lat: float,
    current_lon: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    🏨 RETURN TO HOTEL BUTTON
    Tourist requests route back to hotel from current location.
    Status changes to 'returning'.
    """
    service = TripTrackingService(db)

    result = await service.request_return_route(trip_id, current_lat, current_lon)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


# ================== LIVE LOCATION TRACKING ENDPOINT ==================


@router.post("/{trip_id}/live-location")
async def update_live_location(
    trip_id: int,
    latitude: float,
    longitude: float,
    timestamp: int,
    altitude: Optional[float] = None,
    accuracy: Optional[float] = None,
    speed: Optional[float] = None,
    bearing: Optional[float] = None,
    source: str = "mobile_gps",
    device_id: Optional[str] = None,
    battery_level: Optional[int] = None,
    emergency: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    📍 LIVE LOCATION ENDPOINT
    Continuous location updates from mobile phone or tracking device.
    Used throughout the entire journey.
    """
    service = TripTrackingService(db)

    # Create live update object
    live_update = LiveLocationUpdate(
        trip_id=trip_id,
        user_id=current_user.id,
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        accuracy=accuracy,
        speed=speed,
        bearing=bearing,
        timestamp=timestamp,
        source=source,
        emergency=emergency,
    )

    success = await service.record_live_location(live_update)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to record live location")

    return {
        "success": True,
        "message": "Location updated",
        "timestamp": timestamp,
        "emergency_alert": emergency,
    }


@router.get("/{trip_id}/current-status")
async def get_trip_current_status(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    📊 GET CURRENT STATUS
    Get current trip status, phase, and available actions.
    """
    from app.models.database.trips import Trips
    from sqlmodel import select

    trip = db.exec(select(Trips).where(Trips.id == trip_id)).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Determine available buttons based on current status and phase
    available_actions = []

    if trip.status == "assigned":
        available_actions.append("start_day")
    elif trip.status == "started":
        if trip.trip_type == "trek_day" and trip.current_phase == "to_trek_start":
            available_actions.extend(["link_device", "visiting"])
        elif trip.trip_type == "tour_day":
            available_actions.append("visiting")
    elif trip.status == "visiting":
        if trip.trip_type == "trek_day":
            if not trip.linked_device_id:
                available_actions.append("link_device")
            elif trip.current_phase == "to_trek_start":
                available_actions.append("start_trek")
            elif trip.current_phase == "trek_active":
                available_actions.append("end_trek")
        else:  # tour_day
            available_actions.append("return_to_hotel")
    elif trip.status == "returning":
        # No buttons needed, just tracking until hotel
        pass

    return {
        "trip_id": trip_id,
        "status": trip.status,
        "phase": trip.current_phase,
        "trip_type": trip.trip_type,
        "is_tracking_active": trip.is_tracking_active,
        "linked_device": trip.linked_device_id,
        "available_actions": available_actions,
        "tracking_duration_minutes": (
            int(
                (datetime.datetime.utcnow() - trip.tracking_started_at).total_seconds()
                / 60
            )
            if trip.tracking_started_at
            else 0
        ),
    }


# ================== OFFLINE TREK DATA ENDPOINT ==================


@router.get("/{trip_id}/trek-data")
async def get_offline_trek_data(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    📲 OFFLINE TREK DATA
    Download trek path data for offline use during trek.
    Called before starting trek when phone goes offline.
    """
    from app.models.database.trips import Trips
    from sqlmodel import select

    trip = db.exec(select(Trips).where(Trips.id == trip_id)).first()
    if not trip or not trip.trek_id:
        raise HTTPException(status_code=404, detail="Trek not found")

    service = TripTrackingService(db)
    trek_path = await service.get_trek_path(trip.trek_id)

    if not trek_path:
        raise HTTPException(status_code=404, detail="Trek path data not found")

    return {
        "trek_id": trip.trek_id,
        "path_data": {
            "id": trek_path.id,
            "name": trek_path.name,
            "description": trek_path.description,
            "total_distance_meters": trek_path.total_distance_meters,
            "estimated_duration_hours": trek_path.estimated_duration_hours,
            "elevation_gain_meters": trek_path.elevation_gain_meters,
            "difficulty_rating": trek_path.difficulty_rating,
            "waypoints": trek_path.waypoints,
            "safety_notes": trek_path.safety_notes,
        },
        "offline_ready": True,
        "download_timestamp": int(datetime.datetime.utcnow().timestamp()),
        "instructions": "Trek data downloaded for offline use. Safe trekking!",
    }
