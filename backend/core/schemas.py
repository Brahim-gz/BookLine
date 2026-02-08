"""
Pydantic schemas for tasks, outcomes, and API contracts.
Decoupled from agent logic; used by routes, swarm, and tools.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- Enums ----------


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskMode(str, Enum):
    SINGLE = "single"   # One agent, one provider
    SWARM = "swarm"     # Parallel agents, multiple providers


# ---------- Provider (data-driven) ----------


class AvailabilityProfile(BaseModel):
    """Determines how availability is generated for a provider (no fixed slots)."""
    weekday_hours: tuple[str, str] = ("09:00", "17:00")  # (open, close)
    weekend_enabled: bool = False
    slot_duration_minutes: int = 30
    # Optional: buffer between slots, max bookings per day, etc.
    buffer_minutes: int = 0


class Provider(BaseModel):
    """Single provider loaded from JSON; no hardcoded IDs or names."""
    id: str
    name: str
    rating: float = Field(ge=0, le=5)
    distance_km: float = Field(ge=0)
    receptionist_style: str = "professional"  # e.g. friendly, formal, brief
    availability_profile: AvailabilityProfile = Field(default_factory=AvailabilityProfile)


# ---------- Call transcript (for frontend display) ----------


class TranscriptTurn(BaseModel):
    """One turn in the conversation: agent or receptionist (simulated)."""
    role: str  # "agent" | "receptionist"
    text: str


# ---------- Agentic outcome ----------


class NegotiationOutcome(BaseModel):
    """Structured result from one agent's negotiation; produced by agent logic, consumed by scoring."""
    provider_id: str
    proposed_slot: Optional[datetime] = None
    confidence_score: float = Field(ge=0, le=1)
    rejection_reasons: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    transcript: list[TranscriptTurn] = Field(default_factory=list)  # conversation with this provider


# ---------- Task & API ----------


class PreferenceWeights(BaseModel):
    """User preference weighting for ranking (availability vs rating vs distance)."""
    availability_weight: float = Field(ge=0, le=1, default=0.5)
    rating_weight: float = Field(ge=0, le=1, default=0.3)
    distance_weight: float = Field(ge=0, le=1, default=0.2)


class UserRequest(BaseModel):
    """Natural language user request to start scheduling."""
    message: str
    mode: TaskMode = TaskMode.SINGLE
    preferences: Optional[PreferenceWeights] = None


class TaskCreate(BaseModel):
    """Request body for starting a scheduling task."""
    user_request: UserRequest


class TaskState(BaseModel):
    """In-memory task state; could be persisted (e.g. Redis) for production."""
    task_id: str
    status: TaskStatus
    mode: TaskMode
    user_request: UserRequest
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    outcomes: list[NegotiationOutcome] = Field(default_factory=list)
    tool_calls_log: list[dict[str, Any]] = Field(default_factory=list)
    transcript: list[TranscriptTurn] = Field(default_factory=list)  # single-call conversation; swarm uses outcomes[].transcript
    error_message: Optional[str] = None
    shortlist: list[RankedSlot] = Field(default_factory=list)
    confirmed_appointment: Optional[BookedAppointment] = None


class RankedSlot(BaseModel):
    """One slot in the shortlist after scoring."""
    provider_id: str
    provider_name: Optional[str] = None
    slot: datetime
    score: float
    rank: int


class BookedAppointment(BaseModel):
    """Confirmed booking (calendar integration writes event when configured)."""
    task_id: str
    provider_id: str
    slot: datetime
    booked_at: datetime = Field(default_factory=datetime.utcnow)
    calendar_event_id: Optional[str] = None
    calendar_link: Optional[str] = None


class ConfirmAppointmentRequest(BaseModel):
    """Request to confirm one of the shortlisted slots."""
    task_id: str
    provider_id: str
    slot: datetime
