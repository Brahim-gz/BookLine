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
    out = {
        "ok": True,
        "provider_id": pid,
        "distance_km": prov.distance_km,
        "travel_time_minutes": int(prov.distance_km * 2.5),
    }
    if tool_log and task_id:
        tool_log(task_id, "get_distance", params, out)
    return out
