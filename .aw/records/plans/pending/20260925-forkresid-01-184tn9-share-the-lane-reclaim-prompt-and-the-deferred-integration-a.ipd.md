# IPD: Share the lane reclaim prompt and the deferred-integration adapter, and delete the dead host _record_forced_stop copies

- Date: 2026-09-25
- Kind: child
- Concern: THREE DIVERGENT RUNNER FORKS ARE OWNED BY NO PENDING PLAN, and one of them hides a live behavioral split. Re-measured at HEAD `8e74dcac` with `python3 tools/runner_fork_scan.py` (13 divergent forks). Of the 13, `recovone`/`cdxcbh` owns four (`classify_recovery_disposition`, `build_verify_and_continue_notice`, `reconcile_disposition`, `route_recovery_turn`); `handle_audit_command` is HOST-SPECIFIC-BY-CAPABILITY (research `fedqe6`); `execute_item`, `run_queue`, `initialize_run`, `main`, `build_parser` are the CORE-PLUS-HOOK host shells the maintainer chose 2026-09-14 (recorded by executed `40it5e`). That leaves exactly three unowned: (1) `_record_forced_stop` (backlog `dstnso`): BOTH host copies are DEAD, since `runner_shared.execute_item_core` calls the module-local `runner_shared._record_forced_stop` and nothing in the package or tests names the host copies; `liftaudit`/`afpmdu` edits only the shared copy and states "No host module is in scope". (2) `retry_deferred_integrations` (backlog `5jsjnr`): 46/46 lines at 0.998, but the one differing statement is NOT cosmetic. agy's `_integrate` passes `dict(item)` (a shallow copy) into `make_integration_validation_runner`, so `_record_revalidation` writes `post_merge_revalidation` onto the copy and `record_integration_refusal`'s `revalidation_was_unmeasured(item)` (the `l2mzxn` reclassification) cannot see it on agy's retry path; oc passes the live `item`. Probe: copy call leaves the live item with no record (`unmeasured: False`), live call gives `unmeasured: True`. So on agy a harness refusal during a deferred re-attempt is labeled `merge-refused` (terminal) instead of `merge-unchecked` (deferrable). (3) `_lane_reclaim_prompt` (backlog `8hx3g3`): 29/29 lines differing only in spelling (`print(file=...)` vs `print('', file=...)`, f-string vs `.format`), kept forked solely because it reads the per-host `_LANE_PROMPT_DISABLED`. Also covers `5jsjnr` (live residue: `retry_deferred_integrations`) and `8hx3g3`.
- Scope: IN: `runner_shared.lane_reclaim_prompt` taking suppression and timeout as PARAMETERS with each host's `_lane_reclaim_prompt` a one-statement delegation (the flag, `disable_lane_prompt` and `LANE_PROMPT_TIMEOUT` stay per host); `runner_shared.retry_deferred_integrations` on oc's body with host bindings injected, both hosts one-statement delegations; deleting both dead host `_record_forced_stop` definitions; one behavioral test module; correcting the docstrings that call `_lane_reclaim_prompt` "DIVERGED" or cite test files deleted in `19313eed`. OUT: the four `cdxcbh` symbols; `runner_shared._record_forced_stop` itself (`afpmdu`); the five host shells; `handle_audit_command`; `disable_lane_prompt` (stays per host by design); the unused `validation_runner_for` parameter of `runner_shared.reattempt_deferred_integrations`.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_forkresid_shared_shells.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Set: forkresid
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 184tn9
- From-Backlog: dstnso
- Blocks-Release: next

## Workflow history
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-609, all FIXED, no deferrals. F-1 REPRODUCES EXACTLY as authored and is the plan's real value: I drove both hosts' REAL `retry_deferred_integrations` with a fake `integrate_lane_branch` that calls the runner it is given, and oc recorded ladder kind `merge-unchecked` with `revalidation_was_unmeasured` True while agy recorded `fail-merge` and False. THE MATERIAL CORRECTIONS ARE ALL STALE-MEASUREMENT AND FIXTURE DEFECTS, not reasoning defects. (a) The census is 12 divergent, NOT 13: `reconcile_disposition` was de-forked by `6b94a4d9` ("statusvocab"), a DESCENDANT of the plan's cited HEAD `8e74dcac`, so E-01's `DIVERGENT FORKS (13)` gate and E-06's `(10)` are both RED ON ARRIVAL; corrected to re-derive rather than assert (PR-601). (b) V-02 asserts the agy kind is `merge-refused`, which is not a refusal KIND at all: `INTEGRATION_REFUSAL_CONFLICT` is `fail-merge` and `merge-refused` is a legacy STATUS spelling, so the validation would have failed on a correct measurement (PR-602). (c) E-02's fixture omits `position`/`setid`, and the real `save_state` -> `write_report` raises `KeyError: 'position'` before any assertion is reached - measured (PR-603). (d) E-04's injected-parameter list omits `save_state`, a free name in the body that is per-host by construction (each closes over its own `write_report`), so the lift as specified cannot resolve it (PR-604). (e) E-05 must record that approved sibling `afpmdu` E-03 misattributes these deletions to `recovone`, which puts them OUT of scope, so this plan is the correct and only owner (PR-605). Also: E-03 must delete the now-unused `import select` from BOTH hosts or `ruff` (pre-commit, fail-closed) rejects the commit (PR-606); OQ-01 contradicted its own front matter twice and owed a typed carrier (PR-607); `aw check plans` reports an `error` on this plan today (PR-607); and the gate was missing most of its required elements (PR-609).
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog dstnso, 5jsjnr, 8hx3g3; re-ran runner_fork_scan (default, --closure, --triples) at HEAD 8e74dcac, confirmed 13 divergent forks of which exactly three (_record_forced_stop host copies, retry_deferred_integrations, _lane_reclaim_prompt) are owned by no pending plan and are not intended host shells, and probed the agy dict(item) copy losing the revalidation record.

