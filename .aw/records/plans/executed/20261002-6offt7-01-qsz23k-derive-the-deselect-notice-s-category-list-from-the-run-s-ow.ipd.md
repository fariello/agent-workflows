# IPD: Derive the deselect notice's category list from the run's own marker filter instead of hardcoding it

- Date: 2026-10-02
- Kind: child
- Concern: `tests/deselect_notice.py`'s runtime notice hardcodes the string `the default run skips 'slow' and 'livecorpus'`, deriving nothing from the marker expression the run actually applied. It is accurate today, so this is DUPLICATED SOURCE and not staleness, and it will silently under-report the moment a third category joins `addopts`. Worse, measured at authoring: the sentence is printed UNCONDITIONALLY, so it already lies today under `-m slow`, under `-m livecorpus`, and under `make test-all` plus a `-k` filter, telling a reader that `slow` and `livecorpus` were skipped in runs that deliberately SELECTED them.
- Scope: Make the notice's parenthetical derive from `config.option.markexpr`, the per-run value pytest resolved from `addopts` plus the command line, so the notice describes the run in front of the reader rather than a remembered configuration. Covers a conservative `not X and not Y ...` reader, a verbatim-expression fallback for any expression that reader declines, a no-marker-filter branch for the `-k`/`--deselect` case, and the behavioral tests for all three branches. EXCLUDES changing `addopts`, any marker semantics, or any test's selection; EXCLUDES touching `agent_workflows/` production code, the managed instruction prose in `engine.py`, and the parity test `tests/test_suite_instruction_marker_parity.py`.
- Scope-Paths: tests/deselect_notice.py, tests/test_deselect_notice.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 6offt7
- Set: 6offt7
- Order: 1
- Highest E allocated: 06
- Author: agent
- Id: qsz23k

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: qsz23k verified (set 6offt7, attempt 1).
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 /plan-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: the names branch would credit a `-k` share of the count to marker categories, so a mixed case was added), PR-002, PR-003, PR-004 (LOW, fixed). Premise, F-02 defect, F-03 and F-04 re-verified by probe. Full record: `.aw/records/reviews/20261002-6offt7-01-qsz23k-derive-the-deselect-notice-s-category-list-from-the-run-s-ow.review.md`.
- 2026-10-03 reviewed (aw set): plan-review APPROVE WITH REVISIONS APPLIED
- 2026-10-02 draft (agent): created.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `6offt7` in lane worktree at HEAD `9becd53d9`. GATE NOTE: the item carries NO `- Blocks-Release:`, so this plan inherits none, and the INHERITED `- Work-Kind: chore` is CORRECT under the perceptibility test: no user waits on the notice, the suite's selection is unchanged, and the only cost is a misleading line in terminal output. THE ITEM'S PREMISE VERIFIES, AND IS WEAKER THAN WHAT IS ACTUALLY WRONG. The item frames this as a latent future problem ("That string is correct today ... When a third category is added, the notice silently under-reports"). Measured at authoring, the notice is ALREADY WRONG in three shipped invocations, because the parenthetical is unconditional and names the DEFAULT configuration rather than the run: under CI's own `python -m pytest tests/ -n auto -m slow` step (`.github/workflows/tests.yml`) it prints "the default run skips 'slow'" while `slow` is the only category SELECTED; under `-m livecorpus` likewise; and under `make test-all` (`-m ''`) with any `-k`, it claims a marker deselection in a run that has no marker filter at all and then tells the reader to "run everything with: make test-all", which is the command they are already running. That is a stronger and cheaper-to-falsify reason to fix it than the future-category one, so this plan leads with it (F-02). THE DESIGN QUESTION THE PRIOR PLAN DEFERRED IS ANSWERED, NOT REOPENED. `zb81ah`'s OQ-01 left the maintainer three options (hardcode, parse the expression, or print it verbatim) and named the real cost of the middle one: "`-m 'not slow and not livecorpus'` is a boolean expression, and a general reader of it is more machinery than the notice deserves, while a naive `not (\w+)` regex would be a second approximation that can also be wrong". This plan takes the middle option ONLY where it is provably exact and falls back to the verbatim option everywhere else, which is what makes a conservative reader honest instead of a second approximation: measured at authoring, the reader accepts `not slow and not livecorpus` and `not slow and not livecorpus and not gpu`, and REFUSES `slow`, `not (slow or livecorpus)`, `not slow or not gpu`, `not slow and livecorpus`, and `not slow AND not gpu`, declining to a verbatim print in each (F-04). ONE CORRECTNESS POINT AN EXECUTOR MUST NOT MISS: the notice must read `config.option.markexpr`, NOT `pyproject.toml`. The option value is what pytest resolved for THIS run including the command line, so a `-m slow` override is visible; reading the file back would reproduce the exact bug being fixed in a new place and would also re-couple a test plugin to a config file it should not parse (F-03, F-05).

## Goal

Make the deselect notice describe the run that just happened. The count is already per-run and correct; the parenthetical explaining WHY tests were deselected is a hardcoded sentence about the default configuration, so it is wrong whenever the run is not the default and will under-report when the default gains a category. Derive the explanation from `config.option.markexpr`, print the expression verbatim when it is not a plain conjunction of negated names, and say so plainly when no marker filter is active at all.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: derive the explanation

- [x] E-01 RE-MEASURE the premise at execution HEAD rather than trusting this plan's figures, because `addopts` is exactly the line a concurrent lane may change and because the notice text itself is a one-line edit another lane could have made. Confirm each of: (a) the verbatim `addopts` value in `pyproject.toml`, located by the content string `addopts = "-q -n auto`; (b) that `tests/deselect_notice.py`'s `pytest_terminal_summary` still writes a hardcoded category list, by READING the function, and record the exact current wording; (c) that the notice is still printed unconditionally, by RUNNING the real plugin under `-m slow` and under `-m '' -k <expr>` in a throwaway temp project and pasting the lines it prints; and (d) the current deselection split, re-derived with `python3 -m pytest --collect-only -q` plus `-m slow`, `-m livecorpus` and `-m ''` collections. If `addopts` has changed shape (for example to an expression the E-02 reader would decline), do NOT stop: that is a legitimate input and E-02's fallback branch is what handles it. Report the measured state and any drift from this plan's figures at finalize instead of absorbing it silently.
  - Depends on: none
  - Expected outcome: the configured `addopts`, the current notice wording, pasted proof of the unconditional-print defect under at least `-m slow`, and the re-derived four-way collection split, all measured at execution HEAD with drift from F-01/F-02/F-06 reported.
  - Execution state: performed

