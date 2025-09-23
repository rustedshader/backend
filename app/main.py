import fastapi
from contextlib import asynccontextmanager
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.offline_activity import router as trek_router
from app.api.v1.routes.trips import router as trips_router
from app.api.v1.routes.tracking_deivce import router as tracking_device_router
from app.api.v1.routes.guide import router as guide_router
from app.api.v1.routes.tourist_id import router as tourist_id_router
from app.api.v1.routes.admin import router as admin_router
from app.api.v1.routes.itinerary import router as itinerary_router
from app.api.v1.routes.online_activity import router as places_router
from app.api.v1.routes.routing import router as routing_router
from app.api.v1.routes.geofencing import router as geofencing_router
from app.api.v1.routes.accommodation import router as accommodation_router
from app.api.v1.routes.alerts import router as alerts_router
from app.models.database.base import create_db_and_tables


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    create_db_and_tables()
    yield


app = fastapi.FastAPI(title="SIH Backend API", version="1.0.0", lifespan=lifespan)

app.include_router(router=auth_router)
app.include_router(router=guide_router)
app.include_router(router=itinerary_router)
app.include_router(router=trips_router)
app.include_router(router=trek_router)
app.include_router(router=places_router)
app.include_router(router=accommodation_router)
app.include_router(router=tracking_device_router)
app.include_router(router=tourist_id_router)
app.include_router(router=routing_router)
app.include_router(router=geofencing_router)
app.include_router(router=alerts_router)
app.include_router(router=admin_router)
