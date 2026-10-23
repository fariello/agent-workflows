# IPD: Restore behavioral coverage for the attention board shared-gate fold (_shared_gate_ref) and record render_table/_render_table_row as guarded

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `1n4qco` (Set `trimgap`, group 7 of the `wo21z5` `## Filing plan`) carries three `agent_workflows/attention.py` keys, `_shared_gate_ref`, `render_table` and `_render_table_row`, whose `wo21z5` `## Budget probe results` verdict is `budget-exhausted` (never mutation-probed), with remedy "probe then restore" and control file `tests/test_attention_priority_blocker.py`, a file deleted by the suite trim `19313eed`. Probing them at authoring HEAD `390d90f07` (Findings F-01 to F-03) shows `render_table` and `_render_table_row` are already GUARDED (a `return-none` mutant is killed by 11 and 12 surviving tests), while `_shared_gate_ref` is UNGUARDED: its `return-none` mutant passes every surviving attention test and is killed only by the deleted control file. So today a regression that stops the colored attention board from folding a shared gate ref into one `all N gated by <ref>` line (and from suppressing it on each row) would pass the routine suite.
- Scope: Restore the deleted `tests/test_attention_priority_blocker.py` from `19313eed^` as a `core`-marked behavioral module, adapting the one test that no longer matches HEAD (`test_schema_version_and_json_keys` pins `SCHEMA_VERSION == 4`; HEAD is 5) to assert the observable payload contract instead of a hard-coded number, and add direct behavioral tests of `attention._shared_gate_ref` covering every return branch (shared, single, distinct, mixed, empty, and `long` compaction). Record `render_table` and `_render_table_row` as guarded with re-run probe evidence; no new tests are owed for them. EXCLUDES any change to `agent_workflows/attention.py` or any other production file, and EXCLUDES `_gate_ref_display`, which belongs to the residual rollup backlog item `nzc6dm`.
- Scope-Paths: tests/test_attention_priority_blocker.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 1n4qco
- Set: trimgap
- Order: 25
- Highest E allocated: 04
- Author: opencode
- Id: a5drqh

## Workflow history
- 2026-10-23 to-review (aw set): authored from backlog 1n4qco; probed all three keys at HEAD 390d90f07 (F-01..F-05) before writing expected outcomes

- 2026-10-23 draft (opencode): created.

## Goal

Make a mutation that breaks the attention board's shared-gate fold (`attention._shared_gate_ref`) turn a routine (bare, core-tier) test red, by restoring the deleted control test module and adding direct tests of the fold decision, and record with probe evidence that the other two keys of backlog `1n4qco` are already guarded so their gap is closed without new tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the control module

- [ ] E-01 Restore `tests/test_attention_priority_blocker.py` from `git show 19313eed^:tests/test_attention_priority_blocker.py` (391 lines, 26 tests in classes `AttentionPriorityBlockerTests`, `PlanReleaseBlockerSurfacingTests`, `RetiredPlanIsNotAReleaseBlockerTests`, `ReadinessReaderTests`, `GateRefRenderingTests`, `QuestionCountJsonTests`). Add `import pytest` and `pytestmark = pytest.mark.core` after the imports, and extend the module docstring with one line in the shape `tests/test_attention_stem.py` uses: "Restored under backlog 1n4qco, findings wo21z5, from revision 19313eed^." followed by a line naming the one adapted test (E-02). Keep every other test body verbatim.
  - Depends on: none
  - Expected outcome: the file exists, imports cleanly, carries the `core` marker, and 25 of its 26 tests pass unmodified at HEAD (measured at authoring, F-04).
  - Execution state: pending

- [ ] E-02 Adapt `AttentionPriorityBlockerTests.test_schema_version_and_json_keys`, the only restored test failing at HEAD (`AssertionError: 5 != 4`, F-04), so it asserts the observable contract rather than pinning a constant: replace `self.assertEqual(attention.SCHEMA_VERSION, 4)` (and its version-history comment) with an assertion that the parsed `render_json` payload's `schema_version` equals `attention.SCHEMA_VERSION`, and that the payload carries the top-level keys `items`, `valid`, `violations` and `stranded_lanes`; keep the existing `priority == "low"` and `"blocks_release" in it` item assertions. Do not assert any specific integer for the version.
  - Depends on: E-01
  - Expected outcome: all 26 restored tests pass; the adapted test fails if `render_json` stops emitting `schema_version` or any of the four keys, and does not fail on a future version bump alone.
  - Execution state: pending

### Task group 2: direct fold-decision tests

- [ ] E-03 Add a `SharedGateRefTests` class to the same module that calls `attention._shared_gate_ref(items, long=...)` directly, building blocked items with the same shape as the restored `GateRefRenderingTests._gated` helper (distinct ids and paths per item). Assert each return branch, all measured at authoring (F-05): two items gated by `TODO.md` return `"TODO.md"`; ONE gated item returns `""` (single items are not folded); two items with distinct refs (`TODO.md` and the deep plan path) return `""`; two gated items plus one ungated item return `""` (mixed); an empty list returns `""`; two items gated by the deep path `.aw/records/plans/pending/20260903-runflags-01-uyeko5-wire-the-spec.ipd.md` return `"20260903-runflags-01-uyeko5"` with `long=False` and the full path with `long=True`.
  - Depends on: E-01
  - Expected outcome: 6 assertions (or parametrized rows), each passing at HEAD and each failing under a `return ""` / `return None` mutant on at least the shared-ref rows.
  - Execution state: pending