## Goal

Fix agy's deferred re-attempt mislabeling an unmeasured refusal as a terminal merge refusal, and reduce the runner fork census by the three divergent forks that are owned by no pending plan, leaving every remaining one owned by a pending plan (`cdxcbh`), recorded host-specific (`handle_audit_command`), or an intended host shell. The census FIGURE is re-derived at execution rather than asserted: it was 13 at authoring, is 12 at review (`reconcile_disposition` de-forked by `6b94a4d9`, a descendant of the cited HEAD), and the tree is live.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and failing test

- [ ] E-01 Record the baseline by RE-DERIVING it, not by matching an authored number: run `python3 tools/runner_fork_scan.py`, `python3 tools/runner_fork_scan.py --triples`, `python3 tools/runner_fork_scan.py --closure --symbols _lane_reclaim_prompt retry_deferred_integrations`, and `grep -rn "_record_forced_stop" agent_workflows/ tests/ --include=*.py`. THE CENSUS COUNT IS A LIVE-ARTIFACT MEASUREMENT AND MUST NOT BE ASSERTED AS A CONSTANT. It was 13 when this plan was authored at HEAD `8e74dcac` and was 12 at review: `reconcile_disposition` was single-sourced by commit `6b94a4d9` ("statusvocab: rename the terminal status vocabulary..."), which is a DESCENDANT of the cited HEAD, so the authored 13 was already stale before review. Record whatever number the scanner prints and the three target names' presence; do not treat a differing count as a failure. What this item MUST establish is the three PROPERTIES the plan depends on: `_lane_reclaim_prompt`, `retry_deferred_integrations` and `_record_forced_stop` are each listed under `DIVERGENT FORKS`; `--triples` lists `_record_forced_stop`; and the grep shows the only CALLS of `_record_forced_stop` are inside `runner_shared.py` (both in `execute_item_core`), with the two host hits being bare `def` lines and no call anywhere in `tests/`.
  - Depends on: none
  - Expected outcome: the three target names present under `DIVERGENT FORKS`, `--triples` lists `_record_forced_stop`, and the grep shows zero host or test CALLERS. The printed count is recorded, not asserted.
  - Execution state: pending

- [ ] E-02 Add `tests/test_forkresid_shared_shells.py` with, for EACH host (`oc_runipd`, `agy_runipd`, parameterized by subTest or two methods): (a) `DeferredRetryUnmeasuredTests`: build a tiny real git repo (`git init`, test identity, one commit, `git branch aw/lane/fr0001`), a state with `options={"validate": False, "integration_retry_limit": 10, "on_integration_blocked": "defer"}` and one queue item carrying `{"id6": "fr0001", "status": runner_shared.INTEGRATION_DEFERRED_STATUS, "preserved_branch": "aw/lane/fr0001", "preserved_worktree": "", "attempts": [{}]}` (no `preserved_base`, so the validation runner refuses UNMEASURED on unresolved base/head without running a suite); patch `<host>.integrate_lane_branch` with a fake that CALLS the runner it is given (`ok = runner("", [])`) and returns `(ok, "gate refused", runner_shared.INTEGRATION_REFUSAL_CONFLICT)`; call `<host>.retry_deferred_integrations(run_dir, state)`; assert `item["integration_ladder"]["kind"] == runner_shared.INTEGRATION_REFUSAL_UNMEASURED` and `runner_shared.revalidation_was_unmeasured(item)` is True.
  THE ITEM AND STATE MUST ALSO CARRY THE KEYS `write_report` READS, or the test dies before any assertion. Measured at review: with only the keys listed above, `record_integration_refusal` -> host `save_state` -> `runner_shared.save_state` -> per-host `write_report` -> `runner_shared.write_report` raises `KeyError: 'position'` from the summary-table row builder. The minimum that ran clean at review adds `"position": 1`, `"setid": "fr"`, `"action": "execute"` and `"file": "x.ipd.md"` to the ITEM and `"run_id"`/`"host"` to the STATE. Derive the real minimum by running it rather than copying this list, and prefer reusing an existing fixture's item shape (the neighbouring runner tests' `_state_and_item` shape) over hand-building one, so a future `write_report` field does not break this test alone.
  (b) `LanePromptSuppressionTests`: with `sys.stdin`/`sys.stderr` patched to TTY stubs whose `readline` returns `"d\n"` and `select.select` patched to report ready, `<host>._lane_reclaim_prompt({"holds_work": True, "lane_id": "x", "branch": "b"}, "keep")` returns `"discard"`; after `<host>.disable_lane_prompt()` (inside `mock.patch.object(<host>, "_LANE_PROMPT_DISABLED", False)` so the flag is restored) it returns `None`; and a non-TTY stdin returns `None`. PATCH `select.select` ON THE STDLIB `select` MODULE OBJECT (`mock.patch("select.select", ...)`), not on the host module's attribute: today both hosts do `import select` and call `select.select(...)`, and after E-03 the call moves into `runner_shared` behind a lazy `import select`, so only a patch on the stdlib module reaches both. Run the whole file BEFORE any code change.
  - Depends on: E-01
  - Expected outcome: before the fix, the agy case of (a) FAILS while the oc case passes; all (b) cases pass on both hosts (they pin behavior E-03 must preserve). The agy failure's observed kind is `fail-merge` (see V-02); do not expect `merge-refused`.
  - Execution state: pending

