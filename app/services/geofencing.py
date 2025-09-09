from sqlmodel import Session, select
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import text
from datetime import datetime

from shapely.geometry import Polygon, Point
from shapely.wkt import dumps, loads
from geoalchemy2 import WKTElement
from shapely.validation import make_valid

from app.models.database.geofencing import RestrictedAreas, GeofenceViolations
from app.models.schemas.geofencing import (
    RestrictedAreaCreate,
    RestrictedAreaUpdate,
    RestrictedAreaResponse,
    RestrictedAreaSummary,
    GeofenceCheckResponse,
    PolygonCoordinate,
)


def validate_polygon_geometry(coordinates: List[PolygonCoordinate]) -> dict:
    """Validate polygon geometry and return validation results with Shapely"""
    try:
        # Convert to Shapely format
        coord_pairs = [(coord.longitude, coord.latitude) for coord in coordinates]

        # Create polygon
        polygon = Polygon(coord_pairs)

        validation_result = {
            "is_valid": polygon.is_valid,
            "area_sq_meters": None,
            "perimeter_meters": None,
            "centroid": None,
            "bounds": None,
            "errors": [],
        }

        if polygon.is_valid:
            # Calculate approximate area in square meters (rough conversion for lat/lon)
            # For accurate area calculation, use projected coordinates
            validation_result["area_sq_meters"] = (
                polygon.area * 111000 * 111000
            )  # Rough conversion
            validation_result["perimeter_meters"] = (
                polygon.length * 111000
            )  # Rough conversion

            # Get centroid
            centroid = polygon.centroid
            validation_result["centroid"] = {
                "longitude": centroid.x,
                "latitude": centroid.y,
            }

            # Get bounding box
            minx, miny, maxx, maxy = polygon.bounds
            validation_result["bounds"] = {
                "min_longitude": minx,
                "min_latitude": miny,
                "max_longitude": maxx,
                "max_latitude": maxy,
            }
        else:
            # Try to identify specific issues
            if polygon.is_empty:
                validation_result["errors"].append("Polygon is empty")
            if hasattr(polygon, "is_ring") and not polygon.exterior.is_ring:
                validation_result["errors"].append(
                    "Polygon exterior is not a valid ring"
                )
            if polygon.exterior.is_ccw:
                validation_result["errors"].append(
                    "Polygon vertices are in counter-clockwise order"
                )

        return validation_result

    except Exception as e:
        return {
            "is_valid": False,
            "area_sq_meters": None,
            "perimeter_meters": None,
            "centroid": None,
            "bounds": None,
            "errors": [f"Validation error: {str(e)}"],
        }


def coordinates_to_wkt_polygon(coordinates: List[PolygonCoordinate]) -> str:
    """Convert coordinate list to WKT POLYGON string using Shapely for validation"""
    if len(coordinates) < 3:
        raise ValueError("Polygon must have at least 3 coordinates")

    try:
        # Convert to Shapely-compatible format (longitude, latitude)
        coord_pairs = [(coord.longitude, coord.latitude) for coord in coordinates]

        # Create Shapely polygon
        polygon = Polygon(coord_pairs)

        # Validate and fix the polygon if needed
        if not polygon.is_valid:
            polygon = make_valid(polygon)

        # Convert to WKT using Shapely's dumps function
        return dumps(polygon)

    except Exception as e:
        raise ValueError(f"Invalid polygon coordinates: {str(e)}")


def wkt_polygon_to_coordinates(wkt_polygon: str) -> List[PolygonCoordinate]:
    """Convert WKT POLYGON string to coordinate list using Shapely"""
    try:
        # Parse WKT using Shapely
        polygon = loads(wkt_polygon)

        if not isinstance(polygon, Polygon):
            raise ValueError("WKT must represent a valid polygon")

        # Extract exterior coordinates (excluding the closing coordinate)
        coords = list(polygon.exterior.coords)[:-1]

        # Convert to PolygonCoordinate objects
        return [PolygonCoordinate(longitude=lon, latitude=lat) for lon, lat in coords]

    except Exception as e:
        raise ValueError(f"Invalid WKT polygon format: {str(e)}")


