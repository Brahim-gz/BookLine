"""
Twilio telephony stub. Uses credentials from config; wire here when placing real outbound calls.
Install: pip install twilio
"""
from __future__ import annotations

from typing import Optional

from app.config import get_settings


def is_twilio_configured() -> bool:
    """True if Twilio credentials are set in config (e.g. from .env)."""
    s = get_settings()
    return bool(s.twilio_account_sid and s.twilio_auth_token)


def get_twilio_config() -> dict[str, Optional[str]]:
    """Return Twilio settings for use by call initiators. Never log or expose auth_token."""
    s = get_settings()
    return {
        "account_sid": s.twilio_account_sid,
        "auth_token": s.twilio_auth_token,
        "from_number": s.twilio_phone_number,
    }


def initiate_outbound_call(to_phone: str, callback_url: str) -> Optional[str]:
    """
    Place an outbound call via Twilio (stub). When implemented:
    - Use get_twilio_config() for credentials.
    - Create a Twilio client and call client.calls.create(to=to_phone, from_=from_number, url=callback_url).
    - Return the call SID.
    Requires: pip install twilio
    """
    if not is_twilio_configured():
        return None
    # TODO: from twilio.rest import Client; client = Client(account_sid, auth_token); call = client.calls.create(...); return call.sid
    return None
