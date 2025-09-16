from sqlmodel import Session, select
from app.models.database.online_activity import OnlineActivity
from typing import Optional, List, Tuple
import datetime
import math
from app.models.schemas.online_activity import (
    OnlineActivityCreate,
    OnlineActivityUpdate,
    OnlineActivitySearchQuery,
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


async def search_online_activities(
    search_query: OnlineActivitySearchQuery,
    page: int = 1,
    page_size: int = 20,
    db: Session = None,
) -> Tuple[List[OnlineActivity], int]:
    """Search online activities with filtering and pagination."""
    try:
        statement = select(OnlineActivity).where(OnlineActivity.is_active)

        # Apply filters
        if search_query.city:
            statement = statement.where(
                OnlineActivity.city.ilike(f"%{search_query.city}%")
            )

        if search_query.state:
            statement = statement.where(
                OnlineActivity.state.ilike(f"%{search_query.state}%")
            )

        if search_query.activity_type:
            statement = statement.where(
                OnlineActivity.activity_type.ilike(f"%{search_query.activity_type}%")
            )

        if search_query.is_featured is not None:
            statement = statement.where(
                OnlineActivity.is_featured == search_query.is_featured
            )

        # Get total count
        count_statement = statement
        total_count = len(db.exec(count_statement).all())

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

        activities = db.exec(statement).all()
        return list(activities), total_count

    except Exception as e:
        raise e


async def get_featured_online_activities(
    db: Session, limit: int = 10
) -> List[OnlineActivity]:
    """Get featured online activities."""
    try:
        statement = (
            select(OnlineActivity)
            .where(OnlineActivity.is_active, OnlineActivity.is_featured)
            .limit(limit)
        )

        activities = db.exec(statement).all()
        return list(activities)

    except Exception as e:
        raise e


async def get_nearby_online_activities(
    latitude: float, longitude: float, radius_km: float, db: Session, limit: int = 20
) -> List[OnlineActivity]:
    """Get online activities within a radius of given coordinates."""
    try:
        # Get all active activities
        statement = select(OnlineActivity).where(OnlineActivity.is_active)
        all_activities = db.exec(statement).all()

        # Filter by distance
        nearby_activities = []
        for activity in all_activities:
            if activity.latitude is not None and activity.longitude is not None:
                distance = calculate_distance(
                    latitude,
                    longitude,
                    float(activity.latitude),
                    float(activity.longitude),
                )
                if distance <= radius_km:
                    nearby_activities.append(activity)

        # Sort by distance and limit
        nearby_activities.sort(
            key=lambda a: calculate_distance(
                latitude, longitude, float(a.latitude), float(a.longitude)
            )
        )

        return nearby_activities[:limit]

    except Exception as e:
        raise e


async def get_online_activities_by_type(
    activity_type: str, db: Session, limit: int = 20
) -> List[OnlineActivity]:
    """Get online activities by type."""
    try:
        statement = (
            select(OnlineActivity)
            .where(
                OnlineActivity.is_active,
                OnlineActivity.activity_type.ilike(f"%{activity_type}%"),
            )
            .limit(limit)
        )

        activities = db.exec(statement).all()
        return list(activities)

    except Exception as e:
        raise e


async def get_online_activities_by_city(
    city: str, db: Session, limit: int = 20
) -> List[OnlineActivity]:
    """Get online activities by city."""
    try:
        statement = (
            select(OnlineActivity)
            .where(OnlineActivity.is_active, OnlineActivity.city.ilike(f"%{city}%"))
            .limit(limit)
        )

        activities = db.exec(statement).all()
        return list(activities)

    except Exception as e:
        raise e
