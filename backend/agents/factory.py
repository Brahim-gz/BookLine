"""
Agent Factory: create independent voice agents (ElevenLabs Conversation) with bound tools.
Each agent has no knowledge of other agents; tools are the reasoning mechanism.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Optional

from core.providers_loader import get_provider
from core.schemas import Provider
from tools.registry import build_tool_registry, register_client_tools

logger = logging.getLogger(__name__)

# Lazy imports for ElevenLabs (optional at import time)
def _get_elevenlabs():
    from elevenlabs.client import ElevenLabs
    return ElevenLabs

def _get_conversation():
    from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
    return Conversation, ClientTools


def create_client_tools_for_agent(
    providers_path: Path,
    task_id: Optional[str],
    tool_calls_log: list,
) -> Any:
    """Build and return a ClientTools instance with our tools registered."""
    Conversation, ClientTools = _get_conversation()
    registry = build_tool_registry(providers_path, task_id=task_id, tool_calls_log=tool_calls_log)
    client_tools = ClientTools()
    register_client_tools(client_tools, registry, is_async=False)
    return client_tools


def create_voice_agent(
    provider_id: str,
    providers_path: Path,
    task_id: Optional[str],
    tool_calls_log: list,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    on_agent_response: Optional[Callable[[str], None]] = None,
) -> Any:
    """
    Create one independent voice agent for the given provider.
    Agent uses tools for calendar, provider lookup, distance, slot validation (no hardcoded logic).
    Returns the Conversation instance (not started). Caller starts session and drives with send_user_message.
    """
    ElevenLabs = _get_elevenlabs()
    Conversation, ClientTools = _get_conversation()
    from agents.audio_stub import StubAudioInterface

    client = ElevenLabs(api_key=api_key or "")
    client_tools = create_client_tools_for_agent(providers_path, task_id, tool_calls_log)
    client_tools.start()

    agent_responses: list[str] = []

    def _on_response(text: str) -> None:
        agent_responses.append(text)
        if on_agent_response:
            on_agent_response(text)

    audio = StubAudioInterface()
    conversation = Conversation(
        client=client,
        agent_id=agent_id or "default",
        requires_auth=bool(api_key),
        audio_interface=audio,
        client_tools=client_tools,
        callback_agent_response=_on_response,
    )
    # Attach for runner to read
    conversation._agent_responses = agent_responses  # type: ignore[attr-defined]
    conversation._tool_calls_log = tool_calls_log  # type: ignore[attr-defined]
    conversation._provider_id = provider_id  # type: ignore[attr-defined]
    return conversation
