"""Add geofencing tables

Revision ID: add_geofencing_tables
Revises: 779005bb52a8
Create Date: 2025-09-10 12:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = "add_geofencing_tables"
down_revision: Union[str, Sequence[str], None] = "779005bb52a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add geofencing tables."""

    # Create enums for restricted areas
    restricted_area_status_enum = ENUM(
        "ACTIVE",
        "INACTIVE",
        "TEMPORARILY_DISABLED",
        name="restrictedareastatusenum",
        create_type=False,
    )
    restricted_area_status_enum.create(op.get_bind(), checkfirst=True)

    restricted_area_type_enum = ENUM(
        "RESTRICTED_ZONE",
        "DANGER_ZONE",
        "PRIVATE_PROPERTY",
        "PROTECTED_AREA",
        "MILITARY_ZONE",
        "SEASONAL_CLOSURE",
        name="restrictedareataypeenum",
        create_type=False,
    )
    restricted_area_type_enum.create(op.get_bind(), checkfirst=True)

    # Create restricted_areas table
    op.create_table(
        "restricted_areas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("area_type", restricted_area_type_enum, nullable=False),
        sa.Column("status", restricted_area_status_enum, nullable=False),
        sa.Column(
            "boundary", sa.Text(), nullable=True
        ),  # Will be updated to PostGIS geometry
        sa.Column("created_by_admin_id", sa.Integer(), nullable=False),
        sa.Column("severity_level", sa.Integer(), nullable=False),
        sa.Column(
            "restriction_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("contact_info", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("send_warning_notification", sa.Boolean(), nullable=False),
        sa.Column("auto_alert_authorities", sa.Boolean(), nullable=False),
        sa.Column("buffer_distance_meters", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add PostGIS geometry column for boundary
    op.execute("""
        ALTER TABLE restricted_areas 
        DROP COLUMN boundary,
        ADD COLUMN boundary geometry(POLYGON,4326)
    """)

    # Create indexes
    op.create_index(
        op.f("ix_restricted_areas_id"), "restricted_areas", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_restricted_areas_name"), "restricted_areas", ["name"], unique=False
    )
    op.create_index(
        op.f("ix_restricted_areas_area_type"),
        "restricted_areas",
        ["area_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_restricted_areas_status"), "restricted_areas", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_restricted_areas_created_by_admin_id"),
        "restricted_areas",
        ["created_by_admin_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_restricted_areas_created_at"),
        "restricted_areas",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_restricted_areas_updated_at"),
        "restricted_areas",
        ["updated_at"],
        unique=False,
    )

    # Create spatial index for boundary geometry
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_restricted_areas_boundary ON restricted_areas USING gist (boundary)"
    )

    # Create geofence_violations table
    op.create_table(
        "geofence_violations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("restricted_area_id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=True),
        sa.Column("violation_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "violation_location", sa.Text(), nullable=True
        ),  # Will be updated to PostGIS geometry
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), nullable=False),
        sa.Column("authorities_alerted", sa.Boolean(), nullable=False),
        sa.Column("severity_score", sa.Integer(), nullable=False),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("resolved_by_admin_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["restricted_area_id"], ["restricted_areas.id"]),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"]),
        sa.ForeignKeyConstraint(["resolved_by_admin_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add PostGIS geometry column for violation location
    op.execute("""
        ALTER TABLE geofence_violations 
        DROP COLUMN violation_location,
        ADD COLUMN violation_location geometry(POINT,4326)
    """)

    # Create indexes for geofence_violations
    op.create_index(
        op.f("ix_geofence_violations_id"), "geofence_violations", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_geofence_violations_user_id"),
        "geofence_violations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_geofence_violations_restricted_area_id"),
        "geofence_violations",
        ["restricted_area_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_geofence_violations_trip_id"),
        "geofence_violations",
        ["trip_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_geofence_violations_violation_type"),
        "geofence_violations",
        ["violation_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_geofence_violations_detected_at"),
        "geofence_violations",
        ["detected_at"],
        unique=False,
    )

    # Create spatial index for violation location
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_geofence_violations_location ON geofence_violations USING gist (violation_location)"
    )


def downgrade() -> None:
    """Remove geofencing tables."""

    # Drop tables
    op.drop_table("geofence_violations")
    op.drop_table("restricted_areas")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS restrictedareastatusenum")
    op.execute("DROP TYPE IF EXISTS restrictedareataypeenum")
