"""ensure_alerts_table_indexes

Revision ID: 2a44af28e726
Revises: add_geofencing_tables
Create Date: 2025-09-10 03:08:35.154626

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2a44af28e726"
down_revision: Union[str, Sequence[str], None] = "add_geofencing_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to ensure alerts table and indexes exist."""

    # Create enum types if they don't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alerttypeenum AS ENUM ('DEVIATION', 'EMERGENCY', 'WEATHER', 'OTHER');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alertstatusenum AS ENUM ('NEW', 'ACKNOWLEDGED', 'RESOLVED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create alerts table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            trip_id INTEGER NOT NULL REFERENCES trips(id),
            timestamp INTEGER NOT NULL,
            alert_type alerttypeenum NOT NULL,
            description VARCHAR,
            location GEOMETRY(POINT, 4326),
            status alertstatusenum NOT NULL DEFAULT 'NEW'
        )
    """)

    # Create indexes if they don't exist
    op.execute("CREATE INDEX IF NOT EXISTS idx_alerts_trip_id ON alerts(trip_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_alerts_location ON alerts USING GIST(location)"
    )

    # Create index for emergency alerts (frequently queried)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_alerts_emergency ON alerts(alert_type, status) WHERE alert_type = 'EMERGENCY'"
    )

    # Create composite index for trip alerts with status filtering
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_alerts_trip_status ON alerts(trip_id, status, timestamp DESC)"
    )


def downgrade() -> None:
    """Downgrade schema - remove indexes and table."""

    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_alerts_trip_status")
    op.execute("DROP INDEX IF EXISTS idx_alerts_emergency")
    op.execute("DROP INDEX IF EXISTS idx_alerts_location")
    op.execute("DROP INDEX IF EXISTS idx_alerts_status")
    op.execute("DROP INDEX IF EXISTS idx_alerts_type")
    op.execute("DROP INDEX IF EXISTS idx_alerts_timestamp")
    op.execute("DROP INDEX IF EXISTS idx_alerts_trip_id")

    # Drop table
    op.execute("DROP TABLE IF EXISTS alerts")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS alertstatusenum")
    op.execute("DROP TYPE IF EXISTS alerttypeenum")
