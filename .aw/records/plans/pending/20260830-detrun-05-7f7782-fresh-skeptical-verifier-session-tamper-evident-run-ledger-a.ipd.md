# IPD: Fresh skeptical verifier session, tamper-evident run ledger, and deterministic completion checker

- Date: 2026-08-30
- Kind: child
- Concern: Work-item completion currently relies on agent exit status and post-execution linter rather than a fresh skeptical audit, hash-chained ledger, and deterministic proof boundary.
- Scope: Implement the fresh skeptical verifier session harness, append-only hash-chained run ledger, the deterministic completion checker implementing all 13 common checks, run resume mechanics, aggregate exit code calculation, and `--unverifiable-ok` neutrality handling. Implements spec 25kzda Sections 1.1, 4.2, 5.1, 5.3, 5.5, and 5.6.
- Scope-Paths: agent_workflows/run_verifier.py, agent_workflows/run_ledger.py, agent_workflows/deterministic_checker.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_deterministic_checker.py
- Item-Dependencies: executed:k7o7el
- Status: reviewed
- Set: detrun
- Order: 5
- Highest E allocated: 08
- Author: antigravity
- Id: 7f7782
- Blocks-Release: next

## Workflow history
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001. E-02/E-03/E-04/E-06 are ALREADY SHIPPED: hash-chained append-only ledger with corruption refusal (`run_ledger_store.py`: prev_hash/GENESIS_HASH/BrokenChainError), `aw run show|evidence|verify-ledger` (`run_cli.py`), completion predicates + false-completion validators (`run_evidence.py`), resume/cancel/crash recovery (`run_recovery.py`), plus `run_ledger_schema.py`, `run_freeze.py`, `run_gates.py`. Building a second ledger and a second completion authority in the one component that must be the single trustworthy authority is worse than none: two disagreeing checkers mean neither can authorize completion. Residue: the fresh verifier harness (E-01), after inventorying `run_evidence.py`. Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened 13 common deterministic checks, ledger hash chaining, run resume validation, and exit code aggregation.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE (/plan-review 2026-08-30, PR-001 BLOCKER).** This plan is the second-worst
duplication in the Set after child 01. Verified at HEAD `d4d265b6`:

| This plan's E-item | Already shipped as | Evidence |
| --- | --- | --- |
| E-02 append-only hash-chained ledger + `verify_ledger` | `run_ledger_store.py` | `prev_hash` chaining, `GENESIS_HASH`, `BrokenChainError`, `compute_record_hash`, single-writer lock, typed `LedgerCorruption` refusal, redaction hooks (`agent_workflows/run_ledger_store.py:405,476,507`) |
| E-03 `aw runs show/evidence/verify` | `aw run show`, `aw run evidence`, `aw run verify-ledger` | `agent_workflows/run_cli.py`; `aw run --help` lists them |
| E-04 deterministic completion checker | `run_evidence.py` completion predicates + false-completion validators | module docstring E-01..E-03: capture provenance, mechanically validate against "every known false-completion class", deterministic completion predicates |
| E-06 resume mechanics | `run_recovery.py` | E-02 "resume / cancel / crash recovery"; `aw run resume` shipped and "refuse on interrupted side effects" |
| record vocabulary the checker needs | `run_ledger_schema.py` | typed records separating REQUIRED / ATTEMPTED / OBSERVED / VERIFIED |
| requirement freezing the checker compares against | `run_freeze.py` | frozen requirement digests, `requirement_revision`, evidence invalidation |
| human-gate `needs_input` behavior | `run_gates.py` | "consent is NEVER synthesized"; headless stop with stable `needs_input` |

Creating `run_ledger.py` beside the shipped `run_ledger_store.py`, and `deterministic_checker.py`
beside the shipped `run_evidence.py`, would give the repo two ledgers and two completion authorities.
That is precisely the drift GUIDING_PRINCIPLES P8 forbids, and in a component whose entire value is
being the SINGLE trustworthy authority, a second implementation is worse than none: two disagreeing
checkers mean neither can be trusted to authorize completion.

What IS genuinely unbuilt and worth keeping: the fresh skeptical verifier session harness (E-01) is
real work not obviously shipped (`agy_verifier.py` is only 301 lines and
`orchestrate_isolation.py` defines a `ForkedVerifierForbiddenError`, so the boundary needs
investigation, not assumption); and the specific 13 `RUN-*` common checks of spec 25kzda 4.2 may need
wiring ON TOP of the shipped predicates. A replacement plan must first inventory `run_evidence.py` and
state which of the 13 checks already exist there before proposing to write any.

Original goal, retained for the record: provide the skeptical verification and deterministic authority
layer that launches unpolluted verifier sessions, records a tamper-evident hash-chained run ledger,
evaluates deterministic repository state for completion authorization, supports safe run resumption,
and computes honest aggregate exit codes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fresh skeptical verifier session harness

- [ ] E-01 Create `agent_workflows/run_verifier.py` implementing the fresh skeptical verifier turn harness.
  - Depends on: none
  - Expected outcome: Launches a brand-new host session with zero executor memory inheritance, passes frozen predicates + diff, enforces read-only tool policy, and returns structured machine-parseable findings.
  - Execution state: pending

### Task group 2: Tamper-evident run ledger and inspection tools

- [ ] E-02 Create `agent_workflows/run_ledger.py` implementing the append-only, hash-chained run ledger (`.aw/records/runs/<run-id>/ledger.jsonl`).
  - Depends on: none
  - Expected outcome: Each event record binds to the prior record hash, event payload digest, and captured evidence IDs; provides `verify_ledger(path) -> bool` proving ledger integrity.
  - Execution state: pending

