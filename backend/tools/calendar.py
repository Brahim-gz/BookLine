from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable, Optional

ToolCallLogger = Optional[Callable[[str, str, dict[str, Any], Any], None]]


def check_availability(
    params: dict[str, Any],
    providers_path: Any,
    tool_log: ToolCallLogger = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    date_from = params.get("date_from") or params.get("date_from_iso")
    date_to = params.get("date_to") or params.get("date_to_iso")
    duration_minutes = int(params.get("duration_minutes", 30))
    if not date_from or not date_to:
        out = {"ok": False, "error": "date_from and date_to required (YYYY-MM-DD)", "slots": []}
        if tool_log and task_id:
            tool_log(task_id, "check_availability", params, out)
        return out
    try:
        start = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        end = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        out = {"ok": False, "error": "Invalid date format", "slots": []}
        if tool_log and task_id:
            tool_log(task_id, "check_availability", params, out)
        return out

    try:
        from integrations.google_calendar import is_google_calendar_configured, get_available_slots
        if is_google_calendar_configured():
            slots = get_available_slots(start, end, duration_minutes)
            out = {"ok": True, "slots": slots[:20], "message": "Google Calendar"}
        else:
            raise ImportError
    except Exception:
        slots = []
        day = start.replace(hour=9, minute=0, second=0, microsecond=0)
        end_day = end.replace(hour=17, minute=0, second=0, microsecond=0)
        while day < end_day:
            slot_end = day + timedelta(minutes=duration_minutes)
            if slot_end.hour <= 17 and slot_end.minute <= 0:
                slots.append({"start_iso": day.isoformat(), "end_iso": slot_end.isoformat()})
            day += timedelta(minutes=duration_minutes)
            if day.hour >= 17:
                day = (day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        out = {"ok": True, "slots": slots[:20], "message": "Mock calendar"}
    if tool_log and task_id:
        tool_log(task_id, "check_availability", params, out)
    return out


def get_busy_windows(
    params: dict[str, Any],
    providers_path: Any,
    tool_log: ToolCallLogger = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    date_from = params.get("date_from") or params.get("date_from_iso")
    date_to = params.get("date_to") or params.get("date_to_iso")
    if not date_from or not date_to:
        out = {"ok": False, "error": "date_from and date_to required", "busy": []}
        if tool_log and task_id:
            tool_log(task_id, "get_busy_windows", params, out)
        return out
    try:
        start = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
        end = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        out = {"ok": False, "error": "Invalid date format", "busy": []}
        if tool_log and task_id:
            tool_log(task_id, "get_busy_windows", params, out)
        return out
    try:
        from integrations.google_calendar import is_google_calendar_configured, get_freebusy
        if is_google_calendar_configured():
            fb = get_freebusy(start, end)
            out = {"ok": fb.get("ok", True), "busy": fb.get("busy", []), "message": "Google Calendar"}
        else:
            out = {"ok": True, "busy": [], "message": "Mock; no busy windows."}
    except Exception:
        out = {"ok": True, "busy": [], "message": "Mock; no busy windows."}
    if tool_log and task_id:
        tool_log(task_id, "get_busy_windows", params, out)
    return out
