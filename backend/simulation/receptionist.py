from __future__ import annotations

from datetime import datetime
from typing import Optional

from core.schemas import Provider
from simulation.availability import get_available_slots


def generate_receptionist_response(
    provider: Provider,
    agent_message: str,
    context: dict | None = None,
) -> str:
    context = context or {}
    style = (provider.receptionist_style or "professional").lower()
    from_dt = context.get("from_date") or datetime.utcnow()
    if isinstance(from_dt, str):
        from_dt = datetime.fromisoformat(from_dt.replace("Z", "+00:00"))
    days = int(context.get("days_ahead", 14))
    duration = int(context.get("duration_minutes", 30))
    slots = get_available_slots(provider, from_dt, days_ahead=days, duration_minutes=duration)
    slot_strs = [s.strftime("%A %Y-%m-%d at %H:%M") for s in slots[:5]]
    if not slot_strs:
        if "friendly" in style or "warm" in style:
            return "I'm so sorry, we're fully booked for the next while. Would you like to be waitlisted?"
        if "brief" in style:
            return "No availability in the requested period."
        return "We don't have any available slots in that period. I can suggest calling back later."
    if "brief" in style:
        return f"We have: {', '.join(slot_strs)}. Which do you prefer?"
    if "friendly" in style or "warm" in style:
        return f"Sure! We have a few options: {', '.join(slot_strs)}. Let me know which works for you."
    if "formal" in style:
        return f"Available slots are as follows: {'; '.join(slot_strs)}. Please confirm your choice."
    return f"Our next available slots are: {', '.join(slot_strs)}. Which one would you like to book?"


def build_receptionist_context_message(
    provider: Provider,
    caller_message: str,
    from_date: datetime | None = None,
    days_ahead: int = 14,
    duration_minutes: int = 30,
    max_slots: int = 10,
) -> str:
    from_dt = from_date or datetime.utcnow()
    slots = get_available_slots(provider, from_dt, days_ahead=days_ahead, duration_minutes=duration_minutes)
    slot_strs = [s.strftime("%A %Y-%m-%d at %H:%M") for s in slots[:max_slots]]
    slots_part = ", ".join(slot_strs) if slot_strs else "No availability in the requested period."
    return (
        f"You are the receptionist at {provider.name} (dental office). "
        f"Our available slots are: {slots_part}. "
        f"The caller just said: {caller_message!r}. "
        "Respond briefly and naturally as the receptionist."
    )


def get_next_available(
    provider: Provider,
    from_date: datetime | None = None,
) -> datetime | None:
    from_date = from_date or datetime.utcnow()
    slots = get_available_slots(provider, from_date, days_ahead=30)
    return slots[0] if slots else None