### Task group 2: the three lifts

- [ ] E-03 Share `_lane_reclaim_prompt`. Add `runner_shared.lane_reclaim_prompt(lane: dict[str, Any], default_action: str, *, disabled: bool, timeout: float) -> str | None` carrying oc's body verbatim except that `if _LANE_PROMPT_DISABLED:` becomes `if disabled:` and `LANE_PROMPT_TIMEOUT` becomes `timeout`; import `select` lazily inside the function. Both keyword-only parameters have NO default, so a caller cannot silently skip suppression. Replace each host's `_lane_reclaim_prompt` body with the single statement `return runner_shared.lane_reclaim_prompt(lane, default_action, disabled=_LANE_PROMPT_DISABLED, timeout=LANE_PROMPT_TIMEOUT)`, which reads the host's OWN flag at CALL time, so `disable_lane_prompt`'s `global` write is still honored and the per-host flag is unchanged. Keep `_LANE_PROMPT_DISABLED`, `disable_lane_prompt` and `LANE_PROMPT_TIMEOUT` in each host; drop the host's top-level `import select` only if nothing else in that module uses it. Correct the prose that is now false: the `runner_shared` module docstring bullet and the `# ---- lanes` banner comment that call the reader "DIVERGED, so it stays behind", and the `reclaim_lanes_on_interrupt` docstrings in all three modules that cite `UnmovableSymbolTests`/`tests/test_hostdedup_identical_lift.py` (both removed by `19313eed`); point them at `tests/test_forkresid_shared_shells.py::LanePromptSuppressionTests`.
  - Depends on: E-02
  DELETE THE NOW-UNUSED `import select` FROM BOTH HOSTS, and treat this as required rather than tidy. Verified at review: `select.` appears on exactly ONE line in each host (`oc_runipd.py` and `agy_runipd.py`, both the `select.select(...)` inside `_lane_reclaim_prompt`), so after this item the top-level `import select` is unused in both. `ruff` runs in this repository's pre-commit hooks and is FAIL-CLOSED, so leaving the import makes the commit be REJECTED (F-6), not merely untidy. Re-derive the "nothing else uses it" fact with a grep rather than trusting this sentence.
  - Expected outcome: one body for the prompt; host `_lane_reclaim_prompt` is a sanctioned thin wrapper; `tests/test_oc_runipd.py`'s `mock.patch.object(driver, "_lane_reclaim_prompt", ...)` still takes effect because the host wrapper keeps that NAME and `reclaim_lanes_on_interrupt` passes it as `lane_prompt=_lane_reclaim_prompt`, resolved when the wrapper runs; `ruff` clean on both hosts.
  - Execution state: pending

