from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KnowledgeCreate(BaseModel):
    title: str
    category: str | None = None
    content: str
    tags: list[str] = []
    source_type: str = "manual"


class KnowledgeRead(KnowledgeCreate):
    id: UUID
    coach_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

