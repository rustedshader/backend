from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.models.schemas.auth import UserCreate, UserCreateResponse, Token
from app.models.database.base import get_db
from app.models.database.user import User
from app.models.schemas.countries import Countries
from app.services.auth import create_user, authenticate_user
from app.api.deps import get_current_user, get_current_active_user
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    store_refresh_token,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-up", response_model=UserCreateResponse)
async def sign_up(user_create_data: UserCreate, db: Session = Depends(get_db)):
    if user_create_data.indian_citizenship and not user_create_data.aadhar_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aadhar number is required for Indian citizens",
        )
    if (
        user_create_data.country_code == Countries.INDIA
        and not user_create_data.aadhar_number
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aadhar number is required for users from India",
        )

    if (
        user_create_data.country_code != Countries.INDIA
        and not user_create_data.passport_number
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passport number is required for non-Indian citizens",
        )
    try:
        response = await create_user(user_create_data, db)
        return response
    except ValueError as ve:
        # Handle validation errors (duplicate user data)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(ve)
        ) from ve
    except Exception as e:
        # Handle other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        ) from e


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}, expires_delta=3600
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email, "role": user.role.value}, expires_delta=86400
    )
    await store_refresh_token(db, user.id, refresh_token, expires_delta=86400)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information - requires authentication."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "is_kyc_verified": current_user.is_kyc_verified,
        "is_email_verified": current_user.is_email_verified,
        "blockchain_address": current_user.blockchain_address,
        "tourist_id_token": current_user.tourist_id_token,
        "tourist_id_transaction_hash": current_user.tourist_id_transaction_hash,
    }


@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Example protected route - requires active authentication."""
    return {
        "message": f"Hello {current_user.first_name}, this is a protected route!",
        "user_id": current_user.id,
        "user_role": current_user.role.value,
    }
