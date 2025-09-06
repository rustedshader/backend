# Import all SQLModel models to ensure they are registered with SQLModel.metadata
from app.models.database.user import User, RefreshToken, UserRoleEnum
from app.models.database.trek import Trek, DifficultyLevelEnum

__all__ = ["User", "RefreshToken", "UserRoleEnum", "Trek", "DifficultyLevelEnum"]
