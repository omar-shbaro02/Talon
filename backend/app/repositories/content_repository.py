from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models


def save_generation(
    db: Session,
    content_type: str,
    topic: str,
    tone: str,
    output: str,
    input_context: str | None = None,
    client_id: UUID | None = None,
) -> models.ContentGeneration:
    generation = models.ContentGeneration(
        coach_id=settings.default_coach_id,
        client_id=client_id,
        content_type=content_type,
        topic=topic,
        tone=tone,
        input_context=input_context,
        generated_output=output,
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)
    return generation