- [ ] E-04 Share `retry_deferred_integrations`. Add `runner_shared.retry_deferred_integrations(run_dir, state, *, poll, ask, integrate_lane_branch, integrate_review_lane_branch, make_validation_runner, run_suite_check, process_backlog_close, save_state)` carrying oc's body (`_handle_for`, `_integrate`, `_finish`, `_integrate_review`, `_finish_review`, and the `reattempt_deferred_integrations(...)` call), with `_integrate` passing the LIVE `item` (oc's form, which is the fix) and every host-bound name taken from the injected parameters rather than module globals.
  `save_state` IS IN THAT LIST DELIBERATELY AND WAS MISSING FROM THIS ITEM AS AUTHORED (F-7). It is a FREE NAME in oc's body (measured by an AST walk at review, alongside `integrate_lane_branch`, `integrate_review_lane_branch`, `make_integration_validation_runner`, `run_suite_check`, `process_backlog_close`, `lane_containment`, `worktree_lease`, `resolve_plan_path`, `runner_shared`) and it is per-host BY CONSTRUCTION: each host's `save_state` is `runner_shared.save_state(run_dir, state, write_report=write_report)` closing over its OWN `write_report`, so the shared module's own `save_state` is NOT a substitute (it requires the keyword and would raise `TypeError`). The `reconcile_interrupted`/`record_integration_refusal` precedent already injects it exactly this way. Before writing the signature, re-derive the free-name set with an AST walk and inject every host-bound one; `lane_containment`, `worktree_lease`, `resolve_plan_path`, `Palette`/`should_color` and `utc_now`/`append_jsonl`/`_run_git`/`DriverError` are all reachable inside `runner_shared` already (the scanner's `--closure` marks only `integrate_review_lane_branch`, `lane_containment` and `runner_shared` as ABSENT-FROM-SHARED, and `lane_containment` is imported function-locally in ten existing places there), so those need no injection.
  Keep `validation_runner_for=lambda item: make_validation_runner(state, run_dir, dict(item), suite_check=run_suite_check)` EXACTLY as today, `dict(item)` included. That copy is DELIBERATE and documented: `runner_shared.attributed_away_failure_ids` states "Both hosts' deferral re-attempt lambdas pass `dict(item)` - a SHALLOW COPY - into `validation_runner_for`, so a READ of the answer record works there while any WRITE would land on the copy and be lost", which is why that reader is read-only. It is also INERT, because `reattempt_deferred_integrations` accepts `validation_runner_for` and never reads it (AST walk at review: zero Name loads in the body). The defect F-1 names is the OTHER call, inside `_integrate`, and only that one changes.
  Replace each host's body with one statement: `return runner_shared.retry_deferred_integrations(run_dir, state, poll=poll, ask=ask, integrate_lane_branch=integrate_lane_branch, integrate_review_lane_branch=integrate_review_lane_branch, make_validation_runner=make_integration_validation_runner, run_suite_check=run_suite_check, process_backlog_close=process_backlog_close, save_state=save_state)`, resolving each name from the host module at call time so existing `mock.patch.object(<host>, ...)` seams keep working. Keep the host docstrings short and pointing at the shared one.
  - Depends on: E-02
  - Expected outcome: one body; both hosts sanctioned thin wrappers; agy now records revalidation on the live item.
  - Execution state: pending

- [ ] E-05 Delete the two DEAD host definitions `oc_runipd._record_forced_stop` and `agy_runipd._record_forced_stop`. Re-run the E-01 grep first; if any caller outside `runner_shared.py` has appeared, STOP and report rather than deleting. Do not touch `runner_shared._record_forced_stop` (owned by `afpmdu`).
  THIS PLAN IS THE CORRECT AND ONLY OWNER, and the executor must know why, because an APPROVED sibling says otherwise. `afpmdu` E-03 instructs "DO NOT delete or convert those copies here", correctly excluding them from its own scope, but attributes them to "`recovone` (`cdxcbh`) already names `_record_forced_stop` in its OUT list" - and an OUT list is a DISCLAIMER, not ownership. Verified at review: `cdxcbh`'s Scope OUT clause reads "`_record_forced_stop`/`_lane_reclaim_prompt`/`disable_lane_prompt` (other residue named by the scanner)" and its Deferred section repeats it, so `cdxcbh` explicitly does NOT own them. `afpmdu`'s own F-15 independently measured the same facts this item relies on (both copies hold a full second body, neither is reachable because `execute_item_core` calls the bare name which is absent from its `getattr(driver_module, ...)` rebinding set). So the deletion is unclaimed by any other plan and belongs here; do not defer it to `cdxcbh` on the strength of `afpmdu`'s sentence.
  - Depends on: E-01
  - Expected outcome: `_record_forced_stop` is defined once, in `runner_shared`; no host references it.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Re-run the scanner and the new tests plus the existing retry and lane-reclaim regressions: `python3 tools/runner_fork_scan.py`, `python3 tools/runner_fork_scan.py --triples`, `python3 -m pytest tests/test_forkresid_shared_shells.py -o addopts=""`, and `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -k "FailClosedIntegrationGuard or VerifierGateAndRunnerBug" -o addopts=""`. Before relying on the `-k` selection, CONFIRM IT SELECTS SOMETHING: a `-k` expression matching zero tests exits 5 and reports no failures, which reads as a pass. Paste the collected count.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the census DECREASED BY EXACTLY THREE from E-01's recorded number (12 -> 9 at review's baseline; assert the DELTA and the three names' ABSENCE, never a literal total, since the tree is live and the authored 13 was already stale - see E-01); `--triples` no longer lists `_record_forced_stop`; all new tests pass on both hosts; the existing classes pass with a non-zero collected count.
  - Execution state: pending

- [ ] E-07 Confirm the pre-commit gate the lift can trip: run `ruff check agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py` (and `ruff format --check` on the same three). This is separate from the suite because `ruff` is a fail-closed pre-commit hook here and an unused `import select` left by E-03 makes the COMMIT fail rather than a test (F-6); finding that at commit time wastes a round trip.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: `ruff` reports no findings on the three files.
  - Execution state: pending

