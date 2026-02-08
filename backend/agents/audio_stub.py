from __future__ import annotations

from typing import Callable

try:
    from elevenlabs.conversational_ai.conversation import AudioInterface as _AudioInterface
except ImportError:
    _AudioInterface = object


class StubAudioInterface(_AudioInterface):
    def start(self, input_callback: Callable[[bytes], None]) -> None:
        self._input_callback = input_callback

    def stop(self) -> None:
        self._input_callback = None

    def output(self, audio: bytes) -> None:
        pass

    def interrupt(self) -> None:
        pass
