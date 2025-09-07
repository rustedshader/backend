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
        web3 = Web3()
        userblockchain_account = web3.eth.account.create()
        userblockchain_account_address = userblockchain_account.address
        userblockchain_account_private_key = userblockchain_account.key.hex()

        # Initialize blockchain client and issue tourist ID
        tourist_id_token = None
        tourist_id_transaction_hash = None

        try:
            blockchain_client = TouristIDClient()

            # Create KYC hash from user data
            kyc_data = {
                "first_name": user_create_data.first_name,
                "last_name": user_create_data.last_name,
                "email": user_create_data.email,
                "country_code": user_create_data.country_code.value,
                "aadhar_hash": aadhar_hash,
                "passport_hash": passport_hash,
            }
            kyc_json = json.dumps(kyc_data, sort_keys=True)
            kyc_hash = blockchain_client.bytes32_from_text(kyc_json)

            # Create a basic itinerary hash (can be updated later when user creates itinerary)
            basic_itinerary = f"default_itinerary_for_{user_create_data.email}"
            itinerary_hash = blockchain_client.bytes32_from_text(basic_itinerary)

            # Issue tourist ID (valid for 1 year = 365 * 24 * 3600 seconds)
            validity_seconds = 365 * 24 * 3600

            token_id, receipt = blockchain_client.issue_id(
                tourist=userblockchain_account_address,
                kyc_hash_hex32=kyc_hash,
                itinerary_hash_hex32=itinerary_hash,
                validity_seconds=validity_seconds,
            )

            # Only store token ID if it was successfully parsed
            if token_id != -1:
                tourist_id_token = token_id
            else:
                print("Warning: Token ID could not be parsed from transaction")
                tourist_id_token = None

            tourist_id_transaction_hash = receipt.transactionHash.hex()

        except Exception as blockchain_error:
            # Log the error but continue with user creation
            # In production, you might want to handle this differently
            print(f"Blockchain operation failed: {blockchain_error}")

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
            blockchain_address=userblockchain_account_address,
            tourist_id_token=tourist_id_token,
            tourist_id_transaction_hash=tourist_id_transaction_hash,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_response = UserResponse.model_validate(user)

        return UserCreateResponse(
            user=user_response,
            is_success=True,
            blockchain_private_key=userblockchain_account_private_key,
            blockchain_address=userblockchain_account_address,
            tourist_id_token=tourist_id_token,
            tourist_id_transaction_hash=tourist_id_transaction_hash,
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
