import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def _resolve_env(value: Any) -> Any:
    if isinstance(value, str):
        return re.sub(r"\$\{(\w+)\}", lambda m: os.getenv(m.group(1), ""), value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


class _Namespace:
    def __init__(self, d: dict):
        for k, v in d.items():
            setattr(self, k, _Namespace(v) if isinstance(v, dict) else v)

    def get(self, key: str, default=None):
        return getattr(self, key, default)


def load_config(path: str | None = None) -> _Namespace:
    cfg_path = path or Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(cfg_path, "r") as f:
        raw = yaml.safe_load(f)
    resolved = _resolve_env(raw)
    return _Namespace(resolved)


config = load_config()
