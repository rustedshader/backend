from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.database.blockchain_id import BlockchainApplicationStatusEnum


# Tourist Application Request
class BlockchainApplicationRequest(BaseModel):
    itinerary_id: int = Field(..., description="ID of the user's itinerary")


# Admin Search and Management
class ApplicationSearchQuery(BaseModel):
    query: Optional[str] = Field(
        None, description="Search across user info, application number"
    )
    status: Optional[BlockchainApplicationStatusEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Response Models
class BlockchainApplicationResponse(BaseModel):
    id: int
    application_number: str
    user_id: int
    itinerary_id: int
    status: BlockchainApplicationStatusEnum
    applied_at: datetime
    issued_at: Optional[datetime]
    rejected_at: Optional[datetime]
    processed_by_admin: Optional[int]
    admin_notes: Optional[str]

    # User info (will be populated from relationships)
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None

    class Config:
        from_attributes = True


class BlockchainIDResponse(BaseModel):
    id: int
    blockchain_id: str
    blockchain_hash: str
    issued_date: datetime
    expiry_date: datetime
    is_active: bool
    qr_code_data: Optional[str]

    class Config:
        from_attributes = True


class BlockchainIDIssueRequest(BaseModel):
    application_id: int
    validity_days: int = Field(default=365, ge=1, le=3650)  # 1 day to 10 years
    admin_notes: Optional[str] = Field(None, max_length=1000)


# List Response Wrappers
class ApplicationListResponse(BaseModel):
    applications: List[BlockchainApplicationResponse]
    total_count: int
    page: int
    page_size: int


# Statistics
class BlockchainStatistics(BaseModel):
    total_applications: int
    pending_applications: int
    issued_ids: int
    rejected_applications: int
    applications_today: int
    issued_today: int


# API Response
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# Rejection Request
class ApplicationRejectionRequest(BaseModel):
    admin_notes: str = Field(
        ..., min_length=1, max_length=1000, description="Reason for rejection"
    )
