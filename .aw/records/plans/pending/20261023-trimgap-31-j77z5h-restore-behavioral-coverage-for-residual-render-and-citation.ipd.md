# IPD: Restore behavioral coverage for residual render and citation helpers

- Date: 2026-10-23
- Kind: child
- Concern: Residual backlog item `nzc6dm` carries five small pure rendering/citation keys that the routine core tier does not guard, all with operator `return-none`: `render_stream.Palette.status` and `render_stream._status_glyph_char` (group 18, `wo21z5` `unguarded-unreached`), `attention._gate_ref_display` (group 24, `unguarded`), `plan_readiness.cite_review_entry` (group 39, `unguarded`) and `render_stream.format_spec_impact_announcement` (group 41, `budget-exhausted`). Measured at authoring HEAD `6c0a6b72a` (F-01, F-02): the first four are not reached by the core tier and survive every surviving file that reaches them; `format_spec_impact_announcement` IS reached by core (4 contexts) and its mutant SURVIVES the core-reaching files. So a regression that made the runner status word, the tool-event glyph, the compact gate ref, the review citation or the pre-run SPEC CHANGES banner disappear would pass the routine gate.
- Scope: Add ONE new core-marked test module, `tests/test_render_residual_helpers.py`, with direct behavioral tests of the five keys asserting on their returned strings, tuples and lines (values measured at F-03), mining the two behavioral assertions of the deleted `tests/test_lifecycle_palette_singleness.py` that kill the `render_stream` keys (F-04); then probe all five under the core selection. EXCLUDES restoring `tests/test_lifecycle_palette_singleness.py` whole (its A17 helper walks production source with `ast` and `pathlib`, which `AGENTS.md` forbids, F-04); EXCLUDES any production-code change; EXCLUDES `attention._shared_gate_ref`, `render_table` and `_render_table_row` (owned by plan `a5drqh`).
- Scope-Paths: tests/test_render_residual_helpers.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: nzc6dm
- Set: trimgap
- Order: 31
- Highest E allocated: 06
- Author: opencode
- Id: j77z5h
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved

- 2026-10-23 reviewed (opencode): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (test classes must subclass unittest.TestCase or pytest never collects them, F-06), PR-002 (gate lifecycle and honesty contract), PR-003 (E-05/V-05 exit-status bar on an enforcing host), PR-004 (stale a5drqh status) fixed; F-03 values and two survivals re-measured (F-07)
- 2026-10-23 to-review (opencode): authored from backlog `nzc6dm` (groups 18, 24, 39, 41). Measured core reach at HEAD `6c0a6b72a`, probed each key against its surviving files and against the deleted control files, and measured every asserted return value before writing expected outcomes.
- 2026-10-23 draft (opencode): created.

## Goal

Make a `return-none` mutation of any of the five keys turn a routine core-tier test red, using direct assertions on what each helper returns. Done means all five report `verdict: killed` under a `-m core` selection containing the new module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the new core-tier module

- [x] E-01 Create `tests/test_render_residual_helpers.py` with a provenance docstring naming backlog `nzc6dm`, plan `j77z5h`, findings `wo21z5` and the mined source `19313eed^:tests/test_lifecycle_palette_singleness.py`; imports laid out exactly as `tests/test_attention_stem.py` (`from __future__ import annotations`; stdlib `import unittest`; a separate third-party group `import pytest`; then the first-party group `from agent_workflows import attention, plan_readiness, render_stream`), so ruff `I001` and the mutating pre-commit `ruff --fix` hook do not rewrite and reject the commit; module-level `pytestmark = pytest.mark.core` after the last import; and a `RunnerStatusAndGlyphTests(unittest.TestCase)` class. EVERY test class in this module (E-01 to E-04) MUST subclass `unittest.TestCase`: `[tool.pytest.ini_options]` sets no `python_classes`, so pytest's default `Test*` prefix applies and a plain class named `...Tests` is silently NOT collected (F-06). Assert, as mined from the deleted A17/A18 tests and measured at F-03: `render_stream.Palette(True).status("approved")` contains `38;5;45m` and `.status("executed")` contains `38;5;46m`, and the two differ (ready is not rendered as done); `Palette(True).status("weird")` still contains the word `weird` (an unmapped status degrades to text); `Palette(False).status("executed") == "executed"`. `render_stream._status_glyph_char` returns `("\u2713","green")` for `completed`, `("\u2717","red")` for `error` and `failed`, `("\u2026","yellow")` for `running`, `pending` and `in_progress`, `("\u2022","gray")` for any other status, and in ASCII mode (`use_unicode=False`) `("+","green")`, `("x","red")`, `(".","yellow")`, `("-","gray")`.
  - Depends on: none
  - Expected outcome: the class's tests are COLLECTED (they appear in `-v` output) and PASS at HEAD.
  - Execution state: performed

