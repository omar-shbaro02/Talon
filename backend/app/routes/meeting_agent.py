from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.agents.orchestrator import OrchestratorAgent
from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.repositories import meeting_repository
from app.schemas.meeting_schema import (
    MeetingAgentJoinRequest,
    MeetingAgentJoinResponse,
    MeetingAgentStatusRead,
    MeetingTranscriptRead,
)
from app.services.recall_service import RecallService, verify_recall_signature

router = APIRouter(tags=["meeting-agent"])
orchestrator = OrchestratorAgent()
recall = RecallService()

CONSENT_NOTICE = "This meeting may be recorded and transcribed by TALON Assistant."


@router.post("/meeting-agent/join", response_model=MeetingAgentJoinResponse, status_code=status.HTTP_201_CREATED)
def join_meeting_agent(payload: MeetingAgentJoinRequest, db: Session = Depends(get_db)):
    meeting = models.Meeting(
        coach_id=settings.default_coach_id,
        client_id=payload.client_id,
        title=payload.title,
        meeting_url=payload.meeting_url,
        transcript="",
        transcript_status="pending",
        recording_status="pending",
        analysis_status="pending",
    )
    db.add(meeting)
    db.flush()

    bot = models.MeetingBot(
        coach_id=settings.default_coach_id,
        client_id=payload.client_id,
        meeting_id=meeting.id,
        meeting_url=payload.meeting_url,
        bot_name="TALON Assistant",
        status="creating",
    )
    db.add(bot)
    db.flush()

    try:
        recall_bot = recall.create_bot(payload.meeting_url, bot.bot_name)
    except RuntimeError as exc:
        bot.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    bot.external_bot_id = recall_bot.get("id")
    bot.status = recall_bot.get("status") or ("created" if bot.external_bot_id else "configuration_required")
    db.commit()
    db.refresh(bot)
    return MeetingAgentJoinResponse(
        meeting_id=meeting.id,
        bot_id=bot.id,
        external_bot_id=bot.external_bot_id,
        status=bot.status,
        bot_name=bot.bot_name,
        consent_notice=CONSENT_NOTICE,
    )


@router.post("/webhooks/recall")
async def recall_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    if not verify_recall_signature(dict(request.headers), body):
        raise HTTPException(status_code=401, detail="Invalid Recall webhook signature")

    payload = await request.json()
    bot = _find_bot(db, payload)
    if not bot:
        return {"status": "ignored", "reason": "bot_not_found"}

    meeting = db.get(models.Meeting, bot.meeting_id)
    if not meeting:
        return {"status": "ignored", "reason": "meeting_not_found"}

    _apply_status(payload, bot, meeting)
    _store_recording(db, payload, meeting)
    stored_segments = _store_transcript_segments(db, payload, meeting)

    if _is_transcript_complete(payload, stored_segments):
        meeting.transcript_status = "complete"
        meeting.transcript_full = _build_transcript(db, meeting.id)
        meeting.transcript = meeting.transcript_full or ""
        meeting.analysis_status = "processing"
        analysis = orchestrator.meeting_analysis(db, meeting.title, meeting.transcript)
        meeting_repository.apply_analysis(db, meeting, analysis)
        db.add(
            models.AIInteraction(
                coach_id=meeting.coach_id,
                client_id=meeting.client_id,
                agent_name="MeetingAgent",
                task_type="recorded_meeting_analysis",
                prompt=meeting.transcript,
                response=analysis,
                model=analysis.get("_usage", {}).get("model", settings.openai_model),
                tokens_used=analysis.get("_usage", {}).get("tokens_used"),
            )
        )

    db.commit()
    return {"status": "ok"}


