from __future__ import annotations

import logging
import time
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Optional

from src.commands import CommandRouter
from src.config import Settings
from src.gemini_client import GeminiClient
from src.stt import Listener
from src.tts import Speaker


class VoiceAssistant:
    def __init__(
        self,
        settings: Settings,
        state_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._settings = settings
        self._state_callback = state_callback

        self._speaker = Speaker(
            rate=settings.voice_rate,
            volume=settings.voice_volume,
            gender=settings.voice_gender,
        )
        self._listener = Listener(
            stt_engine=settings.stt_engine,
            language=settings.language,
            whisper_model=settings.whisper_model,
            timeout=settings.stt_timeout,
            phrase_time_limit=settings.stt_phrase_time_limit,
            ambient_calibration_seconds=settings.ambient_calibration_seconds,
            operation_timeout=settings.stt_operation_timeout,
            dynamic_energy=settings.dynamic_energy,
            energy_threshold=settings.energy_threshold,
            pause_threshold=settings.pause_threshold,
            non_speaking_duration=settings.non_speaking_duration,
            microphone_index=settings.microphone_index,
        )
        self._router = CommandRouter(confirmation_required=settings.command_confirmation)
        self._gemini = GeminiClient(settings=settings)

        self._stop_words = {"stop", "shutdown", "exit", "quit", "goodbye"}
        self._stt_error_streak = 0
        self._ai_unavailable_announced = False
        self._last_executed_query = ""
        self._last_executed_at = 0.0
        self._dedup_window_seconds = 5.0
        self._post_speak_cooldown_seconds = 1.0
        self._no_ai_tokens = {
            "telugu",
            "hindi",
            "english",
            "video",
            "song",
            "music",
            "youtube",
        }

    def _set_state(self, state: str) -> None:
        if self._state_callback is None:
            return
        try:
            self._state_callback(state)
        except Exception:
            self._logger.exception("State callback failed")

    def _strip_wake_word(self, text: str) -> str:
        wake = self._settings.wake_word
        lowered = text.lower().strip()
        if lowered.startswith(wake):
            return text[len(wake) :].strip(" ,.!?")
        return text

    def _should_handle(self, heard: str) -> bool:
        if self._settings.always_listen:
            return True
        return self._settings.wake_word in heard.lower()

    @staticmethod
    def _sanitize_ai_response(text: str) -> str:
        t = (text or "").strip()
        if not t:
            return "I could not generate a response for that request."
        if t == "[ai_unavailable]":
            return "[ai_unavailable]"
        lowered = t.lower()
        if "[" in t and "]" in t:
            return "I could not complete that reliably. Please try again."
        if "traceback" in lowered or "exception" in lowered or "error:" in lowered:
            return "I ran into a temporary issue. Please try again."
        if "generic" in lowered and "content" in lowered:
            return "I could not complete that request. Please try a specific command."
        return t

    def _should_call_ai(self, query: str) -> bool:
        q = (query or "").strip().lower()
        if not q:
            return False
        if len(q) <= 2:
            return False
        words = [w for w in q.split() if w]
        if len(words) == 1 and words[0] in self._no_ai_tokens:
            return False
        return True

    def _is_duplicate_query(self, query: str) -> bool:
        normalized = " ".join((query or "").strip().lower().split())
        if not normalized:
            return False
        now = time.monotonic()
        if (now - self._last_executed_at) > self._dedup_window_seconds:
            return False
        if normalized == self._last_executed_query:
            return True
        return SequenceMatcher(None, normalized, self._last_executed_query).ratio() >= 0.88

    def _mark_query_executed(self, query: str) -> None:
        self._last_executed_query = " ".join((query or "").strip().lower().split())
        self._last_executed_at = time.monotonic()

    def _speak_and_cooldown(self, text: str) -> None:
        self._set_state("speaking")
        self._speaker.speak(text)
        time.sleep(self._post_speak_cooldown_seconds)

    def run(self) -> None:
        self._set_state("starting")
        self._listener.calibrate()
        self._speak_and_cooldown(f"{self._settings.assistant_name} online.")
        self._set_state("idle")

        while True:
            self._set_state("listening")
            heard = self._listener.listen_once()
            if not heard:
                continue

            if heard.startswith("[stt_error]"):
                self._stt_error_streak += 1
                if self._stt_error_streak in {1, 4, 8}:
                    self._speak_and_cooldown("Speech recognition is unstable. Check your mic and internet.")
                continue
            self._stt_error_streak = 0

            lower_heard = heard.lower().strip()
            if lower_heard in self._stop_words:
                self._speak_and_cooldown("Shutting down. Goodbye.")
                break

            if not self._should_handle(heard):
                continue

            query = self._strip_wake_word(heard)
            if not query:
                self._speak_and_cooldown("Yes?")
                self._set_state("listening")
                follow_up = self._listener.listen_once(timeout=4, phrase_time_limit=8)
                if not follow_up or follow_up.startswith("[stt_error]"):
                    self._speak_and_cooldown("I did not catch that.")
                    continue
                query = follow_up

            if self._is_duplicate_query(query):
                continue

            cmd_result = self._router.route(query)
            if cmd_result.handled:
                self._mark_query_executed(query)
                self._speak_and_cooldown(cmd_result.response)
                continue

            if not self._should_call_ai(query):
                self._speak_and_cooldown("Please say a clearer command, for example: play shape of you on YouTube.")
                continue

            self._set_state("processing")
            response = self._sanitize_ai_response(self._gemini.ask(query))
            if response == "[ai_unavailable]":
                if not self._ai_unavailable_announced:
                    self._speak_and_cooldown("AI is temporarily unavailable. I can still run local commands.")
                    self._ai_unavailable_announced = True
                continue
            self._ai_unavailable_announced = False
            self._mark_query_executed(query)
            self._speak_and_cooldown(response)
