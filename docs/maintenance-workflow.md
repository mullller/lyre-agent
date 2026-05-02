# Lyre Agent Maintenance Workflow

This document defines how code changes should be planned, implemented, reviewed and shipped for `lyre-agent`.

The goal is to make the repository maintainable even when work continues asynchronously while the owner is away.

## Operating Principle

Lyre Agent should be maintained as a small-core, tool-first project:

```text
Hermes-style Runtime + OpenClaw-style Control Plane
```

Every code change should preserve these principles:

- keep the core lightweight
- avoid unnecessary dependencies
- keep real actions behind explicit tools
- preserve local-first behavior
- keep secrets out of source, logs and memory
- document architecture-impacting changes

## Default Branch Strategy

- `master` is the stable branch.
- Non-trivial changes should use feature branches and Pull Requests.
- Direct commits to `master` are allowed only for small docs-only or emergency fixes.

Branch naming:

```text
feat/<short-topic>
fix/<short-topic>
docs/<short-topic>
refactor/<short-topic>
ci/<short-topic>
chore/<short-topic>
```

Examples:

```text
feat/openai-tool-loop
fix/tui-narrow-terminal
docs/control-plane-roadmap
refactor/tool-registry-metadata
```

## Commit Convention

Use Conventional Commits:

```text
feat: add OpenAI-compatible provider
fix: handle missing rich gracefully
docs: describe control plane roadmap
refactor: split tool registry metadata
test: add runtime tool-loop tests
ci: add pytest workflow
chore: update dependencies
```

Rules:

- Keep subject line concise.
- Use present tense.
- Mention verification in PR body, not necessarily in commit title.

## Change Size Policy

Prefer small PRs.

Good PR size:

- one feature
- one bug fix
- one refactor slice
- one docs topic

Avoid:

- mixing feature + refactor + formatting
- changing architecture and UI in the same PR
- adding platform integrations before core abstractions are ready

## Standard PR Lifecycle

### 1. Understand the task

Before editing:

- read relevant files
- check README architecture section
- identify affected modules
- decide whether this is docs, feature, fix, refactor or chore

### 2. Create or update a plan

For non-trivial work, write a short plan in the PR body or `docs/plans/`:

```md
## Plan

1. Add provider interface
2. Add provider implementation, e.g. OpenAI-compatible or Anthropic Messages API
3. Add tests with mocked HTTP responses
4. Wire runtime to provider selection
5. Update README
```

### 3. Implement in small slices

Each slice should be independently understandable.

Recommended sequence:

1. types/models/interfaces
2. tests
3. implementation
4. CLI/user-facing wiring
5. docs
6. cleanup

### 4. Run verification

Minimum local verification before PR:

```bash
python -m compileall -q lyre_agent tests
python -m lyre_agent.cli version
python -m lyre_agent.cli tool-list
python -m lyre_agent.cli run "查看当前目录文件" --cwd .
```

If pytest is available:

```bash
python -m pytest -q
```

For TUI changes:

```bash
printf '/status\n/help\n/exit\n' | python -m lyre_agent.cli chat --cwd .
printf '/exit\n' | python -m lyre_agent.cli chat --no-banner --cwd .
```

For README/logo changes:

```bash
python - <<'PY'
from pathlib import Path
assert Path('README.md').exists()
assert Path('assets/logo.svg').exists()
print('docs ok')
PY
```

### 5. Open PR

PR title should follow commit convention:

```text
feat: add OpenAI-compatible tool calling
```

PR body must include:

- Summary
- Why
- Changes
- Verification
- Risk / rollback

### 6. Review checklist

Before merge, check:

- [ ] Does this preserve local-first behavior?
- [ ] Does this avoid unnecessary dependencies?
- [ ] Are secrets kept out of code/logs/docs?
- [ ] Are tool side effects explicit?
- [ ] Are risky commands guarded by security policy?
- [ ] Are docs updated if behavior changed?
- [ ] Are tests or smoke checks included?

### 7. Merge

Preferred merge method:

```text
Squash merge
```

Delete feature branch after merge.

## Autonomous Maintenance Rules

When the owner is away, the agent may continue working under these rules.

### Allowed without asking

- docs improvements
- tests
- internal refactors that preserve behavior
- small UI polish
- adding missing error handling
- adding smoke checks
- opening PRs for review

### Requires explicit approval before merge or direct push

- dependency changes
- auth/security changes
- command execution policy changes
- platform integration credentials
- destructive file operations
- large architecture changes
- releasing/publishing packages

### Never do

- commit secrets or tokens
- store PATs in memory/docs/source
- force-push protected branches
- delete branches with unmerged work
- bypass failing tests without documenting why
- add heavy dependencies without justification

## Repository Maintenance Cadence

Recommended recurring maintenance:

### Per change

- run compile check
- run CLI smoke test
- update README/docs when user-facing behavior changes

### Weekly

- review open PRs
- check issues
- prune stale branches
- scan dependencies
- ensure README still matches actual CLI

### Before larger milestones

- add or update architecture docs
- ensure roadmap reflects current direction
- run full test suite
- tag release if packaging is ready

## Current Priority Roadmap

### Phase 1: Hermes-style Runtime

1. `paths.py` and profile-safe storage
2. Hermes-style tool registry metadata
3. `toolsets.py`
4. model providers: OpenAI-compatible and Anthropic Messages API
5. real tool-calling loop (initial provider tool-call parsing and runtime execution implemented)
6. prompt builder

### Phase 2: Skills and Memory

1. SQLite session store
2. memory store
3. skill loader/matcher
4. skill sedimentation workflow

### Phase 3: OpenClaw-style Control Plane

1. policy model
2. approval flow
3. audit logs
4. message routing models
5. gateway-independent platform adapters

### Phase 4: Integrations

1. API server
2. Feishu adapter
3. Telegram adapter
4. GitHub webhook/tooling adapter
5. optional MCP bridge

## Suggested PR Template

Use `.github/pull_request_template.md`.

## Suggested Issue Templates

Use `.github/ISSUE_TEMPLATE/`.
