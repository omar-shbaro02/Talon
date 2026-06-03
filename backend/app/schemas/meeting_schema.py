from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MeetingAnalyzeRequest(BaseModel):
    client_id: UUID | None = None
    title: str
    transcript: str


class MeetingAgentJoinRequest(BaseModel):
    client_id: UUID | None = None
    meeting_url: str
    title: str


class MeetingAgentJoinResponse(BaseModel):
    meeting_id: UUID
    bot_id: UUID
    external_bot_id: str | None = None
    status: str
    bot_name: str
    consent_notice: str


class MeetingAgentStatusRead(BaseModel):
    meeting_id: UUID
    title: str
    bot_status: str | None = None
    transcript_status: str
    recording_status: str
    analysis_status: str


class TranscriptSegmentRead(BaseModel):
    id: UUID
    speaker_name: str | None = None
    speaker_email: str | None = None
    start_time_seconds: float | None = None
    end_time_seconds: float | None = None
    text: str
    confidence: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingTranscriptRead(BaseModel):
    meeting_id: UUID
    title: str
    transcript_full: str | None = None
    segments: list[TranscriptSegmentRead] = []


class MeetingRead(BaseModel):
    id: UUID
    client_id: UUID | None = None
    coach_id: UUID
    title: str
    transcript: str
    meeting_url: str | None = None
    transcript_status: str = "pending"
    recording_status: str = "pending"
    transcript_full: str | None = None
    analysis_status: str = "pending"
    summary: str | None = None
    key_topics: list = []
    decisions: list = []
    commitments: list = []
    coaching_observations: list = []
    leadership_patterns: list = []
    emotional_tone: str | None = None
    risks_or_blockers: list = []
    recommended_next_steps: list = []
    follow_up_email: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
