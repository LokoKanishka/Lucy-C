from __future__ import annotations

import re


_URL_RE = re.compile(r"https?://\S+")


def normalize_for_tts(text: str) -> str:
    """Make assistant text sound natural when read aloud.

    Goal: remove markdown / UI artifacts that TTS would spell out.
    We keep meaning, but strip symbols like **, *, backticks, etc.
    """
    t = (text or "").strip()
    if not t:
        return t

    # Remove code fences and inline code markers
    t = t.replace("```", " ")
    t = t.replace("`", "")

    # Remove common markdown emphasis markers
    t = t.replace("**", "")
    t = t.replace("*", "")
    t = t.replace("__", "")
    t = t.replace("_", "")

    # Turn bullets into pauses
    t = t.replace("•", "-")

    # Remove markdown links: [text](url) -> text
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", t)

    # Remove bare URLs (TTS tends to spell them)
    t = _URL_RE.sub("", t)

    # Parentheses: keep content but remove the literal parentheses
    t = t.replace("(", ", ").replace(")", ", ")

    # Collapse repeated punctuation that sounds bad
    t = re.sub(r"[\s\u00A0]+", " ", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s+,", ", ", t)
    t = re.sub(r"\.{3,}", "…", t)

    return t.strip(" ,")
