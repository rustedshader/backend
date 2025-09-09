"""
Service for generating routes for itineraries.
"""

from sqlmodel import Session, select
from typing import Optional
from app.models.database.itinerary import Itinerary, ItineraryDay
from app.models.database.places import Place
from app.models.database.treks import Trek
from app.models.schemas.routing import (
    RoutePoint,
    RouteSegment,
    DayRoute,
    ItineraryRouteResponse,
)
from app.services.routing import graphhopper_service


class ItineraryRoutingService:
    """Service to generate routes for entire itineraries."""

    async def generate_itinerary_routes(
        self,
        itinerary_id: int,
        db: Session,
        profile: str = "car",
        include_coordinates: bool = True,
        include_instructions: bool = True,
    ) -> Optional[ItineraryRouteResponse]:
        """
        Generate routes for an entire itinerary.

        Args:
            itinerary_id: ID of the itinerary
            db: Database session
            profile: Transportation profile (car, foot, bike)
            include_coordinates: Whether to include route coordinates
            include_instructions: Whether to include turn-by-turn instructions

        Returns:
            Complete routing information for the itinerary
        """
        # Get itinerary
        itinerary = db.exec(
            select(Itinerary).where(Itinerary.id == itinerary_id)
        ).first()

        if not itinerary:
            return None

        # Get all itinerary days ordered by day number
        itinerary_days = db.exec(
            select(ItineraryDay)
            .where(ItineraryDay.itinerary_id == itinerary_id)
            .order_by(ItineraryDay.day_number)
        ).all()

        if not itinerary_days:
            return None

        day_routes = []
        total_distance_km = 0.0
        total_time_hours = 0.0

        for day in itinerary_days:
            day_route = await self._generate_day_routes(
                day, db, profile, include_coordinates, include_instructions
            )

            if day_route:
                day_routes.append(day_route)
                total_distance_km += day_route.total_distance_km
                total_time_hours += day_route.total_time_hours

        return ItineraryRouteResponse(
            itinerary_id=itinerary_id,
            total_days=len(day_routes),
            total_distance_km=round(total_distance_km, 2),
            total_time_hours=round(total_time_hours, 2),
            profile=profile,
            day_routes=day_routes,
        )

    async def _generate_day_routes(
        self,
        day: ItineraryDay,
        db: Session,
        profile: str,
        include_coordinates: bool,
        include_instructions: bool,
    ) -> Optional[DayRoute]:
        """Generate routes for a single day."""
        waypoints = []
        routes = []

        # Get previous day's accommodation as starting point (if exists)
        prev_day = db.exec(
            select(ItineraryDay).where(
                ItineraryDay.itinerary_id == day.itinerary_id,
                ItineraryDay.day_number == day.day_number - 1,
            )
        ).first()

        start_point = None
        if (
            prev_day
            and prev_day.accommodation_latitude
            and prev_day.accommodation_longitude
        ):
            start_point = RoutePoint(
                latitude=prev_day.accommodation_latitude,
                longitude=prev_day.accommodation_longitude,
                name=prev_day.accommodation_name or "Previous Day Accommodation",
                type="hotel",
            )
            waypoints.append(start_point)

        # Get destination point based on day type
        destination_point = None
        if day.day_type == "trek_day" and day.trek_id:
            # Get trek starting coordinates
            trek = db.exec(select(Trek).where(Trek.id == day.trek_id)).first()
            if trek and trek.start_latitude and trek.start_longitude:
                destination_point = RoutePoint(
                    latitude=trek.start_latitude,
                    longitude=trek.start_longitude,
                    name=f"{trek.name} - Trek Start",
                    type="trek_start",
                )
        elif day.day_type == "place_visit_day" and day.primary_place_id:
            # Get place coordinates
            place = db.exec(
                select(Place).where(Place.id == day.primary_place_id)
            ).first()
            if place:
                destination_point = RoutePoint(
                    latitude=place.latitude,
                    longitude=place.longitude,
                    name=place.name,
                    type="place",
                )

        if destination_point:
            waypoints.append(destination_point)

        # Add current day's accommodation as final point for round trip
        if day.accommodation_latitude and day.accommodation_longitude:
            accommodation_point = RoutePoint(
                latitude=day.accommodation_latitude,
                longitude=day.accommodation_longitude,
                name=day.accommodation_name or f"Day {day.day_number} Accommodation",
                type="hotel",
            )
            # Add accommodation for return journey if we have a destination
            if destination_point and len(waypoints) > 0:
                waypoints.append(accommodation_point)
            # If no previous accommodation but we have destination, add accommodation as both start and end
            elif destination_point and len(waypoints) == 0:
                waypoints.extend(
                    [accommodation_point, destination_point, accommodation_point]
                )
            # If no destination but we have accommodation, just add it
            elif len(waypoints) == 0:
                waypoints.append(accommodation_point)

        # Generate routes between waypoints with segment types
        total_distance_km = 0.0
        total_time_hours = 0.0

        for i in range(len(waypoints) - 1):
            from_point = waypoints[i]
            to_point = waypoints[i + 1]

            # Determine segment type
            segment_type = "transfer"  # default
            if from_point.type == "hotel" and to_point.type in ["place", "trek_start"]:
                segment_type = "outbound"
            elif (
                from_point.type in ["place", "trek_start"] and to_point.type == "hotel"
            ):
                segment_type = "return"

            route_data = await graphhopper_service.get_route(
                from_point.latitude,
                from_point.longitude,
                to_point.latitude,
                to_point.longitude,
                profile,
            )

            if route_data:
                summary = graphhopper_service.extract_route_summary(route_data)

                route_segment = RouteSegment(
                    from_point=from_point,
                    to_point=to_point,
                    distance_meters=summary.get("distance_meters", 0),
                    distance_km=summary.get("distance_km", 0),
                    time_seconds=summary.get("time_seconds", 0),
                    time_minutes=summary.get("time_minutes", 0),
                    time_hours=summary.get("time_hours", 0),
                    geojson=summary.get("geometry") if include_coordinates else None,
                    coordinates=summary.get("coordinates", [])
                    if include_coordinates
                    else [],
                    instructions=summary.get("instructions", [])
                    if include_instructions
                    else [],
                    bbox=summary.get("bbox", []),
                    segment_type=segment_type,
                )

                routes.append(route_segment)
                total_distance_km += summary.get("distance_km", 0)
                total_time_hours += summary.get("time_hours", 0)

        if not routes and not waypoints:
            return None

        return DayRoute(
            day_number=day.day_number,
            date=day.date.isoformat(),
            day_type=day.day_type,
            routes=routes,
            total_distance_km=round(total_distance_km, 2),
            total_time_hours=round(total_time_hours, 2),
            waypoints=waypoints,
        )


# Global instance
itinerary_routing_service = ItineraryRoutingService()
