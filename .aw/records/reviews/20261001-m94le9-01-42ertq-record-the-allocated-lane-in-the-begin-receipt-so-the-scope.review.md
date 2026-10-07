# Review findings: plan 42ertq

- Subject-Id: 42ertq
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `08802f6e1` in an isolated review lane. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic
review, and `--phase review-finalize` was clean after revision.

Reproduced (gitignored `.aw/state/review-probe-42ertq/probe*.py`, `tmp_path` repos, no production edit):
- `probe.py`: canonical `aw/lane/pid001` commits `stale.py`; second `allocate_worktree` returns
  `aw/lane/pid001_attempt2` (`attempt-scoped`), uncommitted. `_plan_execution_tree` -> `pid001`
  (canonical? True, recorded attempt? False).
- `probe3.py` via `support.scope_drift_repo` (Scope-Paths `src/demo.py`), same shape: `check_scope_drift` ->
  `check.scope-drift error 1 changed path is outside the plan's declared Scope-Paths: 'stale.py'`, selected tree
  `.../abc123` (the abandoned lane). With the live lane committing in-scope work instead, `probe2.py` selected
  `abc123_attempt2` and emitted nothing, so the defect needs the live lane to hold no work yet.
- `probe4.py`: canonical and `_attempt3` hold work, empty `_attempt2` torn down, re-allocation reuses
  `aw/lane/pid002_attempt2` and commits. `_plan_execution_tree` -> `pid002_attempt3` (live lane? False).
- `unittest.mock.Mock(side_effect=<3-positional fn>)(1,2,3,recorded_branch='x')` -> `TypeError: ... unexpected
  keyword argument 'recorded_branch'`.
- Cited code resolves: `oc_runipd.driver_begin`/`agy_runipd.driver_begin` delegate to `runner_shared.driver_begin`;
  `execute_item_core` self-finalize arm runs `driver_begin` then `allocate_isolation_worktree` and writes
  `attempt["worktree_branch"/"worktree_lane_id"/"worktree_base"]` plus a `worktree-allocated` event
  (`agent_workflows/runner_shared.py:32625-32700`); `RECEIPT_SCHEMA_VERSION = 2` with v2 additive comment
  (`agent_workflows/ipd_lifecycle.py:268-275`); `refreeze_receipt` keeps `base_head` (`:1989`);
  `_atomic_write_json` (`:1265`); `receipt_dir` via `checkout_control_root` (`:702`);
  `lane_branch_name`/`lane_id_from_branch` docstrings (`agent_workflows/worktree_lease.py:102-133`);
  `check.scope-drift` `error`, `check.scope-not-audited` `info` (`agent_workflows/check_engine.py:590-598`);
  no test asserts the receipt `schema_version`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | G. Premise / evidence currency | `agent_workflows/check_engine.py:3333` `_plan_execution_tree` now calls `worktree_lease.enumerate_lane_candidates`; `iqtt8d` finalized `418bd00ff`, `qqg41f` `673ed93a0` (2026-10-01) | The Concern, E-04 fallback ("today's `inspect_lane`"), E-05, E-06 (a) and E-08 conditionals describe a pre-`iqtt8d` world. The canonical-name defect is already fixed, so as written the plan's demonstrated beneficiary no longer exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measured the residual defect (F-13: heuristic misattribution, a false `error` finding) and re-aimed Concern, Goal, Scope, E-01, E-04, E-05, E-06, E-08 and V-items at it; added F-13; annotated F-7, F-12, OQ-01 and the Deferred row. |
| PR-002 | HIGH | IN-SCOPE | E. Testing (test guards the fix) | `tests/test_scope_drift_lane_resolution.py` (canonical-vs-attempt case already covered); probes above | E-06 case (a) built on "attempt-scoped lane recorded vs withheld" would pass both halves under current code, since enumeration already finds an attempt lane that descends from base. The contrast would prove nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (a) rebuilt on the two reproduced F-13 shapes (holds-work tie-break and reused-attempt tie-break), in both false-positive and masked-true-positive directions; V-06 rejects a contrast whose withheld half is already correct. |
| PR-003 | MEDIUM | IN-SCOPE | D. Anti-regression | `tests/test_scope_drift_lane_resolution.py:176-188` patches `_plan_execution_tree` with a 3-positional `side_effect`; mock `TypeError` reproduced | Threading the recorded branch as an unconditional extra argument would break an existing, correct test that this plan declares no right to edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires an optional keyword-only parameter passed only when a lane is recorded; E-08/V-08 run that module unmodified. |
| PR-004 | MEDIUM | UNDER-SCOPE | A. Correctness | `agent_workflows/check_engine.py:3485-3523` not-audited arm re-enumerates siblings when `_plan_execution_tree` returns `None` | The plan did not say how the recorded route interacts with `iqtt8d`'s `check.scope-not-audited` arm, nor whether an unusable recorded lane falls through to enumeration. Falling through, or letting the arm consider siblings, reintroduces the misattribution the record exists to settle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04: a recorded-but-unusable lane returns `None` (no sibling fallback) and the not-audited arm considers only the recorded lane when one is recorded; E-06 (d) and V-04 pin both. |
| PR-005 | LOW | IN-SCOPE | F. KISS / duplication | `agent_workflows/worktree_lease.py:564` "SECOND INSTANCE OF RECONSTRUCT-A-BRANCH-NAME HAZARD" already written by `iqtt8d` | E-05 asked to write the same hazard note again at the new updater. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05/V-05 now cross-reference that note and add only the new fact. |
| PR-006 | LOW | IN-SCOPE | G. Open questions | OQ-01/OQ-02 `Status: open`, `Blocking: no` | Both are answerable from repository evidence after PR-001/PR-004 (supersession is moot once `iqtt8d` executed; PR-004 removes the only correctness reason to clear stale lane records). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved as reversible reviewer decisions D-2, D-3, owner recorded as the reviewer, original rationale preserved. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | With the canonical-name defect already fixed by `iqtt8d`, is this plan still warranted or should it be retired? | Keep, re-aimed at the heuristic misattribution (F-13) | Retire as superseded by `iqtt8d`; REJECT - NEEDS REPLAN | Probes `probe.py`/`probe3.py`/`probe4.py` reproduce a false `error` finding the heuristic cannot avoid; the backlog `m94le9` direction (record, not infer) is exactly the remedy; changes are bounded edits to the existing design | yes |
| D-2 | OQ-01: supersede, keep as fallback, or keep enumeration permanently? | Keep permanently as the fallback | Supersede `iqtt8d` | `iqtt8d` executed; enumeration is the only route for receipts on disk (F-3) and for `aw work begin` lanes (F-8) | yes |
| D-3 | OQ-02: clear or reconcile the lane block on teardown/reclaim? | No; overwrite on retry, degrade to `None` when absent | Teach `teardown_isolation_worktree`/`reclaim_lanes_on_interrupt` to edit the receipt | E-04 no-sibling-fallback rule makes a stale record harmless; those functions are outside Scope-Paths; F-10 precedent | yes |
| D-4 | Should a recorded-but-unusable lane fall through to enumeration? | No, return `None` | Fall through to `enumerate_lane_candidates` | F-13 probes: enumeration picks the abandoned sibling in exactly these shapes; F-10 silence precedent | yes |
| D-5 | How should the recorded branch reach `_plan_execution_tree`? | Optional keyword-only param, passed only when recorded | Unconditional extra argument; re-read receipt inside the function | mock `TypeError` reproduction against `tests/test_scope_drift_lane_resolution.py:176-188`; plan's own "thread it in, don't re-read" instruction | yes |

