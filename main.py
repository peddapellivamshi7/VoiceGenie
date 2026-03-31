from __future__ import annotations

import logging

from src.assistant import VoiceAssistant
from src.config import load_settings


def main() -> None:
    settings = load_settings()
    assistant = VoiceAssistant(settings=settings)

    try:
        assistant.run()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Interrupted by user")


if __name__ == "__main__":
    main()
