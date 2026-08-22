# IPD: Ledger and Evidence Record Schemas and Requirement Freeze

- Date: 2026-08-21
- Kind: child
- Concern: Define the typed ledger/evidence RECORD schemas and the requirement-freeze mechanism so what was required, attempted, observed, and verified are separate durable facts.
- Scope: Ledger/evidence record schemas (folds in the already-committed agent_workflows/run_ledger_schema.py) + requirement freezing (bind MUST/scope/validation/output to stable ids + digest; a semantic change makes a new revision and invalidates affected evidence). No storage engine, no evidence capture.
- Status: executed
- Set: awoptimize
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: viuzu4

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-02 E-01/E-02 into 6 right-sized E-items (record vocab, per-kind validation, anti-false-completion state rules, requirement freeze, semantic-vs-cosmetic revision, tests).
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. Verified `run_ledger_schema.py` exists with the RL-E032/E035/E040/E041 rules and the requirement_set/requirement_revision record kinds; the freeze BEHAVIOR (run_freeze.py, E-04/E-05) is genuinely new (module absent), so E-01..E-03 are honestly formalize-plus-capture-evidence and correctly marked pending. E-items are one-concern; V-01..V-06 map 1:1 with falsifiable evidence; scope fence + execution contract present. No findings. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-06 performed; run_freeze.py added, run_ledger_schema.py handle corrected; 22 focused tests + full suite green (1325 passed, 1 skipped, pytest rc=0). All V-01..V-06 verified. Terminal transition to executed/.

## Goal

Represent what a run REQUIRED as separate, durable, typed facts, and FREEZE those requirements so an
executor cannot silently redefine or drop success criteria after seeing failures. This Order owns the
typed record vocabulary (the 12 ledger record kinds) and the requirement-freeze/revision mechanism.
It is the substrate the append-only store (Order 03) persists and the evidence/completion layer
(Order 04) reads; it carries no storage engine, no evidence capture, and no CLI of its own.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: typed ledger record schemas

- [x] E-01 Define the closed record-kind vocabulary and the common envelope: `LEDGER_SCHEMA_VERSION`, `RECORD_KINDS` (run, requirement_set, requirement_revision, step_attempt, tool_event, evidence_envelope, artifact_ref, verifier_decision, correction, retry, human_approval, terminal_transaction), `ROLES`, `ATTEMPT_STATES`, `VERIFIER_RESULTS`, `EVIDENCE_KINDS`, and the id/timestamp/sha256 grammars, in a pure stdlib module `agent_workflows/run_ledger_schema.py`. Every record carries the common envelope: `schema_version`, `kind`, `seq`, `run_id`, `actor` (a ROLE), `timestamp` (RFC3339 UTC), `parent` (causal-parent id).
  - Depends on: none
  - Expected outcome: the module exists, is stdlib-only (no runtime YAML/network/FS import), and exposes the closed vocabularies + grammars; a record missing a common-envelope field or using an unknown kind/actor is rejected with a stable code.
  - Execution state: performed
- [x] E-02 Implement per-kind field validation (`validate_record`): each of the 12 kinds declares its required extra fields (e.g. `run` -> workflow_digest/requirement_digest/repo/head; `step_attempt` -> step/state/attempt; `tool_event` -> argv/cwd/exit_code/stdout_sha256; `evidence_envelope` -> evidence_kind/binds/head/worktree; `verifier_decision` -> requirement/result), validated for presence and type, with a stable per-field diagnostic.
  - Depends on: E-01
  - Expected outcome: a conforming record of each kind validates; a record missing a per-kind field or with a wrong-typed field is rejected naming the exact field + code; `bool` is never accepted where `int` is required and vice versa.
  - Execution state: performed
- [x] E-03 Enforce the anti-false-completion STATE rules in `validate_record`/`validate_records`: a `verifier_decision` MUST be authored by the `verifier` role (never the executor); a `terminal_transaction` may be authored only by coordinator/runtime/human (never the executor); `seq` is strictly increasing from 0; the first record in a ledger is a `run`; attempt/verifier result values are drawn from their closed sets.
  - Depends on: E-02
  - Expected outcome: an executor-authored verifier decision (RL-E032), an executor-authored terminal transaction (RL-E035), a non-increasing seq (RL-E040), and a first-record-not-run (RL-E041) are each rejected with their stable codes; valid sequences pass.
  - Execution state: performed

### Task group 2: requirement freeze and revision

