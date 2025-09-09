from typing import List, Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.database.user import User, UserRoleEnum
from app.models.schemas.auth import UserResponse


class UserService:
    """Service class for user management operations"""

    @staticmethod
    async def get_all_users(
        db: Session,
        role_filter: Optional[UserRoleEnum] = None,
        is_active_filter: Optional[bool] = None,
        is_verified_filter: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[UserResponse]:
        """Get all users with optional filtering"""
        try:
            statement = select(User)

            # Apply filters
            if role_filter:
                statement = statement.where(User.role == role_filter)

            if is_active_filter is not None:
                statement = statement.where(User.is_active == is_active_filter)

            if is_verified_filter is not None:
                statement = statement.where(User.is_kyc_verified == is_verified_filter)

            # Apply pagination
            statement = statement.offset(offset).limit(limit).order_by(User.id.desc())

            users = db.exec(statement).all()

            return [UserResponse.model_validate(user) for user in users]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve users: {str(e)}",
            )

    @staticmethod
    async def get_user_by_id(db: Session, user_id: int) -> UserResponse:
        """Get user by ID"""
        try:
            statement = select(User).where(User.id == user_id)
            user = db.exec(statement).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            return UserResponse.model_validate(user)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user: {str(e)}",
            )

    @staticmethod
    async def verify_user(db: Session, user_id: int, admin_id: int) -> UserResponse:
        """Verify a user's KYC status"""
        try:
            statement = select(User).where(User.id == user_id)
            user = db.exec(statement).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            if user.is_kyc_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already verified",
                )

            # Update user verification status
            user.is_kyc_verified = True
            db.add(user)
            db.commit()
            db.refresh(user)

            return UserResponse.model_validate(user)

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify user: {str(e)}",
            )

    @staticmethod
    async def get_user_blockchain_info(db: Session, user_id: int) -> dict:
        """Get blockchain information for a user"""
        try:
            statement = select(User).where(User.id == user_id)
            user = db.exec(statement).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            return {
                "user_id": user.id,
                "blockchain_address": user.blockchain_address,
                "tourist_id_token": user.tourist_id_token,
                "tourist_id_transaction_hash": user.tourist_id_transaction_hash,
                "has_blockchain_id": bool(user.tourist_id_token),
                "is_kyc_verified": user.is_kyc_verified,
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve blockchain info: {str(e)}",
            )

    @staticmethod
    async def get_user_stats(db: Session) -> dict:
        """Get user statistics for admin dashboard"""
        try:
            # Get total users count
            total_users = db.exec(select(User)).all()

            # Count by role
            admin_count = len([u for u in total_users if u.role == UserRoleEnum.ADMIN])
            tourist_count = len(
                [u for u in total_users if u.role == UserRoleEnum.TOURIST]
            )
            guide_count = len([u for u in total_users if u.role == UserRoleEnum.GUIDE])
            super_admin_count = len(
                [u for u in total_users if u.role == UserRoleEnum.SUPER_ADMIN]
            )

            # Count by verification status
            verified_count = len([u for u in total_users if u.is_kyc_verified])
            unverified_count = len([u for u in total_users if not u.is_kyc_verified])

            # Count by active status
            active_count = len([u for u in total_users if u.is_active])
            inactive_count = len([u for u in total_users if not u.is_active])

            # Count blockchain IDs
            blockchain_id_count = len([u for u in total_users if u.tourist_id_token])

            return {
                "total_users": len(total_users),
                "by_role": {
                    "admin": admin_count,
                    "tourist": tourist_count,
                    "guide": guide_count,
                    "super_admin": super_admin_count,
                },
                "by_verification": {
                    "verified": verified_count,
                    "unverified": unverified_count,
                },
                "by_status": {
                    "active": active_count,
                    "inactive": inactive_count,
                },
                "blockchain_ids_issued": blockchain_id_count,
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user statistics: {str(e)}",
            )

    @staticmethod
    async def update_user_status(
        db: Session, user_id: int, is_active: bool, admin_id: int
    ) -> UserResponse:
        """Update user active status"""
        try:
            statement = select(User).where(User.id == user_id)
            user = db.exec(statement).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            user.is_active = is_active
            db.add(user)
            db.commit()
            db.refresh(user)

            return UserResponse.model_validate(user)

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update user status: {str(e)}",
            )
