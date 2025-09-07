from app.models.schemas.treks import TrekCreate
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
