#!/usr/bin/env python3
"""
Debug script to check why blockchain ID issuance is failing
"""

import sys

sys.path.append(".")

from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.models.database.user import User
from app.models.database.itinerary import Itinerary


def debug_blockchain_id_issue():
    """Debug the blockchain ID issuance issue"""
    engine = create_engine(str(settings.database_url))

    with Session(engine) as session:
        # Check user with ID 1
        user = session.exec(select(User).where(User.id == 1)).first()
        if not user:
            print("❌ User with ID 1 not found")
            return

        print(f"👤 User found: {user.email}")
        print(f"   First Name: {user.first_name}")
        print(f"   Last Name: {user.last_name}")
        print(f"   Country Code: {user.country_code}")
        print(f"   KYC Verified: {user.is_kyc_verified}")
        print(f"   Has Tourist ID Token: {user.tourist_id_token is not None}")
        print(f"   Tourist ID Token: {user.tourist_id_token}")
        print(f"   Blockchain Address: {user.blockchain_address}")
        print(f"   Aadhar Hash: {user.aadhar_number_hash}")
        print(f"   Passport Hash: {user.passport_number_hash}")

        # Check itinerary with ID 2
        itinerary = session.exec(select(Itinerary).where(Itinerary.id == 2)).first()
        if not itinerary:
            print("\n❌ Itinerary with ID 2 not found")
            # Check what itineraries exist
            all_itineraries = session.exec(select(Itinerary)).all()
            print(f"📋 Available itineraries: {[it.id for it in all_itineraries]}")
        else:
            print(f"\n📋 Itinerary found: {itinerary.title}")
            print(f"   User ID: {itinerary.user_id}")
            print(f"   Status: {itinerary.status}")
            print(f"   Start Date: {itinerary.start_date}")
            print(f"   End Date: {itinerary.end_date}")


if __name__ == "__main__":
    debug_blockchain_id_issue()
