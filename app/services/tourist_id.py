from sqlmodel import Session
from app.models.database.user import User
from app.utils.blockchain import TouristIDClient, TouristInfo
from typing import Optional


class TouristIDService:
    def __init__(self):
        self.blockchain_client = TouristIDClient()

    def get_tourist_id_info(self, user: User) -> Optional[TouristInfo]:
        """Get tourist ID information from the blockchain for a user."""
        if not user.tourist_id_token:
            return None

        try:
            return self.blockchain_client.get_tourist_info(user.tourist_id_token)
        except Exception as e:
            print(f"Error retrieving tourist ID info: {e}")
            return None

    def is_tourist_id_valid(self, user: User) -> bool:
        """Check if the user's tourist ID is valid on the blockchain."""
        if not user.tourist_id_token:
            return False

        try:
            return self.blockchain_client.is_valid(user.tourist_id_token)
        except Exception as e:
            print(f"Error checking tourist ID validity: {e}")
            return False

    def revoke_tourist_id(self, user: User, db: Session) -> bool:
        """Revoke a user's tourist ID on the blockchain."""
        if not user.tourist_id_token:
            return False

        try:
            receipt = self.blockchain_client.revoke_id(user.tourist_id_token)
            # Update user record to reflect revocation
            # Note: The blockchain contract marks it as revoked, but we could also update our DB
            return receipt.status == 1
        except Exception as e:
            print(f"Error revoking tourist ID: {e}")
            return False

    # Note: Tourist ID issuance/reissuance is now handled exclusively by admins
    # via the admin endpoints at entry points for security compliance
