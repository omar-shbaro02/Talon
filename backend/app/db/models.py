import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


def now_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def updated_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


JsonList = MutableList.as_mutable(JSON().with_variant(JSONB(), "postgresql"))
JsonDict = MutableDict.as_mutable(JSON().with_variant(JSONB(), "postgresql"))


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="coach", nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()

    clients: Mapped[list["Client"]] = relationship(back_populates="coach")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(255))
    job_title: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(255))
    goals: Mapped[str | None] = mapped_column(Text)
    challenges: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()

    coach: Mapped[User] = relationship(back_populates="clients")
    meetings: Mapped[list["Meeting"]] = relationship(back_populates="client")
    action_items: Mapped[list["ActionItem"]] = relationship(back_populates="client")
    insights: Mapped[list["ClientInsight"]] = relationship(back_populates="client")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    session_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    location: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False)
    invite_status: Mapped[str] = mapped_column(String(50), default="not_sent", nullable=False)
    invite_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = uuid_pk()
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    transcript: Mapped[str] = mapped_column(Text, default="", nullable=False)
    meeting_url: Mapped[str | None] = mapped_column(Text)
    transcript_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    recording_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    transcript_full: Mapped[str | None] = mapped_column(Text)
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    scheduled_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("scheduled_events.id"))
    google_event_id: Mapped[str | None] = mapped_column(String(255))
    google_meet_link: Mapped[str | None] = mapped_column(Text)
    scheduled_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str | None] = mapped_column(String(100))
    meeting_provider: Mapped[str | None] = mapped_column(String(50))
    summary: Mapped[str | None] = mapped_column(Text)
    key_topics: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    decisions: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    commitments: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    coaching_observations: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    leadership_patterns: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    emotional_tone: Mapped[str | None] = mapped_column(Text)
    risks_or_blockers: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    recommended_next_steps: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    follow_up_email: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()

    client: Mapped[Client | None] = relationship(back_populates="meetings")
    action_items: Mapped[list["ActionItem"]] = relationship(back_populates="meeting")
    bot: Mapped["MeetingBot | None"] = relationship(back_populates="meeting")
    recordings: Mapped[list["MeetingRecording"]] = relationship(back_populates="meeting")
    transcript_segments: Mapped[list["MeetingTranscriptSegment"]] = relationship(back_populates="meeting")
    scheduled_event: Mapped["ScheduledEvent | None"] = relationship(foreign_keys=[scheduled_event_id])


class CalendarConnection(Base):
    __tablename__ = "calendar_connections"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="google", nullable=False)
    google_account_email: Mapped[str | None] = mapped_column(String(255))
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()


class ScheduledEvent(Base):
    __tablename__ = "scheduled_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("meetings.id"))
    google_event_id: Mapped[str | None] = mapped_column(String(255))
    calendar_id: Mapped[str] = mapped_column(String(255), default="primary", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Beirut", nullable=False)
    location: Mapped[str | None] = mapped_column(Text)
    google_meet_link: Mapped[str | None] = mapped_column(Text)
    google_html_link: Mapped[str | None] = mapped_column(Text)
    meeting_provider: Mapped[str] = mapped_column(String(50), default="google_meet", nullable=False)
    meeting_link: Mapped[str | None] = mapped_column(Text)
    attendees: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False)
    invite_status: Mapped[str] = mapped_column(String(50), default="not_sent", nullable=False)
    invite_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    talon_agent_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()

    meeting: Mapped[Meeting | None] = relationship(foreign_keys=[meeting_id])


class MeetingBot(Base):
    __tablename__ = "meeting_bots"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    meeting_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="recall.ai", nullable=False)
    external_bot_id: Mapped[str | None] = mapped_column(String(255))
    meeting_url: Mapped[str] = mapped_column(Text, nullable=False)
    bot_name: Mapped[str] = mapped_column(String(100), default="TALON Assistant", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()

    meeting: Mapped[Meeting] = relationship(back_populates="bot")


class MeetingRecording(Base):
    __tablename__ = "meeting_recordings"

    id: Mapped[uuid.UUID] = uuid_pk()
    meeting_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    recording_url: Mapped[str | None] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(Text)
    video_url: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(50), default="recall.ai", nullable=False)
    created_at: Mapped[datetime] = now_column()

    meeting: Mapped[Meeting] = relationship(back_populates="recordings")


class MeetingTranscriptSegment(Base):
    __tablename__ = "meeting_transcript_segments"

    id: Mapped[uuid.UUID] = uuid_pk()
    meeting_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("meetings.id"), nullable=False)
    speaker_name: Mapped[str | None] = mapped_column(String(255))
    speaker_email: Mapped[str | None] = mapped_column(String(255))
    start_time_seconds: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    end_time_seconds: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    created_at: Mapped[datetime] = now_column()

    meeting: Mapped[Meeting] = relationship(back_populates="transcript_segments")


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("meetings.id"))
    assigned_to: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()

    client: Mapped[Client | None] = relationship(back_populates="action_items")
    meeting: Mapped[Meeting | None] = relationship(back_populates="action_items")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()


class ContentGeneration(Base):
    __tablename__ = "content_generations"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    tone: Mapped[str] = mapped_column(String(100), nullable=False)
    input_context: Mapped[str | None] = mapped_column(Text)
    generated_output: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = now_column()


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[dict] = mapped_column(JsonDict, default=dict, nullable=False)
    model: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = now_column()


class AutomationWorkflow(Base):
    __tablename__ = "automation_workflows"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    workflow_steps: Mapped[list] = mapped_column(JsonList, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = now_column()
    updated_at: Mapped[datetime] = updated_column()


class ClientInsight(Base):
    __tablename__ = "client_insights"

    id: Mapped[uuid.UUID] = uuid_pk()
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = now_column()

    client: Mapped[Client] = relationship(back_populates="insights")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = uuid_pk()
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    results: Mapped[dict] = mapped_column(JsonDict, default=dict, nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = now_column()


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = uuid_pk()
    coach_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(100))
    file_url: Mapped[str | None] = mapped_column(String(500))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = now_column()
