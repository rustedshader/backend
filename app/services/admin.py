from sqlmodel import Session, select, desc
from app.models.database.trips import Trips, TripStatusEnum
from app.models.database.location_history import LocationHistory
from app.models.database.user import User
from app.models.database.location_sharing import LocationSharing
from typing import Sequence, List, Dict
from geoalchemy2.functions import ST_X, ST_Y
from app.utils.blockchain import TouristIDClient
from web3 import Web3
import json
import datetime
# Admin Functions


async def issue_blockchain_id_at_entry_point(
    user_id: int, itinerary_id: int, validity_days: int, official_id: int, db: Session
) -> dict:
    """
    ⚠️ DEPRECATED: Issue blockchain ID to a tourist at an entry point by an authorized official.

    This function is deprecated. Please use the new blockchain ID application system:
    1. Create application: app.services.blockchain_id.apply_for_blockchain_id()
    2. Issue ID: app.services.blockchain_id.issue_blockchain_id()

    This should only be called after physical verification of documents.
    Automatically sets KYC verified to true when blockchain ID is issued.
    """
    try:
        # Add deprecation warning
        import warnings

        warnings.warn(
            "issue_blockchain_id_at_entry_point is deprecated. "
            "Use the new blockchain ID application system instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        from app.services import itinerary as itinerary_service

        # Get the user
        user = db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise ValueError("User not found")

        # KYC verification will be automatically set when blockchain ID is issued

        # Get itinerary data for blockchain
        itinerary_data = await itinerary_service.get_itinerary_for_blockchain(
            itinerary_id=itinerary_id, db=db
        )

        if not itinerary_data or itinerary_data.strip() == "":
            raise ValueError(f"Invalid itinerary data for itinerary_id {itinerary_id}")

        # Create blockchain account for the user
        web3 = Web3()
        userblockchain_account = web3.eth.account.create()
        userblockchain_account_address = userblockchain_account.address
        userblockchain_account_private_key = userblockchain_account.key.hex()

        # Validate blockchain address
        if not userblockchain_account_address or not web3.is_address(
            userblockchain_account_address
        ):
            raise ValueError("Failed to generate valid blockchain address")

        # Initialize blockchain client and issue tourist ID
        # Validate blockchain configuration first
        from app.core.config import settings

        if (
            not settings.owner_address
            or not settings.private_key
            or not settings.contract_address
        ):
            raise ValueError(
                "Blockchain configuration missing. Please set OWNER_ADDRESS, PRIVATE_KEY, and CONTRACT_ADDRESS environment variables."
            )

        blockchain_client = TouristIDClient()

        # Create KYC hash from user data - handle None values
        kyc_data = {
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "email": user.email or "",
            "country_code": user.country_code or "",
            "aadhar_hash": user.aadhar_number_hash or "",
            "passport_hash": user.passport_number_hash or "",
            "verified_by_official": official_id,
        }
        kyc_json = json.dumps(kyc_data, sort_keys=True)
        if not kyc_json or kyc_json.strip() == "":
            raise ValueError("Invalid KYC data - cannot generate hash")

        kyc_hash = blockchain_client.bytes32_from_text(kyc_json)
        if not kyc_hash:
            raise ValueError("Failed to generate KYC hash")

        # Create itinerary hash
        if not itinerary_data or itinerary_data.strip() == "":
            raise ValueError("Invalid itinerary data - cannot generate hash")

        itinerary_hash = blockchain_client.bytes32_from_text(itinerary_data)
        if not itinerary_hash:
            raise ValueError("Failed to generate itinerary hash")

        # Issue tourist ID with specified validity
        validity_seconds = validity_days * 24 * 3600

        token_id, receipt = blockchain_client.issue_id(
            tourist=userblockchain_account_address,
            kyc_hash_hex32=kyc_hash,
            itinerary_hash_hex32=itinerary_hash,
            validity_seconds=validity_seconds,
        )

        # Update user with blockchain information and automatically verify KYC
        user.blockchain_address = userblockchain_account_address
        user.is_kyc_verified = (
            True  # Automatically verify KYC when blockchain ID is issued
        )

        # Create a new trip for this tourist ID
        new_trip = Trips(
            user_id=user_id,
            itinerary_id=itinerary_id,
            status=TripStatusEnum.ONGOING,  # Auto-start the trip when blockchain ID is issued
            tourist_id=str(token_id) if token_id != -1 else None,
            blockchain_transaction_hash=receipt["transactionHash"].hex(),
        )

        db.add(user)
        db.add(new_trip)
        db.commit()
        db.refresh(user)
        db.refresh(new_trip)

        # Create location sharing code for the new trip
        location_sharing = LocationSharing(
            trip_id=new_trip.id,
            user_id=user_id,
            share_code=LocationSharing.generate_share_code(),
            is_active=True,
            expires_at=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(
                days=validity_days
            ),  # Set to same validity as tourist ID
        )

        db.add(location_sharing)
        db.commit()
        db.refresh(location_sharing)

        return {
            "success": True,
            "message": "Blockchain ID issued successfully, KYC verified, and trip started",
            "tourist_id_token": token_id,
            "trip_id": new_trip.id,
            "trip_status": new_trip.status.value,
            "blockchain_address": userblockchain_account_address,
            "transaction_hash": receipt["transactionHash"].hex(),
            "blockchain_private_key": userblockchain_account_private_key,  # Securely provide to user
            "validity_days": validity_days,
            "location_share_code": location_sharing.share_code,  # Include the share code in response
            "location_share_expires_at": location_sharing.expires_at,
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error in issue_blockchain_id_at_entry_point: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback

        print(f"❌ Traceback: {traceback.format_exc()}")
        raise e


async def get_active_trips(db: Session) -> Sequence[Trips]:
    stmt = select(Trips).where(Trips.status == TripStatusEnum.ONGOING)
    trips = db.exec(stmt).all()
    return trips


async def get_latest_location_all_trips(db: Session) -> List[Dict]:
    """Get the latest location for all ongoing trips"""

    # Get all ongoing trips
    ongoing_trips = db.exec(
        select(Trips).where(Trips.status == TripStatusEnum.ONGOING)
    ).all()

    trip_locations = []

    for trip in ongoing_trips:
        # Get the latest location for this trip
        latest_location_query = db.exec(
            select(
                LocationHistory,
                ST_X(LocationHistory.location).label("longitude"),
                ST_Y(LocationHistory.location).label("latitude"),
            )
            .where(LocationHistory.trip_id == trip.id)
            .order_by(desc(LocationHistory.timestamp))
            .limit(1)
        ).first()

        if latest_location_query:
            location_record, longitude, latitude = latest_location_query

            trip_location = {
                "trip_id": trip.id,
                "user_id": trip.user_id,
                "trip_status": trip.status,
                "tourist_id": trip.tourist_id,
                "latest_location": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "timestamp": location_record.timestamp,
                },
            }
        else:
            # No location data available for this trip
            trip_location = {
                "trip_id": trip.id,
                "user_id": trip.user_id,
                "trip_status": trip.status,
                "tourist_id": trip.tourist_id,
                "latest_location": None,
            }

        trip_locations.append(trip_location)

    return trip_locations