- [ ] E-08 Run the bare suite: `python3 -m pytest`.
  - Depends on: E-06, E-07
  - Expected outcome: green summary line, or any failure shown to fail identically on the pre-change tree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Sanctioned de-duplicated form: `runner_shared` owns the body taking outside dependencies as parameters; each host keeps a one-statement delegation (`818uru` OQ-02 ruling; `tools/runner_fork_scan.py::is_pure_delegation`). `reclaim_lanes_on_interrupt` (`gqo6if` E-03) already injects `lane_prompt=`/`disable_prompt=` the same way.
- `runner_shared` forbids module-level mutable state and a registration seam was declined (its module docstring), so the flag must stay per host; passing it as a parameter satisfies both.
- Change-detector tests over code text were retired (`d4dd6b88`, and the trim `19313eed`); new tests here are behavioral. Fork counts are evidenced with the committed scanner, not a new test.
- THE FORK CENSUS IS A LIVE POPULATION, not a code constant: it was 13 at this plan's authoring HEAD `8e74dcac` and 12 at review, because `6b94a4d9` ("statusvocab") single-sourced `reconcile_disposition` in between. Assert the DELTA and the named symbols' absence; never a literal total.
- The refusal KIND vocabulary and the item STATUS vocabulary are different namespaces that share spellings: `INTEGRATION_REFUSAL_CONFLICT` is `fail-merge`, `INTEGRATION_REFUSAL_UNMEASURED` is `merge-unchecked`, `INTEGRATION_REFUSAL_TRANSIENT` is `merge-retry`, and `INTEGRATION_BLOCKED_STATUS`/`INTEGRATION_DEFERRED_STATUS` are `fail-merge`/`merge-retry`. `merge-refused` is a LEGACY status spelling kept only for reading pre-rename run directories (`l2mzxn` renamed all four) and is NOT a refusal kind. Compare against the CONSTANTS, never a literal.
- Any test that reaches a host `save_state` also reaches that host's `write_report` and therefore `runner_shared.write_report`, which indexes `item['position']`, `item['setid']` and the action. A minimal hand-built queue item raises `KeyError` there before any assertion runs (measured at review).
- `ruff` runs as a FAIL-CLOSED pre-commit hook in this repository, so an unused import left by a lift makes the COMMIT fail, not a test.
- An OPEN or DEFERRED open question owes a TYPED durable carrier (`- Carrier:` / `- Carrier-Evidence:` / `- Carrier-Declined:`, `ipd_schema.CARRIER_FIELDS`); prose naming an item satisfies nothing (`check_engine.evaluate_carrier_obligation`).
- An OUT-of-scope clause in another plan is a DISCLAIMER, not an assignment of ownership. `afpmdu` points these deletions at `cdxcbh`, whose own OUT clause disclaims them, which is how this residue came to look owned while being unclaimed.
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-1 | HIGH | agy `retry_deferred_integrations._integrate`: `make_integration_validation_runner(state, run_dir, dict(item), ...)`; oc passes `item`; probe under `/tmp/opencode/g3/probe-forkresid/p.py` printed `copy call -> False live has record: False unmeasured: False` then `live call -> False live has record: True unmeasured: True` | agy's deferred re-attempt cannot apply the `l2mzxn` unmeasured reclassification in `record_integration_refusal`. |
| F-2 | MEDIUM | `grep -rn _record_forced_stop`: calls only at `runner_shared.execute_item_core` (`record = _record_forced_stop(`), plus host `def`s; `afpmdu` Scope-check: "No host module is in scope" | Host copies are dead code and a three-way fork (`--triples`). |
| F-3 | MEDIUM | `--closure`: `_lane_reclaim_prompt` closes over `LANE_PROMPT_TIMEOUT`, `_LANE_PROMPT_DISABLED`, `select`; AST diff is 4 spelling-only lines | Parameter injection removes the only reason it stayed forked. |
| F-4 | LOW | `grep -rn UnmovableSymbolTests tests/` finds only a comment; `tests/test_hostdedup_identical_lift.py`, `tests/test_runner_refork_guard.py` absent (deleted `19313eed`) | Docstrings cite pins that no longer exist. |
| F-5 | INFO | scanner `--symbols` over `dstnso`/`5jsjnr`'s other named symbols: `REAL FORKS : 0`, all 17 sanctioned wrappers | The remainder of both backlog items is already done. |
| F-6 | MEDIUM (added at review) | `grep -n "select\." agent_workflows/oc_runipd.py` and the agy twin each return EXACTLY ONE line, the `select.select(...)` inside `_lane_reclaim_prompt`; `ruff` is a pre-commit hook in this repository and is fail-closed | AFTER E-03 THE TOP-LEVEL `import select` IS UNUSED IN BOTH HOSTS, and leaving it makes the COMMIT be rejected by `ruff` rather than making a test fail. E-03 as authored said to drop it "only if nothing else in that module uses it", which is correct but left the check optional and stated no consequence; the consequence is a wasted commit round trip on a plan whose whole diff is a lift. Now required, with E-07 checking `ruff` explicitly before the commit. |
| F-7 | MEDIUM (added at review) | AST walk of `oc_runipd.retry_deferred_integrations` at review: FREE NAMES include `save_state` alongside `integrate_lane_branch`, `integrate_review_lane_branch`, `make_integration_validation_runner`, `run_suite_check`, `process_backlog_close`, `lane_containment`, `worktree_lease`, `resolve_plan_path`, `runner_shared`. `oc_runipd.save_state` and `agy_runipd.save_state` are each `runner_shared.save_state(run_dir, state, write_report=write_report)` closing over a per-host `write_report`; `runner_shared.save_state` requires `write_report` as a keyword | E-04'S INJECTED-PARAMETER LIST OMITTED `save_state`, so the lift as specified could not resolve it. `_finish` and `_finish_review` both call it, and the shared module's own `save_state` is not a substitute (it would raise `TypeError` for the missing keyword). Silent fallback is not possible here, which is the one mercy: it fails loudly at first call. Added to E-04's signature with the per-host reason and the `reconcile_interrupted` precedent. |
| F-8 | MEDIUM (added at review) | Measured at review by driving both hosts' real `retry_deferred_integrations`: `oc: ladder kind = 'merge-unchecked'` / `unmeasured = True`; `agy: ladder kind = 'fail-merge'` / `unmeasured = False`. `INTEGRATION_REFUSAL_CONFLICT = "fail-merge"`; `merge-refused` appears only in legacy-status allowlists (`oc_runipd.py`, `agy_runipd.py`, `attention.py`, `render_stream.py`) | V-02 ASSERTED THE WRONG FAILURE STRING. It required the agy case fail "with `merge-refused` != `merge-unchecked`", but `merge-refused` is not a refusal KIND at all: it is a legacy STATUS spelling retained for reading pre-rename run directories. The observed kind is `fail-merge`. An executor checking V-02 literally would see a mismatch on a CORRECT measurement and could plausibly "fix" the test toward a string the code never produces. |
| F-9 | LOW (added at review) | `cdxcbh` Scope OUT: "`_record_forced_stop`/`_lane_reclaim_prompt`/`disable_lane_prompt` (other residue named by the scanner)", repeated in its Deferred section; `afpmdu` E-03: "DO NOT delete or convert those copies here ... `recovone` (`cdxcbh`) already names `_record_forced_stop` in its OUT list"; both plans are `approved` | AN APPROVED SIBLING POINTS THIS WORK AT A PLAN THAT DISCLAIMS IT. `afpmdu` correctly excludes the host copies from its own scope but reads `cdxcbh`'s OUT list as ownership, when an OUT list is a disclaimer. So an executor reading `afpmdu` could defer E-05 to `cdxcbh`, which will never do it, and the residue would survive both plans. This plan is the only owner; E-05 now says so with both citations. |
| F-10 | LOW (added at review) | `evaluate_durable_carrier` on this plan at review: one `error`-severity drift, "OQ-01 records an outstanding obligation with NO durable carrier"; OQ-01's own text says "proceed as `chore`" while front matter carries `- Work-Kind: bug` and `- Blocks-Release: next`; source item `5jsjnr` is `- Work-Kind: bug` with `- Blocks-Release: next` | OQ-01 CONTRADICTED ITS OWN FRONT MATTER AND FAILED A GATE. It asked whether the plan should be `bug`/`Blocks-Release`, then said the graduation "fixed `chore`" and to "proceed as `chore`", while the front matter already carries `bug` + `Blocks-Release: next` - correctly INHERITED from source item `5jsjnr`, which carries both. So the question was already answered by the artifact it was written on, and the classification is right for a reason the question denied. It also owed a typed carrier, making `aw check plans` report an `error` on this plan and blocking `aw ipd lint --phase pre-transition`. |

