"""
Google Calendar integration. Uses credentials from app.config.
When credentials are set, provides freebusy and create_event; otherwise returns mock/empty.
Requires: pip install google-auth google-api-python-client
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings


def is_google_calendar_configured() -> bool:
    """True if Google credentials path is set and file exists."""
    s = get_settings()
    if not s.google_credentials_path:
        return False
    p = Path(s.google_credentials_path).expanduser()
    return p.is_file()


def _get_service():
    """Build Calendar API service; returns None if not configured or import fails."""
    if not is_google_calendar_configured():
        return None
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        return None
    s = get_settings()
    path = Path(s.google_credentials_path).expanduser()
    creds = service_account.Credentials.from_service_account_file(
        str(path),
        scopes=["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/calendar.events"],
    )
    return build("calendar", "v3", credentials=creds)


def get_freebusy(
    time_min: datetime,
    time_max: datetime,
    calendar_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Return free/busy info for the calendar in the given window.
    Returns {"busy": [{"start": iso, "end": iso}, ...], "ok": True} or {"ok": False, "error": "..."}.
    """
    service = _get_service()
    cid = calendar_id or get_settings().google_calendar_id or "primary"
    if not service:
        return {"ok": True, "busy": [], "message": "Google Calendar not configured; using mock."}
    try:
        tmin = time_min.isoformat() + "Z" if time_min.tzinfo is None else time_min.isoformat()
        tmax = time_max.isoformat() + "Z" if time_max.tzinfo is None else time_max.isoformat()
        body = {"timeMin": tmin, "timeMax": tmax, "items": [{"id": cid}]}
        result = service.freebusy().query(body=body).execute()
        busy = []
        for cal, data in result.get("calendars", {}).items():
            for item in data.get("busy", []):
                busy.append({"start": item["start"], "end": item["end"]})
        return {"ok": True, "busy": busy}
    except Exception as e:
        return {"ok": False, "error": str(e), "busy": []}


def get_available_slots(
    time_min: datetime,
    time_max: datetime,
    duration_minutes: int = 30,
    calendar_id: Optional[str] = None,
) -> list[dict[str, str]]:
    """
    Return list of free slots {start_iso, end_iso} in the window, excluding busy periods.
    Slot length = duration_minutes.
    """
    fb = get_freebusy(time_min, time_max, calendar_id)
    if not fb.get("ok"):
        return []
    busy_list = fb.get("busy") or []
    if not busy_list:
        # No busy windows: return simple grid
        slots = []
        day = time_min.replace(hour=9, minute=0, second=0, microsecond=0)
        end_day = time_max.replace(hour=17, minute=0, second=0, microsecond=0)
        delta = timedelta(minutes=duration_minutes)
        while day < end_day:
            slot_end = day + delta
            if slot_end <= end_day:
                slots.append({"start_iso": day.isoformat(), "end_iso": slot_end.isoformat()})
            day = slot_end
            if day.hour >= 17:
                day = (day + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        return slots[:50]
    # TODO: Merge busy windows and compute free intervals, then split into duration_minutes slots
    return []


def create_event(
    calendar_id: Optional[str] = None,
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    summary: str = "CallPilot appointment",
    description: str = "",
) -> dict[str, Any]:
    """
    Create a calendar event. Returns {"ok": True, "event_id": "...", "html_link": "..."} or {"ok": False, "error": "..."}.
    """
    service = _get_service()
    cid = calendar_id or get_settings().google_calendar_id or "primary"
    if not service or not start_iso or not end_iso:
        return {"ok": False, "error": "Calendar not configured or missing start/end"}
    try:
        body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_iso, "timeZone": "UTC"},
            "end": {"dateTime": end_iso, "timeZone": "UTC"},
        }
        event = service.events().insert(calendarId=cid, body=body).execute()
        return {"ok": True, "event_id": event.get("id"), "html_link": event.get("htmlLink", "")}
    except Exception as e:
        return {"ok": False, "error": str(e)}
