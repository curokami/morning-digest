from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    raw: dict[str, Any]
    root: Path

    def section(self, name: str) -> dict[str, Any]:
        value = self.raw.get(name, {})
        if not isinstance(value, dict):
            raise ValueError(f"Configuration section {name!r} must be a mapping")
        return value

    def path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).resolve()
    with config_path.open(encoding="utf-8") as stream:
        raw = yaml.safe_load(stream) or {}
    if not isinstance(raw, dict):
        raise ValueError("Configuration root must be a mapping")
    for required in ("sources", "ai", "taxonomy", "persistence", "delivery"):
        if required not in raw:
            raise ValueError(f"Missing required configuration section: {required}")
    return AppConfig(raw=raw, root=config_path.parent)
