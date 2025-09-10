from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Optional
from app.models.database.base import get_db
from app.models.schemas.test_coordinates import (
    TestCoordinatesCreate,
    TestCoordinatesResponse,
)
from app.services.test_coordinates import TestCoordinatesService

router = APIRouter(prefix="/test-coordinates", tags=["Test Coordinates"])


@router.post("/", response_model=TestCoordinatesResponse, status_code=201)
async def create_test_coordinates(
    coordinates: TestCoordinatesCreate, db: Session = Depends(get_db)
):
    """
    Create new test coordinates entry.
    No authentication required - for IoT device testing.
    """
    try:
        result = TestCoordinatesService.create_coordinates(db, coordinates)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save coordinates: {str(e)}"
        )


@router.get("/", response_model=List[TestCoordinatesResponse])
async def get_test_coordinates(
    limit: int = 100, device_id: Optional[str] = None, db: Session = Depends(get_db)
):
    """
    Get test coordinates.
    - limit: Maximum number of records to return (default: 100)
    - device_id: Optional filter by device ID
    """
    try:
        if device_id:
            results = TestCoordinatesService.get_coordinates_by_device(
                db, device_id, limit
            )
        else:
            results = TestCoordinatesService.get_all_coordinates(db, limit)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve coordinates: {str(e)}"
        )


@router.get("/latest", response_model=Optional[TestCoordinatesResponse])
async def get_latest_coordinates(
    device_id: Optional[str] = None, db: Session = Depends(get_db)
):
    """
    Get the most recent coordinates entry.
    - device_id: Optional filter by device ID
    """
    try:
        if device_id:
            results = TestCoordinatesService.get_coordinates_by_device(db, device_id, 1)
        else:
            results = TestCoordinatesService.get_all_coordinates(db, 1)

        return results[0] if results else None
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve latest coordinates: {str(e)}"
        )
