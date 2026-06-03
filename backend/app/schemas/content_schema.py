from uuid import UUID

from pydantic import BaseModel


class ContentGenerateRequest(BaseModel):
    type: str
    topic: str
    tone: str = "professional"
    context: str | None = None
    client_id: UUID | None = None


class CoachAnalyzeRequest(BaseModel):
    client_id: UUID | None = None
    prompt: str
    context: str | None = None

