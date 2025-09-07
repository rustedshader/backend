from fastapi import APIRouter, Depends, status, HTTPException
from deps import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])
