from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import OrchestratorAgent
from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.schemas.content_schema import CoachAnalyzeRequest

router = APIRouter(prefix="/coach", tags=["coach"])
orchestrator = OrchestratorAgent()


@router.post("/analyze")
def analyze_coaching_prompt(payload: CoachAnalyzeRequest, db: Session = Depends(get_db)):
    result = orchestrator.coach_analysis(db, payload.prompt, payload.context)
    db.add(
        models.AIInteraction(
            coach_id=settings.default_coach_id,
            client_id=payload.client_id,
            agent_name="CoachAgent",
            task_type="coach_analysis",
            prompt=payload.prompt,
            response=result,
            model=result.get("_usage", {}).get("model", settings.openai_model),
            tokens_used=result.get("_usage", {}).get("tokens_used"),
        )
    )
    db.commit()
    return result

