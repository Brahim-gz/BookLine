"""
Swarm controller: run multiple voice agents in parallel, aggregate outcomes, rank by scoring engine.
Each agent is independent and isolated; no shared state between agents.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from core.schemas import (
    NegotiationOutcome,
    PreferenceWeights,
    Provider,
    RankedSlot,
    TaskMode,
    UserRequest,
)
from core.providers_loader import load_providers, get_providers_by_id
from core.scoring import rank_outcomes
from agents.runner import run_agent_and_extract_outcome

logger = logging.getLogger(__name__)


async def run_swarm(
    providers_path: Path,
    user_request: UserRequest,
    task_id: Optional[str] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    max_agents: int = 15,
) -> tuple[list[NegotiationOutcome], list[RankedSlot], list[dict]]:
    """
    Run up to max_agents voice agents in parallel (one per provider).
    Returns (outcomes, shortlist, all_tool_calls_logs).
    Tool calls are per-agent; we aggregate into a single list for API display.
    """
    providers = load_providers(providers_path)
    if not providers:
        return [], [], []
    # Limit to max_agents
    selected = providers[:max_agents]
    provider_ids = [p.id for p in selected]
    loop = asyncio.get_event_loop()
    preferences = user_request.preferences or PreferenceWeights()

    async def run_one(pid: str) -> tuple[str, NegotiationOutcome, list[dict]]:
        # Run sync agent in executor so we don't block event loop
        outcome, tool_log, transcript = await loop.run_in_executor(
            None,
            lambda p=pid: run_agent_and_extract_outcome(
                provider_id=p,
                providers_path=providers_path,
                user_request=user_request,
                task_id=task_id,
                api_key=api_key,
                agent_id=agent_id,
            ),
        )
        outcome.transcript = transcript
        return pid, outcome, tool_log

    # Run all agents concurrently
    results = await asyncio.gather(
        *[run_one(pid) for pid in provider_ids],
        return_exceptions=True,
    )

    outcomes: list[NegotiationOutcome] = []
    all_tool_logs: list[dict] = []
    for r in results:
        if isinstance(r, Exception):
            logger.exception("Agent run failed: %s", r)
            continue
        pid, outcome, tool_log = r
        outcomes.append(outcome)
        all_tool_logs.extend(tool_log)

    by_id = get_providers_by_id(providers_path)
    shortlist = rank_outcomes(outcomes, by_id, preferences)
    return outcomes, shortlist, all_tool_logs


def run_single_agent(
    provider_id: str,
    providers_path: Path,
    user_request: UserRequest,
    task_id: Optional[str] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> tuple[NegotiationOutcome, list[RankedSlot], list[dict], list]:
    """
    Single-call mode: one agent, one provider. Returns (outcome, shortlist, tool_log, transcript).
    """
    outcome, tool_log, transcript = run_agent_and_extract_outcome(
        provider_id=provider_id,
        providers_path=providers_path,
        user_request=user_request,
        task_id=task_id,
        api_key=api_key,
        agent_id=agent_id,
    )
    outcome.transcript = transcript
    by_id = get_providers_by_id(providers_path)
    preferences = user_request.preferences or PreferenceWeights()
    shortlist = rank_outcomes([outcome], by_id, preferences)
    return outcome, shortlist, tool_log, transcript
