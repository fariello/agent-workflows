# IPD: Prove the pruned suite still catches regressions with coverage parity, a mutation spot-check, a flake check and final measurements

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `4ul37x` (Set `testprune`) Method steps 3 to 5 and "Evidence required in the final report". Children `tv72xy` (delete pins), `83nnyn` (consolidate) and `c8bfp9` (speed up) each prove their own batch, but the prompt's acceptance claim is Set-wide: the retained suite catches at least every regression the baseline suite caught. Coverage parity alone cannot prove that (equal lines can carry weaker assertions), so the prompt also requires a mutation spot-check over at least 20 sampled deleted or consolidated tests plus every deleted test citing a defect id. Authoring census: 345 test files cite an id6 in an `IPD`/`plan`/`backlog`/`incident` context, so the defect-citing population is large and must be enumerated from the decision table, not guessed. `mutmut` is not installed in this environment, so mutations are hand-applied one-line edits.
- Scope: Read-only on production code except for temporary, reverted mutations. Measure the final suite against the Set baseline (THE baseline is the `qqrgv3` E-07 run directory and its `meta.json` HEAD recorded in the `qqrgv3` decision-table research; research `offdhr` and `7ry5kv` are pre-`qqrgv3` context, lines-only and under-recording per `offdhr`'s own CORRECTION section, and are never the coverage bar): union line and branch coverage of `agent_workflows/`, a list of every line or branch that lost all coverage with a justification or a restored behavioral test; the mutation spot-check; a flake check of three randomized runs plus a serial run; final counts and timings; a CHANGELOG line; finalize the decision-table research; and write the Set's final report as a research record. Restoring a test (or writing a better behavioral one) when a mutation survives is IN scope.
- Scope-Paths: tests/, conftest.py, CHANGELOG.md, .aw/records/research/*testprune*, .aw/records/backlog/
- Item-Dependencies: executed:c8bfp9
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: high
- Set: testprune
- Order: 5
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: vgus66
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): status set to reviewed
- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010, PR-011, PR-012
- 2026-10-16 to-review (aw set): authored from prompt 4ul37x (Set testprune) with baseline research offdhr/7ry5kv

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Demonstrate with pasted measurements that the pruned, consolidated, faster suite loses no covered line or branch without a recorded reason, catches every sampled reintroduced bug, is not flaky under randomized ordering, and runs the full retained suite in under 120s; and publish that as the Set's final report.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: coverage parity

- [ ] E-01 Run the final suite with branch coverage and per-test contexts using the `qqrgv3` tooling, NOT pytest-cov flags (pytest-cov's `--cov-context=test` labels contexts differently and does not attribute subprocess children, so a comparison against the `qqrgv3` baseline reports spurious losses; `qqrgv3` F-7): `python3 -m tests.tools.percov_run --out .aw/state/percov/vgus66-final` (refuse to proceed if its `meta.json` `pytest_exit` is nonzero; fix or disposition failures first, E-07), then `python3 -m tests.tools.percov_analyze .aw/state/percov/vgus66-final --compare <qqrgv3 baseline dir>` for union line and arc totals and percent, per-module totals, and every `(file, line)` and `(file, arc)` covered at baseline but not now. If the baseline directory is gone (it is gitignored scratch, `qqrgv3` E-07), regenerate it by running the same `percov_run` in a temporary worktree at the recorded `meta.json` HEAD with the TESTS and `conftest.py` of that HEAD (`git worktree add --detach <dir> <HEAD>`), and record that the baseline was regenerated. Production code changes on `main` between the baseline HEAD and now (review: 78 files under `agent_workflows/` changed between the `offdhr` commit `6ea45c974` and review HEAD `20f1a9dae`) make lines incomparable: run a SECOND comparison that isolates test changes, the Set-start tests and `conftest.py` checked out over CURRENT production code in a temporary worktree (`git checkout <Set-start HEAD> -- tests/ conftest.py`; review probe: 55 paths restored, 9101 tests collected) and measured with the same `percov_run` (if the Set-start tests carry no `tests/tools/`, copy the current `tests/tools/` in), so the lost set it reports is attributable to the Set's test changes alone; that second comparison is the parity bar, and the first is reported as context.
  - Depends on: none
  - Expected outcome: totals table (baseline, Set-start-tests-on-current-code, final) and an explicit lost-lines list and lost-arcs list from the test-isolating comparison; target both empty. Any Set-start test that fails against current production code is listed and excluded from that comparison with its failure line (a test the code moved past, not a Set loss).
  - Execution state: pending
- [ ] E-02 For each lost line or arc from E-01's test-isolating comparison: either restore coverage with a behavioral test (restore the deleted test if it was behavioral, else write a new one calling the code and asserting outcomes per P16) or record a justification row (allowed reasons only: covered only by a removed structure pin whose deletion `tv72xy` recorded, for example code reached only through `inspect.getsource`; or demonstrably unreachable, shown by reading the guard that excludes it). "Code deleted on `main`" cannot appear here because the test-isolating comparison runs over current code. Rerun E-01's comparison after restorations. Every restored or new test is P16-conformant (calls the code, asserts outputs) and is shown to FAIL on a one-line mutation of the line it restores, then pass after revert.
  - Depends on: E-01
  - Expected outcome: every lost line and arc has a row (restored-by `<node id>` or justified with one of the allowed reasons); post-restoration lost list is empty or fully justified; each restoration's fail-on-mutation, pass-on-revert pair recorded.
  - Execution state: pending
- [ ] E-03 Recompute the hguae9 core per-module coverage with `python3 -m tests.tools.core_measure --out <dir>` and the driven-leaf map with the `tests/tools/leaf_probe.py` plugin (both `hguae9` E-02), and compare to the table and leaf map hguae9 recorded at its execution (V-03/V-04 of `hguae9`); any module whose core coverage fell, or any declared leaf no longer driven by a core test, is restored in this child by marking an existing fast behavioral test `core` or adding one (the hguae9 30s core budget guard must still pass). Declared leaves added to `command_surface.get_declared_leaves()` since hguae9 are listed separately: they are new, not regressions, and are driven by a core test only if hguae9's own rule requires it.
  - Depends on: E-02
  - Expected outcome: zero core coverage regressions per module; every leaf hguae9 recorded as driven is still driven; bare `python3 -m pytest` passes its budget guard.
  - Execution state: pending

### Task group 2: mutation spot-check

- [ ] E-04 Build the sample from the decision-table research: (a) every deleted test (category starting `delete`) whose source or docstring cited a backlog id6, plan id6 or incident (consolidated defect-citing tests are included too, since their row must still catch the defect); (b) a seeded random sample (`random.Random(<seed recorded>)`) of at least 20 further deleted or consolidated node ids drawn across all three children, stratified so each child contributes in proportion to its population with at least 3 each where its population allows (a child with fewer eligible rows contributes all of them). `c8bfp9` deletes nothing (its own gate), so its eligible population is the tests it SPLIT or CONVERTED to in-process and any `xfail` or mark change, recorded in its research rows. Structure-pin deletions (`tv72xy` category `structure`/`name-shape`/`arch-freeze`) that E-05 will classify not-applicable are EXCLUDED from the random draw before sampling, so the 20 are all applicable; they remain in (a) if they cite a defect. Record the sample list, seed, population sizes per child and category, and the exclusion count. The defect-citing set (a) is derived by `git show <Set-start HEAD>:<path>` of each deleted or consolidated test and a search of its name, docstring and body for an id6 that resolves through `aw find` or an incident/run id (the same rule `qqrgv3` E-05 uses), not from the 345-file authoring census.
  - Depends on: none
  - Expected outcome: sample list recorded with seed; random part at least 20 applicable node ids plus the full defect-citing set; stratification counts recorded.
  - Execution state: pending
- [ ] E-05 For each sampled test: read the original test at the Set start commit (`git show <base>:<path>`), identify the production behavior it guarded and the code it targeted (by symbol), apply a one-line mutation that reintroduces that bug (for a defect-citing test, the bug the cited id6 describes), run the retained tests whose `percov` contexts (E-01 final data, `percov_analyze` per-test sets; these include subprocess-attributed contexts) cover the mutated line, and then the full suite `python3 -m pytest tests/ -m ''` if that selection passes, record which retained test failed, and revert the mutation (verify `git diff -- agent_workflows/` empty after each). Structure-pin deletions (`tv72xy` category) whose "bug" was a refactor rather than a behavior change are recorded as not-applicable with that reason, and do not count toward the 20. The mutation must make the ORIGINAL test fail: run the original test (from the Set-start commit, in the temporary worktree of E-01 or copied to a scratch file under `tests/` that is deleted afterwards) against the mutated code and record its failure; a mutation the original test does not catch is not the bug it guarded and is replaced by one it does catch. If no one-line mutation makes the original fail, record the test as `no-detecting-mutation` with the attempts (it guarded nothing behavioral), and it does not count toward the 20. Work through the sample in batches with at most one mutation applied at a time.
  - Depends on: E-04
  - Expected outcome: a results table (node id, symbol, mutation one-liner, original test fails yes/no, catching retained test, revert verified); every mutation the original catches is caught by some retained test, or goes to E-06.
  - Execution state: pending
- [ ] E-06 For any mutation nothing caught: restore the original test or write a better behavioral one that fails on the mutation and passes without it, then re-run that mutation to show it is now caught. Update the decision-table row (category becomes `restored`).
  - Depends on: E-05
  - Expected outcome: zero surviving mutations after restorations, each fix demonstrated by a fail-then-pass pair.
  - Execution state: pending

### Task group 3: flakes and final measurements

- [ ] E-07 Flake check: three full runs `python3 -m pytest tests/ -m ''` with `pytest-randomly` enabled and three distinct recorded seeds (`-p randomly --randomly-seed=<n>`), plus, for every test that failed in any randomized run, a rerun of that node id alone serially (`-o addopts="" -n 0 -p randomly --randomly-seed=<same n>`) and a rerun of its whole module serially with the same seed, to separate ordering dependence from xdist interaction; record which applies. A test that fails under reordering or `-n 6` but passes serially is fixed in this child (a test-isolation fix, for example a missing reset or a shared temp path, is in scope) or quarantined with `@pytest.mark.xfail(strict=False, reason="flaky: <backlog id6>")` plus a backlog item filed via `aw backlog new` (Work-Kind `bug` if it reflects a production defect, which then carries `- Blocks-Release: next`; a pure test-isolation flake that cannot be fixed here is Work-Kind `chore`); never silently deleted. A test that also fails serially is not a flake: it is a real failure, fixed or filed as a `bug` with the gate, and E-08/E-10 do not proceed until it is dispositioned.
  - Depends on: E-06
  - Expected outcome: three passing randomized runs (after fixes), or each flake listed with its disposition (fixed with the rerun showing pass, or quarantined with backlog id6); zero unexplained failures.
  - Execution state: pending
- [ ] E-08 Final measurements: collected count (`--collect-only -m ''`), module count (`tests/test_*.py`), three warm full runs (median, target under 120s), `--durations=20`, union line and branch coverage (from E-02's final comparison), bare `python3 -m pytest` core summary and wall time, all against the Set baseline: collected count and wall times from the `qqrgv3` baseline `meta.json` and the `c8bfp9` E-01 measurement (the `offdhr`/`7ry5kv` figures, 8794 collected and 565.28s at `6ea45c974`, are reported as historical context; review: the Set-start tests collect 9101 at current code, so counts drift and are re-derived). Every run with `AW_CONFIG_DIR` unset (`c8bfp9` F-7).
  - Depends on: E-07
  - Expected outcome: before/after table complete; median under 120s, or the miss recorded with `c8bfp9`'s justification list and reported to the maintainer (`c8bfp9` OQ-02: the executor reports, never decides, a miss).
  - Execution state: pending

### Task group 4: records

- [ ] E-09 Finalize the decision-table research (`qqrgv3`-created, per-row node id, category, reason, surviving node id, mutation result where sampled): add classification counts per category, the list of tests kept despite matching a delete criterion with the compelling reason, flake dispositions, and set its outcome with `aw research set-outcome <id6> --to informational --apply` (it stays `status: active` while Set `testprune` is open; moving it to `reference` with `aw research promote <id6> --to reference` is done only if the orchestrator `8wfzb5` is the last open plan, otherwise left to the Set's close). Then run `aw research index --check`.
  - Depends on: E-03, E-08
  - Expected outcome: decision table has counts per category, the kept-despite-criterion list and the flake dispositions; its outcome is set; `aw research index --check` passes.
  - Execution state: pending
- [ ] E-10 Write the Set's final report as a NEW research record (`aw research new --kind assessment --set testprune --slug test-prune-final-report --topic testing --summary "<counts and wall time>" --apply`; omit `--order` so the tool assigns the next free order in the set, since `offdhr` holds 01 and the `qqrgv3` decision table takes the next) containing every "Evidence required in the final report" item from prompt `4ul37x` (before/after test count, module count, median wall time, `--durations=20`, union line and branch coverage; per-category counts; every deleted node id and reason by reference to the decision table; mutation results; kept-despite-criterion list; flakes and dispositions; every file changed by path from `git diff --name-only <Set-start HEAD>..HEAD` restricted to the Set's commits, which are those carrying `AW-Item: <qqrgv3|tv72xy|83nnyn|c8bfp9|vgus66>` trailers (`git log --format=%H --grep='AW-Item: <id6>'`), since other plans' commits also landed on `main` meanwhile), then run `aw research index --check`. Add one line under `## 2.0.0 (pending)` in `CHANGELOG.md` using the existing `- Changed:` prefix (user-facing prose: no em or en dashes) stating the new full-suite count, the full-suite wall time, and that coverage parity and a mutation spot-check were verified. Run `aw sanitize --agent`.
  - Depends on: E-09
  - Expected outcome: final report present with every required item; CHANGELOG line present with no em or en dash; `aw research index --check` and `aw sanitize --agent` pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Research records are created and indexed only via `aw research new` / `aw research index` (AGENTS.md "Durable reference"); do not hand-name them.
- CHANGELOG is user-facing: no em or en dashes (AGENTS.md execution contract); the pending section is `## 2.0.0 (pending)`, whose entries are flat bullets with `Added:`/`Fixed:`/`Changed:` prefixes (no testing or internal subsection exists).
- The Set's coverage tooling is `qqrgv3`'s (`tests/tools/percov_run.py`, `percov_analyze.py --compare`, `classify.py`), the core tooling is `hguae9`'s (`tests/tools/core_measure.py`, `leaf_probe.py`), and the decision-table research record with its "Recorded deletions" table is created by `qqrgv3` E-07 and appended to by `tv72xy`, `83nnyn`, `c8bfp9`.
- Research shelf status (`todo`/`active`/`reference`/`archive`) and outcome are tool-owned (`aw research promote`, `aw research set-outcome`); `INDEX.json`/`INDEX.md` are generated and gitignored (`.aw/records/research/README.md`).
- `conftest.py` pops `AW_CONFIG_DIR` and sandboxes `AW_HOME` for tests; timings taken from an agent lane must unset `AW_CONFIG_DIR` (`c8bfp9` F-7).
- Live bugs must carry `- Blocks-Release:` (AGENTS.md "Every live bug gates the next release"), so a flake quarantined because of a production defect is filed `bug` with the gate.
- P16: restored coverage must exercise the code and assert on real outputs, never read source.
- `livecorpus` tests stay and are part of the full run measured here.
- Subprocess-launched tests recorded no context in the `offdhr` baseline; `qqrgv3`'s plugin attributes subprocess children to the spawning node id, but E-05 still follows the per-test-context selection with a full-suite run whenever it passes, because a context can be missing for a test that executes no measured line.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Historical baseline: 8794 collected, 565.28s, 75% line (72507/93730) and 26266/37902 branches, lines-and-branches from pytest-cov without subprocess attribution; superseded as the bar by the `qqrgv3` baseline | research `7ry5kv` "full (8794 tests)", `offdhr` CORRECTION |
| F-2 | Coverage parity cannot prove assertion strength; mutation sampling is required | prompt `4ul37x` Method step 3 |
| F-3 | 345 test files cite id6s in a defect context; the deleted subset is enumerated from the decision table | `rg -l` at authoring |
| F-4 | `mutmut` is not installed; hand mutations are the method | `pip show mutmut`: "Package(s) not found: mutmut" (re-checked at review) |
| F-5 | Production code moves under the Set: 383 commits and 78 changed files under `agent_workflows/` between `6ea45c974` and review HEAD `20f1a9dae`, so a raw baseline-versus-final line comparison mixes production changes with test changes | `git rev-list --count`, `git diff --stat 6ea45c974..HEAD -- agent_workflows/` |
| F-6 | The Set-start tests can be run over current code: checking out `tests/` and `conftest.py` from `6ea45c974` into a temporary worktree restored 55 paths and collected 9101 tests (current tests at review: 9496) | review probe, worktree removed afterwards |
| F-7 | Commits from other plans land on `main` during the Set, so `git diff --name-only <base>..HEAD` overstates "every file changed"; Set commits carry `AW-Item: <id6>` trailers | `git log` trailers (for example `AW-Item: c8bfp9`) |

## Proposed changes (ordered, validatable)

E-01..E-03 coverage parity and core parity -> E-04..E-06 mutation spot-check with restorations -> E-07 flakes -> E-08 final measurements -> E-09 decision table finalized -> E-10 final report and CHANGELOG. E-04 is independent of E-01 and may run in parallel.

## Deferred / out of scope (with reason)

- Full mutation testing of `agent_workflows/` (every mutant): disproportionate cost; the prompt requires a spot-check.
  - Carrier-Declined: prompt `4ul37x` specifies "a random sample of at least 20 ... and every deleted test that cites a defect id".
- Fixing production defects a flake reveals: filed as backlog `bug` items with the release gate in E-07, not fixed here.
  - Carrier-Declined: carried by the backlog item E-07 files at execution, whose id6 is not known until then.

## Scope check

- Over-scope: none.
- Under-scope: none; restorations in E-02, E-03 and E-06 make this child able to close the gaps it finds instead of only reporting them.

## Required tests / validation

E-07's three randomized full runs and E-08's three warm full runs (`AW_CONFIG_DIR` unset), both `percov_analyze --compare` outputs, `core_measure` and `leaf_probe` output, every mutation run with its original-test and retained-test results, any restored test module (`python3 -m pytest <module> -o addopts=""`), and the bare `python3 -m pytest` summary, all pasted.

## Spec / documentation sync

CHANGELOG.md line in E-10. No spec governs the test suite, and no production code changes (mutations are temporary). If a restored test or a flake fix needs `conftest.py`, it is declared in Scope-Paths; any other out-of-scope path is justified at finalize.

## Open questions

### OQ-01: What counts as "the bug the test was meant to catch" for a test without a defect citation?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved: the mutation inverts or removes the specific condition, return value or emitted field the original test's strongest assertion checked, in the production symbol that assertion reached (identified from the test body and its per-test coverage context). The mutation one-liner is recorded so a reviewer can dispute it.

### OQ-02: Is a justified lost line acceptable, or must parity be exact?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the prompt, which says union coverage "must not drop; list and justify (or restore) every line or branch that lost all coverage", so justification is permitted. This plan restores by default and justifies only lines covered solely by a recorded structure-pin deletion or demonstrably unreachable (E-02); lines removed from source cannot appear because the parity comparison runs over current code (E-01). The maintainer reviews the justification list in the final report. (Owner corrected at review: no maintainer answer is recorded.)

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `meta.json` of the final and baseline runs (HEAD, `pytest_exit: 0`), the totals table for baseline, Set-start-tests-on-current-code and final, both `percov_analyze --compare` outputs with the test-isolating one's lost-lines and lost-arcs lists (or its "none"), and the list of Set-start tests excluded as failing on current code with their failure lines.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted per-line disposition rows, each restoration's fail-on-mutation and pass-on-revert runs with empty `git diff -- agent_workflows/` after revert, the restored test modules' pass lines, and the rerun comparison output showing the remaining lost set empty or fully justified.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `core_measure` per-module comparison (no module lower), `leaf_probe` driven/declared totals and any previously driven leaf now undriven (expected none) versus hguae9's recorded values, the list of leaves new since hguae9, and the bare `python3 -m pytest` summary line with the budget guard passing.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted sample list with seed, population sizes per child and category, the not-applicable exclusion count, defect-citing count with the id6 each cites, and per-child stratification counts (random sample at least 20 applicable).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted results table with, for each mutation, the original test's failure line against the mutated code, the pytest failure line of the catching retained test (or "none, to E-06"), and the empty `git diff -- agent_workflows/` after revert; the not-applicable and `no-detecting-mutation` rows with reasons and attempts.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: for each surviving mutation, pasted fail-with-mutation and pass-without-mutation runs of the restored or new test; or the statement, backed by V-05, that none survived.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted three randomized full-run summary lines with seeds, the single-test and module serial reruns for each failure with the same seed, each flake's disposition (fix diff and passing rerun, or `xfail` reason plus backlog id6 and its `- Work-Kind:`/`- Blocks-Release:` lines), and any serial-reproducing failure's disposition.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted before/after table: collected count, module count, three wall times and median, `--durations=20`, union line and arc coverage (from E-02's final comparison), and core summary line and wall time, with the baseline source of each "before" value named, and the miss report if the median is not under 120s.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted decision-table counts per category, the kept-despite-criterion list, the flake disposition section, the `aw research set-outcome` result, and `aw research index --check` output.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: pasted final report path and front matter (id, set, order, summary), its section headings mapped one-to-one to the prompt `4ul37x` "Evidence required in the final report" bullets, the changed-file list's derivation command and count, the CHANGELOG diff line (with a `grep -nP '[\x{2013}\x{2014}]'` over it returning nothing), `aw research index --check` output, and the `aw sanitize --agent` result record.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and explicit human approval (all open questions resolved), and only after `c8bfp9` is executed (Item-Dependencies), in an isolated worktree (`aw work begin vgus66`, or the runner's lane). Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is allowed when needed and justified at finalize (`--scope-reason`), and a declared but unmodified path is acknowledged (`--scope-ack`). This plan changes no production code: every mutation is temporary, at most one is applied at a time, and each is reverted before the next and verified by an empty `git diff -- agent_workflows/`; temporary worktrees (E-01) and scratch copies of original tests (E-05) are removed afterwards and `git worktree list` shows none left. Never weaken an assertion or delete a test to make a measurement pass. Run every timing with `AW_CONFIG_DIR` unset. Commit restorations, flake fixes, records and the CHANGELOG line via `aw commit vgus66 -- <paths>` (never `git add -A`); never push or tag. You MUST paste the ACTUAL runner, coverage and mutation output in each V-item; never claim a pass, a catch or a timing you did not run. Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize and the move to `executed/`; executed by hand, finish with `aw ipd lint --phase pre-transition` conforming and then `aw ipd finalize vgus66` (never a hand `git mv`), and publish with `aw integration-lock -- git merge --ff-only <branch>`.
