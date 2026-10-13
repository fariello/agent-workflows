# IPD: Pass the parsed edge's id6 to the runner review-findings dependency gate

- Date: 2026-10-12
- Kind: child
- Concern: The runner's review-findings dependency gate in `runner_shared.dependency_status_detailed` never fires, because it hands `review_findings.subject_gating_blocks` the raw dependency token instead of the target id6.
- Scope: Fix the one call site so the gate receives `edge.id6`, correct the comment that describes it, and add behavioral regression tests that drive `dependency_status_detailed` against a temp repo carrying a real `.review.md` record.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_findings_dependency_gate.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: bs850k
- Blocks-Release: next
- Set: carriergate
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: k81fqx
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-13 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003. Re-measured at HEAD 559173a5c: defect reproduces for executed:<id6> out of queue and in queue (both admitted with a HIGH OPEN finding), the fix blocks both; bare-id6 already blocked pre-fix, so case (b) is now characterization; fixture must carry ### Findings or it passes vacuously; corpus 10 gating subjects, 0 pending dependents; Deferred rows carry Carrier-Declined.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `bs850k`; defect reproduced end to end on this lane's HEAD before writing.

## Goal

Make the execute-action findings gate in `runner_shared.dependency_status_detailed` actually consult the dependency target's review record, so a plan whose `executed:` prerequisite carries an unresolved gating finding is held `dependency-blocked` exactly as revgate `7nkcgp` specified, instead of silently admitted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Fix the call site

- [ ] E-01 In `runner_shared.dependency_status_detailed`, replace `target = dependency_target_id6(edge) or dep` with `target = edge.id6` (the edge is already parsed and non-None at that point, guarded by the `if edge is None: ... continue` branch above it), and rewrite the adjacent comment so it states what the code now does and why the raw token must never reach `_findings_block_reason`. Do NOT change `dependency_target_id6`'s signature or its other callers (`dependency_target_id6(str(dep))` sites elsewhere in the module are correct and stay as they are).
  - Depends on: none
  - Expected outcome: `dependency_status_detailed` passes the bare target id6 to `_findings_block_reason`; the `or dep` raw-token fallback is gone; the comment no longer claims behavior the code lacks.
  - Execution state: pending

### Task group 2: Behavioral regression tests

- [ ] E-02 Add `tests/test_runner_findings_dependency_gate.py` that builds a temp repo (a `.aw/records/plans/executed/` IPD `- Id: dep001`, `- Status: executed`, plus a `.aw/records/reviews/` record `- Subject-Id: dep001` whose `## Round 1` carries a `### Findings` heading above the findings table, because `review_findings.parse_review_text` attributes table rows to Findings only under that heading and a table without it parses to ZERO findings, which would make every blocked case vacuously pass as satisfied; prefer writing the record through `review_findings.render_review`/`write_review` so the fixture cannot drift from the parser) and calls `runner_shared.dependency_status_detailed` directly, asserting on its returned `(satisfied, unsatisfied, reasons)`. Test names are non-binding pointers; the bar is the behavior each case pins. Cases: (a) OUT-OF-QUEUE execute item, dependency `executed:dep001`, HIGH finding decided OPEN -> `satisfied` False, `unsatisfied == ['executed:dep001']`, and the reason names `dep001` and the finding id; (b) the same with the dependency declared as the bare id6 `dep001` -> blocked, with `unsatisfied == ['dep001']` (a CHARACTERIZATION case: it already blocks before E-01, because the `or dep` fallback hands over the raw token, which for a bare id6 IS the id6; it pins that E-01 does not regress the bare form); (c) IN-QUEUE dependency (queue entry `dep001` with run status `executed`) -> blocked identically, proving the gate is not evadable by queue membership; (d) the same finding decided FIXED -> satisfied; (e) the dependent's `action` is `review` -> satisfied (review items are deliberately not findings-gated); (f) a LOW finding OPEN under the default `high` threshold -> satisfied; (g) no review record at all -> satisfied. Every case asserts on returned values only; no test reads source, inspects AST, or pins comment text.
  - Depends on: E-01
  - Expected outcome: the module exists, cases (a) and (c) FAIL on the pre-fix code (shown by reverting E-01 locally and re-running before restoring it) while (b) passes both before and after, and all seven PASS with E-01 applied. A fixture sanity assertion (`review_findings.subject_gating_blocks(repo, 'dep001')` non-empty in the blocked cases) guards against the vacuous-pass trap described above.
  - Execution state: pending

### Task group 3: Corpus impact check

- [ ] E-03 Re-measure on this repository, after E-01, how many pending/approved plans the now-live gate newly blocks: enumerate every `.review.md` subject with a non-empty `review_findings.subject_gating_blocks(repo, id6)` and every pending plan whose `- Item-Dependencies:` names one of them. Record both counts and the list in the plan's Findings drift note. If the plan list is non-empty, do not weaken the gate: record the affected plans by id6 so the maintainer sees which dependents are now (correctly) held.
  - Depends on: E-01
  - Expected outcome: a pasted count of gating subjects and of newly blocked pending dependents, re-derived at execution (authoring and review measurement: 10 and 0, see F-05; that number is context, not the bar).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The suite runs BARE as `python3 -m pytest`; per-test names on a narrowed run use `python3 -m pytest -o addopts="" <path>` (AGENTS.md repo-local development contract).
