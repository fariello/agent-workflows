# IPD: Resolve probe applicability for run_analytics_spa keys and lock scan_for_network_references into the core tier

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `aaud70` (Set `trimgap`, group 3 of the `wo21z5` `## Filing plan`) carries five keys of `agent_workflows/run_analytics_spa.py` that the `wo21z5` budget probe recorded `unprovable` with reason `target file not found`: `_render_findings`, `_render_pricing`, `_render_refusals`, `refusal_from_result`, `scan_for_network_references`. The cause is not a probe-tool limitation: commit `bf5057b69` (2026-10-17 18:16, two minutes after the `wo21z5` baseline `f3afece9`) deleted `run_analytics_spa.py` entirely, retiring the classic report and keeping only its HTML-safety helpers as `agent_workflows/run_analytics_html.py` (F-01). Four keys therefore no longer exist and owe no coverage. The fifth, `scan_for_network_references`, moved to `run_analytics_html.scan_for_network_references` and is still called in production by `run_dashboard` (`violations = spa.scan_for_network_references(doc)`). Re-probing it at authoring HEAD `ce72322b` shows its `return-none` and `raise` mutants are KILLED by the full non-slow selection but SURVIVE the whole routine core tier, because none of its three killing tests is `core`-marked (F-02, F-03). The routine merge gate therefore cannot detect a broken offline-reference scanner.
- Scope: (a) record the disposition of the four deleted keys as "no longer exists; no coverage owed"; (b) add `@pytest.mark.core` to the two fast tests that kill the `scan_for_network_references` mutants (`OfflineReportTests.test_the_offline_harness_FAILS_when_a_network_reference_is_introduced` in `tests/test_run_analytics_e2e.py` and `RenderTests.test_offline_and_escaped` in `tests/test_run_dashboard.py`); (c) re-probe under `-m core` to prove the mutants are now killed by the routine gate. EXCLUDES any production-code change; EXCLUDES writing new tests (existing behavioral tests already kill the mutants); EXCLUDES other `run_analytics_html.py` keys (`escape_text`, `escape_attribute`, `escape_json_for_script`, `sanitize_control_characters` were not in this item); EXCLUDES restoring tests for deleted code from `19313eed^`.
- Scope-Paths: tests/test_run_analytics_e2e.py, tests/test_run_dashboard.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: aaud70
- Set: trimgap
- Order: 26
- Highest E allocated: 04
- Author: opencode
- Id: di5puw

## Workflow history

- 2026-10-23 to-review (opencode): authored from backlog `aaud70`. Traced the `target file not found` verdict to the deletion of `run_analytics_spa.py` in `bf5057b69`; located the surviving key in `run_analytics_html`; probed it at HEAD `ce72322b` (survives `-m core tests/`, killed by full selection and by the two named tests alone). Plan is a core-marking remedy plus a disposition record.
- 2026-10-23 draft (opencode): created.

## Goal

Close every `aaud70` key with a recorded disposition: the four keys deleted with `run_analytics_spa.py` are recorded as owing nothing, and `run_analytics_html.scan_for_network_references` is proven, by pasted mutation-probe output under `-m core`, to be guarded by the routine core-tier gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: disposition of deleted keys

- [ ] E-01 Confirm at execution HEAD that `agent_workflows/run_analytics_spa.py` does not exist and that none of `_render_findings`, `_render_pricing`, `_render_refusals`, `refusal_from_result` is defined anywhere under `agent_workflows/` (`git ls-files agent_workflows/run_analytics_spa.py` empty; `grep -rnE "def (_render_findings|_render_pricing|_render_refusals|refusal_from_result)\b" agent_workflows/` empty). Record in Findings "four keys deleted by `bf5057b69`; no coverage owed". If any of them has been reintroduced, record it as a DEFERRED gap for a new backlog item and do not restore tests in this plan.
  - Depends on: none
  - Expected outcome: both commands print nothing; disposition recorded in Findings.
  - Execution state: pending