## Proposed changes (ordered, validatable)

1. Baseline RE-DERIVED and a failing behavioral test (E-01, E-02).
2. Share the prompt by parameter and drop the dead `import select` (E-03), share the retry adapter on oc's body with `save_state` injected (E-04), delete the two unclaimed dead host copies (E-05).
3. Re-measure the census as a DELTA, run `ruff`, run the suite (E-06, E-07, E-08).

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

- Over-scope: `runner_shared.py` is touched only to ADD `lane_reclaim_prompt` and `retry_deferred_integrations` and to correct the named docstrings/comments; host modules only in `_lane_reclaim_prompt`, `retry_deferred_integrations`, `_record_forced_stop`, the `reclaim_lanes_on_interrupt` docstring, and the now-unused `import select`.
- Under-scope: none. Every divergent fork is accounted for in the Concern, with the census figure corrected at review from 13 to 12 (`reconcile_disposition` de-forked by `6b94a4d9`) and E-01/E-06 rewritten to measure a delta rather than assert a total.
- CONCURRENCY WITH APPROVED SIBLINGS, stated because three approved plans declare `agent_workflows/runner_shared.py`: `cdxcbh` (the four recovery/reconcile symbols), `afpmdu` (`execute_item_core`'s two spawn-path stop handlers and the shared `_record_forced_stop` fallback) and `87jnym` (`reconcile_item_on_interrupt`; verified at review to name none of this plan's three symbols). NO SYMBOL OVERLAPS, which is what matters: file overlap is not a hazard because `aw oc run`/`aw agy run` isolate each item in its own worktree and merge through the revalidate gate. The one real interaction is documentary and is handled in E-05 (F-9).

