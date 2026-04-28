from pathlib import Path

from lyre_agent.security import classify_command
from lyre_agent.tools.file import ReadFileTool, SearchFilesTool, WriteFileTool
from lyre_agent.tools.shell import ShellTool


def test_file_tools(tmp_path: Path):
    target = tmp_path / "hello.txt"
    written = WriteFileTool().run(str(target), "hello\nworld\n")
    assert written.success

    read = ReadFileTool().run(str(target), offset=2, limit=1)
    assert read.success
    assert "2|world" in read.output

    found = SearchFilesTool().run("*.txt", path=str(tmp_path))
    assert found.success
    assert "hello.txt" in found.output


def test_shell_tool():
    result = ShellTool().run("printf hello")
    assert result.success
    assert result.output == "hello"


def test_security_classification():
    assert classify_command("pwd") == "low"
    assert classify_command("pip install x") == "medium"
    assert classify_command("sudo reboot") == "high"
    assert classify_command("rm -rf /") == "deny"
