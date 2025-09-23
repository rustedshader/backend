from sqlmodel import Session, select
from app.models.database.online_activity import OnlineActivity
from typing import Optional, List, Tuple, Dict, Any
import datetime
import math
from geoalchemy2.shape import to_shape
from app.models.schemas.online_activity import (
    OnlineActivityCreate,
    OnlineActivityUpdate,
    OnlineActivitySearchQuery,
)


def _serialize_geometry_to_lat_lng(activity: OnlineActivity) -> Dict[str, Any]:
    """Convert OnlineActivity with geometry to dict with latitude/longitude."""
    activity_data = activity.dict()

    if hasattr(activity, "location") and activity.location:
        try:
            point = to_shape(activity.location)
            activity_data["latitude"] = point.y
            activity_data["longitude"] = point.x
        except Exception:
            activity_data["latitude"] = None
            activity_data["longitude"] = None
    else:
        activity_data["latitude"] = None
        activity_data["longitude"] = None
    return activity_data


async def create_online_activity(
    online_activity_data: OnlineActivityCreate, admin_id: int, db: Session
) -> Dict[str, Any]:
    """Create a new online Activity (admin only)."""
    try:
        data = online_activity_data.model_dump()
        latitude = data.pop("latitude")
        longitude = data.pop("longitude")
        # WKT format: POINT(longitude latitude)
        wkt_point = f"POINT({longitude} {latitude})"
        data["location"] = wkt_point

        place = OnlineActivity(
            **data,
            created_by=admin_id,
            is_active=True,
        )

        db.add(place)
        db.commit()
        db.refresh(place)

        return _serialize_geometry_to_lat_lng(place)
    except Exception as e:
        db.rollback()
        raise e


async def get_online_activity_by_id(
    online_activity_id: int, db: Session
) -> Optional[Dict[str, Any]]:
    """Get a online activity by ID."""
    statement = select(OnlineActivity).where(
        OnlineActivity.id == online_activity_id, OnlineActivity.is_active
    )
    activity = db.exec(statement).first()
    if not activity:
        return None
    return _serialize_geometry_to_lat_lng(activity)


async def _get_online_activity_raw_by_id(
    online_activity_id: int, db: Session
) -> Optional[OnlineActivity]:
    """Get raw OnlineActivity object without serialization - for internal use only."""
    statement = select(OnlineActivity).where(
        OnlineActivity.id == online_activity_id, OnlineActivity.is_active
    )
    return db.exec(statement).first()


async def update_online_activity(
    online_activity_id: int, update_data: OnlineActivityUpdate, db: Session
) -> Optional[Dict[str, Any]]:
    """Update a online activity (admin only)."""
    try:
        online_activity = await _get_online_activity_raw_by_id(online_activity_id, db)
        if not online_activity:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)

        # Handle latitude/longitude conversion to geometry if present
        if "latitude" in update_dict and "longitude" in update_dict:
            latitude = update_dict.pop("latitude")
            longitude = update_dict.pop("longitude")
            if latitude is not None and longitude is not None:
                wkt_point = f"POINT({longitude} {latitude})"
                update_dict["location"] = wkt_point
        elif "latitude" in update_dict or "longitude" in update_dict:
            # Remove individual lat/lng fields if only one is provided
            update_dict.pop("latitude", None)
            update_dict.pop("longitude", None)

        for field, value in update_dict.items():
            setattr(online_activity, field, value)

        online_activity.updated_at = datetime.datetime.now(datetime.timezone.utc)

        db.add(online_activity)
        db.commit()
        db.refresh(online_activity)

        return _serialize_geometry_to_lat_lng(online_activity)
    except Exception as e:
        db.rollback()
        raise e


async def delete_online_activity(online_activity_id: int, db: Session) -> bool:
    """Soft delete a Online Activity (admin only)."""
    try:
        online_activity = await _get_online_activity_raw_by_id(online_activity_id, db)
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
) -> Tuple[List[Dict[str, Any]], int]:
    """Search online activities with filtering and pagination."""
    try:
        statement = select(OnlineActivity).where(OnlineActivity.is_active)

        # Apply filters
        if search_query.name:
            statement = statement.where(
                OnlineActivity.name.ilike(f"%{search_query.name}%")
            )

        if search_query.city:
            statement = statement.where(
                OnlineActivity.city.ilike(f"%{search_query.city}%")
            )

        if search_query.state:
            statement = statement.where(
                OnlineActivity.state.ilike(f"%{search_query.state}%")
            )

        if search_query.place_type:
            statement = statement.where(
                OnlineActivity.place_type.ilike(f"%{search_query.place_type}%")
            )

        # Get total count
        count_statement = statement
        total_count = len(db.exec(count_statement).all())

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

        activities = db.exec(statement).all()
        serialized_activities = [
            _serialize_geometry_to_lat_lng(activity) for activity in activities
        ]
        return serialized_activities, total_count

    except Exception as e:
        raise e


async def get_nearby_online_activities(
    latitude: float, longitude: float, radius_km: float, db: Session, limit: int = 20
) -> List[Dict[str, Any]]:
    """Get online activities within a radius of given coordinates."""
    try:
        # Get all active activities
        statement = select(OnlineActivity).where(OnlineActivity.is_active)
        all_activities = db.exec(statement).all()

        # Filter by distance
        nearby_activities = []
        for activity in all_activities:
            if hasattr(activity, "location") and activity.location:
                try:
                    point = to_shape(activity.location)
                    activity_lat = point.y
                    activity_lng = point.x
                    distance = calculate_distance(
                        latitude,
                        longitude,
                        float(activity_lat),
                        float(activity_lng),
                    )
                    if distance <= radius_km:
                        nearby_activities.append((activity, distance))
                except Exception:
                    continue

        # Sort by distance and limit
        nearby_activities.sort(key=lambda a: a[1])

        # Return serialized activities without distance
        result = []
        for activity, _ in nearby_activities[:limit]:
            result.append(_serialize_geometry_to_lat_lng(activity))

        return result

    except Exception as e:
        raise e


async def get_online_activities_by_type(
    activity_type: str, db: Session, limit: int = 20
) -> List[Dict[str, Any]]:
    """Get online activities by type."""
    try:
        statement = (
            select(OnlineActivity)
            .where(
                OnlineActivity.is_active,
                OnlineActivity.place_type.ilike(f"%{activity_type}%"),
            )
            .limit(limit)
        )

        activities = db.exec(statement).all()
        return [_serialize_geometry_to_lat_lng(activity) for activity in activities]

    except Exception as e:
        raise e


async def get_online_activities_by_city(
    city: str, db: Session, limit: int = 20
) -> List[Dict[str, Any]]:
    """Get online activities by city."""
    try:
        statement = (
            select(OnlineActivity)
            .where(OnlineActivity.is_active, OnlineActivity.city.ilike(f"%{city}%"))
            .limit(limit)
        )

        activities = db.exec(statement).all()
        return [_serialize_geometry_to_lat_lng(activity) for activity in activities]

    except Exception as e:
        raise e
