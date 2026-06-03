from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    client_id: UUID
    title: str
    session_date: datetime
    duration_minutes: int = 60
    location: str | None = None
    notes: str | None = None
    status: str = "scheduled"


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: str | None = None
    session_date: datetime | None = None
    duration_minutes: int | None = None
    location: str | None = None
    notes: str | None = None
    status: str | None = None


class SessionRead(SessionBase):
    id: UUID
    coach_id: UUID
    duration_minutes: int
    location: str | None = None
    invite_status: str
    invite_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    client_name: str | None = None
    client_email: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionInviteRead(BaseModel):
    session_id: UUID
    delivery_status: str
    recipient_email: str | None = None
    subject: str
    body: str
    mailto_url: str
    ics_content: str

    model_config = ConfigDict(from_attributes=True)
