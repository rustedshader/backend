from .user import User, UserRoleEnum, RefreshToken
from .guides import Guides, GuideCertificationLevelEnum, GuideSpecialtyEnum
from .online_activity import OnlineActivity, OnlineActivityTypeEnum
from .offline_activity import (
    OfflineActivity,
    OfflineActivityRouteData,
    DifficultyLevelEnum,
)
from .tracking_device import TrackingDevice, TrackingDeviceStatusEnum
from .trips import (
    Trips,
    TripStatusEnum,
)
from .location_history import LocationHistory
from .itinerary import Itinerary, ItineraryDay
from .geofencing import (
    RestrictedAreas,
    GeofenceViolations,
    RestrictedAreaStatusEnum,
    RestrictedAreaTypeEnum,
)
from .accommodation import Accommodation

__all__ = [
    # User models
    "User",
    "UserRoleEnum",
    "RefreshToken",
    # Guide models
    "Guides",
    "GuideCertificationLevelEnum",
    "GuideSpecialtyEnum",
    # Online Activity models
    "OnlineActivity",
    "OnlineActivityTypeEnum",
    # Offline Activity models
    "OfflineActivity",
    "OfflineActivityRouteData",
    "DifficultyLevelEnum",
    # Tracking device models
    "TrackingDevice",
    "TrackingDeviceStatusEnum",
    # Trip models
    "Trips",
    "TripStatusEnum",
    "LocationHistory",
    # Itinerary models
    "Itinerary",
    "ItineraryDay",
    # Geofencing models
    "RestrictedAreas",
    "GeofenceViolations",
    "RestrictedAreaStatusEnum",
    "RestrictedAreaTypeEnum",
    "Accommodation",
]
