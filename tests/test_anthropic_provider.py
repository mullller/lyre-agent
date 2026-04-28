import json

from lyre_agent.config import ModelConfig
from lyre_agent.llm import AnthropicProvider, provider_from_config


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({"content": [{"type": "text", "text": "hello from claude"}]}).encode("utf-8")


def test_provider_from_config_supports_anthropic():
    provider = provider_from_config(
        ModelConfig(
            provider="anthropic",
            name="claude-sonnet-4-5",
            base_url="https://api.anthropic.com",
            api_key_env="ANTHROPIC_API_KEY",
        )
    )

    assert isinstance(provider, AnthropicProvider)


def test_anthropic_provider_uses_messages_api_and_gateway_key_env(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("ANTHROPIC_GATEWAY_API_KEY", "gateway-secret")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = AnthropicProvider(
        ModelConfig(
            provider="anthropic",
            name="claude-3-5-sonnet-20241022",
            base_url="https://anthropic-gateway.example.com",
            api_key_env="ANTHROPIC_GATEWAY_API_KEY",
        )
    )

    response = provider.complete(
        [
            {"role": "system", "content": "You are concise."},
            {"role": "user", "content": "Hi"},
        ]
    )

    assert response.content == "hello from claude"
    assert captured["url"] == "https://anthropic-gateway.example.com/v1/messages"
    assert captured["headers"]["X-api-key"] == "gateway-secret"
    assert captured["headers"]["Anthropic-version"] == "2023-06-01"
    assert captured["payload"] == {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "system": "You are concise.",
        "messages": [{"role": "user", "content": "Hi"}],
    }
    assert captured["timeout"] == 120


def test_anthropic_provider_accepts_gateway_base_url_with_v1(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse()

    monkeypatch.setenv("ANTHROPIC_GATEWAY_API_KEY", "gateway-secret")
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    provider = AnthropicProvider(
        ModelConfig(
            provider="anthropic",
            name="claude-3-5-sonnet-20241022",
            base_url="https://anthropic-gateway.example.com/v1",
            api_key_env="ANTHROPIC_GATEWAY_API_KEY",
        )
    )

    provider.complete([{"role": "user", "content": "Hi"}])

    assert captured["url"] == "https://anthropic-gateway.example.com/v1/messages"


def test_anthropic_provider_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("MISSING_ANTHROPIC_KEY", raising=False)
    provider = AnthropicProvider(
        ModelConfig(
            provider="anthropic",
            name="claude-sonnet-4-5",
            base_url="https://api.anthropic.com",
            api_key_env="MISSING_ANTHROPIC_KEY",
        )
    )

    response = provider.complete([{"role": "user", "content": "Hi"}])

    assert "Missing API key env var: MISSING_ANTHROPIC_KEY" in response.content
