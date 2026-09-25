# IPD: Share the lane reclaim prompt and the deferred-integration adapter, and delete the dead host _record_forced_stop copies

- Date: 2026-09-25
- Kind: child
- Concern: THREE DIVERGENT RUNNER FORKS ARE OWNED BY NO PENDING PLAN, and one of them hides a live behavioral split. Re-measured at HEAD `8e74dcac` with `python3 tools/runner_fork_scan.py` (13 divergent forks). Of the 13, `recovone`/`cdxcbh` owns four (`classify_recovery_disposition`, `build_verify_and_continue_notice`, `reconcile_disposition`, `route_recovery_turn`); `handle_audit_command` is HOST-SPECIFIC-BY-CAPABILITY (research `fedqe6`); `execute_item`, `run_queue`, `initialize_run`, `main`, `build_parser` are the CORE-PLUS-HOOK host shells the maintainer chose 2026-09-14 (recorded by executed `40it5e`). That leaves exactly three unowned: (1) `_record_forced_stop` (backlog `dstnso`): BOTH host copies are DEAD, since `runner_shared.execute_item_core` calls the module-local `runner_shared._record_forced_stop` and nothing in the package or tests names the host copies; `liftaudit`/`afpmdu` edits only the shared copy and states "No host module is in scope". (2) `retry_deferred_integrations` (backlog `5jsjnr`): 46/46 lines at 0.998, but the one differing statement is NOT cosmetic. agy's `_integrate` passes `dict(item)` (a shallow copy) into `make_integration_validation_runner`, so `_record_revalidation` writes `post_merge_revalidation` onto the copy and `record_integration_refusal`'s `revalidation_was_unmeasured(item)` (the `l2mzxn` reclassification) cannot see it on agy's retry path; oc passes the live `item`. Probe: copy call leaves the live item with no record (`unmeasured: False`), live call gives `unmeasured: True`. So on agy a harness refusal during a deferred re-attempt is labeled `merge-refused` (terminal) instead of `merge-unchecked` (deferrable). (3) `_lane_reclaim_prompt` (backlog `8hx3g3`): 29/29 lines differing only in spelling (`print(file=...)` vs `print('', file=...)`, f-string vs `.format`), kept forked solely because it reads the per-host `_LANE_PROMPT_DISABLED`. Also covers `5jsjnr` (live residue: `retry_deferred_integrations`) and `8hx3g3`.
- Scope: IN: `runner_shared.lane_reclaim_prompt` taking suppression and timeout as PARAMETERS with each host's `_lane_reclaim_prompt` a one-statement delegation (the flag, `disable_lane_prompt` and `LANE_PROMPT_TIMEOUT` stay per host); `runner_shared.retry_deferred_integrations` on oc's body with host bindings injected, both hosts one-statement delegations; deleting both dead host `_record_forced_stop` definitions; one behavioral test module; correcting the docstrings that call `_lane_reclaim_prompt` "DIVERGED" or cite test files deleted in `19313eed`. OUT: the four `cdxcbh` symbols; `runner_shared._record_forced_stop` itself (`afpmdu`); the five host shells; `handle_audit_command`; `disable_lane_prompt` (stays per host by design); the unused `validation_runner_for` parameter of `runner_shared.reattempt_deferred_integrations`.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_forkresid_shared_shells.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: forkresid
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 184tn9
- From-Backlog: dstnso
- Blocks-Release: next

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog dstnso, 5jsjnr, 8hx3g3; re-ran runner_fork_scan (default, --closure, --triples) at HEAD 8e74dcac, confirmed 13 divergent forks of which exactly three (_record_forced_stop host copies, retry_deferred_integrations, _lane_reclaim_prompt) are owned by no pending plan and are not intended host shells, and probed the agy dict(item) copy losing the revalidation record.

## Goal

Take the runner fork census from 13 divergent forks to 10, where every remaining one is owned by a pending plan (`cdxcbh`), recorded host-specific (`handle_audit_command`), or an intended host shell; and fix agy's deferred re-attempt mislabeling an unmeasured refusal as a terminal merge refusal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and failing test

