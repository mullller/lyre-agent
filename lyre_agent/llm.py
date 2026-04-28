from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any
import urllib.error
import urllib.request

from lyre_agent.config import ModelConfig


@dataclass(slots=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class EchoProvider:
    """Tiny offline provider for MVP smoke tests."""

    def complete(self, messages: list[dict[str, str]], tools: list[dict] | None = None) -> LLMResponse:
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return LLMResponse(content=f"Echo: {user}")


class OpenAICompatibleProvider:
    """Minimal OpenAI-compatible Chat Completions provider.

    This intentionally uses the Python standard library so the CLI remains small.
    Tool calling will be layered on top later; for now this provides direct model access.
    """

    def __init__(self, config: ModelConfig):
        if not config.base_url:
            raise ValueError("openai-compatible provider requires model.base_url")
        self.model = config.name
        self.base_url = config.base_url.rstrip("/")
        self.api_key_env = config.api_key_env

    def complete(self, messages: list[dict[str, str]], tools: list[dict] | None = None) -> LLMResponse:
        api_key = os.environ.get(self.api_key_env or "") if self.api_key_env else None
        if self.api_key_env and not api_key:
            return LLMResponse(
                content=f"Missing API key env var: {self.api_key_env}. Run `lyre-agent model show` to inspect model config."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        request.add_header("Content-Type", "application/json")
        if api_key:
            request.add_header("Authorization", f"Bearer {api_key}")

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:800]
            return LLMResponse(content=f"Model request failed: HTTP {exc.code}\n{detail}")
        except Exception as exc:
            return LLMResponse(content=f"Model request failed: {type(exc).__name__}: {exc}")

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        return LLMResponse(content=content)


def provider_from_config(config: ModelConfig):
    if config.provider == "echo":
        return EchoProvider()
    if config.provider in {"openai-compatible", "openai"}:
        return OpenAICompatibleProvider(config)
    raise ValueError(f"Unsupported model provider: {config.provider}")
