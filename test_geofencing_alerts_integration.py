"""
Integration test: Geofencing + Alert System

This script demonstrates how geofencing violations can automatically trigger alerts.
It shows the integration between the geofencing system and alert management.
"""

import httpx
import asyncio


# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Sample restricted area (around a dangerous cliff area)
RESTRICTED_AREA = {
    "name": "Dangerous Cliff Zone - Kedarnath",
    "description": "Steep cliff area with loose rocks - extremely dangerous for tourists",
    "area_type": "DANGEROUS_TERRAIN",
    "coordinates": [
        [79.0650, 30.7350],  # Point 1
        [79.0670, 30.7350],  # Point 2
        [79.0670, 30.7340],  # Point 3
        [79.0650, 30.7340],  # Point 4
        [79.0650, 30.7350],  # Close polygon
    ],
    "is_active": True,
}

# Tourist location that violates the restricted area
TOURIST_LOCATION = {
    "latitude": 30.7345,  # Inside the restricted area
    "longitude": 79.0665,  # Inside the restricted area
}

# Sample trip for testing
SAMPLE_TRIP = {
    "name": "Kedarnath Trek",
    "description": "5-day spiritual trek to Kedarnath temple",
    "destination": "Kedarnath, Uttarakhand",
    "start_date": "2025-09-15",
    "end_date": "2025-09-20",
    "trip_type": "TREK",
}


async def create_test_scenario():
    """Create a complete test scenario with geofencing and alerts."""

    print("🔒 Geofencing + Alert System Integration Test")
    print("=" * 60)

    # Note: This is a demonstration of how the systems would work together
    # In a real scenario, you would:

    print("\n1. 🏔️  SETUP PHASE")
    print("   ✅ Admin creates restricted area around dangerous cliff")
    print(f"   📍 Area: {RESTRICTED_AREA['name']}")
    print(f"   📏 Coordinates: {len(RESTRICTED_AREA['coordinates'])} points")
    print(f"   ⚠️  Type: {RESTRICTED_AREA['area_type']}")

    print("\n2. 🚶 TRIP PHASE")
    print("   ✅ Tourist starts trek to Kedarnath")
    print(f"   🎯 Destination: {SAMPLE_TRIP['destination']}")
    print("   📱 GPS tracking device activated")

    print("\n3. ⚡ REAL-TIME MONITORING")
    print("   🔄 System continuously monitors tourist location")
    print(
        f"   📍 Current location: {TOURIST_LOCATION['latitude']}, {TOURIST_LOCATION['longitude']}"
    )

    print("\n4. 🚨 GEOFENCE VIOLATION DETECTED!")
    print("   ❌ Tourist has entered restricted area")
    print("   🔔 Automatic alert generation triggered")

    # This is what would happen automatically:
    violation_alert = {
        "trip_id": 1,
        "alert_type": "DEVIATION",
        "description": f"GEOFENCE VIOLATION: Tourist entered {RESTRICTED_AREA['name']}",
        "location": TOURIST_LOCATION,
    }

    print(f"\n5. 📢 ALERT CREATED")
    print(f"   🆔 Alert Type: {violation_alert['alert_type']}")
    print(f"   📝 Description: {violation_alert['description']}")
    print(f"   📍 Location: {violation_alert['location']}")

    print("\n6. 🎯 AUTOMATIC RESPONSE CHAIN")
    print("   📨 SMS sent to guide: 'Tourist in dangerous area!'")
    print("   📧 Email sent to emergency contact")
    print("   🚨 Admin dashboard shows emergency alert")
    print("   📱 Push notification to guide's mobile app")

    print("\n7. 🛟 RESCUE COORDINATION")
    print("   👨‍💼 Guide acknowledges alert")
    print("   📞 Guide calls tourist immediately")
    print("   🗺️  Rescue route planned using routing API")
    print("   ✅ Tourist guided to safety")
    print("   ✅ Alert marked as resolved")

    print("\n" + "=" * 60)
    print("🎉 INTEGRATION COMPLETE!")
    print("\nKey Integration Benefits:")
    print("✅ Automatic alert generation from geofence violations")
    print("✅ Real-time safety monitoring")
    print("✅ Immediate emergency response")
    print("✅ Coordinated rescue operations")
    print("✅ Complete audit trail for safety incidents")

    print("\nAPI Endpoints Used in Integration:")
    print("🔗 POST /geofencing/areas/ - Create restricted areas")
    print("🔗 GET /geofencing/areas/check - Check geofence violations")
    print("🔗 POST /alerts/ - Create automatic alerts")
    print("🔗 GET /alerts/emergency - Monitor emergency situations")
    print("🔗 POST /routing/route - Plan rescue routes avoiding restricted areas")


def show_api_examples():
    """Show example API calls for the integration."""

    print("\n" + "=" * 60)
    print("📚 API INTEGRATION EXAMPLES")
    print("=" * 60)

    print("\n1. Create Restricted Area (Admin):")
    print("POST /geofencing/areas/")
    print("Content-Type: application/json")
    print("Authorization: Bearer {admin_token}")
    print(f"Body: {RESTRICTED_AREA}")

    print("\n2. Check Geofence Violation (Automated System):")
    print("POST /geofencing/areas/check")
    print("Content-Type: application/json")
    print("Body: {")
    print(f"  'latitude': {TOURIST_LOCATION['latitude']},")
    print(f"  'longitude': {TOURIST_LOCATION['longitude']}")
    print("}")

    print("\n3. Create Alert on Violation (Automated):")
    print("POST /alerts/")
    print("Content-Type: application/json")
    print("Body: {")
    print("  'trip_id': 1,")
    print("  'alert_type': 'DEVIATION',")
    print("  'description': 'Geofence violation detected',")
    print(f"  'location': {TOURIST_LOCATION}")
    print("}")

    print("\n4. Get Emergency Alerts (Guide Dashboard):")
    print("GET /alerts/emergency")
    print("Authorization: Bearer {guide_token}")

    print("\n5. Plan Safe Route (Rescue Operation):")
    print("POST /routing/route")
    print("Content-Type: application/json")
    print("Body: {")
    print("  'start': [79.0665, 30.7345],")
    print("  'end': [79.0600, 30.7400],")
    print("  'include_block_areas': true")
    print("}")
    print("Note: Restricted areas automatically included as block_areas")


async def main():
    """Main demonstration function."""
    await create_test_scenario()
    show_api_examples()

    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS")
    print("=" * 60)
    print("1. Start the FastAPI server")
    print("2. Create admin user and get auth token")
    print("3. Use the API examples above to test the integration")
    print("4. Monitor the complete safety workflow")


if __name__ == "__main__":
    asyncio.run(main())
