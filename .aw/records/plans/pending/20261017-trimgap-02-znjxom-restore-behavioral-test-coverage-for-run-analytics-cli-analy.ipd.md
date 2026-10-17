# IPD: Restore behavioral test coverage for run_analytics_cli (analyze and query leaves)

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `n6h5eg` (Set `trimgap`, group 2 of the `z2xs98` filing plan) records that `tests/test_run_analytics_cli.py`, the behavioral suite for the `aw runs analyze` and `aw runs query` leaves in `agent_workflows/run_analytics_cli.py`, lost 75 `gap`-classified test names in the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), leaving 445 exclusive lines (across `run_analytics_cli`, `run_analytics_query` and `run_analytics_report`) uncovered by the surviving suite (`b1mx2w` `## Recreated re-diff` row and `## Recreated missing names`), plus one `unguarded-unreached` production key of 4 exclusive lines. The current file was recreated with only 11 tests, none `core`-marked, so the bare routine gate runs none of them (F-03). A mutation that, for example, made the query grammar accept an un-allowlisted filter field, counted a missing metric as zero, let `--path` write files, launched a browser without `--open`, or dropped the agent-record byte budget would pass the routine suite.
- Scope: Append to `tests/test_run_analytics_cli.py` the 75 `gap` tests from `git show 19313eed^:tests/test_run_analytics_cli.py` (with the helpers and fixtures they need), dropping the 4 names `b1mx2w` classified `retired-pin`/`intended-change` (F-02), and add residual tests for the branches of `run_analytics_cli.run_analyze` and `run_analytics_cli._common_base` the restored tests leave unexecuted (F-05, F-06). No test is `core`-marked: the restored tests run in the default non-slow tier, because the core tier already exceeds its budget (OQ-01, F-08). EXCLUDES any production change; EXCLUDES the `runs export`/`runs submit` leaf bodies (`run_export_leaf`, `run_submit_leaf`, carried by `gjmiuw`/`d2vfp2` and `pr6lo9`) beyond the one raw-export call needed to reach `_common_base`; EXCLUDES re-asserting invariants other files now own (F-02).
- Scope-Paths: tests/test_run_analytics_cli.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: n6h5eg
- Set: trimgap
- Order: 2
- Highest E allocated: 03
- Author: opencode
- Id: znjxom

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `n6h5eg`. Replayed the deleted file at HEAD `fbd39b772` (`3 failed, 76 passed in 19.71s`), measured module coverage before and after, re-derived every intended-change failure against the commit that caused it, and probed the residual branches and the core-tier budget before writing any step.
- 2026-10-17 draft (opencode): created.

## Goal

Make the analyze/query behavioral contract of `agent_workflows/run_analytics_cli.py` (declaration, parser registration, collision routing, analyze option surface, `--open` seam, query grammar, missingness and absence classes, agent-record budget, failure semantics, and the rendered report) guarded again by tests that drive `cli.main` and the module's functions and assert on exit codes, emitted records, written files and returned values, and make `run_analyze` and `_common_base` fully reached. Done means the 75 restored tests pass, the residual tests pass, and each of five reverted mutation spot-checks turns a test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the 75 gap tests