- [x] E-02 Add a `GateRefDisplayTests(unittest.TestCase)` class calling `attention._gate_ref_display(ref, long=...)`: `"TODO.md"` -> `"TODO.md"` (a non-path ref is never compacted); `"issue#12"` -> `"issue#12"`; `""` -> `""`; `".aw/records/plans/pending/20260903-runflags-01-uyeko5-wire-the-spec.ipd.md"` -> `"20260903-runflags-01-uyeko5"` with `long=False` and the full path verbatim with `long=True`.
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: performed

- [x] E-03 Add a `CiteReviewEntryTests(unittest.TestCase)` class calling `plan_readiness.cite_review_entry`: `"- 2026-10-01 reviewed (plan-review): findings F-01..F-03 resolved; Readiness go"` -> `"the review of 2026-10-01, findings F-01..F-03"`, and assert the result does NOT contain the verdict token `go` as a word nor `reviewed` (the function's contract is a citation with no verdict token); `""` -> `""`; `"garbage"` -> `""`.
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: performed

- [x] E-04 Add a `SpecImpactAnnouncementTests(unittest.TestCase)` class calling `render_stream.format_spec_impact_announcement(impacts, pal=render_stream.Palette(False))`: an empty list returns `[]`; a list whose only item has `"specs": []` returns `[]`; `[{"id6": "abc123", "setid": "s", "specs": ["a.spec.md", "b.spec.md"]}, {"id6": "def456", "setid": "s", "specs": []}]` returns exactly `["SPEC CHANGES: 1 queued plan(s) declare edits to 2 specification file(s).", "  A spec is the contract other plans are reviewed against, so review these first.", "    abc123 (s) -> a.spec.md", "    abc123 (s) -> b.spec.md"]`.
  - Depends on: E-01
  - Expected outcome: the class's tests PASS at HEAD (values measured at F-03).
  - Execution state: performed

### Task group 2: commit and prove the mutants die in core

- [x] E-05 Commit the module with `aw commit j77z5h -- tests/test_render_residual_helpers.py`, then run the routine bare gate `python3 -m pytest` and record its summary line and any `CORE TIER BUDGET EXCEEDED` block verbatim, plus `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_render_residual_helpers.py`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: bare run summary shows `passed` with no `failed` or `error` and its collected count includes the new tests; it either exits 0 or exits 1 solely because of an enforced `CORE TIER BUDGET EXCEEDED` block (no `Core tier budget not enforced` line) whose listed slowest tests include none from the new module (the core tier already overruns its 30s budget on a 12-CPU host before this plan: sibling `bli2ba` review measured 34.61s, exit 1, 1675 passed). Any other non-zero exit is a failure. The module costs well under one second (pure in-memory calls).
  - Execution state: performed

- [x] E-06 For each key K in (`agent_workflows/render_stream.py::Palette.status`, `agent_workflows/render_stream.py::_status_glyph_char`, `agent_workflows/attention.py::_gate_ref_display`, `agent_workflows/plan_readiness.py::cite_review_entry`, `agent_workflows/render_stream.py::format_spec_impact_announcement`), run `python3 tools/mutation_probe.py --op return-none --format json K -- -o addopts= -q -p no:randomly -n0 -m core tests/test_render_residual_helpers.py`, after E-05's commit (the tool mutates a disposable worktree cut from HEAD). A kill under this core-marked subset is a kill under the full core tier, a superset. Record each `verdict`, `baseline_failing` and `mutant_failing`; if any key survives, add the missing assertion, commit the same way, and re-probe.
  - Depends on: E-05
  - Expected outcome: five `verdict: killed`, each `baseline_failing: 0`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16): every assertion calls a helper and checks its return value. The deleted palette module's source-walking A17 test is not restored.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget; module-level `pytestmark = pytest.mark.core` is the established way in (`tests/test_engine_restored_behavior.py`).
