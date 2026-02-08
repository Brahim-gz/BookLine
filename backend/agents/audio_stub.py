"""
Stub audio interface for backend-only operation (no mic/speaker).
Allows ElevenLabs Conversation to run without pyaudio; conversation can be driven via send_user_message.
"""
from __future__ import annotations

from typing import Callable

# Lazy import to avoid hard dependency at import time; required for Conversation.
try:
    from elevenlabs.conversational_ai.conversation import AudioInterface as _AudioInterface
except ImportError:
    _AudioInterface = object  # type: ignore[misc, assignment]


class StubAudioInterface(_AudioInterface):
    """
    Minimal AudioInterface implementation for server-side use.
    - start: stores input_callback; no real audio device.
    - output: no-op (agent audio is not played).
    - interrupt: no-op.
    Used when driving the conversation via send_user_message (text) instead of live audio.
    """

    def start(self, input_callback: Callable[[bytes], None]) -> None:
        self._input_callback = input_callback
        # Optionally feed silence so the connection stays alive; many agents accept text via send_user_message.
        # We do not push any audio here; the client sends user turns as text.

    def stop(self) -> None:
        self._input_callback = None

    def output(self, audio: bytes) -> None:
        # Discard; no speaker in backend.
        pass

    def interrupt(self) -> None:
        pass
