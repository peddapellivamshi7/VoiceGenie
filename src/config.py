from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    assistant_name: str
    wake_word: str
    always_listen: bool
    stt_engine: str
    whisper_model: str
    voice_rate: int
    voice_volume: float
    voice_gender: str
    language: str
    command_confirmation: bool
    stt_timeout: int
    stt_phrase_time_limit: int
    ambient_calibration_seconds: float
    stt_operation_timeout: float
    dynamic_energy: bool
    energy_threshold: int
    pause_threshold: float
    non_speaking_duration: float
    microphone_index: Optional[int]


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return int(value)


def load_settings() -> Settings:
    load_dotenv()

    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is missing. Add it in your .env file.")

    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    assistant_name = os.getenv("ASSISTANT_NAME", "Jarvis").strip() or "Jarvis"
    wake_word = os.getenv("WAKE_WORD", "jarvis").strip().lower() or "jarvis"
    always_listen = _to_bool(os.getenv("ALWAYS_LISTEN", "false"), False)
    stt_engine = os.getenv("STT_ENGINE", "whisper_local").strip().lower() or "whisper_local"
    whisper_model = os.getenv("WHISPER_MODEL", "base").strip() or "base"
    voice_rate = int(os.getenv("VOICE_RATE", "185").strip())
    voice_volume = float(os.getenv("VOICE_VOLUME", "1.0").strip())
    voice_gender = os.getenv("VOICE_GENDER", "female").strip().lower() or "female"
    language = os.getenv("LANGUAGE", "en-US").strip() or "en-US"
    command_confirmation = _to_bool(os.getenv("COMMAND_CONFIRMATION", "true"), True)
    stt_timeout = int(os.getenv("STT_TIMEOUT", "4").strip())
    stt_phrase_time_limit = int(os.getenv("STT_PHRASE_TIME_LIMIT", "8").strip())
    ambient_calibration_seconds = float(os.getenv("AMBIENT_CALIBRATION_SECONDS", "0.6").strip())
    stt_operation_timeout = float(os.getenv("STT_OPERATION_TIMEOUT", "6").strip())
    dynamic_energy = _to_bool(os.getenv("DYNAMIC_ENERGY", "true"), True)
    energy_threshold = int(os.getenv("ENERGY_THRESHOLD", "300").strip())
    pause_threshold = float(os.getenv("PAUSE_THRESHOLD", "0.7").strip())
    non_speaking_duration = float(os.getenv("NON_SPEAKING_DURATION", "0.35").strip())
    microphone_index = _to_optional_int(os.getenv("MICROPHONE_INDEX"))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    return Settings(
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        assistant_name=assistant_name,
        wake_word=wake_word,
        always_listen=always_listen,
        stt_engine=stt_engine,
        whisper_model=whisper_model,
        voice_rate=voice_rate,
        voice_volume=voice_volume,
        voice_gender=voice_gender,
        language=language,
        command_confirmation=command_confirmation,
        stt_timeout=stt_timeout,
        stt_phrase_time_limit=stt_phrase_time_limit,
        ambient_calibration_seconds=ambient_calibration_seconds,
        stt_operation_timeout=stt_operation_timeout,
        dynamic_energy=dynamic_energy,
        energy_threshold=energy_threshold,
        pause_threshold=pause_threshold,
        non_speaking_duration=non_speaking_duration,
        microphone_index=microphone_index,
    )
