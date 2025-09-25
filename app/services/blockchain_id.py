import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import Session, select, or_
from sqlalchemy import func

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
        app_number = f"BID{datetime.utcnow().strftime('%Y%m%d')}{user_id:06d}"

        # Create application
        application = BlockchainApplication(
            application_number=app_number,
            user_id=user_id,
            itinerary_id=application_data.itinerary_id,
            status=BlockchainApplicationStatusEnum.PENDING,
            applied_at=datetime.utcnow(),
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
        application.rejected_at = datetime.utcnow()
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
    """Admin directly issues blockchain ID from pending application"""
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

        # Generate blockchain ID
        blockchain_id_value = (
            f"BTID{datetime.utcnow().strftime('%Y%m%d')}{application.id:08d}"
        )
        blockchain_hash = _generate_blockchain_hash(application)

        # Calculate expiry date
        expiry_date = datetime.utcnow() + timedelta(days=issue_request.validity_days)

        # Generate QR code data for the blockchain ID
        id_qr_data = {
            "blockchain_id": blockchain_id_value,
            "user_id": application.user_id,
            "issued_date": datetime.utcnow().isoformat(),
            "expiry_date": expiry_date.isoformat(),
        }

        # Create blockchain ID record
        blockchain_id = BlockchainID(
            blockchain_id=blockchain_id_value,
            application_id=application.id,
            user_id=application.user_id,
            blockchain_hash=blockchain_hash,
            issued_date=datetime.utcnow(),
            expiry_date=expiry_date,
            qr_code_data=json.dumps(id_qr_data),
        )

        db.add(blockchain_id)

        # Update application status directly to ISSUED
        application.status = BlockchainApplicationStatusEnum.ISSUED
        application.issued_at = datetime.utcnow()
        application.processed_by_admin = admin_id
        application.admin_notes = issue_request.admin_notes
        db.add(application)

        db.commit()
        db.refresh(blockchain_id)
        db.refresh(application)

        return {
            "blockchain_id": blockchain_id_value,
            "application_id": application.id,
            "issued_date": blockchain_id.issued_date,
            "expiry_date": blockchain_id.expiry_date,
            "qr_code_data": blockchain_id.qr_code_data,
            "message": "Blockchain Tourist ID issued successfully!",
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
        today = datetime.utcnow().date()

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
