# IPD: Prove the pruned suite still catches regressions with coverage parity, a mutation spot-check, a flake check and final measurements

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` (Set `testprune`) Method steps 3 to 5 and "Evidence required in the final report". Children `tv72xy` (delete pins), `83nnyn` (consolidate) and `c8bfp9` (speed up) each prove their own batch, but the prompt's acceptance claim is Set-wide: the retained suite catches at least every regression the baseline suite caught. Coverage parity alone cannot prove that (equal lines can carry weaker assertions), so the prompt also requires a mutation spot-check over at least 20 sampled deleted or consolidated tests plus every deleted test citing a defect id. Authoring census: 345 test files cite an id6 in an `IPD`/`plan`/`backlog`/`incident` context, so the defect-citing population is large and must be enumerated from the decision table, not guessed. `mutmut` is not installed in this environment, so mutations are hand-applied one-line edits.
- Scope: Read-only on production code except for temporary, reverted mutations. Measure the final suite against the Set baseline (research `offdhr` and `7ry5kv`, plus `qqrgv3`'s recorded baseline): union line and branch coverage of `agent_workflows/`, a list of every line or branch that lost all coverage with a justification or a restored behavioral test; the mutation spot-check; a flake check of three randomized runs plus a serial run; final counts and timings; a CHANGELOG line; finalize the decision-table research; and write the Set's final report as a research record. Restoring a test (or writing a better behavioral one) when a mutation survives is IN scope.
- Scope-Paths: tests/, CHANGELOG.md, .aw/records/research/*testprune*, .aw/records/backlog/
- Item-Dependencies: executed:c8bfp9
- Status: to-review
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 5
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: vgus66

## Workflow history
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Demonstrate with pasted measurements that the pruned, consolidated, faster suite loses no covered line or branch without a recorded reason, catches every sampled reintroduced bug, is not flaky under randomized ordering, and runs the full retained suite in under 120s; and publish that as the Set's final report.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: coverage parity

- [ ] E-01 Run the final suite with branch coverage and per-test contexts using the `qqrgv3` tooling (`python3 -m pytest tests/ -m '' -o addopts="" -n auto --dist=worksteal --cov=agent_workflows --cov-branch --cov-context=test`), `coverage json`, and compare to the Set baseline coverage database recorded by `qqrgv3` (same flags, Set start commit): union line and branch totals and percent, per-module totals, and the set of `(file, line)` and `(file, arc)` covered at baseline but not now. Lines that no longer exist in source (production code changed on `main` meanwhile) are excluded by mapping on current source and listed separately.
  - Depends on: none
  - Expected outcome: totals table (baseline versus final) and an explicit lost-lines list and lost-branches list; target both empty.
  - Execution state: pending
- [ ] E-02 For each lost line or branch from E-01: either restore coverage with a behavioral test (restore the deleted test if it was behavioral, else write a new one calling the code and asserting outcomes per P16) or record a justification row (for example unreachable defensive branch, code deleted on `main`, or covered only by a removed structure pin whose deletion `tv72xy` recorded). Rerun E-01's comparison after restorations.
  - Depends on: E-01
  - Expected outcome: every lost line and branch has a row (restored-by `<node id>` or justified); post-restoration lost list is empty or fully justified.
  - Execution state: pending
- [ ] E-03 Recompute the hguae9 core per-module coverage (its `tests/tools/` measurement script) and compare to the table hguae9 recorded at its execution; any module whose core coverage fell, or any leaf no longer driven by a core test, is restored in this child.
  - Depends on: E-02
  - Expected outcome: zero core coverage regressions per module; leaf-map totals unchanged.
  - Execution state: pending

### Task group 2: mutation spot-check

- [ ] E-04 Build the sample from the decision-table research: (a) every deleted test (category starting `delete`) whose source or docstring cited a backlog id6, plan id6 or incident (consolidated defect-citing tests are included too, since their row must still catch the defect); (b) a seeded random sample (`random.Random(<seed recorded>)`) of at least 20 further deleted or consolidated node ids drawn across all three children, stratified so each of `tv72xy`, `83nnyn` and `c8bfp9`-touched subsystems contributes. Record the sample list, seed and population sizes.
  - Depends on: none
  - Expected outcome: sample list recorded with seed; size at least 20 plus the full defect-citing set.
  - Execution state: pending
- [ ] E-05 For each sampled test: read the original test at the Set start commit (`git show <base>:<path>`), identify the production behavior it guarded and the code it targeted (by symbol), apply a one-line mutation that reintroduces that bug (for a defect-citing test, the bug the cited id6 describes), run the retained suite selection that covers that symbol (from the per-test contexts) and then the full suite if the selection passes, record which retained test failed, and revert the mutation (verify `git diff -- agent_workflows/` empty after each). Structure-pin deletions (`tv72xy` category) whose "bug" was a refactor rather than a behavior change are recorded as not-applicable with that reason, and do not count toward the 20.
  - Depends on: E-04
  - Expected outcome: a results table (node id, symbol, mutation one-liner, catching retained test, revert verified); every mutation caught.
  - Execution state: pending
- [ ] E-06 For any mutation nothing caught: restore the original test or write a better behavioral one that fails on the mutation and passes without it, then re-run that mutation to show it is now caught. Update the decision-table row (category becomes `restored`).
  - Depends on: E-05
  - Expected outcome: zero surviving mutations after restorations, each fix demonstrated by a fail-then-pass pair.
  - Execution state: pending

### Task group 3: flakes and final measurements

- [ ] E-07 Flake check: three full runs `python3 -m pytest tests/ -m ''` with `pytest-randomly` enabled and three distinct recorded seeds (`--randomly-seed=<n>`), plus one serial run (`-n 0`) of every module that failed in any randomized run. A test that fails under reordering or `-n 6` but passes serially is fixed in this child or quarantined with an `xfail(strict=False)` plus a backlog item filed via `aw backlog new` (Work-Kind `bug` if it reflects a production defect, which then carries `- Blocks-Release: next`); never silently deleted.
  - Depends on: E-06
  - Expected outcome: three passing randomized runs, or each flake listed with its disposition (fixed or quarantined with backlog id6).
  - Execution state: pending
- [ ] E-08 Final measurements: collected count (`--collect-only -m ''`), module count (`tests/test_*.py`), three warm full runs (median, target under 120s), `--durations=20`, union line and branch coverage (from E-02's final comparison), bare `python3 -m pytest` core summary and wall time, all against the Set baseline (8794 collected and 565.28s at research `offdhr`/`7ry5kv`, or the `qqrgv3` re-measured baseline if it differs).
  - Depends on: E-07
  - Expected outcome: before/after table complete; median under 120s, or the miss recorded with `c8bfp9`'s justification list for maintainer decision.
  - Execution state: pending

### Task group 4: records

- [ ] E-09 Finalize the decision-table research (`qqrgv3`-created, per-row node id, category, reason, surviving node id, mutation result where sampled): add classification counts per category, the list of tests kept despite matching a delete criterion with the compelling reason, flake dispositions, and set it to its final status via `aw research` tooling. Write the Set's final report as a NEW research record (`aw research new --kind assessment --set testprune --order 05 --slug test-prune-final-report --apply`) containing every "Evidence required in the final report" item from prompt `4ul37x` (before/after counts and timings, `--durations=20`, coverage, per-category counts, every deleted node id and reason by reference to the decision table, mutation results, kept-despite-criterion list, flakes, every file changed by path from `git diff --name-only <base>..HEAD`), then run `aw research index`. Add one CHANGELOG line under the pending release's testing or internal section (user-facing prose: no em or en dashes) stating the new counts, the full-suite wall time, and that coverage parity and a mutation spot-check were verified. Run `aw sanitize --agent` on the changed records.
  - Depends on: E-03, E-08
  - Expected outcome: research index check passes; final report present; CHANGELOG line present; sanitizer result pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Research records are created and indexed only via `aw research new` / `aw research index` (AGENTS.md "Durable reference"); do not hand-name them.
- CHANGELOG is user-facing: no em or en dashes (AGENTS.md execution contract); the pending section is `## 2.0.0 (pending)`.
- Live bugs must carry `- Blocks-Release:` (AGENTS.md "Every live bug gates the next release"), so a flake quarantined because of a production defect is filed `bug` with the gate.
- P16: restored coverage must exercise the code and assert on real outputs, never read source.
- `livecorpus` tests stay and are part of the full run measured here.
- Subprocess-launched tests record no in-process coverage context (research `offdhr`), so the per-test-context selection in E-05 is followed by a full-suite run whenever it passes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Baseline: 8794 collected, 565.28s, 75% line (72507/93730) and 26266/37902 branches | research `7ry5kv`, `offdhr` |
| F-2 | Coverage parity cannot prove assertion strength; mutation sampling is required | prompt `4ul37x` Method step 3 |
| F-3 | 345 test files cite id6s in a defect context; the deleted subset is enumerated from the decision table | `rg -l` at authoring |
| F-4 | `mutmut` is not installed; hand mutations are the method | `pip show mutmut` returned nothing |

