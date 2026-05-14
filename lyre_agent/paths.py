from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os


_DEFAULT_LYRE_HOME = "~/.lyre-agent"


def _resolve_home(home: str | Path | None = None) -> Path:
    raw_home = home or os.environ.get("LYRE_HOME") or _DEFAULT_LYRE_HOME
    return Path(raw_home).expanduser().resolve()


@dataclass(slots=True)
class LyrePaths:
    """Filesystem locations used by lyre-agent."""

    home: Path = field(default_factory=_resolve_home)

    def __post_init__(self) -> None:
        self.home = Path(self.home).expanduser().resolve()

    @property
    def config(self) -> Path:
        return self._ensure_dir("config")

    @property
    def sessions(self) -> Path:
        return self._ensure_dir("sessions")

    @property
    def memory(self) -> Path:
        return self._ensure_dir("memory")

    @property
    def skills(self) -> Path:
        return self._ensure_dir("skills")

    @property
    def logs(self) -> Path:
        return self._ensure_dir("logs")

    @property
    def config_file(self) -> Path:
        return self.config / "config.json"

    @property
    def models_file(self) -> Path:
        return self.config / "models.json"

    def ensure_all(self) -> "LyrePaths":
        self.home.mkdir(parents=True, exist_ok=True)
        for path in (self.config, self.sessions, self.memory, self.skills, self.logs):
            path.mkdir(parents=True, exist_ok=True)
        return self

    def _ensure_dir(self, name: str) -> Path:
        path = self.home / name
        path.mkdir(parents=True, exist_ok=True)
        return path


_paths: LyrePaths | None = None


def get_paths() -> LyrePaths:
    """Return the process-wide path manager."""
    global _paths
    if _paths is None:
        _paths = LyrePaths().ensure_all()
    return _paths


def reset_paths(home: str | Path | None = None) -> LyrePaths:
    """Reset the cached path manager, primarily for tests."""
    global _paths
    _paths = LyrePaths(_resolve_home(home)).ensure_all()
    return _paths
