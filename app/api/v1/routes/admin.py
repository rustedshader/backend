from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, select
from app.api.deps import get_current_admin_user
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.database.trips import Trips, TripStatusEnum
from app.models.schemas.auth import (
    BlockchainIDRequest,
    BlockchainIDResponse,
)
from app.utils.blockchain import TouristIDClient
from web3 import Web3
import json

router = APIRouter(prefix="/admin", tags=["admin"])


async def issue_blockchain_id_at_entry_point(
    user_id: int, itinerary_id: int, validity_days: int, official_id: int, db: Session
) -> dict:
    """
    Issue blockchain ID to a tourist at an entry point by an authorized official.
    This should only be called after physical verification of documents.
    """
    try:
        from app.services import itinerary as itinerary_service

        # Get the user
        user = db.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise ValueError("User not found")

        # Check if user is KYC verified (you might want to add this check)
        if not user.is_kyc_verified:
            raise ValueError("User KYC must be verified before issuing blockchain ID")

        # Get itinerary data for blockchain
        itinerary_data = await itinerary_service.get_itinerary_for_blockchain(
            itinerary_id=itinerary_id, db=db
        )

        # Create blockchain account for the user
        web3 = Web3()
        userblockchain_account = web3.eth.account.create()
        userblockchain_account_address = userblockchain_account.address
        userblockchain_account_private_key = userblockchain_account.key.hex()

        # Initialize blockchain client and issue tourist ID
        blockchain_client = TouristIDClient()

        # Create KYC hash from user data
        kyc_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "country_code": user.country_code,
            "aadhar_hash": user.aadhar_number_hash,
            "passport_hash": user.passport_number_hash,
            "verified_by_official": official_id,
        }
        kyc_json = json.dumps(kyc_data, sort_keys=True)
        kyc_hash = blockchain_client.bytes32_from_text(kyc_json)

        # Create itinerary hash
        itinerary_hash = blockchain_client.bytes32_from_text(itinerary_data)

        # Issue tourist ID with specified validity
        validity_seconds = validity_days * 24 * 3600

        token_id, receipt = blockchain_client.issue_id(
            tourist=userblockchain_account_address,
            kyc_hash_hex32=kyc_hash,
            itinerary_hash_hex32=itinerary_hash,
            validity_seconds=validity_seconds,
        )

        # Update user with blockchain information
        user.blockchain_address = userblockchain_account_address

        # Create a new trip for this tourist ID
        new_trip = Trips(
            user_id=user_id,
            itinerary_id=itinerary_id,
            status=TripStatusEnum.ONGOING,  # Auto-start the trip when blockchain ID is issued
            tourist_id=str(token_id) if token_id != -1 else None,
            blockchain_transaction_hash=receipt.transactionHash.hex(),
        )

        db.add(user)
        db.add(new_trip)
        db.commit()
        db.refresh(user)
        db.refresh(new_trip)

        return {
            "success": True,
            "message": "Blockchain ID issued successfully and trip started",
            "tourist_id_token": token_id,
            "trip_id": new_trip.id,
            "trip_status": new_trip.status.value,
            "blockchain_address": userblockchain_account_address,
            "transaction_hash": receipt.transactionHash.hex(),
            "blockchain_private_key": userblockchain_account_private_key,  # Securely provide to user
            "validity_days": validity_days,
        }

    except Exception as e:
        db.rollback()
        print(f"❌ Error in issue_blockchain_id_at_entry_point: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback

        print(f"❌ Traceback: {traceback.format_exc()}")
        raise e


@router.post("/issue-blockchain-id", response_model=BlockchainIDResponse)
async def issue_blockchain_id(
    request: BlockchainIDRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Issue blockchain ID to a tourist at entry point.
    This should only be called after physical verification of documents.
    Only authorized officials can call this endpoint.
    """
    try:
        result = await issue_blockchain_id_at_entry_point(
            user_id=request.user_id,
            itinerary_id=request.itinerary_id,
            validity_days=request.validity_days,
            official_id=admin_user.id,
            db=db,
        )
        return BlockchainIDResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to issue blockchain ID: {e}",
        )
