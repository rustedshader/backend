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
    is_kyc_verified: bool
    is_email_verified: bool
    is_active: bool
    role: UserRoleEnum
    blockchain_address: str | None = None

    class Config:
        from_attributes = True


class UserCreateResponse(BaseModel):
    user: UserResponse
    is_success: bool
    message: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BlockchainIDRequest(BaseModel):
    user_id: int
    itinerary_id: int
    validity_days: int = 30  # Default 30 days validity


class BlockchainIDResponse(BaseModel):
    success: bool
    message: str
    tourist_id_token: int | None = None
    trip_id: int | None = None
    trip_status: str | None = None
    blockchain_address: str | None = None
    transaction_hash: str | None = None
    blockchain_private_key: str | None = None
    validity_days: int


class UserVerificationProfile(BaseModel):
    id: int
    first_name: str
    middle_name: str | None = None
    last_name: str | None = None
    email: str
    country_code: str
    phone_number: str
    is_kyc_verified: bool
    has_blockchain_id: bool
    blockchain_address: str | None = None
    tourist_id_token: int | None = None


class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None


class UserListResponse(BaseModel):
    """Response model for user list with pagination info"""

    users: list[UserResponse]
    total_count: int
    offset: int
    limit: int


class UserVerificationRequest(BaseModel):
    """Request model for user verification"""

    verification_notes: str | None = None


class UserVerificationResponse(BaseModel):
    """Response model for user verification"""

    success: bool
    message: str
    user: UserResponse


class BlockchainInfoResponse(BaseModel):
    """Response model for user blockchain information"""

    user_id: int
    blockchain_address: str | None = None
    tourist_id_token: int | None = None
    tourist_id_transaction_hash: str | None = None
    has_blockchain_id: bool
    is_kyc_verified: bool


class UserStatsResponse(BaseModel):
    """Response model for user statistics"""

    total_users: int
    by_role: dict
    by_verification: dict
    by_status: dict
    blockchain_ids_issued: int


class UserStatusUpdateRequest(BaseModel):
    """Request model for updating user status"""

    is_active: bool
    reason: str | None = None
