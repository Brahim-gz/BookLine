"""
Distance tool: travel time / distance for ranking and user preference.
Can be extended with real routing API (e.g. Google Maps); MVP uses stored distance_km.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from core.providers_loader import get_provider

ToolCallLogger = Optional[Callable[[str, str, dict[str, Any], Any], None]]


def get_distance(
    params: dict[str, Any],
    providers_path: Path,
    tool_log: ToolCallLogger = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Agentic tool: get distance (and optional travel time) to a provider.
    Params: provider_id. Returns distance_km; TODO: travel_time_minutes from routing API.
    """
    pid = params.get("provider_id")
    if not pid:
        out = {"ok": False, "error": "provider_id required"}
        if tool_log and task_id:
            tool_log(task_id, "get_distance", params, out)
        return out
    prov = get_provider(providers_path, pid)
    if not prov:
        out = {"ok": False, "error": "Provider not found", "provider_id": pid}
        if tool_log and task_id:
            tool_log(task_id, "get_distance", params, out)
        return out
    # TODO: Real routing API for travel_time_minutes
    out = {
        "ok": True,
        "provider_id": pid,
        "distance_km": prov.distance_km,
        "travel_time_minutes": int(prov.distance_km * 2.5),  # mock: ~24 km/h average
    }
    if tool_log and task_id:
        tool_log(task_id, "get_distance", params, out)
    return out
