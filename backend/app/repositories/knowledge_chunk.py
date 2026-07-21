from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.repositories.base import BaseRepository


class KnowledgeChunkRepository(BaseRepository[KnowledgeChunk]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, KnowledgeChunk)

    def list_for_organization(self, organization_id: int) -> Sequence[KnowledgeChunk]:
        stmt = select(KnowledgeChunk).where(KnowledgeChunk.organization_id == organization_id)
        return self.db.scalars(stmt).all()

    def list_for_document(self, document_id: int) -> Sequence[KnowledgeChunk]:
        stmt = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index)
        )
        return self.db.scalars(stmt).all()

    def delete_for_document(self, document_id: int) -> None:
        self.db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document_id))
        self.db.flush()
