import fastapi
from app.api.v1.routes.auth import router as auth_router

app = fastapi.FastAPI(
    title="SIH Backend API",
    version="1.0.0",
)

app.include_router(router=auth_router)
