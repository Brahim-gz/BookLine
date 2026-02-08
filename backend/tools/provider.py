from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from core.providers_loader import get_provider, get_providers_by_id
from core.schemas import Provider

ToolCallLogger = Optional[Callable[[str, str, dict[str, Any], Any], None]]


def provider_lookup(
    params: dict[str, Any],
    providers_path: Path,
    tool_log: ToolCallLogger = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    pid = params.get("provider_id")
    if not pid:
        out = {"ok": False, "error": "provider_id required"}
        if tool_log and task_id:
            tool_log(task_id, "provider_lookup", params, out)
        return out
    prov = get_provider(providers_path, pid)
    if not prov:
        out = {"ok": False, "error": "Provider not found", "provider_id": pid}
        if tool_log and task_id:
            tool_log(task_id, "provider_lookup", params, out)
        return out
    out = {
        "ok": True,
        "provider_id": prov.id,
        "name": prov.name,
        "rating": prov.rating,
        "distance_km": prov.distance_km,
        "receptionist_style": prov.receptionist_style,
    }
    if tool_log and task_id:
        tool_log(task_id, "provider_lookup", params, out)
    return out


def list_providers(
    params: dict[str, Any],
    providers_path: Path,
    tool_log: ToolCallLogger = None,
    task_id: Optional[str] = None,
) -> dict[str, Any]:
    by_id = get_providers_by_id(providers_path)
    out = {
        "ok": True,
        "providers": [
            {"provider_id": p.id, "name": p.name, "rating": p.rating, "distance_km": p.distance_km}
            for p in by_id.values()
        ],
    }
    if tool_log and task_id:
        tool_log(task_id, "list_providers", params, out)
    return out
