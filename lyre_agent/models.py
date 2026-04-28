from __future__ import annotations

from dataclasses import dataclass

from lyre_agent.config import AgentConfig, ModelConfig, save_config


@dataclass(frozen=True, slots=True)
class ModelPreset:
    alias: str
    provider: str
    name: str
    base_url: str | None
    api_key_env: str | None
    description: str


MODEL_PRESETS: dict[str, ModelPreset] = {
    "echo": ModelPreset(
        alias="echo",
        provider="echo",
        name="echo",
        base_url=None,
        api_key_env=None,
        description="Offline echo provider for smoke tests.",
    ),
    "openai:gpt-4.1": ModelPreset(
        alias="openai:gpt-4.1",
        provider="openai-compatible",
        name="gpt-4.1",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        description="OpenAI GPT-4.1 via Chat Completions.",
    ),
    "openai:gpt-4.1-mini": ModelPreset(
        alias="openai:gpt-4.1-mini",
        provider="openai-compatible",
        name="gpt-4.1-mini",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        description="Smaller OpenAI GPT-4.1 model.",
    ),
    "openrouter:sonnet": ModelPreset(
        alias="openrouter:sonnet",
        provider="openai-compatible",
        name="anthropic/claude-sonnet-4.5",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        description="Claude Sonnet through OpenRouter's OpenAI-compatible API.",
    ),
    "openrouter:gpt-oss": ModelPreset(
        alias="openrouter:gpt-oss",
        provider="openai-compatible",
        name="openai/gpt-oss-120b",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        description="OpenAI OSS model through OpenRouter.",
    ),
    "local": ModelPreset(
        alias="local",
        provider="openai-compatible",
        name="local-model",
        base_url="http://localhost:8000/v1",
        api_key_env="LYRE_LOCAL_API_KEY",
        description="Local OpenAI-compatible server such as vLLM, LM Studio or Ollama gateway.",
    ),
}


def list_model_presets() -> list[ModelPreset]:
    return [MODEL_PRESETS[key] for key in sorted(MODEL_PRESETS)]


def resolve_model(alias_or_name: str) -> ModelPreset | None:
    return MODEL_PRESETS.get(alias_or_name)


def apply_model_switch(
    config: AgentConfig,
    alias_or_name: str,
    *,
    provider: str | None = None,
    base_url: str | None = None,
    api_key_env: str | None = None,
    config_path: str | None = None,
) -> AgentConfig:
    preset = resolve_model(alias_or_name)
    if preset:
        config.model = ModelConfig(
            provider=preset.provider,
            name=preset.name,
            base_url=preset.base_url,
            api_key_env=preset.api_key_env,
        )
    else:
        config.model = ModelConfig(
            provider=provider or "openai-compatible",
            name=alias_or_name,
            base_url=base_url,
            api_key_env=api_key_env,
        )

    if provider:
        config.model.provider = provider
    if base_url:
        config.model.base_url = base_url
    if api_key_env:
        config.model.api_key_env = api_key_env

    save_config(config, config_path)
    return config
