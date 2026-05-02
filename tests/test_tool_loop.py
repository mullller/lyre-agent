from __future__ import annotations

from copy import deepcopy

from lyre_agent.config import AgentConfig
from lyre_agent.llm import LLMResponse, ToolCall
from lyre_agent.runtime import AgentRuntime
from lyre_agent.tools.base import Tool, ToolResult
from lyre_agent.tools.registry import ToolRegistry


class FakeTool(Tool):
    name = "fake_lookup"
    description = "Look up a fake value."
    input_schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }

    def run(self, **kwargs):
        return ToolResult(success=True, output=f"value for {kwargs['query']}")


class FakeLLM:
    def __init__(self):
        self.calls = []

    def complete(self, messages, tools=None):
        self.calls.append((deepcopy(messages), deepcopy(tools)))
        if len(self.calls) == 1:
            return LLMResponse(tool_calls=[ToolCall(name="fake_lookup", arguments={"query": "alpha"})])
        return LLMResponse(content="final: " + messages[-1]["content"])


def test_runtime_executes_llm_tool_call_and_returns_final_answer():
    registry = ToolRegistry()
    registry.register(FakeTool())
    runtime = AgentRuntime(config=AgentConfig(), tools=registry)
    fake_llm = FakeLLM()
    runtime.llm = fake_llm

    output = runtime.run("use the lookup tool")

    assert output == "final: value for alpha"
    first_messages, first_tools = fake_llm.calls[0]
    second_messages, _ = fake_llm.calls[1]
    assert first_messages == [{"role": "user", "content": "use the lookup tool"}]
    assert first_tools[0]["function"]["name"] == "fake_lookup"
    assert second_messages[-1] == {
        "role": "tool",
        "name": "fake_lookup",
        "content": "value for alpha",
    }
