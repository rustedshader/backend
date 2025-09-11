# Import all SQLModel models to ensure they are registered with SQLModel.metadata
from app.models.database.user import User, RefreshToken, UserRoleEnum
from app.models.database.treks import Trek, DifficultyLevelEnum, TrekRouteData
from app.models.database.trips import (
    Trips,
    TripStatusEnum,
    AlertTypeEnum,
    AlertStatusEnum,
    Alerts,
    LocationHistory,
)
from app.models.database.guides import (
    Guides,
    GuideCertificationLevelEnum,
    GuideSpecialtyEnum,
    GuideTrek,
)
from app.models.database.tracking_device import TrackingDevice, TrackingDeviceStatusEnum
from app.models.database.location_sharing import LocationShareHistory


__all__ = [
    "User",
    "RefreshToken",
    "UserRoleEnum",
    "Trek",
    "DifficultyLevelEnum",
    "TrekRouteData",
    "Trips",
    "TripStatusEnum",
    "AlertTypeEnum",
    "AlertStatusEnum",
    "Alerts",
    "LocationHistory",
    "Guides",
    "GuideCertificationLevelEnum",
    "GuideSpecialtyEnum",
    "GuideTrek",
    "TrackingDevice",
    "TrackingDeviceStatusEnum",
    "LocationShareHistory",
]
