from sqlmodel import Session, select
from app.models.database.trips import Trips, TripStatusEnum
from app.utils.blockchain import TouristIDClient, TouristInfo
from typing import Optional


class TouristIDService:
    def __init__(self):
        self.blockchain_client = TouristIDClient()

    def get_user_active_trip(self, user_id: int, db: Session) -> Optional[Trips]:
        """Get the user's active trip with tourist ID."""
        return db.exec(
            select(Trips)
            .where(
                Trips.user_id == user_id,
                Trips.status.in_([TripStatusEnum.ONGOING, TripStatusEnum.UPCOMING]),
                Trips.tourist_id.isnot(None),
            )
            .order_by(Trips.created_at.desc())
        ).first()

    def get_tourist_id_info(self, trip: Trips) -> Optional[TouristInfo]:
        """Get tourist ID information from the blockchain for a trip."""
        if not trip.tourist_id:
            return None

        try:
            return self.blockchain_client.get_tourist_info(int(trip.tourist_id))
        except Exception as e:
            print(f"Error retrieving tourist ID info: {e}")
            return None

    def is_tourist_id_valid(self, trip: Trips) -> bool:
        """Check if the trip's tourist ID is valid on the blockchain."""
        if not trip.tourist_id:
            return False

        try:
            return self.blockchain_client.is_valid(int(trip.tourist_id))
        except Exception as e:
            print(f"Error checking tourist ID validity: {e}")
            return False

    def revoke_tourist_id(self, trip: Trips, db: Session) -> bool:
        """Revoke a trip's tourist ID on the blockchain and end the trip."""
        if not trip.tourist_id:
            return False

        try:
            receipt = self.blockchain_client.revoke_id(int(trip.tourist_id))
            # Update trip status to cancelled
            trip.status = TripStatusEnum.CANCELLED
            db.add(trip)
            db.commit()
            return receipt.status == 1
        except Exception as e:
            print(f"Error revoking tourist ID: {e}")
            return False

    # Note: Tourist ID issuance/reissuance is now handled exclusively by admins
    # via the admin endpoints at entry points for security compliance
