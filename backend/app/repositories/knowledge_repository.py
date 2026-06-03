from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.schemas.knowledge_schema import KnowledgeCreate


def list_knowledge(db: Session) -> list[models.KnowledgeDocument]:
    return list(db.scalars(select(models.KnowledgeDocument).order_by(models.KnowledgeDocument.created_at.desc())).all())


def create_knowledge(db: Session, payload: KnowledgeCreate) -> models.KnowledgeDocument:
    doc = models.KnowledgeDocument(coach_id=settings.default_coach_id, **payload.model_dump())
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def delete_knowledge(db: Session, knowledge_id: UUID) -> bool:
    doc = db.get(models.KnowledgeDocument, knowledge_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True