- Tests must exercise behavior, never source structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
- Commits go through `aw commit <plan> -- <paths>`, never raw `git add -A`, never push.
- `dependency_status_detailed` has ONE definition, in `runner_shared`; `oc_runipd` and `agy_runipd` re-export it (`agy_runipd` import block comment "depreview 03ie04 E-03: `dependency_status_detailed` is RE-EXPORTED here, not defined"), so one edit fixes both hosts.
- `_findings_block_reason(repo, dep)` delegates entirely to `review_findings.subject_gating_blocks` and fails open on exception; it is the only consumer touched.
- `subject_gating_blocks` matches by exact equality `(doc.subject_id or "").strip() != wanted`, which is why a raw `executed:<id6>` token can never match.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | **THE DEFECT.** `runner_shared.dependency_status_detailed` parses each dependency with `edge = parse_dependency_token(dep)`, then in the execute arm reads `target = dependency_target_id6(edge) or dep`. `dependency_target_id6(token: str)` re-runs `parse_dependency_token` on its argument, which is an `ItemDependency`, not a string, so it returns `None`; `or dep` then substitutes the RAW TOKEN. | Driven on this lane's HEAD: `parse_dependency_token("executed:a8e2l8")` -> `ItemDependency(kind='executed', target_type='ipd', status=None, id6='a8e2l8')`; `dependency_target_id6(<that edge>)` -> `None`; `dependency_target_id6("executed:a8e2l8")` -> `'a8e2l8'`. |
| F-02 | **THE GATE NEVER FIRES, END TO END.** With a temp repo carrying an executed IPD `dep001` and a review record `- Subject-Id: dep001` with a HIGH OPEN finding: `subject_gating_blocks(repo, "dep001")` returns one `GatingBlock(finding_id='PR-001', severity='high', decision='open', ...)`; `subject_gating_blocks(repo, "executed:dep001")` returns `()`; and `dependency_status_detailed(item, state)` for an execute item depending on `executed:dep001` returns `(True, [], {})`, i.e. ADMITTED. | Script run on this lane at authoring time; output pasted verbatim in the three preceding clauses. |
| F-03 | **THE COMMENT ASSERTS THE OPPOSITE OF THE CODE.** The comment directly above the call reads "Uses the parsed edge's target id6, not the raw token", while the code falls back to the raw token on every edge. | Read of `runner_shared.dependency_status_detailed`, the revgate block after `edge_satisfied`. |
| F-04 | **ONE DEFINITION, BOTH HOSTS.** `rg "def dependency_status_detailed" agent_workflows` finds only `runner_shared.py`; `oc_runipd` and `agy_runipd` import it as `dependency_status_detailed as dependency_status_detailed`. Other `dependency_target_id6` callers in the module pass `str(dep)` and are correct. | `rg -n "dependency_target_id6\(" agent_workflows/runner_shared.py` lists the faulty call plus two `dependency_target_id6(str(dep))` calls. |
| F-05 | **BLAST RADIUS IS SMALL TODAY.** Of 927 `.review.md` records (923 distinct subjects), 10 subjects currently return a non-empty `subject_gating_blocks` (`2j4pd0`, `32ij2j`, `62pkkg`, `9iiqmm`, `a6i03f`, `d5ntkj`, `g1w58u`, `obyhrm`, `p47qfu`, `xtklpd`), and 0 pending plans declare an `- Item-Dependencies:` edge to any of them. Turning the gate on therefore newly blocks nothing in the current queue; E-03 re-measures at execution time because the corpus moves. | Script over `review_findings.iter_review_files(repo)` and `.aw/records/plans/pending/*.ipd.md` on this lane at authoring time. |
| F-06 | **NO EXISTING TEST COVERS THE FIRING CASE.** `rg "_findings_block_reason\|subject_gating_blocks" tests/*.py` finds only `tests/test_spec_review_attestation.py` (the empty-repo case) and render tests in `tests/test_dependency_block_reporting.py` that synthesize a `GatingBlock` reason directly rather than producing one through `dependency_status_detailed`. That is why the dead gate went unnoticed. | The `rg` named, run on this lane. |
| F-08 | **ADDED AT REVIEW: THE BARE-ID6 FORM ALREADY BLOCKS, AND A HEADING-LESS FIXTURE PASSES VACUOUSLY.** Re-driven at review HEAD `559173a5c` against a temp repo: with a review record lacking `### Findings`, `subject_gating_blocks(repo, 'dep001')` returned `()` and every case read satisfied. With the heading: `subject_gating_blocks(repo,'dep001')` -> one `GatingBlock(finding_id='PR-001', severity='high', decision='open')`; pre-fix `dependency_status_detailed` returned `(True, [], {})` for `executed:dep001` out of queue AND in queue, but `(False, ['dep001'], {'dep001': 'dep001: review finding PR-001 is high/open and unresolved'})` for bare `dep001`; with `edge.id6` substituted all three block and a `review` item stays `(True, [], {})`. | Review probe in this lane, monkeypatching `dependency_target_id6` to return `edge.id6`. |
| F-07 | **NO AST-PINNING FIXTURE BLOCKS THE EDIT.** `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json` contains a fingerprint for `dependency_status_detailed`, but no test or module references that fixture by name (`rg -n "runnerlayer_rehomed_premove" agent_workflows tests --glob '!*.json'` is empty), so it is a retained historical record and not a live assertion. | The `rg` named, run on this lane. |

