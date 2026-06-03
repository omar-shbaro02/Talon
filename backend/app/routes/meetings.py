from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.orchestrator import OrchestratorAgent
from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.repositories import meeting_repository
from app.schemas.meeting_schema import MeetingAnalyzeRequest, MeetingRead

router = APIRouter(prefix="/meetings", tags=["meetings"])
orchestrator = OrchestratorAgent()


@router.post("/analyze", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
def analyze_meeting(payload: MeetingAnalyzeRequest, db: Session = Depends(get_db)):
    analysis = orchestrator.meeting_analysis(db, payload.title, payload.transcript)
    meeting = meeting_repository.create_meeting_from_analysis(db, payload.title, payload.transcript, payload.client_id, analysis)
    db.add(
        models.AIInteraction(
            coach_id=settings.default_coach_id,
            client_id=payload.client_id,
            agent_name="MeetingAgent",
            task_type="meeting_analysis",
            prompt=payload.transcript,
            response=analysis,
            model=analysis.get("_usage", {}).get("model", settings.openai_model),
            tokens_used=analysis.get("_usage", {}).get("tokens_used"),
        )
    )
    db.commit()
    return meeting


@router.get("", response_model=list[MeetingRead])
def get_meetings(db: Session = Depends(get_db)):
    return meeting_repository.list_meetings(db)


@router.get("/{meeting_id}", response_model=MeetingRead)
def get_meeting(meeting_id: UUID, db: Session = Depends(get_db)):
    meeting = db.get(models.Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/{meeting_id}/analyze", response_model=MeetingRead)
def analyze_stored_meeting(meeting_id: UUID, db: Session = Depends(get_db)):
    meeting = db.get(models.Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    transcript = meeting.transcript_full or meeting.transcript
    if not transcript:
        raise HTTPException(status_code=400, detail="Meeting has no transcript to analyze")

    meeting.analysis_status = "processing"
    analysis = orchestrator.meeting_analysis(db, meeting.title, transcript)
    meeting_repository.apply_analysis(db, meeting, analysis)
    db.add(
        models.AIInteraction(
            coach_id=meeting.coach_id,
            client_id=meeting.client_id,
            agent_name="MeetingAgent",
            task_type="stored_meeting_analysis",
            prompt=transcript,
            response=analysis,
            model=analysis.get("_usage", {}).get("model", settings.openai_model),
            tokens_used=analysis.get("_usage", {}).get("tokens_used"),
        )
    )
    db.commit()
    db.refresh(meeting)
    return meeting
