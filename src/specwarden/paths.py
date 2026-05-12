from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoPaths:
    """Resolve the .claude/ layout under a repo root."""

    root: Path

    @property
    def claude_dir(self) -> Path:
        return self.root / ".claude"

    @property
    def specs_dir(self) -> Path:
        return self.claude_dir / "specs"

    @property
    def decisions_dir(self) -> Path:
        return self.claude_dir / "decisions"

    @property
    def active_marker(self) -> Path:
        return self.specs_dir / "active"

    def ensure_dirs(self) -> None:
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        self.decisions_dir.mkdir(parents=True, exist_ok=True)

    def active_spec_id(self) -> str | None:
        if not self.active_marker.exists():
            return None
        text = self.active_marker.read_text(encoding="utf-8").strip()
        return text or None
