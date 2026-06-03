from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import OrchestratorAgent
from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.repositories.content_repository import save_generation
from app.schemas.content_schema import ContentGenerateRequest

router = APIRouter(prefix="/content", tags=["content"])
orchestrator = OrchestratorAgent()


@router.post("/generate")
def generate_content(payload: ContentGenerateRequest, db: Session = Depends(get_db)):
    result = orchestrator.content_generation(db, payload.type, payload.topic, payload.tone, payload.context)
    output = result.get("content") or str(result)
    generation = save_generation(db, payload.type, payload.topic, payload.tone, output, payload.context, payload.client_id)
    db.add(
        models.AIInteraction(
            coach_id=settings.default_coach_id,
            client_id=payload.client_id,
            agent_name="ContentAgent",
            task_type=payload.type,
            prompt=f"{payload.topic}\n{payload.context or ''}",
            response=result,
            model=result.get("_usage", {}).get("model", settings.openai_model),
            tokens_used=result.get("_usage", {}).get("tokens_used"),
        )
    )
    db.commit()
    return {"id": generation.id, **result}

