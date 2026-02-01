from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

log = logging.getLogger("LucyC.Facts")

class FactsStore:
    """Persistent store for Lucy's long-term memory (facts, decisions).
    
    Stored in a single JSON file per user to keep it simple and portable.
    """

    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, session_user: str) -> Path:
        safe = "".join(c for c in session_user if c.isalnum() or c in ("-", "_", ":"))
        return self.root_dir / f"{safe}_facts.json"

    def get_facts(self, session_user: str) -> Dict[str, Any]:
        p = self._path_for(session_user)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            log.error("Failed to read facts for %s: %s", session_user, e)
            return {}

    def set_fact(self, session_user: str, key: str, value: Any) -> None:
        facts = self.get_facts(session_user)
        facts[key] = value
        self._save_facts(session_user, facts)

    def remove_fact(self, session_user: str, key: str) -> None:
        facts = self.get_facts(session_user)
        if key in facts:
            del facts[key]
            self._save_facts(session_user, facts)

    def _save_facts(self, session_user: str, facts: Dict[str, Any]) -> None:
        p = self._path_for(session_user)
        try:
            p.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            log.error("Failed to save facts for %s: %s", session_user, e)

    def get_facts_summary(self, session_user: str) -> str:
        """Returns a string representation of facts to be injected into the system prompt."""
        facts = self.get_facts(session_user)
        if not facts:
            return ""
        
        lines = ["**Hechos y Decisiones Recordadas**:"]
        for k, v in facts.items():
            lines.append(f"- {k}: {v}")
        return "\n".join(lines)


def default_facts_dir() -> Path:
    # /.../Lucy-C/data/facts
    here = Path(__file__).resolve()
    root = here.parents[1]
    return root / "data" / "facts"
