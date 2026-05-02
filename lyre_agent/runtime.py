from __future__ import annotations

from lyre_agent.config import AgentConfig, load_config
from lyre_agent.llm import provider_from_config
from lyre_agent.tools.registry import ToolRegistry, default_registry


def _tool_schema(tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


class AgentRuntime:
    def __init__(self, config: AgentConfig | None = None, tools: ToolRegistry | None = None):
        self.config = config or load_config()
        self.tools = tools or default_registry()
        self.llm = provider_from_config(self.config.model)

    def run(self, prompt: str, cwd: str | None = None) -> str:
        """Run a single task.

        MVP includes deterministic shortcuts for local tools and an offline echo provider.
        This keeps the repo testable without API keys.
        """
        lower = prompt.lower()
        workdir = cwd or self.config.workspace.root
        if any(word in lower for word in ["当前目录", "list files", "有哪些文件", "文件"]):
            result = self.tools.get("search_files").run(path=workdir, pattern="*", limit=80)
            return "当前目录文件：\n" + result.as_text()
        if "git status" in lower or "git 状态" in lower:
            result = self.tools.get("git_status").run(cwd=workdir)
            return result.as_text() or "Git working tree clean."
        if "git diff" in lower or "diff" in lower:
            result = self.tools.get("git_diff").run(cwd=workdir)
            return result.as_text() or "No diff."
        messages = [{"role": "user", "content": prompt}]
        tool_schemas = [_tool_schema(tool) for tool in self.tools.list()]
        for _ in range(self.config.max_iterations):
            response = self.llm.complete(messages, tools=tool_schemas)
            if not response.tool_calls:
                return response.content
            for tool_call in response.tool_calls:
                try:
                    tool = self.tools.get(tool_call.name)
                    result = tool.run(**tool_call.arguments)
                    content = result.as_text()
                except Exception as exc:
                    content = f"Tool {tool_call.name} failed: {type(exc).__name__}: {exc}"
                messages.append({"role": "tool", "name": tool_call.name, "content": content})
        return "Agent stopped: max_iterations reached while processing tool calls."
