# IPD: Lock record_history rename-ledger mutation coverage into the core tier

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `hrz4cv` (Set `trimgap`, group 9 of the `wo21z5` `## Filing plan`) carries three keys of `agent_workflows/record_history.py` that the `wo21z5` budget probe never ran (`budget-exhausted`): `_endpoint_id6` (`return-none`, control `tests/test_artifact_rename.py`), `append_rename` (`raise`, control `tests/test_rename_ledger.py`) and `record_rename` (`raise`, control `tests/test_rename_ledger.py`). The remedy shape is "probe then restore". Probing at authoring HEAD `303cd2fd1` (F-01..F-04) shows that all three mutants are already KILLED by existing behavioral tests in `tests/test_rename_ledger.py`, so no deleted test needs restoring. The remaining gap is tier membership: `_endpoint_id6 -> None` SURVIVES the whole routine core tier (`-m core tests/`), because none of its killing tests is `core`-marked. A rename that silently files its ledger record under a synthetic key instead of the new id6 would therefore pass the merge gate.
- Scope: (a) record, from the authoring probes and an execution-HEAD re-probe, that `append_rename` and `record_rename` are already guarded by the core tier and owe no restored tests; (b) add `@pytest.mark.core` to the two fast unit tests `RecordRenameCaseTests.test_case1_id6_to_id6` and `RecordRenameCaseTests.test_case2_id6less_to_id6_keys_on_new_id6` in `tests/test_rename_ledger.py`, which each kill both the `_endpoint_id6` `return-none` mutant and the `record_rename` `raise` mutant on their own; (c) re-probe under `-m core` to prove the routine gate now kills them. EXCLUDES any production-code change; EXCLUDES writing new tests or restoring tests from `19313eed^` (the existing tests already kill every mutant); EXCLUDES other `record_history.py` keys not in this item; EXCLUDES changes to `tests/test_artifact_rename.py` (its tests do not kill the `_endpoint_id6` mutant, F-01, so core-marking them would add no protection).
- Scope-Paths: tests/test_rename_ledger.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: hrz4cv
- Set: trimgap
- Order: 27
- Highest E allocated: 04
- Author: opencode
- Id: r495ec

## Workflow history

- 2026-10-23 to-review (opencode): authored from backlog `hrz4cv`. Probed all three keys at HEAD `303cd2fd1` against the control files, the narrowed core subset, and the whole core tier. Every mutant is killed by existing tests; only `_endpoint_id6` survives the core tier. The plan is a core-marking remedy plus disposition records, the same shape as sibling `di5puw`.
- 2026-10-23 draft (opencode): created.

## Goal

Close every `hrz4cv` key with a recorded, probe-backed disposition, and make the routine core-tier gate kill the `_endpoint_id6` `return-none` mutant (and, inside the control file, the `record_rename` `raise` mutant) by core-marking two existing behavioral tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: disposition of already-guarded keys

- [ ] E-01 At execution HEAD, run `python3 tools/mutation_probe.py --op raise agent_workflows/record_history.py::append_rename -- -o addopts= -q -p no:randomly -m core tests/test_rename_ledger.py` and record in Findings that `append_rename` is guarded by the core tier and owes no restored tests. If the verdict is `survived` (meaning the existing core-marked `test_synthetic_key_only_via_case3_path` changed), record it as a DEFERRED gap and file a new backlog item rather than widening this plan.
  - Depends on: none
  - Expected outcome: `verdict: killed`, `mutant_failing` >= 1; disposition line written in Findings.
  - Execution state: pending

### Task group 2: lock _endpoint_id6 and record_rename into the core tier

- [ ] E-02 Add `@pytest.mark.core` to `RecordRenameCaseTests.test_case1_id6_to_id6` in `tests/test_rename_ledger.py`. The file already imports `pytest` and already uses method-level `@pytest.mark.core` (on `test_synthetic_key_only_via_case3_path` and `test_synthetic_key_deterministic_derivation`). Make no other change.
  - Depends on: none
  - Expected outcome: `git diff tests/test_rename_ledger.py` shows one added decorator line above `def test_case1_id6_to_id6`.
  - Execution state: pending

- [ ] E-03 Add `@pytest.mark.core` to `RecordRenameCaseTests.test_case2_id6less_to_id6_keys_on_new_id6` in `tests/test_rename_ledger.py`. Make no other change.
  - Depends on: none
  - Expected outcome: `git diff tests/test_rename_ledger.py` shows one added decorator line above `def test_case2_id6less_to_id6_keys_on_new_id6`.
  - Execution state: pending

