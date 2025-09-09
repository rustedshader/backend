from sqlmodel import Session, select, func
from typing import List, Optional
from geoalchemy2.functions import ST_GeomFromText

from app.models.database.trips import Alerts, AlertTypeEnum, AlertStatusEnum
from app.models.schemas.alerts import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertCoordinates,
    AlertStatsResponse,
)
import datetime


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def create_alert(self, alert_data: AlertCreate) -> AlertResponse:
        """Create a new alert."""
        # Convert coordinates to WKT POINT format
        location_wkt = (
            f"POINT({alert_data.location.longitude} {alert_data.location.latitude})"
        )

        db_alert = Alerts(
            trip_id=alert_data.trip_id,
            alert_type=alert_data.alert_type,
            description=alert_data.description,
            location=ST_GeomFromText(location_wkt, 4326),
            timestamp=int(datetime.datetime.utcnow().timestamp()),
            status=AlertStatusEnum.NEW,
        )

        self.db.add(db_alert)
        self.db.commit()
        self.db.refresh(db_alert)

        return self._convert_to_response(db_alert)

    def get_alert_by_id(self, alert_id: int) -> Optional[AlertResponse]:
        """Get alert by ID."""
        statement = select(Alerts).where(Alerts.id == alert_id)
        alert = self.db.exec(statement).first()

        if not alert:
            return None

        return self._convert_to_response(alert)

    def get_alerts_by_trip(
        self,
        trip_id: int,
        status: Optional[AlertStatusEnum] = None,
        alert_type: Optional[AlertTypeEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AlertResponse]:
        """Get alerts for a specific trip with optional filters."""
        statement = select(Alerts).where(Alerts.trip_id == trip_id)

        if status:
            statement = statement.where(Alerts.status == status)
        if alert_type:
            statement = statement.where(Alerts.alert_type == alert_type)

        statement = (
            statement.order_by(Alerts.timestamp.desc()).offset(skip).limit(limit)
        )

        alerts = self.db.exec(statement).all()
        return [self._convert_to_response(alert) for alert in alerts]

    def get_all_alerts(
        self,
        status: Optional[AlertStatusEnum] = None,
        alert_type: Optional[AlertTypeEnum] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AlertResponse]:
        """Get all alerts with optional filters."""
        statement = select(Alerts)

        if status:
            statement = statement.where(Alerts.status == status)
        if alert_type:
            statement = statement.where(Alerts.alert_type == alert_type)

        statement = (
            statement.order_by(Alerts.timestamp.desc()).offset(skip).limit(limit)
        )

        alerts = self.db.exec(statement).all()
        return [self._convert_to_response(alert) for alert in alerts]

    def update_alert_status(
        self, alert_id: int, status: AlertStatusEnum
    ) -> Optional[AlertResponse]:
        """Update alert status."""
        statement = select(Alerts).where(Alerts.id == alert_id)
        alert = self.db.exec(statement).first()

        if not alert:
            return None

        alert.status = status
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        return self._convert_to_response(alert)

    def update_alert(
        self, alert_id: int, alert_update: AlertUpdate
    ) -> Optional[AlertResponse]:
        """Update alert details."""
        statement = select(Alerts).where(Alerts.id == alert_id)
        alert = self.db.exec(statement).first()

        if not alert:
            return None

        if alert_update.alert_type is not None:
            alert.alert_type = alert_update.alert_type
        if alert_update.description is not None:
            alert.description = alert_update.description
        if alert_update.status is not None:
            alert.status = alert_update.status

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        return self._convert_to_response(alert)

    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert."""
        statement = select(Alerts).where(Alerts.id == alert_id)
        alert = self.db.exec(statement).first()

        if not alert:
            return False

        self.db.delete(alert)
        self.db.commit()
        return True

    def get_emergency_alerts(self) -> List[AlertResponse]:
        """Get all emergency alerts that are new or acknowledged."""
        statement = (
            select(Alerts)
            .where(Alerts.alert_type == AlertTypeEnum.EMERGENCY)
            .where(
                Alerts.status.in_([AlertStatusEnum.NEW, AlertStatusEnum.ACKNOWLEDGED])
            )
            .order_by(Alerts.timestamp.desc())
        )

        alerts = self.db.exec(statement).all()
        return [self._convert_to_response(alert) for alert in alerts]

    def get_alert_statistics(self) -> AlertStatsResponse:
        """Get statistics about alerts."""
        total_alerts = self.db.exec(select(func.count(Alerts.id))).first() or 0

        new_alerts = (
            self.db.exec(
                select(func.count(Alerts.id)).where(
                    Alerts.status == AlertStatusEnum.NEW
                )
            ).first()
            or 0
        )

        acknowledged_alerts = (
            self.db.exec(
                select(func.count(Alerts.id)).where(
                    Alerts.status == AlertStatusEnum.ACKNOWLEDGED
                )
            ).first()
            or 0
        )

        resolved_alerts = (
            self.db.exec(
                select(func.count(Alerts.id)).where(
                    Alerts.status == AlertStatusEnum.RESOLVED
                )
            ).first()
            or 0
        )

        emergency_alerts = (
            self.db.exec(
                select(func.count(Alerts.id)).where(
                    Alerts.alert_type == AlertTypeEnum.EMERGENCY
                )
            ).first()
            or 0
        )

        deviation_alerts = (
            self.db.exec(
                select(func.count(Alerts.id)).where(
                    Alerts.alert_type == AlertTypeEnum.DEVIATION
                )
            ).first()
            or 0
        )

        weather_alerts = (
            self.db.exec(
                select(func.count(Alerts.id)).where(
                    Alerts.alert_type == AlertTypeEnum.WEATHER
                )
            ).first()
            or 0
        )

        other_alerts = (
            self.db.exec(
                select(func.count(Alerts.id)).where(
                    Alerts.alert_type == AlertTypeEnum.OTHER
                )
            ).first()
            or 0
        )

        return AlertStatsResponse(
            total_alerts=total_alerts,
            new_alerts=new_alerts,
            acknowledged_alerts=acknowledged_alerts,
            resolved_alerts=resolved_alerts,
            emergency_alerts=emergency_alerts,
            deviation_alerts=deviation_alerts,
            weather_alerts=weather_alerts,
            other_alerts=other_alerts,
        )

    def _convert_to_response(self, alert: Alerts) -> AlertResponse:
        """Convert database alert to response model."""
        # Extract coordinates from PostGIS geometry
        # Note: This assumes the location is stored as a POINT geometry
        # In a real implementation, you might want to use ST_X and ST_Y functions
        # For now, we'll use a placeholder approach
        from geoalchemy2.shape import to_shape

        if alert.location:
            point = to_shape(alert.location)
            coordinates = AlertCoordinates(latitude=point.y, longitude=point.x)
        else:
            coordinates = AlertCoordinates(latitude=0.0, longitude=0.0)

        return AlertResponse(
            id=alert.id,
            trip_id=alert.trip_id,
            timestamp=alert.timestamp,
            alert_type=alert.alert_type,
            description=alert.description,
            location=coordinates,
            status=alert.status,
        )
