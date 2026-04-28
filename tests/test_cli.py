from lyre_agent.cli import main
from lyre_agent.config import load_config
from lyre_agent.tools.registry import default_registry
from lyre_agent.ui import build_startup_state


def test_version(capsys):
    code = main(["version"])
    captured = capsys.readouterr()
    assert code == 0
    assert "lyre-agent 0.1.0" in captured.out


def test_tool_list(capsys):
    code = main(["tool-list"])
    captured = capsys.readouterr()
    assert code == 0
    assert "shell" in captured.out
    assert "read_file" in captured.out


def test_startup_state_contains_tools(tmp_path):
    state = build_startup_state(load_config(), default_registry(), cwd=str(tmp_path))
    assert state.version == "0.1.0"
    assert "shell" in state.tools
    assert state.workspace == str(tmp_path.resolve())
