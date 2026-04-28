## Summary

<!-- What changed? Keep it concise. -->

## Why

<!-- What problem does this solve? -->

## Changes

- 
- 
- 

## Verification

Run at least the relevant checks:

- [ ] `python -m compileall -q lyre_agent tests`
- [ ] `python -m lyre_agent.cli version`
- [ ] `python -m lyre_agent.cli tool-list`
- [ ] `python -m lyre_agent.cli run "查看当前目录文件" --cwd .`
- [ ] `python -m pytest -q` if pytest is available

Additional verification:

```text
<!-- paste command output or describe manual checks -->
```

## Risk / Rollback

Risk level:

- [ ] Low
- [ ] Medium
- [ ] High

Rollback plan:

```text
<!-- How do we revert safely? -->
```

## Checklist

- [ ] Preserves local-first behavior
- [ ] Avoids unnecessary dependencies
- [ ] Does not commit secrets or tokens
- [ ] Keeps real side effects behind explicit tools
- [ ] Updates docs for user-facing behavior changes
- [ ] Adds/updates tests or smoke checks
