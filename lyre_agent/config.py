from __future__ import annotations

from dataclasses import dataclass, field
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
        return {
            "model": self.model.__dict__,
            "workspace": self.workspace.__dict__,
            "tools": {"shell": self.tools.shell.__dict__},
            "max_iterations": self.max_iterations,
        }


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
    config_path = Path(path or os.environ.get("LYRE_AGENT_CONFIG", "~/.lyre-agent/config.json")).expanduser()
    if not config_path.exists():
        return cfg
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be an object")
    return _merge_dataclass(cfg, data)