- Probe tool: `tools/mutation_probe.py` as used by `wo21z5` and siblings.
- Commit only through `aw commit j77z5h -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `python3 tools/replay_coverage_diff.py baseline --out .aw/state/nzc6dm-auth/core -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `6c0a6b72a` | `Palette.status`, `_status_glyph_char`, `_gate_ref_display`, `cite_review_entry` are absent from the core baseline. `format_spec_impact_announcement` is reached by 4 core contexts in 1 file. |
| F-02 | `tools/mutation_probe.py --op return-none --format json <K> -- -o addopts= -q -p no:randomly -n 6 -m <sel> <files>` at `6c0a6b72a` | `format_spec_impact_announcement` under `-m "core and not slow and not livecorpus"` over its core-reaching file: `survived`, 0 (52.06s). Under `-m "not slow and not livecorpus"`: `_gate_ref_display` over `tests/test_attention.py`: `survived`, 0 (18.83s); `cite_review_entry` over `tests/test_read_verb_zero_match_refusal.py tests/test_review_record_classifier.py`: `survived`, 0 (12.42s). `Palette.status` and `_status_glyph_char` have no surviving reaching file at all (`wo21z5` `unguarded-unreached`). |
| F-03 | direct calls at HEAD `6c0a6b72a` | `Palette(True).status('approved')` = `'\x1b[1;38;5;45mapproved\x1b[0m'`, `.status('executed')` = `'\x1b[1;38;5;46mexecuted\x1b[0m'`, `.status('weird')` = `'\x1b[38;5;244mweird\x1b[0m'`; `Palette(False).status('executed')` = `'executed'`. `_status_glyph_char`: completed `('✓','green')`, error/failed `('✗','red')`, running/pending/in_progress `('…','yellow')`, other `('•','gray')`; ASCII `+`/`x`/`.`/`-` with the same colors. `_gate_ref_display`: `'TODO.md'`, `'issue#12'`, `''` verbatim; the deep plan path -> `'20260903-runflags-01-uyeko5'` (`long=False`) and verbatim (`long=True`). `cite_review_entry` of the E-03 entry -> `'the review of 2026-10-01, findings F-01..F-03'`; `''` and `'garbage'` -> `''`. `format_spec_impact_announcement` outputs as listed in E-04. |
| F-04 | `tools/mutation_probe.py --op return-none --extra-test 19313eed:tests/test_lifecycle_palette_singleness.py <K> -- -o addopts= -q -p no:randomly -n0 tests/test_lifecycle_palette_singleness.py`; and `git show 19313eed^:tests/test_lifecycle_palette_singleness.py` | `Palette.status`: `killed`, 1 (`test_the_runner_lifecycle_colors_no_longer_collapse_ready_into_done`). `_status_glyph_char`: `killed`, 1 (`test_the_tool_event_severity_colors_are_untouched`). E-01 mines exactly those assertions. The same file imports `ast` and `pathlib` and its `_module_files`/`_color_or_glyph_dicts` helpers walk every production module's syntax tree, a code-structure pin, so the file is not restored whole. |
| F-05 | `tools/mutation_probe.py --op return-none --extra-test 19313eed:tests/test_attention_priority_blocker.py agent_workflows/attention.py::_gate_ref_display -- ... tests/test_attention_priority_blocker.py` | `killed`, 7 newly failing `GateRefRenderingTests` tests. Pending plan `a5drqh` restores that file into core and would also guard `_gate_ref_display`; it was `to-review` at authoring and is `approved` at review (`72da75876`) but not executed, so E-02 adds a direct test so this plan does not depend on `a5drqh` executing. |
| F-06 | `/plan-review` at `72da75876`: a scratch module with `pytestmark = pytest.mark.core` and a plain `class RunnerStatusAndGlyphTests:` holding a failing test, run with `python3 -m pytest -o addopts= -q`; `pyproject.toml` `[tool.pytest.ini_options]` (no `python_classes`) | `no tests ran`, exit 5: a class not prefixed `Test` and not subclassing `unittest.TestCase` is not collected. Repo modules use `unittest.TestCase` subclasses with `*Tests` names (`tests/test_run_analytics_telemetry.py` `EventSchemaTests(unittest.TestCase)`). |
| F-07 | `/plan-review` re-measure at `72da75876`/`d3a4d10c6` | Every F-03 return value reproduces exactly. `cite_review_entry` probe over `-m core tests/test_plan_readiness.py`: `survived`, `mutant_failing: 0`. `Palette.status` probe over `-m core tests/`: `survived`, `mutant_failing: 0` (700.57s). The gap is still open. |

## Proposed changes (ordered, validatable)

1. E-01 creates the module and the runner status / glyph tests.
2. E-02 adds the compact gate-ref tests.
3. E-03 adds the review-citation tests.
4. E-04 adds the SPEC CHANGES banner tests.
5. E-05 commits the module and records the bare core gate.
6. E-06 probes all five keys under the core selection.

## Deferred / out of scope (with reason)

