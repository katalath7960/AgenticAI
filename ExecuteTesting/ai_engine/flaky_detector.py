"""Tracks pass/fail history per step and flags flaky tests."""
import json
from pathlib import Path

from utilities.logger import get_logger

log = get_logger(test="FlakyDetector")

_HISTORY_FILE = Path("logs/flaky_history.json")
_WINDOW = 10  # last N runs to consider


class FlakyDetector:
    def __init__(self):
        self._history: dict[str, list[str]] = {}
        self._load()

    def _load(self):
        if _HISTORY_FILE.exists():
            try:
                self._history = json.loads(_HISTORY_FILE.read_text())
            except Exception:
                self._history = {}

    def _save(self):
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _HISTORY_FILE.write_text(json.dumps(self._history, indent=2))

    def record(self, tc_id: str, status: str) -> None:
        history = self._history.setdefault(tc_id, [])
        history.append(status)
        if len(history) > _WINDOW:
            self._history[tc_id] = history[-_WINDOW:]
        self._save()

    def is_flaky(self, tc_id: str) -> bool:
        history = self._history.get(tc_id, [])
        if len(history) < 3:
            return False
        statuses = set(history[-_WINDOW:])
        return "PASS" in statuses and "FAIL" in statuses
