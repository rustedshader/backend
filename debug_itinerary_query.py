#!/usr/bin/env python3
"""
Debug itinerary query issue
"""

import sys

sys.path.append(".")

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.models.database.itinerary import Itinerary


def debug_itinerary_query():
    """Debug the itinerary query"""
    engine = create_engine(str(settings.database_url))

    with Session(engine) as session:
        # First, let's see all itineraries
        all_itineraries = session.exec(select(Itinerary)).all()
        print(f"📋 Total itineraries in database: {len(all_itineraries)}")

        for itinerary in all_itineraries:
            print(
                f"   ID: {itinerary.id}, Title: {itinerary.title}, User: {itinerary.user_id}"
            )

        # Now try to get itinerary with ID 1 specifically
        print(f"\n🔍 Querying for itinerary ID 1...")
        itinerary_1 = session.exec(select(Itinerary).where(Itinerary.id == 1)).first()

        if itinerary_1:
            print(f"✅ Found itinerary 1: {itinerary_1.title}")
        else:
            print("❌ Itinerary 1 not found in query")

        # Let's also check the raw SQL
        print(f"\n📊 Database engine URL: {str(engine.url)}")


if __name__ == "__main__":
    debug_itinerary_query()