### Task group 2: lock scan_for_network_references into the core tier

- [ ] E-02 Add `@pytest.mark.core` to `OfflineReportTests.test_the_offline_harness_FAILS_when_a_network_reference_is_introduced` in `tests/test_run_analytics_e2e.py` (the file already imports `pytest` and already uses method-level `@pytest.mark.core` on `FixtureCorpusTests`). Make no other change to the file.
  - Depends on: none
  - Expected outcome: `git diff tests/test_run_analytics_e2e.py` shows exactly one added decorator line.
  - Execution state: pending

- [ ] E-03 Add `@pytest.mark.core` to `RenderTests.test_offline_and_escaped` in `tests/test_run_dashboard.py`, adding `import pytest` only if the file does not already import it. Make no other change to the file.
  - Depends on: none
  - Expected outcome: `git diff tests/test_run_dashboard.py` shows the decorator line (and at most an `import pytest` line).
  - Execution state: pending

- [ ] E-04 Re-run `python3 tools/mutation_probe.py --op <op> agent_workflows/run_analytics_html.py::scan_for_network_references -- -o addopts= -q -p no:randomly -m core tests/test_run_analytics_e2e.py tests/test_run_dashboard.py` for `<op>` in `return-none` and `raise`, then run the bare routine gate `python3 -m pytest` to confirm the core tier still passes within its 30s budget. `tools/mutation_probe.py` mutates in its own isolated worktree, so production code in the checkout is never modified.
  - Depends on: E-02, E-03
  - Expected outcome: both probes print `verdict: killed` with `mutant_failing: 2` naming the two tests; the bare gate summary shows no failures and no budget breach.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): both tests marked here already call `scan_for_network_references` on a rendered document and assert on its returned list; no test reads source.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only items with a `core` marker (`conftest.pytest_collection_modifyitems`, "Core test tier selection", IPD `hguae9`) and enforces a 30s wall budget. Marking is per test via `@pytest.mark.core` (41 method-level uses in `tests/`) or per module via `pytestmark`.