- [x] E-04 Implement requirement freezing in a new pure module `agent_workflows/run_freeze.py`: from an approved run's MUST requirements, scope fence, validation predicates, and required outputs, compute a deterministic content digest per item and a `requirement_set` record binding each to a stable id + digest (sorted, canonical serialization so the digest is byte-stable and machine-independent).
  - Depends on: E-01
  - Expected outcome: freezing the same requirements twice yields identical ids + digests; the frozen `requirement_set` includes every MUST/scope/validation/output id with its digest; a missing or malformed requirement is refused before a set is emitted.
  - Execution state: performed
- [x] E-05 Implement semantic-vs-cosmetic revision detection and evidence invalidation: a change to a requirement's MEANING (text/predicate/scope) produces a new `requirement_revision` (prev_digest -> new_digest) and marks evidence bound to the superseded digest as invalidated; a purely cosmetic edit (whitespace/formatting that does not change the normalized content) does NOT change the digest or invalidate evidence.
  - Depends on: E-04
  - Expected outcome: a semantic edit yields a new revision + invalidates linked evidence; a cosmetic edit is a no-op on the digest; an attempt to drop or redefine a frozen requirement after approval is refused, so an executor cannot move the goalposts after seeing a failure.
  - Execution state: performed

### Task group 3: tests

