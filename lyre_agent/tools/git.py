from __future__ import annotations

from lyre_agent.tools.base import Tool, ToolResult
from lyre_agent.tools.shell import ShellTool


class GitStatusTool(Tool):
    name = "git_status"
    description = "Run git status --short."
    input_schema = {"type": "object", "properties": {"cwd": {"type": "string"}}}

    def run(self, cwd: str = ".") -> ToolResult:
        return ShellTool().run("git status --short", cwd=cwd)


class GitDiffTool(Tool):
    name = "git_diff"
    description = "Run git diff --stat and git diff."
    input_schema = {"type": "object", "properties": {"cwd": {"type": "string"}}}

    def run(self, cwd: str = ".") -> ToolResult:
        stat = ShellTool().run("git diff --stat", cwd=cwd)
        diff = ShellTool().run("git diff", cwd=cwd)
        return ToolResult(
            success=stat.success and diff.success,
            output=(stat.output + "\n" + diff.output).strip(),
            error=stat.error or diff.error,
            metadata={"stat_exit": stat.metadata.get("exit_code"), "diff_exit": diff.metadata.get("exit_code")},
        )