## Required tests / validation

New `tests/test_forkresid_shared_shells.py` (agy retry case fails before E-04, with the observed kind `fail-merge` and not `merge-refused`); existing `FailClosedIntegrationGuardTests`, `AgyFailClosedIntegrationGuardTests` and `VerifierGateAndRunnerBugTests` as regressions, with their collected count shown to be non-zero; scanner re-run as a DELTA; `ruff` on the three edited modules; bare suite.

## Spec / documentation sync

N/A: no spec describes these internal symbols; in-code docstrings are corrected by E-03.

## Open questions

### OQ-01: Should this plan be `Work-Kind: bug` with `Blocks-Release: next`, given F-1?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, and the artifact already says so; the question was self-contradictory as authored (F-10) and is resolved from repository evidence rather than left for the maintainer. This plan's front matter carries `- Work-Kind: bug` and `- Blocks-Release: next`, correctly INHERITED from source backlog item `5jsjnr`, which itself carries `- Work-Kind: bug` and `- Blocks-Release: next`; AGENTS.md's inheritance obligation makes carrying them mandatory, not optional. The original rationale then said the graduation "fixed `chore`" and to "proceed as `chore`", which contradicts the front matter twice and would invite an executor or approver to DOWNGRADE a correctly gated plan. The substantive test is also met independently: F-1 reproduces measurably (a recoverable harness refusal is labelled terminal on agy, so a lane an operator could recover is reported as needing a human), which is user-perceptible impact, and the repository rule is that a live bug gates the next release. Nothing here needs a maintainer decision; a maintainer who disagrees can still de-gate with `aw ipd set ... --blocks-release -`.
  - Carrier-Declined: Resolved, not deferred: the classification is already correct on this artifact and inherited from a gating source item, so there is no outstanding obligation for a carrier to hold. The release gate itself is carried structurally by `- Blocks-Release: next`, which `aw check release-gates` reads.

### OQ-02: Is parameter injection an acceptable resolution of `8hx3g3`'s design act?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, from repo evidence. `8hx3g3` lists "pass suppression as a parameter" as an option; the declined alternative was a registration seam (process-global state), which this is not; and `runner_shared.reclaim_lanes_on_interrupt` already uses the injected-callable form for the same pair. The flag stays per host and is read at call time, so suppression semantics are unchanged, pinned by E-02(b).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the whole `DIVERGENT FORKS` block WITH its printed count, the `--triples` block, the closure block, and the grep output. State the count as OBSERVED and do not compare it to 13 (see E-01: the tree is live and 13 was already stale at review, where it measured 12). The pass condition is the three PROPERTIES: all three target names appear under `DIVERGENT FORKS`, `--triples` lists `_record_forced_stop`, and the grep shows no CALL of `_record_forced_stop` outside `runner_shared.py` and none in `tests/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_forkresid_shared_shells.py -o addopts=""` run BEFORE E-03..E-05, showing the agy `DeferredRetryUnmeasuredTests` case FAILING and every other case passing. THE FAILURE MUST BE THE RIGHT ONE, and two wrong ones are specifically excluded. (a) The observed ladder kind must be `fail-merge`, which is `INTEGRATION_REFUSAL_CONFLICT`; `merge-refused` is a legacy STATUS spelling and is not a refusal kind, so a diff naming it means the assertion was written against a string the code never produces (F-8). Assert against the CONSTANTS. (b) A `KeyError: 'position'` (or any other missing-key error from `runner_shared.write_report`) is a FIXTURE defect, not the defect under test; if it appears, complete the item's keys and re-run before recording this evidence (F-3 measurement in E-02).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 tools/runner_fork_scan.py --symbols _lane_reclaim_prompt` showing `sanctioned thin wrappers   : 1` and `REAL FORKS                 : 0` (at review this same command reported `0` and `1` respectively, so the flip is the proof); paste `git diff --stat`; paste `LanePromptSuppressionTests` passing on both hosts AFTER the change, which is what proves suppression still reads each host's own flag; and paste `grep -n "^import select" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returning nothing, plus `ruff check` clean on both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 tools/runner_fork_scan.py --symbols retry_deferred_integrations` showing `REAL FORKS                 : 0`; paste the agy `DeferredRetryUnmeasuredTests` case now PASSING; and paste the shared function's SIGNATURE (e.g. `python3 -c "import inspect, agent_workflows.runner_shared as R; print(inspect.signature(R.retry_deferred_integrations))"`) showing `save_state` is a parameter, since its omission was the authored defect (F-7). Also state explicitly that the `validation_runner_for=` lambda still passes `dict(item)`, unchanged and deliberate.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the re-run grep showing `def _record_forced_stop` only in `agent_workflows/runner_shared.py`, and paste the grep for CALL sites showing both remaining ones are inside `execute_item_core`. A `def`-only grep cannot distinguish "deleted the dead copies" from "deleted a live one", so both halves are required.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `DIVERGENT FORKS` block with its count, and state the DELTA against V-01's recorded number: it must be exactly minus three, with `_lane_reclaim_prompt`, `retry_deferred_integrations` and `_record_forced_stop` all ABSENT from the list. Do not assert a literal total. Paste the `--triples` block without `_record_forced_stop`, and both pytest summary lines INCLUDING the collected counts, so a `-k` expression that selected nothing (exit 5, which reads as a pass) is visible.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `ruff check` and `ruff format --check` output for `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py` and `agent_workflows/runner_shared.py`, showing no findings.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. One behavioral fix plus three de-duplications. THE BEHAVIORAL FIX (E-04) is the reason this plan is `Work-Kind: bug` with `Blocks-Release: next`: on `aw agy run`, a deferred integration re-attempt whose post-merge revalidation could not MEASURE is currently labelled `fail-merge` (terminal) instead of `merge-unchecked` (deferrable), so a lane an operator could recover is reported as needing a human. Measured at review by driving both hosts' real `retry_deferred_integrations`. The oc host is already correct and does not change. THE THREE LIFTS are behavior-preserving by construction (one shared body, per-host wrappers keeping the original names and signatures), and the one with any risk is E-03, because prompt suppression depends on each host's `_LANE_PROMPT_DISABLED` being read at CALL time; E-02(b) pins that before the change and V-03 re-checks it after. E-05 deletes two functions that no code anywhere calls.

