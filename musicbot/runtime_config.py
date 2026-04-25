from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class RuntimeConfig:
    jokejoin_enabled: bool = False
    jokejoin_track_url: str | None = None
    jokejoin_user_id: int | None = None


class RuntimeConfigStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def load(self) -> RuntimeConfig:
        if not self.path.exists():
            return RuntimeConfig()

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return RuntimeConfig(
            jokejoin_enabled=bool(payload.get("jokejoin_enabled", False)),
            jokejoin_track_url=payload.get("jokejoin_track_url") or None,
            jokejoin_user_id=payload.get("jokejoin_user_id"),
        )

    def save(self, config: RuntimeConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