- [ ] E-04 Re-run `python3 tools/mutation_probe.py --op return-none agent_workflows/record_history.py::_endpoint_id6 -- -o addopts= -q -p no:randomly -m core tests/test_rename_ledger.py` and `python3 tools/mutation_probe.py --op raise agent_workflows/record_history.py::record_rename -- -o addopts= -q -p no:randomly -m core tests/test_rename_ledger.py`, then run the bare routine gate `python3 -m pytest` to confirm the core tier still passes within its 30s budget. `tools/mutation_probe.py` mutates in its own isolated worktree, so production code in the checkout is never modified.
  - Depends on: E-02, E-03
  - Expected outcome: both probes print `verdict: killed` with `newly_failing` naming both `test_case1_id6_to_id6` and `test_case2_id6less_to_id6_keys_on_new_id6`; the bare gate summary shows no failures and no budget breach.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): both tests marked here call `record_history.record_rename` on a temp repo and assert on what `read_renames_for` returns (record count, `from_name`, `key_kind`); neither reads source.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only items with a `core` marker (`conftest.pytest_collection_modifyitems`, "Core test tier selection", IPD `hguae9`) and enforces a 30s wall budget. Marking is per test via `@pytest.mark.core` (already used twice in `tests/test_rename_ledger.py`).