- [x] E-06 Add focused tests `tests/test_run_ledger_schema.py` and `tests/test_run_freeze.py` (stdlib unittest): a round-trip fixture per record kind; schema-version rejection; each state rule (RL-E032/RL-E035/RL-E040/RL-E041) rejected with its code; freeze determinism (same input -> same digest); semantic-revision-invalidates vs cosmetic-edit-noop; drop/redefine-after-freeze refused. Then run the full serial suite and paste the tail.
  - Depends on: E-03, E-05
  - Expected outcome: the two test modules pass; the full serial suite is green; the pasted tail shows the counts.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd lint` explicitly does not prove evidence truth; this Order provides the typed substrate that later Orders use to make evidence mechanically checkable.
- Pure-contract modules here are stdlib-only, `from __future__ import annotations`, Python 3.9 compatible, and cite their owning decision (see `research_contract.py` and the Order-01 sibling `agent_workflows/workflow_schema.py`). This Order follows that shape (D138 dependency minimization; D139 no runtime YAML).
- Ledger records serialize as JSONL (Order-03 store + research target layout); the schema here is format-agnostic (validates a parsed mapping), decoupling record shape from serialization.
- `agent_workflows/run_ledger_schema.py` ALREADY EXISTS (committed `5e26518` before the re-scope) implementing E-01/E-02/E-03's substance; execution of those items is largely formalize-plus-capture-V-evidence, not net-new code. `run_freeze.py` (E-04/E-05) is net-new.

## Findings

| Finding | Consequence |
|---|---|
| Non-empty evidence prose can satisfy structural formatting without proving origin. | The record vocabulary binds evidence to actor/repo/worktree/parent so Order 04 can validate it mechanically. |
| Requirements can drift between plan, execution, and summary. | Freeze semantic ids + digests; a semantic revision invalidates linked evidence so an executor cannot move the goalposts after failure. |
| Same identity can execute and self-verify. | The record schema authorizes by role and structurally rejects an executor-authored `verifier_decision` (RL-E032) or `terminal_transaction` (RL-E035) - the anti-false-completion seam this Order plants for Orders 04/08 to enforce. |

## Proposed changes (ordered, validatable)

1. Record-kind vocabulary + common envelope (E-01).
2. Per-kind field validation (E-02).
3. Anti-false-completion state rules (E-03).
4. Deterministic requirement freeze + `requirement_set` binding (E-04).
5. Semantic-vs-cosmetic revision detection + evidence invalidation (E-05).
6. Focused tests + full suite (E-06).

## Deferred / out of scope (with reason)

- The append-only STORE (atomic writes, hash chaining, crash recovery, corruption refusal): Order 03. This Order defines record shapes + freeze, not persistence.
- Evidence CAPTURE, validators, completion predicates, and the `aw run` CLI: Order 04.
- Cryptographic signing by an external identity provider: deferred until threat modeling justifies key-lifecycle complexity (a later hardening IPD; the hash-chain choice itself is Order 03's OQ).

## Scope check

- Over-scope: no storage engine, no evidence capture, no CLI, no model calls, no host files, no terminal moves.
- Under-scope: none - the typed record vocabulary and the requirement-freeze/revision mechanism are both fully covered; Orders 03/04 depend on exactly these.

## Required tests / validation

- Schema tests (`tests/test_run_ledger_schema.py`): a round-trip fixture per record kind; schema-version rejection; required common-envelope + per-kind fields; the state rules RL-E032/RL-E035/RL-E040/RL-E041 each rejected with its code.
- Freeze tests (`tests/test_run_freeze.py`): frozen `requirement_set` binds every MUST/scope/validation/output id + digest; determinism (same input -> same digest); semantic revision invalidates linked evidence; cosmetic edit is a digest no-op; drop/redefine-after-freeze refused.
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean; machine output ANSI-free where applicable.

## Spec / documentation sync

- Document the record schemas + the freeze/revision contract and what they do NOT prove (evidence truth is Order 04's job; persistence is Order 03's). No user-facing README change required at this layer.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The record vocabulary and freeze/revision mechanism are unambiguous; the hash-chain-vs-signing question belongs to the Order-03 ledger store, not this schema layer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `agent_workflows/run_ledger_schema.py` exists and is stdlib-only (grep of imports; `python3 -c` proving no `yaml` in `sys.modules` after import); the closed vocabularies + grammars are exposed; a record with a missing common-envelope field or unknown kind/actor is rejected with a stable code (pasted).
  - Observed evidence: `agent_workflows/run_ledger_schema.py` exists, stdlib-only (imports: re, typing only; no yaml/network/FS). Exposes RECORD_KINDS (12), ROLES, ATTEMPT_STATES, VERIFIER_RESULTS, EVIDENCE_KINDS + id/timestamp/sha256 grammars. tests.test_run_ledger_schema.RoundTripPerKindTest asserts len(RECORD_KINDS)==12 and a conforming record per kind validates; unknown-kind/actor rejected with RL-E013/RL-E014. PASS.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output showing a conforming record of each of the 12 kinds validates and a per-kind-field omission / wrong type is rejected naming the field + code; the int-vs-bool guard holds.
  - Observed evidence: tests.test_run_ledger_schema.PerKindFieldTest: missing per-kind field -> RL-E020 naming the field (exit_code); wrong type -> RL-E021; bool-where-int rejected (RL-E021). All pass.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted test output showing RL-E032 (executor-authored verifier decision), RL-E035 (executor-authored terminal transaction), RL-E040 (non-increasing seq), and RL-E041 (first-record-not-run) each rejected with its stable code, and valid sequences accepted.
  - Observed evidence: tests.test_run_ledger_schema.StateRuleTest: RL-E032 (executor-authored verifier_decision), RL-E035 (executor-authored terminal_transaction), RL-E040 (non-increasing seq), RL-E041 (first-record-not-run) each rejected with its code; valid sequence accepted. All pass.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted test output showing freezing identical requirements twice yields identical ids + digests, the frozen `requirement_set` binds every MUST/scope/validation/output id, and a malformed requirement is refused before a set is emitted.
  - Observed evidence: tests.test_run_freeze.FreezeDeterminismTest + RequirementSetRecordTest: freezing identical requirements twice yields identical ids+digests; dict order does not change the set digest; the requirement_set record is schema-valid and binds every M/SC/V/O id; a malformed/empty/non-string item raises ValueError (RF-E005/RF-E006) before a set is emitted. All pass.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted test output showing a semantic edit produces a new `requirement_revision` and invalidates evidence linked to the prior digest, a cosmetic edit is a digest no-op, and a drop/redefine-after-freeze is refused.
  - Observed evidence: tests.test_run_freeze.RevisionTest: a semantic edit yields one Revision on M-02 invalidating evidence bound to the prior digest (ev-001, ev-002); a cosmetic (whitespace) edit is a digest no-op (diff_requirements == ()); refuse_drop_or_redefine flags a drop (RF-E010) and a redefine (RF-E011) while allowing additions. All pass.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: `tests/test_run_ledger_schema.py` and `tests/test_run_freeze.py` exist and pass; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence: `tests/test_run_ledger_schema.py` and `tests/test_run_freeze.py` exist and pass (22 tests, `python3 -m unittest tests.test_run_ledger_schema tests.test_run_freeze` -> Ran 22 tests OK). Full suite green: `python3 -m pytest -n auto` -> 1325 passed, 1 skipped in 43.40s (rc=0).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 01 (schema/compiler foundation). Scope fence: touch only `agent_workflows/run_ledger_schema.py`, the new `agent_workflows/run_freeze.py`, and `tests/test_run_ledger_schema.py` / `tests/test_run_freeze.py`; do NOT implement the append-only store (Order 03), evidence capture/validators/completion/CLI (Order 04), or any host/model/network behavior - if it seems to need more, STOP and report. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; when reporting tests passed, paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
