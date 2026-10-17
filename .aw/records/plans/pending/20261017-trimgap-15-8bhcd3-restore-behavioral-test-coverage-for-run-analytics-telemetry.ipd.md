# IPD: Restore behavioral test coverage for run_analytics_telemetry

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `yqpb7q` (Set `trimgap`, group 15 of the `b1mx2w` `## Filing plan`) records that 24 production keys in `agent_workflows/run_analytics_telemetry.py` (151 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. The module's own behavioral test file, `tests/test_run_analytics_telemetry.py`, was deleted by the suite trim `19313eed`, and the surviving tests that import the module (`tests/test_run_id_collision.py`, `tests/test_telemetry_platform_release.py`, plus runner tests that drive `TelemetryCollector` indirectly) reach only validation and collector plumbing. So a mutation that, for example, made `_parse_accelerator_csv` return `None` for good vendor output, made `build_event` return `None`, made `ResourceSampler.tick` report the opposite outcome, or made `FakeResourceProbeAdapter._count` raise would pass the routine suite.
- Scope: Restore `tests/test_run_analytics_telemetry.py` from `19313eed^` minus its code-pinning parts (the unused `ast` helpers `_code_identifiers`/`_imported_modules`/`_FORBIDDEN_CODE_IDENTIFIERS`, and three tests that assert on the module docstring text or on this test file's own source, F-03), replace the fragment-assembled maintainer-handle canary with a neutral one (F-04), add `pytestmark = pytest.mark.core` so the bare core-tier gate selects it, and append residual tests for the branches of the 24 keys the restored file still leaves unexecuted (F-05). The 24 keys: `_parse_accelerator_csv`, `SystemResourceProbeAdapter._run_bounded`, `build_event`, `ResourceSampler.tick`, `_validate_accelerators`, `FakeResourceProbeAdapter._count`, `FakeResourceProbeAdapter.cpu`, `FakeResourceProbeAdapter.load`, `FakeResourceProbeAdapter.memory`, `FakeResourceProbeAdapter.process`, `ProbeOutcome.to_dict`, `FakeResourceProbeAdapter.accelerators`, `FakeResourceProbeAdapter.tool_versions`, `ResourceSampler.__enter__`, `ResourceSampler._run`, `TelemetryCollector.__enter__`, `TelemetryCollector._note`, `TelemetryCollector.sample`, `_as_int`, `ResourceSampler.__exit__`, `ResourceSampler.running`, `TelemetryCollector.__exit__`, `TelemetryCollector.note_skipped_sample`, `FakeResourceProbeAdapter.__init__`. EXCLUDES any change to `agent_workflows/run_analytics_telemetry.py` or any other production file; EXCLUDES restoring `tests/test_run_analytics_packaging.py` (F-06); EXCLUDES driving the non-key missed lines of `_validate_scalar`, `_validate_number_map`, `node_identity_input` and the `SystemResourceProbeAdapter` procfs readers (F-05).
- Scope-Paths: tests/test_run_analytics_telemetry.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: yqpb7q
- Set: trimgap
- Order: 15
- Highest E allocated: 02
- Author: opencode
- Id: 8bhcd3
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (opencode): authored from backlog `yqpb7q`. Replayed both deleted files named by the item against HEAD `f71c0d0a6` in a scratch copy under `tests/`, applied the proposed subset edits, and measured module line coverage and per-test durations before writing any step; scratch copies and the `.coverage` file were removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 24 `unguarded-unreached` keys of `agent_workflows/run_analytics_telemetry.py` from backlog `yqpb7q` reached by the routine (bare, core-tier) test run, through behavioral tests that build and validate events, drive the fake and real probe adapters, run the collector and sampler lifecycles, and assert on the returned records, the written JSONL stream, thread state and raised refusals. Done means a mutation that breaks accelerator parsing, event construction, collector or sampler lifecycle, or the fake adapter turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the behavioral part of the deleted module

- [ ] E-01 Create `tests/test_run_analytics_telemetry.py` from `git show 19313eed^:tests/test_run_analytics_telemetry.py` with exactly these edits: (1) delete the `_FORBIDDEN_CODE_IDENTIFIERS` constant with its comment block and the `_code_identifiers` and `_imported_modules` helpers (they parse source with `ast` and no remaining test calls them, F-03), and delete `import ast` and `import re` (`re` is used only by the deleted canary-literal test, so leaving it fails the repository's `ruff` pre-commit hook with `F401`, measured at review); (2) delete the three tests `EventSchemaTests.test_docstring_states_the_allowlist_direction`, `ProbeAdapterTests.test_the_bench_env_reuse_decision_is_recorded_in_the_module` (both assert substrings of `tel.__doc__`) and `PrivacyCorpusTests.test_no_literal_canary_is_committed_in_this_file` (reads `Path(__file__)` and regex-matches the maintainer handle's fragments), which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" forbids restoring; (3) change the `_HANDLE` canary from the maintainer-handle fragments to the neutral `"some" + "one"` and delete the now-meaningless control assertion `"control: a handle IS a fail-severity finding, ..."` in `NodeIdentityTests.test_the_sanitizer_does_not_fail_on_a_hostname_which_is_why_the_direct_check_leads` (F-04), keeping its home-path control; (4) add `import pytest` and a module-level `pytestmark = pytest.mark.core`; (5) add a docstring paragraph naming backlog `yqpb7q`, findings `b1mx2w`, source revision `19313eed^`, and that the source-reading and docstring-text tests were deliberately not restored. Keep every other restored test body unchanged. Disposition rule if a restored test fails at execution HEAD (none did at authoring, F-02, or at review): do not mark E-01 performed until that test is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit and adjust only that test's expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it or papering over it, then continue.
  - Depends on: none
  - Expected outcome: the file exists, carries the `core` marker, and every restored test passes serially, under `-n 4`, and under random order (59 at authoring and at review; the count is context, not the bar); a bare `python3 -m pytest --collect-only -q` lists `tests/test_run_analytics_telemetry.py` items; `rg -n "import ast|__doc__|__file__|getsource|import inspect|riello" tests/test_run_analytics_telemetry.py` returns nothing; `python3 -m ruff check --select F401 tests/test_run_analytics_telemetry.py` reports no unused import.
  - Execution state: pending

### Task group 2: residual branch coverage for the 24 keys

- [ ] E-02 Append one `ResidualKeyBranchTests(unittest.TestCase)` class (unittest style, matching the restored file) covering the branches of the 24 keys the restored file leaves unexecuted (F-05), each asserting a value observed at authoring: (a) `tel._parse_accelerator_csv("\n  \nGPU-A, 100, 50, 7, 550.1\n", vendor="nvidia")` returns `[{"vendor": "nvidia", "name": "GPU-A", "memory_total_mib": 100, "memory_used_mib": 50, "utilization_percent": 7, "driver_version": "550.1"}]` (blank-line skip) and `tel._parse_accelerator_csv("\n\n", vendor="nvidia")` is `None`; (b) `tel._as_int("x")` and `tel._as_int(None)` are `None` and `tel._as_int(" 4 ") == 4`; (c) `tel._validate_accelerators` called with `"abc"`, `{"a": 1}` and `5` each raises `tel.SchemaRefusal` whose message contains `"must be a list of accelerator objects"`; (d) `tel.build_event(event_kind="start", execution_id="exec-01", monotonic_offset_seconds=0.0, wall_timestamp="2026-09-13T20:00:00Z", phase=None)` returns a dict whose keys are exactly `{"event_kind", "execution_id", "monotonic_offset_seconds", "schema_version", "wall_timestamp"}` (a `None` field is omitted, not persisted); (e) a `TelemetryCollector` built like the restored `_collector` helper returns `None` from `sample()` before `start()` and again after `close()`, and the stream holds no `sample` event; (f) a `ResourceSampler(collector, interval_seconds=0.01)` on a started collector with the real monotonic clock, after `start()`, reaches `samples_taken >= 1` within a 5 second polling deadline and `stop()` leaves `running` False (the `_run` loop body and its `tick` call); (g) the same sampler with `tick` replaced by a function that records the call and raises `RuntimeError` exits its thread (`_thread.is_alive()` False within the deadline) after exactly one call, proving a tick failure ends the thread rather than propagating. (f), (g) and (h) are the only tests in the file that wait on real time; bound every wait by the deadline so a regression fails rather than hangs. Re-measure each value at execution HEAD before asserting it; if one has changed, apply the E-01 disposition rule. (h) The `_run` skip branch (`if now - last < self.interval: continue`) is NOT executed by (f), because with `interval_seconds=0.01` the clamped `check_interval` equals the interval, so every wake-up already exceeds it; measured at review, line `continue` stayed missed in 5 of 5 runs of (f) and (g). Cover it deterministically: a sampler with `interval_seconds=1.0` and an injected `monotonic` returning `0.0` for its first three calls and `10.0` afterwards, with `check_interval` set to `0.01` after construction, reaches `samples_taken == 1` within the deadline, and `stop()` then ends it. At review, a draft of (a) to (h) passed (67 passed) and left no missed line inside any of the 24 keys in 3 of 3 runs. All values (a) to (g) were re-measured at review at HEAD `be0827929` and matched.
  - Depends on: E-01
  - Expected outcome: the residual tests pass, and the coverage JSON per-function report (see Required tests) shows an empty `missing_lines` for each of the 24 keys (the authoring-time key-body misses were in `_validate_accelerators`, `build_event`, `_parse_accelerator_csv`, `_as_int`, `TelemetryCollector.sample` and `ResourceSampler._run`).
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). This is why E-01 drops the `ast` helpers and the three tests that assert on `tel.__doc__` substrings or on this file's own text. The privacy property the canary-literal test guarded (no sensitive literal committed) is enforced by `aw sanitize --agent` in V-01 instead.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget, so the restored module must carry `pytestmark = pytest.mark.core`. Module-level `pytestmark` applies to `unittest.TestCase` items (precedent: `tests/test_spec_id6_filenames.py`, which mixes both). The restored subset ran `59 passed in 2.21s` serially at authoring; its slowest test took 0.17s.
- Sibling plan precedent in the same Set: `438gkf` (backlog `liybkg`) and `t8j7mn` restore coverage as one core-marked module plus a residual-branch block and validate with `-v` output, coverage output and reverted mutation spot-checks; this plan follows that shape.
- Leak-sanitizer awareness (`AGENTS.md`): a committed test must not carry maintainer-identifying data even fragment-assembled, so E-01 replaces the handle canary (F-04).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows `agent_workflows/run_analytics_telemetry.py::*` with verdict `unguarded-unreached`; `b1mx2w` `## Filing plan` group 15; `## Filed items` row `yqpb7q` | Exactly the 24 keys listed in Scope carry `unguarded-unreached`. Other module keys (`_validate_scalar`, `validate_event`, `TelemetryCollector._emit`, `ResourceSampler.start`/`stop`, ...) are `reached` by 250+ surviving tests and are not in `yqpb7q`. |
| F-02 | `git show 19313eed^:tests/test_run_analytics_telemetry.py` copied to a scratch test path inside the lane and run at HEAD `f71c0d0a6` with `-o addopts="" --cov=agent_workflows.run_analytics_telemetry --cov-report=term-missing` | Verbatim: `62 passed in 1.98s`, `647 stmts, 84 miss, 87%`. After the E-01 edits: `59 passed in 2.21s` serially, `59 passed in 2.37s` under `-n 4`, `59 passed in 2.03s` with random order; coverage unchanged at 87 percent (the removed tests asserted only text). |
| F-03 | Reading the deleted file | `_code_identifiers`, `_imported_modules` and `_FORBIDDEN_CODE_IDENTIFIERS` are defined but never called in the file at `19313eed^` (`rg` finds only their definitions). Three tests assert on text: two on `tel.__doc__` substrings (`"THE SCHEMA IS AN ALLOWLIST"`, `"REUSE DECISION"`, ...) and one reads `Path(__file__)` to regex-check its own canary fragments. All are code-pinning and excluded. |
| F-04 | `ls.scan_text` with `ls.build_ruleset(REPO_ROOT)` at HEAD on candidate canaries | The deleted file's `_HANDLE` is the maintainer's handle assembled from two fragments; restoring it would re-commit maintainer-identifying data, and its `handle` rule fires only because the local hints file knows it, so the control is machine-dependent. A neutral `"/ho" + "me/" + "some" + "one" + "/x"` still scans `home-path` `fail` on any machine, so every home-path canary and control keeps its teeth. With the handle replaced and the handle-only control assertion removed, all 59 tests pass and `aw sanitize --agent` reported `"outcome":"clean" ... "findings":0`. |
| F-05 | E-01 subset coverage, missed lines mapped to enclosing functions | Missed lines inside the 24 keys: `_validate_accelerators` non-list refusal; `build_event` `None`-field skip; `_parse_accelerator_csv` blank-line skip; `_as_int` `except` return; `TelemetryCollector.sample` early `None` return; `ResourceSampler._run` loop body (tests stop the sampler before an interval elapses) and its `continue` skip branch (review: (f) alone never reaches it because `check_interval` clamps to the 0.01 interval, hence E-02 (h)). Direct calls at HEAD produced the values E-02 asserts (including `samples_taken 24` after 0.4s at `interval_seconds=0.01`, and a raising `tick` ending the thread after 1 call). The remaining misses lie in non-key functions (`_validate_scalar`, `_looks_like_path`, `_validate_label_list`, `_validate_number_map`, `validate_event`, `_validate_tool_versions`, `node_identity_input`, `ResourceProbeAdapter` defaults, `SystemResourceProbeAdapter` procfs readers, `_as_label`, `FakeResourceProbeAdapter.disk`, `TelemetryCollector.closed`/`elapsed_seconds`/`_node_id`) and are out of scope. |
| F-06 | `git show 19313eed^:tests/test_run_analytics_packaging.py` run at HEAD in the same scratch run | `1 failed, 11 passed` (with the telemetry file): `test_the_browser_assets_order_07_declares_ship_in_both_artifacts` fails with `ImportError: cannot import name 'REQUIRED_BROWSER_ASSETS' from 'tests.test_packaging'`, matching `b1mx2w` row `tests/test_run_analytics_packaging.py`. Its telemetry reach is only `FakeResourceProbeAdapter.__init__`/`cpu`/`load`/... via `test_measure_telemetry_collection_overhead`, which records a timing and asserts nothing; the restored telemetry file reaches every one of those keys (F-02). The rest of the file measures performance baselines against no declared budget or builds the wheel and sdist (subprocess, slow-tier work owned by `tests/test_packaging.py`). No other backlog item names it. |

## Proposed changes (ordered, validatable)

1. E-01 restores the behavioral subset of the deleted test module with a neutral canary and the `core` marker.
2. E-02 adds residual tests for the key-body branches the restored subset does not execute.

## Deferred / out of scope (with reason)

- `tests/test_run_analytics_packaging.py` is not restored (F-06).
  - Carrier-Declined: no work is owed for this item; every telemetry key it reaches is reached by the E-01 file, its measurement tests assert no budget, its one browser-asset test is stale against `tests/test_packaging.py`, and wheel/sdist content is already asserted there.
- Line coverage of non-key functions in the module (F-05) is not pursued.
  - Carrier-Declined: those functions are `reached` at baseline per `b1mx2w` and are not in `yqpb7q`; chasing their remaining branches would broaden scope beyond the item.

## Scope check

- Over-scope: none. One test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none for the 24 named keys; F-02 and F-05 show the restored subset plus E-02 executes every key's body.

## Required tests / validation

- `python3 -m pytest tests/test_run_analytics_telemetry.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes (core tier, including the restored module, within the 30s budget), with the summary line pasted.
- Reach: `COVERAGE_FILE=.aw/state/<scratch>/cov python3 -m pytest tests/test_run_analytics_telemetry.py -o addopts="" --cov=agent_workflows.run_analytics_telemetry --cov-report=json:.aw/state/<scratch>/cov.json --cov-report=term-missing`, then print, for each of the 24 keys, `files["agent_workflows/run_analytics_telemetry.py"]["functions"][<key>]` `executed_lines` count and `missing_lines` from the JSON (coverage 7.x); each key must have nonzero executed lines and empty `missing_lines`. `COVERAGE_FILE` under the gitignored `.aw/state/` keeps an untracked `.coverage` out of the worktree root; delete the scratch directory afterwards. Measured at review with (a) to (h): all 24 keys have empty `missing_lines`.
- Mutation spot-check: in scratch edits that are NOT committed, apply one mutation at a time (make `_parse_accelerator_csv` return `None`; make `build_event` return `None`; make `ResourceSampler.tick` return `not` its result; make `FakeResourceProbeAdapter._count` raise `RuntimeError`; make `TelemetryCollector.sample` always return `None`; make `_as_int` return `0` on failure), run the module, paste the failure for each, revert, and confirm `git diff agent_workflows/` is empty. `tick` negate-return means flipping both its `return True` (sample taken) and its `return False` (skip) one at a time. At review every listed mutation was killed: `_parse_accelerator_csv` None 2 failed, `build_event` None 2, `_count` raise 3, `sample` None 5, `tick` True->False 2, `tick` skip False->True 2, `_as_int` 0 1.
- `aw sanitize --agent` reports no `fail`.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the deleted telemetry test file verbatim, or a behavioral subset?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: restore the behavioral subset. Verbatim restore would bring back three text-asserting tests and unused `ast` helpers the repository's test contract forbids (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", F-03) and a maintainer-identifying canary (F-04). The remaining 59 tests pass unchanged at HEAD (F-02).

### OQ-02: Should this plan also restore `test_run_analytics_packaging.py`, which the backlog item names as a file to mine?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. The item says "mine", not "restore". Mining it yields nothing for the 24 keys beyond what the telemetry file already reaches, and its remaining content is unasserted measurement, one stale import, and slow wheel builds already covered by `tests/test_packaging.py` (F-06).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` and `git diff --stat HEAD` showing only `tests/test_run_analytics_telemetry.py` added; paste a diff between `git show 19313eed^:tests/test_run_analytics_telemetry.py` and the new file showing the only differences are the removed `ast` helpers and constant, the three removed text-asserting tests, the `_HANDLE` change and removed handle control assertion, the `pytest` import and `pytestmark` line, and the docstring paragraph (plus E-02's appended class); paste `rg -n "import ast|__doc__|__file__|getsource|import inspect|riello" tests/test_run_analytics_telemetry.py` returning nothing; paste the `-v` output listing every restored test as PASSED (or each failure with its E-01 disposition); paste the `ruff check --select F401` result; paste `python3 -m pytest --collect-only -q | rg test_run_analytics_telemetry` showing the module is selected by the bare core tier; paste the bare `python3 -m pytest` summary line and wall time within budget; paste the failures produced by the `build_event` return-None and `FakeResourceProbeAdapter._count` raise mutations (reverted afterwards); paste `aw sanitize --agent` showing no `fail`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every residual test as PASSED (the class name `ResidualKeyBranchTests` is a pointer, not the bar; the bar is that (a) to (h) are each asserted); paste the per-key reach listing from Required tests showing all 24 keys with empty `missing_lines`, plus the `term-missing` line for the module; paste the failures from the `_parse_accelerator_csv` return-None, `ResourceSampler.tick` negate-return, `TelemetryCollector.sample` always-None and `_as_int` return-0 mutations (reverted afterwards); paste three consecutive passing runs of `python3 -m pytest tests/test_run_analytics_telemetry.py -o addopts="" -q -k Residual` to show the real-time sampler tests are not flaky; paste a final empty `git diff agent_workflows/` and a `git status --short` showing no `.coverage` or other scratch file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Scope fence: `tests/test_run_analytics_telemetry.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under E-01's disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch edits to `agent_workflows/run_analytics_telemetry.py` that must be reverted and must not appear in the diff; scratch coverage files live under the gitignored `.aw/state/` and are deleted.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit 8bhcd3 -- tests/test_run_analytics_telemetry.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize 8bhcd3` instead. Never hand-`git mv` the plan.
