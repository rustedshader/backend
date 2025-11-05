"""add_cascade_delete_for_itineraries

Revision ID: c416ece0ee26
Revises: 5309dd9a2417
Create Date: 2025-11-05 16:35:41.021169

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c416ece0ee26"
down_revision: Union[str, Sequence[str], None] = "5309dd9a2417"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add CASCADE delete constraints for itinerary-related foreign keys."""

    # Drop existing foreign key constraints and recreate with CASCADE

    # 1. itinerary_days.itinerary_id
    op.drop_constraint(
        "itinerary_days_itinerary_id_fkey", "itinerary_days", type_="foreignkey"
    )
    op.create_foreign_key(
        "itinerary_days_itinerary_id_fkey",
        "itinerary_days",
        "itineraries",
        ["itinerary_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 2. trips.itinerary_id
    op.drop_constraint("trips_itinerary_id_fkey", "trips", type_="foreignkey")
    op.create_foreign_key(
        "trips_itinerary_id_fkey",
        "trips",
        "itineraries",
        ["itinerary_id"],
        ["id"],
        ondelete="RESTRICT",  # We want to prevent deletion if there are active trips
    )

    # 3. blockchain_applications.itinerary_id
    op.drop_constraint(
        "blockchain_applications_itinerary_id_fkey",
        "blockchain_applications",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "blockchain_applications_itinerary_id_fkey",
        "blockchain_applications",
        "itineraries",
        ["itinerary_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. blockchain_ids.application_id (cascade when application is deleted)
    op.drop_constraint(
        "blockchain_ids_application_id_fkey", "blockchain_ids", type_="foreignkey"
    )
    op.create_foreign_key(
        "blockchain_ids_application_id_fkey",
        "blockchain_ids",
        "blockchain_applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Remove CASCADE delete constraints and restore original constraints."""

    # Restore original foreign key constraints without CASCADE

    # 1. itinerary_days.itinerary_id
    op.drop_constraint(
        "itinerary_days_itinerary_id_fkey", "itinerary_days", type_="foreignkey"
    )
    op.create_foreign_key(
        "itinerary_days_itinerary_id_fkey",
        "itinerary_days",
        "itineraries",
        ["itinerary_id"],
        ["id"],
    )

    # 2. trips.itinerary_id
    op.drop_constraint("trips_itinerary_id_fkey", "trips", type_="foreignkey")
    op.create_foreign_key(
        "trips_itinerary_id_fkey", "trips", "itineraries", ["itinerary_id"], ["id"]
    )

    # 3. blockchain_applications.itinerary_id
    op.drop_constraint(
        "blockchain_applications_itinerary_id_fkey",
        "blockchain_applications",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "blockchain_applications_itinerary_id_fkey",
        "blockchain_applications",
        "itineraries",
        ["itinerary_id"],
        ["id"],
    )

    # 4. blockchain_ids.application_id
    op.drop_constraint(
        "blockchain_ids_application_id_fkey", "blockchain_ids", type_="foreignkey"
    )
    op.create_foreign_key(
        "blockchain_ids_application_id_fkey",
        "blockchain_ids",
        "blockchain_applications",
        ["application_id"],
        ["id"],
    )
