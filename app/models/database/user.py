from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.models.database.base import Base
from enum import Enum as PyEnum


class UserRoleEnum(str, PyEnum):
    ADMIN = "admin"
    USER = "user"
    SUPER_ADMIN = "super_admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    country_code = Column(String, index=True)
    phone_number = Column(String, unique=True, index=True)
    indian_citizenship = Column(Boolean, default=False)
    aadhar_number_hash = Column(String, nullable=True)
    passport_number_hash = Column(String, nullable=True)
    blockchain_address = Column(String, nullable=True)
    is_kyc_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER)
