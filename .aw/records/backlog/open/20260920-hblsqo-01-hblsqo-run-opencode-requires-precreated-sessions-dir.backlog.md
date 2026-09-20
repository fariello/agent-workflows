- Id: hblsqo
- Status: open
- Blocks-Release: next
- Set: hblsqo
- Priority: low
- Work-Kind: bug
- Summary: run_opencode opens the attempt log without creating sessions/, so a new caller crashes at launch

## Workflow history
- 2026-09-20 created (aw backlog): Found while wiring the standalone audit verb (plan mp289j).

MEASURED 2026-09-20: `oc_runipd.run_opencode` computes `log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)` and then opens it with `log_path.open("w")` inside the `with` that also enters `turn_telemetry`. It does NOT create `log_path.parent`. So any caller that has not already created `<run_dir>/sessions/` dies with `FileNotFoundError` at the moment of launch.

WHY IT HAS NEVER BEEN HIT: the only two pre-existing callers are both reached from `initialize_run`, which creates the full run-directory skeleton. The requirement is therefore real but invisible, encoded nowhere except in the initializer that happens to satisfy it.

WHAT IT COST: the standalone `audit` verb (plan `mp289j`) builds a minimal run directory rather than a queued run, and crashed on its first end-to-end invocation. The failure is LATE and therefore expensive in the general case: the prompt has already been written and, with isolation on, a git worktree has already been allocated, so a caller that omits the directory leaks a lane and a prompt before failing.

FIXED LOCALLY by having the audit handler create `outcomes/`, `prompts/` AND `sessions/`. That is a fix to the caller, not to the contract.

THE REAL FIX is one line in `run_opencode` (or in `attempt_log_path`): `log_path.parent.mkdir(parents=True, exist_ok=True)` before the open. It is idempotent, costs nothing on the existing paths, and converts an undocumented caller obligation into a guarantee. The agy twin `run_agy_turn` should be checked for the same shape, since it also writes an attempt log.

EVIDENCE: `agent_workflows/oc_runipd.py` `run_opencode` (the `log_path.open("w", encoding="utf-8") as log` line); `agent_workflows/runner_shared.py` `attempt_log_path`; reproduced by removing the `sessions` entry from `oc_runipd.handle_audit_command`'s mkdir loop and running `tests/test_standalone_verify.py::TheVerbRunsEndToEnd`.
