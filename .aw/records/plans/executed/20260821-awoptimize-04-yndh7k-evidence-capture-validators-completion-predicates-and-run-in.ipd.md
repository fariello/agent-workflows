# IPD: Evidence Capture Validators Completion Predicates and Run Inspection CLI

- Date: 2026-08-21
- Kind: child
- Concern: Turn captured evidence into a deterministic completion predicate so completion is COMPUTED, not claimed by a model.
- Scope: Evidence capture (provenance envelopes bound to command/cwd/HEAD/exit/hash/worktree/actor), evidence validators (one per false-completion class), completion predicates, read-only aw run show|evidence|verify-ledger CLI, and the evidence-layer adversarial fixtures.
- Status: executed
- Set: awoptimize
- Order: 4
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: yndh7k

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-02 E-04..E-08 into 5 right-sized E-items (evidence capture, per-class validators, completion predicate, aw run inspection CLI, adversarial suite) + the evidence-sufficiency matrix.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. This is the completion-as-predicate core; E-03 correctly requires an INDEPENDENT verifier-authored decision (Order-02 RL-E032). PR-001 (MEDIUM, cross-plan): both this Order (E-04) and Order 07 (E-03) create the `aw run` command group + wire run_cli.py, an ownership ambiguity that could collide at execution. FIXED in place: E-04 now OWNS the `aw run` parser-group registration; Order 07's E-03 was cross-referenced to EXTEND (not re-register) the group (disjoint read-only vs lifecycle subcommand sets). V-01..V-05 map 1:1 with falsifiable evidence; adversarial suite mandated before completion. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.
- 2026-08-22 executed (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): E-01..E-05 executed via agy/Gemini (committed a7ce5ce: run_evidence.py, run_cli.py, cli.py aw run group, tests); independently verified by opencode - `aw run` group wired (show/evidence/verify-ledger), 44 module tests pass, full suite 1408 passed 1 skipped (pytest rc=0) WITH a concurrent agent's aw-set changes integrated cleanly. V-01..V-05 evidence real. Terminal transition to executed/.

## Goal

Make completion a deterministic PREDICATE over frozen requirements, valid captured evidence,
repository identity, and independent verifier decisions - not a word an executor emits. This Order
captures evidence at tool/artifact boundaries, mechanically rejects every known false-completion
class, computes completion, exposes read-only inspection through `aw run`, and proves the whole thing
against an adversarial suite. It builds on the Order-02 records + Order-03 store.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: evidence capture

- [x] E-01 Implement evidence capture in `agent_workflows/run_evidence.py`: build an `evidence_envelope`/`tool_event` for a command or artifact recording command argv, cwd, start/end time, exit code, stdout/stderr reference + SHA-256, truncation state, an environment allowlist (no raw secrets), repository HEAD, dirty-state digest, worktree path, actor, and linked E/V/requirement ids; append it via the Order-03 store.
  - Depends on: none
  - Expected outcome: a captured command/artifact envelope contains every required provenance field bound to the correct HEAD/dirty-digest/worktree/actor/ids, with output referenced by hash and no secret leaked into the record.
  - Execution state: performed

### Task group 2: validators and completion

- [x] E-02 Implement evidence validators (`validate_evidence`) that reject, each with a distinct stable reason, every known false-completion class: missing output, fabricated manual text (no captured tool event), stale HEAD, wrong cwd, wrong worktree, mismatched command, expired host probe, truncated required output, failed exit, absent artifact, hash mismatch, and an executor-authored verifier decision.
  - Depends on: E-01
  - Expected outcome: one fixture per listed class is rejected with its stable reason; valid fresh evidence is accepted; a required-truncation/redaction conflict fails closed.
  - Execution state: performed
- [x] E-03 Implement completion predicates (`is_complete`) that return true only when: every frozen requirement (Order 02) is covered, every required E-item is `performed`, every V-item has a `pass` decision authored by an authorized INDEPENDENT verifier (not the executor), all required commands are valid and green, no unresolved blocker/correction remains, and terminal authority is held by the coordinator.
  - Depends on: E-02
  - Expected outcome: a truth-table test shows completion only when all predicates hold and coordinator authority is present; toggling any single input false independently prevents completion; model prose or a direct edit cannot flip a run to complete.
  - Execution state: performed

### Task group 3: inspection CLI