@router.get("/meeting-agent/{meeting_id}/status", response_model=MeetingAgentStatusRead)
def get_agent_status(meeting_id: UUID, db: Session = Depends(get_db)):
    meeting = db.get(models.Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    bot = db.scalar(select(models.MeetingBot).where(models.MeetingBot.meeting_id == meeting_id))
    return MeetingAgentStatusRead(
        meeting_id=meeting.id,
        title=meeting.title,
        bot_status=bot.status if bot else None,
        transcript_status=meeting.transcript_status,
        recording_status=meeting.recording_status,
        analysis_status=meeting.analysis_status,
    )


@router.get("/meetings/{meeting_id}/transcript", response_model=MeetingTranscriptRead)
def get_transcript(meeting_id: UUID, db: Session = Depends(get_db)):
    meeting = db.get(models.Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    segments = db.scalars(
        select(models.MeetingTranscriptSegment)
        .where(models.MeetingTranscriptSegment.meeting_id == meeting_id)
        .order_by(models.MeetingTranscriptSegment.start_time_seconds.asc().nulls_last())
    ).all()
    return MeetingTranscriptRead(
        meeting_id=meeting.id,
        title=meeting.title,
        transcript_full=meeting.transcript_full or meeting.transcript,
        segments=list(segments),
    )


@router.delete("/meetings/{meeting_id}/recording-data", status_code=status.HTTP_204_NO_CONTENT)
def delete_recording_data(meeting_id: UUID, db: Session = Depends(get_db)):
    meeting = db.get(models.Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    db.execute(delete(models.MeetingTranscriptSegment).where(models.MeetingTranscriptSegment.meeting_id == meeting_id))
    db.execute(delete(models.MeetingRecording).where(models.MeetingRecording.meeting_id == meeting_id))
    meeting.transcript = ""
    meeting.transcript_full = None
    meeting.transcript_status = "deleted"
    meeting.recording_status = "deleted"
    meeting.analysis_status = "deleted"
    db.commit()
    return None


def _find_bot(db: Session, payload: dict[str, Any]) -> models.MeetingBot | None:
    external_id = _first_value(payload, ["bot_id", "bot.id", "data.bot_id", "data.bot.id", "data.id", "id"])
    if not external_id:
        return None
    return db.scalar(select(models.MeetingBot).where(models.MeetingBot.external_bot_id == str(external_id)))


def _apply_status(payload: dict[str, Any], bot: models.MeetingBot, meeting: models.Meeting) -> None:
    event = str(_first_value(payload, ["event", "type", "event_type"]) or "").lower()
    status_value = str(_first_value(payload, ["status", "data.status", "data.code"]) or "").lower()
    combined = f"{event} {status_value}"
    if "join" in combined or "in_call" in combined:
        bot.status = "in_meeting"
        bot.joined_at = bot.joined_at or datetime.utcnow()
    elif "leave" in combined or "done" in combined or "complete" in combined:
        bot.status = "completed"
        bot.left_at = bot.left_at or datetime.utcnow()
    elif status_value:
        bot.status = status_value

    if "recording" in combined:
        meeting.recording_status = "complete" if "complete" in combined or "done" in combined else "recording"
    if "transcript" in combined:
        meeting.transcript_status = "complete" if "complete" in combined or "done" in combined else "processing"


def _store_recording(db: Session, payload: dict[str, Any], meeting: models.Meeting) -> None:
    recording_url = _first_value(payload, ["recording_url", "data.recording_url", "data.recording.url", "recording.url"])
    audio_url = _first_value(payload, ["audio_url", "data.audio_url", "data.audio.url"])
    video_url = _first_value(payload, ["video_url", "data.video_url", "data.video.url"])
    if not any([recording_url, audio_url, video_url]):
        return
    db.add(
        models.MeetingRecording(
            meeting_id=meeting.id,
            recording_url=recording_url,
            audio_url=audio_url,
            video_url=video_url,
            duration_seconds=_first_value(payload, ["duration_seconds", "data.duration_seconds"]),
        )
    )
    meeting.recording_status = "complete"


def _store_transcript_segments(db: Session, payload: dict[str, Any], meeting: models.Meeting) -> int:
    segments = _extract_segments(payload)
    for segment in segments:
        text = _segment_text(segment)
        if not text:
            continue
        db.add(
            models.MeetingTranscriptSegment(
                meeting_id=meeting.id,
                speaker_name=segment.get("speaker_name") or segment.get("speaker") or segment.get("participant_name"),
                speaker_email=segment.get("speaker_email"),
                start_time_seconds=_decimal(segment.get("start_time_seconds") or segment.get("start_timestamp") or segment.get("start")),
                end_time_seconds=_decimal(segment.get("end_time_seconds") or segment.get("end_timestamp") or segment.get("end")),
                text=text,
                confidence=_decimal(segment.get("confidence")),
            )
        )
    if segments:
        meeting.transcript_status = "processing"
    return len(segments)


def _extract_segments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [
        _first_value(payload, ["transcript", "data.transcript", "data.segments", "segments"]),
        _first_value(payload, ["data.words", "words"]),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            return [candidate]
    data = payload.get("data")
    return [data] if isinstance(data, dict) and data.get("text") else []


def _segment_text(segment: dict[str, Any]) -> str:
    if segment.get("text"):
        return str(segment["text"]).strip()
    words = segment.get("words")
    if isinstance(words, list):
        values = []
        for word in words:
            if isinstance(word, dict):
                values.append(str(word.get("text") or word.get("word") or "").strip())
            else:
                values.append(str(word).strip())
        return " ".join(value for value in values if value)
    return ""


def _is_transcript_complete(payload: dict[str, Any], stored_segments: int) -> bool:
    event = str(_first_value(payload, ["event", "type", "event_type"]) or "").lower()
    status_value = str(_first_value(payload, ["status", "data.status", "data.code"]) or "").lower()
    return stored_segments > 0 and "transcript" in f"{event} {status_value}" and any(
        token in f"{event} {status_value}" for token in ["complete", "done", "finished"]
    )


def _build_transcript(db: Session, meeting_id: UUID) -> str:
    segments = db.scalars(
        select(models.MeetingTranscriptSegment)
        .where(models.MeetingTranscriptSegment.meeting_id == meeting_id)
        .order_by(models.MeetingTranscriptSegment.start_time_seconds.asc().nulls_last())
    ).all()
    lines = []
    for segment in segments:
        speaker = segment.speaker_name or "Speaker"
        timestamp = _format_time(segment.start_time_seconds)
        lines.append(f"[{timestamp}] {speaker}: {segment.text}")
    return "\n".join(lines)


def _format_time(value: Decimal | None) -> str:
    seconds = int(value or 0)
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _first_value(payload: dict[str, Any], paths: list[str]) -> Any:
    for path in paths:
        value: Any = payload
        for part in path.split("."):
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = value[part]
        if value is not None:
            return value
    return None
