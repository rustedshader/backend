import json
import datetime
from datetime import timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import Session, select, or_
from sqlalchemy import func
from web3 import Web3

from app.models.database.blockchain_id import (
    BlockchainApplication,
    BlockchainID,
    BlockchainApplicationStatusEnum,
)
from app.models.schemas.blockchain_id import (
    BlockchainApplicationRequest,
    BlockchainIDIssueRequest,
    ApplicationSearchQuery,
    BlockchainStatistics,
)
from app.models.database.user import User
from app.models.database.trips import Trips, TripStatusEnum
from app.models.database.location_sharing import LocationSharing
from app.utils.blockchain import TouristIDClient


# Tourist applies for blockchain ID
async def apply_for_blockchain_id(
    application_data: BlockchainApplicationRequest, user_id: int, db: Session
) -> Dict[str, Any]:
    """Tourist applies for blockchain ID using their itinerary ID"""
    try:
        # Check if user already has a pending/issued application
        existing_app = db.exec(
            select(BlockchainApplication).where(
                BlockchainApplication.user_id == user_id,
                BlockchainApplication.status.in_(
                    [
                        BlockchainApplicationStatusEnum.PENDING,
                        BlockchainApplicationStatusEnum.ISSUED,
                    ]
                ),
            )
        ).first()

        if existing_app:
            raise ValueError(
                f"You already have an application with status: {existing_app.status}"
            )

        # Verify itinerary exists and belongs to user (you'll need to add this check based on your itinerary model)
        # itinerary = db.exec(select(Itinerary).where(Itinerary.id == application_data.itinerary_id, Itinerary.user_id == user_id)).first()
        # if not itinerary:
        #     raise ValueError("Itinerary not found or doesn't belong to you")

        # Generate application number
        app_number = f"BID{datetime.datetime.utcnow().strftime('%Y%m%d')}{user_id:06d}"

        # Create application
        application = BlockchainApplication(
            application_number=app_number,
            user_id=user_id,
            itinerary_id=application_data.itinerary_id,
            status=BlockchainApplicationStatusEnum.PENDING,
            applied_at=datetime.datetime.utcnow(),
        )

        db.add(application)
        db.commit()
        db.refresh(application)

        return {
            "application_id": application.id,
            "application_number": app_number,
            "status": application.status,
            "applied_at": application.applied_at,
            "message": "Application submitted successfully! You will be notified once it's processed by the admin.",
        }

    except Exception as e:
        db.rollback()
        raise e