- [x] E-02 ADD a module-level reader to `tests/deselect_notice.py` that turns a marker expression into the list of categories it negates, returning a THREE-WAY result so each caller branch is distinguishable: the empty list for an empty or whitespace-only expression (no marker filter is active), a non-empty list of names for a plain conjunction of negated bare names, and `None` for any expression it declines to interpret. BE CONSERVATIVE BY CONSTRUCTION AND DECLINE LOUDLY, because the whole justification for parsing at all is that an approximation is worse than a verbatim quote (`zb81ah` OQ-01). Accept ONLY a sequence of `not <name>` terms joined by lowercase `and`, where `<name>` matches a bare Python identifier; split on the word `and` with a word-boundary regex so a marker named `android` cannot be split mid-token, and require EVERY term to match or return `None` for the whole expression. Do NOT attempt `or`, parentheses, uppercase operators, a bare positive name, or a mixed conjunction. Give the function a docstring stating that it is deliberately partial and that `None` means "print the expression verbatim", so a later reader does not mistake its narrowness for a bug and widen it. MEASURED AT AUTHORING, the accepted and declined sets are exactly as F-04 records; implement to that table.
  - Depends on: E-01
  - Expected outcome: a named, importable reader in `tests/deselect_notice.py` whose three return shapes are distinguishable and which declines every expression in F-04's reject column.
  - Execution state: performed

- [x] E-03 REWRITE the parenthetical in `pytest_terminal_summary` to branch on E-02's result, read from `getattr(config.option, "markexpr", "") or ""`. USE THE OPTION VALUE AND NOTHING ELSE: it is what pytest resolved for THIS run from `addopts` plus the command line, so an overriding `-m slow` is visible to the notice, and reading `pyproject.toml` back from a test plugin would reproduce the very duplicated-source defect this plan removes (F-03, F-05). THE `config` PARAMETER IS ALREADY IN THE HOOK SIGNATURE, so no plumbing is needed. The three branches, in substance: (a) names present, say that this run's marker filter deselects those categories and name them, and when `config.option.keyword` or `config.option.deselect` is ALSO non-empty, say that `-k`/`--deselect` contributed to the count too, so the count is never attributed wholly to the marker categories (measured at review: under the default `addopts` plus `-k 'not test_b'` the count was 3, of which 2 came from the marker filter and 1 from `-k`; in this repository a bare `python3 -m pytest -k <expr>` deselects thousands of tests through `-k`, and the unqualified form of (a) would credit all of them to `slow`/`livecorpus`); (b) empty list, say that no marker filter was active so `-k` or `--deselect` accounts for the count, and in this branch do NOT advise `make test-all`, because the reader may already be running it; (c) `None`, print the expression VERBATIM and attribute the count to it rather than interpreting it. Keep the `NOTE: <N> tests were deselected` prefix and the count EXACTLY as they are: the count is already per-run and correct, four shipped tests assert on that prefix, and `tests/test_orchestrate_isolation.py` parses `N passed, M deselected` from pytest's own summary line rather than from this notice, so the prefix is the compatibility surface and the parenthetical is the only thing changing. Keep the `make test-all` advice in branch (a) only. This text is developer-facing terminal output rather than user-facing product prose, so spend no effort avoiding dashes, but keep it to one line.
  - Depends on: E-02
  - Expected outcome: the notice's parenthetical is computed per run from `config.option.markexpr`; the `NOTE: <N> tests were deselected` prefix and count are byte-unchanged; no reference to `pyproject.toml` appears anywhere in the module.
  - Execution state: performed

### Task group 2: prove each branch behaviorally

- [x] E-04 EXTEND `tests/test_deselect_notice.py` with outcome tests for all three branches, following the module's EXISTING shape rather than inventing a second one: its `setUp` already writes a `pytest.ini` and a sample test module into a `tempfile.TemporaryDirectory`, and `_run_pytest` already spawns `python3 -m pytest -p tests.deselect_notice` in that directory with `PYTHONPATH` pointed at the repo root. ADD A SECOND FIXTURE PROJECT carrying THREE marker categories (`slow`, `livecorpus`, and a third name this repo does not use, for example `gpu`) with `addopts = -q -m 'not slow and not livecorpus and not gpu'`, which is the FUTURE-CATEGORY case the backlog item is actually about, and assert the notice names all three. Then assert: the verbatim-fallback branch under `-m 'not (slow or livecorpus)'`, which the E-02 reader must decline; the no-marker-filter branch under `-m '' -k <expr>`, asserting both that the output does NOT claim a marker deselection and that it does NOT advise `make test-all`; and the MIXED case, the default fixture `addopts` plus `-k <expr>`, asserting the notice names the marker categories AND mentions `-k` as a contributor. Assert on the printed OUTPUT of a real pytest run, never by importing the reader and asserting on its return value alone, and never by reading the plugin's source.
  - Depends on: E-03
  - Expected outcome: four new cases covering the names, verbatim, no-filter and mixed `-m`-plus-`-k` branches, all passing, each driving a real pytest subprocess and asserting on its terminal output.
  - Execution state: performed