async def create_restricted_area(
    area_data: RestrictedAreaCreate, admin_user_id: int, db: Session
) -> RestrictedAreaResponse:
    """Create a new restricted area using Shapely and GeoAlchemy2"""
    try:
        # Convert coordinates to WKT polygon using Shapely (includes validation)
        wkt_polygon = coordinates_to_wkt_polygon(area_data.boundary_coordinates)

        # Create GeoAlchemy2 WKTElement for seamless PostGIS integration
        geom_element = WKTElement(wkt_polygon, srid=4326)

        # Create the restricted area
        restricted_area = RestrictedAreas(
            name=area_data.name,
            description=area_data.description,
            area_type=area_data.area_type,
            created_by_admin_id=admin_user_id,
            severity_level=area_data.severity_level,
            restriction_reason=area_data.restriction_reason,
            contact_info=area_data.contact_info,
            valid_from=area_data.valid_from,
            valid_until=area_data.valid_until,
            send_warning_notification=area_data.send_warning_notification,
            auto_alert_authorities=area_data.auto_alert_authorities,
            buffer_distance_meters=area_data.buffer_distance_meters,
        )

        # Add to database and get ID
        db.add(restricted_area)
        db.flush()  # Get the ID

        # Update with geometry using GeoAlchemy2 WKTElement
        db.execute(
            text("""
                UPDATE restricted_areas 
                SET boundary = :geom
                WHERE id = :area_id
            """),
            {"geom": geom_element, "area_id": restricted_area.id},
        )

        db.commit()
        db.refresh(restricted_area)

        # Convert to response format
        return await get_restricted_area_by_id(restricted_area.id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create restricted area: {str(e)}",
        )


async def get_active_restricted_areas_for_routing(db: Session) -> List[str]:
    """
    Get all active restricted areas as WKT POLYGON strings for routing block_areas.

    This function is specifically designed to format restricted areas for the
    GraphHopper routing API's block_areas parameter.

    Args:
        db: Database session

    Returns:
        List of WKT POLYGON strings in the format expected by GraphHopper
    """
    try:
        # Query active restricted areas and convert their boundaries to WKT
        result = db.execute(
            text("""
                SELECT ST_AsText(boundary) as wkt_geometry, name, area_type, severity_level
                FROM restricted_areas
                WHERE status = 'ACTIVE'
                AND (valid_from IS NULL OR valid_from <= NOW())
                AND (valid_until IS NULL OR valid_until > NOW())
                AND boundary IS NOT NULL
                ORDER BY severity_level DESC, created_at DESC
            """)
        ).fetchall()

        block_areas = []
        for row in result:
            if row.wkt_geometry:
                # Ensure the WKT format is exactly what GraphHopper expects
                # The format should be: "POLYGON((lon1 lat1, lon2 lat2, lon3 lat3, lon1 lat1))"
                wkt_polygon = row.wkt_geometry

                # Validate that it's a proper POLYGON format
                if wkt_polygon.startswith("POLYGON((") and wkt_polygon.endswith("))"):
                    block_areas.append(wkt_polygon)
                else:
                    print(
                        f"Warning: Invalid WKT format for restricted area: {row.name}"
                    )

        print(f"Found {len(block_areas)} active restricted areas for routing")
        return block_areas

    except Exception as e:
        print(f"Error fetching restricted areas for routing: {e}")
        return []


async def get_restricted_area_by_id(
    area_id: int, db: Session
) -> RestrictedAreaResponse:
    """Get a restricted area by ID"""
    statement = select(RestrictedAreas).where(RestrictedAreas.id == area_id)
    restricted_area = db.exec(statement).first()

    if not restricted_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restricted area not found"
        )

    # Get coordinates from geometry
    result = db.execute(
        text("""
            SELECT ST_AsText(boundary) as wkt_geometry
            FROM restricted_areas
            WHERE id = :area_id
        """),
        {"area_id": area_id},
    ).first()

    coordinates = []
    if result and result.wkt_geometry:
        coordinates = wkt_polygon_to_coordinates(result.wkt_geometry)

    return RestrictedAreaResponse(
        id=restricted_area.id,
        name=restricted_area.name,
        description=restricted_area.description,
        area_type=restricted_area.area_type,
        status=restricted_area.status,
        boundary_coordinates=coordinates,
        created_by_admin_id=restricted_area.created_by_admin_id,
        severity_level=restricted_area.severity_level,
        restriction_reason=restricted_area.restriction_reason,
        contact_info=restricted_area.contact_info,
        valid_from=restricted_area.valid_from,
        valid_until=restricted_area.valid_until,
        send_warning_notification=restricted_area.send_warning_notification,
        auto_alert_authorities=restricted_area.auto_alert_authorities,
        buffer_distance_meters=restricted_area.buffer_distance_meters,
        created_at=restricted_area.created_at,
        updated_at=restricted_area.updated_at,
    )


