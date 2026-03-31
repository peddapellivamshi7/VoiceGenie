from __future__ import annotations

import datetime as dt
import logging
import re
import subprocess
import urllib.request
import webbrowser
from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class CommandResult:
    handled: bool
    response: str


class CommandRouter:
    def __init__(self, confirmation_required: bool = True) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._confirmation_required = confirmation_required

    @staticmethod
    def _normalize(text: str) -> str:
        q = text.lower().strip()
        q = q.replace("\u2019", "'")
        q = re.sub(r"[^a-z0-9\s.:/-]", " ", q)
        q = re.sub(r"\s+", " ", q)
        return q

    @staticmethod
    def _is_ambiguous_media_query(term: str) -> bool:
        term = term.strip().lower()
        return term in {
            "a video",
            "video",
            "some video",
            "music",
            "a song",
            "song",
            "something",
        }

    def _open_youtube_search(self, term: str) -> CommandResult:
        clean = term.strip(" .,!?")
        if not clean:
            webbrowser.open("https://www.youtube.com", new=2)
            return CommandResult(True, "Opened YouTube.")

        if self._is_ambiguous_media_query(clean):
            webbrowser.open("https://www.youtube.com", new=2)
            return CommandResult(True, "Opened YouTube. Tell me the exact video title to play.")

        autoplay_url, search_url = self._resolve_youtube_autoplay_url(clean)
        if autoplay_url:
            webbrowser.open(autoplay_url, new=2)
            return CommandResult(True, f"Playing {clean} on YouTube.")

        webbrowser.open(search_url, new=2)
        return CommandResult(True, f"I could not auto-play that. Opening YouTube results for {clean}.")

    def _resolve_youtube_autoplay_url(self, term: str) -> tuple[str | None, str]:
        search_url = f"https://www.youtube.com/results?search_query={quote_plus(term)}"
        request = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=6) as response:
                html = response.read().decode("utf-8", errors="ignore")
        except Exception:
            self._logger.warning("Could not fetch YouTube search page for autoplay")
            return None, search_url

        match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        if not match:
            return None, search_url

        video_id = match.group(1)
        autoplay_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1"
        return autoplay_url, search_url

    @staticmethod
    def _looks_like_domain(value: str) -> bool:
        return bool(re.match(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$", value))

    def route(self, text: str) -> CommandResult:
        q = self._normalize(text)

        if re.search(r"\b(time|clock)\b", q) and re.search(r"\b(what|tell|current|now|is it)\b", q):
            now = dt.datetime.now().astimezone()
            local_time = now.strftime("%I:%M %p").lstrip("0")
            tz_name = now.tzname() or "local time"
            return CommandResult(True, f"It is {local_time} {tz_name}.")

        if re.search(r"\bdate\b", q) and re.search(r"\b(today|what|current|tell)\b", q):
            today = dt.datetime.now().astimezone().strftime("%A, %B %d, %Y")
            return CommandResult(True, f"Today is {today}.")

        if any(k in q for k in {"open notepad", "open note pad", "notepad"}):
            subprocess.Popen(["notepad.exe"], shell=False)
            return CommandResult(True, "Opened Notepad.")

        if any(k in q for k in {"open calculator", "open calc", "open cal", "calculator"}):
            subprocess.Popen(["calc.exe"], shell=False)
            return CommandResult(True, "Opened Calculator.")

        if any(k in q for k in {"open browser", "open chrome", "open google", "open internet"}):
            webbrowser.open("https://www.google.com", new=2)
            return CommandResult(True, "Opened your browser.")

        if "open youtube" in q or q == "youtube":
            webbrowser.open("https://www.youtube.com", new=2)
            return CommandResult(True, "Opened YouTube.")

        yt_and_play_match = re.search(r"youtube(?:\s+and)?\s+play\s+(.+)$", q)
        if yt_and_play_match:
            return self._open_youtube_search(yt_and_play_match.group(1))

        yt_play_match = re.search(r"(?:play|search)(?:\s+for)?\s+(.+?)\s+(?:on\s+)?youtube(?:\s+(.+))?$", q)
        if yt_play_match:
            before = yt_play_match.group(1).strip()
            after = (yt_play_match.group(2) or "").strip()
            term = f"{before} {after}".strip()
            return self._open_youtube_search(term)

        yt_topic_match = re.search(r"(.+?)\s+on\s+youtube(?:\s+(.+))?$", q)
        if yt_topic_match:
            before = yt_topic_match.group(1).strip()
            after = (yt_topic_match.group(2) or "").strip()
            term = f"{before} {after}".strip()
            return self._open_youtube_search(term)

        yt_loose_match = re.search(r"(.+?)\s+youtube$", q)
        if yt_loose_match:
            return self._open_youtube_search(yt_loose_match.group(1))

        if q.startswith("play "):
            return self._open_youtube_search(q.replace("play ", "", 1))

        if q.startswith("open website "):
            website = q.replace("open website ", "", 1).strip()
            if website and not website.startswith("http"):
                website = f"https://{website}"
            webbrowser.open(website, new=2)
            return CommandResult(True, f"Opened {website}.")

        open_target = re.match(r"^open\s+([a-z0-9.-]+)$", q)
        if open_target:
            target = open_target.group(1)
            if self._looks_like_domain(target):
                website = f"https://{target}"
                webbrowser.open(website, new=2)
                return CommandResult(True, f"Opened {website}.")

        search_query = re.match(r"^(?:search|google)\s+(.+)$", q)
        if search_query:
            term = search_query.group(1).strip()
            url = f"https://www.google.com/search?q={quote_plus(term)}"
            webbrowser.open(url, new=2)
            return CommandResult(True, f"Searching Google for {term}.")

        return CommandResult(False, "")