- [ ] E-01 Append to `tests/test_run_analytics_cli.py`, BELOW the existing `RunAnalyticsCliUxTests` class and above any `if __name__ == "__main__":` guard, the content of `git show 19313eed^:tests/test_run_analytics_cli.py` from its `_approx_tokens` helper through the end of class `TheReportIsRenderedByTheSpaNotAStub`, with these and ONLY these changes: (a) add the deleted file's missing imports (`from contextlib import ...` is already present; add `from agent_workflows import cli`, `from agent_workflows import run_analytics_query as query_mod`, `from agent_workflows import agent_schema`) to the top import block without duplicating existing ones; (b) keep the `BYTE_BUDGET`/`TOKEN_BUDGET` literals and the helpers `_approx_tokens`, `_run`, `_records`, `_make_repo`, `_write_run`, `_RepoFixture`, `_entry`; DROP the `_code_only` helper (it parses source with `ast`; no surviving test calls it, F-04); (c) DROP exactly the four non-gap tests (F-02): `DeclarationContractTests.test_no_new_undeclared_parser_leaf`, `ParserRegistrationTests.test_runs_description_names_every_mutating_exception`, `FailureSemanticsTests.test_no_test_here_reaches_the_network_or_launches_a_browser`, and `TheReportIsRenderedByTheSpaNotAStub.test_the_raw_table_is_not_truncated_to_the_terminal_page_size` and its now-unused `re`-only dependencies if any; (d) RE-POINT one test whose behavior is environmental: `OpenSeamTests.test_the_default_launcher_reports_rather_than_raising` must patch `webbrowser.open` (via `unittest.mock.patch("webbrowser.open", return_value=False)`) so it never touches a real browser and asserts `outcome.launched is False`, `outcome.supported is False` and a non-empty `outcome.remedy` unconditionally (the deleted version called the real `webbrowser.open`, took 6.20s at authoring, and asserted conditionally, F-07); (e) update the module docstring with one paragraph naming backlog `n6h5eg`, findings `b1mx2w`, source revision `19313eed^`, and which four tests were deliberately not restored and why. Keep every other restored test body unchanged. If any restored test fails at execution HEAD (none of the 75 did at authoring, F-01), STOP on that test: record it in Findings, determine whether the current behavior is an intended change (cite the commit) or a regression, and adjust only that test's expectation for an intended change; a regression is out of scope and must be filed with `aw backlog new` as `--work-kind bug --blocks-release next` rather than papered over.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_run_analytics_cli.py -o addopts="" -q` reports `86 passed` (11 existing + 75 restored) with no failures; `rg -n "import ast|ast\.parse|getsource|import inspect|__file__" tests/test_run_analytics_cli.py` returns nothing.
  - Execution state: pending

### Task group 2: residual branch coverage

- [ ] E-02 Append a class `RunAnalyzeResidualBranchTests(_RepoFixture)` covering the `run_analytics_cli.run_analyze` branches the restored file leaves unexecuted (F-05), each asserting the value observed at authoring: (a) `run_analyze` on args parsed from `["runs","analyze","--agent","--dir",<repo>]` with `args.json = True` set afterwards returns `2` and prints a stdout line starting `error: conflicting output format flags` (the `ConflictingFlagsError` arm; the parser itself refuses `--agent --json` before dispatch, so the test sets the attribute post-parse); (b) with `unittest.mock.patch.object(run_analytics_cache, "update_cache", side_effect=run_analytics_cache.CacheError("boom"))`, `_run(["runs","analyze","--agent",*self._dir()])` returns rc `2` and its last record has `kind == "error"`, `outcome == "cannot-run"`, `next == "aw runs analyze --rebuild"`; (c) a human-mode run with stderr replaced by a `StringIO` subclass whose `isatty()` returns True (`redirect_stderr`, plus `--no-color`) returns `0` and its stderr contains `"Analyzing run 1/3:"` (one per run, so `1/3` with `_RepoFixture`'s three runs), the `\x1b[2K` clear sequence, and `"Analyzed 3 run(s)."`. Re-measure each value at execution HEAD before asserting; apply E-01's STOP rule if one changed.
  - Depends on: E-01
  - Expected outcome: the three residual tests pass and `--cov=agent_workflows.run_analytics_cli --cov-report=term-missing` shows no missed line inside `run_analyze` other than any named and explained in V-02.
  - Execution state: pending

- [ ] E-03 Append a class `CommonBaseTests(unittest.TestCase)` reaching `run_analytics_cli._common_base`, the module's `unguarded-unreached` key (F-06), through both a direct call and the one CLI path that uses it: (a) `_common_base([])` is `None`; `_common_base([p/"r1"])` is `(p/"r1").resolve()`; `_common_base([p/"r1", p/"r2"])` is `p.resolve()`; (b) behaviorally, in a temp repo with two runs written by `tests.fixtures.run_analytics.write_run`, `cli.main(["runs","export","--tier","raw","--include","state.json","--apply","--by-human","--agent","--dir",<repo>,"--out",<repo>/"x"])` returns `0` and the bundle contains BOTH `raw/<run-id-1>/state.json` and `raw/<run-id-2>/state.json` (the collision `_common_base` exists to prevent, per its call-site comment in `run_export_leaf`: without a base, two `state.json` files collapse onto one `raw/state.json`). Re-measure at execution HEAD before asserting.
  - Depends on: E-01
  - Expected outcome: both tests pass; `_common_base`'s body is executed (except its `# pragma: no cover` `ValueError` arm).
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). This is why E-01 drops `_code_only` and `test_no_test_here_reaches_the_network_or_launches_a_browser` (it `ast.parse`s its own source), and why the no-launch property stays guarded behaviorally by the restored failing-stub tests in `OpenSeamTests`.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) and fails the session when wall time exceeds 30s on a machine with 12 or more CPUs (`conftest.pytest_sessionfinish`). See OQ-01 and F-08 for why this plan does NOT core-mark the restored tests.
- Sibling plans in the same Set (`t8j7mn`, `438gkf`, `d2vfp2`) restore one module each and validate with `-v` output, coverage output and reverted mutation spot-checks; this plan follows that shape.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `git show 19313eed^:tests/test_run_analytics_cli.py` copied to a scratch path inside the lane and run at HEAD `fbd39b772` with `-o addopts=""` | `3 failed, 76 passed in 19.71s`. 79 test functions. Failures: `test_no_new_undeclared_parser_leaf`, `test_runs_description_names_every_mutating_exception`, `test_the_raw_table_is_not_truncated_to_the_terminal_page_size`. Scratch copy removed. |
| F-02 | `b1mx2w` `## Recreated missing names` rows for `tests/test_run_analytics_cli.py`; re-derived at HEAD | Of 79 missing names: 75 `gap`, 3 `intended-change`, 1 `retired-pin`. (1) `test_no_new_undeclared_parser_leaf` pins five undeclared `oc profile` leaves that `f2cd41b19` declared; the invariant is owned by `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` (`1 passed` at HEAD). (2) `test_runs_description_names_every_mutating_exception` asserts `resume` is declared `mutation`; `6fd70f35c` re-declared it `read` (HEAD mutation set under `runs` is `['runs analyze', 'runs export', 'runs submit']`), and the help still names all four exceptions plus "FOUR exceptions", so only the `cldbus` guard is stale. (3) `test_the_raw_table_is_not_truncated...` expects `row_count == runs`; `c644f8b9f` added phase rows, and a 3-run probe at HEAD embedded `row_count 6`, each run twice (`phase` `aggregate` and `execute`). (4) `test_no_test_here_reaches_the_network...` parses its own file with `ast` (retired-pin). None is a regression; none is restored. |
| F-03 | `rg "def test_" tests/test_run_analytics_cli.py` and `rg pytestmark` at HEAD; bare `python3 -m pytest --collect-only -q` | The file holds 11 tests (`RunAnalyticsCliUxTests`), all distinct from the 79 deleted names, and none is `core`-marked, so 0 items from this file are in the bare core selection. |
| F-04 | `rg -n "_code_only\(" ` over the deleted file | `_code_only` is defined but called by no test in the deleted file; dropping it loses nothing. |
| F-05 | Existing + deleted files run together with `--cov=agent_workflows.run_analytics_cli --cov=agent_workflows.run_analytics_query --cov=agent_workflows.run_analytics_report` | `run_analytics_cli` 62% (existing file alone, 234 missed) -> 73% (164 missed); `run_analytics_query` 46% -> 83%; `run_analytics_report` 58% -> 72%. Remaining `run_analyze` misses: the `ConflictingFlagsError` arm, the `CacheError` arm, and the TTY progress/clear writes. Direct probes at HEAD produced the E-02 values: `(2, 'error: conflicting output format flags: cannot combine --agent and --json\n')`; CacheError -> `{"kind":"error","outcome":"cannot-run","exit":2,...,"next":"aw runs analyze --rebuild"}`; TTY stderr `'[INFO ] Analyzing run 1/1: run-...\r\x1b[2K[INFO ] Analyzed 1 run(s).\n'`. Most remaining module misses are `run_export_leaf`/`run_submit_leaf` (out of scope). |
| F-06 | `b1mx2w` `## Rollup mutation results` row `agent_workflows/run_analytics_cli.py::_common_base` (`unreached`, `unguarded-unreached`) and per-module totals row (3 keys: `budget-exhausted` 2, `unguarded-unreached` 1) | The backlog body and `b1mx2w` `## Filed items` name the module's single `unguarded-unreached` 4-line key as `run_analyze`, but the mutation-results row that carries that verdict is `_common_base`; `run_analyze` is reached at HEAD by the existing file (`test_run_analyze_*`). This plan covers BOTH so the item is satisfied under either reading (E-02 for `run_analyze`, E-03 for `_common_base`). Probe at HEAD: `_common_base([])` -> `None`, one dir -> that dir, two siblings -> their parent; a two-run raw export wrote `raw/run-...1111111/state.json` and `raw/run-...2222222/state.json` in 0.30s. |
| F-07 | `--durations=15` on the scratch replay | `test_the_default_launcher_reports_rather_than_raising` 6.20s (calls real `webbrowser.open`) and `test_the_raw_table_is_not_truncated...` 5.95s are the two slow tests; every other test is under 0.8s. Patching `webbrowser.open` probes at HEAD: `False` -> `LaunchOutcome(launched=False, supported=False, detail='no browser is available on this system', remedy='open the report manually: ...')`. |
| F-08 | Bare `python3 -m pytest` at HEAD on this 12-CPU host, twice; then once with the scratch file `core`-marked (4 slow/failing tests deselected via `-k` in a separate check) | Baseline core tier: `754 passed in 33.51s`, then `754 passed in 31.84s` with `CORE TIER BUDGET EXCEEDED ... 31.85s exceeded budget of 30.00s` (rc 1). With the restored module core-marked: `830 passed in 34.61s`, budget exceeded. The core tier is already over budget before this plan, so core-marking 75 more tests would make the overrun worse; see OQ-01. |

