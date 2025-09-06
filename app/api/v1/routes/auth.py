from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.models.schemas.auth import UserCreate, UserCreateResponse
from app.models.database.base import get_db
from app.models.schemas.countries import Countries
from app.services.auth import create_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-up", response_model=UserCreateResponse)
async def sign_up(user_create_data: UserCreate, db=Depends(get_db)):
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    pass
