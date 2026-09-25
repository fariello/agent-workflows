# IPD: Make the end-of-run spec-edit report read the record execute_item_core actually writes

- Date: 2026-09-24
- Kind: child
- Concern: THE END-OF-RUN DECLARED-SPEC-EDIT REPORT HAS BEEN INERT ON BOTH HOSTS SINCE THE `execute_item` DEDUP, AND ITS MOST IMPORTANT CASE IS NOW SILENT. `runner_shared.record_item_spec_edits` is the copy `runner_shared.execute_item_core` calls at both finalize sites (lane and main tree), and it stores `{"reconciled", "reasons", "acks", "refused"}` under `item["spec_edits_reconciliation"]`. The ONLY reader, `runner_shared.spec_edit_summary` (reached through `runner_shared.report_run_spec_edits` at all six summary sites, three per host), reads `item.get("spec_edits")` and expects the `runner_shared.spec_edit_record` shape `{"state", "declared", "modified_not_declared", "declared_not_modified"}`. So every item that DID finalize is reported `not_finalized`, and because `render_stream.format_spec_edit_report` stays silent when nothing is declared, changed, unfulfilled, or refused, a run whose only spec event is an UNDECLARED spec modification prints NOTHING. That is precisely the case the report exists for, and it inverts the managed AGENTS.md promise ("INCLUDING a spec that was modified WITHOUT being declared ... silence means 'no declared spec edits' and never 'the announcer broke'"). Root cause: commit `70a2059f` ("deduplicate execute_item into runner_shared.execute_item_core") moved the call onto a DIVERGED shared copy; the `oc_runipd.record_item_spec_edits` copy that writes the reader's key and shape is now called by nothing.
- Scope: Make ONE record, written by the ONE recorder the runners call and read by the ONE reader. IN: (a) `runner_shared.record_item_spec_edits` builds its record with `runner_shared.spec_edit_record` (so it carries `declared`/`modified_not_declared`/`declared_not_modified` and a `state` constant) and stores it under `item["spec_edits"]`, keeping its existing refused-detection logic; (b) `runner_shared.spec_edit_summary` tolerates the legacy `spec_edits_reconciliation` record already on disk by converting it losslessly through `spec_edit_record`; (c) retire the dead `oc_runipd.record_item_spec_edits` fork so the two definitions cannot diverge again (both hosts bind the shared one; `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` shrinks by one); (d) behavioral tests driving the real finalize-to-report path on both hosts, plus the silence and legacy cases. OUT: changing the report's wording or adding a new "declared and modified" section (OQ-01); changing `compute_scope_reconciliation` or `finalize_precheck`; the start-of-run announcement (already correct, `st5klo`).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Set: specrpt
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9npssm
- From-Backlog: tm5vnx
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog tm5vnx; re-measured at HEAD 877545fc that the shared recorder writes `spec_edits_reconciliation` while the only reader reads `spec_edits`, that an undeclared-spec-only run prints nothing at all, and that 146 legacy records already sit in local run state.

## Goal

Make `aw oc run` and `aw agy run` actually report, at run end, which specs each finalized item declared and which it changed (including an undeclared spec change), by having the one recorder both runners call write the exact record the one reader consumes, while still rendering run directories written by the broken recorder.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce before changing

- [ ] E-01 RE-MEASURE THE DEFECT at the executing HEAD. (1) `grep -n "spec_edits_reconciliation\|\"spec_edits\"\|item.get(\"spec_edits\")" agent_workflows/*.py` and confirm the writer/reader split. (2) Run a throwaway probe (under `/tmp/`) that calls `runner_shared.record_item_spec_edits` on a plan declaring `docs/A.spec.md` with an injected `reconcile` returning `({"docs/B.spec.md": "why"}, {})`, then `runner_shared.report_run_spec_edits` on `{"repo": ..., "queue": [item]}`; confirm the item is reported `NOT FINALIZED` and that a plan declaring NO spec yields `[]` (silent) even though B was changed. (3) Confirm `oc_runipd.record_item_spec_edits` has no caller (`grep -rn "record_item_spec_edits(" agent_workflows/`), and that `agy_runipd` imports it from `oc_runipd`. If the writer and reader already agree, STOP and report: the defect is fixed.
  - Depends on: none
  - Expected outcome: the three observations pasted, matching the Findings table, or a STOP report.
  - Execution state: pending

### Task group 2: one record

