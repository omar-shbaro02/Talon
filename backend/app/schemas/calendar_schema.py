from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalendarStatusRead(BaseModel):
    connected: bool
    provider: str | None = None
    google_account_email: str | None = None
    token_expiry: datetime | None = None
    scopes: list = []


class CalendarEventCreate(BaseModel):
    client_id: UUID | None = None
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    timezone: str = "Asia/Beirut"
    location: str | None = None
    attendees: list[str] = []
    add_google_meet: bool = True
    talon_agent_enabled: bool = False


class CalendarEventUpdate(BaseModel):
    client_id: UUID | None = None
    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None
    location: str | None = None
    attendees: list[str] | None = None
    add_google_meet: bool | None = None
    talon_agent_enabled: bool | None = None
    status: str | None = None


class ScheduledEventRead(BaseModel):
    id: UUID
    coach_id: UUID
    client_id: UUID | None = None
    meeting_id: UUID | None = None
    google_event_id: str | None = None
    calendar_id: str
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    timezone: str
    location: str | None = None
    google_meet_link: str | None = None
    google_html_link: str | None = None
    attendees: list = []
    status: str
    talon_agent_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendAgentPlaceholderRead(BaseModel):
    message: str
    meeting_url: str
