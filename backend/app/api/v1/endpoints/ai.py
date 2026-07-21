from fastapi import APIRouter, Depends

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.schemas.ai import (
    AIAnalysisResponse,
    AIChatRequest,
    AIChatResponse,
    IncidentAssistRequest,
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    LogAnalysisRequest,
)
from app.services.ai import AIService
from app.repositories.knowledge_document import KnowledgeDocumentRepository
from app.models.knowledge_document import KnowledgeDocument

router = APIRouter(prefix="/organizations/me/ai", tags=["AI Assistant"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.post("/analyze-logs", response_model=AIAnalysisResponse, summary="Analyze log text with AI")
async def analyze_logs(
    payload: LogAnalysisRequest, db: DbSession, current: AuthenticatedUser
) -> AIAnalysisResponse:
    return await AIService(db).analyze_logs(
        organization_id=_org_id(current), requester=current.user, payload=payload
    )


@router.post("/incident-assist", response_model=AIAnalysisResponse, summary="AI incident assistance")
async def incident_assist(
    payload: IncidentAssistRequest, db: DbSession, current: AuthenticatedUser
) -> AIAnalysisResponse:
    return await AIService(db).incident_assist(
        organization_id=_org_id(current),
        requester=current.user,
        title=payload.title,
        description=payload.description,
    )


@router.post("/chat", response_model=AIChatResponse, summary="AI operations chat")
async def ai_chat(
    payload: AIChatRequest, db: DbSession, current: AuthenticatedUser
) -> AIChatResponse:
    return await AIService(db).chat(
        organization_id=_org_id(current), requester=current.user, payload=payload
    )


@router.get("/knowledge", response_model=list[KnowledgeDocumentResponse], summary="List knowledge docs")
def list_knowledge(db: DbSession, current: AuthenticatedUser) -> list[KnowledgeDocumentResponse]:
    docs = KnowledgeDocumentRepository(db).list_for_organization(_org_id(current))
    return [KnowledgeDocumentResponse.model_validate(d) for d in docs]


@router.post(
    "/knowledge",
    response_model=KnowledgeDocumentResponse,
    summary="Create knowledge base document",
)
def create_knowledge(
    payload: KnowledgeDocumentCreate, db: DbSession, current: AuthenticatedUser
) -> KnowledgeDocumentResponse:
    doc = KnowledgeDocument(
        organization_id=_org_id(current),
        title=payload.title,
        category=payload.category,
        content=payload.content,
        tags=payload.tags or None,
    )
    KnowledgeDocumentRepository(db).add(doc)
    db.commit()
    db.refresh(doc)
    return KnowledgeDocumentResponse.model_validate(doc)
