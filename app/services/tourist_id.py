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

    def reissue_tourist_id(
        self, user: User, db: Session, validity_seconds: int = 365 * 24 * 3600
    ) -> Optional[tuple[int, str]]:
        """Reissue a tourist ID for a user (useful for renewals)."""
        try:
            # Create KYC hash from user data
            kyc_data = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "country_code": user.country_code,
                "aadhar_hash": user.aadhar_number_hash,
                "passport_hash": user.passport_number_hash,
            }
            import json

            kyc_json = json.dumps(kyc_data, sort_keys=True)
            kyc_hash = self.blockchain_client.bytes32_from_text(kyc_json)

            # Create a basic itinerary hash (can be updated later)
            basic_itinerary = f"reissued_itinerary_for_{user.email}"
            itinerary_hash = self.blockchain_client.bytes32_from_text(basic_itinerary)

            # Issue new tourist ID
            token_id, receipt = self.blockchain_client.issue_id(
                tourist=user.blockchain_address,
                kyc_hash_hex32=kyc_hash,
                itinerary_hash_hex32=itinerary_hash,
                validity_seconds=validity_seconds,
            )

            # Update user record
            user.tourist_id_token = token_id
            user.tourist_id_transaction_hash = receipt.transactionHash.hex()
            db.add(user)
            db.commit()

            return token_id, receipt.transactionHash.hex()

        except Exception as e:
            print(f"Error reissuing tourist ID: {e}")
            db.rollback()
            return None
