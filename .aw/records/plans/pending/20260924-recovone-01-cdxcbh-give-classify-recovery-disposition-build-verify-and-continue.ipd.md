# IPD: Give classify_recovery_disposition, build_verify_and_continue_notice and reconcile_disposition one working definition each

- Date: 2026-09-24
- Kind: child
- Concern: TWO BACKLOG ITEMS, ONE DEFECT CLASS: A HOST COPY WINS OVER A SHARED COPY THAT IS DIFFERENT, AND THE DIFFERENCE IS A BUG ON ONE SIDE OR THE OTHER. Backlog `zt2b16` (`bug`, `Blocks-Release: next`): `runner_shared.classify_recovery_disposition` is DEAD ON ARRIVAL, it reads `st.path`/`st.base_commit` off a `worktree_lease.LaneState` whose real fields are `worktree_path`/`base_sha`, so it raises `AttributeError` on every lane that exists, and it also drops oc's `not st.exists` and `not st.head or not st.base_sha` guards and matches snapshots by the wrong prefix (`"wip(snapshot):"` where the real one is `worktree_lease.INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX`); only nobody calls it, because `oc_runipd` defines its own, `agy_runipd` delegates to oc's by lazy import, and `runner_shared.execute_item_core` rebinds `route_recovery_turn` off `driver_module`. Its siblings `build_verify_and_continue_notice` and `route_recovery_turn` are likewise three-way forked, and the shared `route_recovery_turn` is ALSO dead for a second, unfiled reason (F-4: it calls `runner_shared.save_state` without the required `write_report=` keyword, `TypeError` even with no lane). Backlog `2t4v1j` (`bug`, `Blocks-Release: next`), the same class inverted: `oc_runipd.reconcile_disposition` indexes `item["configured_file"]` and raises `KeyError` on an item without it, where `agy_runipd` and `runner_shared` use `item.get("configured_file", "")`; because `execute_item_core` binds `getattr(driver_module, "reconcile_disposition", ...)`, the BROKEN oc copy is what runs on the oc host, including from the `StopNowForce`/`StopAtCheckpoint` handlers, which turns an orderly operator stop into a `KeyError`. Both fixes are the same move: keep the WORKING body, make `runner_shared` hold the only definition, and make both hosts re-export (or, where a host-bound dependency forces it, thinly wrap) it.
- Scope: IN: (a) `runner_shared.classify_recovery_disposition` takes oc's body (real `LaneState` field names, the `exists`/`head`/`base_sha` guards, `worktree_lease.commit_subject_is_interrupted_snapshot`); oc's and agy's definitions are deleted and replaced by re-exports, together with oc's AST-identical duplicates `RecoveryDisposition`, `DISPOSITION_*`, `RECOVERY_DISPOSITIONS` and `_lane_commit_subjects`; (b) `build_verify_and_continue_notice` single-sourced the same way; (c) `runner_shared.route_recovery_turn` gains a keyword-only `save_state` injection (the `reconcile_interrupted` precedent) and both hosts become one-line wrappers, so `AGY_IMPORTS_FROM_OC_RUNIPD` loses its three recovery names; (d) `reconcile_disposition` single-sourced on the shared tolerant body, oc's and agy's definitions deleted and re-exported; (e) one new behavioral test module. OUT: any change to the routing POLICY (verify-and-continue vs fresh vs undetermined), to prompt text, or to `reconcile_disposition`'s precedence rungs; `record_item_spec_edits` (the fourth `AGY_IMPORTS_FROM_OC_RUNIPD` name, a different concern); `_record_forced_stop`/`_lane_reclaim_prompt`/`disable_lane_prompt` (other residue named by the scanner); closing the backlog items (a post-execution records act).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_recovone_single_definition.py
- Item-Dependencies: none
- Status: to-review
- Set: recovone
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: cdxcbh
- From-Backlog: zt2b16
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zt2b16 (also covering 2t4v1j); re-measured at HEAD 877545fc by calling every copy against a real `inspect_lane` LaneState and a configured_file-less item: shared classify raises AttributeError, oc reconcile raises KeyError, and shared route_recovery_turn is additionally dead via a save_state TypeError the backlog did not record.

## Goal

Each of `classify_recovery_disposition`, `build_verify_and_continue_notice` and `reconcile_disposition` has exactly ONE definition, in `runner_shared`, and it is the body that actually works; both hosts reach that one object, so neither the `AttributeError` (shared classifier) nor the `KeyError` (oc reconciler) can be reached from any entry point, and `route_recovery_turn` stops being a dead shared copy that a later consolidation would silently adopt.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the defects before touching them

