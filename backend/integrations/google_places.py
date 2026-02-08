from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from app.config import get_settings

def is_google_places_configured() -> bool:
    return bool(get_settings().google_places_api_key)


def get_place_rating_by_place_id(place_id: str) -> dict[str, Any]:
    api_key = get_settings().google_places_api_key
    if not api_key:
        return {"ok": False, "error": "Google Places API key not configured"}
    try:
        import httpx
    except ImportError:
        return {"ok": False, "error": "httpx required"}
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": "rating,userRatingCount"}
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if resp.status_code != 200:
        return {"ok": False, "error": f"Places API returned {resp.status_code}"}
    try:
        data = resp.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON response"}
    rating = data.get("rating")
    total = data.get("userRatingCount", 0)
    if rating is None:
        return {"ok": True, "rating": None, "user_ratings_total": total, "message": "No rating for this place"}
    return {"ok": True, "rating": float(rating), "user_ratings_total": int(total)}


def get_provider_rating(provider_id: str, providers_path: Optional[Path] = None) -> dict[str, Any]:
    from core.providers_loader import get_provider
    settings = get_settings()
    path = providers_path or settings.providers_json_path
    path = Path(path) if path else path
    prov = get_provider(path, provider_id) if path and path.exists() else None
    if prov:
        return {"ok": True, "rating": prov.rating, "provider_id": provider_id, "source": "local"}
    return {"ok": False, "error": "Provider not found", "provider_id": provider_id}