## Round 2

Re-reviewed 2026-10-06 at HEAD `fe2ee961c` in an isolated review-sweep lane. Plan committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic review and
`--phase review-finalize` clean after revision. Round 1's `- Readiness:` had been removed by `8c460a9a1` (plan was
left at `to-review`, which may not carry the field); this round sets `reviewed`.

Re-verified (gitignored probe `.aw/state/review-probe-42ertq-r2/probe.py`, `tmp_path` repo, no production edit):
F-13 shape (i) reproduces at this HEAD: second `allocate_worktree` -> `aw/lane/abc123_attempt2 attempt-scoped`;
`_plan_execution_tree` -> `abc123` (live? False); `check_scope_drift` -> `check.scope-drift` severity `error`,
`1 changed path is outside the plan's declared Scope-Paths: 'stale.py'`. `_plan_execution_tree` signature unchanged
`(repo_root, plan_id, base_head)`. `RECEIPT_SCHEMA_VERSION = 2` (`agent_workflows/ipd_lifecycle.py:275`).
Self-finalize arm: `driver_begin(... isolated=True)` then `allocate_isolation_worktree`
(`agent_workflows/runner_shared.py:33940`, `:33971`). Sibling modules plus the `execute_item_core` harness:
`59 passed in 14.07s`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | MEDIUM | IN-SCOPE | A. Compatibility / C. precedent | `agent_workflows/ipd_lifecycle.py:2089` `record_scope_reasons` (commit `f3e833039`) adds `scope_justifications` with no schema bump; `ipd_lifecycle.py:1994` `begin` stamps `RECEIPT_SCHEMA_VERSION` | E-02 called the v3 bump "the established local practice", but a newer additive receipt key landed without one, and the plan never covered the most common post-change shape: a v3 receipt with NO `lane` block (every non-isolated begin, refused update, or begin-to-allocate window). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names the counter-precedent and the distinguishing reason (a checked-in reader branches on presence, as with v2), notes no reader branches on `schema_version`; E-06 (c), V-02, V-06 and Scope check add a lane-less v3 receipt from real `begin`. |
| PR-102 | MEDIUM | UNDER-SCOPE | G. Reachability of runtime demonstrations | `tests/test_finalize_stale_plan_path.py:146-159` drives `execute_item_core` with `isolate_worktree: True` and `driver_begin` patched to `(0, "ok")`; `agent_workflows/runner_shared.py:33263`, `:33272` resolve via `getattr(driver_module, ...)` | E-06 (e)/(f) and V-03 demanded observations from driving `execute_item_core` without naming a reachable harness; the obvious harness patches `driver_begin` to write NO receipt (so (e) would silently hit the refusal path), and no step said how to force an attempt-scoped handle. "Both hosts" was asserted from one `driver_module`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 names the harness, requires a real receipt for (e) and none for (f), pre-creates a committed canonical lane to force `_attemptN`, and drives both `oc_runipd` and `agy_runipd`; V-06 demands both runs' evidence. |
| PR-103 | LOW | IN-SCOPE | G. Execution contract | plan `## Approval and execution gate` | Gate lacked scope-fence-as-declaration wording (justify via `--scope-reason`/`--scope-ack`), an explicit resolved-OQ statement, and conditional finalize ownership; and "commit ONLY declared Scope-Paths" excluded the plan file the executor must update. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate amended for all four. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Keep the v3 bump given `scope_justifications` landed without one? | Keep the bump, documented with the distinguishing reason | Drop the bump and add `lane` at v2 | v2 precedent (`ipd_lifecycle.py:268-275`): bump when a reader branches on a new key's presence; no reader branches on `schema_version`, so either choice is behavior-neutral | yes |
| D-2 | How should E-06 (e) prove "both hosts"? | Drive `execute_item_core` with each `driver_module` | One host plus inference from shared body | `runner_shared.py:33263-33275` dispatches through `driver_module`; cost is one extra parametrized run | yes |
