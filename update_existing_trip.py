#!/usr/bin/env python3
"""
Script to update existing trip with proper data from its itinerary
"""

import sys

sys.path.append(".")

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.models.database.trips import Trips
from app.models.database.itinerary import Itinerary, ItineraryDay
from app.models.database.places import Place


def update_existing_trip():
    """Update the existing trip with data from its itinerary"""
    engine = create_engine(str(settings.database_url))

    with Session(engine) as session:
        # Get the existing trip
        trip = session.exec(select(Trips).where(Trips.id == 1)).first()
        if not trip:
            print("❌ No trip found with ID 1")
            return

        # Get its itinerary
        itinerary = session.exec(
            select(Itinerary).where(Itinerary.id == trip.itinerary_id)
        ).first()
        if not itinerary:
            print("❌ No itinerary found for this trip")
            return

        # Get the first itinerary day
        itinerary_day = session.exec(
            select(ItineraryDay).where(
                ItineraryDay.itinerary_id == itinerary.id, ItineraryDay.day_number == 1
            )
        ).first()

        # Get the primary place
        primary_place = None
        if itinerary.primary_place_id:
            primary_place = session.exec(
                select(Place).where(Place.id == itinerary.primary_place_id)
            ).first()

        print(f"🔍 Found trip {trip.id} for itinerary {itinerary.id}")
        print(f"📋 Itinerary: {itinerary.title}")
        print(f"🏛️ Primary place: {primary_place.name if primary_place else 'None'}")
        print(
            f"🏨 First day accommodation: {itinerary_day.accommodation_name if itinerary_day else 'None'}"
        )

        # Update trip with rich data
        if itinerary_day:
            trip.hotel_name = itinerary_day.accommodation_name
            trip.hotel_latitude = itinerary_day.accommodation_latitude
            trip.hotel_longitude = itinerary_day.accommodation_longitude

        if primary_place:
            trip.destination_name = (
                f"{primary_place.name}, {itinerary.destination_city}"
            )
            trip.destination_latitude = primary_place.latitude
            trip.destination_longitude = primary_place.longitude
        else:
            trip.destination_name = (
                f"{itinerary.destination_city}, {itinerary.destination_state}"
            )

        trip.current_phase = "tour_planning"
        trip.trek_id = itinerary.trek_id

        # Commit the changes
        session.add(trip)
        session.commit()
        session.refresh(trip)

        print(f"\n✅ Updated trip {trip.id} with:")
        print(f"   Hotel: {trip.hotel_name}")
        print(f"   Hotel Coordinates: ({trip.hotel_latitude}, {trip.hotel_longitude})")
        print(f"   Destination: {trip.destination_name}")
        print(
            f"   Destination Coordinates: ({trip.destination_latitude}, {trip.destination_longitude})"
        )
        print(f"   Current Phase: {trip.current_phase}")


if __name__ == "__main__":
    update_existing_trip()
