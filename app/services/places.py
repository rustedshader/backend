from sqlmodel import Session, select, and_
from app.models.database.places import Place
from app.models.schemas.places import PlaceCreate, PlaceUpdate, PlaceSearchQuery
from typing import List, Optional, Tuple
import datetime
import math


async def create_place(place_data: PlaceCreate, admin_id: int, db: Session) -> Place:
    """Create a new place (admin only)."""
    try:
        place = Place(
            **place_data.model_dump(), created_by_admin_id=admin_id, is_active=True
        )

        db.add(place)
        db.commit()
        db.refresh(place)

        return place
    except Exception as e:
        db.rollback()
        raise e


async def get_place_by_id(place_id: int, db: Session) -> Optional[Place]:
    """Get a place by ID."""
    statement = select(Place).where(Place.id == place_id, Place.is_active)
    return db.exec(statement).first()


async def update_place(
    place_id: int, update_data: PlaceUpdate, db: Session
) -> Optional[Place]:
    """Update a place (admin only)."""
    try:
        place = await get_place_by_id(place_id, db)
        if not place:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(place, field, value)

        place.updated_at = int(datetime.datetime.utcnow().timestamp())

        db.add(place)
        db.commit()
        db.refresh(place)

        return place
    except Exception as e:
        db.rollback()
        raise e


async def delete_place(place_id: int, db: Session) -> bool:
    """Soft delete a place (admin only)."""
    try:
        place = await get_place_by_id(place_id, db)
        if not place:
            return False

        place.is_active = False
        place.updated_at = int(datetime.datetime.utcnow().timestamp())

        db.add(place)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        raise e


async def search_places(
    search_query: PlaceSearchQuery,
    page: int = 1,
    page_size: int = 20,
    db: Session = None,
) -> Tuple[List[Place], int]:
    """Search places with filters and pagination."""
    try:
        statement = select(Place).where(Place.is_active)

        # Apply filters
        if search_query.city:
            statement = statement.where(Place.city.ilike(f"%{search_query.city}%"))

        if search_query.state:
            statement = statement.where(Place.state.ilike(f"%{search_query.state}%"))

        if search_query.place_type:
            statement = statement.where(Place.place_type == search_query.place_type)

        if search_query.is_featured is not None:
            statement = statement.where(Place.is_featured == search_query.is_featured)

        # Location-based search (within radius)
        if (
            search_query.latitude is not None
            and search_query.longitude is not None
            and search_query.radius_km is not None
        ):
            # Simple distance calculation using Haversine formula
            # Note: For production, consider using PostGIS for better performance
            places_in_radius = []
            all_places = db.exec(statement).all()

            for place in all_places:
                distance = calculate_distance(
                    search_query.latitude,
                    search_query.longitude,
                    place.latitude,
                    place.longitude,
                )
                if distance <= search_query.radius_km:
                    places_in_radius.append(place)

            # Apply pagination to filtered results
            total_count = len(places_in_radius)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            places = places_in_radius[start_idx:end_idx]

            return places, total_count

        # Get total count for pagination
        count_statement = statement
        total_count = len(db.exec(count_statement).all())

        # Apply pagination
        offset = (page - 1) * page_size
        statement = statement.offset(offset).limit(page_size)

        places = db.exec(statement).all()
        return list(places), total_count

    except Exception as e:
        raise e


async def get_featured_places(db: Session, limit: int = 10) -> List[Place]:
    """Get featured places."""
    statement = (
        select(Place).where(and_(Place.is_active, Place.is_featured)).limit(limit)
    )
    return list(db.exec(statement).all())


async def get_places_by_type(
    place_type: str, db: Session, limit: int = 20
) -> List[Place]:
    """Get places by type."""
    statement = (
        select(Place)
        .where(and_(Place.is_active, Place.place_type == place_type))
        .limit(limit)
    )
    return list(db.exec(statement).all())


async def get_places_by_city(city: str, db: Session, limit: int = 20) -> List[Place]:
    """Get places in a specific city."""
    statement = (
        select(Place)
        .where(and_(Place.is_active, Place.city.ilike(f"%{city}%")))
        .limit(limit)
    )
    return list(db.exec(statement).all())


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


async def get_nearby_places(
    latitude: float, longitude: float, radius_km: float, db: Session, limit: int = 20
) -> List[Place]:
    """Get places within a specified radius."""
    statement = select(Place).where(Place.is_active).limit(100)  # Get more to filter
    all_places = db.exec(statement).all()

    nearby_places = []
    for place in all_places:
        distance = calculate_distance(
            latitude, longitude, place.latitude, place.longitude
        )
        if distance <= radius_km:
            nearby_places.append(place)

    # Sort by distance and limit results
    nearby_places.sort(
        key=lambda p: calculate_distance(latitude, longitude, p.latitude, p.longitude)
    )
    return nearby_places[:limit]