- Probe tool: `tools/mutation_probe.py` (`--op {return-none,return-true,return-false,negate-return,raise}`, pytest selection after `--`) is the tool `wo21z5` used, so results are directly comparable.
- Sibling precedent: plan `92tzo6` (same Set, Order 24) handles an analogous stale `wo21z5` verdict by re-probing at execution HEAD.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Budget probe results` rows for the five keys (`invalid`, `unprovable`, `target file not found`); `git log -1 bf5057b69` (2026-10-17 18:16:22, "remove classic report.html (run_analytics_spa + assets), keep its HTML-safety helpers as run_analytics_html"); `wo21z5` baseline `f3afece9` dated 2026-10-17 18:14:47 and is an ancestor of `bf5057b69`; `ls agent_workflows/run_analytics_spa.py` fails at HEAD `ce72322b`; `git show bf5057b69^:agent_workflows/run_analytics_spa.py` defines all five keys | The `unprovable` verdict is an artifact of the module being deleted while the probe ran, not of the probe tool. `_render_findings`, `_render_pricing`, `_render_refusals`, `refusal_from_result` were removed with the classic report and no definition exists under `agent_workflows/`. |
| F-02 | `agent_workflows/run_analytics_html.scan_for_network_references` exists; `run_dashboard` calls `spa.scan_for_network_references(doc)`; probe `--op return-none ... -m core tests/test_run_analytics_e2e.py tests/test_run_dashboard.py` at `ce72322b`: `verdict: survived`, `mutant_failing: 0`; same with `--op raise`: `survived`; same `return-none` with `-n 6 -m core tests/` (whole core tier): `verdict: survived`, `mutant_failing: 0`, `wall_s: 244.53` | The surviving key is unguarded by the routine merge gate. Only 1 of 51 tests in the two control files is core-selected (`FixtureCorpusTests::test_the_corpus_carries_all_four_generations_including_both_legacy_ones`). |
| F-03 | Probe `--op return-none` without `-m core` over the two files: `verdict: killed`, `mutant_failing: 3` (`OfflineReportTests::test_the_bundle_opens_from_a_file_url_with_sockets_denied`, `OfflineReportTests::test_the_offline_harness_FAILS_when_a_network_reference_is_introduced`, `RenderTests::test_offline_and_escaped`); probe of both ops over only the two E-02/E-03 tests: `verdict: killed`, `mutant_failing: 2` each | Behavioral coverage already exists in the thorough tier; the gap is tier membership only. The two chosen tests kill both operators by themselves; `test_the_offline_harness_FAILS...` ran in 1.84s total (call under 5ms) and `test_offline_and_escaped` in 1.04s total, so core-marking them costs negligible budget. |

## Proposed changes (ordered, validatable)

1. E-01 records the four deleted keys as owing no coverage.
2. E-02 and E-03 each add one `@pytest.mark.core` decorator to an existing behavioral test.
3. E-04 re-probes under `-m core` (expected `killed`) and runs the bare gate.

## Deferred / out of scope (with reason)

- Core-marking `OfflineReportTests::test_the_bundle_opens_from_a_file_url_with_sockets_denied`.
  - Carrier-Declined: no work is owed; it is the heavier socket-denial bundle test and the two chosen tests already kill both operators (F-03), so adding it would spend core budget redundantly.
- Restoring deleted tests from `19313eed^` for the four removed keys.
  - Carrier-Declined: no work is owed; the production code they would cover no longer exists (F-01).

## Scope check

- Over-scope: none. Two decorator additions in two test files; no production change.
- Under-scope: none. All five backlog keys get a disposition: four by E-01, one by E-02 through E-04.

## Required tests / validation

- E-01 command outputs (both empty) pasted.
- `git diff tests/test_run_analytics_e2e.py tests/test_run_dashboard.py` pasted, showing only decorator (and possibly `import pytest`) additions.
- Both E-04 `tools/mutation_probe.py` outputs pasted in full (`head`/`target`/`operator`/`selection` with `-m core`/`verdict`/`mutant_failing`).
- Bare `python3 -m pytest` summary line pasted.
- `git diff --stat agent_workflows/` empty.

## Spec / documentation sync

N/A: test tier markers only; no behavior, CLI surface, or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Is "investigate probe" satisfied by tier-marking rather than a probe-tool change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: yes. The investigation (F-01) shows the probe tool worked correctly and reported a missing target; nothing in `tools/mutation_probe.py` needs to change. The only real residual gap is that the relocated key is unguarded by the core tier (F-02), which E-02 through E-04 close with existing tests.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the two E-01 commands with their (empty) output and the Findings line recording "four keys deleted by `bf5057b69`; no coverage owed".
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff tests/test_run_analytics_e2e.py` showing exactly one added `@pytest.mark.core` line above `test_the_offline_harness_FAILS_when_a_network_reference_is_introduced`, and paste `python3 -m pytest -o addopts= -q -p no:randomly -m core --collect-only tests/test_run_analytics_e2e.py` output listing that test id.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff tests/test_run_dashboard.py` showing the added `@pytest.mark.core` line above `test_offline_and_escaped` (plus at most `import pytest`), and paste `python3 -m pytest -o addopts= -q -p no:randomly -m core --collect-only tests/test_run_dashboard.py` output listing that test id.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full output of both `tools/mutation_probe.py` runs (produced by the tool itself in E-04), each showing a `selection:` containing `-m core` and `verdict: killed`; paste the bare `python3 -m pytest` summary line showing `passed` with no `failed` and no core-budget failure; paste `git diff --stat agent_workflows/` showing no change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Commit only `tests/test_run_analytics_e2e.py`, `tests/test_run_dashboard.py` and this plan through `aw commit di5puw -- <paths>`; never push. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
