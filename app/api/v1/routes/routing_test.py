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


@router.post("/test-graphhopper-direct", include_in_schema=False)
async def test_graphhopper_direct(
    request: RoutingTestRequest,
    db: Session = Depends(get_db),
):
    """
    Test GraphHopper directly with and without block_areas to debug the issue.
    """
    try:
        import aiohttp
        from app.services.geofencing import get_active_restricted_areas_for_routing

        # Get blocked areas
        blocked_areas = await get_active_restricted_areas_for_routing(db)

        base_url = "https://maps.rustedshader.com"

        # Test 1: Route WITHOUT block_areas
        payload_without_blocks = {
            "profile": request.profile,
            "points_encoded": False,
            "points": [
                [request.start_lon, request.start_lat],
                [request.end_lon, request.end_lat],
            ],
        }

        # Test 2: Route WITH block_areas
        payload_with_blocks = {
            "profile": request.profile,
            "points_encoded": False,
            "points": [
                [request.start_lon, request.start_lat],
                [request.end_lon, request.end_lat],
            ],
            "block_areas": blocked_areas,
        }

        results = {}

        async with aiohttp.ClientSession() as session:
            # Test without blocks
            async with session.post(
                f"{base_url}/route",
                json=payload_without_blocks,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    route_without_blocks = await response.json()
                    results["route_without_blocks"] = {
                        "success": True,
                        "distance_km": round(
                            route_without_blocks["paths"][0]["distance"] / 1000, 2
                        ),
                        "time_minutes": round(
                            route_without_blocks["paths"][0]["time"] / 60000, 1
                        ),
                        "coordinates_count": len(
                            route_without_blocks["paths"][0]["points"]["coordinates"]
                        ),
                        "first_5_coords": route_without_blocks["paths"][0]["points"][
                            "coordinates"
                        ][:5],
                        "last_5_coords": route_without_blocks["paths"][0]["points"][
                            "coordinates"
                        ][-5:],
                    }
                else:
                    results["route_without_blocks"] = {
                        "success": False,
                        "error": f"Status {response.status}: {await response.text()}",
                    }

            # Test with blocks
            async with session.post(
                f"{base_url}/route",
                json=payload_with_blocks,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    route_with_blocks = await response.json()
                    results["route_with_blocks"] = {
                        "success": True,
                        "distance_km": round(
                            route_with_blocks["paths"][0]["distance"] / 1000, 2
                        ),
                        "time_minutes": round(
                            route_with_blocks["paths"][0]["time"] / 60000, 1
                        ),
                        "coordinates_count": len(
                            route_with_blocks["paths"][0]["points"]["coordinates"]
                        ),
                        "first_5_coords": route_with_blocks["paths"][0]["points"][
                            "coordinates"
                        ][:5],
                        "last_5_coords": route_with_blocks["paths"][0]["points"][
                            "coordinates"
                        ][-5:],
                    }
                else:
                    results["route_with_blocks"] = {
                        "success": False,
                        "error": f"Status {response.status}: {await response.text()}",
                    }

        # Analysis
        analysis = {
            "blocked_areas_count": len(blocked_areas),
            "blocked_areas_sample": blocked_areas[:2] if blocked_areas else [],
            "request_points": {
                "start": [request.start_lat, request.start_lon],
                "end": [request.end_lat, request.end_lon],
            },
            "routes_different": False,
            "distance_difference_km": 0,
            "time_difference_minutes": 0,
        }

        if results.get("route_without_blocks", {}).get("success") and results.get(
            "route_with_blocks", {}
        ).get("success"):
            dist_without = results["route_without_blocks"]["distance_km"]
            dist_with = results["route_with_blocks"]["distance_km"]
            time_without = results["route_without_blocks"]["time_minutes"]
            time_with = results["route_with_blocks"]["time_minutes"]

            analysis["routes_different"] = (
                abs(dist_without - dist_with) > 0.1
            )  # 100m difference
            analysis["distance_difference_km"] = round(dist_with - dist_without, 2)
            analysis["time_difference_minutes"] = round(time_with - time_without, 1)

        return {
            "analysis": analysis,
            "results": results,
            "graphhopper_payloads": {
                "without_blocks": payload_without_blocks,
                "with_blocks": payload_with_blocks,
            },
        }

    except Exception as e:
        return {
            "error": str(e),
            "request": {
                "start": [request.start_lat, request.start_lon],
                "end": [request.end_lat, request.end_lon],
                "profile": request.profile,
            },
        }


@router.get("/check-point-in-polygon", include_in_schema=False)
async def check_point_in_polygon(
    lat: float,
    lon: float,
    db: Session = Depends(get_db),
):
    """
    Check if a point is inside any restricted area polygon.
    """
    try:
        from app.services.geofencing import get_active_restricted_areas_for_routing
        from shapely.wkt import loads
        from shapely.geometry import Point

        blocked_areas = await get_active_restricted_areas_for_routing(db)
        point = Point(lon, lat)  # Shapely uses (x, y) which is (lon, lat)

        results = []
        for i, wkt_polygon in enumerate(blocked_areas):
            try:
                polygon = loads(wkt_polygon)
                is_inside = polygon.contains(point)
                results.append(
                    {
                        "polygon_index": i,
                        "wkt": wkt_polygon[:100] + "..."
                        if len(wkt_polygon) > 100
                        else wkt_polygon,
                        "point_inside": is_inside,
                        "polygon_bounds": list(
                            polygon.bounds
                        ),  # (minx, miny, maxx, maxy)
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "polygon_index": i,
                        "wkt": wkt_polygon[:100] + "...",
                        "error": str(e),
                    }
                )

        return {
            "point": {"lat": lat, "lon": lon},
            "total_polygons": len(blocked_areas),
            "polygons_containing_point": sum(
                1 for r in results if r.get("point_inside")
            ),
            "results": results,
        }

    except Exception as e:
        return {"error": str(e), "point": {"lat": lat, "lon": lon}}


@router.get("/test-northeast-india-routing", include_in_schema=False)
async def test_northeast_india_routing():
    """
    Test GraphHopper routing with predefined North East India coordinates.
    Tests multiple city pairs to ensure the service is working correctly.
    """
    try:
        import aiohttp

        base_url = "https://maps.rustedshader.com"

        # North East India test coordinates
        test_routes = [
            {
                "name": "Guwahati to Shillong",
                "start": [91.7362, 26.1445],  # Guwahati
                "end": [91.8933, 25.5788],  # Shillong
                "profile": "car",
            },
            {
                "name": "Guwahati to Dibrugarh",
                "start": [91.7362, 26.1445],  # Guwahati
                "end": [94.9120, 27.4728],  # Dibrugarh
                "profile": "car",
            },
            {
                "name": "Silchar to Imphal",
                "start": [92.7789, 24.8333],  # Silchar
                "end": [93.9063, 24.8170],  # Imphal
                "profile": "car",
            },
            {
                "name": "Short route in Guwahati",
                "start": [91.7362, 26.1445],  # Guwahati center
                "end": [91.7500, 26.1600],  # Nearby location
                "profile": "car",
            },
        ]

        results = {}

        async with aiohttp.ClientSession() as session:
            for test_route in test_routes:
                route_name = test_route["name"]

                # Test without block_areas first
                payload = {
                    "profile": test_route["profile"],
                    "points_encoded": False,
                    "points": [
                        test_route["start"],  # [lon, lat]
                        test_route["end"],
                    ],
                }

                try:
                    async with session.post(
                        f"{base_url}/route",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=30,
                    ) as response:
                        if response.status == 200:
                            route_data = await response.json()
                            path = (
                                route_data["paths"][0]
                                if route_data.get("paths")
                                else {}
                            )

                            results[route_name] = {
                                "success": True,
                                "distance_km": round(path.get("distance", 0) / 1000, 2),
                                "time_minutes": round(path.get("time", 0) / 60000, 1),
                                "coordinates_count": len(
                                    path.get("points", {}).get("coordinates", [])
                                ),
                                "start_coord": test_route["start"],
                                "end_coord": test_route["end"],
                                "first_route_coord": path.get("points", {}).get(
                                    "coordinates", [[]]
                                )[0]
                                if path.get("points", {}).get("coordinates")
                                else None,
                                "last_route_coord": path.get("points", {}).get(
                                    "coordinates", [[]]
                                )[-1]
                                if path.get("points", {}).get("coordinates")
                                else None,
                                "bbox": path.get("bbox", []),
                            }
                        else:
                            error_text = await response.text()
                            results[route_name] = {
                                "success": False,
                                "status": response.status,
                                "error": error_text[:300],
                                "start_coord": test_route["start"],
                                "end_coord": test_route["end"],
                            }

                except Exception as e:
                    results[route_name] = {
                        "success": False,
                        "error": f"Request failed: {str(e)}",
                        "start_coord": test_route["start"],
                        "end_coord": test_route["end"],
                    }

        # Summary
        successful_routes = sum(1 for r in results.values() if r.get("success"))
        total_routes = len(results)

        return {
            "graphhopper_url": base_url,
            "region": "North East India",
            "summary": {
                "successful_routes": successful_routes,
                "total_routes": total_routes,
                "success_rate": f"{successful_routes}/{total_routes}",
                "service_working": successful_routes > 0,
            },
            "test_results": results,
            "notes": [
                "All coordinates are in North East India region",
                "Testing basic routing functionality",
                "This helps verify GraphHopper is working before testing block_areas",
            ],
        }

    except Exception as e:
        return {
            "error": str(e),
            "graphhopper_url": base_url,
            "message": "Failed to test GraphHopper service",
        }


@router.post("/test-northeast-with-blocks", include_in_schema=False)
async def test_northeast_with_blocks(
    db: Session = Depends(get_db),
):
    """
    Test GraphHopper with block_areas using North East India coordinates.
    """
    try:
        import aiohttp
        from app.services.geofencing import get_active_restricted_areas_for_routing

        # Get blocked areas
        blocked_areas = await get_active_restricted_areas_for_routing(db)

        base_url = "https://maps.rustedshader.com"

        # Test route that might intersect with restricted areas
        test_coordinates = {
            "start": [91.7362, 26.1445],  # Guwahati [lon, lat]
            "end": [91.8933, 25.5788],  # Shillong [lon, lat]
        }

        results = {}

        async with aiohttp.ClientSession() as session:
            # Test 1: Without block_areas
            payload_without = {
                "profile": "car",
                "points_encoded": False,
                "points": [test_coordinates["start"], test_coordinates["end"]],
            }

            async with session.post(
                f"{base_url}/route",
                json=payload_without,
                headers={"Content-Type": "application/json"},
                timeout=30,
            ) as response:
                if response.status == 200:
                    route_data = await response.json()
                    path = route_data["paths"][0]
                    results["without_blocks"] = {
                        "success": True,
                        "distance_km": round(path["distance"] / 1000, 2),
                        "time_minutes": round(path["time"] / 60000, 1),
                        "coordinates_count": len(path["points"]["coordinates"]),
                        "route_sample": {
                            "first_5": path["points"]["coordinates"][:5],
                            "last_5": path["points"]["coordinates"][-5:],
                        },
                    }
                else:
                    results["without_blocks"] = {
                        "success": False,
                        "error": f"Status {response.status}: {await response.text()}",
                    }

            # Test 2: With block_areas
            if blocked_areas:
                payload_with = {
                    "profile": "car",
                    "points_encoded": False,
                    "points": [test_coordinates["start"], test_coordinates["end"]],
                    "block_areas": blocked_areas,
                }

                async with session.post(
                    f"{base_url}/route",
                    json=payload_with,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                ) as response:
                    if response.status == 200:
                        route_data = await response.json()
                        path = route_data["paths"][0]
                        results["with_blocks"] = {
                            "success": True,
                            "distance_km": round(path["distance"] / 1000, 2),
                            "time_minutes": round(path["time"] / 60000, 1),
                            "coordinates_count": len(path["points"]["coordinates"]),
                            "route_sample": {
                                "first_5": path["points"]["coordinates"][:5],
                                "last_5": path["points"]["coordinates"][-5:],
                            },
                        }
                    else:
                        error_text = await response.text()
                        results["with_blocks"] = {
                            "success": False,
                            "error": f"Status {response.status}: {error_text[:300]}",
                        }
            else:
                results["with_blocks"] = {
                    "success": False,
                    "error": "No blocked areas found in database",
                }

        # Analysis
        analysis = {
            "blocked_areas_count": len(blocked_areas),
            "test_route": "Guwahati to Shillong",
            "coordinates": test_coordinates,
            "routes_are_different": False,
            "difference_analysis": {},
        }

        if results.get("without_blocks", {}).get("success") and results.get(
            "with_blocks", {}
        ).get("success"):
            without_dist = results["without_blocks"]["distance_km"]
            with_dist = results["with_blocks"]["distance_km"]
            without_time = results["without_blocks"]["time_minutes"]
            with_time = results["with_blocks"]["time_minutes"]

            analysis["routes_are_different"] = abs(without_dist - with_dist) > 0.1
            analysis["difference_analysis"] = {
                "distance_difference_km": round(with_dist - without_dist, 2),
                "time_difference_minutes": round(with_time - without_time, 1),
                "distance_change_percent": round(
                    ((with_dist - without_dist) / without_dist) * 100, 2
                )
                if without_dist > 0
                else 0,
            }

        return {
            "analysis": analysis,
            "results": results,
            "blocked_areas_sample": blocked_areas[:2] if blocked_areas else [],
            "region": "North East India (Guwahati to Shillong)",
            "conclusion": "Routes are identical - block_areas not working"
            if not analysis.get("routes_are_different") and blocked_areas
            else "Routes are different - block_areas working"
            if analysis.get("routes_are_different")
            else "Need to check blocked areas",
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to test North East India routing with blocks",
        }


@router.post("/test-custom-model-geofencing", include_in_schema=False)
async def test_custom_model_geofencing(
    request: RoutingTestRequest,
    db: Session = Depends(get_db),
):
    """
    Test the new Custom Model approach for geofencing with GraphHopper.
    """
    try:
        from app.services.routing import graphhopper_service

        # Test the new Custom Model implementation
        route_data = await graphhopper_service.get_route(
            start_lat=request.start_lat,
            start_lon=request.start_lon,
            end_lat=request.end_lat,
            end_lon=request.end_lon,
            profile=request.profile,
            db=db,
            include_block_areas=True,
        )

        # Also get the GeoJSON data directly for comparison
        restricted_geojson = await graphhopper_service._get_restricted_areas_as_geojson(
            db
        )

        if route_data:
            summary = graphhopper_service.extract_route_summary(route_data)

            return {
                "success": True,
                "approach": "Custom Model with areas (2025 method)",
                "route": {
                    "type": "Feature",
                    "properties": {
                        "distance_km": summary.get("distance_km", 0),
                        "time_minutes": summary.get("time_minutes", 0),
                        "profile": request.profile,
                        "restricted_areas_count": len(
                            restricted_geojson.get("features", [])
                        )
                        if restricted_geojson
                        else 0,
                    },
                    "geometry": summary.get(
                        "geometry", {"type": "LineString", "coordinates": []}
                    ),
                },
                "debug": {
                    "restricted_areas_geojson": restricted_geojson,
                    "custom_model_used": restricted_geojson is not None,
                    "ch_disabled": restricted_geojson is not None,
                    "request_coordinates": {
                        "start": [request.start_lat, request.start_lon],
                        "end": [request.end_lat, request.end_lon],
                    },
                },
            }
        else:
            return {
                "success": False,
                "error": "No route found with Custom Model",
                "debug": {
                    "restricted_areas_geojson": restricted_geojson,
                    "custom_model_attempted": restricted_geojson is not None,
                },
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "approach": "Custom Model with areas (2025 method)",
        }
