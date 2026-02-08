from __future__ import annotations

from typing import Any, Optional

from app.config import get_settings

OUTBOUND_URL = "https://api.elevenlabs.io/v1/convai/twilio/outbound-call"


def is_outbound_configured() -> bool:
    s = get_settings()
    return bool(
        s.elevenlabs_api_key
        and s.elevenlabs_agent_id
        and getattr(s, "elevenlabs_agent_phone_number_id", None)
    )


def start_outbound_call(to_number: str) -> dict[str, Any]:
    s = get_settings()
    api_key = s.elevenlabs_api_key or ""
    agent_id = s.elevenlabs_agent_id or ""
    phone_id = getattr(s, "elevenlabs_agent_phone_number_id", None) or ""
    if not all([api_key, agent_id, phone_id]):
        return {
            "success": False,
            "message": "Outbound calls not configured: set ELEVENLABS_API_KEY, ELEVENLABS_AGENT_ID, ELEVENLABS_AGENT_PHONE_NUMBER_ID",
            "callSid": None,
            "conversation_id": None,
        }
    try:
        import httpx
    except ImportError:
        return {
            "success": False,
            "message": "httpx required for outbound calls: pip install httpx",
            "callSid": None,
            "conversation_id": None,
        }
    payload = {
        "agent_id": agent_id,
        "agent_phone_number_id": phone_id,
        "to_number": to_number,
    }
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(OUTBOUND_URL, json=payload, headers=headers)
    try:
        data = resp.json()
    except Exception:
        data = {}
    if resp.status_code == 200:
        return {
            "success": data.get("success", True),
            "message": data.get("message", "Call initiated"),
            "callSid": data.get("callSid"),
            "conversation_id": data.get("conversation_id"),
        }
    detail = data.get("detail", data.get("message", f"HTTP {resp.status_code}"))
    if isinstance(detail, list) and detail:
        detail = detail[0].get("msg", str(detail[0])) if isinstance(detail[0], dict) else str(detail[0])
    return {
        "success": False,
        "message": str(detail) if detail else f"HTTP {resp.status_code}",
        "callSid": None,
        "conversation_id": None,
    }
