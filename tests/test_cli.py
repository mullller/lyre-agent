from lyre_agent.cli import main


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
