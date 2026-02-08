from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import get_settings

router = APIRouter()


class RatingRequest(BaseModel):
    provider_id: Optional[str] = Field(None, description="Provider ID from our registry")
    place_id: Optional[str] = Field(None, description="Google Place ID for Places API rating")


class DistanceRequest(BaseModel):
    provider_id: str = Field(..., description="Provider ID")
    origin: Optional[str] = Field(None, description="User origin address or lat,lng for Distance Matrix")


class AvailabilityRequest(BaseModel):
    time_min_iso: Optional[str] = Field(None, description="Start of window (ISO datetime)")
    time_max_iso: Optional[str] = Field(None, description="End of window (ISO datetime)")
    duration_minutes: int = Field(30, ge=15, le=120, description="Slot duration in minutes")


class UserWeightingRequest(BaseModel):
    pass


def _providers_path() -> Path:
    s = get_settings()
    p = getattr(s, "providers_json_path", None)
    return Path(p) if p else Path(__file__).resolve().parent.parent.parent / "data" / "providers.json"


@router.post("/rating", response_model=dict)
async def tool_rating(body: RatingRequest) -> dict[str, Any]:
    from integrations.google_places import get_place_rating_by_place_id, get_provider_rating
    if body.place_id:
        out = get_place_rating_by_place_id(body.place_id)
        return out
    if body.provider_id:
        return get_provider_rating(body.provider_id, _providers_path())
    return {"ok": False, "error": "Provide provider_id or place_id"}


@router.post("/distance", response_model=dict)
async def tool_distance(body: DistanceRequest) -> dict[str, Any]:
    from integrations.google_maps_distance import get_provider_distance
    return get_provider_distance(
        body.provider_id,
        origin=body.origin,
        providers_path=_providers_path(),
    )


@router.post("/availability", response_model=dict)
async def tool_availability(body: AvailabilityRequest) -> dict[str, Any]:
    from integrations.google_calendar import get_freebusy, get_available_slots
    now = datetime.utcnow()
    time_min = now
    time_max = now + timedelta(days=14)
    if body.time_min_iso:
        try:
            time_min = datetime.fromisoformat(body.time_min_iso.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    if body.time_max_iso:
        try:
            time_max = datetime.fromisoformat(body.time_max_iso.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    slots = get_available_slots(time_min, time_max, duration_minutes=body.duration_minutes)
    return {"ok": True, "slots": slots, "time_min": time_min.isoformat(), "time_max": time_max.isoformat()}


@router.post("/user-weighting", response_model=dict)
async def tool_user_weighting(body: UserWeightingRequest) -> dict[str, Any]:
    get_settings()
    return {
        "ok": True,
        "availability_weight": 0.5,
        "rating_weight": 0.3,
        "distance_weight": 0.2,
        "message": "Use these weights to rank providers: availability, rating, distance.",
    }
