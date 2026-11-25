- Id: f3qdqh
- Status: open
- Set: f3qdqh
- Work-Kind: bug
- Priority: medium
- Summary: Fix ReleaseResolution attribute mismatch in artifact_meta.check_freshness (outcome/paths vs status/candidates)
- Short-Description: Fix ReleaseResolution attribute mismatch in artifact_meta.check_freshness (outcome/paths vs status/candidates)
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-25 created (aw backlog): Fix ReleaseResolution attribute mismatch in artifact_meta.check_freshness (outcome/paths vs status/candidates)

In agent_workflows/artifact_meta.py::check_freshness (lines 4976-4984), rel_outcome from agent_workflows/releases.py::resolve_release_outcome is accessed as rel_outcome.status and rel_outcome.candidates, whereas ReleaseResolution is NamedTuple(outcome: str, paths: List[Path]). The AttributeError is silently swallowed by except Exception: pass (line 4993), leaving release_gates.release_id6 for release_raw = 'next' unresolved. Discovered during /assess-bugs and re-homed out of orchestrator 92ujfc during /plan-review because it is backend-agnostic (outside companion/AW_HOME scope) and ywl7uc declined carrying it.
