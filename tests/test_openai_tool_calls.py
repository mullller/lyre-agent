from __future__ import annotations

import json
import os
import urllib.request

from lyre_agent.config import ModelConfig
from lyre_agent.llm import OpenAICompatibleProvider


class FakeToolCallResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "type": "function",
                                    "function": {
                                        "name": "search_files",
                                        "arguments": '{"pattern":"*.py","path":"."}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }
        ).encode("utf-8")


def test_openai_provider_parses_function_tool_calls():
    original_urlopen = urllib.request.urlopen
    original_key = os.environ.get("OPENAI_TOOL_TEST_KEY")

    def fake_urlopen(request, timeout):
        return FakeToolCallResponse()

    try:
        os.environ["OPENAI_TOOL_TEST_KEY"] = "test-key"
        urllib.request.urlopen = fake_urlopen
        provider = OpenAICompatibleProvider(
            ModelConfig(
                provider="openai-compatible",
                name="gpt-test",
                base_url="https://openai.example.com/v1",
                api_key_env="OPENAI_TOOL_TEST_KEY",
            )
        )

        response = provider.complete([{"role": "user", "content": "find files"}])

        assert response.content == ""
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "search_files"
        assert response.tool_calls[0].arguments == {"pattern": "*.py", "path": "."}
    finally:
        urllib.request.urlopen = original_urlopen
        if original_key is None:
            os.environ.pop("OPENAI_TOOL_TEST_KEY", None)
        else:
            os.environ["OPENAI_TOOL_TEST_KEY"] = original_key
