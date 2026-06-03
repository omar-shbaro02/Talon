from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models


def list_meetings(db: Session) -> list[models.Meeting]:
    return list(db.scalars(select(models.Meeting).order_by(models.Meeting.created_at.desc())).all())


def create_meeting_from_analysis(db: Session, title: str, transcript: str, client_id: UUID | None, analysis: dict) -> models.Meeting:
    meeting = models.Meeting(
        coach_id=settings.default_coach_id,
        client_id=client_id,
        title=title,
        transcript=transcript,
        summary=analysis.get("summary"),
        key_topics=analysis.get("key_topics", []),
        decisions=analysis.get("decisions", []),
        commitments=analysis.get("commitments", []),
        coaching_observations=analysis.get("coaching_observations", []),
        leadership_patterns=analysis.get("leadership_patterns", []),
        emotional_tone=analysis.get("emotional_tone"),
        risks_or_blockers=analysis.get("risks_or_blockers", []),
        recommended_next_steps=analysis.get("recommended_next_steps", []),
        follow_up_email=analysis.get("follow_up_email"),
        transcript_full=transcript,
        transcript_status="complete",
        analysis_status="complete",
    )
    db.add(meeting)
    db.flush()
    for item in analysis.get("action_items", []):
        db.add(
            models.ActionItem(
                client_id=client_id,
                meeting_id=meeting.id,
                assigned_to=item.get("assigned_to"),
                title=item.get("title", "Follow-up action"),
                description=item.get("description"),
                priority=item.get("priority", "medium"),
            )
        )
    db.commit()
    db.refresh(meeting)
    return meeting


def apply_analysis(db: Session, meeting: models.Meeting, analysis: dict) -> models.Meeting:
    meeting.summary = analysis.get("summary")
    meeting.key_topics = analysis.get("key_topics", [])
    meeting.decisions = analysis.get("decisions", [])
    meeting.commitments = analysis.get("commitments", [])
    meeting.coaching_observations = analysis.get("coaching_observations", [])
    meeting.leadership_patterns = analysis.get("leadership_patterns", [])
    meeting.emotional_tone = analysis.get("emotional_tone")
    meeting.risks_or_blockers = analysis.get("risks_or_blockers", [])
    meeting.recommended_next_steps = analysis.get("recommended_next_steps", [])
    meeting.follow_up_email = analysis.get("follow_up_email")
    meeting.analysis_status = "complete"

    for item in analysis.get("action_items", []):
        db.add(
            models.ActionItem(
                client_id=meeting.client_id,
                meeting_id=meeting.id,
                assigned_to=item.get("assigned_to"),
                title=item.get("title", "Follow-up action"),
                description=item.get("description"),
                priority=item.get("priority", "medium"),
            )
        )
    db.flush()
    return meeting
