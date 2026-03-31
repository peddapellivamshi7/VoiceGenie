from __future__ import annotations

import logging
import time
from typing import Optional

try:
    import google.genai as genai  # new GenAI SDK
    _USING_NEW_GENAI = True
except Exception:
    import google.generativeai as genai  # legacy package
    _USING_NEW_GENAI = False

from src.config import Settings


SYSTEM_PROMPT = """
You are a high-end, concise Windows voice assistant.
Rules:
- Be precise and action-oriented.
- Keep responses short by default unless asked for detail.
- If a task needs OS-level action, describe what was done.
- Never output placeholders like [current time] or [insert value].
- Avoid hallucinating system state.
""".strip()


class GeminiClient:
    def __init__(self, settings: Settings) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._settings = settings
        # Prefer the new `google.genai` client when available, otherwise
        # fall back to the legacy `google.generativeai` API.
        if _USING_NEW_GENAI:
            # create a client and chat wrapper
            self._client = genai.client.Client(api_key=settings.gemini_api_key)
            self._chat = genai.chats.Chat(modules=self._client.models, model=settings.gemini_model, history=[])
        else:
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                system_instruction=SYSTEM_PROMPT,
            )
            self._chat = self._model.start_chat(history=[])
        self._cooldown_until = 0.0

    def ask(self, user_text: str) -> str:
        if time.monotonic() < self._cooldown_until:
            return "[ai_unavailable]"

        try:
            response = self._chat.send_message(user_text)
            # Support both legacy and new SDK response shapes
            text: Optional[str] = None
            # legacy `google.generativeai` sometimes exposes `text` directly
            text = getattr(response, "text", None)
            if not text:
                # new `google.genai` returns a GenerateContentResponse
                # with `candidates` where content may hold the produced text.
                try:
                    if getattr(response, "candidates", None):
                        cand = response.candidates[0]
                        content = getattr(cand, "content", None)
                        if content is None:
                            # content might be a dict-like
                            try:
                                content = cand.get("content")
                            except Exception:
                                content = None
                        if content is not None:
                            text = getattr(content, "text", None) or (content.get("text") if isinstance(content, dict) else None)
                except Exception:
                    text = None

            if text and text.strip():
                return text.strip()
            return "I could not generate a response for that request."
        except Exception as exc:
            self._logger.exception("Gemini request failed")
            msg = str(exc).lower()
            if "429" in msg or "quota" in msg or "resourceexhausted" in msg:
                self._cooldown_until = time.monotonic() + 90
                return "[ai_unavailable]"
            return "[ai_unavailable]"
