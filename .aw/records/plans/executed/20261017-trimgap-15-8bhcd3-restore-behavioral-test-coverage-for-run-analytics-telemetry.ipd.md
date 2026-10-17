# IPD: Restore behavioral test coverage for run_analytics_telemetry

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `yqpb7q` (Set `trimgap`, group 15 of the `b1mx2w` `## Filing plan`) records that 24 production keys in `agent_workflows/run_analytics_telemetry.py` (151 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. The module's own behavioral test file, `tests/test_run_analytics_telemetry.py`, was deleted by the suite trim `19313eed`, and the surviving tests that import the module (`tests/test_run_id_collision.py`, `tests/test_telemetry_platform_release.py`, plus runner tests that drive `TelemetryCollector` indirectly) reach only validation and collector plumbing. So a mutation that, for example, made `_parse_accelerator_csv` return `None` for good vendor output, made `build_event` return `None`, made `ResourceSampler.tick` report the opposite outcome, or made `FakeResourceProbeAdapter._count` raise would pass the routine suite.
- Scope: Restore `tests/test_run_analytics_telemetry.py` from `19313eed^` minus its code-pinning parts (the unused `ast` helpers `_code_identifiers`/`_imported_modules`/`_FORBIDDEN_CODE_IDENTIFIERS`, and three tests that assert on the module docstring text or on this test file's own source, F-03), replace the fragment-assembled maintainer-handle canary with a neutral one (F-04), add `pytestmark = pytest.mark.core` so the bare core-tier gate selects it, and append residual tests for the branches of the 24 keys the restored file still leaves unexecuted (F-05). The 24 keys: `_parse_accelerator_csv`, `SystemResourceProbeAdapter._run_bounded`, `build_event`, `ResourceSampler.tick`, `_validate_accelerators`, `FakeResourceProbeAdapter._count`, `FakeResourceProbeAdapter.cpu`, `FakeResourceProbeAdapter.load`, `FakeResourceProbeAdapter.memory`, `FakeResourceProbeAdapter.process`, `ProbeOutcome.to_dict`, `FakeResourceProbeAdapter.accelerators`, `FakeResourceProbeAdapter.tool_versions`, `ResourceSampler.__enter__`, `ResourceSampler._run`, `TelemetryCollector.__enter__`, `TelemetryCollector._note`, `TelemetryCollector.sample`, `_as_int`, `ResourceSampler.__exit__`, `ResourceSampler.running`, `TelemetryCollector.__exit__`, `TelemetryCollector.note_skipped_sample`, `FakeResourceProbeAdapter.__init__`. EXCLUDES any change to `agent_workflows/run_analytics_telemetry.py` or any other production file; EXCLUDES restoring `tests/test_run_analytics_packaging.py` (F-06); EXCLUDES driving the non-key missed lines of `_validate_scalar`, `_validate_number_map`, `node_identity_input` and the `SystemResourceProbeAdapter` procfs readers (F-05).
- Scope-Paths: tests/test_run_analytics_telemetry.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: yqpb7q
- Set: trimgap
- Order: 15
- Highest E allocated: 02
- Author: opencode
- Id: 8bhcd3

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 8bhcd3 verified (set trimgap, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (opencode): authored from backlog `yqpb7q`. Replayed both deleted files named by the item against HEAD `f71c0d0a6` in a scratch copy under `tests/`, applied the proposed subset edits, and measured module line coverage and per-test durations before writing any step; scratch copies and the `.coverage` file were removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 24 `unguarded-unreached` keys of `agent_workflows/run_analytics_telemetry.py` from backlog `yqpb7q` reached by the routine (bare, core-tier) test run, through behavioral tests that build and validate events, drive the fake and real probe adapters, run the collector and sampler lifecycles, and assert on the returned records, the written JSONL stream, thread state and raised refusals. Done means a mutation that breaks accelerator parsing, event construction, collector or sampler lifecycle, or the fake adapter turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the behavioral part of the deleted module

- [x] E-01 Create `tests/test_run_analytics_telemetry.py` from `git show 19313eed^:tests/test_run_analytics_telemetry.py` with exactly these edits: (1) delete the `_FORBIDDEN_CODE_IDENTIFIERS` constant with its comment block and the `_code_identifiers` and `_imported_modules` helpers (they parse source with `ast` and no remaining test calls them, F-03), and delete `import ast` and `import re` (`re` is used only by the deleted canary-literal test, so leaving it fails the repository's `ruff` pre-commit hook with `F401`, measured at review); (2) delete the three tests `EventSchemaTests.test_docstring_states_the_allowlist_direction`, `ProbeAdapterTests.test_the_bench_env_reuse_decision_is_recorded_in_the_module` (both assert substrings of `tel.__doc__`) and `PrivacyCorpusTests.test_no_literal_canary_is_committed_in_this_file` (reads `Path(__file__)` and regex-matches the maintainer handle's fragments), which `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" forbids restoring; (3) change the `_HANDLE` canary from the maintainer-handle fragments to the neutral `"some" + "one"` and delete the now-meaningless control assertion `"control: a handle IS a fail-severity finding, ..."` in `NodeIdentityTests.test_the_sanitizer_does_not_fail_on_a_hostname_which_is_why_the_direct_check_leads` (F-04), keeping its home-path control; (4) add `import pytest` and a module-level `pytestmark = pytest.mark.core`; (5) add a docstring paragraph naming backlog `yqpb7q`, findings `b1mx2w`, source revision `19313eed^`, and that the source-reading and docstring-text tests were deliberately not restored. Keep every other restored test body unchanged. Disposition rule if a restored test fails at execution HEAD (none did at authoring, F-02, or at review): do not mark E-01 performed until that test is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit and adjust only that test's expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it or papering over it, then continue.
  - Depends on: none
  - Expected outcome: the file exists, carries the `core` marker, and every restored test passes serially, under `-n 4`, and under random order (59 at authoring and at review; the count is context, not the bar); a bare `python3 -m pytest --collect-only -q` lists `tests/test_run_analytics_telemetry.py` items; `rg -n "import ast|__doc__|__file__|getsource|import inspect|riello" tests/test_run_analytics_telemetry.py` returns nothing; `python3 -m ruff check --select F401 tests/test_run_analytics_telemetry.py` reports no unused import.
  - Execution state: performed

### Task group 2: residual branch coverage for the 24 keys

- [x] E-02 Append one `ResidualKeyBranchTests(unittest.TestCase)` class (unittest style, matching the restored file) covering the branches of the 24 keys the restored file leaves unexecuted (F-05), each asserting a value observed at authoring: (a) `tel._parse_accelerator_csv("\n  \nGPU-A, 100, 50, 7, 550.1\n", vendor="nvidia")` returns `[{"vendor": "nvidia", "name": "GPU-A", "memory_total_mib": 100, "memory_used_mib": 50, "utilization_percent": 7, "driver_version": "550.1"}]` (blank-line skip) and `tel._parse_accelerator_csv("\n\n", vendor="nvidia")` is `None`; (b) `tel._as_int("x")` and `tel._as_int(None)` are `None` and `tel._as_int(" 4 ") == 4`; (c) `tel._validate_accelerators` called with `"abc"`, `{"a": 1}` and `5` each raises `tel.SchemaRefusal` whose message contains `"must be a list of accelerator objects"`; (d) `tel.build_event(event_kind="start", execution_id="exec-01", monotonic_offset_seconds=0.0, wall_timestamp="2026-09-13T20:00:00Z", phase=None)` returns a dict whose keys are exactly `{"event_kind", "execution_id", "monotonic_offset_seconds", "schema_version", "wall_timestamp"}` (a `None` field is omitted, not persisted); (e) a `TelemetryCollector` built like the restored `_collector` helper returns `None` from `sample()` before `start()` and again after `close()`, and the stream holds no `sample` event; (f) a `ResourceSampler(collector, interval_seconds=0.01)` on a started collector with the real monotonic clock, after `start()`, reaches `samples_taken >= 1` within a 5 second polling deadline and `stop()` leaves `running` False (the `_run` loop body and its `tick` call); (g) the same sampler with `tick` replaced by a function that records the call and raises `RuntimeError` exits its thread (`_thread.is_alive()` False within the deadline) after exactly one call, proving a tick failure ends the thread rather than propagating. (f), (g) and (h) are the only tests in the file that wait on real time; bound every wait by the deadline so a regression fails rather than hangs. Re-measure each value at execution HEAD before asserting it; if one has changed, apply the E-01 disposition rule. (h) The `_run` skip branch (`if now - last < self.interval: continue`) is NOT executed by (f), because with `interval_seconds=0.01` the clamped `check_interval` equals the interval, so every wake-up already exceeds it; measured at review, line `continue` stayed missed in 5 of 5 runs of (f) and (g). Cover it deterministically: a sampler with `interval_seconds=1.0` and an injected `monotonic` returning `0.0` for its first three calls and `10.0` afterwards, with `check_interval` set to `0.01` after construction, reaches `samples_taken == 1` within the deadline, and `stop()` then ends it. At review, a draft of (a) to (h) passed (67 passed) and left no missed line inside any of the 24 keys in 3 of 3 runs. All values (a) to (g) were re-measured at review at HEAD `be0827929` and matched.
  - Depends on: E-01
  - Expected outcome: the residual tests pass, and the coverage JSON per-function report (see Required tests) shows an empty `missing_lines` for each of the 24 keys (the authoring-time key-body misses were in `_validate_accelerators`, `build_event`, `_parse_accelerator_csv`, `_as_int`, `TelemetryCollector.sample` and `ResourceSampler._run`).
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste `git status --short` and `git diff --stat HEAD` showing only `tests/test_run_analytics_telemetry.py` added; paste a diff between `git show 19313eed^:tests/test_run_analytics_telemetry.py` and the new file showing the only differences are the removed `ast` helpers and constant, the three removed text-asserting tests, the `_HANDLE` change and removed handle control assertion, the `pytest` import and `pytestmark` line, and the docstring paragraph (plus E-02's appended class); paste `rg -n "import ast|__doc__|__file__|getsource|import inspect|riello" tests/test_run_analytics_telemetry.py` returning nothing; paste the `-v` output listing every restored test as PASSED (or each failure with its E-01 disposition); paste the `ruff check --select F401` result; paste `python3 -m pytest --collect-only -q | rg test_run_analytics_telemetry` showing the module is selected by the bare core tier; paste the bare `python3 -m pytest` summary line and wall time within budget; paste the failures produced by the `build_event` return-None and `FakeResourceProbeAdapter._count` raise mutations (reverted afterwards); paste `aw sanitize --agent` showing no `fail`.
  - Observed evidence:
    - `git status --short` and `git diff --stat HEAD` showing only `tests/test_run_analytics_telemetry.py` added:
      ```
      $ git status --short
      ?? tests/test_run_analytics_telemetry.py
      $ git diff --stat HEAD
      (empty)
      ```
    - Diff between `git show 19313eed^:tests/test_run_analytics_telemetry.py` and the new file:
      ```diff
      --- 19313eed^:tests/test_run_analytics_telemetry.py
      +++ tests/test_run_analytics_telemetry.py
      @@ -24,13 +24,15 @@
       the tests that must prove the absence of a subprocess install a stub that RAISES if invoked.

       Stdlib unittest only.
      +
      +Restored for backlog yqpb7q (findings b1mx2w, source revision 19313eed^). The original file's
      +ast-based source-reading helpers and docstring-text assertions were deliberately not restored
      +per repository test conventions forbidding code-pinning tests.
       """

       from __future__ import annotations

      -import ast
       import json
      -import re
       import socket
       import subprocess
       import tempfile
      @@ -39,76 +41,20 @@
       import unittest
       from pathlib import Path

      +import pytest
      +
      +pytestmark = pytest.mark.core
      +
       from agent_workflows import leak_sanitizer as ls
       from agent_workflows import run_analytics_config as cfg
       from agent_workflows import run_analytics_telemetry as tel
       from tests.support import REPO_ROOT

       # --- Canaries, assembled from fragments so this file holds no literal leak ----------------------
      -_HANDLE = "gfa" + "riello"
      +_HANDLE = "some" + "one"
       _HOME_PATH = "/ho" + "me/" + _HANDLE + "/VC/agent-workflows"
       _SALT = "a" * 64
       _OTHER_SALT = "b" * 64
      -
      -#: Names that must appear NOWHERE in this module's executable code.
      -_FORBIDDEN_CODE_IDENTIFIERS = frozenset(...)
      -def _code_identifiers(path: Path) -> set[str]: ...
      -def _imported_modules(path: Path) -> set[str]: ...
      @@ -310,6 +256,0 @@
      -    def test_docstring_states_the_allowlist_direction(self) -> None:
      -        doc = tel.__doc__ or ""
      -        self.assertIn("THE SCHEMA IS AN ALLOWLIST", doc)
      -        self.assertIn("TEST CORPUS", doc)
      -
      @@ -513,14 +454,6 @@
      -    def test_the_bench_env_reuse_decision_is_recorded_in_the_module(self) -> None:
      -        doc = tel.__doc__ or ""
      -        self.assertIn("REUSE DECISION", doc)
      -        self.assertIn("bench_env.py", doc)
      -        self.assertIn("WRITE FRESH, MODELED ON IT, WITH ATTRIBUTION", doc)
      -        self.assertIn("INSTALLED WORKFLOW CONTENT", doc)
      @@ -759,11 +692,7 @@
      -        # CONTROL: the same invocation DOES fail on a username and a home path.
      -        self.assertTrue(
      -            [f for f in _scan(_HANDLE) if f.severity == "fail"],
      -            "control: a handle IS a fail-severity finding, so the scan above was looking",
      -        )
      +        # CONTROL: the same invocation DOES fail on a home path.
               self.assertTrue(
                   [f for f in _scan(_HOME_PATH) if f.severity == "fail"],
                   "control: a home path IS a fail-severity finding",
               )
      @@ -1320,11 +1249,155 @@
      -    def test_no_literal_canary_is_committed_in_this_file(self) -> None:
      -        source = Path(__file__).read_text(encoding="utf-8")
      -        self.assertNotIn(_HANDLE, source.replace('"gfa" + "riello"', ""))
      -        self.assertTrue(re.search(r'"gfa"\s*\+\s*"riello"', source))
      +
      +# ================================================================================================
      +# Residual branch coverage for the 24 unguarded-unreached keys (IPD 8bhcd3, E-02)
      +# ================================================================================================
      +class ResidualKeyBranchTests(unittest.TestCase):
      +    """Residual branch coverage for the 24 unguarded-unreached keys from backlog yqpb7q."""
      ...
      ```
    - `rg -n "import ast|__doc__|__file__|getsource|import inspect|riello" tests/test_run_analytics_telemetry.py` returning nothing:
      ```
      $ rg -n "import ast|__doc__|__file__|getsource|import inspect|riello" tests/test_run_analytics_telemetry.py
      (returns exit code 1, empty output)
      ```
    - `-v` output listing restored tests as PASSED:
      ```
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_each_event_kind_round_trips PASSED [  1%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_full_event_with_every_payload_round_trips PASSED [  2%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_unknown_key_is_refused_and_not_silently_dropped PASSED [  4%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_out_of_vocabulary_event_kind_is_refused PASSED [  5%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_unknown_schema_version_is_refused_before_key_checks PASSED [  7%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_missing_required_field_is_refused PASSED [  8%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_nested_observation_objects_have_their_own_allowlists PASSED [ 10%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_a_raw_host_identity_cannot_ride_in_through_node_id PASSED [ 11%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field PASSED [ 13%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_negative_and_non_finite_numbers_are_refused PASSED [ 14%]
      tests/test_run_analytics_telemetry.py::EventSchemaTests::test_build_event_validates_at_construction PASSED [ 16%]
      tests/test_run_analytics_telemetry.py::SchemaMutationTests::test_dropping_instead_of_refusing_breaks_the_boundary PASSED [ 17%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_real_adapter_probes_this_machine_without_raising PASSED [ 19%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_a_denied_probe_degrades_to_a_structured_reason_rather_than_raising PASSED [ 20%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_absent_procfs_yields_unavailable_not_an_exception PASSED [ 22%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_malformed_procfs_yields_parse_error_with_a_byte_count_only PASSED [ 23%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_composed_resources_record_every_failure_as_a_label PASSED [ 25%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_every_command_probe_is_bounded_by_a_timeout_and_an_output_cap PASSED [ 26%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_a_timing_out_command_is_reported_not_raised PASSED [ 28%]
      tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_a_missing_executable_is_reported_not_raised PASSED [ 29%]
      tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_a_well_formed_reading_parses_to_numeric_and_categorical_fields PASSED [ 31%]
      tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_absent_tool_yields_unavailable PASSED [ 32%]
      tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_timeout_yields_the_timeout_code PASSED [ 34%]
      tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_malformed_output_yields_parse_error_carrying_only_a_byte_length PASSED [ 35%]
      tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_no_raw_tool_output_reaches_the_jsonl_on_any_failure_path PASSED [ 37%]
      tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_persisting_raw_output_would_break_this_suite PASSED [ 38%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_the_same_node_yields_a_stable_pseudonym PASSED [ 40%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_a_different_node_yields_a_different_pseudonym PASSED [ 41%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_rotating_the_salt_invalidates_correlation_by_design PASSED [ 43%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_a_missing_salt_is_refused_rather_than_defaulted PASSED [ 44%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_neither_the_raw_hostname_nor_the_hash_input_appears_in_the_pseudonym PASSED [ 46%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_the_raw_hostname_is_absent_from_the_produced_jsonl PASSED [ 47%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_the_sanitizer_does_not_fail_on_a_hostname_which_is_why_the_direct_check_leads PASSED [ 49%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_sanitizer_scan_of_the_produced_telemetry_is_clean_with_a_control PASSED [ 50%]
      tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_identity_assembly_never_raises_even_with_every_source_broken PASSED [ 52%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_one_execution_yields_exactly_one_start_and_one_end PASSED [ 53%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_second_close_is_a_no_op_and_emits_no_second_end PASSED [ 55%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_second_start_emits_nothing PASSED [ 56%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_durations_derive_from_a_monotonic_clock_and_are_never_negative PASSED [ 58%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_wall_clock_stepping_backwards_cannot_produce_a_negative_duration PASSED [ 59%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_an_unwritable_stream_records_a_warning_and_never_ends_the_run PASSED [ 61%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_disabled_config_emits_nothing_at_all PASSED [ 62%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_an_adapter_that_raises_is_isolated_to_a_warning PASSED [ 64%]
      tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_allowlisted_context_fields_are_carried_and_others_are_not PASSED [ 65%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_the_thread_is_stopped_after_exit PASSED [ 67%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_the_thread_is_stopped_after_an_exception_inside_the_block PASSED [ 68%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_the_thread_is_stopped_by_a_signal_assisted_teardown PASSED [ 70%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_stop_is_idempotent_and_safe_before_start PASSED [ 71%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_an_overlapping_tick_is_skipped_and_counted_never_queued PASSED [ 73%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_a_probe_slower_than_the_interval_skips_rather_than_accumulating PASSED [ 74%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_the_check_interval_is_clamped_against_the_interval PASSED [ 76%]
      tests/test_run_analytics_telemetry.py::SamplerTests::test_sampling_does_not_run_when_it_is_not_enabled PASSED [ 77%]
      tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_each_degraded_case_completes_with_a_structured_warning PASSED [ 79%]
      tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_impossible_values_are_refused_rather_than_persisted PASSED [ 80%]
      tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_negative_and_absurd_resource_values_do_not_break_the_stream PASSED [ 82%]
      tests/test_run_analytics_telemetry.py::NoRealIOTests::test_a_fake_adapter_run_performs_no_subprocess_no_sleep_and_no_network PASSED [ 83%]
      tests/test_run_analytics_telemetry.py::OverheadTests::test_per_event_cost_against_the_real_append_jsonl_is_bounded PASSED [ 85%]
      tests/test_run_analytics_telemetry.py::OverheadTests::test_sampling_cadence_cannot_exceed_the_configured_rate PASSED [ 86%]
      tests/test_run_analytics_telemetry.py::PrivacyCorpusTests::test_no_forbidden_shaped_value_can_be_persisted PASSED [ 88%]
      ```
    - `ruff check --select F401`:
      ```
      $ python3 -m ruff check --select F401 tests/test_run_analytics_telemetry.py
      All checks passed!
      ```
    - `python3 -m pytest --collect-only -q | rg test_run_analytics_telemetry`:
      ```
      $ python3 -m pytest --collect-only -q | rg test_run_analytics_telemetry
      tests/test_run_analytics_telemetry.py: 67
      ```
    - Bare `python3 -m pytest` summary line:
      ```
      960 passed in 46.79s
      Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
      ```
    - Scratch mutation spot-checks (reverted):
      `build_event` return-None:
      ```
      FAILED tests/test_run_analytics_telemetry.py::EventSchemaTests::test_build_event_validates_at_construction
      FAILED tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_build_event_omits_none_fields
      2 failed, 65 passed in 1.59s
      ```
      `FakeResourceProbeAdapter._count` raise:
      ```
      FAILED tests/test_run_analytics_telemetry.py::SamplerTests::test_a_probe_slower_than_the_interval_skips_rather_than_accumulating
      FAILED tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_composed_resources_record_every_failure_as_a_label
      FAILED tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_impossible_values_are_refused_rather_than_persisted
      3 failed, 64 passed in 1.90s
      ```
    - `aw sanitize --agent`:
      ```
      {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5869,"findings":0,"evidence":["leak-scan"],"next":null}
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every residual test as PASSED (the class name `ResidualKeyBranchTests` is a pointer, not the bar; the bar is that (a) to (h) are each asserted); paste the per-key reach listing from Required tests showing all 24 keys with empty `missing_lines`, plus the `term-missing` line for the module; paste the failures from the `_parse_accelerator_csv` return-None, `ResourceSampler.tick` negate-return, `TelemetryCollector.sample` always-None and `_as_int` return-0 mutations (reverted afterwards); paste three consecutive passing runs of `python3 -m pytest tests/test_run_analytics_telemetry.py -o addopts="" -q -k Residual` to show the real-time sampler tests are not flaky; paste a final empty `git diff agent_workflows/` and a `git status --short` showing no `.coverage` or other scratch file.
  - Observed evidence:
    - `-v` output listing every residual test as PASSED:
      ```
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_validate_accelerators_refuses_non_list PASSED [ 89%]
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sampler_run_skip_branch_deterministic PASSED [ 91%]
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_as_int_invalid_or_none_and_whitespace PASSED [ 92%]
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sample_returns_none_before_start_and_after_close PASSED [ 94%]
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_build_event_omits_none_fields PASSED [ 95%]
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_parse_accelerator_csv_blank_line_skip_and_empty PASSED [ 97%]
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sampler_real_loop_runs_and_stops PASSED [ 98%]
      tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sampler_tick_failure_terminates_thread PASSED [100%]
      ```
    - Per-key reach listing from coverage report (all 24 keys have nonzero executed lines and empty missing lines):
      ```
      agent_workflows/run_analytics_telemetry.py     647     70    89%   367, 373, 384, 399, 401, 418, 436, 448, 452, 509, 515-516, 518, 530, 544, 551, 568, 605, 634, 638, 705-706, 711-712, 717, 758, 761, 764, 767, 770, 773, 776, 798-802, 837-838, 869-870, 877-878, 890-891, 895, 902, 905, 909, 930, 933-934, 943-944, 965-966, 968, 977, 997-998, 1000, 1024, 1092, 1095, 1186-1187, 1311, 1322, 1372-1374

      Total keys checked: 24
        _parse_accelerator_csv: executed_lines=21, missing_lines=[]
        SystemResourceProbeAdapter._run_bounded: executed_lines=7, missing_lines=[]
        build_event: executed_lines=6, missing_lines=[]
        ResourceSampler.tick: executed_lines=10, missing_lines=[]
        _validate_accelerators: executed_lines=6, missing_lines=[]
        FakeResourceProbeAdapter._count: executed_lines=3, missing_lines=[]
        FakeResourceProbeAdapter.cpu: executed_lines=2, missing_lines=[]
        FakeResourceProbeAdapter.load: executed_lines=2, missing_lines=[]
        FakeResourceProbeAdapter.memory: executed_lines=2, missing_lines=[]
        FakeResourceProbeAdapter.process: executed_lines=2, missing_lines=[]
        ProbeOutcome.to_dict: executed_lines=4, missing_lines=[]
        FakeResourceProbeAdapter.accelerators: executed_lines=2, missing_lines=[]
        FakeResourceProbeAdapter.tool_versions: executed_lines=2, missing_lines=[]
        ResourceSampler.__enter__: executed_lines=2, missing_lines=[]
        ResourceSampler._run: executed_lines=10, missing_lines=[]
        TelemetryCollector.__enter__: executed_lines=2, missing_lines=[]
        TelemetryCollector._note: executed_lines=2, missing_lines=[]
        TelemetryCollector.sample: executed_lines=3, missing_lines=[]
        _as_int: executed_lines=4, missing_lines=[]
        ResourceSampler.__exit__: executed_lines=1, missing_lines=[]
        ResourceSampler.running: executed_lines=1, missing_lines=[]
        TelemetryCollector.__exit__: executed_lines=1, missing_lines=[]
        TelemetryCollector.note_skipped_sample: executed_lines=1, missing_lines=[]
        FakeResourceProbeAdapter.__init__: executed_lines=10, missing_lines=[]
      All 24 keys nonzero executed lines and empty missing lines: True
      ```
    - Scratch mutation spot-checks (reverted):
      `_parse_accelerator_csv` return-None:
      ```
      FAILED tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_parse_accelerator_csv_blank_line_skip_and_empty
      FAILED tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_a_well_formed_reading_parses_to_numeric_and_categorical_fields
      2 failed, 65 passed in 1.97s
      ```
      `ResourceSampler.tick` negate-return True -> False:
      ```
      FAILED tests/test_run_analytics_telemetry.py::SamplerTests::test_a_probe_slower_than_the_interval_skips_rather_than_accumulating
      FAILED tests/test_run_analytics_telemetry.py::SamplerTests::test_an_overlapping_tick_is_skipped_and_counted_never_queued
      2 failed, 65 passed in 1.75s
      ```
      `ResourceSampler.tick` negate-return False -> True:
      ```
      FAILED tests/test_run_analytics_telemetry.py::SamplerTests::test_an_overlapping_tick_is_skipped_and_counted_never_queued
      FAILED tests/test_run_analytics_telemetry.py::SamplerTests::test_a_probe_slower_than_the_interval_skips_rather_than_accumulating
      2 failed, 65 passed in 3.59s
      ```
      `TelemetryCollector.sample` always-None:
      ```
      FAILED tests/test_run_analytics_telemetry.py::SamplerTests::test_a_probe_slower_than_the_interval_skips_rather_than_accumulating
      FAILED tests/test_run_analytics_telemetry.py::OverheadTests::test_per_event_cost_against_the_real_append_jsonl_is_bounded
      FAILED tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_each_degraded_case_completes_with_a_structured_warning
      FAILED tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_negative_and_absurd_resource_values_do_not_break_the_stream
      FAILED tests/test_run_analytics_telemetry.py::NoRealIOTests::test_a_fake_adapter_run_performs_no_subprocess_no_sleep_and_no_network
      5 failed, 62 passed in 1.20s
      ```
      `_as_int` return-0:
      ```
      FAILED tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_as_int_invalid_or_none_and_whitespace
      1 failed, 66 passed in 2.83s
      ```
    - Three consecutive passing runs of `python3 -m pytest tests/test_run_analytics_telemetry.py -o addopts="" -q -k Residual`:
      ```
      8 passed, 59 deselected in 0.44s
      8 passed, 59 deselected in 0.67s
      8 passed, 59 deselected in 2.04s
      ```
    - Final empty `git diff agent_workflows/`:
      ```
      $ git diff agent_workflows/
      (empty)
      ```
    - `git status --short`:
      ```
      $ git status --short
      ?? tests/test_run_analytics_telemetry.py
      ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Scope fence: `tests/test_run_analytics_telemetry.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under E-01's disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch edits to `agent_workflows/run_analytics_telemetry.py` that must be reverted and must not appear in the diff; scratch coverage files live under the gitignored `.aw/state/` and are deleted.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit 8bhcd3 -- tests/test_run_analytics_telemetry.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize 8bhcd3` instead. Never hand-`git mv` the plan.
