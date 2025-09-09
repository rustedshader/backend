"""remove_difficulty_level_from_places

Revision ID: 24cbbeba86db
Revises: e2d378d4bd9f
Create Date: 2025-09-09 20:14:47.912243

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "24cbbeba86db"
down_revision: Union[str, Sequence[str], None] = "e2d378d4bd9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the difficulty_level index if it exists
    try:
        op.drop_index("ix_places_difficulty_level", table_name="places")
    except Exception:
        pass  # Index might not exist

    # Drop the difficulty_level column
    op.drop_column("places", "difficulty_level")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the difficulty_level column
    op.add_column(
        "places",
        sa.Column(
            "difficulty_level",
            sa.Enum(
                "EASY",
                "MODERATE",
                "DIFFICULT",
                "EXTREME",
                "NOT_APPLICABLE",
                name="difficultylevelenum",
            ),
            nullable=False,
            server_default="NOT_APPLICABLE",
        ),
    )

    # Recreate the index
    op.create_index(
        "ix_places_difficulty_level", "places", ["difficulty_level"], unique=False
    )
