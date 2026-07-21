from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, ValidationAppError
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.knowledge_document import KnowledgeDocumentRepository
from app.repositories.role import UserRoleRepository
from app.schemas.ai import AIAnalysisResponse, AIChatRequest, AIChatResponse, LogAnalysisRequest
from app.services.rag import RAGService

logger = get_logger(__name__)


class AIService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.knowledge = KnowledgeDocumentRepository(db)
        self.memberships = UserRoleRepository(db)
        self.rag = RAGService(db)

    async def analyze_logs(
        self, *, organization_id: int, requester: User, payload: LogAnalysisRequest
    ) -> AIAnalysisResponse:
        self._require_member(requester, organization_id)
        chunks = await self.rag.retrieve(organization_id, payload.log_text[:500], limit=5)
        context = "\n\n".join(
            f"## Chunk {c.chunk_index + 1}\n{c.content[:600]}" for c in chunks
        )

        prompt = f"""Analyze the following log output for an IT operations team.
Provide: summary, likely root cause, severity (low/medium/high/critical), and recommended fixes.

Retrieved knowledge (RAG):
{context or 'None'}

Logs:
{payload.log_text[:8000]}
"""
        answer = await self._complete(prompt)
        return AIAnalysisResponse(
            summary=answer,
            root_cause="See analysis summary for inferred root cause.",
            severity="medium",
            recommendations=["Review the analysis summary and validate on affected systems."],
            knowledge_used=[f"chunk-{c.document_id}-{c.chunk_index}" for c in chunks],
        )

    async def incident_assist(
        self, *, organization_id: int, requester: User, title: str, description: str
    ) -> AIAnalysisResponse:
        self._require_member(requester, organization_id)
        query = f"{title}\n{description or ''}"
        chunks = await self.rag.retrieve(organization_id, query, limit=3)
        context = "\n".join(c.content[:400] for c in chunks)
        prompt = f"""You are an SRE assistant. Given this incident, suggest investigation steps and remediation.

Relevant runbooks/knowledge:
{context or 'None'}

Title: {title}
Description: {description or 'N/A'}

Provide actionable steps."""
        answer = await self._complete(prompt)
        return AIAnalysisResponse(
            summary=answer,
            root_cause="Pending investigation",
            severity="high",
            recommendations=answer.split("\n")[:5],
            knowledge_used=[f"chunk-{c.document_id}-{c.chunk_index}" for c in chunks],
        )

    async def chat(
        self, *, organization_id: int, requester: User, payload: AIChatRequest
    ) -> AIChatResponse:
        self._require_member(requester, organization_id)
        chunks = await self.rag.retrieve(organization_id, payload.message, limit=3)
        context = "\n".join(c.content[:400] for c in chunks)
        prompt = f"""You are an AI operations assistant for an enterprise AIOps platform.
Use this retrieved knowledge if relevant:
{context or 'None'}

User: {payload.message}
"""
        reply = await self._complete(prompt)
        return AIChatResponse(reply=reply)

    async def _complete(self, prompt: str) -> str:
        if not settings.ai_available:
            return (
                "[AI stub — set OPENAI_API_KEY and AI_ENABLED=true]\n\n"
                f"Analysis request received. Prompt preview:\n{prompt[:500]}..."
            )
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are an expert DevOps/SRE assistant."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as exc:
            logger.exception("OpenAI request failed")
            raise ValidationAppError(f"AI request failed: {exc}") from exc

    def _require_member(self, user: User, organization_id: int) -> None:
        if user.is_superuser:
            return
        if not self.memberships.list_for_user_org(user.id, organization_id):
            raise ForbiddenError("Not a member of this organization")
