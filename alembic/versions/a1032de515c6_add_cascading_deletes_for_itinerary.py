"""add_cascading_deletes_for_itinerary

Revision ID: a1032de515c6
Revises: 9a02993f4a0c
Create Date: 2025-09-09 20:38:10.689006

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1032de515c6"
down_revision: Union[str, Sequence[str], None] = "9a02993f4a0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop existing foreign key constraints and recreate with CASCADE

    # Drop existing foreign key constraints
    op.drop_constraint(
        "itinerary_days_itinerary_id_fkey", "itinerary_days", type_="foreignkey"
    )
    op.drop_constraint("trips_itinerary_id_fkey", "trips", type_="foreignkey")

    # Recreate foreign key constraints with CASCADE delete
    op.create_foreign_key(
        "itinerary_days_itinerary_id_fkey",
        "itinerary_days",
        "itineraries",
        ["itinerary_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        "trips_itinerary_id_fkey",
        "trips",
        "itineraries",
        ["itinerary_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop CASCADE foreign key constraints and recreate without CASCADE

    op.drop_constraint(
        "itinerary_days_itinerary_id_fkey", "itinerary_days", type_="foreignkey"
    )
    op.drop_constraint("trips_itinerary_id_fkey", "trips", type_="foreignkey")

    # Recreate foreign key constraints without CASCADE
    op.create_foreign_key(
        "itinerary_days_itinerary_id_fkey",
        "itinerary_days",
        "itineraries",
        ["itinerary_id"],
        ["id"],
    )

    op.create_foreign_key(
        "trips_itinerary_id_fkey", "trips", "itineraries", ["itinerary_id"], ["id"]
    )
