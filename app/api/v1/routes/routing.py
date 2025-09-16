from fastapi import APIRouter

router = APIRouter(prefix="/routing", tags=["routing"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}
