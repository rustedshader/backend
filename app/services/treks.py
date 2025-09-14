from app.models.schemas.treks import TrekCreate, TrekUpdate, TrekDataUpdate
from app.models.database.offline_activity import Trek, TrekRouteData
from sqlmodel import select, Session
from shapely.geometry import LineString
from geoalchemy2.shape import from_shape
import datetime
import geojson
from typing import Any
from geoalchemy2.shape import to_shape


async def create_trecks(
    created_by_id: int, treck_create_data: TrekCreate, db: Session
) -> Trek:
    try:
        new_trek = Trek(**treck_create_data.model_dump())
        new_trek.created_by_id = created_by_id
        db.add(new_trek)
        db.commit()
        db.refresh(new_trek)
        return new_trek
    except Exception as e:
        db.rollback()
        raise e


async def get_trek_by_id(trek_id: int, db: Session) -> Trek | None:
    statement = select(Trek).where(Trek.id == trek_id)
    trek = db.exec(statement).first()
    return trek


async def get_all_treks(db: Session) -> list[Trek]:
    """Get all treks from the database."""
    statement = select(Trek)
    treks = db.exec(statement).all()
    return list(treks)


async def get_treks_by_difficulty(difficulty: str, db: Session) -> list[Trek]:
    """Get treks filtered by difficulty level."""
    statement = select(Trek).where(Trek.difficulty_level == difficulty)
    treks = db.exec(statement).all()
    return list(treks)


async def get_treks_by_state(state: str, db: Session) -> list[Trek]:
    """Get treks filtered by state."""
    statement = select(Trek).where(Trek.state.ilike(f"%{state}%"))
    treks = db.exec(statement).all()
    return list(treks)


async def get_treks_by_duration(
    min_duration: int = None, max_duration: int = None, db: Session = None
) -> list[Trek]:
    """Get treks filtered by duration range."""
    statement = select(Trek)

    if min_duration is not None:
        statement = statement.where(Trek.duration >= min_duration)
    if max_duration is not None:
        statement = statement.where(Trek.duration <= max_duration)

    treks = db.exec(statement).all()
    return list(treks)


async def update_trek(
    trek_id: int, trek_update_data: TrekUpdate, db: Session
) -> Trek | None:
    try:
        # Get the existing trek
        statement = select(Trek).where(Trek.id == trek_id)
        trek = db.exec(statement).first()

        if not trek:
            return None

        # Update only the fields that are provided (not None)
        update_data = trek_update_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trek, field, value)

        db.add(trek)
        db.commit()
        db.refresh(trek)
        return trek
    except Exception as e:
        db.rollback()
        raise e


async def update_trek_route_data(
    treck_route_data: TrekDataUpdate, db: Session
) -> TrekRouteData:
    try:
        # Check if the trek exists
        statement = select(Trek).where(Trek.id == treck_route_data.trek_id)
        trek = db.exec(statement).first()

        if not trek:
            return None

        # Convert route data from [lat, lon] to [lon, lat] for LineString
        # LineString expects coordinates in [longitude, latitude] format
        coordinates = [(point[1], point[0]) for point in treck_route_data.route_data]
        line_string = LineString(coordinates)

        # Check if route data already exists for this trek
        existing_route_statement = select(TrekRouteData).where(
            TrekRouteData.trek_id == treck_route_data.trek_id
        )
        existing_route = db.exec(existing_route_statement).first()

        if existing_route:
            # Update existing route
            existing_route.route = from_shape(line_string, srid=4326)
            existing_route.updated_at = int(datetime.datetime.utcnow().timestamp())
            db.add(existing_route)
            db.commit()
            db.refresh(existing_route)
            return existing_route
        else:
            # Create new TrekRouteData entry
            new_route_data = TrekRouteData(
                trek_id=treck_route_data.trek_id,
                route=from_shape(line_string, srid=4326),
            )
            db.add(new_route_data)
            db.commit()
            db.refresh(new_route_data)
            return new_route_data
    except Exception as e:
        db.rollback()
        raise e


async def get_geojson_route_data(trek_id: int, db: Session) -> Any | None:
    try:
        # Fetch the route data for the given trek_id
        statement = select(TrekRouteData).where(TrekRouteData.trek_id == trek_id)
        route_data = db.exec(statement).first()

        if not route_data or not route_data.route:
            return None

        # Convert the WKB geometry to a Shapely geometry
        shape = to_shape(route_data.route)

        # Convert the Shapely geometry to GeoJSON format
        geojson_data = geojson.Feature(
            geometry=geojson.loads(
                geojson.dumps(geojson.LineString(list(shape.coords)))
            ),
            properties={"trek_id": trek_id},
        )

        return geojson_data
    except Exception as e:
        raise e


async def delete_trek(trek_id: int, db: Session) -> bool:
    """
    Delete a trek and all its related data (route data, trips, etc.)
    Returns True if successful, False if trek not found
    """
    try:
        # Get the trek to verify it exists
        statement = select(Trek).where(Trek.id == trek_id)
        trek = db.exec(statement).first()

        if not trek:
            return False

        # Delete related TrekRouteData first (due to foreign key constraint)
        route_statement = select(TrekRouteData).where(TrekRouteData.trek_id == trek_id)
        route_data = db.exec(route_statement).first()
        if route_data:
            db.delete(route_data)

        # Note: For trips, tracking_device, and guides tables with foreign key references,
        # you might want to handle them based on your business logic:
        # 1. CASCADE delete (delete all related records)
        # 2. SET NULL (if foreign key allows null)
        # 3. Prevent deletion if related records exist
        #
        # For now, we'll delete the trek directly. If you have foreign key constraints
        # that prevent deletion, you'll need to handle those relationships first.

        # Delete the trek
        db.delete(trek)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
