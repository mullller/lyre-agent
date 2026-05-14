from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import os

from lyre_agent.paths import get_paths


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


def get_config_path(path: str | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    env_path = os.environ.get("LYRE_AGENT_CONFIG")
    if env_path:
        return Path(env_path).expanduser()
    return get_paths().config_file


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