# Admin searches applications
async def search_applications(
    search_query: ApplicationSearchQuery,
    page: int = 1,
    page_size: int = 20,
    db: Session = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """Search blockchain applications for admin management"""
    try:
        statement = select(BlockchainApplication)

        # Universal search across application number and user info
        if search_query.query:
            # You'll need to join with User table to search user info
            universal_filter = or_(
                BlockchainApplication.application_number.ilike(
                    f"%{search_query.query}%"
                ),
                # Add more search fields as needed
            )
            statement = statement.where(universal_filter)

        # Specific filters
        if search_query.status:
            statement = statement.where(
                BlockchainApplication.status == search_query.status
            )

        if search_query.date_from:
            statement = statement.where(
                BlockchainApplication.applied_at >= search_query.date_from
            )

        if search_query.date_to:
            statement = statement.where(
                BlockchainApplication.applied_at <= search_query.date_to
            )

        # Get total count
        total_count = len(db.exec(statement).all())

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

        applications = db.exec(statement).all()

        # Format response (you'll need to add user info from User table)
        result = []
        for app in applications:
            app_dict = app.model_dump()
            # Add user info here:
            # user = db.exec(select(User).where(User.id == app.user_id)).first()
            # app_dict["user_name"] = user.name if user else "Unknown"
            # app_dict["user_email"] = user.email if user else "Unknown"
            result.append(app_dict)

        return result, total_count

    except Exception as e:
        raise e


# Get all applications for admin
async def get_all_applications(
    page: int = 1,
    page_size: int = 20,
    status: Optional[BlockchainApplicationStatusEnum] = None,
    db: Session = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """Get all blockchain applications with optional status filter"""
    try:
        statement = select(BlockchainApplication)

        if status:
            statement = statement.where(BlockchainApplication.status == status)

        # Order by newest first
        statement = statement.order_by(BlockchainApplication.applied_at.desc())

        # Get total count
        total_count = len(db.exec(statement).all())

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

        applications = db.exec(statement).all()

        # Format response (you'll need to add user info from User table)
        result = []
        for app in applications:
            app_dict = app.model_dump()
            # Add user info here:
            # user = db.exec(select(User).where(User.id == app.user_id)).first()
            # app_dict["user_name"] = user.name if user else "Unknown"
            # app_dict["user_email"] = user.email if user else "Unknown"
            result.append(app_dict)

        return result, total_count

    except Exception as e:
        raise e


# Admin rejects application
async def reject_application(
    application_id: int,
    admin_id: int,
    admin_notes: str,
    db: Session = None,
) -> Dict[str, Any]:
    """Admin rejects a blockchain ID application"""
    try:
        # Get application
        application = db.exec(
            select(BlockchainApplication).where(
                BlockchainApplication.id == application_id
            )
        ).first()

        if not application:
            raise ValueError("Application not found")

        if application.status != BlockchainApplicationStatusEnum.PENDING:
            raise ValueError(
                f"Application is not pending. Current status: {application.status}"
            )

        # Update application
        application.status = BlockchainApplicationStatusEnum.REJECTED
        application.rejected_at = datetime.datetime.utcnow()
        application.processed_by_admin = admin_id
        application.admin_notes = admin_notes

        db.add(application)
        db.commit()
        db.refresh(application)

        return {
            "application_id": application.id,
            "status": application.status,
            "rejected_at": application.rejected_at,
            "reason": admin_notes,
            "message": "Application rejected.",
        }

    except Exception as e:
        db.rollback()
        raise e


# Issue blockchain ID (directly from pending)
async def issue_blockchain_id(
    issue_request: BlockchainIDIssueRequest, admin_id: int, db: Session
) -> Dict[str, Any]:
    """Admin directly issues REAL blockchain ID from pending application with actual blockchain transaction"""
    try:
        # Get application
        application = db.exec(
            select(BlockchainApplication).where(
                BlockchainApplication.id == issue_request.application_id
            )
        ).first()

        if not application:
            raise ValueError("Application not found")

        if application.status != BlockchainApplicationStatusEnum.PENDING:
            raise ValueError(
                f"Application not pending. Current status: {application.status}"
            )

        # Check if blockchain ID already issued
        existing_id = db.exec(
            select(BlockchainID).where(BlockchainID.application_id == application.id)
        ).first()

        if existing_id:
            raise ValueError("Blockchain ID already issued for this application")

        # Get user details
        user = db.exec(select(User).where(User.id == application.user_id)).first()
        if not user:
            raise ValueError("User not found")

        # Get itinerary data for blockchain
        from app.services import itinerary as itinerary_service

        itinerary_data = await itinerary_service.get_itinerary_for_blockchain(
            itinerary_id=application.itinerary_id, db=db
        )

        if not itinerary_data or itinerary_data.strip() == "":
            raise ValueError(
                f"Invalid itinerary data for itinerary_id {application.itinerary_id}"
            )

        # Create blockchain account for the user
        web3 = Web3()
        userblockchain_account = web3.eth.account.create()
        userblockchain_account_address = userblockchain_account.address

        # Validate blockchain address
        if not userblockchain_account_address or not web3.is_address(
            userblockchain_account_address
        ):
            raise ValueError("Failed to generate valid blockchain address")

        # Initialize blockchain client and issue tourist ID
        from app.core.config import settings

        if (
            not settings.owner_address
            or not settings.private_key
            or not settings.contract_address
        ):
            raise ValueError(
                "Blockchain configuration missing. Please set OWNER_ADDRESS, PRIVATE_KEY, and CONTRACT_ADDRESS environment variables."
            )

        blockchain_client = TouristIDClient()

        # Create KYC hash from user data - handle None values
        kyc_data = {
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "email": user.email or "",
            "country_code": user.country_code or "",
            "aadhar_hash": user.aadhar_number_hash or "",
            "passport_hash": user.passport_number_hash or "",
            "verified_by_official": admin_id,
        }
        kyc_json = json.dumps(kyc_data, sort_keys=True)
        if not kyc_json or kyc_json.strip() == "":
            raise ValueError("Invalid KYC data - cannot generate hash")

        kyc_hash = blockchain_client.bytes32_from_text(kyc_json)
        if not kyc_hash:
            raise ValueError("Failed to generate KYC hash")

        # Create itinerary hash
        itinerary_hash = blockchain_client.bytes32_from_text(itinerary_data)
        if not itinerary_hash:
            raise ValueError("Failed to generate itinerary hash")

        # Issue tourist ID with specified validity
        validity_seconds = issue_request.validity_days * 24 * 3600

        # REAL BLOCKCHAIN TRANSACTION
        token_id, receipt = blockchain_client.issue_id(
            tourist=userblockchain_account_address,
            kyc_hash_hex32=kyc_hash,
            itinerary_hash_hex32=itinerary_hash,
            validity_seconds=validity_seconds,
        )

        # Calculate expiry date
        expiry_date = datetime.datetime.utcnow() + timedelta(
            days=issue_request.validity_days
        )

        # Create blockchain ID record with REAL blockchain data
        blockchain_id = BlockchainID(
            blockchain_id=str(token_id)
            if token_id != -1
            else f"BTID{datetime.datetime.utcnow().strftime('%Y%m%d')}{application.id:08d}",
            application_id=application.id,
            user_id=application.user_id,
            blockchain_hash=receipt["transactionHash"].hex(),
            smart_contract_address=settings.contract_address,
            transaction_hash=receipt["transactionHash"].hex(),
            issued_date=datetime.datetime.utcnow(),
            expiry_date=expiry_date,
            qr_code_data=json.dumps(
                {
                    "blockchain_id": str(token_id),
                    "user_id": application.user_id,
                    "blockchain_address": userblockchain_account_address,
                    "transaction_hash": receipt["transactionHash"].hex(),
                    "issued_date": datetime.datetime.utcnow().isoformat(),
                    "expiry_date": expiry_date.isoformat(),
                }
            ),
        )

        # Update user with blockchain information and automatically verify KYC
        user.blockchain_address = userblockchain_account_address
        user.is_kyc_verified = (
            True  # Automatically verify KYC when blockchain ID is issued
        )

        # Create a new trip for this tourist ID
        new_trip = Trips(
            user_id=application.user_id,
            itinerary_id=application.itinerary_id,
            status=TripStatusEnum.ONGOING,  # Auto-start the trip when blockchain ID is issued
            tourist_id=str(token_id) if token_id != -1 else None,
            blockchain_transaction_hash=receipt["transactionHash"].hex(),
        )

        # Create location sharing code for the new trip
        location_sharing = LocationSharing(
            trip_id=new_trip.id,  # Will be set after commit
            user_id=application.user_id,
            share_code=LocationSharing.generate_share_code(),
            is_active=True,
            expires_at=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=issue_request.validity_days),
        )

        # Update application status directly to ISSUED
        application.status = BlockchainApplicationStatusEnum.ISSUED
        application.issued_at = datetime.datetime.utcnow()
        application.processed_by_admin = admin_id
        application.admin_notes = issue_request.admin_notes

        # Save all changes
        db.add(blockchain_id)
        db.add(user)
        db.add(new_trip)
        db.add(application)
        db.commit()
        db.refresh(blockchain_id)
        db.refresh(new_trip)

        # Update location sharing with trip_id
        location_sharing.trip_id = new_trip.id
        db.add(location_sharing)
        db.commit()
        db.refresh(location_sharing)

        return {
            "success": True,
            "message": "REAL Blockchain Tourist ID issued successfully with blockchain transaction!",
            "blockchain_id": str(token_id)
            if token_id != -1
            else blockchain_id.blockchain_id,
            "application_id": application.id,
            "tourist_id_token": token_id,
            "trip_id": new_trip.id,
            "blockchain_address": userblockchain_account_address,
            "transaction_hash": receipt["transactionHash"].hex(),
            "contract_address": settings.contract_address,
            "issued_date": blockchain_id.issued_date,
            "expiry_date": blockchain_id.expiry_date,
            "qr_code_data": blockchain_id.qr_code_data,
            "share_code": location_sharing.share_code,
        }

    except Exception as e:
        db.rollback()
        raise e


def _generate_blockchain_hash(application: BlockchainApplication) -> str:
    """Generate blockchain hash for the application"""
    import hashlib

    data = (
        f"{application.application_number}{application.user_id}{application.applied_at}"
    )
    return hashlib.sha256(data.encode()).hexdigest()


# Get statistics for dashboard
async def get_blockchain_statistics(db: Session) -> BlockchainStatistics:
    """Get statistics for admin dashboard"""
    try:
        today = datetime.datetime.utcnow().date()

        total_applications = db.exec(select(func.count(BlockchainApplication.id))).one()
        pending_applications = db.exec(
            select(func.count(BlockchainApplication.id)).where(
                BlockchainApplication.status == BlockchainApplicationStatusEnum.PENDING
            )
        ).one()
        issued_ids = db.exec(
            select(func.count(BlockchainApplication.id)).where(
                BlockchainApplication.status == BlockchainApplicationStatusEnum.ISSUED
            )
        ).one()
        rejected_applications = db.exec(
            select(func.count(BlockchainApplication.id)).where(
                BlockchainApplication.status == BlockchainApplicationStatusEnum.REJECTED
            )
        ).one()
        applications_today = db.exec(
            select(func.count(BlockchainApplication.id)).where(
                func.date(BlockchainApplication.applied_at) == today
            )
        ).one()
        issued_today = db.exec(
            select(func.count(BlockchainApplication.id)).where(
                BlockchainApplication.status == BlockchainApplicationStatusEnum.ISSUED,
                func.date(BlockchainApplication.issued_at) == today,
            )
        ).one()

        return BlockchainStatistics(
            total_applications=total_applications,
            pending_applications=pending_applications,
            issued_ids=issued_ids,
            rejected_applications=rejected_applications,
            applications_today=applications_today,
            issued_today=issued_today,
        )

    except Exception as e:
        raise e
