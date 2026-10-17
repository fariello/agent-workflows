# IPD: Restore behavioral test coverage for clean_delta adapter manifest, purity, conversion, drift, repair and uninstall

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `otc788` (Set `trimgap`, group 13 of the `b1mx2w` filing plan `z2xs98`) records that 9 production keys in `agent_workflows/clean_delta.py` (160 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their only behavioral tests lived in `tests/test_clean_delta.py`, which the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted outright (`hpjj44` records it as `pass-exclusive`: 24 tests, 15 functions with exclusive reach, 239 exclusive lines). The surviving callers (`tests/test_awphysical_tools.py`, `tests/test_system_root_accessor.py`) reach only `CleanDeltaManager.install_clean_delta`, `snapshot_target_state`, `compute_target_delta`, `validate_host_evidence` and `resolve_system_provider`. So a mutation that, for example, made `uninstall_adapters` ignore `host_filter` (deleting another host's adapters), made the `prune_block` path drop a user's own `AGENTS.md` prose, or made `convert_legacy_adapters` rewrite a user's own command file, would pass the routine suite.
- Scope: Restore `tests/test_clean_delta.py` from `19313eed^:tests/test_clean_delta.py` as a core-tier behavioral module that drives the 9 keys through their public call surfaces and asserts on return values, written files and file contents. The 9 keys: `convert_legacy_adapters`, `uninstall_adapters`, `detect_adapter_drift`, `repair_adapters`, `verify_adapter_purity`, `resolve_adapter_reference`, `_compute_sha256` (reached through `build_default_adapter_manifest` and `detect_adapter_drift`), `AdapterManifest.get` (reached through `repair_adapters`), `build_default_adapter_manifest`. EXCLUDES any change to `agent_workflows/clean_delta.py` or any other production file, and EXCLUDES the 6 already-reached clean_delta keys, which the restored file will also exercise incidentally but which are not this item's gap.
- Scope-Paths: tests/test_clean_delta.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: otc788
- Set: trimgap
- Order: 13
- Highest E allocated: 05
- Author: opencode
- Id: dwjfu4

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `otc788`. Ran the deleted `19313eed^:tests/test_clean_delta.py` verbatim against HEAD `7dbf402bc` before writing any expected outcome (Finding F-03: 24 passed in 1.27s), so the restore is known to apply cleanly and the expectations below are observed, not inferred.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 9 `unguarded-unreached` clean_delta keys from backlog `otc788` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its outputs and file-system side effects. Done means a mutation that breaks any of these behaviors (manifest invariants, portable references, purity refusal, foreign-content-preserving conversion and its idempotence, drift detection, repair, host-isolated uninstall, block pruning) turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the module into the core tier

- [ ] E-01 Restore the file with `git show 19313eed^:tests/test_clean_delta.py > tests/test_clean_delta.py`, then add `import pytest` and a module-level `pytestmark = pytest.mark.core` (the pattern `tests/test_backlog.py` uses for `unittest.TestCase` classes) so the bare core-tier gate collects it. Extend the module docstring with one paragraph naming backlog `otc788`, findings `b1mx2w` and `hpjj44`, and the trim commit `19313eed` it was restored from. Remove the two stale line-number citations `clean_delta.py:338` and `clean_delta.py:342` in `PortableReferenceTests.test_the_external_invocation_strips_an_absolute_path`'s docstring, replacing them with the symbol `resolve_adapter_reference` and the quoted `lstrip("/")`, since offsets have rotted. Make no other content change.
  - Depends on: none
  - Expected outcome: the file exists, imports cleanly, and `python3 -m pytest --collect-only -q` (bare, core-filtered) lists its 24 tests.
  - Execution state: pending

### Task group 2: confirm each behavior group is guarding its keys

- [ ] E-02 Run the restored module alone (`python3 -m pytest tests/test_clean_delta.py -o addopts="" -v`) and confirm all 24 tests pass, covering `AdapterManifestTests` and `PortableReferenceTests` (keys `build_default_adapter_manifest`, `_compute_sha256`, `resolve_adapter_reference`).
  - Depends on: E-01
  - Expected outcome: 24 passed, no skips.
  - Execution state: pending

- [ ] E-03 Mutation spot-check, scratch edits to `agent_workflows/clean_delta.py` never committed, one at a time, rerunning the module after each and reverting before the next: (a) `verify_adapter_purity` returns True as its first statement; (b) `convert_legacy_adapters` skips the `"<!-- BEGIN AGENT-WORKFLOWS -->" in text` branch (treat every `AGENTS.md` as foreign); (c) `resolve_adapter_reference` returns `canonical_identity` unconditionally.
  - Depends on: E-02
  - Expected outcome: each mutation turns at least one named test red (respectively `AdapterPurityTests`, `LegacyConversionTests`, `PortableReferenceTests`).
  - Execution state: pending

- [ ] E-04 Mutation spot-check, same discipline: (a) `detect_adapter_drift` appends every existing path to `clean` without hashing; (b) `repair_adapters` skips the `MANAGED_SECTION_BLOCK` branch and writes the shim body for every entry; (c) `uninstall_adapters` ignores `host_filter`; (d) `build_default_adapter_manifest` sets `uninstall_behavior="remove"` on the `AGENTS.md` entry; (e) `AdapterManifest.get` returns None. Then confirm `git diff agent_workflows/` is empty.
  - Depends on: E-03
  - Expected outcome: each mutation turns at least one `DriftRepairUninstallTests` or `AdapterManifestTests` test red; the production diff is empty afterwards.
  - Execution state: pending

### Task group 3: core-tier fit

- [ ] E-05 Run bare `python3 -m pytest` and confirm it passes with the new module included and the core-tier wall-time budget (enforced by `conftest.pytest_sessionfinish`, IPD `hguae9`) not exceeded.
  - Depends on: E-01
  - Expected outcome: the summary line reports passed with no budget failure.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). The restored file calls the module's functions and asserts on returned dicts and files on disk; it reads no production source. Its one set-equality assertion (`ADVERTISED_CLEAN_DELTA_CLAIMS == D113_EVIDENCE_PAIRS`) compares runtime values, and its docstring explains why that is a content check and not a count pin.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget, so the restored module must carry `pytestmark = pytest.mark.core`. Module-level `pytestmark` applies to `unittest.TestCase` classes, as `tests/test_backlog.py` already relies on.
- The restored fixture sets `AW_HOME` in `os.environ` in `setUp` and restores it in `tearDown`; under `pytest-xdist` each worker is its own process, so this does not leak across workers.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows for `agent_workflows/clean_delta.py::*` | Exactly 9 clean_delta keys carry `unreached` / `unguarded-unreached`: the 9 named in Scope. The other 6 (`CleanDeltaManager.install_clean_delta`, `CleanDeltaManager.__init__`, `snapshot_target_state`, `compute_target_delta`, `resolve_system_provider`, `validate_host_evidence`) are `reached` by `tests/test_awphysical_tools.py` or `tests/test_system_root_accessor.py`. |
| F-02 | `hpjj44` row for `tests/test_clean_delta.py` | The deleted file was `pass-exclusive`: 24 tests, sole reacher of 15 clean_delta functions (239 exclusive lines), including all 9 keys here. |
| F-03 | `git show 19313eed^:tests/test_clean_delta.py` written to a scratch test path and run at HEAD `7dbf402bc` with `-o addopts=""` | `24 passed in 1.27s`. The module's imports (`AdapterKind`, `AdapterPurityError`, `CleanDeltaManager`, `UnsupportedHostError`, the 9 functions, `register_or_update_project`, `DeliveryMode`, `RecordsBackend`) all still resolve, and every expectation still holds against current behavior. Restoration needs no rewrite. |
| F-04 | `agent_workflows.clean_delta` source read | `_compute_sha256` has no public caller other than `build_default_adapter_manifest` and `detect_adapter_drift`; `AdapterManifest.get` is called by `repair_adapters`. Both private-ish keys are therefore reached through the restored public-surface tests, which is why E-04 mutates them directly to prove the reach is load-bearing. |

## Proposed changes (ordered, validatable)

1. E-01 restores `tests/test_clean_delta.py` with the core marker and a provenance note.
2. E-02 runs it in isolation.
3. E-03 and E-04 prove each key is guarded by a scratch mutation that turns a test red.
4. E-05 confirms it fits the core tier.

## Deferred / out of scope (with reason)

- The 6 already-reached clean_delta keys are not this item's gap; the restored module exercises them incidentally, and no further work is owed for them.
  - Carrier-Declined: they are `reached` at baseline per `b1mx2w`, so no reach gap exists to carry.
- Converting the restored `unittest.TestCase` classes to pytest-style functions is out of scope: it would rewrite tests that pass verbatim (F-03) for no behavioral gain.
  - Carrier-Declined: style-only, no defect or gap owed.

## Scope check

- Over-scope: none. One restored test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none for the 9 named keys.

## Required tests / validation

- `python3 -m pytest tests/test_clean_delta.py -o addopts="" -v` passes, with the per-test list pasted (24 tests).
- Bare `python3 -m pytest` passes (core tier, including the restored module, within the 30s budget), with the summary line pasted.
- Mutation spot-checks of E-03 and E-04: paste the failing test name and assertion for each of the 8 scratch mutations, then an empty `git diff agent_workflows/`.

## Spec / documentation sync

N/A: this plan restores tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the deleted file verbatim, or write a new module as sibling trimgap plans did?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: restore verbatim under its original name. The deleted file passes unmodified at HEAD (F-03), reaches all 9 keys (F-02), and its tests are already behavioral and named for properties. Sibling plans (for example `33f8tn`) wrote new modules because their source tests were scattered across larger deleted files; here the deleted file is exactly this module's suite, and no current file named `tests/test_clean_delta.py` exists to collide with.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat` showing only `tests/test_clean_delta.py` added; paste `git diff --no-index <(git show 19313eed^:tests/test_clean_delta.py) tests/test_clean_delta.py` (or equivalent) showing only the marker, import, provenance paragraph and the two line-number citation edits; paste `python3 -m pytest --collect-only -q | rg -c test_clean_delta` reporting 24.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing all 24 tests as PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, for each of the 3 scratch mutations, the failing test id and assertion message from the rerun.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste, for each of the 5 scratch mutations, the failing test id and assertion message, then the empty output of `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the bare `python3 -m pytest` summary line showing passed and no core-tier budget failure.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_clean_delta.py` through `aw commit <plan> -- tests/test_clean_delta.py`; never push. Mutation spot-checks are scratch edits to `agent_workflows/clean_delta.py` that must be reverted before commit and must not appear in the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
