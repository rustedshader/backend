"""add_missing_itinerary_columns

Revision ID: fe1096ef11b9
Revises: dae22fdf0f44
Create Date: 2025-09-09 19:52:46.513976

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "fe1096ef11b9"
down_revision: Union[str, Sequence[str], None] = "dae22fdf0f44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type if it doesn't exist
    conn = op.get_bind()

    # Check if enum exists
    result = conn.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'itinerarytypeenum'")
    ).fetchone()

    if not result:
        # Create the enum type
        conn.execute(
            sa.text(
                "CREATE TYPE itinerarytypeenum AS ENUM ('TREK', 'CITY_TOUR', 'MIXED')"
            )
        )

    # Add missing columns to itineraries table
    op.add_column(
        "itineraries",
        sa.Column(
            "itinerary_type",
            sa.Enum("TREK", "CITY_TOUR", "MIXED", name="itinerarytypeenum"),
            nullable=True,
        ),
    )
    op.add_column(
        "itineraries", sa.Column("primary_place_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "itineraries",
        sa.Column(
            "destination_city", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.add_column(
        "itineraries",
        sa.Column(
            "destination_state", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.add_column(
        "itineraries",
        sa.Column(
            "destination_country", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )

    # Add indexes
    op.create_index(
        op.f("ix_itineraries_destination_city"),
        "itineraries",
        ["destination_city"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itineraries_destination_country"),
        "itineraries",
        ["destination_country"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itineraries_destination_state"),
        "itineraries",
        ["destination_state"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itineraries_itinerary_type"),
        "itineraries",
        ["itinerary_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itineraries_primary_place_id"),
        "itineraries",
        ["primary_place_id"],
        unique=False,
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_itineraries_primary_place_id",
        "itineraries",
        "places",
        ["primary_place_id"],
        ["id"],
    )

    # Add missing columns to itinerary_days table
    op.add_column(
        "itinerary_days",
        sa.Column(
            "day_type",
            sa.Enum("TREK_DAY", "PLACE_VISIT_DAY", name="daytypeenum"),
            nullable=True,
        ),
    )
    op.add_column("itinerary_days", sa.Column("trek_id", sa.Integer(), nullable=True))
    op.add_column(
        "itinerary_days", sa.Column("primary_place_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "itinerary_days", sa.Column("accommodation_latitude", sa.Float(), nullable=True)
    )
    op.add_column(
        "itinerary_days",
        sa.Column("accommodation_longitude", sa.Float(), nullable=True),
    )

    # Add indexes
    op.create_index(
        op.f("ix_itinerary_days_day_type"), "itinerary_days", ["day_type"], unique=False
    )
    op.create_index(
        op.f("ix_itinerary_days_primary_place_id"),
        "itinerary_days",
        ["primary_place_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_itinerary_days_trek_id"), "itinerary_days", ["trek_id"], unique=False
    )

    # Add foreign key constraints
    op.create_foreign_key(
        "fk_itinerary_days_primary_place_id",
        "itinerary_days",
        "places",
        ["primary_place_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_itinerary_days_trek_id", "itinerary_days", "treks", ["trek_id"], ["id"]
    )

    # Remove submitted_at column as it's no longer needed (auto-approval system)
    op.drop_column("itineraries", "submitted_at")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back submitted_at column
    op.add_column("itineraries", sa.Column("submitted_at", sa.INTEGER(), nullable=True))

    # Drop foreign key constraints
    op.drop_constraint(
        "fk_itinerary_days_trek_id", "itinerary_days", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_itinerary_days_primary_place_id", "itinerary_days", type_="foreignkey"
    )

    # Drop indexes
    op.drop_index(op.f("ix_itinerary_days_trek_id"), table_name="itinerary_days")
    op.drop_index(
        op.f("ix_itinerary_days_primary_place_id"), table_name="itinerary_days"
    )
    op.drop_index(op.f("ix_itinerary_days_day_type"), table_name="itinerary_days")

    # Drop columns from itinerary_days
    op.drop_column("itinerary_days", "accommodation_longitude")
    op.drop_column("itinerary_days", "accommodation_latitude")
    op.drop_column("itinerary_days", "primary_place_id")
    op.drop_column("itinerary_days", "trek_id")
    op.drop_column("itinerary_days", "day_type")

    # Drop foreign key constraint
    op.drop_constraint(
        "fk_itineraries_primary_place_id", "itineraries", type_="foreignkey"
    )

    # Drop indexes
    op.drop_index(op.f("ix_itineraries_primary_place_id"), table_name="itineraries")
    op.drop_index(op.f("ix_itineraries_itinerary_type"), table_name="itineraries")
    op.drop_index(op.f("ix_itineraries_destination_state"), table_name="itineraries")
    op.drop_index(op.f("ix_itineraries_destination_country"), table_name="itineraries")
    op.drop_index(op.f("ix_itineraries_destination_city"), table_name="itineraries")

    # Drop columns from itineraries
    op.drop_column("itineraries", "destination_country")
    op.drop_column("itineraries", "destination_state")
    op.drop_column("itineraries", "destination_city")
    op.drop_column("itineraries", "primary_place_id")
    op.drop_column("itineraries", "itinerary_type")