- [ ] E-01 Record the baseline: run `python3 tools/runner_fork_scan.py`, `python3 tools/runner_fork_scan.py --triples`, and `python3 tools/runner_fork_scan.py --closure --symbols _lane_reclaim_prompt retry_deferred_integrations`, and `grep -rn "_record_forced_stop" agent_workflows/ tests/ --include=*.py`.
  - Depends on: none
  - Expected outcome: `DIVERGENT FORKS (13)` listing the 13 names in this plan's Concern; `--triples` lists `_record_forced_stop`; the grep shows the only CALLS of `_record_forced_stop` are inside `runner_shared.py` (in `execute_item_core`), plus the two host `def` lines.
  - Execution state: pending

- [ ] E-02 Add `tests/test_forkresid_shared_shells.py` with, for EACH host (`oc_runipd`, `agy_runipd`, parameterized by subTest or two methods): (a) `DeferredRetryUnmeasuredTests`: build a tiny real git repo (`git init`, one commit, `git branch aw/lane/fr0001`), a state with `options={"validate": False, "integration_retry_limit": 10, "on_integration_blocked": "defer"}` and one queue item `{"id6": "fr0001", "status": runner_shared.INTEGRATION_DEFERRED_STATUS, "preserved_branch": "aw/lane/fr0001", "preserved_worktree": "", "attempts": [{}]}` (no `preserved_base`, so the validation runner refuses UNMEASURED on unresolved base/head without running a suite); patch `<host>.integrate_lane_branch` with a fake that CALLS the runner it is given (`ok = runner("", [])`) and returns `(ok, "gate refused", runner_shared.INTEGRATION_REFUSAL_CONFLICT)`; call `<host>.retry_deferred_integrations(run_dir, state)`; assert `item["integration_ladder"]["kind"] == runner_shared.INTEGRATION_REFUSAL_UNMEASURED` and `runner_shared.revalidation_was_unmeasured(item)` is True. (b) `LanePromptSuppressionTests`: with `sys.stdin`/`sys.stderr` patched to TTY stubs whose `readline` returns `"d\n"` and `select.select` patched to report ready, `<host>._lane_reclaim_prompt({"holds_work": True, "lane_id": "x", "branch": "b"}, "keep")` returns `"discard"`; after `<host>.disable_lane_prompt()` (inside `mock.patch.object(<host>, "_LANE_PROMPT_DISABLED", False)` so the flag is restored) it returns `None`; and a non-TTY stdin returns `None`. Patch `select.select` on the stdlib `select` module object so the patch reaches the call both before and after E-03. Run the file BEFORE any code change.
  - Depends on: E-01
  - Expected outcome: before the fix, the agy case of (a) FAILS (kind is `merge-refused`) while the oc case passes; all (b) cases pass on both hosts (they pin behavior E-03 must preserve).
  - Execution state: pending

### Task group 2: the three lifts

- [ ] E-03 Share `_lane_reclaim_prompt`. Add `runner_shared.lane_reclaim_prompt(lane: dict[str, Any], default_action: str, *, disabled: bool, timeout: float) -> str | None` carrying oc's body verbatim except that `if _LANE_PROMPT_DISABLED:` becomes `if disabled:` and `LANE_PROMPT_TIMEOUT` becomes `timeout`; import `select` lazily inside the function. Both keyword-only parameters have NO default, so a caller cannot silently skip suppression. Replace each host's `_lane_reclaim_prompt` body with the single statement `return runner_shared.lane_reclaim_prompt(lane, default_action, disabled=_LANE_PROMPT_DISABLED, timeout=LANE_PROMPT_TIMEOUT)`, which reads the host's OWN flag at CALL time, so `disable_lane_prompt`'s `global` write is still honored and the per-host flag is unchanged. Keep `_LANE_PROMPT_DISABLED`, `disable_lane_prompt` and `LANE_PROMPT_TIMEOUT` in each host; drop the host's top-level `import select` only if nothing else in that module uses it. Correct the prose that is now false: the `runner_shared` module docstring bullet and the `# ---- lanes` banner comment that call the reader "DIVERGED, so it stays behind", and the `reclaim_lanes_on_interrupt` docstrings in all three modules that cite `UnmovableSymbolTests`/`tests/test_hostdedup_identical_lift.py` (both removed by `19313eed`); point them at `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests`.
  - Depends on: E-02
  - Expected outcome: one body for the prompt; host `_lane_reclaim_prompt` is a sanctioned thin wrapper; `tests/test_oc_runipd.py`'s `mock.patch.object(driver, "_lane_reclaim_prompt", ...)` still takes effect because the host wrapper stays the name `reclaim_lanes_on_interrupt` injects.
  - Execution state: pending

