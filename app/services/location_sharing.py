"""
Location sharing service for emergency contacts.
"""

import json
import datetime
from typing import List, Dict, Optional, Tuple
from sqlmodel import Session, select

from app.models.database.location_sharing import LocationShareHistory
from app.models.database.itinerary import Itinerary
from app.models.database.trips import Trips
from app.models.database.user import User
from app.models.schemas.location_sharing import (
    ShareLocationRequest,
    ShareLocationWithContactRequest,
    LocationShareResponse,
    EmergencyContactInfo,
)


class LocationSharingService:
    """Service for sharing user locations with emergency contacts."""

    def __init__(self, db: Session):
        self.db = db

    async def share_location_with_emergency_contacts(
        self, user_id: int, request: ShareLocationRequest
    ) -> LocationShareResponse:
        """Share location with all emergency contacts from user's active itinerary."""
        try:
            # Get user information
            user = self.db.exec(select(User).where(User.id == user_id)).first()
            if not user:
                return LocationShareResponse(
                    success=False,
                    message="User not found",
                    shared_with=[],
                    location={},
                    timestamp=int(datetime.datetime.utcnow().timestamp()),
                )

            # Get emergency contacts from active itinerary
            emergency_contacts = await self._get_user_emergency_contacts(user_id)

            if not emergency_contacts:
                return LocationShareResponse(
                    success=False,
                    message="No emergency contacts found in active itinerary",
                    shared_with=[],
                    location={},
                    timestamp=int(datetime.datetime.utcnow().timestamp()),
                )

            # Get trip information if requested
            trip_info = None
            trip_id = None
            if request.include_trip_details:
                trip_info, trip_id = await self._get_current_trip_info(user_id)

            # Create location share record
            share_record = LocationShareHistory(
                user_id=user_id,
                latitude=request.latitude,
                longitude=request.longitude,
                shared_with_contacts=json.dumps(
                    [
                        {
                            "name": contact.name,
                            "phone": contact.phone,
                            "relation": contact.relation,
                        }
                        for contact in emergency_contacts
                    ]
                ),
                message=request.message,
                emergency_level=request.emergency_level,
                trip_id=trip_id,
                trip_info=json.dumps(trip_info) if trip_info else None,
                timestamp=int(datetime.datetime.utcnow().timestamp()),
                share_method="manual",
            )

            self.db.add(share_record)
            self.db.commit()
            self.db.refresh(share_record)

            # Simulate sending notifications (in real implementation, integrate with SMS/email service)
            contact_names = [contact.name for contact in emergency_contacts]

            # Create response
            location_data = {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "user_name": f"{user.first_name} {user.last_name}",
                "user_phone": user.phone_number,
                "message": request.message,
                "emergency_level": request.emergency_level,
                "trip_info": trip_info,
                "google_maps_link": f"https://maps.google.com/?q={request.latitude},{request.longitude}",
            }

            return LocationShareResponse(
                success=True,
                message=f"Location shared with {len(emergency_contacts)} emergency contacts",
                shared_with=contact_names,
                location=location_data,
                timestamp=share_record.timestamp,
                share_id=str(share_record.id),
            )

        except Exception as e:
            self.db.rollback()
            return LocationShareResponse(
                success=False,
                message=f"Failed to share location: {str(e)}",
                shared_with=[],
                location={},
                timestamp=int(datetime.datetime.utcnow().timestamp()),
            )

    async def share_location_with_contact(
        self, user_id: int, request: ShareLocationWithContactRequest
    ) -> LocationShareResponse:
        """Share location with a specific contact."""
        try:
            # Get user information
            user = self.db.exec(select(User).where(User.id == user_id)).first()
            if not user:
                return LocationShareResponse(
                    success=False,
                    message="User not found",
                    shared_with=[],
                    location={},
                    timestamp=int(datetime.datetime.utcnow().timestamp()),
                )

            # Get trip information if requested
            trip_info = None
            trip_id = None
            if request.include_trip_details:
                trip_info, trip_id = await self._get_current_trip_info(user_id)

            # Create contact info
            contact_name = request.contact_name or request.contact_phone
            contacts = [
                {
                    "name": contact_name,
                    "phone": request.contact_phone,
                    "relation": "custom",
                }
            ]

            # Create location share record
            share_record = LocationShareHistory(
                user_id=user_id,
                latitude=request.latitude,
                longitude=request.longitude,
                shared_with_contacts=json.dumps(contacts),
                message=request.message,
                emergency_level=request.emergency_level,
                trip_id=trip_id,
                trip_info=json.dumps(trip_info) if trip_info else None,
                timestamp=int(datetime.datetime.utcnow().timestamp()),
                share_method="manual",
            )

            self.db.add(share_record)
            self.db.commit()
            self.db.refresh(share_record)

            # Create response
            location_data = {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "user_name": f"{user.first_name} {user.last_name}",
                "user_phone": user.phone_number,
                "message": request.message,
                "emergency_level": request.emergency_level,
                "trip_info": trip_info,
                "google_maps_link": f"https://maps.google.com/?q={request.latitude},{request.longitude}",
            }

            return LocationShareResponse(
                success=True,
                message=f"Location shared with {contact_name}",
                shared_with=[contact_name],
                location=location_data,
                timestamp=share_record.timestamp,
                share_id=str(share_record.id),
            )

        except Exception as e:
            self.db.rollback()
            return LocationShareResponse(
                success=False,
                message=f"Failed to share location: {str(e)}",
                shared_with=[],
                location={},
                timestamp=int(datetime.datetime.utcnow().timestamp()),
            )

    async def get_user_location_shares(
        self, user_id: int, limit: int = 50
    ) -> List[Dict]:
        """Get user's location sharing history."""
        try:
            shares = self.db.exec(
                select(LocationShareHistory)
                .where(LocationShareHistory.user_id == user_id)
                .order_by(LocationShareHistory.created_at.desc())
                .limit(limit)
            ).all()

            result = []
            for share in shares:
                shared_contacts = json.loads(share.shared_with_contacts)
                trip_info = json.loads(share.trip_info) if share.trip_info else None

                result.append(
                    {
                        "id": share.id,
                        "latitude": share.latitude,
                        "longitude": share.longitude,
                        "shared_with": [contact["name"] for contact in shared_contacts],
                        "message": share.message,
                        "emergency_level": share.emergency_level,
                        "trip_info": trip_info,
                        "timestamp": share.timestamp,
                        "created_at": share.created_at,
                        "delivery_status": share.delivery_status,
                    }
                )

            return result

        except Exception as e:
            print(f"Error getting location shares: {e}")
            return []

    async def _get_user_emergency_contacts(
        self, user_id: int
    ) -> List[EmergencyContactInfo]:
        """Get emergency contacts from user's active itinerary."""
        try:
            # Get the most recent active itinerary
            itinerary = self.db.exec(
                select(Itinerary)
                .where(Itinerary.user_id == user_id)
                .where(Itinerary.status == "ACTIVE")
                .order_by(Itinerary.created_at.desc())
                .limit(1)
            ).first()

            if not itinerary:
                return []

            return [
                EmergencyContactInfo(
                    name=itinerary.emergency_contact_name,
                    phone=itinerary.emergency_contact_phone,
                    relation=itinerary.emergency_contact_relation,
                )
            ]

        except Exception as e:
            print(f"Error getting emergency contacts: {e}")
            return []

    async def _get_current_trip_info(
        self, user_id: int
    ) -> Tuple[Optional[Dict], Optional[int]]:
        """Get current trip information for context."""
        try:
            # Get active trip
            trip = self.db.exec(
                select(Trips)
                .where(Trips.user_id == user_id)
                .where(Trips.status.in_(["started", "visiting", "returning"]))
                .order_by(Trips.created_at.desc())
                .limit(1)
            ).first()

            if not trip:
                return None, None

            trip_info = {
                "trip_id": trip.id,
                "trip_type": trip.trip_type,
                "status": trip.status,
                "destination": trip.destination_name,
                "hotel": trip.hotel_name,
                "tracking_active": trip.is_tracking_active,
            }

            return trip_info, trip.id

        except Exception as e:
            print(f"Error getting trip info: {e}")
            return None, None

    async def create_emergency_location_share(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        emergency_message: str = "EMERGENCY: Need immediate assistance!",
    ) -> LocationShareResponse:
        """Create an emergency location share with high priority."""
        emergency_request = ShareLocationRequest(
            latitude=latitude,
            longitude=longitude,
            message=emergency_message,
            include_trip_details=True,
            emergency_level="emergency",
        )

        return await self.share_location_with_emergency_contacts(
            user_id, emergency_request
        )
