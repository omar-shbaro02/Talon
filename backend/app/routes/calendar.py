from types import SimpleNamespace
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.db.database import get_db
from app.schemas.calendar_schema import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarStatusRead,
    ScheduledEventRead,
    SendAgentPlaceholderRead,
)
from app.services import google_calendar_service

router = APIRouter(prefix="/calendar", tags=["calendar"])


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
    if not connection:
        return CalendarStatusRead(connected=False)
    return CalendarStatusRead(
        connected=True,
        provider=connection.provider,
        google_account_email=connection.google_account_email,
        token_expiry=connection.token_expiry,
        scopes=connection.scopes,
    )


@router.post("/events", response_model=ScheduledEventRead, status_code=status.HTTP_201_CREATED)
def create_calendar_event(payload: CalendarEventCreate, db: Session = Depends(get_db)):
    connection = active_connection(db)
    if not connection:
        raise HTTPException(status_code=400, detail="Connect Google Calendar before scheduling sessions.")
    if payload.client_id and not db.get(models.Client, payload.client_id):
        raise HTTPException(status_code=404, detail="Client not found")

    payload.add_google_meet = True
    try:
        credentials = google_calendar_service.refresh_if_needed(db, connection)
        google_event = google_calendar_service.create_google_event(credentials, payload)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Google Calendar event creation failed: {exc}") from exc

    meet_link = google_calendar_service.extract_meet_link(google_event)
    scheduled = models.ScheduledEvent(
        coach_id=settings.default_coach_id,
        client_id=payload.client_id,
        google_event_id=google_event.get("id"),
        calendar_id="primary",
        title=payload.title,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        timezone=payload.timezone,
        location=payload.location,
        google_meet_link=meet_link,
        google_html_link=google_event.get("htmlLink"),
        attendees=payload.attendees,
        status="scheduled",
        talon_agent_enabled=payload.talon_agent_enabled,
    )
    db.add(scheduled)
    db.flush()

    if payload.talon_agent_enabled and meet_link:
        meeting = models.Meeting(
            coach_id=settings.default_coach_id,
            client_id=payload.client_id,
            title=payload.title,
            transcript="",
            meeting_url=meet_link,
            scheduled_event_id=scheduled.id,
            google_event_id=google_event.get("id"),
            google_meet_link=meet_link,
            scheduled_start_time=payload.start_time,
            scheduled_end_time=payload.end_time,
            timezone=payload.timezone,
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
        add_google_meet=True if payload.add_google_meet is None else payload.add_google_meet or bool(scheduled.google_meet_link),
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
    scheduled.google_html_link = google_event.get("htmlLink") or scheduled.google_html_link

    if scheduled.meeting_id:
        meeting = db.get(models.Meeting, scheduled.meeting_id)
        if meeting:
            meeting.title = scheduled.title
            meeting.meeting_url = meet_link
            meeting.google_meet_link = meet_link
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


@router.post("/events/{event_id}/send-agent", response_model=SendAgentPlaceholderRead)
def send_agent_placeholder(event_id: UUID, db: Session = Depends(get_db)):
    scheduled = db.get(models.ScheduledEvent, event_id)
    if not scheduled:
        raise HTTPException(status_code=404, detail="Scheduled event not found")
    if not scheduled.google_meet_link:
        raise HTTPException(status_code=400, detail="Scheduled event does not have a Google Meet link")
    return SendAgentPlaceholderRead(
        message="TALON Meeting Agent dispatch will be implemented with Recall.ai integration.",
        meeting_url=scheduled.google_meet_link,
    )
