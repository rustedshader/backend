"""make_trek_id_optional_in_trips

Revision ID: 9a02993f4a0c
Revises: 24cbbeba86db
Create Date: 2025-09-09 20:29:50.709477

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a02993f4a0c"
down_revision: Union[str, Sequence[str], None] = "24cbbeba86db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make trek_id nullable in trips table
    op.alter_column("trips", "trek_id", nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make trek_id non-nullable again (careful: this might fail if there are null values)
    op.alter_column("trips", "trek_id", nullable=False)
