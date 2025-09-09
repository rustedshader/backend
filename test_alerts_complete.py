"""
Test script for Alert API functionality.

This script demonstrates how to use the Alert Management API for creating,
managing, and monitoring alerts in the SIH tourism safety system.
"""

import httpx
import asyncio
import json
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Sample test data
SAMPLE_LOGIN = {"username": "admin@test.com", "password": "admin123"}

SAMPLE_ALERT = {
    "trip_id": 1,
    "alert_type": "EMERGENCY",
    "description": "Tourist has not responded to check-in for 2 hours",
    "location": {"latitude": 28.7041, "longitude": 77.1025},
}

SAMPLE_DEVIATION_ALERT = {
    "trip_id": 1,
    "alert_type": "DEVIATION",
    "description": "Tourist is 500m off planned route near Kedarnath",
    "location": {"latitude": 30.7346, "longitude": 79.0669},
}

SAMPLE_WEATHER_ALERT = {
    "trip_id": 1,
    "alert_type": "WEATHER",
    "description": "Heavy rainfall warning issued for trekking area",
    "location": {"latitude": 30.7346, "longitude": 79.0669},
}


async def get_auth_token():
    """Get authentication token for API calls."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data=SAMPLE_LOGIN,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None


async def test_create_alert(token: str, alert_data: dict):
    """Test creating an alert."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/alerts/", json=alert_data, headers=headers
        )

        print(f"\n=== Create Alert ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alert = response.json()
            print(f"Created alert ID: {alert['id']}")
            print(f"Type: {alert['alert_type']}")
            print(f"Status: {alert['status']}")
            print(
                f"Location: {alert['location']['latitude']}, {alert['location']['longitude']}"
            )
            return alert["id"]
        else:
            print(f"Error: {response.text}")
            return None


async def test_get_alert_statistics(token: str):
    """Test getting alert statistics."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/alerts/statistics", headers=headers)

        print(f"\n=== Alert Statistics ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"Total Alerts: {stats['total_alerts']}")
            print(f"New Alerts: {stats['new_alerts']}")
            print(f"Emergency Alerts: {stats['emergency_alerts']}")
            print(f"Deviation Alerts: {stats['deviation_alerts']}")
            print(f"Weather Alerts: {stats['weather_alerts']}")
        else:
            print(f"Error: {response.text}")


async def test_get_emergency_alerts(token: str):
    """Test getting emergency alerts."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/alerts/emergency", headers=headers)

        print(f"\n=== Emergency Alerts ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alerts = response.json()
            print(f"Found {len(alerts)} emergency alerts")
            for alert in alerts:
                print(f"  Alert {alert['id']}: {alert['description']}")
        else:
            print(f"Error: {response.text}")


async def test_get_trip_alerts(token: str, trip_id: int):
    """Test getting alerts for a specific trip."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/alerts/trip/{trip_id}", headers=headers
        )

        print(f"\n=== Trip {trip_id} Alerts ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alerts = response.json()
            print(f"Found {len(alerts)} alerts for trip {trip_id}")
            for alert in alerts:
                print(
                    f"  Alert {alert['id']}: {alert['alert_type']} - {alert['status']}"
                )
        else:
            print(f"Error: {response.text}")


async def test_acknowledge_alert(token: str, alert_id: int):
    """Test acknowledging an alert."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/alerts/{alert_id}/acknowledge", headers=headers
        )

        print(f"\n=== Acknowledge Alert {alert_id} ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alert = response.json()
            print(f"Alert status updated to: {alert['status']}")
        else:
            print(f"Error: {response.text}")


async def test_resolve_alert(token: str, alert_id: int):
    """Test resolving an alert."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/alerts/{alert_id}/resolve", headers=headers
        )

        print(f"\n=== Resolve Alert {alert_id} ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alert = response.json()
            print(f"Alert status updated to: {alert['status']}")
        else:
            print(f"Error: {response.text}")


async def test_get_all_alerts(token: str):
    """Test getting all alerts with filters."""
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}

    # Test getting new alerts
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/alerts/?status=NEW&limit=10", headers=headers
        )

        print(f"\n=== All NEW Alerts ===")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            alerts = response.json()
            print(f"Found {len(alerts)} new alerts")
            for alert in alerts:
                print(
                    f"  Alert {alert['id']}: {alert['alert_type']} - {alert['description'][:50]}..."
                )
        else:
            print(f"Error: {response.text}")


async def main():
    """Main test function."""
    print("🚨 Alert Management API Test Suite")
    print("=" * 50)

    # Get authentication token
    print("Getting authentication token...")
    token = await get_auth_token()
    if not token:
        print(
            "❌ Failed to get authentication token. Make sure the server is running and credentials are correct."
        )
        return

    print("✅ Authentication successful!")

    # Test creating different types of alerts
    emergency_alert_id = await test_create_alert(token, SAMPLE_ALERT)
    deviation_alert_id = await test_create_alert(token, SAMPLE_DEVIATION_ALERT)
    weather_alert_id = await test_create_alert(token, SAMPLE_WEATHER_ALERT)

    # Test getting alert statistics
    await test_get_alert_statistics(token)

    # Test getting emergency alerts
    await test_get_emergency_alerts(token)

    # Test getting trip alerts
    await test_get_trip_alerts(token, 1)

    # Test alert lifecycle management
    if emergency_alert_id:
        await test_acknowledge_alert(token, emergency_alert_id)
        await test_resolve_alert(token, emergency_alert_id)

    # Test getting all alerts with filters
    await test_get_all_alerts(token)

    print("\n" + "=" * 50)
    print("🎉 Alert API test suite completed!")
    print("\nKey Features Tested:")
    print("✅ Alert creation (Emergency, Deviation, Weather)")
    print("✅ Alert statistics")
    print("✅ Emergency alerts monitoring")
    print("✅ Trip-specific alerts")
    print("✅ Alert acknowledgment")
    print("✅ Alert resolution")
    print("✅ Alert filtering")


if __name__ == "__main__":
    print("To run this test:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. Ensure you have an admin user in the database")
    print("3. Update SAMPLE_LOGIN credentials if needed")
    print("4. Run: python test_alerts_complete.py")
    print()

    # Uncomment the line below to run the test
    # asyncio.run(main())
