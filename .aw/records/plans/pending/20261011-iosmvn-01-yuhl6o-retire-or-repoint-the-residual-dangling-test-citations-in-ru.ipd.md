# IPD: Retire or repoint the residual dangling test citations in runner_shared

- Date: 2026-10-11
- Kind: child
- Concern: `agent_workflows/runner_shared.py` carries 41 comment/docstring citations of test files that commit `19313eed` deleted, that do not exist at HEAD, that no sibling plan owns, and whose surrounding prose (3 lines either side) does not already record the deletion. Each tells a reader that a named test guards a property, and the reader cannot open it. Measured at authoring HEAD `8538be828` with the Set's measurement command (see Project conventions): `UNRETIRED 41` for this file.
- Scope: IN: comment and docstring prose in `agent_workflows/runner_shared.py` only, at the 41 sites in Findings. Each site is dispositioned one of: REPOINT (a live test at HEAD asserts the same property; cite it), RETIRE-PIN (the deleted test read source or pinned structure; state that it was deleted in `19313eed` and will not return under `GUIDING_PRINCIPLES` P16), or RETIRE-UNGUARDED (the deleted test was behavioral and no live test asserts the property; state that it was deleted in `19313eed` and that no live guard currently asserts it). The design reasoning each comment carries is preserved. OUT: any executable change; restoring any test; the sites owned by other plans (`046nys`/`dtelfb`, `3tov52`/`65d5zf`, `yf1p8y`, executed `rcp8c4`), excluded by the measurement regex; filing backlog for unguarded properties (Order 04 `ellenm`).
- Scope-Paths: agent_workflows/runner_shared.py, .aw/records/plans/pending/20261011-iosmvn-01-yuhl6o-retire-or-repoint-the-residual-dangling-test-citations-in-ru.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: yuhl6o

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`; 41 sites measured at HEAD `8538be828`.

## Goal

Make every residual `19313eed` dangling test citation in `runner_shared.py` truthful: either it names a test that exists and asserts the property, or it says plainly that the guard was deleted in `19313eed` and whether anything still asserts the property.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [ ] E-01 Re-measure at execution HEAD: run the Set measurement command (Project conventions) with argument `agent_workflows/runner_shared.py` and record the list and `UNRETIRED N` line; record `git rev-parse --short HEAD`. Any site not in Findings (or any Findings row now absent) is recorded as a delta and dispositioned by the same rules.
  - Depends on: none
  - Expected outcome: the recorded list equals Findings S-01..S-41 or each delta carries a recorded disposition.
  - Execution state: pending

- [ ] E-02 For each site, decide its disposition and record it in a table appended to this plan's Findings (`Site | Disposition | Evidence`). Evidence for REPOINT is the live test id plus a pasted `rg -n` hit in `tests/`; for RETIRE-PIN, the deleted test's form from `git show 19313eed^:<path>` (e.g. `ast.parse`/`inspect.getsource`/source substring); for RETIRE-UNGUARDED, the empty `rg` over `tests/` for the property's symbol or behavior.
  - Depends on: E-01
  - Expected outcome: 41 (plus deltas) dispositioned rows, each with evidence.
  - Execution state: pending

### Task group 2: Edit

- [ ] E-03 Apply the dispositions as comment/docstring edits in `agent_workflows/runner_shared.py`. REPOINT replaces the path (and `::Symbol`) with the live one. RETIRE-PIN and RETIRE-UNGUARDED keep the sentence's design reason and replace the enforcement claim with the wording precedent already used in `oc_runipd.py` ("deleted in `19313eed`; no live guard currently asserts this") so that `19313eed` appears within three lines of the citation. Do not change any statement, constant, signature, or identifier.
  - Depends on: E-02
  - Expected outcome: measurement command prints `UNRETIRED 0` for this file.
  - Execution state: pending

- [ ] E-04 Prove the edit is prose-only and regression-free: run the AST-equivalence command (Project conventions) against the E-01 HEAD and run the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: `AST-DIFFER []`; suite summary with no failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND (identical in every child; pass the files as arguments). A hit is a `tests/test_*.py` path deleted by `19313eed`, absent at HEAD, not in a sibling-owned cluster, with no `19313eed` within 3 lines:

```sh
python3 -c 'import re,subprocess,sys;from pathlib import Path;D=set(subprocess.check_output(["git","diff","--diff-filter=D","--name-only","19313eed^","19313eed"],text=True).split());O=re.compile(r"test_(orchestrator_probe_cache|review_findings_cascade|runner_stop_triggers|runner_backlog_close|runner_layering|run_flag_surface)\.py");B=[(f,i+1,t) for f in sys.argv[1:] for L in [Path(f).read_text().splitlines()] for i,l in enumerate(L) for t in re.findall(r"tests/test_\w+\.py",l) if t in D and not Path(t).is_file() and not O.search(t) and "19313eed" not in " ".join(L[max(0,i-3):i+4])];[print(*b) for b in B];print("UNRETIRED",len(B))' <files...>
```

- AST-EQUIVALENCE COMMAND (docstrings blanked; comments are invisible to `ast`), `<rev>` the E-01 HEAD: `python3 -c "import ast,subprocess,sys
def norm(src):
 t=ast.parse(src)
 for n in ast.walk(t):
  b=getattr(n,'body',None)
  if isinstance(b,list) and b and isinstance(b[0],ast.Expr) and isinstance(getattr(b[0],'value',None),ast.Constant) and isinstance(b[0].value.value,str): b[0].value.value=''
 return ast.dump(t)