- Probe tool: `tools/mutation_probe.py` (`--op {return-none,return-true,return-false,negate-return,raise}`, pytest selection after `--`) is the tool `wo21z5` used, so results are directly comparable.
- Sibling precedent: plan `di5puw` (same Set, Order 26) remedies an analogous tier-membership gap by core-marking existing killing tests and re-probing under `-m core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All probes run at HEAD `303cd2fd1` with `tools/mutation_probe.py`, baseline_failing 0 in every case.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `--op return-none record_history.py::_endpoint_id6 -- ... tests/test_artifact_rename.py`: `verdict: survived`, `mutant_failing: 0` (also `survived` with `-m core`); same op over `tests/test_rename_ledger.py` (no `-m core`): `verdict: killed`, `mutant_failing: 4` (`CliEmissionTests::test_applied_plan_rename_appends_one_record`, `RecordRenameCaseTests::test_case1_id6_to_id6`, `::test_case2_id6less_to_id6_keys_on_new_id6`, `::test_multi_rename_history_accumulates`); same op with `-n 6 -m core tests/` (whole core tier): `verdict: survived`, `mutant_failing: 0`, `wall_s: 434.22` | The `wo21z5` control file for `_endpoint_id6` does not kill it at all; `tests/test_rename_ledger.py` does, but only in the thorough tier. The routine merge gate cannot detect `_endpoint_id6` returning None, which would make `record_rename` misfile Case-1/Case-2 renames under a synthetic key. |
| F-02 | `--op raise record_history.py::append_rename -- ... tests/test_rename_ledger.py`: `killed`, `mutant_failing: 9`; with `-m core`: `killed`, `mutant_failing: 1` (`AppendRenameUnitTests::test_synthetic_key_only_via_case3_path`, already `@pytest.mark.core`) | `append_rename` is already guarded by the core tier. No restoration or marking owed. |
| F-03 | `--op raise record_history.py::record_rename -- ... tests/test_rename_ledger.py`: `killed`, `mutant_failing: 7`; with `-m core` on that file: `survived`, `mutant_failing: 0`; with `-n 6 -m core tests/`: `killed`, `mutant_failing: 4` (`test_artifact_rename::TestArtifactRename::test_rename_roadmaps` and three `test_spec_id6_filenames` tests), `wall_s: 414.58` | `record_rename` is already guarded by the whole core tier through CLI rename tests, so no restoration is owed. Its own unit-test file has no core-marked killer, which E-02/E-03 also fix as a side effect. |
| F-04 | Probes of each op over only `RecordRenameCaseTests::test_case1_id6_to_id6` and only `::test_case2_id6less_to_id6_keys_on_new_id6`: `_endpoint_id6 return-none` killed (`mutant_failing: 1`) and `record_rename raise` killed (`mutant_failing: 1`) for each test; the whole `RecordRenameCaseTests` class runs `6 passed in 0.23s`, with no call above 0.03s | Each of the two chosen tests kills both mutants by itself, so marking both gives redundancy at negligible core-budget cost. |
| F-05 | `git show 19313eed^:tests/test_rename_ledger.py` test names (`test_write_and_read_back` through `test_dry_run_appends_nothing`) all exist in today's `tests/test_rename_ledger.py` | No deleted rename-ledger test remains to mine; the "restore" half of the remedy has nothing to restore. |

## Proposed changes (ordered, validatable)

1. E-01 re-confirms and records `append_rename` as already core-guarded (F-02); `record_rename`'s disposition is recorded from F-03 and re-proven in E-04.
2. E-02 and E-03 each add one `@pytest.mark.core` decorator to an existing behavioral test in `tests/test_rename_ledger.py`.
3. E-04 re-probes `_endpoint_id6` and `record_rename` under `-m core` (expected `killed`) and runs the bare gate.

## Deferred / out of scope (with reason)

- Core-marking `CliEmissionTests::test_applied_plan_rename_appends_one_record` or `::test_multi_rename_history_accumulates`.
  - Carrier-Declined: no work is owed; the two chosen unit tests already kill both mutants (F-04), and the CLI emission test spawns a subprocess, so marking it would spend core budget redundantly.
- Restoring tests from `19313eed^` for this module.
  - Carrier-Declined: no work is owed; every pre-deletion rename-ledger test is present at HEAD (F-05), and existing tests kill every mutant (F-01..F-03).
- Changing `tests/test_artifact_rename.py`.
  - Carrier-Declined: no work is owed; it does not kill the `_endpoint_id6` mutant (F-01), and `wo21z5` naming it as the control file was a queue-assignment choice, not a coverage claim.

## Scope check

- Over-scope: none. Two decorator additions in one test file; no production change.
- Under-scope: none. All three backlog keys get a disposition: `append_rename` by E-01, `_endpoint_id6` and `record_rename` by E-02 through E-04.

## Required tests / validation

- E-01 probe output pasted (`verdict: killed` under `-m core`).
- `git diff tests/test_rename_ledger.py` pasted, showing only the two decorator additions.
- `python3 -m pytest -o addopts= -q -p no:randomly -m core --collect-only tests/test_rename_ledger.py` output listing both newly marked tests.
- Both E-04 `tools/mutation_probe.py` outputs pasted in full (`head`/`target`/`operator`/`selection` with `-m core`/`verdict`/`newly_failing`).
- Bare `python3 -m pytest` summary line pasted.
- `git diff --stat agent_workflows/` empty.

## Spec / documentation sync

N/A: test tier markers only; no behavior, CLI surface, or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Does "probe then restore" require restoring tests when probing finds no gap?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. The probe step (F-01..F-04) shows every mutant is already killed by tests present at HEAD, and F-05 shows nothing from `19313eed^` is missing. The only real residual gap is core-tier membership for `_endpoint_id6` (F-01), which E-02 through E-04 close with existing tests, matching sibling plan `di5puw`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the full E-01 `tools/mutation_probe.py` output (produced by the tool in E-01) showing `selection:` containing `-m core`, `verdict: killed`, and `newly_failing` naming `test_synthetic_key_only_via_case3_path`; paste the Findings disposition line for `append_rename`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff tests/test_rename_ledger.py` showing an added `@pytest.mark.core` line directly above `def test_case1_id6_to_id6`, and paste `python3 -m pytest -o addopts= -q -p no:randomly -m core --collect-only tests/test_rename_ledger.py` output listing `RecordRenameCaseTests::test_case1_id6_to_id6`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff tests/test_rename_ledger.py` showing an added `@pytest.mark.core` line directly above `def test_case2_id6less_to_id6_keys_on_new_id6`, and paste the same `--collect-only -m core` output listing `RecordRenameCaseTests::test_case2_id6less_to_id6_keys_on_new_id6`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the full output of both E-04 `tools/mutation_probe.py` runs (produced by the tool itself in E-04), each showing a `selection:` containing `-m core` and `verdict: killed` with both newly marked tests in `newly_failing`; paste the bare `python3 -m pytest` summary line showing `passed` with no `failed` and no core-budget failure; paste `git diff --stat agent_workflows/` showing no change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Commit only `tests/test_rename_ledger.py` and this plan through `aw commit r495ec -- <paths>`; never push. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
