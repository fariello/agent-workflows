# IPD: Make the end-of-run spec-edit report read the record execute_item_core actually writes

- Date: 2026-09-24
- Kind: child
- Concern: THE END-OF-RUN DECLARED-SPEC-EDIT REPORT HAS BEEN INERT ON BOTH HOSTS SINCE THE `execute_item` DEDUP, AND ITS MOST IMPORTANT CASE IS NOW SILENT. `runner_shared.record_item_spec_edits` is the copy `runner_shared.execute_item_core` calls at both finalize sites (lane and main tree), and it stores `{"reconciled", "reasons", "acks", "refused"}` under `item["spec_edits_reconciliation"]`. The ONLY reader, `runner_shared.spec_edit_summary` (reached through `runner_shared.report_run_spec_edits` at all six summary sites, three per host), reads `item.get("spec_edits")` and expects the `runner_shared.spec_edit_record` shape `{"state", "declared", "modified_not_declared", "declared_not_modified"}`. So every item that DID finalize is reported `not_finalized`, and because `render_stream.format_spec_edit_report` stays silent when nothing is declared, changed, unfulfilled, or refused, a run whose only spec event is an UNDECLARED spec modification prints NOTHING. That is precisely the case the report exists for, and it inverts the managed AGENTS.md promise ("INCLUDING a spec that was modified WITHOUT being declared ... silence means 'no declared spec edits' and never 'the announcer broke'"). Root cause: commit `70a2059f` ("deduplicate execute_item into runner_shared.execute_item_core") moved the call onto a DIVERGED shared copy; the `oc_runipd.record_item_spec_edits` copy that writes the reader's key and shape is now called by nothing.
- Scope: Make ONE record, written by the ONE recorder the runners call and read by the ONE reader. IN: (a) `runner_shared.record_item_spec_edits` builds its record with `runner_shared.spec_edit_record` (so it carries `declared`/`modified_not_declared`/`declared_not_modified` and a `state` constant) and stores it under `item["spec_edits"]`, keeping its existing refused-detection logic; (b) `runner_shared.spec_edit_summary` tolerates the legacy `spec_edits_reconciliation` record already on disk by converting it losslessly through `spec_edit_record`; (c) retire the dead `oc_runipd.record_item_spec_edits` fork so the two definitions cannot diverge again (both hosts bind the shared one; `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` shrinks by one); (d) behavioral tests driving the real finalize-to-report path on both hosts, plus the silence and legacy cases. OUT: changing the report's wording or adding a new "declared and modified" section (OQ-01); changing `compute_scope_reconciliation` or `finalize_precheck`; the start-of-run announcement (already correct, `st5klo`).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_shared.py
- Item-Dependencies: executed:cdxcbh
- Status: executed
- Readiness: go-pending-approval
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
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 9npssm verified (set specrpt, attempt 2).
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 readiness re-check (opencode/its_direct/pt3-claude-opus-5.5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-09-25, findings PR-001..F-7. Recomputed at HEAD `7835a4d5`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-25 same-status (aw set): OQ-03 resolved by maintainer 2026-09-25: run cdxcbh first

- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review; REVIEWED - OPEN QUESTIONS; PR-001..PR-005; PR-001 is a BLOCKER left OPEN and escalated as OQ-03 (Blocking: yes, Finding: F-8), so Readiness is no-go pending one human ordering decision. Every authored finding reproduces at HEAD 0a06a2d6, including the exact report strings: a finalized item reports NOT FINALIZED, and an undeclared-spec-only run prints literally nothing while the same queue with a reader-shaped record prints UNDECLARED SPEC CHANGE(S). PR-001 found that this plan's E-04 and pending plan cdxcbh's E-05 both edit AGY_IMPORTS_FROM_OC_RUNIPD, with neither ordered, and that this-plan-first makes cdxcbh's recorded expected outcome FALSE. PR-002 found F-5's on-disk counts unverifiable where the plan executes (.aw/records/runs/ is gitignored and absent in a lane). PR-003 corrected F-7's grep count while confirming its conclusion.

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog tm5vnx; re-measured at HEAD 877545fc that the shared recorder writes `spec_edits_reconciliation` while the only reader reads `spec_edits`, that an undeclared-spec-only run prints nothing at all, and that 146 legacy records already sit in local run state.

## Goal

Make `aw oc run` and `aw agy run` actually report, at run end, which specs each finalized item declared and which it changed (including an undeclared spec change), by having the one recorder both runners call write the exact record the one reader consumes, while still rendering run directories written by the broken recorder.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce before changing

- [x] E-01 RE-MEASURE THE DEFECT at the executing HEAD. (1) `grep -n "spec_edits_reconciliation\|\"spec_edits\"\|item.get(\"spec_edits\")" agent_workflows/*.py` and confirm the writer/reader split. (2) Run a throwaway probe (under `/tmp/`) that calls `runner_shared.record_item_spec_edits` on a plan declaring `docs/A.spec.md` with an injected `reconcile` returning `({"docs/B.spec.md": "why"}, {})`, then `runner_shared.report_run_spec_edits` on `{"repo": ..., "queue": [item]}`; confirm the item is reported `NOT FINALIZED` and that a plan declaring NO spec yields `[]` (silent) even though B was changed. (3) Confirm `oc_runipd.record_item_spec_edits` has no caller (`grep -rn "record_item_spec_edits(" agent_workflows/`), and that `agy_runipd` imports it from `oc_runipd`. If the writer and reader already agree, STOP and report: the defect is fixed.
  DO NOT ATTEMPT TO RE-DERIVE F-5's ON-DISK COUNTS, and do not read the main checkout to get them. `.aw/records/runs/` is GITIGNORED, so in a lane or a fresh clone it does not exist (measured at review: absent here), and the 146/32/4 figures are one machine's local state rather than a repository fact. Nothing in E-02..E-07 depends on them: E-03's conversion is proven by E-07's SYNTHETIC legacy record. If you can see run directories, reporting a refreshed count is welcome as context; if you cannot, say so in one line and continue.
  ALSO MEASURE THE CROSS-PLAN STATE E-04 DEPENDS ON: paste `python3 -c "from agent_workflows import runner_shared as r; print(sorted(r.AGY_IMPORTS_FROM_OC_RUNIPD))"`. If it still holds the three recovery names, plan `cdxcbh` has not executed and E-04's collision note applies; if it holds only `record_item_spec_edits`, `cdxcbh` has run and E-04 simply empties the set.
  - Depends on: none
  - Expected outcome: the three observations pasted, matching the Findings table, or a STOP report; plus the `AGY_IMPORTS_FROM_OC_RUNIPD` membership, and an explicit line on whether F-5's counts were re-derivable.
  - Execution state: performed

### Task group 2: one record

- [x] E-02 CHANGE THE WRITER. In `runner_shared.record_item_spec_edits`, keep the existing `reconcile` call and the `finalize_precheck` refused-detection exactly as they are, then build the record with `spec_edit_record(plan_path, reasons, acks, state=SPEC_RECONCILE_REFUSED if refused else SPEC_RECONCILED)` and store it under `item["spec_edits"]`. Stop writing `spec_edits_reconciliation` (no other reader exists; see F-4). The declared set comes from `declared_spec_paths` over the plan text at finalize time and the modified sets from the `.spec.md` filter over `reasons`/`acks`, which is exactly the computation the pre-dedup `oc_runipd.record_item_spec_edits` performed; reuse it, do not re-derive a diff. Port the pre-dedup docstring's two load-bearing explanations (why it is recorded durably on the queue item, and why refused is detected rather than inferred from emptiness) onto the shared function.
  - Depends on: E-01
  - Expected outcome: after one finalize, the queue item carries exactly one spec record, under `spec_edits`, in the `spec_edit_record` shape; the refused path still records `state: "refused"`.
  - Execution state: performed

- [x] E-03 MAKE THE READER TOLERATE LEGACY ON-DISK STATE. In `runner_shared.spec_edit_summary`, when `item.get("spec_edits")` is absent but `item.get("spec_edits_reconciliation")` is a mapping, convert it: `refused: true` maps to `SPEC_RECONCILE_REFUSED`; otherwise call `spec_edit_record(plan_path, legacy["reasons"], legacy["acks"], state=SPEC_RECONCILED)` using the `plan_path` the function already resolves through `queue_plan_path` (fall back to an empty declared list when it is None). The conversion is lossless because the legacy maps are keyed by path, which is all `spec_edit_record` reads. Update the docstring's "An older run directory carrying no `spec_edits` key" sentence to describe both legacy shapes. Do NOT write the converted record back to state (the reader stays read-only).
  - Depends on: E-02
  - Expected outcome: `print_status` / the end report on a run directory written between `70a2059f` and this fix renders its reconciled items correctly instead of as never-finalized.
  - Execution state: performed

- [x] E-04 RETIRE THE DEAD FORK. Delete `oc_runipd.record_item_spec_edits` and re-export the shared one in `oc_runipd`'s existing `from agent_workflows.runner_shared import (... as ...)` block (so `oc_runipd.record_item_spec_edits is runner_shared.record_item_spec_edits`); move `agy_runipd`'s import of that name from its `oc_runipd` statement into its `runner_shared` statement and update the adjacent comment that names `tm5vnx`; remove `"record_item_spec_edits"` from `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` (its own comment says shrinking is progress). Check `oc_runipd.spec_edit_record` stays imported only if still used; drop an unused re-export only if nothing imports it from `oc_runipd`.
  THIS ITEM COLLIDES WITH PENDING PLAN `cdxcbh` (Set `recovone`), AND THE COLLISION IS ORDER-DEPENDENT, SO READ THIS BEFORE EDITING THE CONSTANT. `cdxcbh` E-05 removes the OTHER THREE names and asserts, as its expected outcome, `AGY_IMPORTS_FROM_OC_RUNIPD == frozenset({"record_item_spec_edits"})`. This item removes exactly that name. Measured at review: the constant is `{build_verify_and_continue_notice, classify_recovery_disposition, record_item_spec_edits, route_recovery_turn}`; if THIS plan lands first the set becomes EMPTY and `cdxcbh`'s equality assertion is FALSE, while if `cdxcbh` lands first its assertion holds and this plan then empties the set cleanly. Both plans declare `- Item-Dependencies: none`, so nothing orders them today.
  WHAT TO DO, and it is not "adjust the other plan" (its record is not yours to edit): if `AGY_IMPORTS_FROM_OC_RUNIPD` no longer contains the other three when you arrive, `cdxcbh` has already executed and you simply empty the set. If it DOES still contain them, you are running first, so leave a note in your commit message that `cdxcbh` E-05's expected-outcome equality must read `frozenset()` rather than `frozenset({"record_item_spec_edits"})`, and REPORT it, so a human retargets that plan rather than an executor discovering it as a failed validation mid-run. Do NOT weaken this item to avoid the collision: the name's removal is the point of E-04.
  THE CONSTANT MAY LEGITIMATELY BECOME EMPTY, so check what an empty `frozenset()` breaks before assuming it is fine: re-read the constant's own comment (which says shrinking is progress) and confirm no consumer treats emptiness specially. Measured at review, `grep -rn "AGY_IMPORTS_FROM_OC_RUNIPD" tests/ agent_workflows/` finds only the definition itself, so there is no consumer to break; re-derive that rather than trusting it.
  - Depends on: E-02
  - Expected outcome: exactly one `def record_item_spec_edits` in the package; `oc_runipd.record_item_spec_edits is agy_runipd.record_item_spec_edits is runner_shared.record_item_spec_edits` is True; `AGY_IMPORTS_FROM_OC_RUNIPD` no longer contains `record_item_spec_edits`, with its remaining membership REPORTED (it is `frozenset()` if `cdxcbh` already ran and the three recovery names otherwise), and the `cdxcbh` interaction stated either way.
  - Execution state: performed

### Task group 3: prove it on the real path

- [x] E-05 ADD THE OC BEHAVIORAL TEST in `tests/test_oc_runipd.py`, beside `SelfFinalizeWiringTests`, reusing `_init_repo_with_conforming_plan`'s shape with a plan variant whose `- Scope-Paths:` is `docs/A.spec.md`. Drive `driver.execute_item(run_dir, state, item, recovery=False)` with the REAL `driver_begin` (so a real receipt exists and the real `compute_scope_reconciliation` runs), a fake `run_opencode` that edits and COMMITS both `docs/A.spec.md` and `docs/B.spec.md`, an outcome file as the neighbouring tests write it, `no_audit: True`, `isolate_worktree: False`; `driver_finalize` may be patched to `(0, "finalized")` because the record is written BEFORE finalize. Then call `driver.report_run_spec_edits(state, stream=buf)` and assert: `"declared -> docs/A.spec.md"` present; `"declared, unmodified -> docs/A.spec.md"` ABSENT (A was declared and modified); `"modified (undeclared) -> docs/B.spec.md"` present; `"Reconciled 1 item(s)"` present; `"NOT FINALIZED"` absent. Also assert the queue item has `spec_edits` and no `spec_edits_reconciliation`. In the same class add the SILENCE case: plan declaring `src/` only, fake turn committing `src/demo.txt`, and assert `report_run_spec_edits` returns `[]` and wrote nothing to the stream.
  - Depends on: E-02
  - Expected outcome: both tests pass after E-02 and the first FAILS against the pre-E-02 writer (the item reports as never finalized and B is not named).
  - Execution state: performed

- [x] E-06 ADD THE AGY PARITY TEST in `tests/test_agy_runipd_cli.py`, using that file's `_state_and_item` harness and patching `agy_runipd.run_agy_turn` the way its existing wiring tests do, with the same A-declared / A+B-modified fixture and the same four report assertions. This is what makes the AGENTS.md "BOTH RUNNERS" claim tested behaviorally rather than by object identity.
  - Depends on: E-02
  - Expected outcome: the agy case passes after E-02 and fails against the pre-E-02 writer.
  - Execution state: performed

- [x] E-07 ADD THE LEGACY-STATE TEST in `tests/test_runner_shared.py`: a state whose queue item carries ONLY a legacy `spec_edits_reconciliation` record `{"reconciled": True, "reasons": {"docs/B.spec.md": "x"}, "acks": {"docs/A.spec.md": "y"}, "refused": False}` (plus a plan file declaring `docs/A.spec.md`) renders `"modified (undeclared) -> docs/B.spec.md"` and `"declared, unmodified -> docs/A.spec.md"`, and a legacy `refused: True` record renders under `UNVERIFIED`. Assert `spec_edit_summary` does not mutate the state (compare a deep copy).
  - Depends on: E-03
  - Expected outcome: the legacy test passes after E-03 and fails before it.
  - Execution state: performed

- [x] E-08 RUN THE BARE SUITE `python3 -m pytest` (no extra flags) before and after the change and compare failing NODE IDS, not counts.
  - Depends on: E-04, E-05, E-06, E-07
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: performed

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
| F-5 | MED | on-disk run state | Legacy records already exist, so a reader that only learns the new key would still misreport past runs via `print_status`. In the primary checkout's `.aw/records/runs/*/state.json`: 146 queue items carry `spec_edits_reconciliation` (single shape `('acks','reasons','reconciled','refused')`), 4 of them naming a `.spec.md`; 32 older items carry the pre-dedup `spec_edits` shape. NOT RE-VERIFIABLE IN A LANE OR A FRESH CLONE, stated at review rather than left as a trap: `.aw/records/runs/` is GITIGNORED, so it is absent from a worktree entirely (measured at review: the directory does not exist here). The COUNTS are therefore a property of one machine's local state and must never become a pass bar; what E-03 and E-07 actually need is only that the legacy SHAPE exists and is convertible, which E-07 proves from a synthetic record with no dependency on any run directory. If the counts cannot be re-derived at execution, say so and proceed; do not treat their absence as drift. | inline python scan over `state.json` files in the primary checkout: `items with spec_edits_reconciliation: 146 ... items with spec_edits: 32`; `legacy records naming a .spec.md: 4`. At review, in this lane: `.aw/records/runs/` ABSENT (gitignored), so the scan is unrunnable and the legacy shape is instead pinned by E-07's synthetic fixture |
| F-6 | LOW | tests | No test covers any of this: the `st5klo` test files `tests/test_spec_impact_visibility.py` and `tests/test_spec_visibility.py` no longer exist (removed by `80db6750`/`19313eed`), and `grep -rn "spec_edit\|report_run_spec" tests/*.py` returns nothing. The dedup regression therefore landed green. | `ls tests/test_spec_impact_visibility.py` -> `No such file or directory`; `git log --oneline --diff-filter=D` on both paths names `19313eed` |
| F-7 | INFO | governing spec | Spec `25kzda` (`aw-run-deterministic-run-and-verify.spec.md`) does not describe the end-of-run spec-edit report. CONCLUSION CONFIRMED AT REVIEW, COUNT CORRECTED: the grep returns 1 line, not 0, but that line is unrelated prose about why a spec amendment is recorded at all ("WHY IT EXISTS, recorded because a spec edit changes the contract every plan is reviewed against", inside the gate-2 adjudication section) and describes no report. So no `.spec.md` governs this surface and no amendment is needed, exactly as the plan concludes. | `grep -n -i "spec.edit\|SPEC EDITS\|spec_edit"` on the spec -> 1 hit, in the gate-2 adjudication prose, not a report description; `engine.py` string "BOTH RUNNERS ALSO REPORT AT RUN END" |
| F-8 | BLOCKER (added at review) | plan `E-04`; pending plan `cdxcbh` (Set `recovone`) E-05; `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` | TWO RELEASE-GATING PENDING PLANS EDIT THE SAME CONSTANT AND ONE ORDER MAKES THE OTHER'S VALIDATION FALSE, with nothing ordering them. `cdxcbh` E-05 removes the three recovery names and states as its expected outcome `AGY_IMPORTS_FROM_OC_RUNIPD == frozenset({"record_item_spec_edits"})`; THIS plan's E-04 removes precisely `record_item_spec_edits`. Measured: the constant currently holds all four. If this plan lands first the set is EMPTY and `cdxcbh`'s equality assertion is false, so its executor hits a failed validation on work that is actually correct; if `cdxcbh` lands first, both hold. BOTH plans declare `- Item-Dependencies: none`, so the runner's dependency-depth sort imposes no order between them and either sequence can occur. This is not a file-overlap concern (lanes and merge-and-revalidate handle that) but a CONTENT contradiction between two recorded expected outcomes. | `sorted(AGY_IMPORTS_FROM_OC_RUNIPD)` -> all four names; `cdxcbh` E-05 expected outcome quotes the one-element frozenset; both plans' `- Item-Dependencies: none`; simulated both orders, only `cdxcbh`-first leaves both assertions true |
| F-9 | MED (added at review) | `.aw/records/runs/` (gitignored); plan `F-5` and `E-01` | F-5'S EVIDENCE CANNOT BE RE-DERIVED WHERE THIS PLAN WILL EXECUTE. `.aw/records/runs/` is gitignored, so in a lane worktree or a fresh clone it is absent entirely (measured at review: the directory does not exist here), making the 146/32/4 counts a property of one machine rather than a repository fact. E-01 as authored asked for observations "matching the Findings table", which invites an executor to treat an unobtainable count as drift and STOP. Nothing in E-02..E-07 actually depends on those counts: E-03's conversion is proven by E-07's synthetic legacy record. | `.aw/records/runs/` absent in this worktree; `.gitignore` carries `.aw/records/runs/`; E-07's fixture is a hand-built legacy dict needing no run directory |
| F-10 | LOW (added at review) | `runner_shared.compute_scope_reconciliation`; plan `E-05`'s absence assertion | E-05 ASSERTS AN ABSENCE, AND THE ABSENCE IS SOUND BY CONSTRUCTION RATHER THAN BY LUCK, which is worth recording because an absence assertion is the easy kind to get wrong. E-05 requires `"declared, unmodified -> docs/A.spec.md"` to be ABSENT when A was declared AND modified. Verified: `compute_scope_reconciliation` builds `reasons` from `out_of_scope_paths` and `acks` from `in_scope_unmodified`, so a declared-and-modified path is in NEITHER map, hence in neither `modified_not_declared` nor `declared_not_modified`, and the renderer has no fourth section that could name it. It will appear only under `declared ->`, which is what E-05 asserts positively. | `reasons = {p: ... for p in out_of_scope}`, `acks = {p: ... for p in in_scope_unmodified}`; `format_spec_edit_report` has exactly three per-path sections plus the counts line |

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
- Status: resolved
- Owner: maintainer
- Carrier-Declined: The maintainer declined the change outright, so nothing remains owed.
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-25 (via /askme): NO, keep the current wording. The fix ships as planned; a declared-and-changed spec stays readable as "listed under Declared, absent from DECLARED BUT NOT MODIFIED", and no follow-up is filed. Reason: the fact is already legible, and a positive line would need a new record field and computation for no functional gain. The original analysis follows. Default NO, and the DEFAULT NEEDS NO DECISION TO EXECUTE THIS PLAN, which is why it is `Blocking: no`: doing nothing is the default, the plan changes no report wording, and the question is a pure ADDITIVE wording preference that can be answered after this fix lands. `runner_shared.spec_edit_record` has no `declared_and_modified` field and `render_stream.format_spec_edit_report` expresses that fact as "listed under Declared, absent from DECLARED BUT NOT MODIFIED"; the backlog item and AGENTS.md ask only for declared, changed and undeclared-changed to be reported, which the existing shape already carries. Tests assert the fact by absence. A maintainer wanting a positive line can file it as a follow-up wording change.
  VERIFIED AT REVIEW, so the maintainer is answering on facts rather than on the author's summary. `spec_edit_record` returns exactly `{state, declared, modified_not_declared, declared_not_modified}` and no fifth key; `format_spec_edit_report` has exactly three per-path sections (`declared ->`, `modified (undeclared) ->`, `declared, unmodified ->`) plus the counts line; and a declared-AND-modified spec appears in NEITHER `reasons` NOR `acks`, because `compute_scope_reconciliation` builds `reasons` from `out_of_scope_paths` and `acks` from `in_scope_unmodified`, so such a path is absent from both by construction. That is what makes the absence assertion in E-05 sound rather than incidental, and it also means a positive line would need a NEW field and a new computation, not just a new string - worth knowing before answering.

### OQ-03: In which order must this plan and `cdxcbh` execute, given both edit `AGY_IMPORTS_FROM_OC_RUNIPD` and one order falsifies `cdxcbh`'s recorded expected outcome?

- Blocking: yes
- Finding: PR-001
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-25 (via /askme): option (1), run `cdxcbh` first. Applied as `- Item-Dependencies: executed:cdxcbh` with `aw ipd dependencies set` (commit `eec5dc49`), so the runner will not dispatch this plan until `cdxcbh` is executed and both plans' recorded expected outcomes hold. Reason given: it is the smallest change, enforced automatically, and edits only this plan. Consequence for E-04: when it executes, `AGY_IMPORTS_FROM_OC_RUNIPD` will already hold only `record_item_spec_edits`, and E-04 empties it. The original analysis follows. NEEDS A HUMAN DECISION because it is an ordering and priority question across two separate release-gating plans, and because the fix for one option is an edit to ANOTHER plan's record, which this plan's executor has no authority to make. THE FACTS, measured at review: `AGY_IMPORTS_FROM_OC_RUNIPD` currently holds all four names; `cdxcbh` (Set `recovone`) E-05 removes three of them and records as its expected outcome `AGY_IMPORTS_FROM_OC_RUNIPD == frozenset({"record_item_spec_edits"})`; this plan's E-04 removes exactly that remaining name. If `cdxcbh` executes first, both plans' assertions hold. If THIS plan executes first, the constant becomes `frozenset()` and `cdxcbh`'s executor meets a FALSE validation on work that is nevertheless correct. Both plans declare `- Item-Dependencies: none`, so the runner's dependency-depth sort imposes no order and either sequence can occur unattended. No consumer reads the constant (`grep -rn` finds only its definition), so an empty set breaks no code; the only casualty is a plan's recorded expectation.
  THE THREE OPTIONS, so the decision is concrete. (1) ORDER THEM: add `- Item-Dependencies: executed:cdxcbh` to THIS plan, which is the smallest change, is enforced at dispatch, and needs no edit to `cdxcbh`. (2) RETARGET `cdxcbh`: amend its E-05 expected outcome to `frozenset()` and let either order work; this edits a plan currently `reviewed`/`go-pending-approval` and so needs its own sign-off. (3) ACCEPT THE RACE: execute in any order and let whichever executor hits the stale assertion report it; cheapest now, but it spends an agent turn discovering a known contradiction. RECOMMENDATION: option (1), because it is the one change that cannot be wrong in either order and because `cdxcbh` is the plan whose assertion is fragile. This plan does NOT apply it unilaterally: adding a dependency changes what the runner will execute and when, which is the maintainer's call.
- Carrier: 9npssm

### OQ-02: Which key should the unified record live under?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `spec_edits`. It is the key the reader, `report_run_spec_edits`'s docstring ("An older run directory carrying no `spec_edits` key"), the pre-dedup writer, and the 32 older on-disk items already use; `spec_edits_reconciliation` has no reader anywhere in the package (F-4 grep). Reading the legacy key on the side (E-03) covers the 146 items written in between.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `grep -n` output showing `item["spec_edits_reconciliation"] = record` in `runner_shared.record_item_spec_edits` and `item.get("spec_edits")` in `runner_shared.spec_edit_summary`; paste the probe output showing `NOT FINALIZED` for the finalized item and `[]` for the undeclared-only run; paste the grep proving `oc_runipd.record_item_spec_edits` has no call site.
  - Observed evidence: Verified at HEAD: writer/reader split confirmed, probe produced NOT FINALIZED and [], no call sites for oc_runipd fork. Details pasted below.
    ```
    agent_workflows/oc_runipd.py:1255:    item["spec_edits"] = record
    agent_workflows/runner_shared.py:27054:    item["spec_edits_reconciliation"] = record
    agent_workflows/runner_shared.py:31989:        record = item.get("spec_edits") or None
    ```
    Probe output (simulated item finalized with injected reasons={"docs/B.spec.md": "why"}):
    ```
    item keys after record: ['id6', 'plan_path', 'spec_edits_reconciliation']
    report with declared A, changed B:
    SPEC EDITS THIS RUN
      Declared: 1 plan(s) declared edits to 1 specification file(s).
        01test declared -> docs/A.spec.md
      Reconciled 0 item(s); 0 could NOT be reconciled (finalize precheck refused); 1 never finalized.
      NOT FINALIZED: 01test.
    ```
    Undeclared-only run output:
    `undeclared-only run lines: []`
    `undeclared-only run output: ''`

    Call sites of `record_item_spec_edits`:
    ```
    agent_workflows/oc_runipd.py:1199:def record_item_spec_edits(
    agent_workflows/runner_shared.py:27024:def record_item_spec_edits(
    agent_workflows/runner_shared.py:29060:                record_item_spec_edits(
    agent_workflows/runner_shared.py:29286:                record_item_spec_edits(
    ```
    (showing no call site for `oc_runipd.record_item_spec_edits`; agy_runipd imported from oc_runipd but execute_item_core used runner_shared's definition).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of `runner_shared.record_item_spec_edits` showing `spec_edit_record(...)` and `item["spec_edits"] = record`, with the `finalize_precheck` refused branch unchanged; paste `grep -n "spec_edits_reconciliation" agent_workflows/*.py` showing only the E-03 legacy read remains.
  - Observed evidence: Verified: runner_shared.record_item_spec_edits writes spec_edit_record under item["spec_edits"] with precheck refused branch preserved; only legacy read remains in runner_shared.spec_edit_summary. Details pasted below.
    Diff of `runner_shared.record_item_spec_edits`:
    ```diff
    @@ -27045,13 +27064,13 @@ def record_item_spec_edits(
                         refused = True
                 except Exception:
                     refused = True
    -    record: dict[str, Any] = {
    -        "reconciled": not refused,
    -        "reasons": dict(reasons),
    -        "acks": dict(acks),
    -        "refused": refused,
    -    }
    -    item["spec_edits_reconciliation"] = record
    +    record = spec_edit_record(
    +        plan_path,
    +        reasons,
    +        acks,
    +        state=SPEC_RECONCILE_REFUSED if refused else SPEC_RECONCILED,
    +    )
    +    item["spec_edits"] = record
         return record
    ```
    `finalize_precheck` call unchanged in the `if not refused and not reasons and not acks:` block.

    `grep -n "spec_edits_reconciliation" agent_workflows/*.py`:
    ```
    agent_workflows/runner_shared.py:31995:    `spec_edits` key converts a legacy `spec_edits_reconciliation` record losslessly through
    agent_workflows/runner_shared.py:32014:        if not record and isinstance(item.get("spec_edits_reconciliation"), Mapping):
    agent_workflows/runner_shared.py:32015:            legacy = item["spec_edits_reconciliation"]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff of `runner_shared.spec_edit_summary` showing the legacy conversion through `spec_edit_record`; paste `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k legacy` passing (this is E-07's test and is the executable proof of E-03).
  - Observed evidence: Verified: runner_shared.spec_edit_summary converts legacy spec_edits_reconciliation records through spec_edit_record; legacy test passes in tests/test_runner_shared.py. Details pasted below.
    Diff of `runner_shared.spec_edit_summary`:
    ```diff
    @@ -31987,6 +32011,22 @@ def spec_edit_summary(repo: Path, state: "Mapping[str, Any]") -> dict[str, Any]:
                 if specs:
                     declared[id6] = specs
             record = item.get("spec_edits") or None
    +        if not record and isinstance(item.get("spec_edits_reconciliation"), Mapping):
    +            legacy = item["spec_edits_reconciliation"]
    +            if legacy.get("refused"):
    +                record = spec_edit_record(
    +                    plan_path,
    +                    legacy.get("reasons") or {},
    +                    legacy.get("acks") or {},
    +                    state=SPEC_RECONCILE_REFUSED,
    +                )
    +            else:
    +                record = spec_edit_record(
    +                    plan_path,
    +                    legacy.get("reasons") or {},
    +                    legacy.get("acks") or {},
    +                    state=SPEC_RECONCILED,
    +                )
             if not record:
    ```
    Test execution:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k LegacySpecEditsStateTests
    .                                                                        [100%]
    1 passed, 92 deselected in 0.67s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `grep -rn "def record_item_spec_edits" agent_workflows/` showing exactly one hit (in `runner_shared.py`); paste `python3 -c "from agent_workflows import oc_runipd, agy_runipd, runner_shared as r; print(oc_runipd.record_item_spec_edits is r.record_item_spec_edits is agy_runipd.record_item_spec_edits, 'record_item_spec_edits' in r.AGY_IMPORTS_FROM_OC_RUNIPD)"` printing `True False`.
  - Observed evidence: Verified: exactly one def record_item_spec_edits in agent_workflows/runner_shared.py at runner_shared.record_item_spec_edits; identity check True False. Details pasted below.
    `grep -rn "def record_item_spec_edits" agent_workflows/`:
    ```
    agent_workflows/runner_shared.py:27020:def record_item_spec_edits(
    ```
    Python check:
    ```
    $ python3 -c "from agent_workflows import oc_runipd, agy_runipd, runner_shared as r; print(oc_runipd.record_item_spec_edits is r.record_item_spec_edits is agy_runipd.record_item_spec_edits, 'record_item_spec_edits' in r.AGY_IMPORTS_FROM_OC_RUNIPD)"
    True False
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k <new test names>` showing both new tests passed; then paste the SAME command FAILING with only the E-02 hunk temporarily reverted (the A/B test must fail on the `modified (undeclared) -> docs/B.spec.md` or `NOT FINALIZED` assertion), and the passing run again after restoring.
  - Observed evidence: Verified: SpecEditReportBehavioralTests in tests/test_oc_runipd.py passes with fix (2 passed), fails with E-02 reverted (1 failed on 'spec_edits' not found in item / spec_edits_reconciliation present), and passes restored (2 passed). Details pasted below.
    Passing run with fix:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k SpecEditReportBehavioralTests
    ..                                                                       [100%]
    2 passed, 164 deselected in 2.14s
    ```
    Failing run with E-02 hunk temporarily reverted:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k SpecEditReportBehavioralTests
    .F                                                                       [100%]
    =================================== FAILURES ===================================
    _ SpecEditReportBehavioralTests.test_execute_item_spec_edits_report_declared_and_undeclared _
    ...
    >           self.assertIn("spec_edits", item)
    E           AssertionError: 'spec_edits' not found in {'position': 1, 'id6': 'spe001', ... 'spec_edits_reconciliation': {'reconciled': True, 'reasons': {'docs/B.spec.md': "changed by the plan's approved execution (auto-reconciled by aw oc run)"}, 'acks': {}, 'refused': False}}
    =========================== short test summary info ============================
    FAILED tests/test_oc_runipd.py::SpecEditReportBehavioralTests::test_execute_item_spec_edits_report_declared_and_undeclared
    1 failed, 1 passed, 164 deselected in 2.19s
    ```
    Restored passing run:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py -o addopts="" -q -k SpecEditReportBehavioralTests
    ..                                                                       [100%]
    2 passed, 164 deselected in 2.14s
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k <new test name>` passing, and the same command failing with the E-02 hunk temporarily reverted.
  - Observed evidence: Verified: test_execute_item_spec_edits_report_parity_with_oc in tests/test_agy_runipd_cli.py passes with fix (1 passed), fails with E-02 reverted (1 failed on 'spec_edits' not found in item / spec_edits_reconciliation present), and passes restored (1 passed). Details pasted below.
    Passing run with fix:
    ```
    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k test_execute_item_spec_edits_report_parity_with_oc
    .                                                                        [100%]
    1 passed, 56 deselected in 1.54s
    ```
    Failing run with E-02 hunk temporarily reverted:
    ```
    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k test_execute_item_spec_edits_report_parity_with_oc
    F                                                                        [100%]
    =================================== FAILURES ===================================
    ___ AgySelfFinalizeTests.test_execute_item_spec_edits_report_parity_with_oc ____
    ...
    >           self.assertIn("spec_edits", item)
    E           AssertionError: 'spec_edits' not found in {'position': 1, 'id6': 'agy001', ... 'spec_edits_reconciliation': {'reconciled': True, 'reasons': {'docs/B.spec.md': "changed by the plan's approved execution (auto-reconciled by aw agy run)"}, 'acks': {}, 'refused': False}}
    =========================== short test summary info ============================
    FAILED tests/test_agy_runipd_cli.py::AgySelfFinalizeTests::test_execute_item_spec_edits_report_parity_with_oc
    1 failed, 56 deselected in 1.18s
    ```
    Restored passing run:
    ```
    $ python3 -m pytest tests/test_agy_runipd_cli.py -o addopts="" -q -k test_execute_item_spec_edits_report_parity_with_oc
    .                                                                        [100%]
    1 passed, 56 deselected in 1.54s
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k <new test names>` passing, and the same command failing with the E-03 hunk temporarily reverted.
  - Observed evidence: Verified: LegacySpecEditsStateTests in tests/test_runner_shared.py passes with fix (1 passed), fails with E-03 reverted (1 failed on AssertionError: 0 != 1), and passes restored (1 passed). Details pasted below.
    Passing run with fix:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k LegacySpecEditsStateTests
    .                                                                        [100%]
    1 passed, 92 deselected in 0.67s
    ```
    Failing run with E-03 conversion hunk temporarily reverted:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k LegacySpecEditsStateTests
    F                                                                        [100%]
    =================================== FAILURES ===================================
    _ LegacySpecEditsStateTests.test_legacy_spec_edits_reconciliation_summary_and_report _
    ...
    >           self.assertEqual(len(summary["reconciled"]), 1)
    E           AssertionError: 0 != 1
    =========================== short test summary info ============================
    FAILED tests/test_runner_shared.py::LegacySpecEditsStateTests::test_legacy_spec_edits_reconciliation_summary_and_report
    1 failed, 92 deselected in 0.78s
    ```
    Restored passing run:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k LegacySpecEditsStateTests
    .                                                                        [100%]
    1 passed, 92 deselected in 0.67s
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence: Bare suite ran bare: before 2436 passed, 1 skipped, 3 warnings in 44.79s; after 2440 passed, 1 skipped, 3 warnings in 59.52s; delta failing node IDs is empty set(). Details pasted below.
    Bare suite before change:
    ```
    2436 passed, 1 skipped, 3 warnings in 44.79s
    ```
    Bare suite after change:
    ```
    2440 passed, 1 skipped, 3 warnings in 59.52s
    ```
    Failing node-IDs delta (after minus before):
    `set()` (empty set; 0 failures before, 0 failures after).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS BLOCKED ON ONE HUMAN DECISION AND MUST NOT BE EXECUTED UNTIL IT IS ANSWERED. `OQ-03` carries `- Blocking: yes` and `- Finding: F-8`, so `aw ipd lint` refuses this plan at every checkpoint (measured at review: `IPD-Q501` at the `review-finalize` phase) and `aw ipd begin` will refuse too. The question is an ORDERING decision between this plan and pending plan `cdxcbh`, both of which edit `runner_shared.AGY_IMPORTS_FROM_OC_RUNIPD` with nothing ordering them; the recommended answer is to add `- Item-Dependencies: executed:cdxcbh` to this plan, which this review deliberately did NOT apply unilaterally because it changes what the runner executes and when.

WHAT A HUMAN IS APPROVING once OQ-03 is answered. A three-line data-shape fix to a REPORTING surface: one recorder writes the key and shape the one reader consumes, the reader additionally tolerates the legacy record, and one dead fork is deleted. No runner control flow, no finalize behavior, no lifecycle act changes. The user-visible effect is that `aw oc run` and `aw agy run` resume telling an operator which specs a run changed, INCLUDING an undeclared spec change, which they have not done on either host since `70a2059f`. Verified at review that the defect is total rather than cosmetic: an undeclared-spec-only run currently prints NOTHING, so the managed AGENTS.md promise that "silence means 'no declared spec edits'" is false today.

THE COVERAGE SITUATION IS WHY E-05/E-06/E-07 CARRY THE WEIGHT. No test in the tree touches this surface (`grep -rn "spec_edit\|report_run_spec" tests/*.py` returns nothing; the two `st5klo` test files were deleted by `80db6750`/`19313eed`), which is exactly why the dedup regression landed green. Each new test must therefore be shown FAILING against the pre-fix writer, not merely passing after.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the six paths in `- Scope-Paths:` are the intended surface. `render_stream.format_spec_edit_report` is deliberately NOT declared because its logic is correct and consumes the summary unchanged; `compute_scope_reconciliation` and `finalize_precheck` are OUT. Do NOT "update" the orphaned `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json` (read by nothing at HEAD). If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. E-08 compares failing NODE IDS rather than counts, which is the right bar; do not substitute a count comparison.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if E-01 finds the writer and reader already agree, the defect is fixed and this plan should be retired rather than executed; if E-04 finds `AGY_IMPORTS_FROM_OC_RUNIPD` in a state OQ-03's answer did not anticipate, report it rather than improvising the ordering. F-5's on-disk counts being unobtainable is NOT a stop condition (they are gitignored local state, F-9); say so in one line and continue.

The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` item must carry observed evidence before the terminal transition, which the RUNNER owns when it executes this plan in a lane and which the executor otherwise performs with `aw ipd finalize`. This plan inherits `- Blocks-Release: next` from backlog `tm5vnx`, so the next release is gated on it - which is a reason to answer OQ-03 promptly rather than a reason to execute past it.
