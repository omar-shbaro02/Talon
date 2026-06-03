from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models


def ensure_default_user(db: Session) -> models.User:
    user = db.get(models.User, settings.default_coach_id)
    if user:
        return user

    user = models.User(
        id=settings.default_coach_id,
        full_name="TALON Coach",
        email="coach@talon.local",
        password_hash="local-dev-placeholder",
        role="coach",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def parse_uuid(value: str | UUID | None) -> UUID | None:
    if value is None or isinstance(value, UUID):
        return value
    return UUID(value)