r=sys.argv[1];bad=[f for f in sys.argv[2:] if norm(subprocess.check_output(['git','show',r+':'+f],text=True))!=norm(open(f).read())];print('AST-DIFFER',bad)" <rev> <files...>` (verified at authoring HEAD: `AST-DIFFER []` on the unchanged file).
- Retirement wording precedent: `oc_runipd.py` re-export comments ("`tests/test_runner_refork_guard.py` was deleted in `19313eed`, so no live guard currently asserts this property"), and executed plans `rcp8c4`/`gia5i7`.
- Code-pinning tests will not be restored (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES` P16, maintainer ruling recorded on `pn7rw3`).
- Run the suite bare: `python3 -m pytest`. Cite code by symbol.

## Findings

Measured at HEAD `8538be828`. Enclosing symbol is the innermost `def`/`class`; "module" means a module-level comment block near that region.

| Site | Enclosing symbol | Cited path |
|---|---|---|
| S-01 | module (`_KIND_RE` block) | `tests/test_runner_item_dependencies.py` |
| S-02 | `_lane_record_informativeness` | `tests/test_runner_telemetry_integration.py` |
| S-03 | `add_audit_parser` | `tests/test_rununify_build_parser.py` |
| S-04 | module (`PlanRecord` section) | `tests/test_rununify_record.py` |
| S-05 | `PlanRecord` | `tests/test_rununify_record.py` |
| S-06 | `parse_plan_file` | `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` |
| S-07 | module | `tests/test_runner_item_dependencies.py::InRunExecutedDependencyTests` |
| S-08 | `manifest_entry_is_selectable` | `tests/test_runner_item_dependencies.py::InRunExecutedDependencyTests` |
| S-09 | module (clean-base note) | `tests/test_lane_clean_base.py` |
| S-10 | module (deferral reason mapping) | `tests/test_orchestrator_deferral_reporting.py` |
| S-11 | `orchestrator_refusal_text` | `tests/test_orchestrator_deferral_reporting.py` |
| S-12 | module (telemetry seam) | `tests/test_runner_refork_guard.py` |
| S-13 | `defect_report_prompt_block` | `tests/test_reporting_contract.py` |
| S-14 | `defect_report_prompt_block` | `tests/test_lane_prompt_purity.py` |
| S-15 | module (lift exclusions) | `tests/test_rununify_lift.py` |
| S-16 | module (suite baseline) | `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` |
| S-17 | module (suite baseline) | `tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable` |
| S-18 | module (suite adjudication) | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-19 | `gate_answer_is_warranted` | `tests/test_runner_telemetry_integration.py` |
| S-20 | `perform_gate_answer` | `tests/test_suite_baseline.py` |
| S-21 | module (suite baseline) | `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` |
| S-22 | module (suite adjudication) | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-23 | `new_failures_since_baseline` | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-24 | `unattributed_merged_failures` | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-25 | `extract_session_id` | `tests/test_rununify_conflicts.py` |
| S-26 | `driver_begin` | `tests/test_lane_tool_identity.py` |
| S-27 | module (host descriptor) | `tests/test_rununify_host_descriptor.py` |
| S-28 | module (success-bar note) | `tests/test_runner_item_dependencies.py::_SHARED_NAMES` |
| S-29 | module (success states) | `tests/test_rununify_run_queue.py::TheExitCodeReflectsTheRealOutcome` |
| S-30 | `exit_code_statuses` | `tests/test_runner_stop_levels12.py` |
| S-31 | `finalize_outcome` | `tests/test_rununify_execute_item.py` |
| S-32 | `terminate_process` | `tests/test_runner_shutdown.py` |
| S-33 | `_record_checkpoint_stop` | `tests/test_runner_stop.py::test_stop_isolated_git_status` |
| S-34 | `reconcile_interrupted` | `tests/test_rununify_run_queue.py` |
| S-35 | `_run_verifier_turn` | `tests/test_runner_refork_guard.py` |
| S-36 | `execute_item_core` | `tests/test_rununify_execute_item_gates.py` |
| S-37 | `edge_satisfied` | `tests/test_runner_refork_guard.py` |
| S-38 | module (signal-handler note) | `tests/test_lane_allocation_idempotent.py` |
| S-39 | module (signal-handler note) | `tests/test_runner_stop.py` |
| S-40 | module (signal-handler note) | `tests/test_runner_stop_level3.py` |
| S-41 | module (signal-handler note) | `tests/test_runner_stop_level4.py` |

Observed shape at authoring (to guide, not to pre-decide, E-02): S-02/S-19 cite an `ast.Name` guard (RETIRE-PIN candidates); S-16/S-21 have a live sibling `tests/test_suite_baseline_direction.py` that may be a REPOINT for the direction property only; S-07/S-08 already mention the deletion further than 3 lines away and backlog `mv18lz` carries the lost coverage; S-18/S-22..S-24 cite a behavioral class (44 functions in `19313eed^:tests/test_suite_adjudication.py`), a likely RETIRE-UNGUARDED.

## Proposed changes (ordered, validatable)

1. E-01 re-measure. 2. E-02 disposition table with evidence. 3. E-03 prose edits. 4. E-04 AST-equivalence and bare suite.

## Deferred / out of scope (with reason)

- Filing backlog items for RETIRE-UNGUARDED properties: done once for the whole Set.
  - Carrier: ellenm
- Restoring the lost behavioral coverage for `manifest_entry_is_selectable` (S-07/S-08).
  - Carrier: mv18lz
- `test_orchestrator_probe_cache.py`, `test_review_findings_cascade.py`, `test_runner_layering.py`, `test_run_flag_surface.py` citations in this file: owned by plans `dtelfb`/`65d5zf`, backlog `yf1p8y`, and executed `rcp8c4`.
  - Carrier: 046nys
- Restoring any source-reading guard.
  - Carrier-Declined: forbidden by `AGENTS.md` and `GUIDING_PRINCIPLES` P16.

## Scope check

- Over-scope: none; one production file, prose only, proven by E-04.
- Under-scope: none; every one of the 41 measured sites has a row and an E-item; lost coverage is carried by `ellenm`/`mv18lz`.

## Required tests / validation

- Measurement command on `agent_workflows/runner_shared.py` -> `UNRETIRED 0`.
- AST-equivalence command -> `AST-DIFFER []`.
- Bare `python3 -m pytest` with no failures.

## Spec / documentation sync

N/A: comment and docstring prose only; no spec describes these comments and no `.spec.md` is touched.

## Open questions

### OQ-01: Rewrite each citation or delete it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Rewrite, preserving the design reason. Executed plans `rcp8c4` and `gia5i7` set the precedent: the comment's reason is the valuable part, and deleting it loses why the code is shaped as it is.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted measurement output (all hit lines plus `UNRETIRED N`) and the HEAD sha, with any delta rows listed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the appended disposition table with one row per site and pasted `rg`/`git show` evidence for at least every REPOINT and every RETIRE-UNGUARDED row.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted post-edit measurement output ending `UNRETIRED 0`, and `git diff --stat agent_workflows/runner_shared.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `AST-DIFFER []` output and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Commit through `aw commit yuhl6o -- <paths>` limited to the declared Scope-Paths; never push. Move to `executed/` only via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass` with pasted evidence.
