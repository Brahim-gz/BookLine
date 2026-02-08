"""
Extract NegotiationOutcome from agent run: tool calls log and optional agent response.
Decoupled from agent logic; pure function over structured logs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from core.schemas import NegotiationOutcome


def extract_outcome(
    provider_id: str,
    tool_calls_log: list[dict[str, Any]],
    agent_final_message: Optional[str] = None,
) -> NegotiationOutcome:
    """
    Build NegotiationOutcome from one agent's tool_calls_log and optional final message.
    - proposed_slot: from last validate_slot(valid=True) or confirm_slot; or None.
    - confidence_score: 1.0 if confirm_slot succeeded, else from validate_slot or 0.5.
    - rejection_reasons: from tool errors or agent message hints.
    """
    proposed_slot: Optional[datetime] = None
    confidence = 0.5
    rejection_reasons: list[str] = []

    for entry in tool_calls_log:
        tool = entry.get("tool") or entry.get("tool_name")
        params = entry.get("params") or {}
        result = entry.get("result") or {}
        if isinstance(result, dict):
            if tool == "validate_slot" and result.get("valid") and result.get("slot_iso"):
                try:
                    proposed_slot = datetime.fromisoformat(
                        str(result["slot_iso"]).replace("Z", "+00:00")
                    )
                    confidence = 0.85
                except (ValueError, TypeError):
                    pass
            if tool == "confirm_slot" and result.get("ok") and result.get("slot_iso"):
                try:
                    proposed_slot = datetime.fromisoformat(
                        str(result["slot_iso"]).replace("Z", "+00:00")
                    )
                    confidence = 1.0
                except (ValueError, TypeError):
                    pass
            if not result.get("ok") and result.get("error"):
                rejection_reasons.append(str(result.get("error")))

    if agent_final_message and "sorry" in agent_final_message.lower() and not proposed_slot:
        rejection_reasons.append("Agent reported inability to book.")

    return NegotiationOutcome(
        provider_id=provider_id,
        proposed_slot=proposed_slot,
        confidence_score=min(1.0, max(0.0, confidence)),
        rejection_reasons=rejection_reasons[:5],
        raw_metadata={"tool_calls_count": len(tool_calls_log)},
    )
