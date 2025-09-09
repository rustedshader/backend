"""add_trek_path_table

Revision ID: 7732b2435053
Revises: 6cb22c2bfde4
Create Date: 2025-09-10 00:09:11.871198

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = "7732b2435053"
down_revision: Union[str, Sequence[str], None] = "6cb22c2bfde4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create trek_paths table
    op.create_table(
        "trek_paths",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trek_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "path_coordinates",
            Geometry(geometry_type="LINESTRING", srid=4326),
            nullable=True,
        ),
        sa.Column("total_distance_meters", sa.Float(), nullable=False),
        sa.Column("estimated_duration_hours", sa.Float(), nullable=False),
        sa.Column("elevation_gain_meters", sa.Float(), nullable=True),
        sa.Column("difficulty_rating", sa.Integer(), nullable=True),
        sa.Column("waypoints", sa.String(), nullable=True),  # JSON string
        sa.Column("safety_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["trek_id"], ["treks.id"]),
    )
    op.create_index("ix_trek_paths_id", "trek_paths", ["id"])
    op.create_index("ix_trek_paths_trek_id", "trek_paths", ["trek_id"])
    op.create_index("ix_trek_paths_name", "trek_paths", ["name"])
    op.create_index(
        "ix_trek_paths_total_distance_meters", "trek_paths", ["total_distance_meters"]
    )
    op.create_index(
        "ix_trek_paths_estimated_duration_hours",
        "trek_paths",
        ["estimated_duration_hours"],
    )
    op.create_index("ix_trek_paths_created_at", "trek_paths", ["created_at"])
    op.create_index("ix_trek_paths_is_active", "trek_paths", ["is_active"])

    # Create route_segments table if it doesn't exist
    op.create_table(
        "route_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("segment_type", sa.String(), nullable=False),
        sa.Column("start_timestamp", sa.BigInteger(), nullable=False),
        sa.Column("end_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("start_latitude", sa.Float(), nullable=False),
        sa.Column("start_longitude", sa.Float(), nullable=False),
        sa.Column("end_latitude", sa.Float(), nullable=True),
        sa.Column("end_longitude", sa.Float(), nullable=True),
        sa.Column("total_distance_meters", sa.Float(), nullable=True),
        sa.Column("total_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("max_speed_ms", sa.Float(), nullable=True),
        sa.Column("avg_speed_ms", sa.Float(), nullable=True),
        sa.Column("trek_path_id", sa.Integer(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"]),
        sa.ForeignKeyConstraint(["trek_path_id"], ["trek_paths.id"]),
    )
    op.create_index("ix_route_segments_id", "route_segments", ["id"])
    op.create_index("ix_route_segments_trip_id", "route_segments", ["trip_id"])
    op.create_index(
        "ix_route_segments_segment_type", "route_segments", ["segment_type"]
    )
    op.create_index(
        "ix_route_segments_start_timestamp", "route_segments", ["start_timestamp"]
    )
    op.create_index(
        "ix_route_segments_end_timestamp", "route_segments", ["end_timestamp"]
    )
    op.create_index(
        "ix_route_segments_start_latitude", "route_segments", ["start_latitude"]
    )
    op.create_index(
        "ix_route_segments_start_longitude", "route_segments", ["start_longitude"]
    )
    op.create_index(
        "ix_route_segments_end_latitude", "route_segments", ["end_latitude"]
    )
    op.create_index(
        "ix_route_segments_end_longitude", "route_segments", ["end_longitude"]
    )
    op.create_index(
        "ix_route_segments_trek_path_id", "route_segments", ["trek_path_id"]
    )
    op.create_index(
        "ix_route_segments_is_completed", "route_segments", ["is_completed"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop route_segments table
    op.drop_index("ix_route_segments_is_completed", "route_segments")
    op.drop_index("ix_route_segments_trek_path_id", "route_segments")
    op.drop_index("ix_route_segments_end_longitude", "route_segments")
    op.drop_index("ix_route_segments_end_latitude", "route_segments")
    op.drop_index("ix_route_segments_start_longitude", "route_segments")
    op.drop_index("ix_route_segments_start_latitude", "route_segments")
    op.drop_index("ix_route_segments_end_timestamp", "route_segments")
    op.drop_index("ix_route_segments_start_timestamp", "route_segments")
    op.drop_index("ix_route_segments_segment_type", "route_segments")
    op.drop_index("ix_route_segments_trip_id", "route_segments")
    op.drop_index("ix_route_segments_id", "route_segments")
    op.drop_table("route_segments")

    # Drop trek_paths table
    op.drop_index("ix_trek_paths_is_active", "trek_paths")
    op.drop_index("ix_trek_paths_created_at", "trek_paths")
    op.drop_index("ix_trek_paths_estimated_duration_hours", "trek_paths")
    op.drop_index("ix_trek_paths_total_distance_meters", "trek_paths")
    op.drop_index("ix_trek_paths_name", "trek_paths")
    op.drop_index("ix_trek_paths_trek_id", "trek_paths")
    op.drop_index("ix_trek_paths_id", "trek_paths")
    op.drop_table("trek_paths")
