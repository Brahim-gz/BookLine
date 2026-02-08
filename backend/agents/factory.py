from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Optional

from app.config import get_settings
from core.providers_loader import get_provider
from core.schemas import Provider
from tools.registry import build_tool_registry, register_client_tools

logger = logging.getLogger(__name__)


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
    conversation._agent_responses = agent_responses
    conversation._tool_calls_log = tool_calls_log
    conversation._provider_id = provider_id
    return conversation


def create_receptionist_conversation(
    provider: Provider,
    providers_path: Path,
    api_key: Optional[str] = None,
    agent_id: Optional[str] = None,
    on_receptionist_response: Optional[Callable[[str], None]] = None,
) -> Any:
    ElevenLabs = _get_elevenlabs()
    Conversation, ClientTools = _get_conversation()
    from agents.audio_stub import StubAudioInterface

    settings = get_settings()
    receptionist_agent_id = getattr(settings, "elevenlabs_receptionist_agent_id", None) or agent_id or "default"

    client_tools = ClientTools()
    register_client_tools(client_tools, {}, is_async=False)
    client_tools.start()

    receptionist_responses: list[str] = []

    def _on_response(text: str) -> None:
        receptionist_responses.append(text)
        if on_receptionist_response:
            on_receptionist_response(text)

    client = ElevenLabs(api_key=api_key or "")
    audio = StubAudioInterface()
    conversation = Conversation(
        client=client,
        agent_id=receptionist_agent_id,
        requires_auth=bool(api_key),
        audio_interface=audio,
        client_tools=client_tools,
        callback_agent_response=_on_response,
    )
    conversation._receptionist_responses = receptionist_responses
    return conversation
