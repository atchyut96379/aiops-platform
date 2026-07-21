from __future__ import annotations

import math
import re
from typing import Sequence

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.repositories.knowledge_chunk import KnowledgeChunkRepository

logger = get_logger(__name__)

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100


def _split_text(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= CHUNK_SIZE:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= CHUNK_SIZE:
                current = para
            else:
                start = 0
                while start < len(para):
                    end = start + CHUNK_SIZE
                    chunks.append(para[start:end])
                    start = end - CHUNK_OVERLAP
                current = ""
    if current:
        chunks.append(current)
    return chunks or [text[:CHUNK_SIZE]]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RAGService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.chunks = KnowledgeChunkRepository(db)

    async def index_document(self, document: KnowledgeDocument) -> int:
        self.chunks.delete_for_document(document.id)
        pieces = _split_text(document.content)
        count = 0
        for idx, piece in enumerate(pieces):
            chunk = KnowledgeChunk(
                organization_id=document.organization_id,
                document_id=document.id,
                chunk_index=idx,
                content=piece,
                token_count=len(piece.split()),
            )
            if settings.ai_available:
                try:
                    chunk.embedding = await self._embed(piece)
                except Exception:
                    logger.exception("Failed to embed chunk for doc %s", document.id)
            self.chunks.add(chunk)
            count += 1
        self.db.commit()
        return count

    async def retrieve(
        self, organization_id: int, query: str, limit: int = 5
    ) -> Sequence[KnowledgeChunk]:
        all_chunks = self.chunks.list_for_organization(organization_id)
        if not all_chunks:
            return []

        embedded = [c for c in all_chunks if c.embedding]
        if settings.ai_available and embedded:
            try:
                query_vec = await self._embed(query)
                ranked = sorted(
                    embedded,
                    key=lambda c: _cosine_similarity(query_vec, c.embedding),
                    reverse=True,
                )
                return ranked[:limit]
            except Exception:
                logger.exception("Semantic search failed, falling back to keyword match")

        pattern = query.lower()
        keyword_hits = [
            c for c in all_chunks if pattern in c.content.lower()
        ]
        return keyword_hits[:limit]

    async def _embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.EMBEDDING_MODEL,
                    "input": text[:8000],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
