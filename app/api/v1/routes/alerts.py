from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from app.api.deps import get_current_user, get_db, get_current_admin_user
from app.models.database.user import User
from app.models.schemas.alerts import (
    AlertCreate,
    AlertUpdate,
    AlertResponse,
    AlertStatsResponse,
    AlertTypeEnum,
    AlertStatusEnum,
)
from app.services.alerts import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new alert.

    - Tourists can create alerts for their own trips
    - Guides can create alerts for trips they are guiding
    - Admins can create alerts for any trip
    """
    alert_service = AlertService(db)

    # TODO: Add validation to ensure user can create alerts for this trip
    # This would require checking if the user is the tourist, guide, or admin

    try:
        return alert_service.create_alert(alert_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create alert: {str(e)}")


@router.get("/emergency", response_model=List[AlertResponse])
async def get_emergency_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get all active emergency alerts.

    Admin only endpoint for monitoring emergency situations.
    """
    alert_service = AlertService(db)
    return alert_service.get_emergency_alerts()


@router.get("/statistics", response_model=AlertStatsResponse)
async def get_alert_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get alert statistics.

    Admin only endpoint for dashboard analytics.
    """
    alert_service = AlertService(db)
    return alert_service.get_alert_statistics()


@router.get("/trip/{trip_id}", response_model=List[AlertResponse])
async def get_trip_alerts(
    trip_id: int,
    status: Optional[AlertStatusEnum] = Query(
        None, description="Filter by alert status"
    ),
    alert_type: Optional[AlertTypeEnum] = Query(
        None, description="Filter by alert type"
    ),
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of alerts to return"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get alerts for a specific trip.

    - Tourists can view alerts for their own trips
    - Guides can view alerts for trips they are guiding
    - Admins can view alerts for any trip
    """
    alert_service = AlertService(db)

    # TODO: Add validation to ensure user can view alerts for this trip

    return alert_service.get_alerts_by_trip(
        trip_id=trip_id,
        status=status,
        alert_type=alert_type,
        skip=skip,
        limit=limit,
    )


@router.get("/", response_model=List[AlertResponse])
async def get_all_alerts(
    status: Optional[AlertStatusEnum] = Query(
        None, description="Filter by alert status"
    ),
    alert_type: Optional[AlertTypeEnum] = Query(
        None, description="Filter by alert type"
    ),
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of alerts to return"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get all alerts with optional filters.

    Admin only endpoint for monitoring all alerts across the system.
    """
    alert_service = AlertService(db)

    return alert_service.get_all_alerts(
        status=status,
        alert_type=alert_type,
        skip=skip,
        limit=limit,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific alert by ID.

    - Tourists can view alerts for their own trips
    - Guides can view alerts for trips they are guiding
    - Admins can view any alert
    """
    alert_service = AlertService(db)

    alert = alert_service.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # TODO: Add validation to ensure user can view this alert

    return alert


@router.patch("/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: int,
    status: AlertStatusEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update alert status (acknowledge, resolve, etc.).

    - Guides can acknowledge/resolve alerts for their trips
    - Admins can update any alert status
    """
    alert_service = AlertService(db)

    alert = alert_service.update_alert_status(alert_id, status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # TODO: Add validation to ensure user can update this alert

    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update alert details.

    - Alert creators can update their own alerts
    - Admins can update any alert
    """
    alert_service = AlertService(db)

    alert = alert_service.update_alert(alert_id, alert_update)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # TODO: Add validation to ensure user can update this alert

    return alert


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Delete an alert.

    Admin only endpoint for data cleanup.
    """
    alert_service = AlertService(db)

    success = alert_service.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"message": "Alert deleted successfully"}


# Convenience endpoints for common operations
@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Acknowledge an alert (shortcut for updating status to acknowledged).
    """
    alert_service = AlertService(db)

    alert = alert_service.update_alert_status(alert_id, AlertStatusEnum.ACKNOWLEDGED)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resolve an alert (shortcut for updating status to resolved).
    """
    alert_service = AlertService(db)

    alert = alert_service.update_alert_status(alert_id, AlertStatusEnum.RESOLVED)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert
