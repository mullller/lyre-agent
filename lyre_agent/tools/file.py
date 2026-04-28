from __future__ import annotations

from pathlib import Path
import fnmatch

from lyre_agent.tools.base import Tool, ToolResult


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read a UTF-8 text file with optional line offset and limit."
    input_schema = {"type": "object", "properties": {"path": {"type": "string"}}}

    def run(self, path: str, offset: int = 1, limit: int = 500) -> ToolResult:
        p = Path(path)
        if not p.exists():
            return ToolResult(False, error=f"File not found: {path}")
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(offset - 1, 0)
        selected = lines[start : start + limit]
        numbered = "\n".join(f"{i + start + 1}|{line}" for i, line in enumerate(selected))
        return ToolResult(True, numbered, metadata={"total_lines": len(lines)})


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write a UTF-8 text file, replacing existing content."
    input_schema = {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}

    def run(self, path: str, content: str) -> ToolResult:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ToolResult(True, f"Wrote {len(content.encode('utf-8'))} bytes to {path}")


class SearchFilesTool(Tool):
    name = "search_files"
    description = "Find files by glob pattern under a directory."
    input_schema = {"type": "object", "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}}}

    def run(self, pattern: str = "*", path: str = ".", limit: int = 100) -> ToolResult:
        base = Path(path)
        if not base.exists():
            return ToolResult(False, error=f"Path not found: {path}")
        matches: list[str] = []
        for p in base.rglob("*"):
            if len(matches) >= limit:
                break
            rel = str(p.relative_to(base))
            if fnmatch.fnmatch(p.name, pattern) or fnmatch.fnmatch(rel, pattern):
                matches.append(rel + ("/" if p.is_dir() else ""))
        return ToolResult(True, "\n".join(matches), metadata={"count": len(matches)})
