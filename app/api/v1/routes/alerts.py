from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from typing import List, Optional
from app.api.deps import get_db, get_current_user, get_current_admin_user
from app.models.database.user import User
from app.models.database.alerts import AlertTypeEnum, AlertStatusEnum

from app.models.schemas.alerts import (
    AlertCreate,
    AlertResponse,
    AlertListResponse,
    AlertStatsResponse,
)
from app.services import alerts as alerts_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


# User endpoints
@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new alert by user."""
    try:
        alert = await alerts_service.create_alert(
            alert_data, current_user.id, db
        )
        return AlertResponse.model_validate(alert)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create alert: {str(e)}",
        )


@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    alert_type: Optional[AlertTypeEnum] = Query(None),
    status_filter: Optional[AlertStatusEnum] = Query(AlertStatusEnum.ACTIVE),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get alerts with optional filters and pagination."""
    try:
        alerts, total_count = await alerts_service.get_all_alerts(
            page=page,
            page_size=page_size,
            alert_type=alert_type,
            status=status_filter,
            db=db,
        )

        alert_responses = [
            AlertResponse.model_validate(alert) for alert in alerts
        ]

        return AlertListResponse(
            alerts=alert_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts: {str(e)}",
        )


@router.get("/nearby", response_model=List[AlertResponse])
async def get_nearby_alerts(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, ge=0.1, le=100),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get active alerts within a radius of given coordinates."""
    try:
        alerts = await alerts_service.get_nearby_alerts(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            db=db,
            limit=limit,
            status=AlertStatusEnum.ACTIVE,
        )
        return [
            AlertResponse.model_validate(alert) for alert in alerts
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search nearby alerts: {str(e)}",
        )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific alert by ID."""
    try:
        alert = await alerts_service.get_alert_by_id(alert_id, db)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Alert not found"
            )

        return AlertResponse.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alert: {str(e)}",
        )


# Admin endpoints
@router.get("/admin/all", response_model=AlertListResponse)
async def get_all_alerts_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    alert_type: Optional[AlertTypeEnum] = Query(None),
    status_filter: Optional[AlertStatusEnum] = Query(None),
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get all alerts for admin dashboard with filtering and pagination."""
    try:
        alerts, total_count = await alerts_service.get_all_alerts(
            page=page,
            page_size=page_size,
            alert_type=alert_type,
            status=status_filter,
            db=db,
        )

        alert_responses = [
            AlertResponse.model_validate(alert) for alert in alerts
        ]

        return AlertListResponse(
            alerts=alert_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alerts for admin: {str(e)}",
        )


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Mark an alert as resolved (admin only)."""
    try:
        alert = await alerts_service.resolve_alert(
            alert_id, current_admin.id, db
        )
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Alert not found"
            )

        return AlertResponse.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}",
        )


@router.get("/admin/stats", response_model=AlertStatsResponse)
async def get_admin_alert_stats(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get alert statistics for admin dashboard."""
    try:
        stats = await alerts_service.get_admin_alert_stats(db)
        return AlertStatsResponse.model_validate(stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch alert statistics: {str(e)}",
        )