- [ ] E-04 Add one table-level test to `SharedGateRefTests` that asserts the fold's observable effect on `attention.render_table` (the only caller that hoists into a note line, `render_table` "all {len(visible)} gated by {shared_gate}"): with `term=T.Term(color=True)`, `show_all=True`, `legend=False` and two items gated by `TODO.md`, the ANSI-stripped output's first line is exactly `all 2 gated by TODO.md` and no row contains `[gate artifact:`; with the two distinct-ref items, no line starts with `all ` and each row carries its own `[gate artifact: ...]` suffix (`TODO.md` and `20260903-runflags-01-uyeko5`). Both outputs measured at authoring (F-05).
  - Depends on: E-03
  - Expected outcome: the table-level test passes at HEAD and fails when `_shared_gate_ref` returns `""` (no note line) or when `render_table` stops passing `gate_in_header` (rows repeat the ref).
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). Every assertion here calls `render_board`, `render_table`, `render_json`, `scan`, `release_blockers`, `read_readiness`, `count_question_stats` or `_shared_gate_ref` and checks the returned value. E-02 removes the one assertion that pinned a constant instead of an output.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`), under a 30s budget. A restored module must carry `pytestmark = pytest.mark.core` to be reached by the merge gate; the restored file ran its 26 tests in 0.27s at authoring (F-04).
- Restoration precedent in this Set: `tests/test_attention_stem.py` (restored under backlog `q86fxm` by plan `y4bt1c`) restores a deleted attention module verbatim with `pytestmark = pytest.mark.core` and a provenance docstring line. E-01 follows that shape.
- `render_board` with a colored `Term` returns `render_table` early, so the colored board's gate fold is the `render_table` note line, not the `render_board` section header (`render_board` "if colored: return render_table(...)"). E-04 therefore asserts on `render_table`.
- Mutation probing: `tools/mutation_probe.py <path.py>::<qualname> --op <op> --format json [--extra-test COMMIT:PATH] -- <pytest args>` mutates committed HEAD in a disposable worktree; `--extra-test 19313eed:<path>` reads `19313eed^:<path>`. Verdict mapping is the `rf1xxr` E-02 rule as quoted in `lictgf` E-02: survivor `killed` -> `guarded`; survivor `survived` with control `killed` -> `unguarded`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/mutation_probe.py agent_workflows/attention.py::_shared_gate_ref --op return-none --format json -- -m "not slow and not livecorpus" tests/test_attention.py tests/test_attention_output_safety.py tests/test_attention_stem.py tests/test_backlog.py` at HEAD `390d90f07` | `verdict: survived`, `baseline_failing: 0`, `mutant_failing: 0`, `wall_s: 30.7`. No surviving attention test detects a fold that never fires. |
| F-02 | same probe with `--extra-test 19313eed:tests/test_attention_priority_blocker.py -- tests/test_attention_priority_blocker.py` | `verdict: killed`, newly failing `GateRefRenderingTests::test_shared_ref_folds_into_header_and_leaves_rows`, `extra_tests_overwrote: []`. Mapped verdict: `unguarded`. The deleted control file is the remedy source. (Its `baseline_failing: 1` is the schema test of F-04, unrelated to the mutant.) |
| F-03 | same survivor command for `render_table` and `_render_table_row` | `render_table`: `killed`, 11 newly failing (for example `test_attention.AttentionTableFormattingAndSortingTests::test_table_formatting_and_sorting`), `wall_s: 31.96`. `_render_table_row`: `killed`, 12 newly failing, `wall_s: 32.63`. Mapped verdict for both: `guarded`. The `wo21z5` `budget-exhausted` verdict reflected an exhausted probe budget, not a coverage gap. |
| F-04 | the restored file run from gitignored scratch with `python3 -m pytest -o addopts="" -q -p no:randomly` | `1 failed, 25 passed in 0.27s`; the only failure is `test_schema_version_and_json_keys`: `AssertionError: 5 != 4` (`attention.SCHEMA_VERSION` is 5 at HEAD). `render_json` emits keys `items, mapping_version, parked_questions, schema_version, stranded_lanes, valid, violations`, with `schema_version == attention.SCHEMA_VERSION`. No test in the current `tests/` tree defines any of the restored test names other than `test_plain_board_unchanged` (also in `tests/test_attention_stem.py`, a different class and module, so no collision). |
| F-05 | direct calls at HEAD `390d90f07` | `_shared_gate_ref`: two same `TODO.md` -> `'TODO.md'`; one -> `''`; distinct -> `''`; mixed with ungated -> `''`; empty -> `''`; two deep-path -> `'20260903-runflags-01-uyeko5'` (`long=False`) and the full path (`long=True`). `render_table` (colored, stripped, `legend=False`) on two `TODO.md` items: first line `all 2 gated by TODO.md`, rows carry no gate suffix; on distinct refs: no note line, rows end `[gate artifact: TODO.md]` and `[gate artifact: 20260903-runflags-01-uyeko5]`. |