## Proposed changes (ordered, validatable)

1. E-01 restores the 75 gap tests and their helpers into the existing test file.
2. E-02 adds three residual tests for `run_analyze`'s unexecuted arms.
3. E-03 adds `_common_base` tests, direct and through the raw export path.

## Deferred / out of scope (with reason)

- `run_export_leaf` / `run_submit_leaf` behavioral coverage (the `runs export`/`runs submit` CLI section of the deleted `tests/test_run_analytics_submit.py`) belongs to the submit/export restoration.
  - Carrier: gjmiuw
- Mutation-probing the `subprocess-only` `budget-exhausted` keys `run_export_leaf` and `run_submit_leaf`.
  - Carrier: lrnh5f
- The four non-gap tests (F-02).
  - Carrier-Declined: no work is owed; each invariant is either owned by another surviving test, changed intentionally by a cited commit, or a source-reading test `AGENTS.md` forbids.
- The pre-existing core-tier budget overrun (F-08) is not caused or fixed by this plan.
  - Carrier-Declined: outside this item's scope; this plan adds nothing to the core tier, so it does not worsen it.

## Scope check

- Over-scope: none. One test file is the only path declared and changed; E-03(b) calls `runs export` only to observe `_common_base`'s effect.
- Under-scope: none for the 75 gap names and both readings of the unreached key (F-06).

