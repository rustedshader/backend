"""add_test_coordinates_table

Revision ID: 319d120eecc2
Revises: 2a44af28e726
Create Date: 2025-09-11 03:48:36.557984

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "319d120eecc2"
down_revision: Union[str, Sequence[str], None] = "2a44af28e726"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create test_coordinates table
    op.create_table(
        "test_coordinates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop test_coordinates table
    op.drop_table("test_coordinates")
