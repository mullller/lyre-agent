from __future__ import annotations

from lyre_agent.config import AgentConfig, load_config
from lyre_agent.llm import EchoProvider
from lyre_agent.tools.registry import ToolRegistry, default_registry


class AgentRuntime:
    def __init__(self, config: AgentConfig | None = None, tools: ToolRegistry | None = None):
        self.config = config or load_config()
        self.tools = tools or default_registry()
        self.llm = EchoProvider()

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
        response = self.llm.complete([{"role": "user", "content": prompt}])
        return response.content
