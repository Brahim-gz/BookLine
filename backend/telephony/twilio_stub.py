from __future__ import annotations

from typing import Optional

from app.config import get_settings


def is_twilio_configured() -> bool:
    s = get_settings()
    return bool(s.twilio_account_sid and s.twilio_auth_token)


def get_twilio_config() -> dict[str, Optional[str]]:
    s = get_settings()
    return {
        "account_sid": s.twilio_account_sid,
        "auth_token": s.twilio_auth_token,
        "from_number": s.twilio_phone_number,
    }


def get_simulation_recipient() -> Optional[str]:
    return get_settings().simulation_call_recipient


def initiate_outbound_call(to_phone: Optional[str], callback_url: str) -> Optional[str]:
    if not is_twilio_configured():
        return None
    number = to_phone if to_phone is not None else get_simulation_recipient()
    if not number:
        return None
    return None


def initiate_simulation_call(callback_url: str) -> Optional[str]:
    return initiate_outbound_call(to_phone=None, callback_url=callback_url)