- [ ] E-02 CHANGE THE WRITER. In `runner_shared.record_item_spec_edits`, keep the existing `reconcile` call and the `finalize_precheck` refused-detection exactly as they are, then build the record with `spec_edit_record(plan_path, reasons, acks, state=SPEC_RECONCILE_REFUSED if refused else SPEC_RECONCILED)` and store it under `item["spec_edits"]`. Stop writing `spec_edits_reconciliation` (no other reader exists; see F-4). The declared set comes from `declared_spec_paths` over the plan text at finalize time and the modified sets from the `.spec.md` filter over `reasons`/`acks`, which is exactly the computation the pre-dedup `oc_runipd.record_item_spec_edits` performed; reuse it, do not re-derive a diff. Port the pre-dedup docstring's two load-bearing explanations (why it is recorded durably on the queue item, and why refused is detected rather than inferred from emptiness) onto the shared function.
  - Depends on: E-01
  - Expected outcome: after one finalize, the queue item carries exactly one spec record, under `spec_edits`, in the `spec_edit_record` shape; the refused path still records `state: "refused"`.
  - Execution state: pending

- [ ] E-03 MAKE THE READER TOLERATE LEGACY ON-DISK STATE. In `runner_shared.spec_edit_summary`, when `item.get("spec_edits")` is absent but `item.get("spec_edits_reconciliation")` is a mapping, convert it: `refused: true` maps to `SPEC_RECONCILE_REFUSED`; otherwise call `spec_edit_record(plan_path, legacy["reasons"], legacy["acks"], state=SPEC_RECONCILED)` using the `plan_path` the function already resolves through `queue_plan_path` (fall back to an empty declared list when it is None). The conversion is lossless because the legacy maps are keyed by path, which is all `spec_edit_record` reads. Update the docstring's "An older run directory carrying no `spec_edits` key" sentence to describe both legacy shapes. Do NOT write the converted record back to state (the reader stays read-only).
  - Depends on: E-02
  - Expected outcome: `print_status` / the end report on a run directory written between `70a2059f` and this fix renders its reconciled items correctly instead of as never-finalized.
  - Execution state: pending

- [ ] E-04 RETIRE THE DEAD FORK. Delete `oc_runipd.record_item_spec_edits` and re-export the shared one in `oc_runipd`'s existing `from agent_workflows.runner_shared import (... as ...)` block (so `oc_runipd.record_item_spec_edits is runner_shared.record_item_spec_edits`); move `agy_runipd`'s import of that name from its `oc_runipd` statement into its `runner_shared` statement and update the adjacent comment that names `tm5vnx`; remove `"record_item_spec_edits"` from `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` (its own comment says shrinking is progress). Check `oc_runipd.spec_edit_record` stays imported only if still used; drop an unused re-export only if nothing imports it from `oc_runipd`.
  - Depends on: E-02
  - Expected outcome: exactly one `def record_item_spec_edits` in the package; `oc_runipd.record_item_spec_edits is agy_runipd.record_item_spec_edits is runner_shared.record_item_spec_edits` is True.
  - Execution state: pending

### Task group 3: prove it on the real path

- [ ] E-05 ADD THE OC BEHAVIORAL TEST in `tests/test_oc_runipd.py`, beside `SelfFinalizeWiringTests`, reusing `_init_repo_with_conforming_plan`'s shape with a plan variant whose `- Scope-Paths:` is `docs/A.spec.md`. Drive `driver.execute_item(run_dir, state, item, recovery=False)` with the REAL `driver_begin` (so a real receipt exists and the real `compute_scope_reconciliation` runs), a fake `run_opencode` that edits and COMMITS both `docs/A.spec.md` and `docs/B.spec.md`, an outcome file as the neighbouring tests write it, `no_audit: True`, `isolate_worktree: False`; `driver_finalize` may be patched to `(0, "finalized")` because the record is written BEFORE finalize. Then call `driver.report_run_spec_edits(state, stream=buf)` and assert: `"declared -> docs/A.spec.md"` present; `"declared, unmodified -> docs/A.spec.md"` ABSENT (A was declared and modified); `"modified (undeclared) -> docs/B.spec.md"` present; `"Reconciled 1 item(s)"` present; `"NOT FINALIZED"` absent. Also assert the queue item has `spec_edits` and no `spec_edits_reconciliation`. In the same class add the SILENCE case: plan declaring `src/` only, fake turn committing `src/demo.txt`, and assert `report_run_spec_edits` returns `[]` and wrote nothing to the stream.
  - Depends on: E-02
  - Expected outcome: both tests pass after E-02 and the first FAILS against the pre-E-02 writer (the item reports as never finalized and B is not named).
  - Execution state: pending

