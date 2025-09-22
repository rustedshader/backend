from sqlmodel import Session, select
from app.models.database.accommodation import Accommodation
from typing import Optional, List, Tuple, Dict, Any
import math
from geoalchemy2.shape import to_shape
from app.models.schemas.accommodation import (
    AccommodationCreate,
    AccommodationUpdate,
    AccommodationSearchQuery,
)


def _serialize_geometry_to_lat_lng(accommodation: Accommodation) -> Dict[str, Any]:
    """Convert Accommodation with geometry to dict with latitude/longitude."""
    accommodation_data = accommodation.dict()

    if hasattr(accommodation, "location") and accommodation.location:
        try:
            point = to_shape(accommodation.location)
            accommodation_data["latitude"] = point.y
            accommodation_data["longitude"] = point.x
        except Exception:
            accommodation_data["latitude"] = None
            accommodation_data["longitude"] = None
    else:
        accommodation_data["latitude"] = None
        accommodation_data["longitude"] = None
    return accommodation_data


async def create_accommodation(
    accommodation_data: AccommodationCreate, db: Session
) -> Dict[str, Any]:
    """Create a new accommodation."""
    try:
        data = accommodation_data.model_dump()
        latitude = data.pop("latitude")
        longitude = data.pop("longitude")
        # WKT format: POINT(longitude latitude)
        wkt_point = f"POINT({longitude} {latitude})"
        data["location"] = wkt_point

        accommodation = Accommodation(**data)

        db.add(accommodation)
        db.commit()
        db.refresh(accommodation)

        return _serialize_geometry_to_lat_lng(accommodation)
    except Exception as e:
        db.rollback()
        raise e


async def get_accommodation_by_id(
    accommodation_id: int, db: Session
) -> Optional[Dict[str, Any]]:
    """Get an accommodation by ID."""
    statement = select(Accommodation).where(Accommodation.id == accommodation_id)
    accommodation = db.exec(statement).first()
    if not accommodation:
        return None
    return _serialize_geometry_to_lat_lng(accommodation)


async def _get_accommodation_raw_by_id(
    accommodation_id: int, db: Session
) -> Optional[Accommodation]:
    """Get raw Accommodation object without serialization - for internal use only."""
    statement = select(Accommodation).where(Accommodation.id == accommodation_id)
    return db.exec(statement).first()


async def update_accommodation(
    accommodation_id: int, update_data: AccommodationUpdate, db: Session
) -> Optional[Dict[str, Any]]:
    """Update an accommodation."""
    try:
        accommodation = await _get_accommodation_raw_by_id(accommodation_id, db)
        if not accommodation:
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
            setattr(accommodation, field, value)

        db.add(accommodation)
        db.commit()
        db.refresh(accommodation)

        return _serialize_geometry_to_lat_lng(accommodation)
    except Exception as e:
        db.rollback()
        raise e


async def delete_accommodation(accommodation_id: int, db: Session) -> bool:
    """Delete an accommodation."""
    try:
        accommodation = await _get_accommodation_raw_by_id(accommodation_id, db)
        if not accommodation:
            return False

        db.delete(accommodation)
        db.commit()

        return True
    except Exception as e:
        db.rollback()
        raise e


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


async def get_accommodations(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    city: Optional[str] = None,
    state: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """Get accommodations with optional filtering and pagination."""
    try:
        statement = select(Accommodation)

        # Apply filters
        if city:
            statement = statement.where(Accommodation.city.ilike(f"%{city}%"))
        if state:
            statement = statement.where(Accommodation.state.ilike(f"%{state}%"))

        # Execute query for counting and pagination
        accommodations = db.exec(statement).all()

        # Apply location-based filtering if coordinates provided
        filtered_accommodations = []
        if latitude is not None and longitude is not None and radius_km is not None:
            for accommodation in accommodations:
                try:
                    if accommodation.location:
                        point = to_shape(accommodation.location)
                        distance = calculate_distance(
                            latitude, longitude, point.y, point.x
                        )
                        if distance <= radius_km:
                            filtered_accommodations.append(accommodation)
                except Exception:
                    continue
        else:
            filtered_accommodations = accommodations

        # Count total results
        total_count = len(filtered_accommodations)

        # Apply pagination
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_accommodations = filtered_accommodations[start_index:end_index]

        # Serialize accommodations
        serialized_accommodations = []
        for accommodation in paginated_accommodations:
            serialized_accommodations.append(
                _serialize_geometry_to_lat_lng(accommodation)
            )

        return serialized_accommodations, total_count

    except Exception as e:
        raise e


async def search_accommodations(
    search_query: AccommodationSearchQuery,
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    """Search accommodations based on search criteria."""
    return await get_accommodations(
        db=db,
        page=page,
        page_size=page_size,
        city=search_query.city,
        state=search_query.state,
        latitude=search_query.latitude,
        longitude=search_query.longitude,
        radius_km=search_query.radius_km,
    )
