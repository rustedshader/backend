"""
GraphHopper routing service for calculating routes between points.
"""

import aiohttp
from typing import List, Dict, Any, Optional, Tuple


class GraphHopperService:
    """Service to interact with self-hosted GraphHopper instance."""

    def __init__(self):
        self.base_url = "https://maps.rustedshader.com"
        self.default_profile = "car"  # car, foot, bike

    async def get_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
        profile: str = "car",
    ) -> Optional[Dict[str, Any]]:
        """
        Get route between two points using GraphHopper API.

        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Destination latitude
            end_lon: Destination longitude
            profile: Transportation profile (car, foot, bike)

        Returns:
            Route data from GraphHopper API or None if error
        """
        url = f"{self.base_url}/route"

        params = {
            "point": [f"{start_lat},{start_lon}", f"{end_lat},{end_lon}"],
            "profile": profile,
            "points_encoded": "false",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"GraphHopper API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error calling GraphHopper API: {e}")
            return None

    async def get_multiple_routes(
        self, waypoints: List[Tuple[float, float]], profile: str = "car"
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Get routes between multiple waypoints.

        Args:
            waypoints: List of (lat, lon) tuples
            profile: Transportation profile

        Returns:
            List of route data for each segment
        """
        routes = []

        for i in range(len(waypoints) - 1):
            start_lat, start_lon = waypoints[i]
            end_lat, end_lon = waypoints[i + 1]

            route = await self.get_route(
                start_lat, start_lon, end_lat, end_lon, profile
            )
            routes.append(route)

        return routes

    def extract_route_summary(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key information from GraphHopper route response.

        Args:
            route_data: Raw response from GraphHopper API

        Returns:
            Simplified route summary with proper GeoJSON
        """
        if not route_data or "paths" not in route_data or not route_data["paths"]:
            return {}

        path = route_data["paths"][0]  # Take first path

        # Get coordinates and convert to proper GeoJSON LineString
        coordinates = path.get("points", {}).get("coordinates", [])
        geojson_geometry = (
            {"type": "LineString", "coordinates": coordinates} if coordinates else None
        )

        return {
            "distance_meters": path.get("distance", 0),
            "distance_km": round(path.get("distance", 0) / 1000, 2),
            "time_seconds": path.get("time", 0),
            "time_minutes": round(path.get("time", 0) / 60, 1),
            "time_hours": round(path.get("time", 0) / 3600, 2),
            "geometry": geojson_geometry,
            "coordinates": coordinates,  # Keep raw coordinates for backward compatibility
            "instructions": path.get("instructions", []),
            "bbox": path.get("bbox", []),
        }


# Global instance
graphhopper_service = GraphHopperService()