- Restoring `tests/test_lifecycle_palette_singleness.py` whole.
  - Carrier-Declined: no work is owed; its other tests pin source structure (F-04), which `AGENTS.md` forbids restoring, and its two behavioral kills are mined into E-01.
- `attention._shared_gate_ref`, `render_table`, `_render_table_row`.
  - Carrier: a5drqh
  - Carrier-Evidence: .aw/records/plans/executed/20261023-trimgap-25-a5drqh-restore-behavioral-coverage-for-the-attention-board-shared-g.ipd.md

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. All five keys get direct assertions (E-01 to E-04) and a core-selection probe (E-06).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_render_residual_helpers.py`: every test PASSED, list pasted (E-01 to E-04).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-05).
- Five `tools/mutation_probe.py` JSON results pasted, each `verdict: killed`, `baseline_failing: 0` (E-06).
- `git diff --stat <E-05 parent>..HEAD -- agent_workflows/` empty (no production change).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Should E-02 rely on plan `a5drqh` restoring the attention control file instead of adding a direct test?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `a5drqh` is approved but not executed (it was `to-review` at authoring), and a dependency on a plan that may never execute would leave this key's gap open indefinitely. The direct test is five assertions on a pure function and costs effectively nothing; if both land, the overlap is harmless and either one alone keeps the key guarded (F-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_render_residual_helpers.py` showing the provenance docstring (naming `nzc6dm`, `j77z5h`, `wo21z5`, `19313eed^`) and `pytestmark = pytest.mark.core`; paste the `-v` lines for every `RunnerStatusAndGlyphTests` test, each PASSED; paste `grep -nE "inspect|getsource|ast\.|pathlib" tests/test_render_residual_helpers.py` returning nothing.
  - Observed evidence:
    ```text
    $ head -n 19 tests/test_render_residual_helpers.py
    """Residual render and citation behavioral tests.

    Provenance:
    - Backlog: nzc6dm
    - Plan: j77z5h
    - Findings: wo21z5
    - Mined source: 19313eed^:tests/test_lifecycle_palette_singleness.py
    """

    from __future__ import annotations

    import unittest

    import pytest

    from agent_workflows import attention, plan_readiness, render_stream

    pytestmark = pytest.mark.core

    $ python3 -m pytest -o addopts="" -v tests/test_render_residual_helpers.py -k RunnerStatusAndGlyphTests
    tests/test_render_residual_helpers.py::RunnerStatusAndGlyphTests::test_palette_status_ready_differs_from_done_and_unmapped_degrades PASSED [ 50%]
    tests/test_render_residual_helpers.py::RunnerStatusAndGlyphTests::test_status_glyph_char_unicode_and_ascii PASSED [100%]

    $ grep -nE "inspect|getsource|ast\.|pathlib" tests/test_render_residual_helpers.py
    (empty output, exit 1)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` lines for every `GateRefDisplayTests` test, each PASSED.
  - Observed evidence:
    ```text
    $ python3 -m pytest -o addopts="" -v tests/test_render_residual_helpers.py -k GateRefDisplayTests
    tests/test_render_residual_helpers.py::GateRefDisplayTests::test_gate_ref_display_compact_and_verbatim PASSED [100%]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` lines for every `CiteReviewEntryTests` test, each PASSED.
  - Observed evidence:
    ```text
    $ python3 -m pytest -o addopts="" -v tests/test_render_residual_helpers.py -k CiteReviewEntryTests
    tests/test_render_residual_helpers.py::CiteReviewEntryTests::test_cite_review_entry_derives_citation_without_verdict_token PASSED [100%]
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `-v` lines for every `SpecImpactAnnouncementTests` test, each PASSED.
  - Observed evidence:
    ```text
    $ python3 -m pytest -o addopts="" -v tests/test_render_residual_helpers.py -k SpecImpactAnnouncementTests
    tests/test_render_residual_helpers.py::SpecImpactAnnouncementTests::test_format_spec_impact_announcement_empty_and_populated PASSED [100%]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `aw commit` output (or `git show --stat HEAD`) naming only `tests/test_render_residual_helpers.py`; paste the bare `python3 -m pytest` summary line with no `failed` or `error`, its exit status, any `CORE TIER BUDGET EXCEEDED` block verbatim (an exit 1 passes only per E-05's expected outcome; state that check), and the module's `--durations=0` output.
  - Observed evidence:
    ```text
    $ aw commit j77z5h -- tests/test_render_residual_helpers.py
    aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/j77z5h but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/j77z5h's package (set AW_NO_REEXEC=1 to disable)
    aw commit: committed 1 path(s): d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66

    $ git show --stat d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66
    commit d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66 (HEAD -> aw/lane/j77z5h)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 23 22:57:09 2026 -0400

        work(j77z5h): Restore behavioral coverage for residual render and citation helpers

        AW-Run: run-20261024T014601Z-3125888
        AW-Item: j77z5h
        AW-Runner: aw agy run

     tests/test_render_residual_helpers.py | 158 ++++++++++++++++++++++++++++++++++
     1 file changed, 158 insertions(+)

    $ python3 -m pytest
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 104.31s exceeded budget of 30.00s.
    Host 1-minute load average: 16.22 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    Top 10 slowest core tests:
       1.  11.23s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       2.  10.58s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       3.   8.31s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       4.   7.77s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       5.   6.60s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       6.   6.39s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       7.   5.18s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
       8.   4.62s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
       9.   4.43s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
      10.   4.32s  tests/test_ipd_lint.py::ReadinessAttestationTests::test_every_readiness_carrying_plan_in_the_tree_is_attested
    ===========================================================================================
    ...
    1727 passed, 11 warnings in 104.30s (0:01:44)
    Exit status: 0 (no failed or error). None of the slowest tests are from tests/test_render_residual_helpers.py.

    $ python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_render_residual_helpers.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=4259758881
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/j77z5h
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 5 items

    tests/test_render_residual_helpers.py .....                              [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== slowest durations ===============================

    (15 durations < 0.005s hidden.  Use -vv to show these durations.)
    ============================== 5 passed in 0.38s ===============================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the five JSON outputs produced by `tools/mutation_probe.py` (E-06), each with `head` equal to the E-05 commit or later, a selection containing `-m core tests/test_render_residual_helpers.py`, `verdict: killed` and `baseline_failing: 0`; paste `git diff --stat <E-05 parent>..HEAD -- agent_workflows/` showing no change.
  - Observed evidence:
    ```json
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66", "mutant_failing": 1, "newly_failing": ["tests.test_render_residual_helpers.RunnerStatusAndGlyphTests::test_palette_status_ready_differs_from_done_and_unmapped_degrades"], "newly_failing_total": 1, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_render_residual_helpers.py"], "target": "agent_workflows/render_stream.py::Palette.status", "verdict": "killed", "wall_s": 12.01}
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66", "mutant_failing": 1, "newly_failing": ["tests.test_render_residual_helpers.RunnerStatusAndGlyphTests::test_status_glyph_char_unicode_and_ascii"], "newly_failing_total": 1, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_render_residual_helpers.py"], "target": "agent_workflows/render_stream.py::_status_glyph_char", "verdict": "killed", "wall_s": 9.5}
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66", "mutant_failing": 1, "newly_failing": ["tests.test_render_residual_helpers.GateRefDisplayTests::test_gate_ref_display_compact_and_verbatim"], "newly_failing_total": 1, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_render_residual_helpers.py"], "target": "agent_workflows/attention.py::_gate_ref_display", "verdict": "killed", "wall_s": 13.46}
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66", "mutant_failing": 1, "newly_failing": ["tests.test_render_residual_helpers.CiteReviewEntryTests::test_cite_review_entry_derives_citation_without_verdict_token"], "newly_failing_total": 1, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_render_residual_helpers.py"], "target": "agent_workflows/plan_readiness.py::cite_review_entry", "verdict": "killed", "wall_s": 11.37}
    {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "d5f72aa8f00a94a3bfd01d3adcb24d1b5c655f66", "mutant_failing": 1, "newly_failing": ["tests.test_render_residual_helpers.SpecImpactAnnouncementTests::test_format_spec_impact_announcement_empty_and_populated"], "newly_failing_total": 1, "operator": "return-none", "reason": null, "selection": ["-o", "addopts=", "-q", "-p", "no:randomly", "-n0", "-m", "core", "tests/test_render_residual_helpers.py"], "target": "agent_workflows/render_stream.py::format_spec_impact_announcement", "verdict": "killed", "wall_s": 9.37}
    ```
    And:
    ```text
    $ git diff --stat 834e41a5cabd449803129d4aade33a5a4cac5ce4..HEAD -- agent_workflows/
    (empty)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract: all open questions are resolved. SCOPE FENCE: `tests/test_render_residual_helpers.py` only; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Commit through `aw commit j77z5h -- tests/test_render_residual_helpers.py`, never push, never `git add -A`, and paste actual runner output for every `V-*`. You MUST paste the ACTUAL runner and probe output; never claim a test passed or a mutant was killed that you did not run. No production file under `agent_workflows/` may change. Scope reconciliation: `aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path. Lifecycle: after every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize j77z5h` itself.
