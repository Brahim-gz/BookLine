"""
Appointments API: confirm a booking from the shortlist.
Prevents double booking by validating against task state; TODO: calendar integration.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.schemas import BookedAppointment, ConfirmAppointmentRequest, TaskStatus
from api.routes.tasks import _tasks, _tasks_lock

router = APIRouter()


class ConfirmResponse(BaseModel):
    ok: bool
    appointment: BookedAppointment | None = None
    error: str | None = None


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_appointment(body: ConfirmAppointmentRequest) -> ConfirmResponse:
    """
    Confirm one of the shortlisted slots. Validates that (task_id, provider_id, slot)
    appears in the task's shortlist to prevent double booking / invalid selection.
    """
    async with _tasks_lock:
        state = _tasks.get(body.task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Task not found")
    if state.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Task must be completed before confirming an appointment.",
        )
    # Check slot is in shortlist
    match = None
    for s in state.shortlist:
        if s.provider_id == body.provider_id and s.slot == body.slot:
            match = s
            break
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Selected provider_id and slot are not in the task shortlist.",
        )
    calendar_event_id = None
    calendar_link = None
    try:
        from integrations.google_calendar import is_google_calendar_configured, create_event
        if is_google_calendar_configured():
            start_iso = body.slot.isoformat()
            end_iso = (body.slot + timedelta(minutes=30)).isoformat()
            ev = create_event(start_iso=start_iso, end_iso=end_iso, summary=f"Dental appointment – {body.provider_id}")
            if ev.get("ok"):
                calendar_event_id = ev.get("event_id")
                calendar_link = ev.get("html_link")
    except Exception:
        pass
    appointment = BookedAppointment(
        task_id=body.task_id,
        provider_id=body.provider_id,
        slot=body.slot,
        calendar_event_id=calendar_event_id,
        calendar_link=calendar_link,
    )
    async with _tasks_lock:
        state = _tasks.get(body.task_id)
        if state:
            state.confirmed_appointment = appointment
    return ConfirmResponse(ok=True, appointment=appointment)
