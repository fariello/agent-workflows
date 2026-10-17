# IPD: Restore behavioral test coverage for clean_delta adapter manifest, purity, conversion, drift, repair and uninstall

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `otc788` (Set `trimgap`, group 13 of the `b1mx2w` filing plan `z2xs98`) records that 9 production keys in `agent_workflows/clean_delta.py` (160 exclusive lines) are `unreached` by the routine non-slow test selection at baseline HEAD `86f0d88d`, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their only behavioral tests lived in `tests/test_clean_delta.py`, which the suite trim `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted outright (`hpjj44` records it as `pass-exclusive`: 24 tests, 15 functions with exclusive reach, 239 exclusive lines). The surviving callers (`tests/test_awphysical_tools.py`, `tests/test_system_root_accessor.py`) reach only `CleanDeltaManager.install_clean_delta`, `snapshot_target_state`, `compute_target_delta`, `validate_host_evidence` and `resolve_system_provider`. So a mutation that, for example, made `uninstall_adapters` ignore `host_filter` (deleting another host's adapters), made the `prune_block` path drop a user's own `AGENTS.md` prose, or made `convert_legacy_adapters` rewrite a user's own command file, would pass the routine suite.
- Scope: Restore `tests/test_clean_delta.py` from `19313eed^:tests/test_clean_delta.py` as a core-tier behavioral module that drives the 9 keys through their public call surfaces and asserts on return values, written files and file contents. The 9 keys: `convert_legacy_adapters`, `uninstall_adapters`, `detect_adapter_drift`, `repair_adapters`, `verify_adapter_purity`, `resolve_adapter_reference`, `_compute_sha256` (reached through `build_default_adapter_manifest` and `detect_adapter_drift`), `AdapterManifest.get` (reached through `repair_adapters`), `build_default_adapter_manifest`. EXCLUDES any change to `agent_workflows/clean_delta.py` or any other production file, and EXCLUDES the 6 already-reached clean_delta keys, which the restored file will also exercise incidentally but which are not this item's gap.
- Scope-Paths: tests/test_clean_delta.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: otc788
- Set: trimgap
- Order: 13
- Highest E allocated: 06
- Author: opencode
- Id: dwjfu4

## Workflow history
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005

- 2026-10-17 to-review (opencode): authored from backlog `otc788`. Ran the deleted `19313eed^:tests/test_clean_delta.py` verbatim against HEAD `7dbf402bc` before writing any expected outcome (Finding F-03: 24 passed in 1.27s), so the restore is known to apply cleanly and the expectations below are observed, not inferred.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 9 `unguarded-unreached` clean_delta keys from backlog `otc788` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its outputs and file-system side effects. Done means a mutation that breaks any of these behaviors (manifest invariants, portable references, purity refusal, foreign-content-preserving conversion and its idempotence, drift detection, repair, host-isolated uninstall, block pruning) turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the module into the core tier

- [ ] E-01 Restore the file with `git show 19313eed^:tests/test_clean_delta.py > tests/test_clean_delta.py`, then add `import pytest` and a module-level `pytestmark = pytest.mark.core` (the pattern `tests/test_backlog.py` uses for `unittest.TestCase` classes) so the bare core-tier gate collects it. Extend the module docstring with one paragraph naming backlog `otc788`, findings `b1mx2w` and `hpjj44`, and the trim commit `19313eed` it was restored from. Remove the two stale line-number citations `clean_delta.py:338` and `clean_delta.py:342` in `PortableReferenceTests.test_the_external_invocation_strips_an_absolute_path`'s docstring, replacing them with the symbol `resolve_adapter_reference` and the quoted `lstrip("/")`, since offsets have rotted. Insert `import pytest` with the other top-level imports and `pytestmark = pytest.mark.core` AFTER the last complete top-level import statement (the file imports `from agent_workflows.clean_delta import (...)` as a parenthesized multi-line statement, so "after the last import line" is unsafe). Make no other content change to the restored tests (E-06 appends new ones). Disposition rule if a restored test fails at execution HEAD (none did at authoring, F-03, nor at review, F-05): do not mark the item performed until it is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: the file exists, imports cleanly, and a bare `python3 -m pytest --collect-only -q` (core-filtered) lists every restored test in it (24 at authoring and at review; re-derive the count at execution and record it in V-01).
  - Execution state: pending

### Task group 2: confirm each behavior group is guarding its keys

- [ ] E-02 Run the restored module alone (`python3 -m pytest tests/test_clean_delta.py -o addopts="" -v`) and confirm every restored test passes, covering `AdapterManifestTests` and `PortableReferenceTests` (keys `build_default_adapter_manifest`, `_compute_sha256`, `resolve_adapter_reference`).
  - Depends on: E-01
  - Expected outcome: every collected test passed, no skips (24 at authoring; the bar is all-pass, not the count).
  - Execution state: pending

- [ ] E-03 Mutation spot-check, scratch edits to `agent_workflows/clean_delta.py` never committed, one at a time, rerunning the module after each and reverting before the next: (a) `verify_adapter_purity` returns True as its first statement; (b) `convert_legacy_adapters` skips the `"<!-- BEGIN AGENT-WORKFLOWS -->" in text` branch (treat every `AGENTS.md` as foreign); (c) `resolve_adapter_reference` returns `canonical_identity` unconditionally.
  - Depends on: E-02
  - Expected outcome: each mutation turns at least one named test red (respectively `AdapterPurityTests`, `LegacyConversionTests`, `PortableReferenceTests`).
  - Execution state: pending

- [ ] E-04 Mutation spot-check, same discipline: (a) `detect_adapter_drift` appends every existing path to `clean` without hashing (replace `if h == entry.generated_hash or entry.ownership_marker in content:` with `if True:`); (b) `repair_adapters` skips the `MANAGED_SECTION_BLOCK` branch and writes the shim body for every entry; (c) `uninstall_adapters` ignores `host_filter`; (d) `build_default_adapter_manifest` sets `uninstall_behavior="remove"` on the `AGENTS.md` entry; (e) `AdapterManifest.get` returns None; (f) `_compute_sha256` returns a constant string. Then confirm `git diff agent_workflows/` is empty.
  - Depends on: E-06
  - Expected outcome: each mutation turns at least one test red: (a) and (b) only through the E-06 tests (they SURVIVE the 24 restored tests, F-05); (c), (d), (e) through `DriftRepairUninstallTests` or `AdapterManifestTests`; (f) through `TargetDeltaTests` (it reaches `_compute_sha256` via `snapshot_target_state`, F-04). The production diff is empty afterwards.
  - Execution state: pending

- [ ] E-06 Append to `tests/test_clean_delta.py` a `DriftAndBlockRepairTests(_CleanDeltaFixture)` class (inheriting the module `core` marker) with two behavioral tests: (1) after `repair_adapters(self.target_repo, manifest=m)` on `m = self.manifest()`, overwrite `.opencode/commands/verify.md` with `"user rewrote this\n"`; assert `detect_adapter_drift(self.target_repo, m)["drifted"] == [".opencode/commands/verify.md"]`, then that a second `repair_adapters` returns exactly `[".opencode/commands/verify.md"]` and the file again contains `"<!-- aw:managed -->"` (drift is detected and only the drifted adapter is rewritten); (2) after `repair_adapters` on a fresh fixture, assert `AGENTS.md` contains `"<!-- /aw:block -->"` (repair writes the closing marker a managed block needs), and that `uninstall_adapters(self.target_repo, manifest=m, host_filter="codex")` returns `["AGENTS.md"]` and leaves no `AGENTS.md` on disk (a block-only file is pruned to nothing and removed). Both values were observed at review (F-05). Re-measure at execution HEAD before asserting; apply the E-01 disposition rule if one differs.
  - Depends on: E-02
  - Expected outcome: both new tests pass, and E-04 mutations (a) and (b) each turn one of them red.
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
| F-04 | `agent_workflows.clean_delta` source read (corrected at review) | `_compute_sha256` is called by `build_default_adapter_manifest`, `detect_adapter_drift` and `snapshot_target_state` (the `snap.file_hashes[rel_p] = _compute_sha256(text)` line); `AdapterManifest.get` is called by `repair_adapters`. Both private-ish keys are reached through the restored public-surface tests, which is why E-04 (e) and (f) mutate them directly to prove the reach is load-bearing. |
| F-05 | review (2026-10-17, HEAD `316482e76`): restored file with the core marker, scratch mutations of `clean_delta.py` reverted (`git diff agent_workflows/` empty) | Bare collect lists `tests/test_clean_delta.py: 24`; isolated run `24 passed`; bare `python3 -m pytest` with the file present `777 passed in 26.14s` (30s budget). Mutations KILLED by the restored tests: E-03 (a) 3 `AdapterPurityTests`, (b) `test_conversion_replaces_our_block...`, (c) 2 `PortableReferenceTests`; E-04 (c) `test_host_scoped_uninstall...`, (d) 2 tests, (e) 2 tests, (f) `TargetDeltaTests::test_every_kind_of_change_is_detected_and_classified`. SURVIVED (`24 passed`): E-04 (a) drift-always-clean and (b) block-repaired-as-shim, because no restored test drifts an installed adapter or inspects a repaired `AGENTS.md`. Scratch versions of the two E-06 tests passed at HEAD and each killed one of those two mutations. |

## Proposed changes (ordered, validatable)

1. E-01 restores `tests/test_clean_delta.py` with the core marker and a provenance note.
2. E-02 runs it in isolation.
3. E-06 adds two tests for the drift and managed-block repair behaviors no restored test guards (F-05).
4. E-03 and E-04 prove each key is guarded by a scratch mutation that turns a test red.
5. E-05 confirms it fits the core tier.

## Deferred / out of scope (with reason)

- The 6 already-reached clean_delta keys are not this item's gap; the restored module exercises them incidentally, and no further work is owed for them.
  - Carrier-Declined: they are `reached` at baseline per `b1mx2w`, so no reach gap exists to carry.
- Converting the restored `unittest.TestCase` classes to pytest-style functions is out of scope: it would rewrite tests that pass verbatim (F-03) for no behavioral gain.
  - Carrier-Declined: style-only, no defect or gap owed.

## Scope check

- Over-scope: none. One restored test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none for the 9 named keys once E-06 lands (without it, drift classification and managed-block repair were unguarded, F-05).

## Required tests / validation

- `python3 -m pytest tests/test_clean_delta.py -o addopts="" -v` passes, with the per-test list pasted (24 restored plus 2 E-06 tests at review).
- Bare `python3 -m pytest` passes (core tier, including the restored module, within the 30s budget), with the summary line pasted.
- Mutation spot-checks of E-03 and E-04: paste the failing test name and assertion for each of the 9 scratch mutations, then an empty `git diff agent_workflows/`.
- Core-tier budget: the bare run measured 26.14s of a 30s budget at review, so paste the wall time; a budget failure is a STOP-worthy unsafe condition to report, not something to fix by un-marking tests.

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
  - Required evidence: paste `git diff --stat` showing only `tests/test_clean_delta.py` added; paste `git diff --no-index <(git show 19313eed^:tests/test_clean_delta.py) tests/test_clean_delta.py` (or equivalent) showing only the marker, import, provenance paragraph, the two line-number citation edits and the appended E-06 class; paste `python3 -m pytest --collect-only -q | rg test_clean_delta` showing the module selected by the bare core tier with its count, and state that count matches the `-v` run in V-02.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing every collected restored test as PASSED, with the summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, for each of the 3 scratch mutations, the failing test id and assertion message from the rerun.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste, for each of the 6 scratch mutations (a)..(f), the failing test id and assertion message (for (a) and (b), an E-06 test), then the empty output of `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the bare `python3 -m pytest` summary line with its wall time showing passed and no core-tier budget failure.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `-v` lines for both `DriftAndBlockRepairTests` tests as PASSED; paste the class source from the committed file showing it calls `detect_adapter_drift`, `repair_adapters` and `uninstall_adapters` and asserts on their returned lists and the files on disk.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:

- Open questions: all resolved (OQ-01).
- Scope fence: `tests/test_clean_delta.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under the E-01 disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch edits to `agent_workflows/clean_delta.py` that must be reverted before commit and must be absent from the diff.
- Honesty: you MUST paste the actual runner output for every test and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit dwjfu4 -- tests/test_clean_delta.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize dwjfu4` instead. Never hand-`git mv` the plan.
