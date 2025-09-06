from sqlalchemy.orm import Session
from app.models.database.user import User
from app.models.schemas.auth import UserCreate, UserCreateResponse, UserResponse
from app.utils.security import hash_password, hash_identifier
from web3 import Web3


async def create_user(user_create_data: UserCreate, db: Session) -> UserCreateResponse:
    try:
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
        )
    except Exception as e:
        db.rollback()
        raise e