- [ ] E-06 ADD THE AGY PARITY TEST in `tests/test_agy_runipd_cli.py`, using that file's `_state_and_item` harness and patching `agy_runipd.run_agy_turn` the way its existing wiring tests do, with the same A-declared / A+B-modified fixture and the same four report assertions. This is what makes the AGENTS.md "BOTH RUNNERS" claim tested behaviorally rather than by object identity.
  - Depends on: E-02
  - Expected outcome: the agy case passes after E-02 and fails against the pre-E-02 writer.
  - Execution state: pending

- [ ] E-07 ADD THE LEGACY-STATE TEST in `tests/test_runner_shared.py`: a state whose queue item carries ONLY a legacy `spec_edits_reconciliation` record `{"reconciled": True, "reasons": {"docs/B.spec.md": "x"}, "acks": {"docs/A.spec.md": "y"}, "refused": False}` (plus a plan file declaring `docs/A.spec.md`) renders `"modified (undeclared) -> docs/B.spec.md"` and `"declared, unmodified -> docs/A.spec.md"`, and a legacy `refused: True` record renders under `UNVERIFIED`. Assert `spec_edit_summary` does not mutate the state (compare a deep copy).
  - Depends on: E-03
  - Expected outcome: the legacy test passes after E-03 and fails before it.
  - Execution state: pending

