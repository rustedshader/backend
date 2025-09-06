import fastapi
from app.api.v1.routes.auth import router

app = fastapi.FastAPI()

app.include_router(router=router)