async def get_all_restricted_areas(
    db: Session,
    status_filter: Optional[str] = None,
    area_type_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[RestrictedAreaSummary]:
    """Get all restricted areas with optional filtering"""
    statement = select(RestrictedAreas)

    if status_filter:
        statement = statement.where(RestrictedAreas.status == status_filter)

    if area_type_filter:
        statement = statement.where(RestrictedAreas.area_type == area_type_filter)

    statement = (
        statement.offset(offset)
        .limit(limit)
        .order_by(RestrictedAreas.created_at.desc())
    )

    restricted_areas = db.exec(statement).all()

    return [
        RestrictedAreaSummary(
            id=area.id,
            name=area.name,
            area_type=area.area_type,
            status=area.status,
            severity_level=area.severity_level,
            created_at=area.created_at,
        )
        for area in restricted_areas
    ]


async def update_restricted_area(
    area_id: int, area_data: RestrictedAreaUpdate, db: Session
) -> RestrictedAreaResponse:
    """Update an existing restricted area"""
    statement = select(RestrictedAreas).where(RestrictedAreas.id == area_id)
    restricted_area = db.exec(statement).first()

    if not restricted_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restricted area not found"
        )

    try:
        # Update basic fields
        for field, value in area_data.model_dump(exclude_unset=True).items():
            if field != "boundary_coordinates" and hasattr(restricted_area, field):
                setattr(restricted_area, field, value)

        restricted_area.updated_at = datetime.utcnow()

        # Update geometry if coordinates provided
        if area_data.boundary_coordinates:
            wkt_polygon = coordinates_to_wkt_polygon(area_data.boundary_coordinates)
            db.execute(
                text(f"""
                    UPDATE restricted_areas 
                    SET boundary = ST_GeomFromText('{wkt_polygon}', 4326)
                    WHERE id = :area_id
                """),
                {"area_id": area_id},
            )

        db.commit()
        db.refresh(restricted_area)

        return await get_restricted_area_by_id(area_id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update restricted area: {str(e)}",
        )


async def delete_restricted_area(area_id: int, db: Session) -> bool:
    """Delete a restricted area"""
    statement = select(RestrictedAreas).where(RestrictedAreas.id == area_id)
    restricted_area = db.exec(statement).first()

    if not restricted_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Restricted area not found"
        )

    try:
        db.delete(restricted_area)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete restricted area: {str(e)}",
        )


async def check_location_restrictions_shapely(
    longitude: float, latitude: float, db: Session, user_id: Optional[int] = None
) -> GeofenceCheckResponse:
    """Check if a location is within any restricted areas using Shapely for geometry operations"""
    try:
        # Create a Shapely Point for the location
        location_point = Point(longitude, latitude)

        # Get all active restricted areas with their WKT boundaries
        result = db.execute(
            text("""
                SELECT id, name, area_type, status, severity_level, 
                       send_warning_notification, auto_alert_authorities,
                       buffer_distance_meters, ST_AsText(boundary) as wkt_boundary
                FROM restricted_areas
                WHERE status = 'active'
                AND (valid_from IS NULL OR valid_from <= NOW())
                AND (valid_until IS NULL OR valid_until > NOW())
                ORDER BY severity_level DESC
            """)
        ).fetchall()

        restricted_areas = []
        warnings = []
        max_severity = 0
        is_restricted = False

        for row in result:
            try:
                # Parse the WKT boundary using Shapely
                area_polygon = loads(row.wkt_boundary)

                # Check if point is inside the polygon
                is_inside = area_polygon.contains(location_point)

                # Check if point is within buffer distance
                buffer_distance = row.buffer_distance_meters or 100
                is_in_buffer = (
                    location_point.distance(area_polygon) <= buffer_distance / 111000
                )  # Rough conversion to degrees

                if is_inside:
                    is_restricted = True
                    warnings.append(
                        f"You are currently in a restricted {row.area_type.replace('_', ' ')}: {row.name}"
                    )

                    # Log violation if user_id provided
                    if user_id:
                        await log_geofence_violation(
                            user_id=user_id,
                            restricted_area_id=row.id,
                            longitude=longitude,
                            latitude=latitude,
                            violation_type="entry",
                            db=db,
                        )
                elif is_in_buffer:
                    warnings.append(
                        f"Warning: You are approaching a restricted {row.area_type.replace('_', ' ')}: {row.name}"
                    )

                if is_inside or is_in_buffer:
                    max_severity = max(max_severity, row.severity_level)
                    restricted_areas.append(
                        RestrictedAreaSummary(
                            id=row.id,
                            name=row.name,
                            area_type=row.area_type,
                            status=row.status,
                            severity_level=row.severity_level,
                            created_at=datetime.utcnow(),
                        )
                    )

            except Exception as polygon_error:
                # Log error but continue with other areas
                print(f"Error processing polygon for area {row.id}: {polygon_error}")
                continue

        return GeofenceCheckResponse(
            is_restricted=is_restricted,
            restricted_areas=restricted_areas,
            warnings=warnings,
            severity_level=max_severity,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check location restrictions: {str(e)}",
        )


