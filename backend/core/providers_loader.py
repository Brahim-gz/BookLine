from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from core.schemas import AvailabilityProfile, Provider


def load_providers(path: Path) -> list[Provider]:
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    providers: list[Provider] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ap = item.get("availability_profile")
        if isinstance(ap, dict):
            item = {**item, "availability_profile": AvailabilityProfile(**ap)}
        try:
            providers.append(Provider(**item))
        except Exception:
            continue
    return providers


def get_providers_by_id(path: Path) -> dict[str, Provider]:
    return {p.id: p for p in load_providers(path)}


def get_provider(path: Path, provider_id: str) -> Optional[Provider]:
    return get_providers_by_id(path).get(provider_id)
