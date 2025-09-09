#!/usr/bin/env python3
"""
Test script for the enhanced routing system with GeoJSON and round-trip functionality
"""

import asyncio
from app.services.routing import GraphHopperService


async def test_geojson_format():
    """Test that our GraphHopper service returns proper GeoJSON"""
    print("Testing GeoJSON format...")

    graphhopper = GraphHopperService()

    # Test coordinates: Delhi to Agra (example)
    route_data = await graphhopper.get_route(
        start_lat=28.6139,
        start_lon=77.2090,
        end_lat=27.1767,
        end_lon=78.0081,
        profile="car",
    )

    if route_data:
        summary = graphhopper.extract_route_summary(route_data)

        print(f"Distance: {summary.get('distance_km', 0):.2f} km")
        print(f"Time: {summary.get('time_hours', 0):.2f} hours")

        # Check GeoJSON geometry
        geometry = summary.get("geometry")
        if geometry:
            print(f"Geometry type: {geometry.get('type')}")
            print(f"Coordinates count: {len(geometry.get('coordinates', []))}")

            # Validate GeoJSON structure
            if geometry.get("type") == "LineString" and "coordinates" in geometry:
                print("✅ GeoJSON format is correct!")

                # Sample first few coordinates
                coords = geometry["coordinates"][:3]
                print(f"Sample coordinates: {coords}")
            else:
                print("❌ GeoJSON format is incorrect")
        else:
            print("❌ No geometry found in response")
    else:
        print("❌ No route data received")


async def test_segment_types():
    """Test that segment types are correctly classified"""
    print("\nTesting segment type classification...")

    from app.models.schemas.routing import RoutePoint

    # Mock waypoints for a typical round trip
    hotel = RoutePoint(
        latitude=28.6139, longitude=77.2090, name="Hotel Delhi", type="hotel"
    )

    attraction = RoutePoint(
        latitude=28.6562, longitude=77.2410, name="Red Fort", type="place"
    )

    # Simulate segment type logic
    segments = [(hotel, attraction, "outbound"), (attraction, hotel, "return")]

    for from_point, to_point, expected_type in segments:
        # Apply the same logic as in the service
        segment_type = "transfer"  # default
        if from_point.type == "hotel" and to_point.type in ["place", "trek_start"]:
            segment_type = "outbound"
        elif from_point.type in ["place", "trek_start"] and to_point.type == "hotel":
            segment_type = "return"

        if segment_type == expected_type:
            print(f"✅ {from_point.name} → {to_point.name}: {segment_type}")
        else:
            print(
                f"❌ {from_point.name} → {to_point.name}: expected {expected_type}, got {segment_type}"
            )


def test_route_segment_schema():
    """Test the RouteSegment schema with GeoJSON"""
    print("\nTesting RouteSegment schema...")

    from app.models.schemas.routing import RouteSegment, RoutePoint

    # Create sample points
    start = RoutePoint(
        latitude=28.6139, longitude=77.2090, name="Start Point", type="hotel"
    )

    end = RoutePoint(
        latitude=28.6562, longitude=77.2410, name="End Point", type="place"
    )

    # Create sample GeoJSON geometry
    sample_geometry = {
        "type": "LineString",
        "coordinates": [[77.2090, 28.6139], [77.2200, 28.6300], [77.2410, 28.6562]],
    }

    # Create RouteSegment
    try:
        segment = RouteSegment(
            from_point=start,
            to_point=end,
            distance_meters=5000,
            distance_km=5.0,
            time_seconds=900,
            time_minutes=15.0,
            time_hours=0.25,
            geometry=sample_geometry,
            coordinates=[[77.2090, 28.6139], [77.2410, 28.6562]],
            instructions=[],
            bbox=[77.2090, 28.6139, 77.2410, 28.6562],
            segment_type="outbound",
        )

        print("✅ RouteSegment schema works correctly")
        print(f"   Segment type: {segment.segment_type}")
        print(
            f"   Geometry type: {segment.geometry['type'] if segment.geometry else None}"
        )
        print(f"   Distance: {segment.distance_km} km")

    except Exception as e:
        print(f"❌ RouteSegment schema error: {e}")


if __name__ == "__main__":
    print("🧪 Testing Enhanced Routing System")
    print("=" * 50)

    # Test schema first (synchronous)
    test_route_segment_schema()

    # Test async components
    asyncio.run(test_geojson_format())
    asyncio.run(test_segment_types())

    print("\n🎉 Testing complete!")
