# Review findings: plan behm9r

- Subject-Id: behm9r
- Subject-Type: ipd
- Reviewed-At: 2026-11-24
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ed34590cd` in a runner review-sweep lane worktree (non-interactive). The plan was committed and unmodified (last plan commit `b7ff07851`), so no pre-review snapshot was taken. Before revisions, `aw ipd lint --phase author` reported 2 info advisories (`IPD-C802`) and no errors or warnings. After revisions, `aw ipd lint --phase review-finalize` reported 3 advisories (`IPD-Z603` for E-03 naming 11 units, plus the same 2 `IPD-C802`) and no errors or warnings. Reviewed against backlog `diobl2`, spec `25kzda` (2.5b, 2.5d, the `--full-auto` dispatch row), spec `z7nbn1`, and `agent_workflows/runner_shared.py` (`execute_item_core`, `action_for`, `plan_kind_from_file`, `set_plan_approved`, `isolation_for_action`, `item_reached_success`, `dispatch_orchestrator_item`, `enforce_orchestrator_probe_gate`), `agent_workflows/status_set.py` (orchestrator readiness gate), `agent_workflows/orchestrator_readiness.py::review_readiness`, both hosts' `execute_item` and `run_queue`, and the test patterns in `tests/test_rereview_reviewed_plan.py` and `tests/test_orchestrator_retirement.py`.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | No Readiness or Review-Depth | `Readiness: go-pending-approval`, `Review-Depth: standard` | s7 output |
| E-01 | Code change and log wording only | Adds the `reached_success` comment update and keeps the `except` branch unchanged | PR-006 |
| E-02 | Called `execute_item_core` directly; no fixture readiness; no isolation setting | Drives `oc_runipd.execute_item` with patched `run_opencode`; `isolate_worktree: False`; ready orchestrator fixtures with `COVERAGE_PASS`; `import pytest`; fail-before expectations per case | PR-002, PR-003, PR-004, PR-005 |
| E-03 | One test for both hosts; "patch the item executor" | One test per host; stub `run_opencode` / `run_agy_turn`; never patch `execute_item`; fail-before expectation; slow-allowlist fallback | PR-001, PR-007 |
| Project conventions | No test model; no note on the readiness gate | Adds the `TestRereviewExecutionTurn` model and the `set_plan_approved` readiness-gate note | PR-001, PR-002 |
| Findings | F-01 to F-05 | Adds F-06 to F-09 | PR-001 to PR-005 |
| Proposed changes 2 and 3, Scope check, Required tests, Spec sync | Generic test wording | Matches the revised E-02 and E-03; adds the review baseline run and the fail-before step; records the spec check | PR-001 to PR-007 |
| V-01, V-02, V-03 | Post-fix output only | Add the fail-before output, the spawn-patch and fixture hunks, and the absence of `Failed to auto-approve` | PR-001, PR-002 |

#### Issues

- `IPD-C802` (the reachability-rule line in the validation section): an em dash in boilerplate the plan inherited; advisory only and left unchanged.
- `IPD-Z603` (E-03 names 11 units): advisory. E-03 is one concern (the per-host end-to-end test), and the names are the symbols the executor must patch or leave real, so it stays as one item.

### Step T

1. Yes: `execute_item_core` is the shared item executor for both runner hosts.
2. Yes: it changes which dispatch path a `--full-auto` orchestrator takes (agent turn versus rollup retirement).
3. No: 4 E-items, two files.
4. Yes: no `.spec.md` path in Scope-Paths.
5. Medium: a wrong fix either keeps spending an agent turn on orchestrators or routes a child plan away from execution.

Tier: standard.

### Step R1

- Checked: the diagnosis holds. In `execute_item_core`, the block `if run_action != "review": item["action"] = "execute"` follows `set_plan_approved`, and the `if auto_approved:` print hardcodes "progressing to execution". A grep finds no other `item["action"] = "execute"` site in `agent_workflows/`. `action_for(kind, "auto-approved")` returns `orchestrate` for an orchestrator and `execute` for `child` or `None`. Both hosts' `run_queue` short-circuit `action == "orchestrate"` to `dispatch_orchestrator_item`.
- Missed: `set_plan_approved` runs `aw set auto-approved`, and `status_set.py` gates that target on `orchestrator_readiness.review_readiness(..., ask=False)` for an orchestrator. An unready fixture is refused, the refusal is caught, and the test sees no auto-approval at all (PR-002).

### Step R2

- Checked: E/V bijection 4/4. Every V-item demands pasted diffs and runner output. `Item-Dependencies: none` is correct for Order 1 of a one-child Set. `From-Backlog: diobl2` and `Blocks-Release: next` match the backlog item.
- E-03 told the executor to "patch the item executor". `tests/test_orchestrator_retirement.py::DispatchRunCase.drive` patches `execute_item`, which skips `execute_item_core`, so that pattern would pass on unpatched code (PR-001).
- E-02 called `execute_item_core` directly without naming its six injected host bindings (PR-003). `isolation_for_action` defaults to isolation on (PR-004). The test module has no `import pytest` (PR-005).
- Baseline at `ed34590cd`: `tests/test_runner_fullauto_and_sweep_fixes.py` + `tests/test_rereview_reviewed_plan.py::TestRereviewExecutionTurn` + `tests/test_orchestrator_retirement.py::AnOrchestratorIsRetiredMidRun` gave `9 passed in 5.07s`, `0 unlisted slow tests`.

### Step R3

- Checked: no new subprocess, path, or input surface. The fix routes an already-approved orchestrator to the existing rollup path, which keeps its coverage re-check (`dispatch_orchestrator_item` calls `review_readiness(..., ask=True)`) before retirement. No security finding.

### Step R4

- Checked: the run-start probe gate skips orchestrators whose action is not `orchestrate`, so a newly-`orchestrate` item is covered only by the retirement-time re-check. With a current `- Coverage:` record that costs zero model calls, and with a stale one it probes, which is the documented 2.5b behavior. `item_reached_success({"action": "orchestrate", "status": "reviewed"})` is `False`, the same as the existing `execute` case, so only the comment needs updating (PR-006). Spec sync N/A is correct: the `25kzda` row "Tool-set `auto-approved` ... then execute" read with the `z7nbn1` refinement already means `orchestrate` for an orchestrator.

### Step S5

- Checked: no question needs a human. Test strategy, fixture readiness, and isolation settings are resolved from repository evidence and recorded as decisions D-1 to D-3.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | G executability / test validity | `oc_runipd.execute_item` calls `runner_shared.execute_item_core`; `tests/test_orchestrator_retirement.py::DispatchRunCase.drive` patches `execute_item` | Stubbing the item executor bypasses the code under test, so the E-03 test would pass on unpatched code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 stubs `run_opencode` / `run_agy_turn`, forbids patching `execute_item`, and requires a fail-before run; V-03 demands it. |
| PR-002 | MEDIUM | IN-SCOPE | C compatibility (gate) | `runner_shared.set_plan_approved` (`aw set auto-approved` via `run_checked`); `status_set.py` `_ready_forward_targets` includes `"auto-approved"` and calls `review_readiness(..., ask=False)` for orchestrators | An unready orchestrator fixture is refused; the `except` prints `Failed to auto-approve` and `auto_approved` stays `False`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and E-03 require a child row, a ready child, a conforming CONFIRM row, and a current `COVERAGE_PASS` record; V-02 checks for no `Failed to auto-approve`. |
| PR-003 | MEDIUM | IN-SCOPE | G executability | `runner_shared.execute_item_core` keyword arguments `host_labels`, `spawn_executor`, `spawn_verifier`, `raw_launcher`, `run_suite_check`, `process_backlog_close` (`oc_runipd.py` passes `raw_launcher=run_opencode`) | A direct call needs six host bindings the plan did not name. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 drives `oc_runipd.execute_item`, following `TestRereviewExecutionTurn`, and allows a direct call only with every binding from `oc_runipd`. |
| PR-004 | MEDIUM | IN-SCOPE | Performance / isolation | `runner_shared.isolation_for_action` falls back to `options.get("isolate_worktree", True)` | Without `isolate_worktree: False` each review turn allocates a real worktree, risking the 2s threshold. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and E-03 set `isolate_worktree: False`. |
| PR-005 | LOW | IN-SCOPE | G executability | `tests/test_runner_fullauto_and_sweep_fixes.py` imports `unittest` only | `@pytest.mark.core` raises `NameError` without `import pytest`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds `import pytest`; F-09. |
| PR-006 | LOW | IN-SCOPE | Documentation in code | Comment above `reached_success = item_reached_success(` ("rewritten it from `review` to `execute`") | The comment becomes incomplete once the bridge can write `orchestrate`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 updates the comment; V-01 demands the hunk. |
| PR-007 | LOW | IN-SCOPE | Performance | Real `aw set` subprocess plus real `retire_orchestrator` commit per host; measured `execute_item_core` tests run about 0.6-0.7s each | Two hosts in one test risk crossing the 2s slow threshold. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 splits into one test per host and names the slow-allowlist fallback. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Which layer do the tests stub? | The spawn layer (`run_opencode`, `run_agy_turn`) | Stub `execute_item` (rejected: bypasses the fix); call `execute_item_core` directly (allowed only with all host bindings) | `TestRereviewExecutionTurn` precedent; PR-001, PR-003 | yes |
| D-2 | Real or mocked `set_plan_approved`? | Real, with ready orchestrator fixtures | Mock it (rejected: hides the 2.5d gate interaction the fix depends on in production) | `status_set.py` readiness gate; PR-002 | yes |
| D-3 | One cross-host test or one per host? | One per host with a shared helper | One combined test (rejected: slow-threshold risk, and a failure would not name the host) | PR-007 | yes |
| D-4 | Review tier | standard | simple | Step T answers 1 and 2 yes, 5 medium | yes |
