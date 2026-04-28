# lyre-agent

Local-first CLI agent for developer workflows.

`lyre-agent` is designed as a lightweight, local-first CLI agent for engineering work. It borrows the proven architectural ideas from Hermes Agent — tool-first execution, provider-agnostic LLMs, sessions, memory, skills, and platform gateways — but keeps the core intentionally small.

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
- Provider-agnostic: OpenAI-compatible providers first, local models later.
- Skill-driven: reusable workflows should be stored as markdown skills.

## Architecture

Lyre Agent follows a small-core, tool-first architecture inspired by Hermes Agent.

The core runtime is responsible for:

1. Building the conversation context from config, session, memory and skills.
2. Calling an LLM provider with OpenAI-compatible tool schemas.
3. Dispatching tool calls through a central registry.
4. Appending normalized tool results back into the conversation.
5. Repeating until the model returns a final answer.

High-level flow:

```text
CLI / Chat / API / Webhook
          |
          v
   Agent Runtime
          |
          v
    LLM Provider
          |
          v
    Tool Registry
          |
          v
 File / Shell / Git / HTTP / Platform Tools
```

Long-lived context is provided by sessions, memory and skills:

```text
Config + Session + Memory + Skills
              |
              v
        Prompt Builder
              |
              v
        Agent Runtime
```

## Module layout

Planned module boundaries:

```text
lyre_agent/
  cli.py              # terminal entrypoints
  runtime.py          # agent loop and orchestration
  prompt.py           # system prompt and context builder
  config.py           # non-secret configuration
  paths.py            # LYRE_HOME/profile-safe paths

  llm/
    base.py           # provider interface
    openai_compatible.py
    echo.py

  tools/
    base.py           # Tool and ToolResult contracts
    registry.py       # central tool registry
    toolsets.py       # toolset grouping and enablement
    shell.py
    file.py
    git.py
    http.py
    github.py
    feishu.py

  session/
    store.py          # SQLite-backed sessions/messages/tool calls
    models.py

  memory/
    store.py          # durable user/project memory
    search.py

  skills/
    loader.py         # SKILL.md loader
    matcher.py        # task-to-skill matching
    models.py

  gateway/
    server.py         # optional HTTP/API mode
    models.py
    platforms/
      feishu.py
      telegram.py

  security/
    risk.py           # command/file operation risk classification
    approvals.py      # confirmation flow
    sandbox.py        # workspace boundary checks
```

The current MVP already includes the first slice of this layout: CLI, runtime, config, an offline echo provider, security classification, and file/shell/git tools.

## Core design principles

### 1. Local-first

The default operating model is the current workspace. Lyre Agent should avoid heavy local state, large dependencies and unnecessary generated files.

### 2. Tool-first

The model should not pretend to operate on the system. All real actions should go through explicit tools with normalized results and audit-friendly metadata.

### 3. Provider-agnostic

The runtime should not depend on a specific model SDK. Providers should implement a common interface. OpenAI-compatible tool calling is the first target because it covers OpenAI, OpenRouter, vLLM, LM Studio and many local gateways.

### 4. Small core, pluggable edges

The core should stay small. Integrations such as Feishu, Telegram, GitHub automation, browser automation and MCP should be optional toolsets or adapters, not mandatory dependencies.

### 5. Secret-safe

Normal settings belong in config files. Secrets belong in environment variables, `.env`, or auth stores. Tokens must not be written to memory, skills, logs or committed files.

### 6. Skill-driven

Repeatable workflows should become skills. A skill is a markdown document with trigger conditions, prerequisites, steps, verification and common pitfalls.

### 7. Profile-safe

All persistent paths should go through a central path helper, similar to Hermes' home/profile model. This allows isolated profiles for different projects, teams or platforms.

## Runtime loop

Target runtime behavior:

```text
user prompt
  -> load config/session/memory/skills
  -> build messages
  -> call LLM with tool schemas
  -> if tool calls: dispatch tools and append results
  -> repeat until final answer
```

Pseudo-code:

```python
def run(prompt, session_id=None):
    session = session_store.load_or_create(session_id)
    memories = memory.search(prompt)
    skills = skill_matcher.match(prompt)
    tools = registry.enabled_tools()

    messages = prompt_builder.build(
        session=session,
        memories=memories,
        skills=skills,
        user_prompt=prompt,
    )

    for _ in range(config.agent.max_turns):
        response = llm.complete(messages, tools=tools.schemas())

        if response.tool_calls:
            for call in response.tool_calls:
                result = tool_dispatcher.dispatch(call)
                messages.append(tool_result_message(result))
            continue

        return response.content

    return "Task did not finish: max turns reached."
```

## Tool system

Tools are registered centrally. Each tool should expose:

- `name`
- `toolset`
- `description`
- `input_schema`
- `handler`
- optional `check_fn`
- optional `requires_env`

This allows the runtime to export model-compatible schemas, disable unavailable tools, and group capabilities by environment.

Suggested toolsets:

```text
core       clarify, think
file       read_file, write_file, patch_file, search_files
terminal   shell, background_process
git        git_status, git_diff, git_log
http       http_get, http_post
memory     memory_add, memory_search
skills     skill_list, skill_view, skill_create
github     GitHub API helpers
feishu     Feishu send/reply/mention helpers
```

## Sessions, memory and skills

### Sessions

Sessions persist conversation history and tool calls:

```sql
sessions(id, title, cwd, created_at, updated_at)
messages(id, session_id, role, content, created_at)
tool_calls(id, session_id, name, args, result, created_at)
```

### Memory

Memory should be durable but compact:

- user preferences
- project conventions
- environment quirks
- recurring tool lessons

### Skills

Skills live under:

```text
~/.lyre-agent/skills/<skill-name>/SKILL.md
```

Recommended structure:

```md
---
name: example-skill
description: What this workflow does
---

# Trigger conditions
# Prerequisites
# Steps
# Verification
# Common pitfalls
```

## Gateway direction

Lyre Agent should eventually support:

```bash
lyre-agent serve
```

With endpoints such as:

```http
POST /v1/run
POST /v1/chat
POST /webhook/feishu
POST /webhook/telegram
```

All platforms should normalize into one message model:

```python
class IncomingMessage:
    platform: str
    chat_id: str
    user_id: str
    text: str
    raw: dict
```

Then all platforms share the same `AgentRuntime`.

## Roadmap

1. Add `paths.py` and profile-safe storage.
2. Refactor tool registry toward Hermes-style registration metadata.
3. Add `toolsets.py` and config-based enable/disable.
4. Implement OpenAI-compatible LLM provider.
5. Replace shortcut runtime with a real tool-calling loop.
6. Add SQLite session store.
7. Add memory store and retrieval.
8. Add skill loader and matcher.
9. Add stronger security approvals and workspace boundary checks.
10. Add API server mode.
11. Add Feishu/Telegram gateway adapters.

## Current MVP status

Implemented:

- CLI entrypoint
- config loader
- runtime skeleton
- offline echo provider
- tool registry
- file tools
- shell tool
- git tools
- command risk classification
- smoke tests

Next recommended step:

```text
paths.py + Hermes-style Tool Registry + OpenAI-compatible tool loop
```
