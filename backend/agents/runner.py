from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.schemas import NegotiationOutcome, TranscriptTurn, UserRequest
from core.providers_loader import get_provider
from simulation.receptionist import build_receptionist_context_message, generate_receptionist_response

from agents.factory import create_receptionist_conversation, create_voice_agent
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
    tool_calls_log: list[dict] = []
    transcript: list[TranscriptTurn] = []
    last_agent_message: Optional[str] = None
    path = Path(providers_path) if not isinstance(providers_path, Path) else providers_path
    provider = get_provider(path, provider_id)

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
    agent_responses = conversation._agent_responses

    use_two_agents = provider is not None
    recipient_conversation = None
    receptionist_responses: list[str] = []
    if use_two_agents:
        try:
            recipient_conversation = create_receptionist_conversation(
                provider=provider,
                providers_path=path,
                api_key=api_key,
                agent_id=agent_id,
            )
            receptionist_responses = recipient_conversation._receptionist_responses
        except Exception as e:
            logger.warning("Could not create recipient conversation, falling back to scripted receptionist: %s", e)
            use_two_agents = False

    conversation.start_session()
    if recipient_conversation:
        try:
            recipient_conversation.start_session()
        except Exception as e:
            logger.warning("Could not start recipient session, falling back to scripted receptionist: %s", e)
            use_two_agents = False
            recipient_conversation = None

    time.sleep(2.0)

    try:
        initial_user_message = (
            f"{user_request.message} You are calling the dental office for provider {provider_id}"
            + (f" ({provider.name})." if provider else ".")
        )
        conversation.send_user_message(initial_user_message)

        if use_two_agents and recipient_conversation:
            for turn in range(max_turns):
                deadline = time.monotonic() + turn_timeout_seconds
                while time.monotonic() < deadline and len(agent_responses) <= turn:
                    time.sleep(0.3)
                if len(agent_responses) <= turn:
                    break
                agent_text = agent_responses[turn]
                transcript.append(TranscriptTurn(role="agent", text=agent_text))
                if not agent_text.strip():
                    break
                context_message = build_receptionist_context_message(
                    provider,
                    agent_text,
                    from_date=datetime.utcnow(),
                    days_ahead=14,
                    duration_minutes=30,
                )
                recipient_conversation.send_user_message(context_message)
                deadline = time.monotonic() + turn_timeout_seconds
                while time.monotonic() < deadline and len(receptionist_responses) <= turn:
                    time.sleep(0.3)
                if len(receptionist_responses) <= turn:
                    break
                receptionist_reply = receptionist_responses[turn]
                transcript.append(TranscriptTurn(role="receptionist", text=receptionist_reply))
                if not receptionist_reply.strip():
                    break
                conversation.send_user_message(receptionist_reply)
            time.sleep(2.0)
            if agent_responses:
                last_agent_message = agent_responses[-1]
                if transcript and transcript[-1].role != "agent":
                    transcript.append(TranscriptTurn(role="agent", text=last_agent_message))
        else:
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
        if recipient_conversation:
            try:
                recipient_conversation.end_session()
                recipient_conversation.wait_for_session_end()
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
