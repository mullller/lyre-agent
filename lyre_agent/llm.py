from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class EchoProvider:
    """Tiny offline provider for MVP smoke tests.

    Real OpenAI-compatible provider can be added without changing Runtime.
    """

    def complete(self, messages: list[dict[str, str]], tools: list[dict] | None = None) -> LLMResponse:
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return LLMResponse(content=f"Echo: {user}")
