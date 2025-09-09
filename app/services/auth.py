from sqlmodel import Session, select
from app.models.database.user import User
from app.models.schemas.auth import UserCreate, UserCreateResponse, UserResponse
from app.utils.security import hash_password, hash_identifier, verify_password
from app.utils.blockchain import TouristIDClient
from web3 import Web3
import hashlib
import json


async def create_user(user_create_data: UserCreate, db: Session) -> UserCreateResponse:
    try:
        # First, check if user already exists to avoid unnecessary blockchain operations
        existing_user_email = db.exec(
            select(User).where(User.email == user_create_data.email)
        ).first()
        if existing_user_email:
            raise ValueError(f"User with email {user_create_data.email} already exists")

        # Check if phone number already exists
        existing_user_phone = db.exec(
            select(User).where(User.phone_number == user_create_data.phone_number)
        ).first()
        if existing_user_phone:
            raise ValueError(
                f"User with phone number {user_create_data.phone_number} already exists"
            )

        # If Aadhar number is provided, check for duplicates
        if user_create_data.aadhar_number:
            aadhar_hash_check = hash_identifier(user_create_data.aadhar_number)
            existing_user_aadhar = db.exec(
                select(User).where(User.aadhar_number_hash == aadhar_hash_check)
            ).first()
            if existing_user_aadhar:
                raise ValueError("User with this Aadhar number already exists")

        # If passport number is provided, check for duplicates
        if user_create_data.passport_number:
            passport_hash_check = hash_identifier(user_create_data.passport_number)
            existing_user_passport = db.exec(
                select(User).where(User.passport_number_hash == passport_hash_check)
            ).first()
            if existing_user_passport:
                raise ValueError("User with this passport number already exists")

        # Now proceed with user creation since all validations passed
        password_hash = hash_password(user_create_data.password)
        aadhar_hash = (
            hash_identifier(user_create_data.aadhar_number)
            if user_create_data.aadhar_number
            else None
        )
        passport_hash = (
            hash_identifier(user_create_data.passport_number)
            if user_create_data.passport_number
            else None
        )

        # Create user without blockchain ID - ID will be issued at entry points
        user = User(
            first_name=user_create_data.first_name,
            middle_name=user_create_data.middle_name,
            last_name=user_create_data.last_name,
            email=user_create_data.email,
            country_code=user_create_data.country_code.value,
            phone_number=user_create_data.phone_number,
            indian_citizenship=user_create_data.indian_citizenship,
            aadhar_number_hash=aadhar_hash,
            passport_number_hash=passport_hash,
            password_hash=password_hash,
            # Blockchain fields will be null until official verification
            blockchain_address=None,
            tourist_id_token=None,
            tourist_id_transaction_hash=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_response = UserResponse.model_validate(user)

        return UserCreateResponse(
            user=user_response,
            is_success=True,
            message="Profile created successfully. Blockchain ID will be issued at entry points.",
        )
    except ValueError as ve:
        # Handle validation errors (duplicate email, phone, etc.)
        db.rollback()
        raise ve
    except Exception as e:
        # Handle other unexpected errors
        db.rollback()
        raise e


async def authenticate_user(email: str, password: str, db: Session) -> User | None:
    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


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

        # Check if user already has a blockchain ID
        if user.tourist_id_token is not None:
            raise ValueError("User already has a blockchain ID issued")

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
        user.tourist_id_token = token_id if token_id != -1 else None
        user.tourist_id_transaction_hash = receipt.transactionHash.hex()

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "success": True,
            "message": "Blockchain ID issued successfully",
            "tourist_id_token": token_id,
            "blockchain_address": userblockchain_account_address,
            "transaction_hash": receipt.transactionHash.hex(),
            "blockchain_private_key": userblockchain_account_private_key,  # Securely provide to user
            "validity_days": validity_days,
        }

    except Exception as e:
        db.rollback()
        raise e


async def get_user_profile_for_verification(user_id: int, db: Session) -> dict:
    """
    Get user profile information for official verification at entry points.
    """
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise ValueError("User not found")

    return {
        "id": user.id,
        "first_name": user.first_name,
        "middle_name": user.middle_name,
        "last_name": user.last_name,
        "email": user.email,
        "country_code": user.country_code,
        "phone_number": user.phone_number,
        "indian_citizenship": user.indian_citizenship,
        "is_kyc_verified": user.is_kyc_verified,
        "has_blockchain_id": user.tourist_id_token is not None,
        "blockchain_address": user.blockchain_address,
        "tourist_id_token": user.tourist_id_token,
    }
