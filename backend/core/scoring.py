"""
Scoring engine: ranks negotiation outcomes by availability, rating, distance.
Uses user preference weights; no hardcoded provider logic.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from core.schemas import NegotiationOutcome, PreferenceWeights, Provider, RankedSlot

if TYPE_CHECKING:
    pass


def _normalize(x: float, low: float, high: float) -> float:
    """Map value to [0, 1] given expected range; clamp if outside."""
    if high <= low:
        return 1.0
    return max(0.0, min(1.0, (x - low) / (high - low)))


def rank_outcomes(
    outcomes: list[NegotiationOutcome],
    providers_by_id: dict[str, Provider],
    preferences: PreferenceWeights,
    now: datetime | None = None,
) -> list[RankedSlot]:
    """
    Aggregate structured outcomes into a shortlist.
    - Earliest availability: earlier slot -> higher score component
    - Rating: higher provider rating -> higher component
    - Distance: shorter distance -> higher component
    Weights from preferences; no double booking (each outcome is one provider).
    """
    now = now or datetime.utcnow()
    slots: list[RankedSlot] = []
    # Collect only outcomes with a proposed slot
    for o in outcomes:
        if o.proposed_slot is None or o.provider_id not in providers_by_id:
            continue
        prov = providers_by_id[o.provider_id]
        # Normalize: availability = earlier is better (score 1 for "soonest" relative to others)
        # We'll do a second pass to normalize across all slots
        slots.append(
            RankedSlot(
                provider_id=o.provider_id,
                provider_name=prov.name,
                slot=o.proposed_slot,
                score=0.0,  # computed below
                rank=0,
            )
        )

    if not slots:
        return []

    # Ranges for normalization
    times = [s.slot for s in slots]
    earliest = min(times)
    latest = max(times)
    ratings = [providers_by_id[s.provider_id].rating for s in slots]
    dists = [providers_by_id[s.provider_id].distance_km for s in slots]
    min_r, max_r = min(ratings), max(ratings)
    min_d, max_d = min(dists), max(dists)
    # For time: earlier is better, so we score (latest - t) / (latest - earliest) -> earlier = higher
    time_span = (latest - earliest).total_seconds() if latest != earliest else 1.0

    scored: list[tuple[RankedSlot, float]] = []
    for s in slots:
        prov = providers_by_id[s.provider_id]
        t_norm = (
            (latest - s.slot).total_seconds() / time_span
            if time_span else 1.0
        )
        r_norm = _normalize(prov.rating, min_r, max_r) if max_r > min_r else 1.0
        # Distance: shorter is better -> invert so higher = better
        d_norm = 1.0 - _normalize(prov.distance_km, min_d, max_d) if max_d > min_d else 1.0
        score = (
            preferences.availability_weight * t_norm
            + preferences.rating_weight * r_norm
            + preferences.distance_weight * d_norm
        )
        scored.append((s, score))

    scored.sort(key=lambda x: -x[1])
    result: list[RankedSlot] = []
    for rank, (s, score) in enumerate(scored, start=1):
        s.score = round(score, 4)
        s.rank = rank
        result.append(s)
    return result
