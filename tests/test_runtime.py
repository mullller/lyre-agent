from lyre_agent.runtime import AgentRuntime


def test_runtime_echo():
    out = AgentRuntime().run("你好")
    assert "你好" in out


def test_runtime_lists_files(tmp_path):
    (tmp_path / "a.txt").write_text("x")
    out = AgentRuntime().run("查看当前目录文件", cwd=str(tmp_path))
    assert "a.txt" in out
