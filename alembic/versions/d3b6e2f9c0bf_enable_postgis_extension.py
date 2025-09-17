"""Enable PostGIS extension

Revision ID: d3b6e2f9c0bf
Revises: aea640aeae73
Create Date: 2025-09-18 03:14:25.538553

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d3b6e2f9c0bf"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")


def downgrade() -> None:
    """Downgrade schema."""
    # Disable PostGIS extension
    op.execute("DROP EXTENSION IF EXISTS postgis CASCADE;")
