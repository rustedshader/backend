# Removed duplicate imports
from sqlmodel import select, Session
from shapely.geometry import LineString
from geoalchemy2.shape import from_shape, to_shape
import datetime
import geojson
from app.models.schemas.offline_activity import (
    OfflineActivityCreate,
    OfflineActivityUpdate,
    OfflineActivityDataUpdate,
)
from app.models.database.offline_activity import (
    OfflineActivity,
    OfflineActivityRouteData,
)
from typing import List


async def create_offline_activity(
    created_by_id: int, offline_activity_create_data: OfflineActivityCreate, db: Session
) -> OfflineActivity:
    try:
        new_activity = OfflineActivity(**offline_activity_create_data.model_dump())
        new_activity.created_by = created_by_id
        db.add(new_activity)
        db.commit()
        db.refresh(new_activity)
        return new_activity
    except Exception as e:
        db.rollback()
        raise e


async def get_offline_activity_by_id(
    activity_id: int, db: Session
) -> OfflineActivity | None:
    statement = select(OfflineActivity).where(OfflineActivity.id == activity_id)
    activity = db.exec(statement).first()
    return activity


async def get_all_offline_activities(db: Session) -> List[OfflineActivity]:
    """Get all offline activities from the database."""
    statement = select(OfflineActivity)
    activities = db.exec(statement).all()
    return List(activities)


async def get_offline_activities_by_difficulty(
    difficulty: str, db: Session
) -> List[OfflineActivity]:
    """Get offline activities filtered by difficulty level."""
    statement = select(OfflineActivity).where(
        OfflineActivity.difficulty_level == difficulty
    )
    activities = db.exec(statement).all()
    return List(activities)


async def get_offline_activities_by_state(
    state: str, db: Session
) -> List[OfflineActivity]:
    """Get offline activities filtered by state."""
    statement = select(OfflineActivity).where(OfflineActivity.state.ilike(f"%{state}%"))
    activities = db.exec(statement).all()
    return List(activities)


async def update_offline_activity(
    activity_id: int, activity_update_data: OfflineActivityUpdate, db: Session
) -> OfflineActivity | None:
    try:
        statement = select(OfflineActivity).where(OfflineActivity.id == activity_id)
        activity = db.exec(statement).first()
        if not activity:
            return None
        update_data = activity_update_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(activity, field, value)
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    except Exception as e:
        db.rollback()
        raise e


async def update_offline_activity_route_data(
    activity_route_data: OfflineActivityDataUpdate, db: Session
) -> OfflineActivityRouteData:
    try:
        statement = select(OfflineActivity).where(
            OfflineActivity.id == activity_route_data.offline_activity_id
        )
        activity = db.exec(statement).first()
        if not activity:
            return None
        coordinates = [(point[1], point[0]) for point in activity_route_data.route_data]
        line_string = LineString(coordinates)
        existing_route_statement = select(OfflineActivityRouteData).where(
            OfflineActivityRouteData.offline_activity_id
            == activity_route_data.offline_activity_id
        )
        existing_route = db.exec(existing_route_statement).first()
        if existing_route:
            existing_route.route = from_shape(line_string, srid=4326)
            existing_route.updated_at = int(datetime.datetime.utcnow().timestamp())
            db.add(existing_route)
            db.commit()
            db.refresh(existing_route)
            return existing_route
        else:
            new_route_data = OfflineActivityRouteData(
                offline_activity_id=activity_route_data.offline_activity_id,
                route=from_shape(line_string, srid=4326),
            )
            db.add(new_route_data)
            db.commit()
            db.refresh(new_route_data)
            return new_route_data
    except Exception as e:
        db.rollback()
        raise e


async def get_geojson_route_data(activity_id: int, db: Session):
    try:
        statement = select(OfflineActivityRouteData).where(
            OfflineActivityRouteData.offline_activity_id == activity_id
        )
        route_data = db.exec(statement).first()
        if not route_data or not route_data.route:
            return None
        shape = to_shape(route_data.route)
        geojson_data = geojson.Feature(
            geometry=geojson.loads(
                geojson.dumps(geojson.LineString(list(shape.coords)))
            ),
            properties={"offline_activity_id": activity_id},
        )
        return geojson_data
    except Exception as e:
        raise e


async def delete_offline_activity(activity_id: int, db: Session) -> bool:
    """
    Delete an offline activity and all its related data (route data, trips, etc.)
    Returns True if successful, False if activity not found
    """
    try:
        statement = select(OfflineActivity).where(OfflineActivity.id == activity_id)
        activity = db.exec(statement).first()
        if not activity:
            return False
        route_statement = select(OfflineActivityRouteData).where(
            OfflineActivityRouteData.offline_activity_id == activity_id
        )
        route_data = db.exec(route_statement).first()
        if route_data:
            db.delete(route_data)
        db.delete(activity)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
