"""
Run one voice agent: start Conversation, drive with user/receptionist messages, extract outcome.
Uses simulation for receptionist replies when doing multi-turn negotiation.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from core.schemas import NegotiationOutcome, TranscriptTurn, UserRequest
from core.providers_loader import get_provider
from simulation.receptionist import generate_receptionist_response

from agents.factory import create_voice_agent
from agents.outcome import extract_outcome

logger = logging.getLogger(__name__)


def run_agent_sync(
    provider_id: str,
    providers_path: str,
    user_request: UserRequest,
    task_id: Optional[str] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    max_turns: int = 8,
    turn_timeout_seconds: float = 30.0,
) -> tuple[list[dict], str | None, list[TranscriptTurn]]:
    """
    Run one agent against one provider; return (tool_calls_log, last_agent_message, transcript).
    Transcript is ordered turns (receptionist, agent, receptionist, agent, ...) for frontend display.
    """
    tool_calls_log: list[dict] = []
    transcript: list[TranscriptTurn] = []
    last_agent_message: Optional[str] = None
    path = Path(providers_path) if not isinstance(providers_path, Path) else providers_path

    def on_response(text: str) -> None:
        nonlocal last_agent_message
        last_agent_message = text

    conversation = create_voice_agent(
        provider_id=provider_id,
        providers_path=path,
        task_id=task_id,
        tool_calls_log=tool_calls_log,
        api_key=api_key,
        agent_id=agent_id,
        on_agent_response=on_response,
    )
    agent_responses = conversation._agent_responses  # type: ignore[attr-defined]

    conversation.start_session()
    # Allow WebSocket to connect
    time.sleep(2.0)

    try:
        provider = get_provider(path, provider_id)
        initial_user_message = (
            f"{user_request.message} You are calling the dental office for provider {provider_id}"
            + (f" ({provider.name})." if provider else ".")
        )
        conversation.send_user_message(initial_user_message)
        transcript.append(TranscriptTurn(role="receptionist", text=initial_user_message))

        for turn in range(max_turns - 1):
            deadline = time.monotonic() + turn_timeout_seconds
            while time.monotonic() < deadline and len(agent_responses) <= turn:
                time.sleep(0.3)
            if len(agent_responses) <= turn:
                break
            agent_text = agent_responses[turn]
            transcript.append(TranscriptTurn(role="agent", text=agent_text))
            if not agent_text or not provider:
                break
            receptionist_reply = generate_receptionist_response(
                provider,
                agent_text,
                context={"from_date": None, "days_ahead": 14},
            )
            conversation.send_user_message(receptionist_reply)
            transcript.append(TranscriptTurn(role="receptionist", text=receptionist_reply))
        # Wait for any final response
        time.sleep(3.0)
        if agent_responses:
            last_agent_message = agent_responses[-1]
            if not transcript or transcript[-1].role != "agent":
                transcript.append(TranscriptTurn(role="agent", text=last_agent_message))
    except RuntimeError as e:
        logger.warning("Conversation send/wait error: %s", e)
    finally:
        conversation.end_session()
        try:
            conversation.wait_for_session_end()
        except Exception:
            pass

    return tool_calls_log, last_agent_message, transcript


def run_agent_and_extract_outcome(
    provider_id: str,
    providers_path: Path | str,
    user_request: UserRequest,
    task_id: Optional[str] = None,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> tuple[NegotiationOutcome, list[dict], list[TranscriptTurn]]:
    """Run agent and return (NegotiationOutcome, tool_calls_log, transcript) for use by swarm/tasks."""
    tool_calls_log, last_message, transcript = run_agent_sync(
        provider_id=provider_id,
        providers_path=providers_path,
        user_request=user_request,
        task_id=task_id,
        api_key=api_key,
        agent_id=agent_id,
    )
    outcome = extract_outcome(provider_id, tool_calls_log, last_message)
    return outcome, tool_calls_log, transcript