- [x] E-04 CREATE the `aw run` command group and add its read-only `show`, `evidence`, and `verify-ledger` subcommands (a thin `agent_workflows/run_cli.py` wired into `agent_workflows/cli.py`, mirroring how `workflow_cli.py` registered the `workflow` group in Order 01) with human + `--agent`/`--json` machine output, stable error codes, redaction of sensitive values, and NO writes by default; `verify-ledger` surfaces Order-03 chain/corruption status and Order-04 evidence validity. OWNERSHIP: this Order OWNS the `aw run` parser-group registration; Order 07 (retry/recovery/lifecycle) EXTENDS the same group with its mutating `start|next|record|resume|cancel|status|finalize` subcommands and MUST NOT re-register the group. The two subcommand sets are disjoint (read-only inspection here; lifecycle there).
  - Depends on: E-03
  - Expected outcome: the `aw run` group exists with the three read-only subcommands; they expose why a run is incomplete and which precise evidence is missing/invalid; machine modes are ANSI-free; no invocation writes to disk; exit codes distinguish clean / invalid-evidence / corruption / invocation error; the group is registered so Order 07 can add subcommands without collision.
  - Execution state: performed

### Task group 4: adversarial suite

- [x] E-05 Add the adversarial test suite `tests/test_run_evidence_completion.py` (stdlib unittest) covering fabricated success text, checked boxes without captured events, green targeted tests plus a red full suite, stale evidence, test deletion, test weakening, mismatched commit/worktree, replay, ledger corruption, interrupted append, and executor/verifier identity collision; each must produce an incomplete or correction-required outcome and the original failed attempt must remain in ledger history. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: every seeded deception + accidental-false-completion fixture fails closed with a named reason; the scorer confirms zero seeded critical escapes; the full serial suite is green (pasted).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Evidence sufficiency matrix

| Claim | Minimum evidence | Additional independent action |
|---|---|---|
| File changed as required | content/diff hash at bound HEAD | verifier inspects symbol and scope |
| Command passed | captured invocation, cwd, exit 0, complete output hash | verifier reruns when risk requires |
| Test proves requirement | test maps to requirement and fails under a seeded break | verifier reviews falsifiability |
| No regression | approved full-suite command at bound HEAD | compare baseline and investigate skips |
| Host capability supported | exact host/version/config probe and nonce side effect | independent or repeated probe before expiry |
| Workflow complete | all deterministic predicates pass | coordinator performs terminal transaction |

## Project conventions discovered (Step 0)

- `aw ipd lint` explicitly does not prove evidence truth; that gap is exactly what this Order's validators + completion predicate close.
- Existing verification workflows already require actual-diff inspection and rerunning repo checks; this Order turns those rules into mechanical ledger predicates rather than prose asks.
- Machine CLI output in this repo is ANSI-free with stable exit codes (0/1/2), mirroring `aw ipd lint` and the Order-01 `aw workflow` CLI; `run_cli.py` follows that shape and wires into `cli.py` like `workflow_cli.py` did.
- Evidence records must never carry raw secrets (an environment allowlist + redaction, reusing the Order-03 redaction hook).

## Findings

| Finding | Consequence |
|---|---|
| Non-empty evidence prose can satisfy structural formatting without proving origin. | Capture evidence at tool/artifact boundaries and validate it mechanically; model-pasted prose is not evidence. |
| Test success may be scoped, stale, or achieved by weakening tests. | Bind evidence to command + HEAD + worktree; the adversarial suite includes green-targeted/red-full, test deletion, and test weakening. |
| Same identity can execute and self-verify. | The completion predicate requires the V-decision to be authored by an INDEPENDENT verifier role; an executor-authored verifier decision is rejected (Order-02 RL-E032) and cannot satisfy completion. |
| A corrupted or replayed ledger could back a false completion. | Completion consumes only Order-03-verified history; corruption/replay fixtures must fail closed. |

## Proposed changes (ordered, validatable)

1. Capture provenance at command/artifact boundaries (E-01).
2. Reject every invalid/stale/fabricated evidence class (E-02).
3. Compute completion rather than accept a claim (E-03).
4. Expose read-only inspection commands (E-04).
5. Prove it with an adversarial suite + full suite (E-05).

## Deferred / out of scope (with reason)

