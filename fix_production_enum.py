#!/usr/bin/env python3
"""
Script to fix the production database enum issue.
Run this before running alembic upgrade head if you encounter the itinerarytypeenum error.
"""

import sqlalchemy as sa
from app.core.config import settings


def fix_enum_issue():
    """Create the itinerarytypeenum if it doesn't exist."""
    engine = sa.create_engine(settings.database_url)

    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()

        try:
            # Check if enum exists
            result = conn.execute(
                sa.text("SELECT 1 FROM pg_type WHERE typname = 'itinerarytypeenum'")
            ).fetchone()

            if not result:
                print("Creating itinerarytypeenum...")
                conn.execute(
                    sa.text(
                        "CREATE TYPE itinerarytypeenum AS ENUM ('TREK', 'CITY_TOUR', 'MIXED')"
                    )
                )
                print("✅ itinerarytypeenum created successfully")
            else:
                print("✅ itinerarytypeenum already exists")

            # Verify the enum
            result = conn.execute(
                sa.text("""
                SELECT enumlabel FROM pg_enum WHERE enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = 'itinerarytypeenum'
                )
            """)
            )

            enum_values = [row[0] for row in result]
            print(f"Enum values: {enum_values}")

            trans.commit()
            print("✅ Database fix completed successfully")

        except Exception as e:
            trans.rollback()
            print(f"❌ Error: {e}")
            raise


if __name__ == "__main__":
    fix_enum_issue()
