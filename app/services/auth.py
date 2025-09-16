from sqlmodel import Session, select
from app.models.database.user import User
from app.models.schemas.auth import UserCreate, UserCreateResponse, UserResponse
from app.utils.security import hash_password, hash_identifier, verify_password


async def create_user(user_create_data: UserCreate, db: Session) -> UserCreateResponse:
    try:
        existing_user_email = db.exec(
            select(User).where(User.email == user_create_data.email)
        ).first()
        if existing_user_email:
            raise ValueError(f"User with email {user_create_data.email} already exists")

        existing_user_phone = db.exec(
            select(User).where(User.phone_number == user_create_data.phone_number)
        ).first()
        if existing_user_phone:
            raise ValueError(
                f"User with phone number {user_create_data.phone_number} already exists"
            )

        if user_create_data.aadhar_number:
            aadhar_hash_check = hash_identifier(user_create_data.aadhar_number)
            existing_user_aadhar = db.exec(
                select(User).where(User.aadhar_number_hash == aadhar_hash_check)
            ).first()
            if existing_user_aadhar:
                raise ValueError("User with this Aadhar number already exists")

        if user_create_data.passport_number:
            passport_hash_check = hash_identifier(user_create_data.passport_number)
            existing_user_passport = db.exec(
                select(User).where(User.passport_number_hash == passport_hash_check)
            ).first()
            if existing_user_passport:
                raise ValueError("User with this passport number already exists")

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

        user = User(
            first_name=user_create_data.first_name,
            middle_name=user_create_data.middle_name,
            last_name=user_create_data.last_name,
            email=user_create_data.email,
            country_code=user_create_data.country_code.value,
            phone_number=user_create_data.phone_number,
            aadhar_number_hash=aadhar_hash,
            passport_number_hash=passport_hash,
            password_hash=password_hash,
            blockchain_address=None,
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
        db.rollback()
        raise ve
    except Exception as e:
        db.rollback()
        raise e


async def authenticate_user(email: str, password: str, db: Session) -> User | None:
    statement = select(User).where(User.email == email)
    user = db.exec(statement).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None
