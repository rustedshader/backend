from app.models.schemas.treks import TrekCreate, TrekUpdate
from app.models.database.treks import Trek
from sqlmodel import select, Session


async def create_trecks(
    created_by_id: int, treck_create_data: TrekCreate, db: Session
) -> Trek:
    try:
        new_trek = Trek(**treck_create_data.model_dump())
        new_trek.created_by_id = created_by_id
        db.add(new_trek)
        db.commit()
        db.refresh(new_trek)
        return new_trek
    except Exception as e:
        db.rollback()
        raise e


async def get_trek_by_id(trek_id: int, db: Session) -> Trek | None:
    statement = select(Trek).where(Trek.id == trek_id)
    trek = db.exec(statement).first()
    return trek


async def update_trek(
    trek_id: int, trek_update_data: TrekUpdate, db: Session
) -> Trek | None:
    try:
        # Get the existing trek
        statement = select(Trek).where(Trek.id == trek_id)
        trek = db.exec(statement).first()

        if not trek:
            return None

        # Update only the fields that are provided (not None)
        update_data = trek_update_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trek, field, value)

        db.add(trek)
        db.commit()
        db.refresh(trek)
        return trek
    except Exception as e:
        db.rollback()
        raise e