SCOPE FENCE, stated as a DECLARATION for reconciliation, not as a stop directive. `agent_workflows/runner_shared.py`: ADD `lane_reclaim_prompt` and `retry_deferred_integrations`, and correct the module-docstring bullet, the `# ---- lanes` banner comment and the `reclaim_lanes_on_interrupt` docstring where they call the prompt "DIVERGED" or cite `UnmovableSymbolTests` / `tests/test_hostdedup_identical_lift.py`. `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`: the bodies of `_lane_reclaim_prompt` and `retry_deferred_integrations`, the deletion of `_record_forced_stop` and of `import select`, and the `reclaim_lanes_on_interrupt` docstring. `tests/test_forkresid_shared_shells.py` is new. EXPLICITLY NOT IN SCOPE: the four `cdxcbh` symbols (`classify_recovery_disposition`, `build_verify_and_continue_notice`, `reconcile_disposition`, `route_recovery_turn`); `runner_shared._record_forced_stop` itself and `execute_item_core`'s stop handlers (`afpmdu`); `reconcile_item_on_interrupt` (`87jnym`); the five host shells (`execute_item`, `run_queue`, `initialize_run`, `main`, `build_parser`); `handle_audit_command`; `disable_lane_prompt`; `reattempt_deferred_integrations`'s unused `validation_runner_for` parameter; and the deliberate `dict(item)` in the `validation_runner_for` lambda. An out-of-scope edit is to be MADE and then JUSTIFIED through `aw ipd finalize --scope-reason`, never silently.

HARD MUST: paste the ACTUAL output for every `V-*`. Never claim a command passed without running it. Three claims are specifically easy to fake or to mis-certify and are named for that reason: V-02's failure STRING (assert the constants, since `merge-refused` is not a kind), V-06's `-k` selection (a zero-match `-k` exits 5 and reads as a pass, so paste the collected count), and V-01/V-06's census figures (a DELTA, never a literal total). Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

STOP AND REPORT, for a genuinely unsafe condition only: if the E-01 grep finds any CALLER of a host `_record_forced_stop` (E-05 already says this); if one of the three target symbols is no longer a divergent fork at execution time, which means a sibling landed it first and that part of the plan is spent rather than failed; or if `runner_shared` cannot resolve a free name E-04 did not anticipate and no injection precedent exists for it.

This plan is `reviewed` (review complete; NOT approved) and requires explicit human approval before execution. The executor commits only the `- Scope-Paths:` files via `aw commit 184tn9 -- <paths>`, never `git add -A`, and never pushes. LIFECYCLE TRANSITION: the plan reaches `executed/` only after every `V-*` carries concrete observed evidence and `aw ipd lint --phase pre-transition` conforms. Under `aw oc run` / `aw agy run` the RUNNER owns that transition and the executor must not hand-roll it; run by hand, the executor completes it with `aw ipd finalize` (never a hand-rolled `git mv`). The three backlog items (`dstnso`, `5jsjnr`, `8hx3g3`) are already `graduated`, so no close is owed here; `5jsjnr` carries the release gate this plan inherits, so that gate is discharged by this plan reaching `executed`, not by editing the item.
