from typing import Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from app.db.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, db: Session, model: Type[ModelT]) -> None:
        self.db = db
        self.model = model

    def get(self, entity_id: int) -> Optional[ModelT]:
        return self.db.get(self.model, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.flush()
