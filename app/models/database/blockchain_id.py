from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from enum import Enum


class BlockchainApplicationStatusEnum(str, Enum):
    PENDING = "pending"
    ISSUED = "issued"
    REJECTED = "rejected"


class BlockchainApplication(SQLModel, table=True):
    """Applications for blockchain ID issuance using itinerary ID"""

    __tablename__ = "blockchain_applications"

    id: Optional[int] = Field(default=None, primary_key=True)
    application_number: str = Field(..., unique=True, max_length=50)  # Auto-generated
    user_id: int = Field(..., foreign_key="users.id")
    itinerary_id: int = Field(..., foreign_key="itineraries.id")

    # Application Status and Timestamps
    status: BlockchainApplicationStatusEnum = Field(
        default=BlockchainApplicationStatusEnum.PENDING
    )
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    issued_at: Optional[datetime] = Field(default=None)
    rejected_at: Optional[datetime] = Field(default=None)

    # Admin who processed the application
    processed_by_admin: Optional[int] = Field(default=None, foreign_key="users.id")
    admin_notes: Optional[str] = Field(default=None, max_length=1000)

    # Relationships
    blockchain_id: Optional["BlockchainID"] = Relationship(back_populates="application")


class BlockchainID(SQLModel, table=True):
    """Issued blockchain IDs"""

    __tablename__ = "blockchain_ids"

    id: Optional[int] = Field(default=None, primary_key=True)
    blockchain_id: str = Field(..., unique=True, max_length=100)  # Unique blockchain ID
    application_id: int = Field(..., foreign_key="blockchain_applications.id")
    user_id: int = Field(..., foreign_key="users.id")

    # Blockchain Information
    blockchain_hash: str = Field(..., max_length=255)  # Hash on blockchain
    smart_contract_address: Optional[str] = Field(None, max_length=255)
    transaction_hash: Optional[str] = Field(None, max_length=255)

    # Validity Information
    issued_date: datetime = Field(default_factory=datetime.utcnow)
    expiry_date: datetime = Field(...)
    is_active: bool = Field(default=True)

    # QR Code data for the blockchain ID (for tourist to show)
    qr_code_data: Optional[str] = Field(None, max_length=1000)

    # Relationships
    application: BlockchainApplication = Relationship(back_populates="blockchain_id")
