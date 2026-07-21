from pydantic import BaseModel, Field


class LogAnalysisRequest(BaseModel):
    log_text: str = Field(min_length=1, max_length=50000)
    asset_id: int | None = None


class AIAnalysisResponse(BaseModel):
    summary: str
    root_cause: str
    severity: str
    recommendations: list[str] = Field(default_factory=list)
    knowledge_used: list[str] = Field(default_factory=list)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class AIChatResponse(BaseModel):
    reply: str


class IncidentAssistRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    category: str = Field(default="runbook", max_length=50)
    content: str = Field(min_length=1)
    tags: str = ""


class KnowledgeDocumentResponse(BaseModel):
    id: int
    organization_id: int
    title: str
    category: str
    content: str
    tags: str | None = None

    model_config = {"from_attributes": True}
