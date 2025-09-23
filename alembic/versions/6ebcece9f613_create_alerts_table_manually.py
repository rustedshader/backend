"""create_alerts_table_manually

Revision ID: 6ebcece9f613
Revises: 480ca0bdc4b0
Create Date: 2025-09-23 21:52:21.784650

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6ebcece9f613"
down_revision: Union[str, Sequence[str], None] = "480ca0bdc4b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enums if they don't exist using DO blocks
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alerttypeenum') THEN
                CREATE TYPE alerttypeenum AS ENUM ('EMERGENCY', 'HELP_NEEDED', 'SAFETY_CONCERN', 'LOST', 'MEDICAL', 'ACCIDENT');
            END IF;
        END
        $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alertstatusenum') THEN
                CREATE TYPE alertstatusenum AS ENUM ('ACTIVE', 'RESOLVED');
            END IF;
        END
        $$;
    """)

    # Create alerts table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            message VARCHAR(500) NOT NULL,
            alert_type alerttypeenum NOT NULL,
            status alertstatusenum NOT NULL DEFAULT 'ACTIVE',
            location GEOMETRY(POINT, 4326) NOT NULL,
            created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            resolved_by INTEGER REFERENCES users(id),
            resolved_at TIMESTAMP WITH TIME ZONE
        )
    """)

    # Create indexes if they don't exist
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_id ON alerts (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_alert_type ON alerts (alert_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts (status)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_alerts_location ON alerts USING GIST (location)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_created_by ON alerts (created_by)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_created_at ON alerts (created_at)")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_alerts_created_at")
    op.execute("DROP INDEX IF EXISTS ix_alerts_created_by")
    op.execute("DROP INDEX IF EXISTS ix_alerts_location")
    op.execute("DROP INDEX IF EXISTS ix_alerts_status")
    op.execute("DROP INDEX IF EXISTS ix_alerts_alert_type")
    op.execute("DROP INDEX IF EXISTS ix_alerts_id")

    # Drop table and enums
    op.execute("DROP TABLE IF EXISTS alerts")
    op.execute("DROP TYPE IF EXISTS alertstatusenum")
    op.execute("DROP TYPE IF EXISTS alerttypeenum")
