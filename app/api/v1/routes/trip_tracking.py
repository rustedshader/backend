"""
API endpoints for trip tracking and GPS data management.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from typing import List, Optional
from app.api.deps import get_current_user, get_session
from app.models.database.user import User
from app.models.schemas.trip_tracking import (
    LocationBatch,
    LiveLocationUpdate,
    TripTrackingStats,
    TripTypeEnum,
    TrekPhaseEnum,
)
from app.services.trip_tracking import TripTrackingService

router = APIRouter(prefix="/tracking", tags=["Trip Tracking"])


@router.post("/start/{trip_id}")
async def start_trip_tracking(
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
    """Start GPS tracking for a trip."""
    service = TripTrackingService(db)

    success = await service.start_trip_tracking(
        trip_id=trip_id,
        trip_type=trip_type,
        hotel_lat=hotel_lat,
        hotel_lon=hotel_lon,
        hotel_name=hotel_name,
        destination_lat=destination_lat,
        destination_lon=destination_lon,
        destination_name=destination_name,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Trip not found")

    return {"message": "Trip tracking started", "trip_id": trip_id}


@router.post("/location/batch")
async def upload_location_batch(
    location_batch: LocationBatch,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Upload a batch of location points."""
    service = TripTrackingService(db)

    # Verify user owns the trip
    # Add validation logic here

    success = await service.record_location_batch(location_batch)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to record location batch")

    return {
        "message": "Location batch recorded successfully",
        "locations_count": len(location_batch.locations),
    }


@router.post("/location/live")
async def update_live_location(
    live_update: LiveLocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update live location for real-time tracking."""
    service = TripTrackingService(db)

    # Verify user owns the trip
    # Add validation logic here

    success = await service.record_live_location(live_update)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to record live location")

    return {"message": "Live location updated", "timestamp": live_update.timestamp}


@router.patch("/phase/{trip_id}")
async def update_trip_phase(
    trip_id: int,
    new_phase: TrekPhaseEnum,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update the current phase of a trek trip."""
    service = TripTrackingService(db)

    success = await service.update_trip_phase(trip_id, new_phase)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to update trip phase or trip is not a trek day",
        )

    return {"message": "Trip phase updated", "new_phase": new_phase}


@router.post("/segment/start/{trip_id}")
async def start_route_segment(
    trip_id: int,
    segment_type: str,
    start_lat: float,
    start_lon: float,
    trek_path_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Start a new route segment."""
    service = TripTrackingService(db)

    segment_id = await service.create_route_segment(
        trip_id=trip_id,
        segment_type=segment_type,
        start_lat=start_lat,
        start_lon=start_lon,
        trek_path_id=trek_path_id,
    )

    if not segment_id:
        raise HTTPException(status_code=400, detail="Failed to create route segment")

    return {
        "message": "Route segment started",
        "segment_id": segment_id,
        "segment_type": segment_type,
    }


@router.patch("/segment/complete/{segment_id}")
async def complete_route_segment(
    segment_id: int,
    end_lat: float,
    end_lon: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Complete a route segment with end coordinates."""
    service = TripTrackingService(db)

    success = await service.complete_route_segment(segment_id, end_lat, end_lon)

    if not success:
        raise HTTPException(status_code=404, detail="Route segment not found")

    return {"message": "Route segment completed", "segment_id": segment_id}


@router.post("/stop/{trip_id}")
async def stop_trip_tracking(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Stop GPS tracking for a trip."""
    service = TripTrackingService(db)

    success = await service.stop_trip_tracking(trip_id)

    if not success:
        raise HTTPException(status_code=404, detail="Trip not found")

    return {"message": "Trip tracking stopped", "trip_id": trip_id}


@router.get("/stats/{trip_id}")
async def get_trip_stats(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> TripTrackingStats:
    """Get comprehensive tracking statistics for a trip."""
    service = TripTrackingService(db)

    stats = await service.get_trip_tracking_stats(trip_id)

    if not stats:
        raise HTTPException(status_code=404, detail="Trip not found")

    return stats


@router.get("/trek-path/{trek_id}")
async def get_trek_path(
    trek_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get the pre-made trek path for a trek."""
    service = TripTrackingService(db)

    trek_path = await service.get_trek_path(trek_id)

    if not trek_path:
        raise HTTPException(status_code=404, detail="Trek path not found")

    return {
        "id": trek_path.id,
        "trek_id": trek_path.trek_id,
        "name": trek_path.name,
        "description": trek_path.description,
        "total_distance_meters": trek_path.total_distance_meters,
        "estimated_duration_hours": trek_path.estimated_duration_hours,
        "elevation_gain_meters": trek_path.elevation_gain_meters,
        "difficulty_rating": trek_path.difficulty_rating,
        "waypoints": trek_path.waypoints,
        "safety_notes": trek_path.safety_notes,
    }


@router.post("/trek-path/{trek_id}")
async def create_trek_path(
    trek_id: int,
    name: str,
    path_coordinates: List[List[float]],
    distance_meters: float,
    duration_hours: float,
    description: Optional[str] = None,
    elevation_gain: Optional[float] = None,
    waypoints: Optional[List[dict]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create a new trek path."""
    service = TripTrackingService(db)

    path_id = await service.create_trek_path(
        trek_id=trek_id,
        name=name,
        path_coordinates=path_coordinates,
        distance_meters=distance_meters,
        duration_hours=duration_hours,
        description=description,
        elevation_gain=elevation_gain,
        waypoints=waypoints,
    )

    if not path_id:
        raise HTTPException(status_code=400, detail="Failed to create trek path")

    return {
        "message": "Trek path created successfully",
        "path_id": path_id,
        "trek_id": trek_id,
    }