- [ ] E-01 RE-MEASURE ALL FOUR FINDINGS AT YOUR HEAD, with a throwaway probe (not committed) that builds a temp git repo, cuts a lane branch named by `worktree_lease.lane_branch_name("abc123")` holding one ordinary commit, and calls each copy. Expected at authoring (HEAD `877545fc`): `worktree_lease.inspect_lane(...)` returns state `HOLDS-WORK`, `commits_ahead` 1, `hasattr(st, "path")` False; `oc_runipd.classify_recovery_disposition` and `agy_runipd.classify_recovery_disposition` both `verify-and-continue`; `runner_shared.classify_recovery_disposition` raises `AttributeError: 'LaneState' object has no attribute 'path'`; `runner_shared.route_recovery_turn(run_dir, {"repo": ...}, {"id6": "abc123"}, True)` raises `TypeError: save_state() missing 1 required keyword-only argument: 'write_report'` (F-4); with `item = {"id6": "abc123", "position": 1, "action": "execute"}`, `oc_runipd.reconcile_disposition(repo, item, run_dir, 0)` raises `KeyError: 'configured_file'` while agy and shared return `('partial', None)`. Also run `python3 tools/runner_fork_scan.py --triples` and record the `NEITHER-DELEGATES` row and the `reconcile_disposition` `BOTH-DELEGATE` row. If ANY of these no longer reproduces, STOP and report which, rather than proceeding on a stale premise.
  - Depends on: none
  - Expected outcome: every finding in the Findings table reproduced (or its drift reported) with pasted probe output and scanner rows.
  - Execution state: pending

- [ ] E-02 WRITE `tests/test_recovone_single_definition.py` FIRST, and show it RED against the unmodified tree. Four test classes, all behavioral except the identity pin: (1) a temp-repo fixture (git init, one base commit, lane branch from `worktree_lease.lane_branch_name`) and, for each host module in `(oc_runipd, agy_runipd)`, `classify_recovery_disposition(repo, item, state)` where `item` carries `preserved_lane_id`/`preserved_base` (the first rung of `runner_shared.resolve_prior_lane`), for three lane shapes: an ordinary commit -> `verify-and-continue` with `real_commits` naming it; a commit whose subject starts with `worktree_lease.INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX` -> `fresh-execution` with `snapshot_only` True; a recorded lane id whose branch does not exist -> `fresh-execution`; assert both hosts AND `runner_shared` return the same `disposition`, `snapshot_only` and `inspected_worktree`/`inspected_branch`, and never raise. The LaneState MUST come from the real `worktree_lease.inspect_lane`, not a hand-built stub; a stub is exactly how the wrong field names survived. (2) `route_recovery_turn(run_dir, state, item, True)` via each host with a real `run_dir`: returns a decision, writes `item["recovery_routing"]["disposition"]`, and `run_dir / "state.json"` exists afterwards (proves the `save_state` injection). (3) For each of `oc_runipd`, `agy_runipd`: `reconcile_disposition(repo, {"id6": "abc123", "position": 1, "action": "execute"}, run_dir, 0)` returns `("partial", None)` and with exit code 1 returns `("failed-safely", None)`, no `KeyError`. (4) Identity: for each name in `("classify_recovery_disposition", "build_verify_and_continue_notice", "reconcile_disposition")` and each host, `getattr(host, name) is getattr(runner_shared, name)`. Use `unittest.TestCase` like the neighbouring runner tests.
  - Depends on: E-01
  - Expected outcome: the module exists; run against the unmodified tree it FAILS (at least: shared-classifier cases raise `AttributeError`, oc reconcile raises `KeyError`, identity fails, shared route raises `TypeError`).
  - Execution state: pending

### Task group 2: single-source the recovery-routing trio

