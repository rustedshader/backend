from sqlmodel import Session, select
from typing import List
from app.models.database.test_coordinates import TestCoordinates
from app.models.schemas.test_coordinates import TestCoordinatesCreate


class TestCoordinatesService:
    @staticmethod
    def create_coordinates(
        db: Session, coordinates_data: TestCoordinatesCreate
    ) -> TestCoordinates:
        """Create new test coordinates entry"""
        db_coordinates = TestCoordinates(
            latitude=coordinates_data.latitude,
            longitude=coordinates_data.longitude,
            device_id=coordinates_data.device_id,
        )
        db.add(db_coordinates)
        db.commit()
        db.refresh(db_coordinates)
        return db_coordinates

    @staticmethod
    def get_all_coordinates(db: Session, limit: int = 100) -> List[TestCoordinates]:
        """Get all test coordinates with optional limit"""
        statement = (
            select(TestCoordinates)
            .order_by(TestCoordinates.timestamp.desc())
            .limit(limit)
        )
        results = db.exec(statement)
        return list(results)

    @staticmethod
    def get_coordinates_by_device(
        db: Session, device_id: str, limit: int = 100
    ) -> List[TestCoordinates]:
        """Get coordinates for a specific device"""
        statement = (
            select(TestCoordinates)
            .where(TestCoordinates.device_id == device_id)
            .order_by(TestCoordinates.timestamp.desc())
            .limit(limit)
        )
        results = db.exec(statement)
        return list(results)