## Required tests / validation

- `python3 -m pytest tests/test_run_analytics_cli.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` summary line pasted; its passed count must equal the pre-change baseline count (this plan adds no core tests), and any budget message must be compared against the pre-change run on the same host.
- `python3 -m pytest tests/test_run_analytics_cli.py` (default addopts, so the `not slow and not livecorpus` filter applies) passes with the full count, showing the restored tests are selected by the non-slow tier.
- Coverage: `python3 -m pytest tests/test_run_analytics_cli.py -o addopts="" --cov=agent_workflows.run_analytics_cli --cov=agent_workflows.run_analytics_query --cov=agent_workflows.run_analytics_report --cov-report=term-missing` pasted.
- Mutation spot-checks (scratch, reverted): see V-01..V-03.
- `aw sanitize --agent` reports no `fail`.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should the restored tests be `core`-marked so the bare gate runs them?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. The core tier already exceeds its 30s budget on this 12-CPU host before this plan (F-08: 31.84s, rc 1), and core-marking the restored module measured 34.61s. The backlog remedy asks to restore the tests, not to promote them into the core tier, and the sibling plans' core-marking was justified by sub-second files. The restored tests run in the default non-slow tier (explicit-path runs, `make test-all`, CI). A maintainer who wants a core subset can promote individual sub-second tests later.

### OQ-02: Which key is the backlog's `unguarded-unreached` key, `run_analyze` or `_common_base`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: cover both (F-06). The mutation-results row says `_common_base`; the backlog body says `run_analyze`. E-02 closes `run_analyze`'s unexecuted arms and E-03 reaches `_common_base`, so the item is satisfied under either reading at the cost of five small tests. The backlog's requirements are not modified.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` and `git diff --stat HEAD` showing only `tests/test_run_analytics_cli.py` changed; paste the list of `def test_` names added (from `git diff`) and a `comm` against the 75 `gap` names of `b1mx2w` `## Recreated missing names` showing zero missing and zero extra besides E-02/E-03's tests; paste `rg -n "import ast|ast\.parse|getsource|import inspect|__file__" tests/test_run_analytics_cli.py` returning nothing; paste the `-v` output showing all 86 E-01-era tests PASSED; paste the failures produced by two scratch mutations, reverted afterwards: make `run_analytics_query.parse_filters` accept any field name, and make `_analyze_path` publish a bundle before returning; paste `aw sanitize --agent` showing no `fail`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing the three `RunAnalyzeResidualBranchTests` tests PASSED; paste the `--cov-report=term-missing` line for `agent_workflows/run_analytics_cli.py` and name any missed line still inside `run_analyze` with the reason; paste the failure from a scratch mutation (reverted) that changes the `CacheError` arm's `next_cmd` to `"aw runs analyze"`; paste the bare `python3 -m pytest` summary line with its passed count equal to the pre-change baseline, plus the pre-change line from the same host.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing the `CommonBaseTests` tests PASSED; paste the failure produced by a scratch mutation (reverted) making `_common_base` return `None` unconditionally, which must fail the behavioral raw-export assertion (only one `state.json` survives); paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_run_analytics_cli.py` through `aw commit <plan> -- tests/test_run_analytics_cli.py`; never push. Mutation spot-checks are scratch edits to `agent_workflows/` files that must be reverted before commit and must not appear in the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass` (under a runner, the runner finalizes).