- [ ] E-03 SINGLE-SOURCE `classify_recovery_disposition` ON OC'S BODY. In `runner_shared`, replace the body of `classify_recovery_disposition` with `oc_runipd.classify_recovery_disposition`'s body verbatim, INCLUDING its docstring and its "DELIBERATELY BROAD" `except Exception` comment (reads `st.worktree_path`, `st.base_sha`, `st.head`, `st.exists`; filters with `worktree_lease.commit_subject_is_interrupted_snapshot`). The shared copy's `lane_branch_tip` call and `"wip(snapshot):"` prefix are DELETED, not merged: the prefix matches no snapshot the driver writes. Then delete oc's definition AND oc's AST-identical duplicates `DISPOSITION_FRESH_EXECUTION`, `DISPOSITION_VERIFY_AND_CONTINUE`, `DISPOSITION_UNDETERMINED`, `RECOVERY_DISPOSITIONS`, `RecoveryDisposition`, `_lane_commit_subjects` (verify AST equality first, measured True at authoring for the class and the helper), replacing them with `from agent_workflows.runner_shared import (X as X,)` re-exports in the established style (e.g. oc's existing `resolve_prior_lane as resolve_prior_lane`). In `agy_runipd`, delete the lazy-import delegator and re-export the same way. Keep oc's `route_recovery_turn` compiling until E-05 (it resolves the re-exported names).
  - Depends on: E-02
  - Expected outcome: exactly one `def classify_recovery_disposition` in `agent_workflows/` (in `runner_shared`), exactly one `class RecoveryDisposition`; E-02 class (1) passes on both hosts.
  - Execution state: pending

- [ ] E-04 SINGLE-SOURCE `build_verify_and_continue_notice`. Measured at authoring: for a `verify-and-continue` `RecoveryDisposition` with a dirty flag and one real commit, oc's and shared's outputs are byte-equal (`True`), the only AST differences being oc's direct attribute access versus shared's `getattr(..., default)`. Replace the shared body with oc's body and docstring (the one every production run has executed), annotate `decision: RecoveryDisposition`, delete oc's definition and agy's lazy delegator, and re-export in both hosts. The two host `build_prompt` wrappers pass `build_verify_and_continue_notice=build_verify_and_continue_notice`, which now names the shared object; leave those call sites as they are.
  - Depends on: E-03
  - Expected outcome: one `def build_verify_and_continue_notice` in `agent_workflows/`; identity assertion for it passes on both hosts.
  - Execution state: pending

- [ ] E-05 MAKE THE SHARED `route_recovery_turn` REACHABLE AND CORRECT, then make both hosts thin wrappers (F-4). A PURE RE-EXPORT IS NOT POSSIBLE here, which is why it is a wrapper and not in the identity pin: the body calls `save_state`, whose shared form requires the host-bound `write_report=` keyword. Follow the `runner_shared.reconcile_interrupted` precedent exactly: add a keyword-only `save_state: Callable[[Path, dict[str, Any]], None]` parameter to `runner_shared.route_recovery_turn`, carry oc's docstring into it, and replace `oc_runipd.route_recovery_turn` and `agy_runipd.route_recovery_turn` with one-line wrappers `return runner_shared.route_recovery_turn(run_dir, state, item, recovery, save_state=save_state)` keeping the original name and signature (so `execute_item_core`'s `getattr(driver_module, "route_recovery_turn", ...)` still resolves the host wrapper). Remove `build_verify_and_continue_notice`, `classify_recovery_disposition` and `route_recovery_turn` from `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD`, leaving `record_item_spec_edits`, and rewrite that constant's comment and the "runnerlayer Order 02 (`1f7xno`) TRIED TO CONSOLIDATE" paragraph above oc's former definition and agy's "resumedupe (`txc9l1`) E-04" comment so none of them still claims the consolidation is deferred. Confirm `grep -n "from agent_workflows.oc_runipd import" agent_workflows/agy_runipd.py` names none of the three.
  - Depends on: E-04
  - Expected outcome: E-02 class (2) passes on both hosts; `AGY_IMPORTS_FROM_OC_RUNIPD == frozenset({"record_item_spec_edits"})`; `tests/test_orchestrator_shape_gate.py` (asserts the oc-to-agy import count `<= 4`) still passes; no prose left asserting the three names are deferred.
  - Execution state: pending

### Task group 3: single-source reconcile_disposition