- [ ] E-04 Share `retry_deferred_integrations`. Add `runner_shared.retry_deferred_integrations(run_dir, state, *, poll, ask, integrate_lane_branch, integrate_review_lane_branch, make_validation_runner, run_suite_check, process_backlog_close)` carrying oc's body (`_handle_for`, `_integrate`, `_finish`, `_integrate_review`, `_finish_review`, and the `reattempt_deferred_integrations(...)` call), with `_integrate` passing the LIVE `item` (oc's form, which is the fix) and every host-bound name taken from the injected parameters rather than module globals. Keep `validation_runner_for=lambda item: make_validation_runner(state, run_dir, dict(item), suite_check=run_suite_check)` exactly as today. Replace each host's body with one statement: `return runner_shared.retry_deferred_integrations(run_dir, state, poll=poll, ask=ask, integrate_lane_branch=integrate_lane_branch, integrate_review_lane_branch=integrate_review_lane_branch, make_validation_runner=make_integration_validation_runner, run_suite_check=run_suite_check, process_backlog_close=process_backlog_close)`, resolving each name from the host module at call time so existing `mock.patch.object(<host>, ...)` seams keep working. Keep the host docstrings short and pointing at the shared one.
  - Depends on: E-02
  - Expected outcome: one body; both hosts sanctioned thin wrappers; agy now records revalidation on the live item.
  - Execution state: pending

- [ ] E-05 Delete the two DEAD host definitions `oc_runipd._record_forced_stop` and `agy_runipd._record_forced_stop`. Re-run the E-01 grep first; if any caller outside `runner_shared.py` has appeared, STOP and report rather than deleting. Do not touch `runner_shared._record_forced_stop` (owned by `afpmdu`).
  - Depends on: E-01
  - Expected outcome: `_record_forced_stop` is defined once, in `runner_shared`; no host references it.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Re-run the scanner and the new tests plus the existing retry and lane-reclaim regressions: `python3 tools/runner_fork_scan.py`, `python3 tools/runner_fork_scan.py --triples`, `python3 -m pytest tests/test_forkresid_shared_shells.py -o addopts=""`, and `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -k "FailClosedIntegrationGuard or VerifierGateAndRunnerBug" -o addopts=""`.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: `DIVERGENT FORKS (10)` with `_lane_reclaim_prompt`, `retry_deferred_integrations` and `_record_forced_stop` absent; `--triples` no longer lists `_record_forced_stop`; all new tests pass on both hosts; the existing classes pass.
  - Execution state: pending

