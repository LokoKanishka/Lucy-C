from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class HistoryItem:
    ts: float
    session_user: str
    kind: str  # "text" | "voice"
    llm_provider: str
    ollama_model: str
    user_text: str
    transcript: str
    reply: str


class HistoryStore:
    """Very small JSONL history store.

    Design goals:
    - survives restarts
    - append-only
    - one file per session_user
    """

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, session_user: str) -> Path:
        safe = "".join(c for c in session_user if c.isalnum() or c in ("-", "_", ":"))
        return self.root_dir / f"{safe}.jsonl"

    def append(self, item: HistoryItem) -> None:
        p = self._path_for(item.session_user)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")

    def read(self, session_user: str, limit: int = 200) -> list[Dict[str, Any]]:
        p = self._path_for(session_user)
        if not p.exists():
            return []
        lines = p.read_text(encoding="utf-8").splitlines()
        lines = lines[-max(1, int(limit)) :]
        out: list[Dict[str, Any]] = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out


def default_history_dir() -> Path:
    # /.../Lucy-C/data/history
    here = Path(__file__).resolve()
    root = here.parents[1]
    return root / "data" / "history"