## Proposed changes (ordered, validatable)

E-01..E-03 coverage parity and core parity -> E-04..E-06 mutation spot-check with restorations -> E-07 flakes -> E-08 final measurements -> E-09 records, report, CHANGELOG. E-04 is independent of E-01 and may run in parallel.

## Deferred / out of scope (with reason)

- Full mutation testing of `agent_workflows/` (every mutant): disproportionate cost; the prompt requires a spot-check.
  - Carrier-Declined: prompt `4ul37x` specifies "a random sample of at least 20 ... and every deleted test that cites a defect id".
- Fixing production defects a flake reveals: filed as backlog `bug` items with the release gate in E-07, not fixed here.
  - Carrier-Declined: carried by the backlog item E-07 files at execution, whose id6 is not known until then.

## Scope check

- Over-scope: none.
- Under-scope: none; restorations in E-02, E-03 and E-06 make this child able to close the gaps it finds instead of only reporting them.

## Required tests / validation

E-07's three randomized full runs and E-08's three warm full runs, the coverage comparisons, every mutation run, and the bare `python3 -m pytest` summary, all pasted.

## Spec / documentation sync

CHANGELOG.md line in E-09. No spec governs the test suite.

## Open questions

### OQ-01: What counts as "the bug the test was meant to catch" for a test without a defect citation?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved: the mutation inverts or removes the specific condition, return value or emitted field the original test's strongest assertion checked, in the production symbol that assertion reached (identified from the test body and its per-test coverage context). The mutation one-liner is recorded so a reviewer can dispute it.

