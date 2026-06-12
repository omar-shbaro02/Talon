from types import SimpleNamespace
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.schemas.calendar_schema import (
    CalendarAgentDispatchRead,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarInviteRead,
    CalendarStatusRead,
    ScheduledEventRead,
)
from app.services import google_calendar_service
from app.services.meeting_provider_service import create_teams_meeting, create_zoom_meeting, teams_configured, zoom_configured
from app.services.recall_service import RecallService
from app.services.scheduled_event_email import send_event_invite

router = APIRouter(prefix="/calendar", tags=["calendar"])
recall = RecallService()
CONSENT_NOTICE = "This meeting may be recorded and transcribed by TALON Assistant."


def active_connection(db: Session) -> models.CalendarConnection | None:
    return db.scalar(
        select(models.CalendarConnection)
        .where(models.CalendarConnection.user_id == settings.default_coach_id)
        .where(models.CalendarConnection.provider == "google")
        .where(models.CalendarConnection.is_active.is_(True))
        .order_by(models.CalendarConnection.created_at.desc())
    )


@router.get("/status", response_model=CalendarStatusRead)
def calendar_status(db: Session = Depends(get_db)):
    connection = active_connection(db)
    meeting_providers = {
        "google_meet": bool(connection),
        "zoom": zoom_configured(),
        "teams": teams_configured(),
    }
    if not connection:
        return CalendarStatusRead(connected=False, meeting_providers=meeting_providers)
    return CalendarStatusRead(
        connected=True,
        provider=connection.provider,
        google_account_email=connection.google_account_email,
        token_expiry=connection.token_expiry,
        scopes=connection.scopes,
        meeting_providers=meeting_providers,
    )


@router.post("/events", response_model=ScheduledEventRead, status_code=status.HTTP_201_CREATED)
def create_calendar_event(payload: CalendarEventCreate, db: Session = Depends(get_db)):
    if payload.client_id and not db.get(models.Client, payload.client_id):
        raise HTTPException(status_code=404, detail="Client not found")

    provider = payload.meeting_provider
    if provider not in {"google_meet", "zoom", "teams"}:
        raise HTTPException(status_code=400, detail="Choose Google Meet, Zoom, or Microsoft Teams.")

    connection = active_connection(db)
    google_event = {}
    meeting_link = None
    external_provider_id = None

    try:
        if provider == "google_meet":
            if not connection:
                raise HTTPException(status_code=400, detail="Connect Google Calendar before generating a Google Meet link.")
            payload.add_google_meet = True
            credentials = google_calendar_service.refresh_if_needed(db, connection)
            google_event = google_calendar_service.create_google_event(credentials, payload)
            meeting_link = google_calendar_service.extract_meet_link(google_event)
        elif provider == "zoom":
            zoom_meeting = create_zoom_meeting(payload)
            meeting_link = zoom_meeting.link
            external_provider_id = zoom_meeting.external_id
        else:
            teams_meeting = create_teams_meeting(payload)
            meeting_link = teams_meeting.link
            external_provider_id = teams_meeting.external_id

        if provider != "google_meet" and connection:
            calendar_payload = SimpleNamespace(**payload.model_dump())
            calendar_payload.add_google_meet = False
            calendar_payload.location = meeting_link
            credentials = google_calendar_service.refresh_if_needed(db, connection)
            google_event = google_calendar_service.create_google_event(credentials, calendar_payload)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"{provider_label(provider)} meeting creation failed: {exc}") from exc

    scheduled = models.ScheduledEvent(
        coach_id=settings.default_coach_id,
        client_id=payload.client_id,
        google_event_id=google_event.get("id") or external_provider_id,
        calendar_id="primary",
        title=payload.title,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        timezone=payload.timezone,
        location=payload.location or meeting_link,
        google_meet_link=meeting_link if provider == "google_meet" else None,
        google_html_link=google_event.get("htmlLink"),
        meeting_provider=provider,
        meeting_link=meeting_link,
        attendees=payload.attendees,
        status="scheduled",
        talon_agent_enabled=payload.talon_agent_enabled,
    )
    db.add(scheduled)
    db.flush()

    if payload.talon_agent_enabled and meeting_link:
        meeting = models.Meeting(
            coach_id=settings.default_coach_id,
            client_id=payload.client_id,
            title=payload.title,
            transcript="",
            meeting_url=meeting_link,
            scheduled_event_id=scheduled.id,
            google_event_id=google_event.get("id"),
            google_meet_link=meeting_link if provider == "google_meet" else None,
            scheduled_start_time=payload.start_time,
            scheduled_end_time=payload.end_time,
            timezone=payload.timezone,
            meeting_provider=provider,
            transcript_status="pending",
            recording_status="pending",
            analysis_status="pending",
        )
        db.add(meeting)
        db.flush()
        scheduled.meeting_id = meeting.id

    db.commit()
    db.refresh(scheduled)
    return scheduled


