import fastapi
from contextlib import asynccontextmanager
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.trek import router as trek_router
from app.api.v1.routes.trips import router as trips_router
from app.models.database.base import create_db_and_tables

# Import all models to ensure they are registered with SQLModel.metadata
from app.models import User, RefreshToken, Trek  # noqa: F401


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    # Create tables on startup
    create_db_and_tables()
    yield


app = fastapi.FastAPI(title="SIH Backend API", version="1.0.0", lifespan=lifespan)

app.include_router(router=auth_router)
app.include_router(router=trek_router)
app.include_router(router=trips_router)
