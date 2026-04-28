from __future__ import annotations

from lyre_agent.tools.base import Tool
from lyre_agent.tools.file import ReadFileTool, SearchFilesTool, WriteFileTool
from lyre_agent.tools.git import GitDiffTool, GitStatusTool
from lyre_agent.tools.shell import ShellTool


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def list(self) -> list[Tool]:
        return [self._tools[name] for name in self.names()]


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ShellTool())
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(SearchFilesTool())
    registry.register(GitStatusTool())
    registry.register(GitDiffTool())
    return registry
