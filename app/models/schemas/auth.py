from pydantic import BaseModel, EmailStr
from app.models.schemas.countries import Countries
from app.models.database.user import UserRoleEnum


class UserCreate(BaseModel):
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    country_code: Countries
    email: EmailStr
    password: str
    phone_number: str
    indian_citizenship: bool = False
    aadhar_number: str | None = None
    passport_number: str | None = None


class UserResponse(BaseModel):
    id: int
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    email: str
    country_code: str
    phone_number: str
    indian_citizenship: bool
    is_kyc_verified: bool
    is_email_verified: bool
    is_active: bool
    role: UserRoleEnum
    blockchain_address: str | None = None
    tourist_id_token: int | None = None
    tourist_id_transaction_hash: str | None = None

    class Config:
        from_attributes = True


class UserCreateResponse(BaseModel):
    user: UserResponse
    is_success: bool
    blockchain_private_key: str
    blockchain_address: str
    tourist_id_token: int | None = None
    tourist_id_transaction_hash: str | None = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None
