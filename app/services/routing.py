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
        db: Optional[object] = None,
        include_block_areas: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Get route between two points using GraphHopper API with Custom Model for area avoidance.

        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Destination latitude
            end_lon: Destination longitude
            profile: Transportation profile (car, foot, bike)
            db: Database session for fetching restricted areas
            include_block_areas: Whether to include restricted areas using Custom Model

        Returns:
            Route data from GraphHopper API or None if error
        """
        url = f"{self.base_url}/route"

        # Prepare request payload for POST request
        payload = {
            "profile": profile,
            "points_encoded": False,
            "points": [
                [start_lon, start_lat],  # GraphHopper expects [lon, lat]
                [end_lon, end_lat],
            ],
        }

        # Add custom model with restricted areas if database session is provided
        if db and include_block_areas:
            restricted_areas_geojson = await self._get_restricted_areas_as_geojson(db)
            if restricted_areas_geojson:
                payload["ch.disable"] = True  # Required for custom models
                payload["custom_model"] = {
                    "priority": [],
                    "areas": restricted_areas_geojson,
                }

                # Add priority rules to avoid each restricted area
                features = restricted_areas_geojson.get("features", [])
                for feature in features:
                    area_id = feature.get("id", "")
                    if area_id:
                        payload["custom_model"]["priority"].append(
                            {
                                "if": f"in_{area_id}",
                                "multiply_by": "0",  # Complete avoidance
                            }
                        )

                print(
                    f"DEBUG: Adding Custom Model with {len(features)} restricted areas"
                )
                print(
                    f"DEBUG: Custom Model priority rules: {payload['custom_model']['priority']}"
                )
            else:
                print("DEBUG: No active restricted areas found for Custom Model")

        print(f"DEBUG: GraphHopper request URL: {url}")
        print(
            f"DEBUG: GraphHopper request has custom_model: {'custom_model' in payload}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers={"Content-Type": "application/json"}
                ) as response:
                    response_text = await response.text()
                    print(f"DEBUG: GraphHopper response status: {response.status}")

                    if response.status == 200:
                        result = await response.json()
                        print(
                            f"DEBUG: GraphHopper returned route with {len(result.get('paths', []))} paths"
                        )
                        return result
                    else:
                        print(f"GraphHopper API error: {response.status}")
                        print(f"Error details: {response_text}")
                        return None
        except Exception as e:
            print(f"Error calling GraphHopper API: {e}")
            return None

    async def get_multiple_routes(
        self,
        waypoints: List[Tuple[float, float]],
        profile: str = "car",
        db: Optional[object] = None,
        include_block_areas: bool = True,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Get routes between multiple waypoints.

        Args:
            waypoints: List of (lat, lon) tuples
            profile: Transportation profile
            db: Database session for fetching restricted areas
            include_block_areas: Whether to include restricted areas as blocked areas

        Returns:
            List of route data for each segment
        """
        routes = []

        for i in range(len(waypoints) - 1):
            start_lat, start_lon = waypoints[i]
            end_lat, end_lon = waypoints[i + 1]

            route = await self.get_route(
                start_lat,
                start_lon,
                end_lat,
                end_lon,
                profile,
                db=db,
                include_block_areas=include_block_areas,
            )
            routes.append(route)

        return routes

    async def _get_active_restricted_areas(self, db: object) -> List[str]:
        """
        Get all active restricted areas as WKT POLYGON strings for block_areas.
        DEPRECATED: Use _get_restricted_areas_as_geojson for Custom Models.

        Args:
            db: Database session

        Returns:
            List of WKT POLYGON strings representing restricted areas
        """
        try:
            # Import the dedicated geofencing function
            from app.services.geofencing import get_active_restricted_areas_for_routing

            return await get_active_restricted_areas_for_routing(db)

        except Exception as e:
            print(f"Error fetching restricted areas for routing: {e}")
            return []

    async def _get_restricted_areas_as_geojson(
        self, db: object
    ) -> Optional[Dict[str, Any]]:
        """
        Get all active restricted areas as GeoJSON FeatureCollection for Custom Models.

        Args:
            db: Database session

        Returns:
            GeoJSON FeatureCollection with restricted area polygons or None if no areas
        """
        try:
            from app.services.geofencing import get_active_restricted_areas_for_routing
            import re

            # Get WKT polygons
            wkt_polygons = await get_active_restricted_areas_for_routing(db)

            if not wkt_polygons:
                return None

            features = []

            for i, wkt_polygon in enumerate(wkt_polygons):
                try:
                    # Parse WKT POLYGON to extract coordinates
                    # Example: "POLYGON((lon1 lat1,lon2 lat2,lon3 lat3,lon1 lat1))"

                    # Use regex to extract coordinate pairs
                    match = re.search(r"POLYGON\(\((.*?)\)\)", wkt_polygon)
                    if not match:
                        print(
                            f"Warning: Invalid WKT format for polygon {i}: {wkt_polygon[:50]}..."
                        )
                        continue

                    coords_str = match.group(1)
                    coord_pairs = coords_str.split(",")

                    # Convert to [longitude, latitude] pairs
                    coordinates = []
                    for pair in coord_pairs:
                        lon_lat = pair.strip().split(" ")
                        if len(lon_lat) == 2:
                            try:
                                lon, lat = float(lon_lat[0]), float(lon_lat[1])
                                coordinates.append([lon, lat])
                            except ValueError:
                                print(f"Warning: Invalid coordinate pair: {pair}")
                                continue

                    if len(coordinates) < 4:  # Need at least 4 points for a polygon
                        print(f"Warning: Insufficient coordinates for polygon {i}")
                        continue

                    # Ensure polygon is closed (first and last coordinates are the same)
                    if coordinates[0] != coordinates[-1]:
                        coordinates.append(coordinates[0])

                    # Create GeoJSON Feature
                    feature = {
                        "type": "Feature",
                        "id": f"restricted_area_{i}",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [coordinates],  # Array of linear ring arrays
                        },
                        "properties": {
                            "name": f"Restricted Area {i + 1}",
                            "restriction_type": "avoid",
                        },
                    }

                    features.append(feature)

                except Exception as e:
                    print(f"Error processing WKT polygon {i}: {e}")
                    continue

            if not features:
                print("No valid restricted area features could be created")
                return None

            geojson_collection = {"type": "FeatureCollection", "features": features}

            print(
                f"Created GeoJSON FeatureCollection with {len(features)} restricted areas"
            )
            return geojson_collection

        except Exception as e:
            print(f"Error creating GeoJSON from restricted areas: {e}")
            return None

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
