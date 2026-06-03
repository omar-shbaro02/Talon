from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.schemas.session_schema import SessionCreate, SessionUpdate


def list_sessions(db: Session, client_id: UUID | None = None, upcoming_only: bool = False) -> list[models.Session]:
    query = select(models.Session).order_by(models.Session.session_date.asc())
    if client_id:
        query = query.where(models.Session.client_id == client_id)
    if upcoming_only:
        query = query.where(models.Session.session_date >= datetime.utcnow())
    return list(db.scalars(query).all())


def list_sessions_between(db: Session, start: datetime, end: datetime) -> list[models.Session]:
    return list(
        db.scalars(
            select(models.Session)
            .where(models.Session.session_date >= start)
            .where(models.Session.session_date < end)
            .order_by(models.Session.session_date.asc())
        ).all()
    )


def list_week_sessions(db: Session) -> list[models.Session]:
    now = datetime.utcnow()
    return list_sessions_between(db, now, now + timedelta(days=7))


def get_session(db: Session, session_id: UUID) -> models.Session | None:
    return db.get(models.Session, session_id)


def create_session(db: Session, payload: SessionCreate) -> models.Session:
    session = models.Session(coach_id=settings.default_coach_id, **payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session(db: Session, session: models.Session, payload: SessionUpdate) -> models.Session:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session