## Proposed changes (ordered, validatable)

1. E-01 restores the control module with the `core` marker and provenance docstring.
2. E-02 adapts the single test that pins a stale constant to assert the JSON payload contract.
3. E-03 adds direct branch tests of `_shared_gate_ref`.
4. E-04 adds a table-level test of the fold's observable effect.

## Deferred / out of scope (with reason)

- `render_table` and `_render_table_row` get no new tests: F-03 shows each `return-none` mutant is already killed by 11 and 12 surviving tests, so they are guarded and no coverage is owed. V-04 re-runs both probes at execution HEAD to confirm that still holds.
  - Carrier-Declined: no work is owed; both keys are measured guarded, and the restored module adds further coverage of both as a side effect.
- `_gate_ref_display` is out of scope: it is group 24 of the `wo21z5` filing plan, rolled into the residual backlog item.
  - Carrier: nzc6dm
- The section-header fold inside `render_board` (`header_extra = f" in {shared_gate}"`) is reachable only when `colored` is True, but the colored path returns `render_table` first, so that branch is not reachable from `render_board`. Whether it should be removed is a production-code question outside this test-only plan.
  - Carrier-Declined: no reach gap is created by this plan and the backlog item names no work on it; any cleanup is a separate decision for the maintainer.

## Scope check

- Over-scope: none. One restored test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none. All three keys named by backlog `1n4qco` are probed (F-01 to F-03); the one unguarded key gets restored and direct coverage, and the two guarded keys are recorded with evidence.

## Required tests / validation

- `python3 -m pytest tests/test_attention_priority_blocker.py -o addopts="" -v -p no:randomly` passes, with the per-test list pasted (26 restored tests plus the E-03/E-04 tests).
- Bare `python3 -m pytest` passes (core tier, including the new module, within the 30s budget), with the summary line pasted.
- Mutation spot-check (scratch edit, never committed): make `attention._shared_gate_ref` `return ""` as its first statement, run the new module, paste the failures (expected to include `test_shared_ref_folds_into_header_and_leaves_rows` and the E-03/E-04 shared-ref assertions), then revert and paste an empty `git diff agent_workflows/`.
- Guarded re-check: re-run the F-03 survivor probe for `render_table` and `_render_table_row` at execution HEAD and paste each JSON's `verdict` and `newly_failing_total`.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should `render_table` and `_render_table_row` get new tests even though they probe guarded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The backlog item's remedy is "probe then restore", which means restore only what the probe shows unguarded (the `rf1xxr` E-02 mapping: survivor `killed` -> `guarded`). F-03 measured both killed by the surviving suite, so restoring coverage for them would add tests that close no gap. The restored control module exercises both anyway, and V-04 re-confirms the guarded verdict at execution HEAD.

### OQ-02: Restore `test_schema_version_and_json_keys` verbatim, drop it, or adapt it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Adapt (E-02). Verbatim fails at HEAD (F-04). Dropping it loses the only check that `render_json` carries the item `priority` and `blocks_release` keys. Pinning the new integer would be a constant check that breaks on every legitimate bump and asserts no behavior, which P16 forbids; asserting the emitted `schema_version` matches the module constant and the payload keys exist is the observable contract.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` showing only `tests/test_attention_priority_blocker.py` added; paste `python3 -m pytest --collect-only -q tests/test_attention_priority_blocker.py` output showing the module is collected by the bare (core-tier) selection with a nonzero count; and paste the bare `python3 -m pytest` summary line showing it passed within the core-tier budget.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output line showing `test_schema_version_and_json_keys` PASSED, and paste `git diff --no-index` (or equivalent) between `19313eed^:tests/test_attention_priority_blocker.py` and the restored file showing that the only body change is inside that test plus the marker and docstring lines.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing the `SharedGateRefTests` direct-branch test(s) as PASSED, and paste the failure output of the new module under the scratch mutation `return ""` as the first statement of `_shared_gate_ref` (showing at least `test_shared_ref_folds_into_header_and_leaves_rows` and the E-03 shared-ref assertion failing), followed by an empty `git diff agent_workflows/` after reverting.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output line showing the table-level fold test PASSED and its failure under the same scratch mutation as V-03; and paste, from re-running the F-03 survivor probe at execution HEAD, the `verdict` and `newly_failing_total` for `render_table` and `_render_table_row` (each must be `killed` with a nonzero count).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). The executor follows the agent execution contract in `AGENTS.md`: change only `tests/test_attention_priority_blocker.py`, keep every mutation spot-check as an uncommitted scratch edit that is reverted before commit, commit through `aw commit a5drqh -- tests/test_attention_priority_blocker.py`, never push, and paste actual runner output for every `V-*`. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
