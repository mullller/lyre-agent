# lyre-agent

Local-first CLI agent for developer workflows.

## MVP commands

```bash
python -m lyre_agent.cli version
python -m lyre_agent.cli config-show
python -m lyre_agent.cli tool-list
python -m lyre_agent.cli run "查看当前目录文件" --cwd .
python -m lyre_agent.cli chat
```

## Design goals

- Local-first: operate on the current workspace.
- Tool-based: shell, file, git first; integrations later.
- Safe by default: risky shell commands are classified before execution.
- Small MVP: no required third-party dependencies yet.

## Roadmap

1. OpenAI-compatible LLM provider.
2. SQLite sessions and memory.
3. Skill loader.
4. FastAPI server mode.
5. Feishu/Telegram integrations.
