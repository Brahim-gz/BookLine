from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from app.config import get_settings
from core.providers_loader import get_provider

DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


def is_google_maps_configured() -> bool:
    return bool(get_settings().google_maps_api_key)


def get_distance_matrix(origin: str, destination: str) -> dict[str, Any]:
    api_key = get_settings().google_maps_api_key
    if not api_key:
        return {"ok": False, "error": "Google Maps API key not configured"}
    try:
        import httpx
    except ImportError:
        return {"ok": False, "error": "httpx required"}
    params = {"origins": origin, "destinations": destination, "key": api_key}
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(DISTANCE_MATRIX_URL, params=params)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if resp.status_code != 200:
        return {"ok": False, "error": f"Maps API returned {resp.status_code}"}
    try:
        data = resp.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON response"}
    if data.get("status") != "OK":
        return {"ok": False, "error": data.get("error_message", data.get("status", "Unknown error"))}
    rows = data.get("rows") or []
    if not rows:
        return {"ok": False, "error": "No rows in response"}
    elements = rows[0].get("elements") or []
    if not elements:
        return {"ok": False, "error": "No elements in response"}
    el = elements[0]
    if el.get("status") != "OK":
        return {"ok": False, "error": el.get("status", "No route found")}
    dist = el.get("distance", {}).get("value")  # meters
    dura = el.get("duration", {}).get("value")  # seconds
    if dist is None or dura is None:
        return {"ok": False, "error": "Missing distance or duration"}
    return {
        "ok": True,
        "distance_km": round(dist / 1000.0, 2),
        "duration_minutes": max(1, int(dura / 60)),
    }


def get_provider_distance(
    provider_id: str,
    origin: Optional[str] = None,
    providers_path: Optional[Path] = None,
) -> dict[str, Any]:
    settings = get_settings()
    path = providers_path or settings.providers_json_path
    path = Path(path) if path else path
    prov = get_provider(path, provider_id) if path and path.exists() else None
    if not prov:
        return {"ok": False, "error": "Provider not found", "provider_id": provider_id}
    dest = prov.address
    if origin and dest and is_google_maps_configured():
        out = get_distance_matrix(origin, dest)
        if out.get("ok"):
            out["provider_id"] = provider_id
            return out
    return {
        "ok": True,
        "provider_id": provider_id,
        "distance_km": prov.distance_km,
        "duration_minutes": max(1, int(prov.distance_km * 2.5)),
        "source": "local",
    }
