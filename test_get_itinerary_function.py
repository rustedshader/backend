#!/usr/bin/env python3
"""
Test get_itinerary_for_blockchain function directly
"""

import sys
import asyncio

sys.path.append(".")

from sqlmodel import Session, create_engine
from app.core.config import settings
from app.services.itinerary import get_itinerary_for_blockchain


async def test_get_itinerary_for_blockchain():
    """Test the get_itinerary_for_blockchain function"""
    engine = create_engine(str(settings.database_url))

    with Session(engine) as session:
        try:
            print("🔍 Testing get_itinerary_for_blockchain with itinerary_id=1...")
            result = await get_itinerary_for_blockchain(1, session)
            print("✅ Function succeeded!")
            print(f"📄 Result length: {len(result)} characters")
            print(f"📄 First 200 chars: {result[:200]}...")
        except Exception as e:
            print(f"❌ Function failed: {str(e)}")
            import traceback

            print(f"❌ Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_get_itinerary_for_blockchain())
