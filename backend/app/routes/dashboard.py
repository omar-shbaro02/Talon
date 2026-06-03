from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    week_end = now + timedelta(days=7)
    active_clients = db.scalar(select(func.count()).select_from(models.Client).where(models.Client.status == "active")) or 0
    pending_actions = db.scalar(select(func.count()).select_from(models.ActionItem).where(models.ActionItem.status != "done")) or 0
    week_sessions = db.scalars(
        select(models.Session)
        .where(models.Session.session_date >= now)
        .where(models.Session.session_date < week_end)
        .order_by(models.Session.session_date.asc())
    ).all()
    today_sessions = [session for session in week_sessions if session.session_date <= today_end]
    meetings = db.scalars(select(models.Meeting).order_by(models.Meeting.created_at.desc()).limit(3)).all()
    recorded_meetings = db.scalars(
        select(models.Meeting)
        .where(models.Meeting.meeting_url.is_not(None))
        .order_by(models.Meeting.created_at.desc())
        .limit(5)
    ).all()
    clients = db.scalars(select(models.Client).order_by(models.Client.created_at.desc()).limit(4)).all()
    calendar_connection = db.scalar(
        select(models.CalendarConnection)
        .where(models.CalendarConnection.is_active.is_(True))
        .order_by(models.CalendarConnection.created_at.desc())
    )
    scheduled_events = db.scalars(
        select(models.ScheduledEvent)
        .where(models.ScheduledEvent.status != "cancelled")
        .where(models.ScheduledEvent.start_time >= now)
        .order_by(models.ScheduledEvent.start_time.asc())
        .limit(6)
    ).all()
    today_meetings = [event for event in scheduled_events if event.start_time <= today_end]
    agent_ready = [event for event in scheduled_events if event.talon_agent_enabled and event.google_meet_link]

    return {
        "active_clients": active_clients,
        "sessions_this_week": len(week_sessions),
        "pending_actions": pending_actions,
        "generated_insights": db.scalar(select(func.count()).select_from(models.AIInteraction)) or 0,
        "today_sessions": [
            {
                "id": str(session.id),
                "client_id": str(session.client_id),
                "client_name": db.get(models.Client, session.client_id).full_name if db.get(models.Client, session.client_id) else None,
                "title": session.title,
                "session_date": session.session_date,
                "status": session.status,
            }
            for session in today_sessions
        ],
        "recent_meeting_summaries": [
            {"id": str(meeting.id), "title": meeting.title, "summary": meeting.summary, "created_at": meeting.created_at}
            for meeting in meetings
        ],
        "latest_recorded_sessions": [
            {
                "id": str(meeting.id),
                "client_name": meeting.client.full_name if meeting.client else "No client",
                "title": meeting.title,
                "transcript_status": meeting.transcript_status,
                "analysis_status": meeting.analysis_status,
            }
            for meeting in recorded_meetings
        ],
        "active_client_list": [
            {"id": str(client.id), "full_name": client.full_name, "company": client.company, "status": client.status}
            for client in clients
        ],
        "google_calendar_connected": bool(calendar_connection),
        "google_calendar_email": calendar_connection.google_account_email if calendar_connection else None,
        "todays_meetings": [
            {
                "id": str(event.id),
                "title": event.title,
                "start_time": event.start_time,
                "google_meet_link": event.google_meet_link,
                "status": event.status,
            }
            for event in today_meetings
        ],
        "upcoming_scheduled_events": [
            {
                "id": str(event.id),
                "title": event.title,
                "start_time": event.start_time,
                "google_meet_link": event.google_meet_link,
                "status": event.status,
            }
            for event in scheduled_events
        ],
        "talon_agent_ready_meetings": [
            {
                "id": str(event.id),
                "title": event.title,
                "start_time": event.start_time,
                "meeting_url": event.google_meet_link,
            }
            for event in agent_ready
        ],
        "ai_recommendations": [
            "Review clients with open action items before the next session.",
            "Convert recent meeting observations into one measurable leadership experiment.",
            "Add your preferred coaching frameworks to Knowledge Hub for stronger AI context.",
        ],
        "quick_actions": ["Add client", "Analyze meeting", "Generate content", "Add knowledge note"],
    }
