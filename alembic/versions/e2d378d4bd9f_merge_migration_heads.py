"""merge_migration_heads

Revision ID: e2d378d4bd9f
Revises: 4ac136f61ee6, fe1096ef11b9
Create Date: 2025-09-09 20:14:39.896263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2d378d4bd9f'
down_revision: Union[str, Sequence[str], None] = ('4ac136f61ee6', 'fe1096ef11b9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
