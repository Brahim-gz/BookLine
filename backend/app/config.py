"""
Application configuration. All external endpoints and feature flags live here.
No provider-specific or slot logic is hardcoded.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config; load from env and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ElevenLabs Conversational AI
    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_agent_id: Optional[str] = os.getenv("ELEVENLABS_AGENT_ID")

    # Paths (data-driven)
    providers_json_path: Path = Path(__file__).resolve().parent.parent / "data" / "providers.json"

    # Swarm
    swarm_max_agents: int = 15

    # Twilio (telephony) - optional; when set, outbound calls can be placed via Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None  # From number for outbound calls

    # Google Calendar - path to service account or OAuth credentials JSON file
    google_credentials_path: Optional[str] = None
    google_calendar_id: Optional[str] = None  # User's calendar ID (e.g. "primary" or email)


def get_settings() -> Settings:
    return Settings()
