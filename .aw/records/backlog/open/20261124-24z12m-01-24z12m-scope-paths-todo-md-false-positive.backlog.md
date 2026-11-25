- Id: 24z12m
- Status: open
- Set: 24z12m
- Work-Kind: bug
- Priority: medium
- Summary: check.scope-paths false-positives on real filenames containing TODO (such as TODO.md)
- Short-Description: check.scope-paths false-positives on real filenames containing TODO (such as TODO.md)
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-25 created (aw backlog): check.scope-paths false-positives on real filenames containing TODO (such as TODO.md)

### Bug

In `agent_workflows/production_checks.py::_check_ipd_conformance`, step 4 (`check.scope-paths`) runs a raw substring check:

```python
if not scope_val or "TODO" in scope_val or scope_val == "grandfathered":
```

Any valid IPD whose `- Scope-Paths:` legitimately lists a repository file whose name contains `TODO` (such as `TODO.md`) is falsely rejected with `BACKLOG-GRADUATE-IPD` / `SPEC-PLAN-CONFORMANCE`: `Scope-Paths must be concrete (not empty, not TODO, not grandfathered)`.

### Production evidence

Observed on 2026-11-24 during a `pubrun` planning run (`run-20261124T202433Z-1567679`): graduating backlog `qqwebg` produced IPD `1kcrdn` with `- Scope-Paths: .github/workflows/ci.yml, pyproject.toml, CONTRIBUTING.md, CHANGELOG.md, TODO.md`. The raw substring check failed the gate after 2h 12m and $25.89 of valid plan authoring.

### Acceptance criteria

1. `_check_ipd_conformance` rejects unfilled `TODO` placeholders in `Scope-Paths` (for example bare `TODO`, `TODO (...)`, or a comma-separated entry whose trimmed token is `TODO` or starts with `TODO `/`TODO:`) while accepting legitimate file paths such as `TODO.md` or `docs/TODO.md`.
2. Unit tests cover both legitimate paths containing `TODO` (`TODO.md`, `docs/TODO.md`) and placeholder `TODO` values.
