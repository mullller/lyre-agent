from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import os


@dataclass(slots=True)
class ModelConfig:
    provider: str = "echo"
    name: str = "echo"
    base_url: str | None = None
    api_key_env: str | None = None


@dataclass(slots=True)
class WorkspaceConfig:
    root: str = "."
    allow_write: bool = True
    allow_shell: bool = True
    allow_outside_root: bool = False


@dataclass(slots=True)
class ShellConfig:
    enabled: bool = True
    timeout: int = 180


@dataclass(slots=True)
class ToolsConfig:
    shell: ShellConfig = field(default_factory=ShellConfig)


@dataclass(slots=True)
class AgentConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    max_iterations: int = 8

    def to_dict(self) -> dict:
        return asdict(self)


# ── Remote host management ──────────────────────────────────────────────────


@dataclass(slots=True)
class RemoteHost:
    """A remote Lyre Agent host accessible via SSH."""

    name: str
    host: str
    user: str = "root"
    port: int = 22
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RemoteHost":
        return cls(
            name=data["name"],
            host=data["host"],
            user=data.get("user", "root"),
            port=data.get("port", 22),
            description=data.get("description", ""),
        )


@dataclass(slots=True)
class RemoteConfig:
    """Collection of remote Lyre Agent hosts."""

    remotes: dict[str, RemoteHost] = field(default_factory=dict)

    def add(self, host: RemoteHost) -> None:
        self.remotes[host.name] = host

    def remove(self, name: str) -> None:
        del self.remotes[name]

    def get(self, name: str) -> RemoteHost | None:
        return self.remotes.get(name)

    def list(self) -> list[RemoteHost]:
        return list(self.remotes.values())

    def to_dict(self) -> dict:
        return {"remotes": {k: v.to_dict() for k, v in self.remotes.items()}}

    @classmethod
    def from_dict(cls, data: dict) -> "RemoteConfig":
        if not isinstance(data, dict):
            raise ValueError("remote config root must be an object")
        cfg = cls()
        for name, host_data in data.get("remotes", {}).items():
            host_data["name"] = name
            cfg.remotes[name] = RemoteHost.from_dict(host_data)
        return cfg


# ── Config paths ────────────────────────────────────────────────────────────


def get_config_path(path: str | None = None) -> Path:
    return Path(path or os.environ.get("LYRE_AGENT_CONFIG", "~/.lyre-agent/config.json")).expanduser()


def get_remote_config_path() -> Path:
    return Path(os.environ.get("LYRE_REMOTE_CONFIG", "~/.lyre-agent/remotes.json")).expanduser()


# ── Config loading ──────────────────────────────────────────────────────────


def _merge_dataclass(obj, data: dict):
    for key, value in data.items():
        if not hasattr(obj, key):
            continue
        current = getattr(obj, key)
        if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
            _merge_dataclass(current, value)
        else:
            setattr(obj, key, value)
    return obj


def load_config(path: str | None = None) -> AgentConfig:
    """Load config from JSON file. YAML can be added later without adding dependencies."""
    cfg = AgentConfig()
    config_path = get_config_path(path)
    if not config_path.exists():
        return cfg
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be an object")
    return _merge_dataclass(cfg, data)


def save_config(config: AgentConfig, path: str | None = None) -> Path:
    config_path = get_config_path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return config_path


def load_remote_config() -> RemoteConfig:
    """Load remote hosts from ~/.lyre-agent/remotes.json."""
    config_path = get_remote_config_path()
    if not config_path.exists():
        return RemoteConfig()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return RemoteConfig.from_dict(data)


def save_remote_config(config: RemoteConfig) -> Path:
    """Save remote hosts to ~/.lyre-agent/remotes.json."""
    config_path = get_remote_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return config_path
