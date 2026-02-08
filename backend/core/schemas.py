from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskMode(str, Enum):
    SINGLE = "single"
    SWARM = "swarm"


class AvailabilityProfile(BaseModel):
    weekday_hours: tuple[str, str] = ("09:00", "17:00")
    weekend_enabled: bool = False
    slot_duration_minutes: int = 30
    buffer_minutes: int = 0


class Provider(BaseModel):
    id: str
    name: str
    rating: float = Field(ge=0, le=5)
    distance_km: float = Field(ge=0)
    receptionist_style: str = "professional"
    availability_profile: AvailabilityProfile = Field(default_factory=AvailabilityProfile)
    address: Optional[str] = None


class TranscriptTurn(BaseModel):
    role: str
    text: str


class NegotiationOutcome(BaseModel):
    provider_id: str
    proposed_slot: Optional[datetime] = None
    confidence_score: float = Field(ge=0, le=1)
    rejection_reasons: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    transcript: list[TranscriptTurn] = Field(default_factory=list)


class PreferenceWeights(BaseModel):
    availability_weight: float = Field(ge=0, le=1, default=0.5)
    rating_weight: float = Field(ge=0, le=1, default=0.3)
    distance_weight: float = Field(ge=0, le=1, default=0.2)


class UserRequest(BaseModel):
    message: str
    mode: TaskMode = TaskMode.SINGLE
    preferences: Optional[PreferenceWeights] = None


class TaskCreate(BaseModel):
    user_request: UserRequest


class TaskState(BaseModel):
    task_id: str
    status: TaskStatus
    mode: TaskMode
    user_request: UserRequest
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    outcomes: list[NegotiationOutcome] = Field(default_factory=list)
    tool_calls_log: list[dict[str, Any]] = Field(default_factory=list)
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    error_message: Optional[str] = None
    shortlist: list[RankedSlot] = Field(default_factory=list)
    confirmed_appointment: Optional[BookedAppointment] = None


class RankedSlot(BaseModel):
    provider_id: str
    provider_name: Optional[str] = None
    slot: datetime
    score: float
    rank: int


class BookedAppointment(BaseModel):
    task_id: str
    provider_id: str
    slot: datetime
    booked_at: datetime = Field(default_factory=datetime.utcnow)
    calendar_event_id: Optional[str] = None
    calendar_link: Optional[str] = None


class ConfirmAppointmentRequest(BaseModel):
    task_id: str
    provider_id: str
    slot: datetime