- [x] E-05 ADD the case that pins the DEFECT THIS PLAN ACTUALLY FIXES, which is the unconditional print: run the fixture project with `-m slow` (the shape CI's own second step uses) and assert the notice does NOT claim that `slow` was skipped. State in the test's name or docstring that this is the regression guard for a notice that described the default configuration instead of the run. ALSO assert the four EXISTING cases still pass unchanged, which they must, since none of them overrides `-m` and all four assert only on the `NOTE: 1 tests were deselected` prefix: if any of the four needs editing, that is a signal E-03 changed the prefix it was told not to change, so report it rather than adapting the test.
  - Depends on: E-03
  - Expected outcome: one new case proving the notice no longer claims a category was skipped in a run that selected it, plus the four pre-existing cases passing with their assertions byte-unchanged.
  - Execution state: performed

- [x] E-06 PROVE the new coverage is falsifiable and that nothing else regressed. Run the targeted module with `python3 -m pytest tests/test_deselect_notice.py -o addopts=""` and the full suite BARE (`python3 -m pytest`). Then apply a NEGATIVE CONTROL: revert the parenthetical to the hardcoded string while leaving the tests in place, confirm that the names-branch, verbatim-branch, no-filter-branch, mixed and `-m slow` cases FAIL, and restore. A single control suffices here because every new case consults the derived text, unlike a guard whose cases reach the changed symbol by different paths. BASELINE THE SUITE BEFORE EDITING AND JUDGE ON THE DELTA OF FAILING NODE IDS, because a bare run is NOT all-green at authoring: measured on a clean tree at HEAD `9becd53d9`, `3 failed, 4624 passed, 2 skipped` where all three failures are in unrelated modules and all three reproduce with this plan's own new file removed from the tree (F-07). Do not inherit that result; re-derive it and attribute every failing node to a named E-item or to the pre-existing set.
  - Depends on: E-04, E-05
  - Expected outcome: the targeted module passes; the bare suite shows no NEW failing node attributable to this plan; under the hardcoded-string control the five derived-text cases fail; the control is reverted and `git diff` shows only the two declared scope paths.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `tests/deselect_notice.py` is registered as a plugin from the root `conftest.py` through `pytest_plugins = ["tests.deselect_notice", "tests.livecorpus_notice"]`, so it loads in EVERY pytest invocation in this repository. It is not packaged: no `pyproject.toml` wheel or sdist include names `tests/`, so nothing installs into a managed repo and this plan changes no shipped artifact.
- The plugin's `pytest_terminal_summary` hook already receives `config`, so `config.option.markexpr` is reachable with no new plumbing. The module already handles the xdist split, accumulating per-worker counts through `workeroutput` and taking `max(worker_max, _deselected_count)`; E-03 touches none of that.
- `tests/livecorpus_notice.py` is the sibling precedent for a notice-only plugin that is deliberately partial and DOCUMENTS its bounds in the module docstring (its "THE DETECTOR'S FOUR BOUNDS" section). E-02's docstring follows that convention: state what the reader declines and why, so narrowness reads as design.
- `tests/test_deselect_notice.py` drives real pytest SUBPROCESSES against a temp project and asserts on stdout, which is the outcome-testing shape GUIDING_PRINCIPLES P16 requires; it also uses `runner_shared.parse_suite_summary` to read the count line. E-04 extends that shape rather than importing the reader and asserting on its return value.
- `tests/test_suite_instruction_marker_parity.py` is the parity guard for a DIFFERENT surface (`engine.agents_pointer_prose` versus `addopts`) and uses a 3.9-safe flat-TOML parse because `tomllib` is 3.11+ while CI's floor is 3.9. It is NOT this plan's model and is not edited: the notice must not read `pyproject.toml` at all (F-05).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The item's stated defect reproduces exactly: the category list is a literal, deriving nothing. | `tests/deselect_notice.py`'s `pytest_terminal_summary` writes `f"NOTE: {total_deselected} tests were deselected by -m/-k and did not "` followed by the literal continuation `"run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all"`. The function reads `_worker_counts` and `_deselected_count` and nothing else; its `config` parameter is unused. |
| F-02 | **THE NOTICE IS ALREADY WRONG TODAY, IN THREE SHIPPED INVOCATIONS, WHICH IS STRONGER THAN THE ITEM'S LATENT-FUTURE FRAMING.** The parenthetical is unconditional, so it describes the default configuration even when the run overrode it. | Measured at authoring with the REAL plugin (`PYTHONPATH=<repo> python3 -m pytest -p tests.deselect_notice`) against a temp project having markers `slow`/`livecorpus` and `addopts = -q -m 'not slow and not livecorpus'`. Under `-m slow`: `NOTE: 2 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all` alongside `1 passed, 2 deselected`, i.e. it claims `slow` was skipped in the run that selected ONLY `slow`. Under `-m '' -k 'not test_a2'`: the same sentence plus the same `make test-all` advice, in a run with NO marker filter that is already the `make test-all` shape. Under `-m 'not slow'`: same sentence, naming a category this run did not deselect. `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -m slow` as its own step, so the first case is a shipped CI invocation and not a hypothetical. |
| F-03 | `config.option.markexpr` carries the per-run resolved expression, including a command-line override, and is populated on the COORDINATOR under xdist, which is the process that prints the terminal summary. | Probe conftest printing `config.option.markexpr` in `pytest_terminal_summary`: with `addopts = -q -m 'not slow and not livecorpus'` and no override it reported `'not slow and not livecorpus'`; under `-m ''` it reported `''`; under `-m 'not slow'` it reported `'not slow'`; under `-n 2` it reported the addopts value on the coordinator. With no `addopts` at all it reported `''` rather than raising, and `hasattr(config.option, "markexpr")` was True in every case. |
| F-04 | A CONSERVATIVE reader is exact on every expression this repository plausibly configures and DECLINES every form it cannot represent, which is what makes E-02 honest rather than a second approximation. | Probe implementing the E-02 rule (split on word-boundary `and`, require every term to match `^not\s+([A-Za-z_]\w*)$`). ACCEPTED: `''` -> `[]`; `'   '` -> `[]`; `'not slow and not livecorpus'` -> `['slow','livecorpus']`; `'not slow and not livecorpus and not gpu'` -> `['slow','livecorpus','gpu']`; `'not slow'` -> `['slow']`; `'not slow and not live_corpus'` -> `['slow','live_corpus']`; heavy whitespace `'  not  slow   and   not  gpu '` -> `['slow','gpu']`. DECLINED (returned `None`): `'slow'`, `'not (slow or livecorpus)'`, `'not slow or not gpu'`, `'not slow and livecorpus'`, `'not slow and not (gpu)'`, `'not slow AND not gpu'`. Driven end to end through a probe plugin, the declined cases printed the expression verbatim and the three-category case named all three. |
| F-05 | READING `pyproject.toml` WOULD BE THE WRONG FIX and would recreate the defect in a new place, so this is recorded as a rejected option rather than left for an executor to rediscover. | Two independent reasons, both measured. First, `addopts` is only one of two inputs: under `-m slow` the file still reads `not slow and not livecorpus` while the run's actual filter is `slow` (F-03), so a file-derived notice would still be wrong in exactly F-02's three cases. Second, the file is not reliably present: the plugin runs against ANY project (its own test module builds a temp project with a `pytest.ini` and no `pyproject.toml` at all), so a file read would have to degrade anyway. `tests/test_suite_instruction_marker_parity.py` legitimately parses the file because its subject IS the file-versus-prose relationship; the notice's subject is the run. |
| F-06 | The four-way collection split at authoring HEAD, recorded so E-01 compares against a real baseline rather than a remembered one. | `python3 -m pytest --collect-only -q` at HEAD `9becd53d9`: 4629 collected with `NOTE: 232 tests were deselected`. `-m slow`: 227 collected, 4634 deselected. `-m livecorpus`: 5 collected, 4856 deselected. `-m ''`: 4861 collected, no notice printed (nothing deselected), which also confirms the notice is correctly silent when no deselection occurs. |
| F-07 | **A BARE SUITE RUN IS NOT ALL-GREEN AT AUTHORING, and all three failures are unrelated to this plan**, so E-06 must judge on a delta rather than an absolute green bar. | Bare `python3 -m pytest` on a clean tree at HEAD `9becd53d9`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 107.86s`. The three are `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` (a live-corpus assertion failing on a third party's spec, `20261001-89xjll-...spec.md: ['attention.unsafe-field']`), and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`. All three reproduce in isolation with `-o addopts=""` AND reproduce with this plan's own new file moved out of the tree, so none is caused by this lane. |
| F-08 | The `NOTE: <N> tests were deselected` PREFIX is a compatibility surface and the parenthetical is not, which bounds E-03's edit. | Four cases in `tests/test_deselect_notice.py` assert on `"NOTE: 1 tests were deselected"` or on `"tests were deselected"`; none asserts on the category list. A sweep for the notice's wording outside the plugin and its own test module found no other consumer: `tests/test_orchestrate_isolation.py` asserts on pytest's OWN summary line (`11 passed, 45 deselected in 0.26s`), not on this notice, and `agent_workflows/runner_shared.parse_suite_summary` matches `^(?:=+\s*)?(\d+ (?:passed|failed).*?)(?:\s*=+)?$`, which is pytest's count line and cannot match the `NOTE:` line. |
| F-10 | **THE MOST COMMON DEVELOPER INVOCATION MIXES BOTH SOURCES, so a names-only branch would still mis-attribute the count** (added at review). Under the default `addopts` a developer's `python3 -m pytest -k <expr>` keeps `markexpr` at the default conjunction while `-k` deselects most of the suite. Both `config.option.keyword` and `config.option.deselect` are readable on the coordinator, so E-03 can say `-k`/`--deselect` contributed without plumbing. | Review probe, a three-marker fixture with `addopts = -q -m 'not slow and not livecorpus and not gpu'`: `-k 'not test_b'` reported `MARKEXPR='not slow and not livecorpus and not gpu' KW='not test_b'` with `1 passed, 3 deselected` (2 by marker, 1 by `-k`); `--deselect test_s.py::test_a` reported `config.option.deselect == ['test_s.py::test_a']`, and `None` when absent |
| F-09 | `GUIDING_PRINCIPLES.md` credits this notice as a standing mitigation, which is why its honesty matters beyond cosmetics. | P-section on deselecting at collection time: "a marker deselect is announced in every run by `tests/deselect_notice.py`". The backlog item makes the same point, that the notice is "credited as the runtime mitigation for stale instructions", and adds that `tests/test_suite_instruction_marker_parity.py` does not cover it. Verified: that module asserts over `engine.agents_pointer_prose` for both target layouts and never loads the plugin. |

## Proposed changes (ordered, validatable)

1. Add a conservative, deliberately partial marker-expression reader to `tests/deselect_notice.py` with a three-way result: names, empty (no filter), or `None` (decline) (E-02).
2. Branch the notice's parenthetical on that result, reading `config.option.markexpr`, while leaving the `NOTE: <N> tests were deselected` prefix and the count byte-unchanged (E-03).
3. Extend `tests/test_deselect_notice.py` with behavioral cases for the three-category future case, the verbatim fallback, the no-marker-filter case and the mixed marker-plus-`-k` case (E-04).
4. Add the regression case for the unconditional-print defect under `-m slow`, the shape CI itself runs (E-05).

No `agent_workflows/` file is changed. If a production change proves necessary during execution, that is a separate finding to file rather than to absorb here.

## Deferred / out of scope (with reason)

- A GENERAL marker-expression evaluator (handling `or`, parentheses, and positive terms): deliberately out of scope. `zb81ah`'s OQ-01 named this cost precisely ("a general reader of it is more machinery than the notice deserves"), and E-02's decline-to-verbatim branch means the general case is handled HONESTLY rather than handled wrongly.
  - Carrier-Declined: NOTHING TO CARRY, because no gap is left open. Every expression the reader declines still produces a true statement (the expression printed verbatim), so there is no incorrect output waiting for a future fix. Filing a carrier would assert a defect that the fallback branch defines away and would invite a later agent to widen a parser whose narrowness is the point.
- Changing `addopts`, any marker's semantics, or any test's selection: out of scope. This plan changes one line of terminal output and its tests; the deselected COUNT must be unmoved, which V-06 requires as proof.
  - Carrier-Declined: NOTHING TO CARRY, because this row records a NEGATIVE CONSTRAINT rather than deferred work. No defect in `addopts` or in any marker's semantics is asserted anywhere in this plan: F-06 measures the current selection split as the intended configuration and V-06 requires proof it is UNCHANGED. Filing a carrier would assert that a future change to the suite's selection is owed, which it is not, and would invite a later agent to alter selection on this plan's authority.
- Teaching `tests/test_suite_instruction_marker_parity.py` to cover the notice too: out of scope. The backlog item observes that it does not cover the notice, and that observation is CLOSED by this plan from the other side: once the notice derives its text from the run, there is no second hardcoded list for a parity test to pin. A parity test comparing the notice to `pyproject.toml` would re-introduce exactly the file coupling F-05 rejects.
  - Carrier-Declined: THE GAP IS CLOSED BY CONSTRUCTION RATHER THAN DEFERRED. The item's concern is a duplicated source; E-02 and E-03 remove the duplicate, so there is nothing left to keep in parity. E-04's and E-05's cases are the coverage, and they assert on run output rather than on a config file.
- The three pre-existing suite failures recorded in F-07: out of scope and not this lane's. They are in unrelated modules and reproduce with this plan's file absent from the tree.
  - Carrier-Declined: NOT THIS PLAN'S SUBJECT AND NOT SAFELY ATTRIBUTABLE FROM HERE. One is a live-corpus assertion reddened by another party's spec artifact, which is the documented `livecorpus` blast-radius class rather than a defect in this lane's reach; the other two are in modules this plan does not touch and whose causes are unmeasured here. Filing a carrier naming three unrelated failures from a notice-text plan would assert ownership of diagnoses not performed. An executor that still sees them should report them with its measured evidence so they can be filed on their own merits.

## Scope check

- Over-scope: none. Two paths, both under `tests/`, both named in `- Scope-Paths:`.
- Under-scope: the declared paths cover every intended edit. NO `.spec.md` file is touched, so no spec amendment is declared and none is required: the notice is not spec-governed and no marker semantics change. FOUR NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, no file under `agent_workflows/` may appear in the changed set; the managed instruction prose in `engine.py` is a different surface already fixed by `zb81ah`. SECOND, the `addopts` assignment line in `pyproject.toml` must be byte-identical afterwards and the bare suite's DESELECTED count must be unmoved, which together are the observable proof that documentation changed and selection did not. THIRD, the `NOTE: <N> tests were deselected` prefix and the count expression must be byte-unchanged, since four existing tests assert on the prefix (F-08). FOURTH, `tests/test_suite_instruction_marker_parity.py` is NOT edited.

## Required tests / validation

- `python3 -m pytest tests/test_deselect_notice.py -o addopts=""` as the targeted set, with the actual `N passed` summary pasted. `-o addopts=""` is the repository's prescribed way to reach a narrowed run rather than fighting the configured flags one at a time. Measured at authoring on the UNMODIFIED module: `4 passed in 5.09s`.
- The full suite, `python3 -m pytest`, run BARE per the execution contract (no added flags), to prove no regression elsewhere. RE-DERIVE THE BASELINE ON A CLEAN TREE BEFORE EDITING and judge on the DELTA of failing node ids: a bare run at authoring was NOT all-green (`3 failed, 4624 passed, 2 skipped`), and all three failures are in unrelated modules and reproduce with this plan's file absent (F-07). Do not inherit that result; measure, then attribute every failing node against a named E-item or against the pre-existing set.
- ONE negative control proving the new coverage can actually FAIL: restore the hardcoded parenthetical while keeping the new tests, and confirm the names-branch, verbatim-branch, no-filter-branch, mixed and `-m slow` cases all FAIL. A guard that cannot fail is not a guard. One control is sufficient here, unlike a multi-path guard, because every new case reads the same derived text; if ANY of the five passes under the control, that case is not testing the derivation and must be fixed before finalize.
- Proof that selection did not change: the bare suite's deselected count compared against the F-06 baseline (232 at authoring, re-derived at execution), plus `git diff` over `pyproject.toml` showing it untouched.

## Spec / documentation sync

N/A with reason: this plan changes one line of developer-facing terminal output emitted by a test-only pytest plugin that is not packaged into any wheel or sdist, changes no public contract, no CLI surface, and no `.spec.md` file. `GUIDING_PRINCIPLES.md` references the notice's EXISTENCE as an announcement mechanism (F-09), which stays true and in fact becomes more true, so no doc edit is required; the three-category case E-04 adds is what records the new behavior.

## Open questions

### OQ-01: Should the notice name the deselected categories at all, or only print the marker expression verbatim?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED IN FAVOR OF BOTH, SPLIT BY WHETHER THE DERIVATION IS PROVABLY EXACT, which is what `zb81ah`'s OQ-01 left to the maintainer and what this plan answers from measurement rather than preference. That question listed three options and named the real objection to the middle one: parsing a boolean expression is more machinery than a notice deserves, and a naive `not (\w+)` regex is a second approximation that can also be wrong. The resolution honors that objection instead of overriding it: the reader accepts ONLY a plain conjunction of negated bare names, which is the shape this repository configures and the shape a third category would extend, and DECLINES everything else to the verbatim option the question itself proposed as the cheaper middle ground (F-04). So the common case gets the readable, nameable form that makes `livecorpus` discoverable to someone who has never heard of it, and the uncommon case gets a statement that cannot be wrong because it quotes rather than interprets. THE HONEST COST, recorded rather than hidden: there are now two possible wordings of the same notice, so a reader comparing two runs may see different phrasings. That is accepted because the alternative is a single wording that is false in at least three shipped invocations (F-02).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: the execution HEAD sha, plus pasted output of: the verbatim `addopts` line from `pyproject.toml`; the current body of `tests/deselect_notice.py`'s `pytest_terminal_summary` showing the hardcoded list still present (or, if a lane already changed it, the current text and a statement of the drift); the notice lines printed by a REAL plugin run under `-m slow` and under `-m '' -k <expr>` in a throwaway temp project, showing the unconditional-print defect; and the four-way collection split (default, `-m slow`, `-m livecorpus`, `-m ''`). Must state explicitly whether anything drifted from F-01, F-02 or F-06's figures (default 4629 collected / 232 deselected; `slow` 227; `livecorpus` 5; `-m ''` 4861 with no notice; HEAD `9becd53d9`).
  - Observed evidence: Measured at execution HEAD `0329857d3d9eee784e994dd532ae39e4ba10040c`:
    (a) `pyproject.toml` verbatim `addopts` line:
    `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`
    (b) `tests/deselect_notice.py`'s `pytest_terminal_summary` prior to edit:
    ```python
    def pytest_terminal_summary(
        terminalreporter: Any, exitstatus: Any, config: Any
    ) -> None:
        worker_max = max(_worker_counts) if _worker_counts else 0
        total_deselected = max(worker_max, _deselected_count)
        if total_deselected > 0:
            terminalreporter.write_line(
                f"NOTE: {total_deselected} tests were deselected by -m/-k and did not "
                "run (the default run skips 'slow' and 'livecorpus'); run everything with: "
                "make test-all"
            )
    ```
    (c) Unconditional-print defect reproduction in temp project:
    Under `-m slow`:
    ```
    .                                                                        [100%]
    NOTE: 1 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    1 passed, 1 deselected in 0.03s
    ```
    Under `-m "" -k not test_slow`:
    ```
    .                                                                        [100%]
    NOTE: 1 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    1 passed, 1 deselected in 0.09s
    ```
    (d) Four-way collection split at execution HEAD:
    - default: `6446/6704 tests collected (258 deselected) in 10.81s`, notice: `NOTE: 258 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all`
    - `-m slow`: `248/6704 tests collected (6456 deselected) in 9.92s`, notice: `NOTE: 6456 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all`
    - `-m livecorpus`: `10/6704 tests collected (6694 deselected) in 10.08s`, notice: `NOTE: 6694 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all`
    - `-m ""`: `6704 tests collected in 9.03s`, no notice printed.
    Drift statement: The suite grew from 4861 total tests at authoring HEAD `9becd53d9` to 6704 total tests at execution HEAD `0329857d3` (+1843 tests). Deselected counts: default 258 (authoring baseline 232); slow 6456 (authoring baseline 4634); livecorpus 6694 (authoring baseline 4856); empty `-m ''` 6704 with no notice. The defect reproduced identically.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the reader function's body and docstring, then paste the result of exercising it over F-04's FULL table, both columns, showing each accepted expression's returned name list and `None` for each of `'slow'`, `'not (slow or livecorpus)'`, `'not slow or not gpu'`, `'not slow and livecorpus'`, `'not slow and not (gpu)'` and `'not slow AND not gpu'`. Also show `''` and a whitespace-only string returning the EMPTY LIST rather than `None`, since branch (b) in E-03 depends on those two being distinguishable. State explicitly that the `and` split is word-boundary anchored, and demonstrate it with an expression containing a marker name that CONTAINS the substring `and` (for example `not android`), proving it is not split mid-token.
  - Observed evidence: Reader function body and docstring from `tests/deselect_notice.py`:
    ```python
    def parse_negated_markers(markexpr: str) -> list[str] | None:
        """Turn a marker expression into a list of categories it negates.

        This reader is deliberately partial and conservative by construction.
        Returns:
          - [] for an empty or whitespace-only expression (no marker filter active).
          - list of str for a plain conjunction of negated bare names ('not <name>').
          - None for any expression it declines to interpret (meaning print verbatim).
        """
        if not isinstance(markexpr, str):
            return None
        stripped = markexpr.strip()
        if not stripped:
            return []

        terms = re.split(r"\s+\band\b\s+", stripped)
        names: list[str] = []
        for term in terms:
            m = _TERM_RE.match(term.strip())
            if not m:
                return None
            names.append(m.group(1))
        return names
    ```
    Exercising over F-04's full table (including empty string and whitespace-only returning `[]`):
    ```
    ''                                         -> []
    '   '                                      -> []
    'not slow and not livecorpus'              -> ['slow', 'livecorpus']
    'not slow and not livecorpus and not gpu'  -> ['slow', 'livecorpus', 'gpu']
    'not slow'                                 -> ['slow']
    'not slow and not live_corpus'             -> ['slow', 'live_corpus']
    '  not  slow   and   not  gpu '            -> ['slow', 'gpu']
    'slow'                                     -> None
    'not (slow or livecorpus)'                 -> None
    'not slow or not gpu'                      -> None
    'not slow and livecorpus'                  -> None
    'not slow and not (gpu)'                   -> None
    'not slow AND not gpu'                     -> None
    ```
    Word-boundary anchoring verification:
    The `and` split uses regex `r"\s+\band\b\s+"`. When tested on expressions with marker names containing the substring `and`:
    ```
    'not android'                              -> ['android']
    'not slow and not android'                 -> ['slow', 'android']
    ```
    `not android` is not split mid-token.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the rewritten `pytest_terminal_summary` body, and quote the three branches. Prove the two bounds explicitly: (a) show that the value read is `config.option.markexpr` and paste a search over the module for `pyproject` and for `read_text` showing NO hit, since a file read would recreate the defect (F-05); (b) show the `NOTE: <N> tests were deselected` prefix and the `max(worker_max, _deselected_count)` count expression are byte-unchanged, by pasting `git diff tests/deselect_notice.py` and pointing at the unchanged lines. Also confirm the xdist accumulation hooks (`pytest_testnodedown`, `pytest_sessionfinish`) are untouched.
  - Observed evidence: Rewritten `pytest_terminal_summary` body in `tests/deselect_notice.py`:
    ```python
    def pytest_terminal_summary(
        terminalreporter: Any, exitstatus: Any, config: Any
    ) -> None:
        worker_max = max(_worker_counts) if _worker_counts else 0
        total_deselected = max(worker_max, _deselected_count)
        if total_deselected > 0:
            markexpr = getattr(config.option, "markexpr", "") or ""
            keyword = getattr(config.option, "keyword", "") or ""
            deselect = getattr(config.option, "deselect", None) or []
            has_k_or_deselect = bool(keyword or deselect)

            names = parse_negated_markers(markexpr)
            if names is not None and len(names) > 0:
                if len(names) == 1:
                    cats = f"'{names[0]}'"
                elif len(names) == 2:
                    cats = f"'{names[0]}' and '{names[1]}'"
                else:
                    cats = f"{', '.join(repr(n) for n in names[:-1])} and {names[-1]!r}"
                if has_k_or_deselect:
                    parenthetical = (
                        f"(this run's marker filter skips {cats}, and -k/--deselect also contributed); "
                        "run everything with: make test-all"
                    )
                else:
                    parenthetical = (
                        f"(this run's marker filter skips {cats}); "
                        "run everything with: make test-all"
                    )
            elif names is not None:
                # Empty list: no marker filter active
                parenthetical = (
                    "(no marker filter was active; deselected by -k/--deselect)"
                )
            else:
                # None: print expression verbatim
                if has_k_or_deselect:
                    parenthetical = (
                        f"(filtered by marker expression: '{markexpr}', and -k/--deselect also contributed)"
                    )
                else:
                    parenthetical = f"(filtered by marker expression: '{markexpr}')"

            terminalreporter.write_line(
                f"NOTE: {total_deselected} tests were deselected by -m/-k and did not "
                f"run {parenthetical}"
            )
    ```
    Bounds proof:
    (a) The option value read is `getattr(config.option, "markexpr", "") or ""`. Search over `tests/deselect_notice.py` for `pyproject` and `read_text`:
    `grep -E "pyproject|read_text" tests/deselect_notice.py` returned exit code 1 with 0 matches.
    (b) The `NOTE: <N> tests were deselected` prefix and the `max(worker_max, _deselected_count)` count expression are byte-unchanged, confirmed by `git diff tests/deselect_notice.py`:
    Lines `worker_max = max(_worker_counts) if _worker_counts else 0` and `total_deselected = max(worker_max, _deselected_count)` and `if total_deselected > 0:` and `f"NOTE: {total_deselected} tests were deselected by -m/-k and did not "` are untouched.
    (c) The xdist accumulation hooks (`pytest_testnodedown`, `pytest_sessionfinish`) and `pytest_deselected` are untouched.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_deselect_notice.py -o addopts="" -v` output naming the four new cases as passed, and for EACH quote the asserted output string: the three-category case showing all three names (`slow`, `livecorpus` and the third) in the notice; the verbatim case showing `not (slow or livecorpus)` printed as an expression rather than interpreted; the no-filter case showing both that no marker deselection is claimed AND that `make test-all` is absent; and the mixed case showing both the marker names and the `-k` contribution. State that each case drives a real pytest subprocess and asserts on its stdout, and confirm no new test reads the plugin's source with `read_text`, `inspect`, `ast` or substring search (P16).
  - Observed evidence: Output of `python3 -m pytest tests/test_deselect_notice.py -o addopts="" -v` naming the four new cases:
    ```
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_three_categories_named_in_notice PASSED [ 11%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_verbatim_fallback_for_unparsed_marker_expression PASSED [ 22%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_mixed_marker_and_keyword_deselection PASSED [ 55%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_no_marker_filter_with_keyword_deselection PASSED [100%]
    ```
    Asserted output string for each:
    1. Three-category case (`test_three_categories_named_in_notice`):
       Asserts:
       `self.assertIn("NOTE: 3 tests were deselected", result.stdout)`
       `self.assertIn("'slow'", result.stdout)`
       `self.assertIn("'livecorpus'", result.stdout)`
       `self.assertIn("'gpu'", result.stdout)`
       `self.assertIn("make test-all", result.stdout)`
       Notice output: `NOTE: 3 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow', 'livecorpus' and 'gpu'); run everything with: make test-all`
    2. Verbatim case (`test_verbatim_fallback_for_unparsed_marker_expression`):
       Asserts:
       `self.assertIn("NOTE: 1 tests were deselected", result.stdout)`
       `self.assertIn("not (slow or livecorpus)", result.stdout)`
       `self.assertNotIn("make test-all", result.stdout)`
       Notice output: `NOTE: 1 tests were deselected by -m/-k and did not run (filtered by marker expression: 'not (slow or livecorpus)')`
    3. No-filter case (`test_no_marker_filter_with_keyword_deselection`):
       Asserts:
       `self.assertIn("NOTE: 1 tests were deselected", result.stdout)`
       `self.assertIn("no marker filter was active", result.stdout)`
       `self.assertNotIn("marker filter skips", result.stdout)`
       `self.assertNotIn("make test-all", result.stdout)`
       Notice output: `NOTE: 1 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)`
    4. Mixed case (`test_mixed_marker_and_keyword_deselection`):
       Asserts:
       `self.assertIn("NOTE: 2 tests were deselected", result.stdout)`
       `self.assertIn("'slow'", result.stdout)`
       `self.assertIn("-k/--deselect also contributed", result.stdout)`
       `self.assertIn("make test-all", result.stdout)`
       Notice output: `NOTE: 2 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow', and -k/--deselect also contributed); run everything with: make test-all`
    Subprocess execution and source-pin check:
    All cases drive real pytest subprocesses against temp directories using `_run_pytest(...)` or `subprocess.run(...)` and assert on `result.stdout`. No test imports or inspects the plugin's source code using `read_text`, `inspect`, `ast`, regex, or line counting (P16).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `-m slow` case as passed from the same `-v` run, and quote its assertion showing the notice does NOT claim `slow` was skipped. Then paste the four PRE-EXISTING cases as passed and paste `git diff tests/test_deselect_notice.py` showing their assertion lines UNCHANGED; if any pre-existing assertion had to be edited, state which and why, since that would mean the `NOTE:` prefix moved contrary to E-03's constraint (F-08).
  - Observed evidence: `-m slow` case passed from verbose run:
    ```
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_unconditional_print_regression_under_selected_marker PASSED [ 44%]
    ```
    Assertion showing notice does NOT claim `slow` was skipped:
    `self.assertNotIn("skips 'slow'", result.stdout)`
    `self.assertNotIn("the default run skips 'slow'", result.stdout)`
    `self.assertIn("filtered by marker expression: 'slow'", result.stdout)`
    Notice output: `NOTE: 1 tests were deselected by -m/-k and did not run (filtered by marker expression: 'slow')`
    Four pre-existing cases passed from the same verbose run:
    ```
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_xdist_workers PASSED [ 77%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_no_xdist PASSED [ 66%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_with_zero_workers PASSED [ 88%]
    tests/test_deselect_notice.py::DeselectNoticePluginTests::test_deselect_notice_absent_when_nothing_deselected PASSED [ 33%]
    ```
    Pre-existing assertion lines check: `git diff tests/test_deselect_notice.py` shows only added lines at the end of the class. The four pre-existing test methods and their assertion lines are byte-unchanged; the `NOTE: 1 tests were deselected` prefix compatibility boundary was completely preserved.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste (a) the targeted `python3 -m pytest tests/test_deselect_notice.py -o addopts=""` summary line (authoring baseline on the unmodified module was `4 passed in 5.09s`; the bar is that every pre-existing case and every case E-04/E-05 added is listed as passed, not a particular total); (b) the bare `python3 -m pytest` summary line, reconciled against a baseline YOU measured on a clean tree BEFORE editing, with every failing node id attributed either to a named E-item or to F-07's pre-existing set, noting that at authoring the three pre-existing failures were `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, so re-derive rather than inherit; (c) the NEGATIVE CONTROL: the diff restoring the hardcoded parenthetical and pytest output showing the names, verbatim, no-filter, mixed and `-m slow` cases ALL failing, with a statement that any of the five PASSING under the control is a defect in that case and not an acceptable result; (d) the control reverted, shown by `git diff --name-only` listing exactly `tests/deselect_notice.py` and `tests/test_deselect_notice.py` and nothing else; and (e) the selection-unchanged proof: the bare run's deselected count compared against the V-01 re-derived baseline, plus `git diff pyproject.toml` empty.
  - Observed evidence:
    (a) Targeted summary line:
    `============================== 9 passed in 24.02s ==============================`
    (All 4 pre-existing cases and all 5 newly added cases passed).
    (b) Bare `python3 -m pytest` summary line:
    `6449 passed, 2 skipped, 3 warnings in 253.40s (0:04:13)`
    Reconciled against baseline measured on clean tree prior to edit (`6444 passed, 2 skipped, 3 warnings in 290.31s`): exactly +5 passed, 0 failures, 0 regressions across the full suite.
    (c) Negative control:
    Parenthetical in `tests/deselect_notice.py` temporarily restored to `"run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all"`.
    Output of `python3 -m pytest tests/test_deselect_notice.py -o addopts="" -v`:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_deselect_notice.py::DeselectNoticePluginTests::test_verbatim_fallback_for_unparsed_marker_expression
    FAILED tests/test_deselect_notice.py::DeselectNoticePluginTests::test_three_categories_named_in_notice
    FAILED tests/test_deselect_notice.py::DeselectNoticePluginTests::test_unconditional_print_regression_under_selected_marker
    FAILED tests/test_deselect_notice.py::DeselectNoticePluginTests::test_no_marker_filter_with_keyword_deselection
    FAILED tests/test_deselect_notice.py::DeselectNoticePluginTests::test_mixed_marker_and_keyword_deselection
    ========================= 5 failed, 4 passed in 10.19s =========================
    ```
    All 5 new cases failed and all 4 pre-existing cases passed under the control, proving falsifiability.
    (d) Negative control reverted: `git diff --name-only` confirms exactly the two declared scope paths:
    ```
    tests/deselect_notice.py
    tests/test_deselect_notice.py
    ```
    (e) Selection unchanged proof:
    Deselected count in bare suite run is 258, exactly matching the 258 baseline measured before editing in V-01. Notice output: `NOTE: 258 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all`.
    `git diff pyproject.toml` is completely empty.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Open questions: OQ-01 is `- Status: resolved` and `- Blocking: no`, so nothing here waits on a human decision. It records the answer to the design question `zb81ah` deferred to the maintainer, resolved from measurement (F-04) rather than from preference, and both halves of the answer keep the notice true.

This plan is `- Status: to-review`. It has NOT been reviewed and is NOT approved; execution requires `/plan-review` and then explicit human sign-off recorded with `aw ipd set approved qsz23k --by-human`. No `- Readiness:` field is written here, because that field is an output of the review this plan has not had.

Scope fence (a DECLARATION so the runner can reconcile afterwards, not a stop directive): the executor edits only `tests/deselect_notice.py` and `tests/test_deselect_notice.py`. FOUR NEGATIVE CONSTRAINTS. FIRST, do NOT change `addopts` or any marker semantics; V-06 requires `git diff pyproject.toml` empty and the deselected count unmoved, precisely so a later reader can see this plan changed output and not selection. SECOND, do NOT change the `NOTE: <N> tests were deselected` prefix or the count expression; four existing tests assert on the prefix and V-05 requires their assertions pasted byte-unchanged. THIRD, do NOT read `pyproject.toml` from the plugin; the run's own `config.option.markexpr` is the source, and V-03 requires a search showing no file read. FOURTH, do NOT edit any file under `agent_workflows/` or `tests/test_suite_instruction_marker_parity.py`. If the work genuinely requires an edit outside the declared set, MAKE it and JUSTIFY it: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Do STOP and report only for a genuinely unsafe condition: a concurrent edit to either scope path that cannot be safely combined, or `config.option.markexpr` being absent on the coordinator in the installed pytest (F-03 measured it present, including under `-n 2` and with no `addopts` at all).

Execution contract: commit ONLY the two declared paths via `aw commit qsz23k -- tests/deselect_notice.py tests/test_deselect_notice.py`, never `git add -A` and never `--no-verify`, and do not push. Verify the staged set with `git diff --cached --name-only` before committing, since this checkout is shared. Run the suite BARE (`python3 -m pytest`) and PASTE THE ACTUAL RUNNER OUTPUT; a claim of passing tests without pasted output is a contract violation, and so is marking a `V-*` complete from the matching `E-*` checkmark rather than from evidence inspected in a separate pass. The E-06 negative control is a TEMPORARY edit to a scope path and MUST be reverted before commit.

Post-gate lifecycle move: this plan is terminal only when `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence with `Result: pass`. The terminal transition to `.aw/records/plans/executed/` then happens through the tooled lifecycle and NEVER by hand: if a runner (`aw oc run` / `aw agy run`) is driving this plan the runner OWNS the finalize and the executor must not call it; if the plan is executed by hand, the executor runs `aw ipd finalize` itself.

NEGATIVE-CONTROL RULE, STATED PRECISELY SO IT CANNOT MISFIRE: if the E-06 control does not fail ALL FIVE of the names-branch, verbatim-branch, no-filter-branch, mixed and `-m slow` cases, the case that passed is not testing the derivation: FIX THAT CASE and re-run the control; V-06 stays `failed` until all five fail under the control. Do NOT stop merely because the bare suite is red: F-07 measured three pre-existing failures in unrelated modules on a clean tree, so attribute each failing node and continue unless a failure is attributable to this plan's own change.
