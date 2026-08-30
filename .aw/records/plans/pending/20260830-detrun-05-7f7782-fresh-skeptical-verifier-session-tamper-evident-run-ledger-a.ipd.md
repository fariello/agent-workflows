# IPD: Fresh skeptical verifier session, tamper-evident run ledger, and deterministic completion checker

- Date: 2026-08-30
- Kind: child
- Concern: Work-item completion currently relies on agent exit status and post-execution linter rather than a fresh skeptical audit, hash-chained ledger, and deterministic proof boundary.
- Scope: Implement the fresh skeptical verifier session harness, append-only hash-chained run ledger, the deterministic completion checker authorizing all lifecycle transitions, aggregate exit code calculation, and `--unverifiable-ok` neutrality handling. Implements spec 25kzda Sections 1.1, 4.2, 5.1, 5.3, and 5.6.
- Scope-Paths: agent_workflows/run_verifier.py, agent_workflows/run_ledger.py, agent_workflows/deterministic_checker.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_deterministic_checker.py
- Item-Dependencies: executed:k7o7el
- Status: to-review
- Set: detrun
- Order: 5
- Highest E allocated: 07
- Author: antigravity
- Id: 7f7782
- Blocks-Release: next

## Workflow history

- 2026-08-30 draft (antigravity): created.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).

## Goal

Provide the skeptical verification and deterministic authority layer that launches unpolluted verifier sessions, records a tamper-evident hash-chained run ledger, evaluates deterministic repository state for completion authorization, and computes honest aggregate exit codes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fresh skeptical verifier session harness

- [ ] E-01 Create `agent_workflows/run_verifier.py` implementing the fresh skeptical verifier turn harness.
  - Depends on: none
  - Expected outcome: Launches a brand-new host session with zero executor memory inheritance, passes frozen predicates + diff, and returns structured machine-parseable findings.
  - Execution state: pending

### Task group 2: Tamper-evident run ledger

- [ ] E-02 Create `agent_workflows/run_ledger.py` implementing the append-only, hash-chained run ledger (`.aw/records/runs/<run-id>/ledger.jsonl`).
  - Depends on: none
  - Expected outcome: Each event record binds to the prior record hash, event payload digest, and captured evidence IDs; provides `verify_ledger(path) -> bool` proving ledger integrity.
  - Execution state: pending

- [ ] E-03 Add `aw runs show <run-id>`, `aw runs evidence <run-id>`, and `aw runs verify <run-id>` inspection commands in `agent_workflows/cli.py`.
  - Depends on: E-02
  - Expected outcome: Users can inspect run event timelines, list captured command outputs, and verify cryptographic ledger integrity offline.
  - Execution state: pending

### Task group 3: Deterministic completion checker

- [ ] E-04 Create `agent_workflows/deterministic_checker.py` implementing the comprehensive suite of deterministic completion checks from spec Section 4.2 (`RUN-FROZEN-IDENTITY`, `RUN-STRUCTURE-PREFLIGHT`, `RUN-LEDGER-INTEGRITY`, `RUN-FRESH-VERIFIER`, `RUN-SCOPE-DELTA`, `RUN-COMMIT-CONTENTS`, `RUN-CHECK-FRESHNESS`, `RUN-CROSS-TREE`).
  - Depends on: E-01, E-02
  - Expected outcome: Deterministic checker evaluates real repository/git state, verifies commit trailers, reruns check recipes, and alone authorizes `verified` outcomes and terminal transitions.
  - Execution state: pending

- [ ] E-05 Implement aggregate exit code calculation (0, 1, 2, 3, 4, 130) and `--unverifiable-ok` aggregate neutrality handling in `agent_workflows/deterministic_checker.py`.
  - Depends on: E-04
  - Expected outcome: Run exit codes reflect exact outcome states; contractless prompts contribute aggregate neutrality under `--unverifiable-ok` without falsifying item-level `ran` / `unavailable` state.
  - Execution state: pending

### Task group 4: Runner integration

- [ ] E-06 Wire verifier sessions, ledger recording, and deterministic checker authorization into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-01, E-02, E-04, E-05
  - Expected outcome: Full run pipeline executes executor -> verifier -> deterministic check -> terminal transaction, outputting structured JSON and formatted TTY status lines.
  - Execution state: pending

### Task group 5: Test suite coverage

- [ ] E-07 Create `tests/test_deterministic_checker.py` covering fresh verifier session invocation, ledger hash chaining, all 13 common deterministic checks, exit code aggregation, and inspection CLI commands.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: Full pytest suite passes with complete branch coverage on verification and ledger validation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Ledger paths: `.aw/records/runs/run-<timestamp>-<pid>/ledger.jsonl`.
- Aggregate exit codes: 0 (all verified / neutral), 1 (failed/unmet), 2 (bad selector), 3 (needs input), 4 (fatal integrity abort), 130 (interrupted).

## Findings

- Currently, `runipd` verifies single IPD execution via `ipd lint --phase pre-transition` but does not record a cryptographic hash-chained event ledger or launch a skeptical second turn for semantic cross-checks.

## Proposed changes (ordered, validatable)

1. Implement fresh verifier session launcher in `run_verifier.py` (E-01).
2. Implement hash-chained ledger in `run_ledger.py` (E-02).
3. Add `aw runs show/verify` CLI commands (E-03).
4. Implement deterministic checker suite in `deterministic_checker.py` (E-04).
5. Implement exit code aggregation and `--unverifiable-ok` neutrality (E-05).
6. Integrate with runner dispatch loop (E-06).
7. Cover with comprehensive tests in `test_deterministic_checker.py` (E-07).

## Deferred / out of scope (with reason)

- **External third-party API transaction verification**: Requires custom remote receipt capturing, deferred per spec Section 6.1.
- **Hardware-enforced TEE attestation**: Beyond repository scope; cryptographic hashing is standard SHA-256.

## Scope check

- Over-scope: none. Strictly implements verification, ledger integrity, and completion authority.
- Under-scope: none. Covers all 13 checks in spec Section 4.2 and the complete exit code matrix.

## Required tests / validation

- `python3 -m pytest tests/test_deterministic_checker.py` passing.
- `aw runs verify <run-id>` demonstrating ledger integrity validation on real runs.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 1.1, 4.2, 5.1, 5.3, and 5.6.
- Updates `.aw/records/runs/README.md` documenting the ledger structure and verification CLI.

## Open questions

### OQ-01: Does a skeptical verifier session have tool write access?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 1.1
- Resolution or deferral rationale: RESOLVED - No. The skeptical verifier is read-only; it inspects the diff, test evidence, and candidate state, returning structured findings. Any repairs are executed in a correction turn or reviewed by the checker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Test showing verifier spawned in a separate session without executor history and returning structured finding objects.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Python test writing sequential ledger events, validating hash chain integrity, and detecting tampered records.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: CLI session running `aw runs show` and `aw runs verify` against a completed run ledger.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Test suite executing all 13 common deterministic checks against passing and failing synthetic repository states.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Test verifying exact exit code return values across all 6 exit classes including `--unverifiable-ok` neutrality.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: End-to-end runner test executing a verified IPD lifecycle with ledger creation and deterministic checker sign-off.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `pytest tests/test_deterministic_checker.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