async def check_location_restrictions(
    longitude: float, latitude: float, db: Session, user_id: Optional[int] = None
) -> GeofenceCheckResponse:
    """Check if a location is within any restricted areas"""
    try:
        # Query for intersecting restricted areas
        result = db.execute(
            text("""
                SELECT id, name, area_type, status, severity_level, 
                       send_warning_notification, auto_alert_authorities,
                       ST_Contains(boundary, ST_Point(:lon, :lat)) as is_inside,
                       ST_Distance(boundary, ST_Point(:lon, :lat)) as distance_meters
                FROM restricted_areas
                WHERE status = 'active'
                AND (valid_from IS NULL OR valid_from <= NOW())
                AND (valid_until IS NULL OR valid_until > NOW())
                AND (
                    ST_Contains(boundary, ST_Point(:lon, :lat))
                    OR ST_DWithin(boundary, ST_Point(:lon, :lat), COALESCE(buffer_distance_meters, 100))
                )
                ORDER BY severity_level DESC, distance_meters ASC
            """),
            {"lon": longitude, "lat": latitude},
        ).fetchall()

        restricted_areas = []
        warnings = []
        max_severity = 0
        is_restricted = False

        for row in result:
            if row.is_inside:
                is_restricted = True
                warnings.append(
                    f"You are currently in a restricted {row.area_type.replace('_', ' ')}: {row.name}"
                )

                # Log violation if user_id provided
                if user_id:
                    await log_geofence_violation(
                        user_id=user_id,
                        restricted_area_id=row.id,
                        longitude=longitude,
                        latitude=latitude,
                        violation_type="entry",
                        db=db,
                    )
            else:
                warnings.append(
                    f"Warning: You are approaching a restricted {row.area_type.replace('_', ' ')}: {row.name}"
                )

            max_severity = max(max_severity, row.severity_level)

            restricted_areas.append(
                RestrictedAreaSummary(
                    id=row.id,
                    name=row.name,
                    area_type=row.area_type,
                    status=row.status,
                    severity_level=row.severity_level,
                    created_at=datetime.utcnow(),  # This would normally come from the actual timestamp
                )
            )

        return GeofenceCheckResponse(
            is_restricted=is_restricted,
            restricted_areas=restricted_areas,
            warnings=warnings,
            severity_level=max_severity,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check location restrictions: {str(e)}",
        )


async def log_geofence_violation(
    user_id: int,
    restricted_area_id: int,
    longitude: float,
    latitude: float,
    violation_type: str,
    db: Session,
    trip_id: Optional[int] = None,
) -> GeofenceViolations:
    """Log a geofence violation"""
    try:
        violation = GeofenceViolations(
            user_id=user_id,
            restricted_area_id=restricted_area_id,
            trip_id=trip_id,
            violation_type=violation_type,
            notification_sent=False,
            authorities_alerted=False,
            severity_score=1,  # This could be calculated based on area severity and violation type
        )

        db.add(violation)
        db.flush()

        # Set the violation location geometry
        db.execute(
            text("""
                UPDATE geofence_violations 
                SET violation_location = ST_Point(:lon, :lat)
                WHERE id = :violation_id
            """),
            {
                "lon": float(longitude),
                "lat": float(latitude),
                "violation_id": violation.id,
            },
        )

        db.commit()
        db.refresh(violation)

        return violation

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log geofence violation: {str(e)}",
        )