- [ ] E-06 SINGLE-SOURCE `reconcile_disposition` ON THE SHARED TOLERANT BODY (`2t4v1j`). The shared body already uses `item.get("configured_file", "")` in both places and routes through `read_recorded_outcome` and `outcome_precedence_disposition`, whose docstrings state they apply the same three rungs in the same order as the inlined host copies; the only other closure difference is `TERMINAL_STATES`, whose host and shared values are EQUAL (measured: symmetric difference `[]`). Before deleting anything, compare the three bodies once more with a docstring-stripped `ast.unparse` diff and paste it: at authoring oc-vs-agy differed ONLY in the two `configured_file` subscripts, and agy-vs-shared only in the helper extraction and the local `runner_stop`/`_read_status` imports. Carry oc's docstring and its "runstop foi1b3" deliberate-stop comment block into the shared definition (the shared copy has neither), then delete `oc_runipd.reconcile_disposition` and `agy_runipd.reconcile_disposition` and re-export the shared one in both. DO NOT convert this to a wrapper: nothing in it is host-bound, and a re-export is what lets the identity pin hold. KEEP THE `driver_module` REBINDING WORKING: `execute_item_core` reads `getattr(driver_module, "reconcile_disposition", globals().get(...))`, and `tests/test_defect_report.py` patches `mock.patch.object(oc_runipd, "reconcile_disposition", reconcile)`; because the name stays an attribute of `oc_runipd`, that patch still redirects the call. Prove it by running that module.
  - Depends on: E-02
  - Expected outcome: one `def reconcile_disposition` in `agent_workflows/`; E-02 classes (3) and the `reconcile_disposition` identity assertion pass; `tests/test_defect_report.py` and `tests/test_runner_shared.py` (whose deferral-passthrough case loops both hosts) pass unmodified.
  - Execution state: pending

### Task group 4: prove convergence

- [ ] E-07 PROVE CONVERGENCE WITH THE COMMITTED SCANNER AND THE TARGETED SUITES. Run `python3 tools/runner_fork_scan.py --triples` and show `classify_recovery_disposition`, `build_verify_and_continue_notice` and `reconcile_disposition` no longer appear as co-defined symbols (a re-export is not a definition), `route_recovery_turn` now classifies `BOTH-DELEGATE`, and the headline `co-defined in both runners` fell from the E-01 value by exactly three. Then run the targeted set: `python3 -m pytest tests/test_recovone_single_definition.py tests/test_oc_runipd.py tests/test_runner_shared.py tests/test_defect_report.py tests/test_orchestrator_shape_gate.py tests/test_hostdedup_third_host.py -o addopts="" -q`.
  - Depends on: E-05, E-06
  - Expected outcome: scanner rows as described; targeted suite all passed (pre-change baselines at authoring: `274 passed` for `test_oc_runipd.py test_runner_shared.py test_defect_report.py`, `23 passed` for `test_hostdedup_third_host.py test_orchestrator_shape_gate.py`).
  - Execution state: pending

- [ ] E-08 RUN THE BARE SUITE `python3 -m pytest` (no extra flags) and record its summary line.
  - Depends on: E-07
  - Expected outcome: no failures; any failure is triaged as caused-by-this-plan or pre-existing (reproduced on the unmodified tree) and reported, never absorbed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE LIFT PATTERN IS A RE-EXPORT, NOT A WRAPPER, WHEN NOTHING IS HOST-BOUND. Hosts import shared names one per statement as `from agent_workflows.runner_shared import (name as name,)` (e.g. `resolve_prior_lane` in both hosts), which is what makes `host.name is runner_shared.name` hold. A WRAPPER is reserved for a body with a host-bound dependency, injected by keyword (`runner_shared.reconcile_interrupted(run_dir, state, save_state=save_state)`, the `818uru` OQ-02 ruling).