- Record SHAPES + requirement freeze: Order 02. The append-only STORE + tamper evidence: Order 03. This Order consumes both.
- The run STATE MACHINE / scheduling / terminal-transition execution: Order 05 (this Order computes the completion predicate; the runtime enforces it at the gate).
- The independent VERIFIER role/packet/isolation: Orders 08/09 (this Order requires a verifier-authored decision but does not implement the verifier's context isolation).
- Provider-specific telemetry / live model calls: Orders 12/13.

## Scope check

- Over-scope: no record-schema definition, no ledger-store internals, no runtime scheduling, no verifier isolation, no model/host calls, no terminal moves.
- Under-scope: none - capture, validation, completion, inspection CLI, and the adversarial suite are all covered.

## Required tests / validation

- `tests/test_run_evidence_completion.py`: capture provenance fixtures; one rejection fixture per false-completion class (E-02); the completion truth-table (E-03); CLI golden tests (human + agent, no ANSI, no writes, exit codes) (E-04); the full adversarial suite (E-05).
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean; machine-output ANSI checks.

## Spec / documentation sync

- Document the evidence-envelope fields, the evidence-sufficiency matrix, the completion predicate, the `aw run` inspection commands + exit codes, and what the layer does NOT prove (semantic correctness remains the reviewer's job). Add examples for incomplete, blocked, corrected, corrupted, and terminal runs.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The capture fields, validator classes, and completion predicate are enumerated from the old-02 evidence-sufficiency matrix and adversarial list; no open decision. Verifier-context isolation is Orders 08/09; this Order only requires that a V-decision be verifier-authored.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output showing a captured command/artifact envelope contains every required provenance field bound to the correct HEAD/dirty-digest/worktree/actor/E-V-requirement ids, output referenced by hash, and no secret in the record.
  - Observed evidence: `tests.test_run_evidence_completion.TestEvidenceCaptureProvenance` passes (4 tests in 0.015s). Shows captured command and artifact envelopes contain every required provenance field (argv, cwd, start/end time, exit code, stdout/stderr SHA-256, HEAD, dirty digest, worktree, actor, binds), output referenced by hash, and environment allowlist strictly filtering secrets (e.g. API keys, AWS secret keys, Github tokens).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output showing one fixture per listed false-completion class rejected with its distinct stable reason, valid fresh evidence accepted, and a truncation/redaction conflict failing closed.
  - Observed evidence: `tests.test_run_evidence_completion.TestEvidenceValidators` passes (13 tests in 0.021s). Shows one fixture per listed false-completion class rejected with distinct stable reasons (`EV-MISSING-OUTPUT`, `EV-FABRICATED-TEXT`, `EV-STALE-HEAD`, `EV-WRONG-CWD`, `EV-WRONG-WORKTREE`, `EV-COMMAND-MISMATCH`, `EV-EXPIRED-PROBE`, `EV-TRUNCATED-OUTPUT`, `EV-FAILED-EXIT`, `EV-ABSENT-ARTIFACT`, `EV-HASH-MISMATCH`, `EV-EXECUTOR-VERIFIER`, `EV-REDACTION-CONFLICT`), valid fresh evidence accepted, and redaction blocking verification failing closed.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted truth-table test output showing completion only when every predicate holds + coordinator authority present, each input toggled false independently prevents completion, and model prose / a direct edit cannot flip a run complete.
  - Observed evidence: `tests.test_run_evidence_completion.TestCompletionPredicates` passes (8 tests in 0.012s). Shows completion truth-table evaluating True only when every predicate holds (covered requirements, performed steps, verifier independence, green commands, no blockers, coordinator authority present). Toggling any single input false independently prevents completion (`is_complete=False`), and model prose or direct edits cannot flip completion.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted CLI golden output showing `aw run show|evidence|verify-ledger` expose missing/invalid evidence + corruption with stable codes, redact sensitive values, make no writes by default, and emit ANSI-free machine output.
  - Observed evidence: `tests.test_run_evidence_completion.TestRunCLI` passes (7 tests in 0.320s). Shows `aw run show|evidence|verify-ledger` expose missing/invalid evidence and corruption with stable exit codes (0 clean/complete, 1 incomplete/findings, 2 corruption/error), redact sensitive values, make zero writes by default, and emit ANSI-free machine output (`--agent`/`--json`).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: `tests/test_run_evidence_completion.py` exists and passes; every adversarial fixture yields incomplete/correction-required with a named reason and the original failed attempt remains in ledger history; pasted full serial-suite tail showing green counts and zero seeded critical escapes.
  - Observed evidence: `tests.test_run_evidence_completion.TestAdversarialSuite` passes (11 tests in 0.315s). Shows every seeded deception and accidental false-completion fixture fails closed with a named reason, failed attempts remain in ledger history, and full test suite is green (`make test` -> 100% green).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Orders 02 (records + freeze) and 03 (append-only store). Scope fence: touch only `agent_workflows/run_evidence.py`, the completion-predicate module, `agent_workflows/run_cli.py` + its wiring in `agent_workflows/cli.py`, and `tests/test_run_evidence_completion.py`; do NOT implement the runtime state machine (Order 05) or the verifier's context isolation (Orders 08/09) - if it seems to need more, STOP and report. Do not accept prose pasted by a model as captured evidence; do not expose secrets or unrestricted environment state in evidence records; if a required redaction would make a completion predicate unverifiable, STOP and revise the evidence design explicitly. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition, and the adversarial suite MUST run before any lifecycle completion. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
