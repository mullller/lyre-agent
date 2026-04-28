import json

from lyre_agent.config import load_config
from lyre_agent.models import apply_model_switch, list_model_presets


def test_list_model_presets_includes_echo_and_openai():
    aliases = {preset.alias for preset in list_model_presets()}
    assert "echo" in aliases
    assert "openai:gpt-4.1" in aliases
    assert "anthropic:sonnet" in aliases
    assert "local" in aliases


def test_apply_model_switch_preset(tmp_path):
    config_path = tmp_path / "config.json"
    cfg = load_config(str(config_path))

    apply_model_switch(cfg, "openai:gpt-4.1-mini", config_path=str(config_path))

    data = json.loads(config_path.read_text())
    assert data["model"]["provider"] == "openai-compatible"
    assert data["model"]["name"] == "gpt-4.1-mini"
    assert data["model"]["api_key_env"] == "OPENAI_API_KEY"


def test_apply_model_switch_custom(tmp_path):
    config_path = tmp_path / "config.json"
    cfg = load_config(str(config_path))

    apply_model_switch(
        cfg,
        "my-model",
        provider="openai-compatible",
        base_url="http://localhost:1234/v1",
        api_key_env="LOCAL_KEY",
        config_path=str(config_path),
    )

    loaded = load_config(str(config_path))
    assert loaded.model.provider == "openai-compatible"
    assert loaded.model.name == "my-model"
    assert loaded.model.base_url == "http://localhost:1234/v1"
    assert loaded.model.api_key_env == "LOCAL_KEY"


def test_apply_model_switch_anthropic_preset(tmp_path):
    config_path = tmp_path / "config.json"
    cfg = load_config(str(config_path))

    apply_model_switch(cfg, "anthropic:sonnet", config_path=str(config_path))

    loaded = load_config(str(config_path))
    assert loaded.model.provider == "anthropic"
    assert loaded.model.name == "claude-sonnet-4-5"
    assert loaded.model.base_url == "https://api.anthropic.com"
    assert loaded.model.api_key_env == "ANTHROPIC_API_KEY"


def test_apply_model_switch_custom_anthropic_gateway(tmp_path):
    config_path = tmp_path / "config.json"
    cfg = load_config(str(config_path))

    apply_model_switch(
        cfg,
        "claude-3-5-sonnet-20241022",
        provider="anthropic",
        base_url="https://anthropic-gateway.example.com",
        api_key_env="ANTHROPIC_GATEWAY_API_KEY",
        config_path=str(config_path),
    )

    loaded = load_config(str(config_path))
    assert loaded.model.provider == "anthropic"
    assert loaded.model.name == "claude-3-5-sonnet-20241022"
    assert loaded.model.base_url == "https://anthropic-gateway.example.com"
    assert loaded.model.api_key_env == "ANTHROPIC_GATEWAY_API_KEY"
