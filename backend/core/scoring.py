from __future__ import annotations

from core.schemas import NegotiationOutcome, PreferenceWeights, Provider, RankedSlot


def rank_outcomes_by_agent(
    outcomes: list[NegotiationOutcome],
    providers_by_id: dict[str, Provider],
) -> list[RankedSlot]:
    slots: list[RankedSlot] = []
    for o in outcomes:
        if o.proposed_slot is None or o.provider_id not in providers_by_id:
            continue
        prov = providers_by_id[o.provider_id]
        slots.append(
            RankedSlot(
                provider_id=o.provider_id,
                provider_name=prov.name,
                slot=o.proposed_slot,
                score=round(o.confidence_score, 4),
                rank=0,
            )
        )
    if not slots:
        return []
    slots.sort(key=lambda s: -s.score)
    for rank, s in enumerate(slots, start=1):
        s.rank = rank
    return slots


def rank_outcomes(
    outcomes: list[NegotiationOutcome],
    providers_by_id: dict[str, Provider],
    preferences: PreferenceWeights,
    now=None,
) -> list[RankedSlot]:
    return rank_outcomes_by_agent(outcomes, providers_by_id)
