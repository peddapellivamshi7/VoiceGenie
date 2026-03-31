from __future__ import annotations

import logging
from typing import Optional

import speech_recognition as sr


class Listener:
    def __init__(
        self,
        stt_engine: str,
        language: str,
        whisper_model: str = "base",
        timeout: int = 4,
        phrase_time_limit: int = 8,
        ambient_calibration_seconds: float = 0.6,
        operation_timeout: float = 6.0,
        dynamic_energy: bool = True,
        energy_threshold: int = 300,
        pause_threshold: float = 0.7,
        non_speaking_duration: float = 0.35,
        microphone_index: Optional[int] = None,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._recognizer = sr.Recognizer()
        self._stt_engine = stt_engine
        self._language = language
        self._whisper_model = whisper_model
        self._timeout = timeout
        self._phrase_time_limit = phrase_time_limit
        self._ambient_calibration_seconds = ambient_calibration_seconds

        selected_index = self._select_microphone_index(microphone_index)
        self._microphone = sr.Microphone(device_index=selected_index)
        self._logger.info("Using microphone index: %s", selected_index)

        self._recognizer.operation_timeout = operation_timeout
        self._recognizer.dynamic_energy_threshold = dynamic_energy
        self._recognizer.energy_threshold = energy_threshold
        self._recognizer.pause_threshold = pause_threshold
        self._recognizer.non_speaking_duration = non_speaking_duration

    def _select_microphone_index(self, configured_index: Optional[int]) -> Optional[int]:
        if configured_index is not None:
            return configured_index

        try:
            names = sr.Microphone.list_microphone_names()
        except Exception:
            return None

        preferred = (
            "microphone",
            "mic",
            "headset",
            "headphone",
            "input",
        )
        avoid = ("output", "speaker", "stereo mix")

        for i, name in enumerate(names):
            lowered = name.lower()
            if any(a in lowered for a in avoid):
                continue
            if any(p in lowered for p in preferred):
                return i

        return None

    def _whisper_language(self) -> str:
        return self._language.split("-", 1)[0].strip().lower() or "en"

    def calibrate(self) -> None:
        with self._microphone as source:
            self._logger.info("Calibrating ambient noise...")
            self._recognizer.adjust_for_ambient_noise(source, duration=self._ambient_calibration_seconds)

    def _recognize_with_whisper(self, audio: sr.AudioData) -> str:
        return self._recognizer.recognize_whisper(
            audio,
            model=self._whisper_model,
            language=self._whisper_language(),
        )

    def _recognize_with_google(self, audio: sr.AudioData) -> str:
        return self._recognizer.recognize_google(audio, language=self._language)

    def listen_once(self, timeout: Optional[int] = None, phrase_time_limit: Optional[int] = None) -> Optional[str]:
        timeout = self._timeout if timeout is None else timeout
        phrase_time_limit = self._phrase_time_limit if phrase_time_limit is None else phrase_time_limit
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
        except sr.WaitTimeoutError:
            return None

        try:
            if self._stt_engine == "whisper_local":
                try:
                    text = self._recognize_with_whisper(audio)
                except Exception as exc:
                    self._logger.warning("Whisper STT failed, falling back to Google STT: %s", exc)
                    text = self._recognize_with_google(audio)
            else:
                text = self._recognize_with_google(audio)
            text = text.strip()
            self._logger.info("STT: %s", text)
            return text if text else None
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            self._logger.warning("Speech recognition service unavailable")
            return "[stt_error] service_unavailable"
        except Exception as exc:
            self._logger.exception("Speech recognition failed")
            return f"[stt_error] {exc}"
