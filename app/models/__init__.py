# Import all SQLModel models to ensure they are registered with SQLModel.metadata
from app.models.database.user import User, RefreshToken, UserRoleEnum
from app.models.database.offline_activity import (
    Trek,
    DifficultyLevelEnum,
    TrekRouteData,
)
from app.models.database.trips import (
    Trips,
    TripStatusEnum,
)
from app.models.database.location_history import LocationHistory
from app.models.database.guides import (
    Guides,
    GuideCertificationLevelEnum,
    GuideSpecialtyEnum,
    GuideTrek,
)
from app.models.database.tracking_device import TrackingDevice, TrackingDeviceStatusEnum


__all__ = [
    "User",
    "RefreshToken",
    "UserRoleEnum",
    "Trek",
    "DifficultyLevelEnum",
    "TrekRouteData",
    "Trips",
    "TripStatusEnum",
    "LocationHistory",
    "Guides",
    "GuideCertificationLevelEnum",
    "GuideSpecialtyEnum",
    "GuideTrek",
    "TrackingDevice",
    "TrackingDeviceStatusEnum",
]
