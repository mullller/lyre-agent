from __future__ import annotations

import json
import os
import urllib.request

from lyre_agent.config import ModelConfig
from lyre_agent.llm import AnthropicProvider


class FakeAnthropicToolUseResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(
            {
                "content": [
                    {"type": "text", "text": "I will inspect files."},
                    {"type": "tool_use", "name": "search_files", "input": {"pattern": "*.py"}},
                ]
            }
        ).encode("utf-8")


def test_anthropic_provider_parses_tool_use_blocks():
    original_urlopen = urllib.request.urlopen
    original_key = os.environ.get("ANTHROPIC_TOOL_TEST_KEY")

    def fake_urlopen(request, timeout):
        return FakeAnthropicToolUseResponse()

    try:
        os.environ["ANTHROPIC_TOOL_TEST_KEY"] = "test-key"
        urllib.request.urlopen = fake_urlopen
        provider = AnthropicProvider(
            ModelConfig(
                provider="anthropic",
                name="claude-test",
                base_url="https://anthropic.example.com",
                api_key_env="ANTHROPIC_TOOL_TEST_KEY",
            )
        )

        response = provider.complete([{"role": "user", "content": "find files"}])

        assert response.content == "I will inspect files."
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "search_files"
        assert response.tool_calls[0].arguments == {"pattern": "*.py"}
    finally:
        urllib.request.urlopen = original_urlopen
        if original_key is None:
            os.environ.pop("ANTHROPIC_TOOL_TEST_KEY", None)
        else:
            os.environ["ANTHROPIC_TOOL_TEST_KEY"] = original_key
