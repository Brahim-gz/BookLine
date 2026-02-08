"""
Slot validation and confirmation tool: check slot with provider availability, confirm booking.
Decoupled from agent logic; explicit and logged.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from core.providers_loader import get_provider

ToolCallLogger = Optional[Callable[[str, str, dict[str, Any], Any], None]]


def validate_slot(
    params: dict[str, Any],
    providers_path: Path,
    tool_log: ToolCallLogger = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Agentic tool: validate that a proposed slot is available for the provider and user.
    Params: provider_id, slot_iso (datetime), duration_minutes (optional).
    Uses simulation layer for provider availability; calendar for user (mock).
    """
    pid = params.get("provider_id")
    slot_iso = params.get("slot_iso") or params.get("slot")
    duration_minutes = int(params.get("duration_minutes", 30))
    if not pid or not slot_iso:
        out = {"ok": False, "valid": False, "error": "provider_id and slot_iso required"}
        if tool_log and task_id:
            tool_log(task_id, "validate_slot", params, out)
        return out
    try:
        slot = datetime.fromisoformat(slot_iso.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        out = {"ok": False, "valid": False, "error": "Invalid slot_iso format"}
        if tool_log and task_id:
            tool_log(task_id, "validate_slot", params, out)
        return out
    prov = get_provider(providers_path, pid)
    if not prov:
        out = {"ok": False, "valid": False, "error": "Provider not found"}
        if tool_log and task_id:
            tool_log(task_id, "validate_slot", params, out)
        return out
    # Actual availability check is done in simulation.availability; here we do a simple mock
    # so that the agent gets a deterministic answer. In production, this would call
    # simulation.availability.is_slot_available(prov, slot, duration_minutes).
    from simulation.availability import is_slot_available
    valid = is_slot_available(prov, slot, duration_minutes)
    out = {
        "ok": True,
        "valid": valid,
        "provider_id": pid,
        "slot_iso": slot_iso,
        "message": "Slot available" if valid else "Slot not available",
    }
    if tool_log and task_id:
        tool_log(task_id, "validate_slot", params, out)
    return out


def confirm_slot(
    params: dict[str, Any],
    providers_path: Path,
    tool_log: ToolCallLogger = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Agentic tool: confirm booking of a slot (blocks slot in calendar and provider).
    Params: provider_id, slot_iso. Returns confirmation id; TODO: calendar event id.
    """
    pid = params.get("provider_id")
    slot_iso = params.get("slot_iso") or params.get("slot")
    if not pid or not slot_iso:
        out = {"ok": False, "error": "provider_id and slot_iso required"}
        if tool_log and task_id:
            tool_log(task_id, "confirm_slot", params, out)
        return out
    # TODO: Persist booking (DB or calendar API) and prevent double booking
    out = {
        "ok": True,
        "provider_id": pid,
        "slot_iso": slot_iso,
        "confirmation_id": f"book-{pid}-{slot_iso[:10]}",
        "message": "Booking confirmed (mock).",
    }
    if tool_log and task_id:
        tool_log(task_id, "confirm_slot", params, out)
    return out
