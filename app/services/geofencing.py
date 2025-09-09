from sqlmodel import Session, select
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import text
from datetime import datetime

from app.models.database.geofencing import RestrictedAreas, GeofenceViolations
from app.models.schemas.geofencing import (
    RestrictedAreaCreate,
    RestrictedAreaUpdate,
    RestrictedAreaResponse,
    RestrictedAreaSummary,
    GeofenceCheckResponse,
    PolygonCoordinate,
)


def coordinates_to_wkt_polygon(coordinates: List[PolygonCoordinate]) -> str:
    """Convert coordinate list to WKT POLYGON string for PostGIS"""
    if len(coordinates) < 3:
        raise ValueError("Polygon must have at least 3 coordinates")

    # Ensure polygon is closed (first and last point are the same)
    coord_pairs = [(coord.longitude, coord.latitude) for coord in coordinates]
    if coord_pairs[0] != coord_pairs[-1]:
        coord_pairs.append(coord_pairs[0])

    # Create WKT string
    coord_string = ", ".join([f"{lon} {lat}" for lon, lat in coord_pairs])
    return f"POLYGON(({coord_string}))"


def wkt_polygon_to_coordinates(wkt_polygon: str) -> List[PolygonCoordinate]:
    """Convert WKT POLYGON string to coordinate list"""
    # Remove POLYGON(( and )) from the string
    coord_string = wkt_polygon.replace("POLYGON((", "").replace("))", "")

    # Split coordinates and convert to PolygonCoordinate objects
    coordinates = []
    for coord_pair in coord_string.split(", "):
        lon, lat = map(float, coord_pair.split())
        coordinates.append(PolygonCoordinate(longitude=lon, latitude=lat))

    # Remove the last coordinate if it's the same as the first (closing coordinate)
    if len(coordinates) > 1 and coordinates[0] == coordinates[-1]:
        coordinates.pop()

    return coordinates


async def create_restricted_area(
    area_data: RestrictedAreaCreate, admin_user_id: int, db: Session
) -> RestrictedAreaResponse:
    """Create a new restricted area"""
    try:
        # Convert coordinates to PostGIS geometry
        wkt_polygon = coordinates_to_wkt_polygon(area_data.boundary_coordinates)

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

        # Set the geometry using raw SQL
        db.add(restricted_area)
        db.flush()  # Get the ID

        # Update with geometry
        db.execute(
            text(f"""
                UPDATE restricted_areas 
                SET boundary = ST_GeomFromText('{wkt_polygon}', 4326)
                WHERE id = :area_id
            """),
            {"area_id": restricted_area.id},
        )

        db.commit()
        db.refresh(restricted_area)

        # Convert to response format
        return await get_restricted_area_by_id(restricted_area.id, db)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log geofence violation: {str(e)}",
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
            {"lon": longitude, "lat": latitude, "violation_id": violation.id},
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
