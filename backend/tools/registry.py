"""
Tool registry: build ClientTools with bound context (providers path, task_id, logging).
Decoupled from agent logic; all tools explicit and logged.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from tools import calendar, distance, provider, slots


def _tool_log_callback(task_id: Optional[str], log_append: Optional[Callable[[dict], None]]) -> Optional[Callable[[str, str, dict, Any], None]]:
    if not task_id or not log_append:
        return None
    def log(name: str, params: dict, result: Any) -> None:
        log_append({"tool": name, "params": params, "result": result})
    return log


def build_tool_registry(
    providers_path: Path,
    task_id: Optional[str] = None,
    tool_calls_log: Optional[list] = None,
) -> dict[str, Callable[..., dict[str, Any]]]:
    """
    Return a dict of tool_name -> callable for registration with ElevenLabs ClientTools.
    Each callable takes a single `params` dict (from the agent) and returns a dict.
    """
    def append_log(entry: dict) -> None:
        if tool_calls_log is not None:
            tool_calls_log.append(entry)

    tool_log = _tool_log_callback(task_id, append_log)

    def check_availability(params: dict) -> dict:
        return calendar.check_availability(params, providers_path, tool_log, task_id)

    def get_busy_windows(params: dict) -> dict:
        return calendar.get_busy_windows(params, providers_path, tool_log, task_id)

    def provider_lookup(params: dict) -> dict:
        return provider.provider_lookup(params, providers_path, tool_log, task_id)

    def list_providers(params: dict) -> dict:
        return provider.list_providers(params, providers_path, tool_log, task_id)

    def get_distance(params: dict) -> dict:
        return distance.get_distance(params, providers_path, tool_log, task_id)

    def validate_slot(params: dict) -> dict:
        return slots.validate_slot(params, providers_path, tool_log, task_id)

    def confirm_slot(params: dict) -> dict:
        return slots.confirm_slot(params, providers_path, tool_log, task_id)

    return {
        "check_availability": check_availability,
        "get_busy_windows": get_busy_windows,
        "provider_lookup": provider_lookup,
        "list_providers": list_providers,
        "get_distance": get_distance,
        "validate_slot": validate_slot,
        "confirm_slot": confirm_slot,
    }


def register_client_tools(
    client_tools_obj: Any,
    registry: dict[str, Callable[..., dict[str, Any]]],
    is_async: bool = False,
) -> None:
    """
    Register our tools with ElevenLabs ClientTools.
    client_tools_obj: instance of elevenlabs.conversational_ai.conversation.ClientTools
    """
    for name, fn in registry.items():
        client_tools_obj.register(name, fn, is_async=is_async)