- [ ] E-03 Add `aw runs show <run-id>`, `aw runs evidence <run-id>`, and `aw runs verify <run-id>` inspection commands in `agent_workflows/cli.py`.
  - Depends on: E-02
  - Expected outcome: Users can inspect run event timelines, list captured command outputs, and verify cryptographic ledger integrity offline.
  - Execution state: pending

### Task group 3: Deterministic completion checker

- [ ] E-04 Create `agent_workflows/deterministic_checker.py` implementing the comprehensive suite of all 13 deterministic completion checks from spec Section 4.2 (`RUN-FROZEN-IDENTITY`, `RUN-STRUCTURE-PREFLIGHT`, `RUN-BASELINE-OWNERSHIP`, `RUN-LEDGER-INTEGRITY`, `RUN-HOST-CAPABILITY`, `RUN-HOST-ATTEMPT`, `RUN-FRESH-VERIFIER`, `RUN-SCOPE-DELTA`, `RUN-COMMIT-CONTENTS`, `RUN-COMMIT-GATEWAY`, `RUN-NO-PUSH`, `RUN-CHECK-FRESHNESS`, `RUN-CROSS-TREE`).
  - Depends on: E-01, E-02
  - Expected outcome: Deterministic checker evaluates real repository/git state, verifies commit trailers, reruns check recipes, and alone authorizes `verified` outcomes and terminal transitions.
  - Execution state: pending

- [ ] E-05 Implement aggregate exit code calculation (0, 1, 2, 3, 4, 130), retry budget enforcement (0..10), and `--unverifiable-ok` aggregate neutrality handling in `agent_workflows/deterministic_checker.py`.
  - Depends on: E-04
  - Expected outcome: Run exit codes reflect exact outcome states; contractless prompts contribute aggregate neutrality under `--unverifiable-ok` without falsifying item-level `ran` / `unavailable` state.
  - Execution state: pending

### Task group 4: Run resume mechanics and runner integration

- [ ] E-06 Implement safe run resumption (`aw <host> run --resume <run-id>`) in `agent_workflows/deterministic_checker.py` and wire verifier sessions, ledger recording, and deterministic checks into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
  - Depends on: E-01, E-02, E-04, E-05
  - Expected outcome: Resume validates ledger integrity, re-evaluates dependency satisfaction for skipped nodes, and continues execution on the frozen DAG without option mutation.
  - Execution state: pending

### Task group 5: Test suite coverage and edge cases

- [ ] E-07 Create `tests/test_deterministic_checker.py` covering fresh verifier session invocation, ledger hash chaining, all 13 common deterministic checks, exit code aggregation, run resumption, and inspection CLI commands.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: Full pytest suite passes with complete branch coverage on verification and ledger validation.
  - Execution state: pending

- [ ] E-08 Add adversarial verification tests: tampered ledger detection, stale check output rejection, verifier memory inheritance refusal, and resume with modified options rejection.
  - Depends on: E-07
  - Expected outcome: All adversarial edge case tests assert correct fail-closed rejection and exact error codes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Ledger paths: `.aw/records/runs/run-<timestamp>-<pid>/ledger.jsonl`.
- Aggregate exit codes: 0 (all verified / neutral), 1 (failed/unmet), 2 (bad selector), 3 (needs input), 4 (fatal integrity abort), 130 (interrupted).
- Run resume requires identical host and cannot alter frozen queue options or retry budget.

## Findings

- Currently, `runipd` verifies single IPD execution via `ipd lint --phase pre-transition` but does not record a cryptographic hash-chained event ledger or launch a skeptical second turn for semantic cross-checks.
- Verification authority must be independent of agent self-reporting and host transport success.

## Proposed changes (ordered, validatable)

1. Implement fresh verifier session launcher in `run_verifier.py` (E-01).
2. Implement hash-chained ledger in `run_ledger.py` (E-02).
3. Add `aw runs show/evidence/verify` CLI commands (E-03).
4. Implement all 13 checks in `deterministic_checker.py` (E-04).
5. Implement exit code aggregation and `--unverifiable-ok` neutrality (E-05).
6. Implement `--resume` mechanics and integrate with runner dispatch loop (E-06).
7. Cover with comprehensive unit and adversarial tests in `test_deterministic_checker.py` (E-07, E-08).

## Deferred / out of scope (with reason)

- **External third-party API transaction verification**: Requires custom remote receipt capturing, deferred per spec Section 6.1.
- **Hardware-enforced TEE attestation**: Beyond repository scope; cryptographic hashing is standard SHA-256.

## Scope check

- Over-scope: none. Strictly implements verification, ledger integrity, run resumption, and completion authority.
- Under-scope: none. Covers all 13 checks in spec Section 4.2 and the complete exit code matrix.

## Required tests / validation

- `python3 -m pytest tests/test_deterministic_checker.py` passing.
- `aw runs verify <run-id>` demonstrating ledger integrity validation on real runs.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 1.1, 4.2, 5.1, 5.3, 5.5, and 5.6.
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
  - Required evidence: End-to-end runner test executing a verified IPD lifecycle with ledger creation, deterministic checker sign-off, and clean `--resume` continuation.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `pytest tests/test_deterministic_checker.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Adversarial pytest assertions verifying rejection of tampered ledgers and stale check command evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30).** Do NOT execute and do NOT approve.
E-02/E-03/E-04/E-06 are already shipped as `run_ledger_store.py`, `run_cli.py`, `run_evidence.py`, and
`run_recovery.py` (see the table under `## Goal`). Building them again would create a second run ledger
and a second completion authority in the one component that must be a single source of truth. The plan
also depends on child 04, which is itself REPLAN. An executor reaching this gate must STOP and report.
Retire with the parent Set `detrun` (`r4mbcw`); do not file under `executed/`. The verifier-session
harness (E-01) is the salvageable residue, after an inventory of `run_evidence.py`.