- [ ] E-08 RUN THE BARE SUITE `python3 -m pytest` (no extra flags) before and after the change and compare failing NODE IDS, not counts.
  - Depends on: E-04, E-05, E-06, E-07
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE DEFINITION, BOUND BY BOTH HOSTS: shared runner behavior lives in `runner_shared` and each driver re-exports it with the `from agent_workflows.runner_shared import (name as name)` form; a per-driver second copy is the drift class `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` tracks and whose comment says "this set SHRINKING is progress".
- THE REPORT READS ONLY DURABLE STATE (`spec_edit_summary` docstring), so it renders identically from a normal exit, a signal path, and `print_status` on a finished run dir. That is why the reader must tolerate records already written to `state.json`, and why the fix must not depend on process memory.
- AN EMPTY RECONCILIATION IS AMBIGUOUS (clean versus precheck refused), so `record_item_spec_edits` asks `ipd_lifecycle.finalize_precheck` directly in the empty case; that logic is correct in the shared copy and must be preserved verbatim.
- The record is written BEFORE `driver_finalize` in both `execute_item_core` finalize branches, so a test may patch finalize without weakening what it proves about the record.
- `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json` holds an AST of `spec_edit_summary`, but `grep -rn "runnerlayer_rehomed" --include=*.py .` returns 0 hits at HEAD (its test was removed in `19313eed`), so editing that function trips no fingerprint gate. Do not "update" the orphaned fixture.
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All re-measured at HEAD `877545fc` (`git rev-parse --short HEAD`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.record_item_spec_edits` vs `runner_shared.spec_edit_summary` | The writer stores under `spec_edits_reconciliation` in shape `reconciled/reasons/acks/refused`; the reader reads `spec_edits` in shape `state/declared/modified_not_declared/declared_not_modified`. Backlog claim CONFIRMED. | `grep -n` output: `runner_shared.py:25587: item["spec_edits_reconciliation"] = record`, `runner_shared.py:30389: record = item.get("spec_edits") or None`, `oc_runipd.py:1258: item["spec_edits"] = record` |
| F-2 | HIGH | end-of-run report, both hosts | A finalized item is reported as never finalized. | probe: plan declares `docs/A.spec.md`, reconcile returns `{"docs/B.spec.md": "why"}`; item keys after record: `['spec_edits_reconciliation']`; report: `Reconciled 0 item(s); 0 could NOT be reconciled ...; 1 never finalized.` / `NOT FINALIZED: aaaaaa.` |
| F-3 | HIGH (worse than filed) | `render_stream.format_spec_edit_report` silence rule | An UNDECLARED spec change on a plan that declares no spec produces NO OUTPUT at all, because the misread record contributes nothing to `changed` and nothing was declared. The same queue with a reader-shaped record prints `UNDECLARED SPEC CHANGE(S)` / `aaaaaa modified (undeclared) -> docs/B.spec.md`. So the report is not merely mislabelled, it is silent on exactly its headline case, and the AGENTS.md sentence "silence means 'no declared spec edits'" is false. | probe 2: `undeclared-only run prints: []`; reader-shaped record prints the two lines quoted |
| F-4 | MED | `oc_runipd.record_item_spec_edits` | Dead fork: defined, re-exported to agy (`from agent_workflows.oc_runipd import (record_item_spec_edits as record_item_spec_edits,)`), called by nothing. `execute_item_core` resolves the bare name in `runner_shared`'s namespace (it is not in the `getattr(driver_module, ...)` list). Identity probe: `oc_runipd.record_item_spec_edits is runner_shared.record_item_spec_edits` -> `False`; agy's is oc's -> `True`. | `grep -rn "record_item_spec_edits(" agent_workflows/` shows only the two `def`s and the two `runner_shared` call sites |
| F-5 | MED | on-disk run state | Legacy records already exist, so a reader that only learns the new key would still misreport past runs via `print_status`. In the primary checkout's `.aw/records/runs/*/state.json`: 146 queue items carry `spec_edits_reconciliation` (single shape `('acks','reasons','reconciled','refused')`), 4 of them naming a `.spec.md`; 32 older items carry the pre-dedup `spec_edits` shape. | inline python scan over `state.json` files: `items with spec_edits_reconciliation: 146 ... items with spec_edits: 32`; `legacy records naming a .spec.md: 4` |
| F-6 | LOW | tests | No test covers any of this: the `st5klo` test files `tests/test_spec_impact_visibility.py` and `tests/test_spec_visibility.py` no longer exist (removed by `80db6750`/`19313eed`), and `grep -rn "spec_edit\|report_run_spec" tests/*.py` returns nothing. The dedup regression therefore landed green. | `ls tests/test_spec_impact_visibility.py` -> `No such file or directory`; `git log --oneline --diff-filter=D` on both paths names `19313eed` |
| F-7 | INFO | governing spec | Spec `25kzda` (`aw-run-deterministic-run-and-verify.spec.md`) does not describe the end-of-run spec-edit report: `grep -n -i "spec.edit\|SPEC EDITS\|spec_edit"` on it returns 0 lines. The behavior is specified by executed plan `st5klo` and the managed AGENTS.md text generated from `engine.py`; both already describe the CORRECT behavior, which this plan restores. No spec amendment is needed. | grep count `0` on the spec; `engine.py` string "BOTH RUNNERS ALSO REPORT AT RUN END" |

## Proposed changes (ordered, validatable)

1. E-01 reproduces F-1 through F-4 at the executing HEAD (or stops if fixed).
2. E-02 makes the shared recorder write the `spec_edit_record` shape under `spec_edits`.
3. E-03 makes the reader convert a legacy `spec_edits_reconciliation` record losslessly.
4. E-04 deletes the dead `oc_runipd` fork and binds both hosts to the shared recorder.
5. E-05/E-06 prove the finalize-to-report path on each host (A declared+modified, B modified-not-declared; and silence for a no-spec run).
6. E-07 proves legacy on-disk state renders correctly and the reader does not mutate state.
7. E-08 runs the bare suite before and after.

## Deferred / out of scope (with reason)

- Adding an explicit "declared and modified" line to the report. Today a declared spec that was modified is shown under `Declared:` and simply NOT under `DECLARED BUT NOT MODIFIED`; that is the `st5klo` design and the tests assert it by absence. See OQ-01.
  - Carrier-Declined: Wording change outside the defect; the current rendering is sufficient to state the fact and was reviewed under st5klo.
- Rewriting legacy run-state files on disk to the new key. The reader converts on read, which is lossless and keeps run directories immutable.
  - Carrier-Declined: A read-side conversion fully covers old run directories; mutating historical state buys nothing.
- Deleting the orphaned `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`. It is read by nothing, but removing test fixtures belongs with whoever trimmed the suite.
  - Carrier-Declined: Unrelated housekeeping with no behavioral effect; not an obligation of this defect.
- A spec paragraph in `25kzda` describing the end-of-run report. The behavior is contractually stated in AGENTS.md/`engine.py` and was never in the spec; adding it is a scope decision, not a fix.
  - Carrier-Declined: No spec currently governs this surface and the fix restores already-documented behavior.

## Scope check

- Over-scope: none. One recorder, one reader, one dead fork, and three test files.
- Under-scope: `render_stream.format_spec_edit_report` is deliberately NOT declared: its logic is correct and consumes the summary unchanged. If E-05 shows it must change, declare `agent_workflows/render_stream.py` before editing it.
- Scope-Paths justification: `runner_shared.py` holds the writer, the reader and `AGY_IMPORTS_FROM_OC_RUNIPD`; `oc_runipd.py` holds the dead fork and its re-export block; `agy_runipd.py` holds the import to repoint; the three test files receive E-05, E-06 and E-07 respectively.

## Required tests / validation

- E-05 (oc) and E-06 (agy): behavioral, through `execute_item` with a real begin receipt and real `compute_scope_reconciliation`, asserting A declared and modified, B modified-not-declared, 1 reconciled, none never-finalized; plus the silence case (a run with no spec edits prints nothing). Each must be shown FAILING against the pre-E-02 writer (stash-free: temporarily revert only the E-02 hunk in the working tree, run, restore).
- E-07: legacy-record conversion and non-mutation in `tests/test_runner_shared.py`.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: spec `25kzda` does not describe this report (F-7), so no `.spec.md` is edited and none is declared.
- AGENTS.md / `engine.py`: no edit. Their "BOTH RUNNERS ALSO REPORT AT RUN END" text is the intended behavior; this plan makes it true again.
- Docstrings: `runner_shared.record_item_spec_edits` gains the pre-dedup explanation (E-02); `runner_shared.spec_edit_summary` documents both legacy shapes (E-03); the `agy_runipd` import comment that cites `tm5vnx` is updated (E-04).

## Open questions

### OQ-01: Should the report add an explicit "declared and modified" list?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default NO. `runner_shared.spec_edit_record` has no `declared_and_modified` field and `render_stream.format_spec_edit_report` expresses that fact as "listed under Declared, absent from DECLARED BUT NOT MODIFIED"; the backlog item and AGENTS.md ask only for declared, changed and undeclared-changed to be reported, which the existing shape already carries. Tests assert the fact by absence. A maintainer wanting a positive line can file it as a follow-up wording change.

### OQ-02: Which key should the unified record live under?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `spec_edits`. It is the key the reader, `report_run_spec_edits`'s docstring ("An older run directory carrying no `spec_edits` key"), the pre-dedup writer, and the 32 older on-disk items already use; `spec_edits_reconciliation` has no reader anywhere in the package (F-4 grep). Reading the legacy key on the side (E-03) covers the 146 items written in between.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `grep -n` output showing `item["spec_edits_reconciliation"] = record` in `runner_shared.record_item_spec_edits` and `item.get("spec_edits")` in `runner_shared.spec_edit_summary`; paste the probe output showing `NOT FINALIZED` for the finalized item and `[]` for the undeclared-only run; paste the grep proving `oc_runipd.record_item_spec_edits` has no call site.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `runner_shared.record_item_spec_edits` showing `spec_edit_record(...)` and `item["spec_edits"] = record`, with the `finalize_precheck` refused branch unchanged; paste `grep -n "spec_edits_reconciliation" agent_workflows/*.py` showing only the E-03 legacy read remains.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of `runner_shared.spec_edit_summary` showing the legacy conversion through `spec_edit_record`; paste `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k legacy` passing (this is E-07's test and is the executable proof of E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -rn "def record_item_spec_edits" agent_workflows/` showing exactly one hit (in `runner_shared.py`); paste `python3 -c "from agent_workflows import oc_runipd, agy_runipd, runner_shared as r; print(oc_runipd.record_item_spec_edits is r.record_item_spec_edits is agy_runipd.record_item_spec_edits, 'record_item_spec_edits' in r.AGY_IMPORTS_FROM_OC_RUNIPD)"` printing `True False`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k <new test names>` showing both new tests passed; then paste the SAME command FAILING with only the E-02 hunk temporarily reverted (the A/B test must fail on the `modified (undeclared) -> docs/B.spec.md` or `NOT FINALIZED` assertion), and the passing run again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k <new test name>` passing, and the same command failing with the E-02 hunk temporarily reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k <new test names>` passing, and the same command failing with the E-03 hunk temporarily reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. Do not move this plan to `executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries observed evidence. This plan inherits `- Blocks-Release: next` from backlog `tm5vnx`, so the next release is gated on it.
