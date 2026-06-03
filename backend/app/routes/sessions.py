from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_db
from app.repositories import session_repository
from app.schemas.session_schema import SessionCreate, SessionInviteRead, SessionRead, SessionUpdate
from app.services.calendar_email import send_session_invite

router = APIRouter(prefix="/sessions", tags=["sessions"])


def serialize_session(db: Session, session: models.Session) -> dict:
    client = db.get(models.Client, session.client_id)
    return {
        "id": session.id,
        "client_id": session.client_id,
        "coach_id": session.coach_id,
        "title": session.title,
        "session_date": session.session_date,
        "duration_minutes": session.duration_minutes,
        "location": session.location,
        "notes": session.notes,
        "status": session.status,
        "invite_status": session.invite_status,
        "invite_sent_at": session.invite_sent_at,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "client_name": client.full_name if client else None,
        "client_email": client.email if client else None,
    }


@router.get("", response_model=list[SessionRead])
def get_sessions(
    client_id: UUID | None = Query(default=None),
    upcoming_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    sessions = session_repository.list_sessions(db, client_id=client_id, upcoming_only=upcoming_only)
    return [serialize_session(db, item) for item in sessions]


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)):
    if not db.get(models.Client, payload.client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    session = session_repository.create_session(db, payload)
    return serialize_session(db, session)


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    session = session_repository.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_session(db, session)


@router.put("/{session_id}", response_model=SessionRead)
def update_session(session_id: UUID, payload: SessionUpdate, db: Session = Depends(get_db)):
    session = session_repository.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session = session_repository.update_session(db, session, payload)
    return serialize_session(db, session)


@router.post("/{session_id}/send-invite", response_model=SessionInviteRead)
def send_invite(session_id: UUID, db: Session = Depends(get_db)):
    session = session_repository.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    client = db.get(models.Client, session.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    invite = send_session_invite(client, session)
    session.invite_status = invite.delivery_status
    if invite.delivery_status == "sent":
        session.invite_sent_at = datetime.utcnow()
    db.commit()

    return {
        "session_id": session.id,
        "delivery_status": invite.delivery_status,
        "recipient_email": invite.recipient_email,
        "subject": invite.subject,
        "body": invite.body,
        "mailto_url": invite.mailto_url,
        "ics_content": invite.ics_content,
    }
