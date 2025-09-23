from sqlmodel import Session, select, func
from app.models.database.alerts import Alert, AlertStatusEnum, AlertTypeEnum
from app.models.schemas.alerts import (
    AlertCreate,
)
from typing import Optional, List, Tuple, Dict, Any
import datetime
import math
from geoalchemy2.shape import to_shape


def _serialize_geometry_to_lat_lng(alert: Alert) -> Dict[str, Any]:
    """Convert Alert with geometry to dict with latitude/longitude."""
    alert_data = alert.dict()

    if hasattr(alert, "location") and alert.location:
        try:
            point = to_shape(alert.location)
            alert_data["latitude"] = point.y
            alert_data["longitude"] = point.x
        except Exception:
            alert_data["latitude"] = None
            alert_data["longitude"] = None
    else:
        alert_data["latitude"] = None
        alert_data["longitude"] = None

    # Remove the geometry field from response
    alert_data.pop("location", None)
    return alert_data


async def create_alert(
    alert_data: AlertCreate, user_id: int, db: Session
) -> Dict[str, Any]:
    """Create a new alert by user."""
    try:
        data = alert_data.model_dump()

        # Handle location
        latitude = data.pop("latitude")
        longitude = data.pop("longitude")

        # WKT format: POINT(longitude latitude)
        wkt_point = f"POINT({longitude} {latitude})"
        data["location"] = wkt_point

        alert = Alert(
            **data,
            created_by=user_id,
            status=AlertStatusEnum.ACTIVE,
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        return _serialize_geometry_to_lat_lng(alert)
    except Exception as e:
        db.rollback()
        raise e


async def get_alert_by_id(alert_id: int, db: Session) -> Optional[Dict[str, Any]]:
    """Get an alert by ID."""
    try:
        statement = select(Alert).where(Alert.id == alert_id)
        alert = db.exec(statement).first()

        if not alert:
            return None

        return _serialize_geometry_to_lat_lng(alert)
    except Exception as e:
        raise e


async def resolve_alert(
    alert_id: int, admin_id: int, db: Session
) -> Optional[Dict[str, Any]]:
    """Mark an alert as resolved (admin only)."""
    try:
        statement = select(Alert).where(Alert.id == alert_id)
        alert = db.exec(statement).first()

        if not alert:
            return None

        alert.status = AlertStatusEnum.RESOLVED
        alert.resolved_by = admin_id
        alert.resolved_at = datetime.datetime.now(datetime.timezone.utc)

        db.add(alert)
        db.commit()
        db.refresh(alert)

        return _serialize_geometry_to_lat_lng(alert)
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


async def get_all_alerts(
    page: int = 1,
    page_size: int = 20,
    alert_type: Optional[AlertTypeEnum] = None,
    status: Optional[AlertStatusEnum] = None,
    db: Session = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """Get all alerts with filtering and pagination."""
    try:
        statement = select(Alert)

        # Apply filters
        if alert_type:
            statement = statement.where(Alert.alert_type == alert_type)

        if status:
            statement = statement.where(Alert.status == status)

        # Get total count
        all_alerts = db.exec(statement).all()
        total_count = len(all_alerts)

        # Apply pagination
        offset = (page - 1) * page_size
        paginated_statement = statement.offset(offset).limit(page_size)
        alerts = db.exec(paginated_statement).all()

        # Serialize alerts
        serialized_alerts = [_serialize_geometry_to_lat_lng(alert) for alert in alerts]

        return serialized_alerts, total_count

    except Exception as e:
        raise e


async def get_nearby_alerts(
    latitude: float,
    longitude: float,
    radius_km: float,
    db: Session,
    limit: int = 20,
    status: Optional[AlertStatusEnum] = AlertStatusEnum.ACTIVE,
) -> List[Dict[str, Any]]:
    """Get alerts within a radius of given coordinates."""
    try:
        # Get alerts with optional status filter
        statement = select(Alert)
        if status:
            statement = statement.where(Alert.status == status)

        all_alerts = db.exec(statement).all()

        # Filter by distance
        nearby_alerts = []
        for alert in all_alerts:
            if hasattr(alert, "location") and alert.location:
                try:
                    point = to_shape(alert.location)
                    distance = calculate_distance(latitude, longitude, point.y, point.x)
                    if distance <= radius_km:
                        nearby_alerts.append((alert, distance))
                except Exception:
                    continue

        # Sort by distance and apply limit
        nearby_alerts.sort(key=lambda x: x[1])
        limited_alerts = nearby_alerts[:limit]

        # Serialize results
        return [_serialize_geometry_to_lat_lng(alert[0]) for alert in limited_alerts]

    except Exception as e:
        raise e


async def get_admin_alert_stats(db: Session) -> Dict[str, Any]:
    """Get alert statistics for admin dashboard."""
    try:
        # Total alerts
        total_count = db.exec(select(func.count(Alert.id))).first()

        # Active alerts
        active_count = db.exec(
            select(func.count(Alert.id)).where(Alert.status == AlertStatusEnum.ACTIVE)
        ).first()

        # Alerts by type
        type_stats = {}
        for alert_type in AlertTypeEnum:
            count = db.exec(
                select(func.count(Alert.id)).where(Alert.alert_type == alert_type)
            ).first()
            type_stats[alert_type.value] = count

        # Alerts by status
        status_stats = {}
        for status in AlertStatusEnum:
            count = db.exec(
                select(func.count(Alert.id)).where(Alert.status == status)
            ).first()
            status_stats[status.value] = count

        return {
            "total_alerts": total_count,
            "active_alerts": active_count,
            "alerts_by_type": type_stats,
            "alerts_by_status": status_stats,
        }

    except Exception as e:
        raise e
