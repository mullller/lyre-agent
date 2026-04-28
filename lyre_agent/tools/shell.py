from __future__ import annotations

import subprocess
from lyre_agent.security import classify_command
from lyre_agent.tools.base import Tool, ToolResult


class ShellTool(Tool):
    name = "shell"
    description = "Run a shell command in the current workspace."
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "cwd": {"type": "string"},
            "timeout": {"type": "integer"},
        },
        "required": ["command"],
    }

    def __init__(self, require_confirm: bool = False):
        self.require_confirm = require_confirm

    def run(self, command: str, cwd: str | None = None, timeout: int = 180) -> ToolResult:
        risk = classify_command(command)
        if risk == "deny":
            return ToolResult(False, error=f"Command denied by policy: {command}", metadata={"risk": risk})
        if risk == "high" and self.require_confirm:
            return ToolResult(False, error="High risk command requires confirmation", metadata={"risk": risk})
        try:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                timeout=timeout,
                text=True,
                capture_output=True,
            )
            return ToolResult(
                success=proc.returncode == 0,
                output=proc.stdout,
                error=proc.stderr if proc.returncode != 0 else None,
                metadata={"exit_code": proc.returncode, "risk": risk},
            )
        except subprocess.TimeoutExpired:
            return ToolResult(False, error=f"Command timed out after {timeout}s", metadata={"risk": risk})