### OQ-02: Is a justified lost line acceptable, or must parity be exact?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: The prompt says union coverage "must not drop; list and justify (or restore) every line or branch that lost all coverage". This plan restores by default and justifies only lines that are unreachable or removed from source; the maintainer reviews the justification list in the final report.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted baseline versus final union line and branch totals and percents, and the lost-lines and lost-branches lists (or "none" from the comparison script's output).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted per-line disposition rows and the rerun comparison output showing the remaining lost set empty or fully justified.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted core per-module comparison (no module lower) and leaf-map totals versus hguae9's recorded values.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted sample list with seed, population sizes, defect-citing count, and per-child stratification counts (random sample at least 20).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted results table with, for each mutation, the pytest failure line of the catching test and the empty `git diff -- agent_workflows/` after revert.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: for each surviving mutation, pasted fail-with-mutation and pass-without-mutation runs of the restored or new test; or the statement, backed by V-05, that none survived.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted three randomized full-run summary lines with seeds, any serial reruns, and each flake's disposition with backlog id6 where quarantined.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted before/after table: collected count, module count, three wall times and median, `--durations=20`, union line and branch coverage, and core summary line and wall time.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted `aw research index --check` output, the final report's path and summary line, the CHANGELOG diff line, and the `aw sanitize --agent` result record.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and explicit human approval, and only after `c8bfp9` is executed. Work in an isolated worktree via `aw work begin vgus66`; every mutation is temporary and reverted before the next, verified by an empty `git diff -- agent_workflows/`; commit restorations, records and the CHANGELOG line with `aw commit vgus66 -- <paths>`; never push or tag; publish via `aw integration-lock -- git merge --ff-only <branch>`. Paste ACTUAL output in every V-item. On completion run `aw ipd lint --phase pre-transition` and move the plan to `executed/` through the lifecycle tooling.
