from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.repositories.base import BaseRepository


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, KnowledgeDocument)

    def list_for_organization(
        self,
        organization_id: int,
        *,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.organization_id == organization_id
        )
        if category:
            stmt = stmt.where(KnowledgeDocument.category == category)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                KnowledgeDocument.title.ilike(pattern) | KnowledgeDocument.content.ilike(pattern)
            )
        return self.db.scalars(stmt.order_by(KnowledgeDocument.title).offset(skip).limit(limit)).all()

    def search_content(self, organization_id: int, query: str, limit: int = 5) -> Sequence[KnowledgeDocument]:
        pattern = f"%{query}%"
        stmt = (
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.organization_id == organization_id,
                KnowledgeDocument.title.ilike(pattern) | KnowledgeDocument.content.ilike(pattern),
            )
            .limit(limit)
        )
        return self.db.scalars(stmt).all()
