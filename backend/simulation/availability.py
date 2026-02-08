"""
Availability generation based on provider profiles.
No fixed dates or hardcoded slots; deterministic from profile and current time.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Tuple

from core.schemas import AvailabilityProfile, Provider


def _parse_time(t: str) -> Tuple[int, int]:
    """Parse 'HH:MM' -> (hour, minute)."""
    parts = t.strip().split(":")
    h = int(parts[0]) if len(parts) > 0 else 9
    m = int(parts[1]) if len(parts) > 1 else 0
    return h, m


def get_available_slots(
    provider: Provider,
    from_date: datetime,
    days_ahead: int = 14,
    duration_minutes: int | None = None,
) -> List[datetime]:
    """
    Generate available slot starts for a provider based on availability_profile.
    No fixed dates; slots are derived from weekday_hours, weekend_enabled, slot_duration.
    """
    profile = provider.availability_profile
    duration = duration_minutes or profile.slot_duration_minutes
    open_h, open_m = _parse_time(profile.weekday_hours[0])
    close_h, close_m = _parse_time(profile.weekday_hours[1])
    slots: List[datetime] = []
    day = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
    for _ in range(days_ahead):
        if day.weekday() >= 5 and not profile.weekend_enabled:
            day += timedelta(days=1)
            continue
        current = day.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
        end_of_day = day.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
        while current + timedelta(minutes=duration + profile.buffer_minutes) <= end_of_day:
            if current >= from_date:
                slots.append(current)
            current += timedelta(minutes=profile.slot_duration_minutes + profile.buffer_minutes)
        day += timedelta(days=1)
    return slots


def is_slot_available(
    provider: Provider,
    slot: datetime,
    duration_minutes: int = 30,
) -> bool:
    """
    Check if a given slot is within provider's availability profile.
    Used by slot validation tool; no persistence of "booked" slots in MVP (mock).
    """
    profile = provider.availability_profile
    if slot.weekday() >= 5 and not profile.weekend_enabled:
        return False
    open_h, open_m = _parse_time(profile.weekday_hours[0])
    close_h, close_m = _parse_time(profile.weekday_hours[1])
    start = slot.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
    end = slot.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    if slot < start:
        return False
    if slot + timedelta(minutes=duration_minutes + profile.buffer_minutes) > end:
        return False
    # TODO: Cross-check with actual booked slots (DB or calendar) to prevent double booking
    return True
