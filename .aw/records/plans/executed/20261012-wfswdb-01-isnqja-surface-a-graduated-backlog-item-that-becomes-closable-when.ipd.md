# IPD: Surface a graduated backlog item that becomes closable when its spec carrier reaches implemented

- Date: 2026-10-12
- Kind: child
- Concern: After `5eygjt` made `runner_shared.evaluate_backlog_close` refuse a MIXED (plan + spec) backlog item whose spec carrier is not `implemented`, nothing re-evaluates that item when the spec later reaches `implemented`. The runner evaluates a close only from `runner_shared.process_backlog_close`, which runs when a PLAN carrier executes, and `aw specs set ... implemented` (`specs.run_set` -> `status_set.run_set_command`) consults no From-Backlog item. So such an item stays `graduated` silently, and no surface tells an operator it is now closable.
- Scope: IN: (a) a new read-only advisory producer `check_engine.graduated_closable_warnings(repo_root)` that reports every `graduated` backlog item whose From-Backlog carriers are ALL terminal (plans `executed`, specs `implemented`, judged by the shipped `check_engine._carrier_is_executed`), built on the ONE-walk `check_engine._from_backlog_carrier_index`, with a copy-pasteable `Fix:` close command; (b) registering its rule id `check.graduated-item-closable` in `check_engine.RULE_REGISTRY` at `info` severity; (c) rendering it in the `aw attention` human board as its own advisory section next to `release-gate-warnings`, never affecting the exit code or `--check`; (d) behavioral tests; (e) a CHANGELOG entry. OUT: performing or offering the close from `aw specs set ... implemented` (see OQ-01 and Deferred); changing `release_gate_warnings` (its output is consumed by `production_checks.backlog_cross_tree` as a FAILING finding for any rule other than `check.orphaned-live-blocker`, so adding a rule there would change graduation verdicts); changing either close predicate; the JSON/agent attention renderer.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/attention.py, tests/test_graduated_closable_warning.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: wfswdb
- Set: wfswdb
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: isnqja

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: isnqja verified (set wfswdb, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `wfswdb` (filed by `5eygjt` plan-review finding F-10). Findings measured at HEAD `402655b05c7b0de8092202968d89d62bd2e70cfd` in the isolated authoring lane.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make a `graduated` backlog item whose carriers have ALL reached a terminal state visible in `aw attention`, with the exact command that closes it, so the close `5eygjt` deliberately deferred until a spec ships is not silently lost when that spec later reaches `implemented` (or when any other route finishes the last carrier outside a run).

WHAT CHANGES, as observable output: on a repository holding a graduated item whose plan is `executed` and whose spec is `implemented`, `aw attention` prints a `graduated-closable (1)` section naming the item, the rule `check.graduated-item-closable`, and a `Fix: aw backlog set <id6> --status done --evidence <carrier path>` line; the exit code and `--check` result are unchanged. With the spec still `approved`, no such section appears.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: confirm the premises

- [x] E-01 RE-MEASURE THE PREMISES AT EXECUTION HEAD and paste the outputs: (1) every call site of `process_backlog_close(` in `agent_workflows/` (F-01: only runner paths after a plan executes); (2) that `agent_workflows/specs.py` and `agent_workflows/status_set.py` contain no call to `evaluate_backlog_close`/`process_backlog_close` (F-02); (3) the live census of `graduated` items whose carriers are all terminal, via `_from_backlog_carrier_index` + `_carrier_is_executed` (F-04); (4) the bare `python3 -m pytest` baseline failing node ids; (5) two warm `aw attention` wall-clock timings (F-06), which are the before-state for V-05.
  - Depends on: none
  - Expected outcome: five pasted measurements naming the HEAD sha. IF a re-trigger now exists (a spec-implemented path that already evaluates or reports the item close), STOP and report the plan as overtaken with the contradicting output rather than adding a second surface.
  - Execution state: performed

### Task group 2: pin the behavior first

- [x] E-02 ADD BEHAVIORAL TESTS in new `tests/test_graduated_closable_warning.py`, written BEFORE E-03/E-04 so they are observed failing first, on `tempfile` scratch repos with real files (reuse the fixture shape of `tests/test_check_engine_release_gate.py::_create_minimal_repo`, copied locally, not imported, so the two files stay independent). Cases: (1) graduated item + executed plan + `implemented` spec, both carrying `- From-Backlog:` -> exactly one `check.graduated-item-closable` warning located at the item, whose detail contains `aw backlog set <id6> --status done --evidence ` and a carrier path; (2) the same with the spec `approved` -> zero warnings; (3) graduated item with a PENDING plan -> zero; (4) graduated IPD-only item whose plan is executed -> one warning (the predicate is uniform, not mixed-only); (5) an `open` item and a `done` item with all-terminal carriers -> zero (only `graduated` qualifies); (6) a graduated item with NO carrier -> zero; (7) REMEDY WORKS: on case (1) with the item carrying `- Blocks-Release:` resolving to a planned release, run the warning's `Fix:` command through the real CLI (`python3 -m agent_workflows backlog set ... --dir <repo> --no-commit`, subprocess) and assert exit 0 and the item now under `backlog/done/`; repeat it with the carrier plan carrying a DIFFERENT `- Blocks-Release:` from the item (the case E-03 cites as the reason for `--evidence`), with the same assertions; (8) ATTENTION SURFACE: drive `attention.run` on case (1)'s repo (as `tests/test_attention.py` does) and assert stdout contains `graduated-closable (1)`, the item id6, and the `Fix:` line, and that the return code equals the return code of the same run on case (2)'s repo, also under `--check` (the section never changes the exit code); and drive `attention --agent` on case (1)'s repo and assert its stdout does not contain `check.graduated-item-closable` (the section is human-view only and must not reach machine output); (9) `check_engine.rule_spec("check.graduated-item-closable").severity == "info"`.
  - Depends on: E-01
  - Expected outcome: cases (1), (4), (7), (8), (9) fail before E-03/E-04 (the `--agent` half of (8) passes before and after, since nothing emits the rule yet) (missing function/section/registration) and all pass after; (2), (3), (5), (6) are vacuous before (they import a function that does not yet exist, so they ERROR) and pass after.
  - TEST OUTCOMES, NOT CODE STRUCTURE (P16): assert only on returned `Drift` fields, CLI exit codes, on-disk moves and rendered stdout. No `inspect`/`ast`/regex over production source. Do not pin the full detail string; assert on the command fragment and ids.
  - Execution state: performed

### Task group 3: implement

- [x] E-03 ADD `check_engine.graduated_closable_warnings(repo_root) -> List[Drift]` beside `release_gate_warnings`, and register `"check.graduated-item-closable": RuleSpec("info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07")` in `RULE_REGISTRY`. Algorithm: build `_from_backlog_carrier_index(repo_root)` ONCE; iterate `backlog._iter_items(repo_root)`; keep items whose parsed `- Status:` is `graduated` (read the field via `_status_meta`, not the directory, matching `check_graduation_incomplete`); look up the item's carriers by its `- Id:`; emit one `Drift(str(item_path), "check.graduated-item-closable", detail)` iff the carrier list is non-empty and EVERY carrier satisfies `_carrier_is_executed`. Detail: `"a graduated item's carriers are all terminal (plans executed, specs implemented); close it done.\n    Fix: aw backlog set <id6> --status done --evidence <repo-relative path of the first carrier, plans first>"`, using the same `\n    Fix:` suffix convention `release_gate_warnings` uses so the attention renderer's partition works unchanged. Read failures skip the item (fail toward silence: this is advisory and must never raise into `aw attention`).
  - Depends on: E-02
  - Expected outcome: cases (1)-(6) and (9) pass.
  - DO NOT call `find_from_backlog_artifacts` per item: it re-walks both trees per call and `tests/test_carrier_scan_single_item_contract.py` fails on a loop-derived argument. DO NOT add a second spec-status reader: `_carrier_is_executed` is the one authority (its docstring records why a spec's truth is its `- Status:` field). DO NOT add the rule to `release_gate_warnings` (F-05).
  - WHY `--evidence` IN THE FIX: SATISFIED accepts any resolvable in-tree records path (`check_engine.resolve_evidence_artifact`), so the command is legitimate whether the item is gated or not and regardless of whether its carriers share its gate; HANDOFF alone would refuse a gated item whose terminal carriers carry a different gate. Every cited carrier is terminal by construction, so the citation is true.
  - Execution state: performed

- [x] E-04 RENDER THE SECTION IN `attention.run`'s human board, immediately after the `release-gate-warnings` block, under the same guard (`not type_filters or "backlog" in type_filters`), the same selector filtering, the same `try/except -> []` fail-closed wrapper, and the same row/`Fix:` formatting, with header `graduated-closable (<n>)` (colored 214 bold when colored, else `## ` prefixed, as the neighbouring header is). Advisory only: it must not add to the drift set, the JSON output, or the exit code.
  - Depends on: E-03
  - Expected outcome: case (8) passes; `aw attention` on this repository prints no new section while F-04's census is zero.
  - Execution state: performed

- [x] E-05 ADD A CHANGELOG ENTRY under the topmost pending heading (at authoring `## 2.0.0 (pending)`), one sentence: `aw attention` now lists graduated backlog items whose plan and spec carriers have all finished, with the command that closes them. Then run the bare full suite and re-time `aw attention` warm twice.
  - Depends on: E-03, E-04
  - Expected outcome: failing node-id set equals E-01's baseline plus nothing; the new test file passes; the warm `aw attention` delta versus E-01 is recorded with numbers.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `aw attention` is READ-ONLY and computed on demand (AGENTS.md "What needs attention"); its release-gate advisory section is human-view only and "NEVER affect[s] the exit code" (comment above the `release_gate_warnings` call in `attention.run`). The new section follows that precedent exactly.
- Carrier discovery for MANY items must use `check_engine._from_backlog_carrier_index` (one walk of plans + specs); `find_from_backlog_artifacts` is single-item only and machine-checked by `tests/test_carrier_scan_single_item_contract.py`.
- A carrier's terminal state has one authority, `check_engine._carrier_is_executed`: plans by an `executed` path segment, specs by `- Status: implemented`.
- `production_checks.backlog_cross_tree` treats every `release_gate_warnings` rule except `check.orphaned-live-blocker` as a FAILING graduation finding, so that producer's rule set is load-bearing for graduation verdicts.
- Tests drive behavior (GUIDING_PRINCIPLES P16); the suite runs bare as `python3 -m pytest`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All at HEAD `402655b05c7b0de8092202968d89d62bd2e70cfd`.

| id | sev | finding | evidence |
|---|---|---|---|
| F-01 | MED | The runner evaluates a backlog close only from `runner_shared.process_backlog_close`, whose docstring reads "After a plan reaches `executed`, close its backlog item if this run earned it"; its call sites are all in runner code (`runner_shared` four sites, plus the `oc_runipd`/`agy_runipd` wrappers). | `grep -rn "process_backlog_close(" agent_workflows/*.py` |
| F-02 | MED | `aw specs set` is a thin adapter to `status_set.run_set_command(scoped_type="specs")` and neither module calls `evaluate_backlog_close`; so a spec reaching `implemented` re-evaluates nothing. | `specs.run_set`; grep of `specs.py`/`status_set.py` |
| F-03 | LOW | Since `5eygjt`, `evaluate_backlog_close` refuses a mixed item with reason `spec carrier(s) not implemented: ...`; the refusal is recorded (`backlog-item-left-open` event, `render_unclosed_report`) but only inside that run's records. | `runner_shared.evaluate_backlog_close`; `5eygjt` V-02 |
| F-04 | LOW | Live census: 61 `graduated` items; 0 have all carriers terminal; 2 graduated items have a spec carrier (`ms06pi` spec-only, spec not implemented; `fcnz1r` 8 plans, 7 executed, spec `wy9aru` not implemented). So the gap is latent today and `fcnz1r` is the first item that will hit it. | scratch script over `_from_backlog_carrier_index` + `_carrier_is_executed` |
| F-05 | MED | `release_gate_warnings` is consumed by `attention.run`, `production_checks.backlog_cross_tree`, and twice in `runner_shared` (graduation advisory). `backlog_cross_tree` converts any non-`orphaned-live-blocker` rule located at the item into a `BACKLOG-CROSS-TREE` failure. A new rule there would change graduation outcomes, so the new producer must be separate. | `production_checks.backlog_cross_tree` body |
| F-06 | LOW | Cost: `_from_backlog_carrier_index` measured 0.29-0.34 s warm (672 keys); `release_gate_warnings` 0.30 s; a warm `aw attention` 5.67 s. The new producer adds roughly one index walk, about 5 percent of the command; E-05 measures the real end-to-end delta. | timing script, `/usr/bin/time aw attention` |
| F-07 | LOW | The inner gate's SATISFIED arm accepts any resolvable in-tree records path, so `--evidence <terminal carrier>` makes the Fix command legitimate for gated and ungated items alike. | `check_engine.evaluate_blocking_close` docstring; `check_engine.resolve_evidence_artifact` |
| F-08 | LOW | REVIEW-ADDED. Pending sibling `0owirm` (Set `gradfix`) adds `runner_shared.backlog_item_already_complete` for `open` items and explicitly hands the `graduated` case to this plan (its Deferred: "owned by pending plan `isnqja`"). Its predicate requires at least one IPD carrier; this plan's requires a non-empty carrier list, so a spec-only graduated item with an `implemented` spec is surfaced here but would be NO_IPD_CARRIER there. Measured at review: `aw backlog set <id6> --status done --evidence <terminal carrier>` exits 0 and moves a graduated item to `done/` for a same-gate carrier, a different-gate carrier, and an ungated item, so a spec-only surface is still closable. | The two predicates are on different populations (`open` vs `graduated`) and both judge terminality by `_carrier_is_executed`, so they cannot disagree about one carrier. The spec-only difference is deliberate here (the backlog item is about spec carriers). Converging them is out of scope; do not import `0owirm`'s predicate, which may not exist at execution. |

## Proposed changes (ordered, validatable)

1. Re-measure the premises and baselines (E-01).
2. Write the failing behavioral tests (E-02).
3. Add `graduated_closable_warnings` and register its rule at `info` (E-03).
4. Render the advisory section in `aw attention` (E-04).
5. CHANGELOG, full suite, timing (E-05).

## Deferred / out of scope (with reason)

- PERFORMING OR OFFERING THE CLOSE FROM `aw specs set ... implemented`. Declined in favour of the attention surface (OQ-01): a spec setter mutating a backlog item is a cross-artifact side effect in a shared-checkout, path-scoped-commit workflow, the runner deliberately decides close eligibility against main (`process_backlog_close` docstring, OQ-01 of `9iq461`), and a setter hook only covers one of several routes by which a last carrier becomes terminal.
  - Carrier-Declined: NOT OWED. The attention surface closes the visibility gap the backlog item names for every route; a setter-side hint would be a convenience, and if a maintainer wants it, it is a separate `followup` on `status_set.run_set_command`.
- ADDING THE RULE TO `release_gate_warnings` or to `aw check`. Excluded because of F-05 (graduation verdicts) and because a closable item is not a defect to fail a check on.
  - Carrier-Declined: NOT OWED; deliberate design choice recorded here.
- CONVERGING WITH `0owirm`'s `backlog_item_already_complete` (F-08). Different item populations, same terminality authority; folding them together would couple this plan to an unexecuted sibling.
  - Carrier-Declined: NOT OWED; both judge carriers through `_carrier_is_executed`, so no disagreement is possible on a single carrier.
- JSON / `--agent` attention output. The precedent section (`release-gate-warnings`) is human-view only; widening machine output is a contract change.
  - Carrier-Declined: NOT OWED; follows the shipped precedent.

## Scope check

- Over-scope: none. Two production modules gain one function, one registry entry and one render block; one new test file; one CHANGELOG line.
- Under-scope: an item whose spec carrier is retired (`superseded`/`deferred`/`parked`) is never "all terminal" by `_carrier_is_executed` and so is not surfaced; that matches both close predicates and remains a hand decision.

## Required tests / validation

- `tests/test_graduated_closable_warning.py` (new), nine behavioral cases (E-02), with (1), (4), (7), (8), (9) observed failing before E-03/E-04.
- `tests/test_carrier_scan_single_item_contract.py`, `tests/test_check_engine_release_gate.py`, `tests/test_backlog_production.py`, `tests/test_attention.py`, `tests/test_severity_tier_contract.py` stay green unchanged.
- Bare `python3 -m pytest` compared by node id against E-01's baseline.
- Warm `aw attention` timing before (E-01) and after (E-05).

## Spec / documentation sync

- No `.spec.md` is amended and `Scope-Paths` declares none: no spec describes the `aw attention` advisory sections or `release_gate_warnings` (grep of `.aw/records/specs` for `release-gate-warnings`/`release_gate_warnings` returned nothing at authoring).
- `CHANGELOG.md` gets one user-facing line (E-05), written without em or en dashes.
- `AGENTS.md` needs no edit: it describes the close routes, which are unchanged.

## Open questions

### OQ-01: Should `aw specs set implemented` re-evaluate the item close, or should the attention view surface the closable item?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence: the attention view. (a) `aw attention` is the documented cross-tree "what needs attention" surface and is read-only, so surfacing costs no new mutation path; (b) it catches EVERY route by which the last carrier becomes terminal (spec setter, a plan executed outside a run, a hand edit), whereas a setter hook catches one; (c) the runner deliberately takes close decisions against main with earned-path rules (`runner_shared.process_backlog_close`, `evaluate_backlog_close` E-04 "the run must have EARNED it"), which a spec setter cannot reproduce, so a setter-side close would be a third close predicate; (d) the backlog item itself frames the attention option as an acceptable answer and states the gap is not a correctness defect. The setter-side option is recorded as declined in Deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted outputs of all five E-01 measurements with the HEAD sha: the `process_backlog_close(` call-site list, the empty grep over `specs.py`/`status_set.py`, the census counts (graduated total, all-terminal count, ids of graduated items with a spec carrier), the baseline failing node-id list (or `none`) with the pytest summary line, and two warm `aw attention` timings.
  - Observed evidence: HEAD sha `21c2743daa19f58c5848102e2c75b6c862cec077`:
    (1) `grep -rn "process_backlog_close(" agent_workflows/`:
    ```
    agent_workflows/agy_runipd.py:1689:def process_backlog_close(
    agent_workflows/agy_runipd.py:1698:    return runner_shared.process_backlog_close(
    agent_workflows/oc_runipd.py:1334:def process_backlog_close(
    agent_workflows/oc_runipd.py:1343:    return runner_shared.process_backlog_close(
    agent_workflows/runner_shared.py:12779:            process_backlog_close(run_dir, state, item)
    agent_workflows/runner_shared.py:40198:                        process_backlog_close(
    agent_workflows/runner_shared.py:41116:                    process_backlog_close(run_dir, state, item)
    agent_workflows/runner_shared.py:41586:def process_backlog_close(
    agent_workflows/runner_shared.py:42003:                process_backlog_close(
    ```
    (2) `grep -rn "evaluate_backlog_close\|process_backlog_close" agent_workflows/specs.py agent_workflows/status_set.py`:
    Output: empty (exit code 1, no matches).
    (3) Live census counts:
    Total graduated items: 65
    All terminal items count: 2 (`rolswj`, `23p80m`)
    Graduated items with spec: 2 (`ms06pi`, `fcnz1r`)
    (4) Baseline pytest:
    `7937 passed, 4 skipped, 18 xfailed, 3 warnings in 1035.89s (0:17:15)`
    Failing node ids: none.
    (5) Two warm `aw attention` wall-clock timings:
    Run 1: real 11.16, user 8.68, sys 1.32
    Run 2: real 10.79, user 8.33, sys 1.27
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the new test file's pytest output BEFORE E-03/E-04 showing cases (1), (4), (7), (8), (9) failing or erroring with their node ids and summary line, and a statement that the run happened before any production edit (no stash, no revert).
  - Observed evidence: Run executed at HEAD `21c2743daa19f58c5848102e2c75b6c862cec077` with only untracked `tests/test_graduated_closable_warning.py` present before any production edits to `agent_workflows/check_engine.py` or `agent_workflows/attention.py` (no stash, no revert):
    ```
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_2_spec_approved_produces_zero_warnings FAILED [ 11%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_1_graduated_with_executed_plan_and_implemented_spec FAILED [ 22%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_7_remedy_works_with_same_and_different_gate FAILED [ 33%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_6_graduated_item_with_no_carrier_produces_zero_warnings FAILED [ 44%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_3_pending_plan_produces_zero_warnings FAILED [ 55%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_8_attention_surface_rendering_and_invariants FAILED [ 66%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_9_rule_spec_registration_and_severity FAILED [ 77%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_4_graduated_ipd_only_item_with_executed_plan FAILED [ 88%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_5_open_and_done_items_produce_zero_warnings FAILED [100%]
    =========================== short test summary info ============================
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_2_spec_approved_produces_zero_warnings
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_1_graduated_with_executed_plan_and_implemented_spec
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_7_remedy_works_with_same_and_different_gate
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_6_graduated_item_with_no_carrier_produces_zero_warnings
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_3_pending_plan_produces_zero_warnings
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_8_attention_surface_rendering_and_invariants
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_9_rule_spec_registration_and_severity
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_4_graduated_ipd_only_item_with_executed_plan
    FAILED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_5_open_and_done_items_produce_zero_warnings
    ============================== 9 failed in 0.88s ===============================
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pytest output showing cases (1)-(6) and (9) passing after E-03, plus the pasted `Drift` produced for case (1) (location, rule, detail), plus `tests/test_carrier_scan_single_item_contract.py` passing output.
  - Observed evidence: Cases (1)-(6), (7), and (9) passing after E-03:
    ```
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_5_open_and_done_items_produce_zero_warnings PASSED [ 11%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_4_graduated_ipd_only_item_with_executed_plan PASSED [ 22%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_2_spec_approved_produces_zero_warnings PASSED [ 33%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_3_pending_plan_produces_zero_warnings PASSED [ 44%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_9_rule_spec_registration_and_severity PASSED [ 55%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_6_graduated_item_with_no_carrier_produces_zero_warnings PASSED [ 66%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_1_graduated_with_executed_plan_and_implemented_spec PASSED [ 88%]
    tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_7_remedy_works_with_same_and_different_gate PASSED [100%]
    ```
    Drift produced for case (1):
    ```
    LOCATION: /tmp/tmp9ngzgch3/.aw/records/backlog/graduated/20261012-0001-01-bklg01-test-item.bklg.md
    RULE: check.graduated-item-closable
    DETAIL:
    a graduated item's carriers are all terminal (plans executed, specs implemented); close it done.
        Fix: aw backlog set bklg01 --status done --evidence .aw/records/plans/executed/20261012-set01-01-plan01-test-plan.ipd.md
    ```
    `tests/test_carrier_scan_single_item_contract.py` passing output:
    ```
    ============================== 9 passed in 10.23s ==============================
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: case (7) and (8) passing output, plus the literal `aw attention` stdout excerpt from case (1)'s scratch repo showing the `graduated-closable (1)` header, the item row and the `Fix:` line (produced by `attention.run`, the E-04 render block), and the two return codes from case (1)/(2) repos being equal.
  - Observed evidence: Cases (7) and (8) passing in `tests/test_graduated_closable_warning.py`:
    ```
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_7_remedy_works_with_same_and_different_gate
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_8_attention_surface_rendering_and_invariants
    ```
    Literal `aw attention` stdout excerpt from case (1)'s scratch repo:
    ```
    ## graduated-closable (1)
    - /tmp/tmpi113tbe4/.aw/records/backlog/graduated/20261012-0001-01-bklg01-test-item.bklg.md: check.graduated-item-closable: a graduated item's carriers are all terminal (plans executed, specs implemented); close it done.
        Fix: aw backlog set bklg01 --status done --evidence .aw/records/plans/executed/20261012-set01-01-plan01-test-plan.ipd.md
    ```
    Return codes comparison:
    `RC1: 0`, `RC2: 0`, `RC_CHK1: 0`, `RC_CHK2: 0`
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the CHANGELOG diff hunk; the bare `python3 -m pytest` summary line verbatim with the failing node-id list compared against V-01's baseline (no node id added); `python3 -m pytest -o addopts="" -rA tests/test_graduated_closable_warning.py` output showing every case named in E-02 PASSED with none skipped or xfailed (a re-derived per-case listing, not a count bar); two warm `aw attention` timings after the change beside V-01's.
  - Observed evidence:
    CHANGELOG diff hunk:
    ```diff
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Added: `aw attention` now lists graduated backlog items whose plan and spec carriers have all finished, with the command that closes them.
     - Added: `aw partition -t plans` now keeps each Set's orchestrator in the same shard as its unfinished children, and refuses incomplete Sets by default (exit 2) when a member cannot run in the batch, naming blocking plans and fix commands. Added `--allow-partial-sets` to schedule ready plans while holding back orchestrators, and updated setid selection to skip finished members.
     - Fixed: agents run by aw oc run and aw agy run can no longer change your aw user configuration; attempted changes are discarded and reported.
     - Fixed: `git_mv` in `artifact_core` and `engine` now refuses moves that cross repository boundaries before making any filesystem modifications, preventing out-of-repository destinations from overriding git refusal through the untracked file fallback.
    ```
    Bare `python3 -m pytest` summary line:
    `7946 passed, 4 skipped, 18 xfailed, 3 warnings in 582.84s (0:09:42)`
    Failing node-id list compared to V-01 baseline: none (0 failed in baseline, 0 failed post-change).
    `python3 -m pytest -o addopts="" -rA tests/test_graduated_closable_warning.py` output:
    ```
    ==================================== PASSES ====================================
    =========================== short test summary info ============================
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_1_graduated_with_executed_plan_and_implemented_spec
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_2_spec_approved_produces_zero_warnings
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_5_open_and_done_items_produce_zero_warnings
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_4_graduated_ipd_only_item_with_executed_plan
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_7_remedy_works_with_same_and_different_gate
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_9_rule_spec_registration_and_severity
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_3_pending_plan_produces_zero_warnings
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_8_attention_surface_rendering_and_invariants
    PASSED tests/test_graduated_closable_warning.py::TestGraduatedClosableWarning::test_case_6_graduated_item_with_no_carrier_produces_zero_warnings
    ============================== 9 passed in 1.14s ===============================
    ```
    Warm `aw attention` wall-clock timings:
    Before (V-01):
    Run 1: real 11.16s, user 8.68s, sys 1.32s
    Run 2: real 10.79s, user 8.33s, sys 1.27s
    After (V-05):
    Run 1: real 7.21s, user 5.95s, sys 1.04s
    Run 2: real 6.33s, user 5.47s, sys 1.03s
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` plus this plan file, through `aw commit <plan> -- <paths>`; never `git add -A`, never push. `- Scope-Paths:` is a declaration: an undeclared edit the work genuinely needs is made and justified at finalize with `--scope-reason <path>=<why>`.

OPEN QUESTIONS. OQ-01 is resolved; no blocking question remains.

HONESTY. Every `Observed evidence` MUST paste the ACTUAL runner output (pytest lines, `aw attention` stdout, timings); never claim a pass that was not run.

LIFECYCLE START. Begin with `aw ipd begin isnqja --actor <you>`. Commit via `aw commit isnqja -- agent_workflows/check_engine.py agent_workflows/attention.py tests/test_graduated_closable_warning.py CHANGELOG.md <this plan>`.

ORDER MATTERS. E-02's tests are run and observed failing before E-03 edits production code; V-02 cannot be satisfied retroactively.

POST-GATE LIFECYCLE MOVE. Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the driver performs finalize, so the executor must NOT run `aw ipd finalize` itself; outside a run use `aw ipd finalize isnqja --actor <you> --message <msg> --apply`, never a hand `git mv`. Closing backlog item `wfswdb` is the runner's act on executing this carrier; it carries no `- Blocks-Release:`, so this plan inherits none.
