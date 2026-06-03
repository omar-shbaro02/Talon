from fastapi import FastAPI
from sqlalchemy import inspect, text

from app.core.cors import configure_cors
from app.db.base import Base
from app.db.database import engine
from app.db import models  # noqa: F401
from app.routes import auth_google, calendar, clients, coach, content, dashboard, knowledge, meeting_agent, meetings, sessions
from app.services.storage import ensure_default_user
from app.db.database import SessionLocal

app = FastAPI(title="TALON API", version="0.1.0")
configure_cors(app)


def ensure_sqlite_dev_columns() -> None:
    if not engine.url.drivername.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if not inspector.has_table("sessions"):
        return
    session_columns = {column["name"] for column in inspector.get_columns("sessions")}
    session_additions = {
        "duration_minutes": "ALTER TABLE sessions ADD COLUMN duration_minutes INTEGER NOT NULL DEFAULT 60",
        "location": "ALTER TABLE sessions ADD COLUMN location VARCHAR(500)",
        "invite_status": "ALTER TABLE sessions ADD COLUMN invite_status VARCHAR(50) NOT NULL DEFAULT 'not_sent'",
        "invite_sent_at": "ALTER TABLE sessions ADD COLUMN invite_sent_at DATETIME",
    }
    meeting_columns = {column["name"] for column in inspector.get_columns("meetings")} if inspector.has_table("meetings") else set()
    meeting_additions = {
        "meeting_url": "ALTER TABLE meetings ADD COLUMN meeting_url TEXT",
        "transcript_status": "ALTER TABLE meetings ADD COLUMN transcript_status VARCHAR(50) NOT NULL DEFAULT 'pending'",
        "recording_status": "ALTER TABLE meetings ADD COLUMN recording_status VARCHAR(50) NOT NULL DEFAULT 'pending'",
        "transcript_full": "ALTER TABLE meetings ADD COLUMN transcript_full TEXT",
        "analysis_status": "ALTER TABLE meetings ADD COLUMN analysis_status VARCHAR(50) NOT NULL DEFAULT 'pending'",
        "leadership_patterns": "ALTER TABLE meetings ADD COLUMN leadership_patterns JSON NOT NULL DEFAULT '[]'",
        "emotional_tone": "ALTER TABLE meetings ADD COLUMN emotional_tone TEXT",
        "risks_or_blockers": "ALTER TABLE meetings ADD COLUMN risks_or_blockers JSON NOT NULL DEFAULT '[]'",
        "scheduled_event_id": "ALTER TABLE meetings ADD COLUMN scheduled_event_id CHAR(32)",
        "google_event_id": "ALTER TABLE meetings ADD COLUMN google_event_id VARCHAR(255)",
        "google_meet_link": "ALTER TABLE meetings ADD COLUMN google_meet_link TEXT",
        "scheduled_start_time": "ALTER TABLE meetings ADD COLUMN scheduled_start_time DATETIME",
        "scheduled_end_time": "ALTER TABLE meetings ADD COLUMN scheduled_end_time DATETIME",
        "timezone": "ALTER TABLE meetings ADD COLUMN timezone VARCHAR(100)",
    }
    with engine.begin() as connection:
        for column, statement in session_additions.items():
            if column not in session_columns:
                connection.execute(text(statement))
        for column, statement in meeting_additions.items():
            if column not in meeting_columns:
                connection.execute(text(statement))


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_dev_columns()
    with SessionLocal() as db:
        ensure_default_user(db)


@app.get("/health")
def health():
    return {"status": "ok", "service": "TALON API"}


app.include_router(dashboard.router)
app.include_router(auth_google.router)
app.include_router(calendar.router)
app.include_router(clients.router)
app.include_router(meetings.router)
app.include_router(meeting_agent.router)
app.include_router(sessions.router)
app.include_router(coach.router)
app.include_router(knowledge.router)
app.include_router(content.router)
