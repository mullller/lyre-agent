from pathlib import Path

from lyre_agent.config import get_config_path, save_config, AgentConfig
from lyre_agent.paths import LyrePaths, get_paths, reset_paths


def test_default_home_uses_lyre_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("LYRE_HOME", raising=False)

    paths = reset_paths()

    assert paths.home == tmp_path / ".lyre-agent"


def test_lyre_home_env_overrides_default(tmp_path, monkeypatch):
    custom_home = tmp_path / "custom-lyre"
    monkeypatch.setenv("LYRE_HOME", str(custom_home))

    paths = reset_paths()

    assert paths.home == custom_home.resolve()


def test_direct_home_argument_overrides_env(tmp_path, monkeypatch):
    monkeypatch.setenv("LYRE_HOME", str(tmp_path / "env-home"))

    paths = reset_paths(tmp_path / "explicit-home")

    assert paths.home == (tmp_path / "explicit-home").resolve()


def test_subdirectories_are_created(tmp_path):
    paths = LyrePaths(tmp_path / "lyre").ensure_all()

    assert paths.home.is_dir()
    assert paths.config.is_dir()
    assert paths.sessions.is_dir()
    assert paths.memory.is_dir()
    assert paths.skills.is_dir()
    assert paths.logs.is_dir()


def test_config_and_models_file_paths(tmp_path):
    paths = LyrePaths(tmp_path / "lyre")

    assert paths.config_file == tmp_path / "lyre" / "config" / "config.json"
    assert paths.models_file == tmp_path / "lyre" / "config" / "models.json"


def test_get_paths_returns_cached_instance(tmp_path, monkeypatch):
    monkeypatch.setenv("LYRE_HOME", str(tmp_path / "lyre"))
    first = reset_paths()

    assert get_paths() is first


def test_get_config_path_uses_lyre_home(tmp_path, monkeypatch):
    monkeypatch.setenv("LYRE_HOME", str(tmp_path / "lyre"))
    monkeypatch.delenv("LYRE_AGENT_CONFIG", raising=False)
    reset_paths()

    assert get_config_path() == tmp_path / "lyre" / "config" / "config.json"


def test_get_config_path_keeps_explicit_path_priority(tmp_path, monkeypatch):
    monkeypatch.setenv("LYRE_HOME", str(tmp_path / "lyre"))

    assert get_config_path(str(tmp_path / "explicit.json")) == tmp_path / "explicit.json"


def test_get_config_path_keeps_legacy_env_priority(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy.json"
    monkeypatch.setenv("LYRE_HOME", str(tmp_path / "lyre"))
    monkeypatch.setenv("LYRE_AGENT_CONFIG", str(legacy))

    assert get_config_path() == legacy


def test_save_config_creates_config_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("LYRE_HOME", str(tmp_path / "lyre"))
    monkeypatch.delenv("LYRE_AGENT_CONFIG", raising=False)
    reset_paths()

    saved_path = save_config(AgentConfig())

    assert saved_path == tmp_path / "lyre" / "config" / "config.json"
    assert saved_path.exists()