@router.get("/events", response_model=list[ScheduledEventRead])
def list_calendar_events(db: Session = Depends(get_db)):
    return list(
        db.scalars(
            select(models.ScheduledEvent)
            .where(models.ScheduledEvent.status != "cancelled")
            .order_by(models.ScheduledEvent.start_time.asc())
        ).all()
    )


@router.put("/events/{event_id}", response_model=ScheduledEventRead)
def update_calendar_event(event_id: UUID, payload: CalendarEventUpdate, db: Session = Depends(get_db)):
    scheduled = db.get(models.ScheduledEvent, event_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    connection = active_connection(db)
    if not connection:
        raise HTTPException(status_code=400, detail="Connect Google Calendar before updating sessions.")

    merged = SimpleNamespace(
        title=payload.title if payload.title is not None else scheduled.title,
        description=payload.description if payload.description is not None else scheduled.description,
        start_time=payload.start_time if payload.start_time is not None else scheduled.start_time,
        end_time=payload.end_time if payload.end_time is not None else scheduled.end_time,
        timezone=payload.timezone if payload.timezone is not None else scheduled.timezone,
        location=payload.location if payload.location is not None else scheduled.location,
        attendees=payload.attendees if payload.attendees is not None else scheduled.attendees,
        add_google_meet=scheduled.meeting_provider == "google_meet" if payload.add_google_meet is None else payload.add_google_meet or bool(scheduled.google_meet_link),
    )

    try:
        credentials = google_calendar_service.refresh_if_needed(db, connection)
        google_event = google_calendar_service.update_google_event(credentials, scheduled.google_event_id, merged, scheduled.calendar_id)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Google Calendar event update failed: {exc}") from exc

    meet_link = google_calendar_service.extract_meet_link(google_event) or scheduled.google_meet_link
    for field in ["client_id", "title", "description", "start_time", "end_time", "timezone", "location", "attendees", "talon_agent_enabled", "status"]:
        value = getattr(payload, field, None)
        if value is not None:
            setattr(scheduled, field, value)
    scheduled.google_meet_link = meet_link
    scheduled.meeting_link = meet_link
    scheduled.google_html_link = google_event.get("htmlLink") or scheduled.google_html_link

    if scheduled.meeting_id:
        meeting = db.get(models.Meeting, scheduled.meeting_id)
        if meeting:
            meeting.title = scheduled.title
            meeting.meeting_url = meet_link
            meeting.google_meet_link = meet_link
            meeting.meeting_provider = scheduled.meeting_provider
            meeting.google_event_id = scheduled.google_event_id
            meeting.scheduled_start_time = scheduled.start_time
            meeting.scheduled_end_time = scheduled.end_time
            meeting.timezone = scheduled.timezone
    db.commit()
    db.refresh(scheduled)
    return scheduled


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_event(event_id: UUID, db: Session = Depends(get_db)):
    scheduled = db.get(models.ScheduledEvent, event_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    connection = active_connection(db)
    if not connection:
        raise HTTPException(status_code=400, detail="Connect Google Calendar before cancelling sessions.")
    try:
        credentials = google_calendar_service.refresh_if_needed(db, connection)
        if scheduled.google_event_id:
            google_calendar_service.delete_google_event(credentials, scheduled.google_event_id, scheduled.calendar_id)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Google Calendar event cancellation failed: {exc}") from exc
    scheduled.status = "cancelled"
    db.commit()
    return None


@router.post("/events/{event_id}/send-agent", response_model=CalendarAgentDispatchRead)
def send_agent(event_id: UUID, db: Session = Depends(get_db)):
    scheduled = db.get(models.ScheduledEvent, event_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    meeting_url = scheduled.meeting_link or scheduled.google_meet_link
    if not meeting_url:
        raise HTTPException(status_code=400, detail="Scheduled event does not have a meeting link")

    meeting = db.get(models.Meeting, scheduled.meeting_id) if scheduled.meeting_id else None
    if not meeting:
        meeting = models.Meeting(
            coach_id=settings.default_coach_id,
            client_id=scheduled.client_id,
            title=scheduled.title,
            transcript="",
            meeting_url=meeting_url,
            scheduled_event_id=scheduled.id,
            google_event_id=scheduled.google_event_id,
            google_meet_link=scheduled.google_meet_link,
            scheduled_start_time=scheduled.start_time,
            scheduled_end_time=scheduled.end_time,
            timezone=scheduled.timezone,
            meeting_provider=scheduled.meeting_provider,
            transcript_status="pending",
            recording_status="pending",
            analysis_status="pending",
        )
        db.add(meeting)
        db.flush()
        scheduled.meeting_id = meeting.id

    bot = db.scalar(select(models.MeetingBot).where(models.MeetingBot.meeting_id == meeting.id))
    if not bot:
        bot = models.MeetingBot(
            coach_id=settings.default_coach_id,
            client_id=scheduled.client_id,
            meeting_id=meeting.id,
            meeting_url=meeting_url,
            bot_name="TALON Assistant",
            status="creating",
        )
        db.add(bot)
        db.flush()

        try:
            recall_bot = recall.create_bot(meeting_url, bot.bot_name, CONSENT_NOTICE)
        except RuntimeError as exc:
            bot.status = "failed"
            db.commit()
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        bot.external_bot_id = recall_bot.get("id")
        bot.status = recall_bot.get("status") or ("created" if bot.external_bot_id else "configuration_required")

    scheduled.talon_agent_enabled = True
    db.commit()
    db.refresh(bot)
    return CalendarAgentDispatchRead(
        event_id=scheduled.id,
        meeting_id=meeting.id,
        bot_id=bot.id,
        external_bot_id=bot.external_bot_id,
        status=bot.status,
        bot_name=bot.bot_name,
        consent_notice=CONSENT_NOTICE,
        meeting_url=meeting_url,
    )


@router.post("/events/{event_id}/send-invite", response_model=CalendarInviteRead)
def send_calendar_invite(event_id: UUID, db: Session = Depends(get_db)):
    scheduled = db.get(models.ScheduledEvent, event_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    client = db.get(models.Client, scheduled.client_id) if scheduled.client_id else None
    invite = send_event_invite(client, scheduled)
    scheduled.invite_status = invite.delivery_status
    if invite.delivery_status == "sent":
        scheduled.invite_sent_at = datetime.utcnow()
    db.commit()
    return CalendarInviteRead(
        event_id=scheduled.id,
        delivery_status=invite.delivery_status,
        recipient_email=invite.recipient_email,
        subject=invite.subject,
        body=invite.body,
        mailto_url=invite.mailto_url,
        ics_content=invite.ics_content,
    )


def provider_label(provider: str) -> str:
    return {
        "google_meet": "Google Meet",
        "zoom": "Zoom",
        "teams": "Microsoft Teams",
    }.get(provider, "Video")