- [ ] E-07 Run the bare suite: `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: green summary line, or any failure shown to fail identically on the pre-change tree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Sanctioned de-duplicated form: `runner_shared` owns the body taking outside dependencies as parameters; each host keeps a one-statement delegation (`818uru` OQ-02 ruling; `tools/runner_fork_scan.py::is_pure_delegation`). `reclaim_lanes_on_interrupt` (`gqo6if` E-03) already injects `lane_prompt=`/`disable_prompt=` the same way.
- `runner_shared` forbids module-level mutable state and a registration seam was declined (its module docstring), so the flag must stay per host; passing it as a parameter satisfies both.
- Change-detector tests over code text were retired (`d4dd6b88`, and the trim `19313eed`); new tests here are behavioral. Fork counts are evidenced with the committed scanner, not a new test.
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-1 | HIGH | agy `retry_deferred_integrations._integrate`: `make_integration_validation_runner(state, run_dir, dict(item), ...)`; oc passes `item`; probe under `/tmp/opencode/g3/probe-forkresid/p.py` printed `copy call -> False live has record: False unmeasured: False` then `live call -> False live has record: True unmeasured: True` | agy's deferred re-attempt cannot apply the `l2mzxn` unmeasured reclassification in `record_integration_refusal`. |
| F-2 | MEDIUM | `grep -rn _record_forced_stop`: calls only at `runner_shared.execute_item_core` (`record = _record_forced_stop(`), plus host `def`s; `afpmdu` Scope-check: "No host module is in scope" | Host copies are dead code and a three-way fork (`--triples`). |
| F-3 | MEDIUM | `--closure`: `_lane_reclaim_prompt` closes over `LANE_PROMPT_TIMEOUT`, `_LANE_PROMPT_DISABLED`, `select`; AST diff is 4 spelling-only lines | Parameter injection removes the only reason it stayed forked. |
| F-4 | LOW | `grep -rn UnmovableSymbolTests tests/` finds only a comment; `tests/test_hostdedup_identical_lift.py`, `tests/test_runner_refork_guard.py` absent (deleted `19313eed`) | Docstrings cite pins that no longer exist. |
| F-5 | INFO | scanner `--symbols` over `dstnso`/`5jsjnr`'s other named symbols: `REAL FORKS : 0`, all 17 sanctioned wrappers | The remainder of both backlog items is already done. |

## Proposed changes (ordered, validatable)

1. Baseline and a failing behavioral test (E-01, E-02).
2. Share the prompt by parameter (E-03), share the retry adapter on oc's body (E-04), delete dead host copies (E-05).
3. Re-measure and run the suite (E-06, E-07).

## Deferred / out of scope (with reason)

- The four recovery-routing/reconcile forks.
  - Carrier: cdxcbh
- `runner_shared._record_forced_stop`'s broken `git_status(repo)` fallback.
  - Carrier: afpmdu
- `reattempt_deferred_integrations`'s `validation_runner_for` parameter is accepted and never read in its body; removing it widens this chore into a signature change.
  - Carrier-Declined: harmless while unused; both hosts pass it identically after E-04, so it cannot drift.
- `disable_lane_prompt` remains an identical per-host pair.
  - Carrier-Declined: by design; it writes the per-host flag through `global`, and sharing it is the regression `runner_shared`'s docstring records.

## Scope check

- Over-scope: `runner_shared.py` is touched only to ADD `lane_reclaim_prompt` and `retry_deferred_integrations` and to correct the named docstrings/comments; host modules only in `_lane_reclaim_prompt`, `retry_deferred_integrations`, `_record_forced_stop`, the `reclaim_lanes_on_interrupt` docstring, and a now-unused `import select`.
- Under-scope: none; every divergent fork is accounted for in the Concern.

## Required tests / validation

New `tests/test_forkresid_shared_shells.py` (agy retry case fails before E-04); existing `FailClosedIntegrationGuardTests`, `AgyFailClosedIntegrationGuardTests` and `VerifierGateAndRunnerBugTests` as regressions; scanner re-run; bare suite.

## Spec / documentation sync

N/A: no spec describes these internal symbols; in-code docstrings are corrected by E-03.

## Open questions

### OQ-01: Should this plan be `Work-Kind: bug` with `Blocks-Release: next`, given F-1?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: F-1 is a user-perceptible defect on agy (a recoverable refusal goes terminal), and the repo rule is that a live bug gates the next release. The graduation instruction fixed `chore`, so this plan keeps it. Default: proceed as `chore`; the maintainer may reclassify with `aw ipd set` before approval.

### OQ-02: Is parameter injection an acceptable resolution of `8hx3g3`'s design act?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, from repo evidence. `8hx3g3` lists "pass suppression as a parameter" as an option; the declined alternative was a registration seam (process-global state), which this is not; and `runner_shared.reclaim_lanes_on_interrupt` already uses the injected-callable form for the same pair. The flag stays per host and is read at call time, so suppression semantics are unchanged, pinned by E-02(b).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `DIVERGENT FORKS (13)` block, the `--triples` block, the two closure blocks, and the grep output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_forkresid_shared_shells.py -o addopts=""` run BEFORE E-03..E-05, showing the agy `DeferredRetryUnmeasuredTests` case FAILING with `merge-refused` != `merge-unchecked` and every other case passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 tools/runner_fork_scan.py --symbols _lane_reclaim_prompt` showing `sanctioned thin wrappers   : 1` and `REAL FORKS                 : 0`; paste `git diff --stat`; paste `LanePromptSuppressionTests` passing on both hosts after the change.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 tools/runner_fork_scan.py --symbols retry_deferred_integrations` showing `REAL FORKS                 : 0`; paste the agy `DeferredRetryUnmeasuredTests` case now PASSING.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the re-run grep showing `def _record_forced_stop` only in `agent_workflows/runner_shared.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `DIVERGENT FORKS (10)` and its list, the `--triples` block without `_record_forced_stop`, and both pytest summary lines.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the `- Scope-Paths:` files via `aw commit 184tn9 -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. After every V item passes and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/`; the backlog items are closed as a separate records act.
