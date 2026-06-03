from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models
from app.schemas.client_schema import ClientCreate, ClientUpdate


def list_clients(db: Session) -> list[models.Client]:
    return list(db.scalars(select(models.Client).order_by(models.Client.created_at.desc())).all())


def get_client(db: Session, client_id: UUID) -> models.Client | None:
    return db.get(models.Client, client_id)


def create_client(db: Session, payload: ClientCreate) -> models.Client:
    client = models.Client(coach_id=settings.default_coach_id, **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def update_client(db: Session, client: models.Client, payload: ClientUpdate) -> models.Client:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client