- `execute_item_core` RESOLVES HOST SEAMS OFF `driver_module` FIRST (`getattr(driver_module, "reconcile_disposition", globals().get("reconcile_disposition"))`, same for `route_recovery_turn`). A shared definition that a host also defines is therefore DEAD, which is how both defects here hid; and a host attribute must remain present (as a re-export) for test patches on the host module to keep redirecting.
- `tools/runner_fork_scan.py` IS THE COMMITTED CONVERGENCE INSTRUMENT (`--triples`, `--closure`, `--symbols`). Its identity metric is docstring-stripped `ast.unparse` and it does NOT erase names, so READ `--closure` BEFORE LIFTING: that is what exposed `save_state` and the absent `runner_stop`/`_read_status` imports for these symbols.
- AN AST-IDENTICAL BODY IS ONLY SAFELY MOVABLE IF EVERYTHING IT RESOLVES IS ALSO SAFE (recorded in oc's paragraph above `route_recovery_turn` and in the `AGY_IMPORTS_FROM_OC_RUNIPD` comment). This plan's F-4 is a second instance of the same trap.
- THERE IS NO LONGER ANY RECOVERY-ROUTING TEST IN-TREE. `tests/test_resumedupe.py`, which the code comments and `zt2b16` cite, was deleted by commit `19313eed` ("trim test suite"). `grep` for `classify_recovery_disposition`/`route_recovery_turn`/`recovery_routing` in `tests/` finds nothing, so E-02 is the only coverage these paths will have; it must be behavioral.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All re-measured at HEAD `877545fc` (`git rev-parse --short HEAD`) with probes under `/tmp/opencode/probe-recovone/`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.classify_recovery_disposition` | DEAD ON ARRIVAL, confirmed: reads `st.path` and `st.base_commit`, which `worktree_lease.LaneState` does not have; also drops oc's `not st.exists` and `not st.head or not st.base_sha` guards, calls `lane_branch_tip` instead, and filters snapshots with `subj.startswith("wip(snapshot):")` where the driver writes `INTERRUPTED_SNAPSHOT_SUBJECT_PREFIX = "WIP INTERRUPTED SNAPSHOT (not finished work):"`. | probe on a real `inspect_lane` result: `LaneState: HOLDS-WORK 1 has path? False`; `oc verify-and-continue`; `agy verify-and-continue`; `shared RAISED AttributeError 'LaneState' object has no attribute 'path'`. `LaneState._fields` has `worktree_path`, `base_sha`, no `path`/`base_commit`. |
| F-2 | MED | `build_verify_and_continue_notice` (oc, shared; agy delegates to oc) | Three-way fork, but the two real bodies are behavior-equivalent: they differ only in direct attribute access vs `getattr(..., default)`. | docstring-stripped AST: `oc==rs: False`; output probe on a dirty verify-and-continue `RecoveryDisposition`: byte-equal `True` |
| F-3 | HIGH | `oc_runipd.reconcile_disposition` (`2t4v1j`) | Confirmed: indexes `item["configured_file"]` twice; agy and shared use `.get(..., "")`. Because `execute_item_core` binds `getattr(driver_module, "reconcile_disposition", ...)`, the oc copy is what runs on the oc host, including the `except runner_stop.StopNowForce` / `except runner_stop.StopAtCheckpoint` handlers (`item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` then `raise`). The shared copy is unreachable. | probe with `{'id6':'abc123','position':1,'action':'execute'}`: `oc RAISED KeyError 'configured_file'`, `agy ('partial', None)`, `shared ('partial', None)`; AST diff oc-vs-agy is exactly the two subscripts |
| F-4 | HIGH | `runner_shared.route_recovery_turn` | NOT IN EITHER BACKLOG ITEM: the shared copy is dead for a SECOND reason independent of F-1. It calls `save_state(run_dir, state)` but `runner_shared.save_state` requires keyword-only `write_report`, so it raises before reaching the classifier. It is AST-identical to oc's (`oc==rs: True`), which is exactly why a pure re-export would have been wrong. | probe with no lane recorded: `shared route (no lane) RAISED TypeError save_state() missing 1 required keyword-only argument: 'write_report'` |
| F-5 | INFO | runner fork census | The scanner already names the defect set. | `python3 tools/runner_fork_scan.py --triples`: `NEITHER-DELEGATES 6 _lane_reclaim_prompt, _record_forced_stop, build_verify_and_continue_notice, classify_recovery_disposition, disable_lane_prompt, route_recovery_turn`; `reconcile_disposition BOTH-DELEGATE . 40 40 0.976`; headline `co-defined in both runners : 61` |
| F-6 | MED | tests | No in-tree test exercises recovery routing: `tests/test_resumedupe.py`, cited by oc's comments and `zt2b16` as the four tests that caught F-1, was deleted in `19313eed`. The only `reconcile_disposition` tests pass `configured_file`, so neither F-1 nor F-3 is guarded. | `grep -rln "classify_recovery_disposition\|route_recovery_turn\|recovery_routing" tests/*.py` -> no match; `git show --stat 19313eed` lists `tests/test_resumedupe.py | 675 ----` |
| F-7 | INFO | lift safety | The duplicates oc carries beside its classifier are safe to re-export: `RecoveryDisposition` and `_lane_commit_subjects` are AST-identical to shared; `TERMINAL_STATES` values are equal across all three modules; `resolve_prior_lane`, `_run_git`, `resolve_plan_path`, `plan_bucket`, `load_json` are already the shared objects in oc. No `isinstance(..., RecoveryDisposition)` exists anywhere, and no test patches any of these names on a host module except `tests/test_defect_report.py`'s `mock.patch.object(oc_runipd, "reconcile_disposition", ...)`. | AST probe: `_lane_commit_subjects True`, `RecoveryDisposition True`; `TERMINAL_STATES` symmetric difference `[]`; `oc._run_git is r._run_git, oc.resolve_prior_lane is r.resolve_prior_lane -> True True` |
| F-8 | LOW | `zt2b16` text | Stale detail only: its line numbers (`:22052`, `:4893`, ...) no longer match, and the four `test_resumedupe.py` tests it cites no longer exist (F-6). The substantive claims all hold. | as F-1, F-6 |

## Proposed changes (ordered, validatable)

1. E-01 reproduces F-1..F-5 and stops on drift.
2. E-02 writes the behavioral test module and shows it red.
3. E-03 moves oc's classifier body into `runner_shared`, deletes the host copies and oc's identical duplicates, re-exports.
4. E-04 does the same for the notice builder.
5. E-05 injects `save_state` into the shared `route_recovery_turn`, turns both hosts into wrappers, empties the recovery names out of `AGY_IMPORTS_FROM_OC_RUNIPD`, fixes the stale prose.
6. E-06 re-exports the shared tolerant `reconcile_disposition` from both hosts, keeping the host attribute so the `driver_module` rebinding and the existing test patch still work.
7. E-07 proves convergence with `tools/runner_fork_scan.py` and targeted suites; E-08 runs the bare suite.

## Deferred / out of scope (with reason)

- `record_item_spec_edits`, the one name left in `AGY_IMPORTS_FROM_OC_RUNIPD`. Different concern (spec-edit reporting), not part of either source item.
  - Carrier-Declined: Not a defect; it is a remaining import-direction tidy with no reported misbehavior, outside both source items.
- The other scanner residue (`_record_forced_stop`, `_lane_reclaim_prompt`, `disable_lane_prompt`). Named by F-5 but not part of the recovery-routing or reconcile class.
  - Carrier-Declined: No defect reported for them; `disable_lane_prompt` is recorded by `li44r9` D1 as deliberately staying forked.
- Changing routing policy, prompt text, or `reconcile_disposition` precedence. This plan picks between existing bodies; it does not redesign them.
  - Carrier-Declined: Not an obligation; any such change needs its own plan and review.
- Closing backlog `zt2b16` and `2t4v1j` after execution. `zt2b16` is linked by `- From-Backlog:` and this plan inherits its gate; `2t4v1j` is not linked, so its close needs `--evidence` citing this plan once executed.
  - Carrier-Evidence: .aw/records/backlog/open/20260922-2t4v1j-01-2t4v1j-reconcile-disposition-configured-file-keyerror.backlog.md

## Scope check

- Over-scope: E-05 reaches `route_recovery_turn`, which neither backlog item asks to fix by name. It is included because `zt2b16` itself says "the three recovery-routing names are all deferred together, which is the correct unit", and because single-sourcing the classifier while leaving a shared `route_recovery_turn` that raises `TypeError` (F-4) would recreate the exact dead-shared-copy hazard this plan removes.
- Under-scope: none known. If E-06's AST re-diff shows any difference beyond those listed, or any test patches a host attribute E-03..E-06 removes, STOP and report instead of widening.

## Required tests / validation

- New `tests/test_recovone_single_definition.py`, shown FAILING on the unmodified tree and passing after, with the LaneState from a real `worktree_lease.inspect_lane` call.
- Targeted modules listed in E-07, including `tests/test_defect_report.py` (the host-attribute patch) and `tests/test_orchestrator_shape_gate.py` (oc-to-agy import ceiling).
- `python3 tools/runner_fork_scan.py --triples` before (E-01) and after (E-07).
- Bare `python3 -m pytest` summary line.

## Spec / documentation sync

- N/A for specs: `grep -rln "classify_recovery_disposition\|build_verify_and_continue_notice\|verify-and-continue" .aw/records/specs` finds none, and no behavior a spec describes changes.
- In-code prose MUST be corrected in E-05: the `AGY_IMPORTS_FROM_OC_RUNIPD` comment in `runner_shared`, the "runnerlayer Order 02 (`1f7xno`) TRIED TO CONSOLIDATE" block in `oc_runipd`, and agy's "resumedupe (`txc9l1`) E-04" and `route_recovery_turn` docstring, all of which currently assert the consolidation is deferred and cite the deleted `tests/test_resumedupe.py`.

## Open questions

### OQ-01: Which body survives for build_verify_and_continue_notice?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE. Both bodies produce byte-equal output for a real `RecoveryDisposition` (F-2), so the choice cannot change behavior; oc's is chosen because it is the one every production run has executed and it carries the full docstring. The executor may keep shared's `getattr` form instead only if E-02's identity and routing tests still pass, but must not merge the two.
- Carrier-Declined: Resolved at authoring with no residual work.

### OQ-02: Should route_recovery_turn be lifted here or left host-defined?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: lift it as a `save_state`-injected shared body with host wrappers. Leaving oc's copy (with agy delegating to oc) would work functionally once the classifier is re-exported, but would keep a shared `route_recovery_turn` that raises `TypeError` (F-4) and keep agy importing from oc, the configuration `zt2b16` and the `AGY_IMPORTS_FROM_OC_RUNIPD` comment both identify as the hazard. The wrapper form is the established `reconcile_interrupted` precedent, so no new design is introduced.
- Carrier-Declined: Resolved at authoring with no residual work.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the probe's full stdout showing the LaneState line, the three classifier results (shared `AttributeError`), the shared `route_recovery_turn` `TypeError`, and the three `reconcile_disposition` results (oc `KeyError`); paste the `NEITHER-DELEGATES`, `reconcile_disposition` and `co-defined in both runners` rows from `python3 tools/runner_fork_scan.py --triples`; paste `git rev-parse --short HEAD`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_recovone_single_definition.py -o addopts="" -q` run against the UNMODIFIED production code (new test file only) showing failures that include `AttributeError` for the shared classifier, `KeyError: 'configured_file'` for oc reconcile, and failed `assertIs` identity checks; paste the grep proving the LaneState is obtained via `worktree_lease.inspect_lane` in the test module.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -n "def classify_recovery_disposition\|class RecoveryDisposition\|def _lane_commit_subjects" agent_workflows/*.py` showing only `runner_shared.py` hits; paste `grep -n "st\.path\|base_commit or\|wip(snapshot)" agent_workflows/runner_shared.py` showing none in the classifier; paste the E-02 class (1) tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n "def build_verify_and_continue_notice" agent_workflows/*.py` showing one hit in `runner_shared.py`; paste the identity test for this name passing for both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -c "from agent_workflows import runner_shared as r; print(sorted(r.AGY_IMPORTS_FROM_OC_RUNIPD))"` showing `['record_item_spec_edits']`; paste `grep -n "from agent_workflows.oc_runipd import" agent_workflows/agy_runipd.py`; paste the E-02 class (2) tests passing on both hosts; paste `python3 -m pytest tests/test_orchestrator_shape_gate.py -o addopts="" -q` summary; paste `grep -n "test_resumedupe\|TRIED TO CONSOLIDATE" agent_workflows/*.py` showing no stale deferral prose remains.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the pre-deletion docstring-stripped AST diff of the three `reconcile_disposition` bodies; paste `grep -n "def reconcile_disposition\|item\[\"configured_file\"\]" agent_workflows/*.py` showing one def (shared) and no subscript form in it; paste E-02 class (3) and the identity test passing; paste `python3 -m pytest tests/test_defect_report.py tests/test_runner_shared.py -o addopts="" -q` summary showing the host-attribute patch still works; paste the same class (3) test FAILING with oc's old definition temporarily restored (then restore the fix).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the after-run `python3 tools/runner_fork_scan.py --triples` rows showing the three names gone from the co-defined census, `route_recovery_turn` as `BOTH-DELEGATE`, and `co-defined in both runners` exactly three below V-01's value; paste the targeted pytest summary line from E-07's command.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of a bare `python3 -m pytest` (e.g. `N passed, M skipped ... in Ts`), with any failure named and shown pre-existing on the unmodified tree.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes; test claims must paste actual runner output. STOP CONDITIONS: if E-01 finds any finding no longer reproduces, or E-06's AST re-diff shows a difference beyond those recorded in F-3, or removing a host definition breaks a test that patches it, stop and report rather than widening scope. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the terminal transition, which the runner owns in a managed lane (report results and let it finalize) and the executor otherwise performs with `aw ipd finalize`.