## Proposed changes (ordered, validatable)

1. E-01: one-line fix at the call site plus a corrected comment, in `agent_workflows/runner_shared.py`.
2. E-02: new behavioral test module `tests/test_runner_findings_dependency_gate.py`.
3. E-03: re-measure corpus impact and record it.

## Deferred / out of scope (with reason)

- Hardening `dependency_target_id6` to accept an `ItemDependency` as well as a string: not needed once the only mis-typed caller passes `edge.id6`, and widening a typed helper to paper over a caller error would hide the next such mistake. Out of scope.
  - Carrier-Declined: deliberately rejected; the caller fix removes the only mis-typed call (F-04).
- `_findings_block_reason`'s fail-open-on-exception posture: deliberate per revgate `7nkcgp` ("a crashing gate is a disabled gate"); unchanged.
  - Carrier-Declined: settled by revgate `7nkcgp`; no change wanted.
- Any change to `review_findings.subject_gating_blocks` or the threshold config: they behave correctly (F-02); the defect is solely in the caller.
  - Carrier-Declined: no defect exists there (F-02, F-08).

## Scope check

- Over-scope: none. Two paths, one function edit, one new test module.
- Under-scope: none. Both hosts share the one definition (F-04), so no per-host edit is needed; the in-queue and out-of-queue paths both reach the fixed line after `edge_satisfied`, and E-02 case (c) covers the in-queue path.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_runner_findings_dependency_gate.py -v`, showing all seven cases by name passing, plus evidence that cases (a) and (c) fail without E-01 while (b) passes either way.
- `python3 -m pytest -o addopts="" tests/test_dependency_block_reporting.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_orchestrator_retirement.py tests/test_hostcapgate_execute_requirement.py` (the existing consumers of `dependency_status_detailed`), passing.
- The bare full suite `python3 -m pytest`, with the executor re-deriving the pre-change baseline on its own HEAD and showing no new failures.
- `aw ipd lint <this plan> --phase pre-transition` conforming.
- `aw sanitize --agent` clean on the changed files.

## Spec / documentation sync

N/A. The fix RESTORES behavior already specified by revgate Order 03 (`7nkcgp`: an `executed:` dependency is satisfied only if it also carries no unresolved gating findings) and stated in `dependency_status_detailed`'s own docstring; no spec text describes the buggy behavior, so no `.spec.md` is amended and none is listed in `- Scope-Paths:`.

## Open questions

None. The only judgement call (whether to harden `dependency_target_id6` instead of fixing the caller) is resolved in `## Deferred / out of scope` from the repository evidence in F-01 and F-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted `git diff` of `agent_workflows/runner_shared.py` showing the call site now reads `edge.id6` with no `or dep` raw-token fallback and the comment rewritten; plus a pasted direct call `dependency_status_detailed(item, state)` against the F-02 temp-repo fixture returning `satisfied=False` with `unsatisfied == ['executed:dep001']` (observation produced by `runner_shared.dependency_status_detailed`, the function E-01 edits).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" tests/test_runner_findings_dependency_gate.py -v` showing all seven cases (a)-(g) passing by name; pasted output of the same run with E-01 reverted showing cases (a) and (c) FAILING and (b) passing, then `git diff --stat` after restoring E-01 showing no residue; pasted output of the existing-consumer test files listed under Required tests passing; and the pasted summary line of a bare `python3 -m pytest` with no failures beyond the executor's re-derived baseline.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the pasted output of the corpus measurement script showing the count of gating subjects, the count of pending plans with an edge to one, and the id6 list of any such plans.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is NOT approved for execution by its authoring or its review: it requires explicit human approval before any execution turn. Open questions: none.

An executor must: honor the two declared `- Scope-Paths:` exactly; commit only the paths it changed, through `aw commit <plan> -- <paths>`, and never push; run the validation plan above and PASTE ACTUAL OUTPUT rather than claiming success; and not weaken the gate if E-03 finds newly blocked dependents. Under `aw oc run` / `aw agy run` the RUNNER owns `aw ipd begin`/`aw ipd finalize` and the executor must NOT run them; it leaves every `V-*` at `Result: pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforming. Executed by hand with no runner, the executor performs the terminal transition through `aw ipd finalize`, never a hand-rolled `git mv`, and only once that same bar is met. SCOPE FENCE: an out-of-scope edit that proves necessary is justified with `--scope-reason` at finalize, and a declared path left unmodified needs `--scope-ack`.
