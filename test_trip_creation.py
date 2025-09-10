#!/usr/bin/env python3
"""
Test script to verify trip auto-creation with populated fields
"""

import sys
import os

sys.path.append(".")

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.models.database.trips import Trips
from app.models.database.itinerary import Itinerary
from app.models.database.places import Place


def test_current_trips():
    """Check current trips in database"""
    engine = create_engine(str(settings.database_url))

    with Session(engine) as session:
        # Get all trips
        trips = session.exec(select(Trips)).all()
        print(f"📊 Total trips in database: {len(trips)}")

        # Show details of each trip
        for trip in trips:
            print(f"\n🎯 Trip ID: {trip.id}")
            print(f"   User ID: {trip.user_id}")
            print(f"   Itinerary ID: {trip.itinerary_id}")
            print(f"   Start Date: {trip.start_date}")
            print(f"   End Date: {trip.end_date}")
            print(f"   Status: {trip.status}")
            print(f"   Trip Type: {trip.trip_type}")
            print(f"   Hotel: {trip.hotel_name}")
            print(
                f"   Hotel Coordinates: ({trip.hotel_latitude}, {trip.hotel_longitude})"
            )
            print(f"   Destination: {trip.destination_name}")
            print(
                f"   Destination Coordinates: ({trip.destination_latitude}, {trip.destination_longitude})"
            )
            print(f"   Current Phase: {trip.current_phase}")
            print(f"   Trek ID: {trip.trek_id}")
            print(f"   Guide ID: {trip.guide_id}")
            print(f"   Tracking Device ID: {trip.tracking_deivce_id}")
            print(f"   Is Tracking Active: {trip.is_tracking_active}")

        # Also check itineraries
        itineraries = session.exec(select(Itinerary)).all()
        print(f"\n📋 Total itineraries in database: {len(itineraries)}")

        # Check places
        places = session.exec(select(Place)).all()
        print(f"📍 Total places in database: {len(places)}")

        if places:
            print("\n🏛️ Available places:")
            for place in places[:5]:  # Show first 5 places
                print(
                    f"   Place ID {place.id}: {place.name} at ({place.latitude}, {place.longitude})"
                )


if __name__ == "__main__":
    test_current_trips()
