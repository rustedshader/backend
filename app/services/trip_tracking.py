"""
Trip tracking service for handling GPS data and route management.
"""

from sqlmodel import Session, select
from typing import List, Optional, Dict
from app.models.database.trips import (
    Trips,
    LocationHistory,
    TrekPath,
    RouteSegment,
    TripTypeEnum,
    TrekPhaseEnum,
    TourPhaseEnum,
    TripStatusEnum,
)
from app.models.database.treks import Trek
from app.models.schemas.trip_tracking import (
    LocationBatch,
    LiveLocationUpdate,
    TripTrackingStats,
    StartDayRequest,
    StartTrekRequest,
    EndTrekRequest,
    DeviceLinkRequest,
)
import datetime
from geoalchemy2.functions import ST_MakePoint
import json


class TripTrackingService:
    """Service for managing trip tracking and GPS data."""

    def __init__(self, db: Session):
        self.db = db

    async def start_trip_tracking(
        self,
        trip_id: int,
        trip_type: TripTypeEnum,
        hotel_lat: float,
        hotel_lon: float,
        hotel_name: str,
        destination_lat: Optional[float] = None,
        destination_lon: Optional[float] = None,
        destination_name: Optional[str] = None,
    ) -> bool:
        """Start tracking for a trip."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip:
            return False

        # Update trip with tracking information
        trip.trip_type = trip_type
        trip.hotel_latitude = hotel_lat
        trip.hotel_longitude = hotel_lon
        trip.hotel_name = hotel_name
        trip.destination_latitude = destination_lat
        trip.destination_longitude = destination_lon
        trip.destination_name = destination_name
        trip.is_tracking_active = True
        trip.tracking_started_at = datetime.datetime.utcnow()

        # Set initial phase
        if trip_type == TripTypeEnum.TREK_DAY:
            trip.current_phase = TrekPhaseEnum.TO_TREK_START
            # Get trek start coordinates
            if trip.trek_id:
                trek = self.db.exec(select(Trek).where(Trek.id == trip.trek_id)).first()
                if trek:
                    trip.trek_start_latitude = trek.start_latitude
                    trip.trek_start_longitude = trek.start_longitude

        self.db.add(trip)
        self.db.commit()
        return True

    async def record_location_batch(self, location_batch: LocationBatch) -> bool:
        """Record a batch of location points."""
        try:
            for location in location_batch.locations:
                location_record = LocationHistory(
                    trip_id=location_batch.trip_id,
                    user_id=location_batch.user_id,
                    timestamp=location.timestamp,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    altitude=location.altitude,
                    accuracy=location.accuracy,
                    speed=location.speed,
                    bearing=location.bearing,
                    source=location.source,
                    trip_phase=location_batch.trip_phase,
                    device_id=location.device_id,
                    battery_level=location.battery_level,
                    signal_strength=location.signal_strength,
                    notes=location_batch.notes,
                    location=ST_MakePoint(location.longitude, location.latitude),
                )
                self.db.add(location_record)

            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error recording location batch: {e}")
            return False

    async def record_live_location(self, live_update: LiveLocationUpdate) -> bool:
        """Record a single live location update."""
        try:
            location_record = LocationHistory(
                trip_id=live_update.trip_id,
                user_id=live_update.user_id,
                timestamp=live_update.timestamp,
                latitude=live_update.latitude,
                longitude=live_update.longitude,
                altitude=live_update.altitude,
                accuracy=live_update.accuracy,
                speed=live_update.speed,
                bearing=live_update.bearing,
                source=live_update.source,
                trip_phase=live_update.trip_phase,
                location=ST_MakePoint(live_update.longitude, live_update.latitude),
                is_waypoint=live_update.emergency,  # Mark emergency locations as waypoints
            )
            self.db.add(location_record)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"Error recording live location: {e}")
            return False

    async def update_trip_phase(self, trip_id: int, new_phase: TrekPhaseEnum) -> bool:
        """Update the current phase of a trek trip."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip or trip.trip_type != TripTypeEnum.TREK_DAY:
            return False

        trip.current_phase = new_phase
        self.db.add(trip)
        self.db.commit()
        return True

    async def create_route_segment(
        self,
        trip_id: int,
        segment_type: str,
        start_lat: float,
        start_lon: float,
        trek_path_id: Optional[int] = None,
    ) -> Optional[int]:
        """Create a new route segment."""
        segment = RouteSegment(
            trip_id=trip_id,
            segment_type=segment_type,
            start_timestamp=int(datetime.datetime.utcnow().timestamp()),
            start_latitude=start_lat,
            start_longitude=start_lon,
            trek_path_id=trek_path_id,
        )

        self.db.add(segment)
        self.db.commit()
        self.db.refresh(segment)
        return segment.id

    async def complete_route_segment(
        self, segment_id: int, end_lat: float, end_lon: float
    ) -> bool:
        """Complete a route segment with end coordinates and statistics."""
        segment = self.db.exec(
            select(RouteSegment).where(RouteSegment.id == segment_id)
        ).first()
        if not segment:
            return False

        # Update segment
        segment.end_timestamp = int(datetime.datetime.utcnow().timestamp())
        segment.end_latitude = end_lat
        segment.end_longitude = end_lon
        segment.is_completed = True

        # Calculate statistics from location history
        locations = self.db.exec(
            select(LocationHistory)
            .where(LocationHistory.trip_id == segment.trip_id)
            .where(LocationHistory.timestamp >= segment.start_timestamp)
            .where(LocationHistory.timestamp <= segment.end_timestamp)
            .order_by(LocationHistory.timestamp)
        ).all()

        if locations:
            total_distance = 0
            speeds = []

            for i in range(1, len(locations)):
                prev_loc = locations[i - 1]
                curr_loc = locations[i]

                # Calculate distance (simplified)
                lat_diff = curr_loc.latitude - prev_loc.latitude
                lon_diff = curr_loc.longitude - prev_loc.longitude
                distance = (
                    (lat_diff**2 + lon_diff**2) ** 0.5
                ) * 111000  # rough conversion to meters
                total_distance += distance

                # Calculate speed if we have time difference
                time_diff = curr_loc.timestamp - prev_loc.timestamp
                if time_diff > 0:
                    speeds.append(distance / time_diff)

            segment.total_distance_meters = total_distance
            segment.total_duration_seconds = (
                segment.end_timestamp - segment.start_timestamp
            )
            if speeds:
                segment.avg_speed_ms = sum(speeds) / len(speeds)
                segment.max_speed_ms = max(speeds)

        self.db.add(segment)
        self.db.commit()
        return True

    async def stop_trip_tracking(self, trip_id: int) -> bool:
        """Stop tracking for a trip."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip:
            return False

        trip.is_tracking_active = False
        trip.tracking_ended_at = datetime.datetime.utcnow()
        trip.status = "completed"

        self.db.add(trip)
        self.db.commit()
        return True

    async def get_trip_tracking_stats(
        self, trip_id: int
    ) -> Optional[TripTrackingStats]:
        """Get comprehensive tracking statistics for a trip."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip:
            return None

        # Get all location records
        locations = self.db.exec(
            select(LocationHistory)
            .where(LocationHistory.trip_id == trip_id)
            .order_by(LocationHistory.timestamp)
        ).all()

        # Get route segments
        segments = self.db.exec(
            select(RouteSegment).where(RouteSegment.trip_id == trip_id)
        ).all()

        if not locations:
            return TripTrackingStats(
                trip_id=trip_id,
                total_distance_meters=0,
                total_duration_seconds=0,
                avg_speed_ms=0,
                max_speed_ms=0,
                locations_recorded=0,
                segments_completed=0,
                current_phase=trip.current_phase,
                tracking_started_at=trip.tracking_started_at,
                tracking_ended_at=trip.tracking_ended_at,
            )

        # Calculate total statistics
        total_distance = sum(s.total_distance_meters or 0 for s in segments)
        total_duration = 0
        speeds = []

        if len(locations) > 1:
            total_duration = locations[-1].timestamp - locations[0].timestamp

            for i in range(1, len(locations)):
                if locations[i].speed:
                    speeds.append(locations[i].speed)

        return TripTrackingStats(
            trip_id=trip_id,
            total_distance_meters=total_distance,
            total_duration_seconds=total_duration,
            avg_speed_ms=sum(speeds) / len(speeds) if speeds else 0,
            max_speed_ms=max(speeds) if speeds else 0,
            locations_recorded=len(locations),
            segments_completed=len([s for s in segments if s.is_completed]),
            current_phase=trip.current_phase,
            tracking_started_at=trip.tracking_started_at,
            tracking_ended_at=trip.tracking_ended_at,
        )

    async def get_trek_path(self, trek_id: int) -> Optional[TrekPath]:
        """Get the pre-made trek path for a trek."""
        trek_path = self.db.exec(
            select(TrekPath)
            .where(TrekPath.trek_id == trek_id)
            .where(TrekPath.is_active)
        ).first()

        return trek_path

    async def create_trek_path(
        self,
        trek_id: int,
        name: str,
        path_coordinates: List[List[float]],
        distance_meters: float,
        duration_hours: float,
        description: Optional[str] = None,
        elevation_gain: Optional[float] = None,
        waypoints: Optional[List[Dict]] = None,
    ) -> Optional[int]:
        """Create a new trek path."""
        trek_path = TrekPath(
            trek_id=trek_id,
            name=name,
            description=description,
            total_distance_meters=distance_meters,
            estimated_duration_hours=duration_hours,
            elevation_gain_meters=elevation_gain,
            waypoints=json.dumps(waypoints) if waypoints else None,
        )

        self.db.add(trek_path)
        self.db.commit()
        self.db.refresh(trek_path)
        return trek_path.id

    # ================== BUTTON-DRIVEN WORKFLOW METHODS ==================

    async def start_day(
        self,
        trip_id: int,
        trip_type: TripTypeEnum,
        hotel_lat: float,
        hotel_lon: float,
        hotel_name: str,
        destination_lat: Optional[float] = None,
        destination_lon: Optional[float] = None,
        destination_name: Optional[str] = None,
    ) -> Dict[str, any]:
        """Start the day - Tourist presses 'Start Day' button."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip:
            return {"success": False, "error": "Trip not found"}

        # Update trip with day start information
        trip.trip_type = trip_type
        trip.hotel_latitude = hotel_lat
        trip.hotel_longitude = hotel_lon
        trip.hotel_name = hotel_name
        trip.destination_latitude = destination_lat
        trip.destination_longitude = destination_lon
        trip.destination_name = destination_name
        trip.is_tracking_active = True
        trip.tracking_started_at = datetime.datetime.utcnow()
        trip.status = "started"

        # Set initial phase based on trip type
        if trip_type == TripTypeEnum.TREK_DAY:
            trip.current_phase = TrekPhaseEnum.TO_TREK_START.value
            # Get trek start coordinates
            if trip.trek_id:
                trek = self.db.exec(select(Trek).where(Trek.id == trip.trek_id)).first()
                if trek:
                    trip.trek_start_latitude = trek.start_latitude
                    trip.trek_start_longitude = trek.start_longitude
        else:  # TOUR_DAY
            trip.current_phase = TourPhaseEnum.TO_DESTINATION.value

        self.db.add(trip)
        self.db.commit()

        # Return route information for mobile app
        if trip_type == TripTypeEnum.TREK_DAY and trip.trek_start_latitude:
            return {
                "success": True,
                "message": "Trek day started",
                "phase": trip.current_phase,
                "route_to": {
                    "latitude": trip.trek_start_latitude,
                    "longitude": trip.trek_start_longitude,
                    "name": "Trek Starting Point",
                },
                "instructions": "Follow GPS route to trek starting point. Keep sending location data.",
            }
        elif trip_type == TripTypeEnum.TOUR_DAY and destination_lat:
            return {
                "success": True,
                "message": "Tour day started",
                "phase": trip.current_phase,
                "route_to": {
                    "latitude": destination_lat,
                    "longitude": destination_lon,
                    "name": destination_name or "Tourist Destination",
                },
                "instructions": "Follow GPS route to destination. Keep sending location data.",
            }
        else:
            return {"success": False, "error": "Missing destination coordinates"}

    async def set_visiting_status(self, trip_id: int) -> Dict[str, any]:
        """Tourist reaches destination and presses 'Visiting' button."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip:
            return {"success": False, "error": "Trip not found"}

        trip.status = "visiting"

        if trip.trip_type == TripTypeEnum.TOUR_DAY:
            trip.current_phase = TourPhaseEnum.AT_DESTINATION.value
        # For trek days, this is handled by start_trek method

        self.db.add(trip)
        self.db.commit()

        return {
            "success": True,
            "message": "Status updated to visiting",
            "phase": trip.current_phase,
            "instructions": "Enjoy your visit! Press 'Return to Hotel' when ready to go back.",
        }

    async def link_tracking_device(
        self, trip_id: int, device_id: str
    ) -> Dict[str, any]:
        """Link tracking device for trek - Tourist presses 'Link Device' button."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip or trip.trip_type != TripTypeEnum.TREK_DAY:
            return {"success": False, "error": "Trip not found or not a trek day"}

        trip.linked_device_id = device_id
        trip.device_linked_at = datetime.datetime.utcnow()

        self.db.add(trip)
        self.db.commit()

        return {
            "success": True,
            "message": f"Device {device_id} linked successfully",
            "instructions": "Device linked. Now you can start the trek.",
        }

    async def start_trek(self, trip_id: int, device_id: str) -> Dict[str, any]:
        """Start trek with tracking device - Tourist presses 'Start Trek' button."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip or trip.trip_type != TripTypeEnum.TREK_DAY:
            return {"success": False, "error": "Trip not found or not a trek day"}

        if trip.linked_device_id != device_id:
            return {"success": False, "error": "Device not linked or wrong device ID"}

        # Update trip status
        trip.status = "visiting"
        trip.current_phase = TrekPhaseEnum.TREK_ACTIVE.value

        self.db.add(trip)
        self.db.commit()

        # Get pre-stored trek data
        trek_path = await self.get_trek_path(trip.trek_id)

        return {
            "success": True,
            "message": "Trek started with tracking device",
            "phase": trip.current_phase,
            "trek_data": {
                "path_id": trek_path.id if trek_path else None,
                "estimated_duration_hours": trek_path.estimated_duration_hours
                if trek_path
                else None,
                "total_distance_meters": trek_path.total_distance_meters
                if trek_path
                else None,
                "waypoints": trek_path.waypoints if trek_path else None,
                "safety_notes": trek_path.safety_notes if trek_path else None,
            },
            "instructions": "Trek data downloaded. Phone going offline. Tracking device will send location data.",
        }

    async def end_trek(
        self, trip_id: int, trek_end_lat: float, trek_end_lon: float
    ) -> Dict[str, any]:
        """End trek and request return route - Tourist presses 'End Trek' button."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip or trip.trip_type != TripTypeEnum.TREK_DAY:
            return {"success": False, "error": "Trip not found or not a trek day"}

        # Update trek end coordinates
        trip.trek_end_latitude = trek_end_lat
        trip.trek_end_longitude = trek_end_lon
        trip.current_phase = TrekPhaseEnum.FROM_TREK_END.value
        trip.status = "returning"

        self.db.add(trip)
        self.db.commit()

        return {
            "success": True,
            "message": "Trek ended successfully",
            "phase": trip.current_phase,
            "return_route": {
                "from": {
                    "latitude": trek_end_lat,
                    "longitude": trek_end_lon,
                    "name": "Trek End Point",
                },
                "to": {
                    "latitude": trip.hotel_latitude,
                    "longitude": trip.hotel_longitude,
                    "name": trip.hotel_name,
                },
            },
            "instructions": "Follow GPS route back to hotel. Mobile GPS tracking resumed.",
        }

    async def request_return_route(
        self, trip_id: int, current_lat: float, current_lon: float
    ) -> Dict[str, any]:
        """Request route back to hotel - Tourist presses 'Return to Hotel' button."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip:
            return {"success": False, "error": "Trip not found"}

        # Update status and phase
        trip.status = "returning"

        if trip.trip_type == TripTypeEnum.TOUR_DAY:
            trip.current_phase = TourPhaseEnum.TO_HOTEL.value
        # For trek days, this is handled by end_trek method

        self.db.add(trip)
        self.db.commit()

        return {
            "success": True,
            "message": "Return route requested",
            "phase": trip.current_phase,
            "return_route": {
                "from": {
                    "latitude": current_lat,
                    "longitude": current_lon,
                    "name": "Current Location",
                },
                "to": {
                    "latitude": trip.hotel_latitude,
                    "longitude": trip.hotel_longitude,
                    "name": trip.hotel_name,
                },
            },
            "instructions": "Follow GPS route back to hotel. Keep sending location data until you reach the hotel.",
        }

    async def complete_day(self, trip_id: int) -> Dict[str, any]:
        """Complete the day when tourist reaches hotel."""
        trip = self.db.exec(select(Trips).where(Trips.id == trip_id)).first()
        if not trip:
            return {"success": False, "error": "Trip not found"}

        trip.status = "completed"
        trip.is_tracking_active = False
        trip.tracking_ended_at = datetime.datetime.utcnow()

        self.db.add(trip)
        self.db.commit()

        # Calculate final statistics
        stats = await self.get_trip_tracking_stats(trip_id)

        return {
            "success": True,
            "message": "Day completed successfully",
            "final_stats": {
                "total_distance_km": stats.total_distance_meters / 1000 if stats else 0,
                "total_duration_hours": stats.total_duration_seconds / 3600
                if stats
                else 0,
                "locations_recorded": stats.locations_recorded if stats else 0,
            },
            "instructions": "Day completed! Thank you for using our tracking service.",
        }
