from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClientBase(BaseModel):
    full_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    industry: str | None = None
    goals: str | None = None
    challenges: str | None = None
    status: str = "active"


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    job_title: str | None = None
    industry: str | None = None
    goals: str | None = None
    challenges: str | None = None
    status: str | None = None


class ClientRead(ClientBase):
    id: UUID
    coach_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
