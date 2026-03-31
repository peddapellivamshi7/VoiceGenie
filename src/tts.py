from __future__ import annotations

import logging
import threading

import pyttsx3


class Speaker:
    def __init__(self, rate: int, volume: float, gender: str = "female") -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", rate)
        self._engine.setProperty("volume", volume)
        self._select_voice(gender)
        self._lock = threading.Lock()

    def _select_voice(self, gender: str) -> None:
        requested = (gender or "female").strip().lower()
        if requested not in {"female", "male"}:
            requested = "female"

        try:
            voices = self._engine.getProperty("voices") or []
        except Exception:
            self._logger.exception("Failed to fetch TTS voices")
            return

        keywords = ["zira", "female", "woman", "hazel"] if requested == "female" else ["david", "male", "man", "mark"]
        fallback_keywords = ["female", "woman"] if requested == "female" else ["male", "man"]

        selected = None
        for voice in voices:
            info = f"{getattr(voice, 'id', '')} {getattr(voice, 'name', '')}".lower()
            if any(k in info for k in keywords):
                selected = voice
                break

        if selected is None:
            for voice in voices:
                info = f"{getattr(voice, 'id', '')} {getattr(voice, 'name', '')}".lower()
                if any(k in info for k in fallback_keywords):
                    selected = voice
                    break

        if selected is None and voices:
            selected = voices[0]

        if selected is not None:
            self._engine.setProperty("voice", selected.id)
            self._logger.info("TTS voice selected: %s", getattr(selected, "name", selected.id))

    def speak(self, text: str) -> None:
        if not text or not text.strip():
            return
        with self._lock:
            self._logger.info("TTS: %s", text)
            self._engine.say(text)
            self._engine.runAndWait()
