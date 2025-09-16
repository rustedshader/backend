from sqlmodel import Session, select
from app.models.database.online_activity import OnlineActivity
from typing import Optional
import datetime
import math
from app.models.schemas.online_activity import (
    OnlineActivityCreate,
    OnlineActivityUpdate,
)


async def create_online_activity(
    online_activity_data: OnlineActivityCreate, admin_id: int, db: Session
) -> OnlineActivity:
    """Create a new online Activity (admin only)."""
    try:
        place = OnlineActivity(
            **online_activity_data.model_dump(),
            created_by=admin_id,
            is_active=True,
        )

        db.add(place)
        db.commit()
        db.refresh(place)

        return place
    except Exception as e:
        db.rollback()
        raise e


async def get_online_activity_by_id(
    online_activity_id: int, db: Session
) -> Optional[OnlineActivity]:
    """Get a online activity by ID."""
    statement = select(OnlineActivity).where(
        OnlineActivity.id == online_activity_id, OnlineActivity.is_active
    )
    return db.exec(statement).first()


async def update_online_activity(
    online_activity_id: int, update_data: OnlineActivityUpdate, db: Session
) -> Optional[OnlineActivity]:
    """Update a online activity (admin only)."""
    try:
        online_activity = await get_online_activity_by_id(online_activity_id, db)
        if not online_activity:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(online_activity, field, value)

        online_activity.updated_at = datetime.datetime.now(datetime.timezone.utc)

        db.add(online_activity)
        db.commit()
        db.refresh(online_activity)

        return online_activity
    except Exception as e:
        db.rollback()
        raise e


async def delete_online_activity(online_activity_id: int, db: Session) -> bool:
    """Soft delete a Online Activity (admin only)."""
    try:
        online_activity = await get_online_activity_by_id(online_activity_id, db)
        if not online_activity:
            return False

        online_activity.is_active = False
        online_activity.updated_at = datetime.datetime.now(datetime.timezone.utc)

        db.add(online_activity)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        raise e


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on Earth using Haversine formula.
    Returns distance in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers
    r = 6371

    return c * r
