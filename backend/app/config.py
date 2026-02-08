from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_agent_id: Optional[str] = os.getenv("ELEVENLABS_AGENT_ID")
    elevenlabs_receptionist_agent_id: Optional[str] = None
    elevenlabs_agent_phone_number_id: Optional[str] = None

    providers_json_path: Path = Path(__file__).resolve().parent.parent / "data" / "providers.json"

    swarm_max_agents: int = 15

    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    simulation_call_recipient: Optional[str] = None

    google_credentials_path: Optional[str] = None
    google_calendar_id: Optional[str] = None

    google_places_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None


def get_settings() -> Settings:
    return Settings()
