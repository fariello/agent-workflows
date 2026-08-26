# IPD: Phase 1: versioned policy schema and shared aw check --format json with positive and adversarial fixtures

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 1 (the "host-independent deterministic core" all other layers must call): a single policy engine, conceptually `aw check --format json`, where each finding carries a stable rule id, severity + assurance class, affected artifact/location, observed-vs-required state, the exact recovery command, and whether the result is deterministic/heuristic/externally-attested. The toolkit already has a unified `check_engine` (check_engine.py) producing a `Drift` list, but it is not yet organized as a versioned policy schema with the full finding shape, and it lacks a systematic positive+adversarial fixture corpus. Phases 2-5 (atomic commands, hooks, CI) must all call THIS engine so results never diverge by host.
- Scope: Formalize the shared policy engine on top of the existing `check_engine`: (1) a VERSIONED policy schema (a schema_version + a registry of rules, each with stable id, severity, assurance class from the Phase-0 catalog, and determinism/heuristic/attested tag); (2) enrich the `Drift`/finding shape and `aw check --format json` output to include observed-vs-required, the exact recovery command, and the determinism/assurance tags; (3) a fixture corpus with POSITIVE cases (clean artifacts pass) and ADVERSARIAL cases (each cataloged invariant's violation is detected) drawn from the Phase-0 catalog and findings section 9 (code-before-IPD, hand-edited status, terminal transition without evidence, out-of-scope staged tree, claimed-but-unrun tests, stale-tree evidence, missing/disabled/malformed hook, etc.). This child does NOT add the atomic commands/hooks/CI; it makes the engine the single, versioned, well-shaped source of truth they will all call. Reuse the existing per-type validators (check_engine composes them); do not fork. Also includes the first concrete authoring-lifecycle rule (detect-and-nudge): a `draft` IPD whose authoring placeholders are all resolved is flagged with the `aw ipd set to-review` recovery command, fixing the recurring miss where a finished draft is never advanced to `to-review` (scaffold correctly emits `draft` for a stub at ipd_authoring.py:131; nothing advances it when authoring completes).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/artifact_core.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_authoring.py, agent_workflows/cli.py, tests/
- Status: draft
- Set: agentadhere
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: uisjns

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Formalize the existing `check_engine` into a versioned policy engine surfaced as `aw check --format json`, with each finding carrying rule id, severity, assurance class, observed-vs-required, exact recovery command, and determinism tag, plus a positive + adversarial fixture corpus, so every later layer calls one source of truth.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: versioned schema + finding shape

- [ ] E-01 Add a versioned policy schema over `check_engine`: a rule registry keyed by stable rule id, each with severity, assurance class (from Phase-0 catalog), and a determinism/heuristic/attested tag; enrich the finding/`Drift` shape + `aw check --format json` to include observed-vs-required, the exact recovery command, and the tags.
  - Depends on: none
  - Expected outcome: `aw check --format json` emits findings with the full documented shape and a schema_version.
  - Execution state: pending

### Task group 2: fixture corpus

- [ ] E-02 Build a positive + adversarial fixture corpus (from the Phase-0 catalog and findings section 9): clean artifacts pass; each cataloged invariant's violation is detected with the right rule id and recovery command.
  - Depends on: E-01
  - Expected outcome: a test suite where every positive fixture is clean and every adversarial fixture triggers exactly the expected rule.
  - Execution state: pending

### Task group 3: draft-readiness detect-and-nudge rule

- [ ] E-03 Add a shared `authoring_placeholders_resolved(plan_text) -> bool` predicate (detects remaining authoring placeholders: `Concern: TODO.`/`Scope: TODO.`/`Scope-Paths: TODO`/`Goal` TODO / `TODO.` E-V bodies from the scaffold at ipd_authoring.py:120-160) and a policy rule `check.ipd-draft-ready-to-review`: a plan at `Status: draft` with NO remaining placeholders is flagged (severity info/advisory) with the exact recovery command `aw ipd set to-review <id6>`; a draft that still has placeholders is silent (correctly still a stub). Surface the SAME rule as a passing-nudge line from `aw ipd lint --phase author` when it passes on a placeholder-free draft. DETECT-AND-NUDGE only: never auto-flip the status (keeps `to-review` an explicit, tool-authored transition).
  - Depends on: E-01
  - Expected outcome: `aw check`/`aw ipd lint --phase author` on a placeholder-free `draft` emits the advance nudge with the `aw ipd set to-review` command; a draft with placeholders emits nothing; no status is auto-changed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `check_engine` (check_engine.py) already composes the per-type validators into a `Drift` list and is consumed by `aw check <type>` - EXTEND it, do not fork; reuse `check_names`/`check_content`/`check_refs`/`check_collisions` and the release/backlog rules.
- `_core.Drift` (artifact_core) is the current finding type; enrich it (or wrap it) rather than introducing a parallel finding type.
- Findings section 9 enumerates the adversarial cases to encode as fixtures.

## Findings

The engine exists; Phase 1 is about GIVING IT A CONTRACT (versioned schema + rich finding shape) and PROVING IT (adversarial fixtures), so downstream layers can depend on stable rule ids and recovery commands.

## Proposed changes (ordered, validatable)

1. `check_engine.py`/`artifact_core.py`: versioned rule registry + enriched finding shape.
2. `cli.py`: `aw check --format json` emits the full shape + schema_version.
3. `check_engine.py`/`ipd_lint.py`/`ipd_authoring.py`: shared `authoring_placeholders_resolved` predicate + `check.ipd-draft-ready-to-review` detect-and-nudge rule; `aw ipd lint --phase author` prints the advance hint on a placeholder-free draft.
4. `tests/`: positive + adversarial fixture corpus + draft-readiness detect/nudge/no-auto-flip cases.

## Deferred / out of scope (with reason)

- Atomic commands (phase 2), event-state (phase 3), hooks (phase 4), CI (phase 5): they CALL this engine but are separate children.

## Scope check

- Over-scope: none.
- Under-scope: none (schema + finding shape + fixtures is the phase-1 deliverable).

## Required tests / validation

- `aw check --format json` output conforms to the documented finding shape (schema_version, rule id, severity, assurance class, observed-vs-required, recovery command, determinism tag).
- Every positive fixture passes clean; every adversarial fixture triggers exactly its expected rule id and recovery command.
- Determinism: repeated runs on the same tree produce identical findings.
- Draft-readiness: `aw check`/`aw ipd lint --phase author` on a placeholder-free `draft` emits `check.ipd-draft-ready-to-review` with the `aw ipd set to-review <id6>` recovery command; a draft that still has authoring placeholders emits nothing; the status is NEVER auto-changed (detect-and-nudge, not auto-flip).

## Spec / documentation sync

- Document the policy schema + finding shape (a spec or docs page); reference the Phase-0 catalog.

## Open questions

### OQ-01: Version the schema separately from the existing check output, or bump a shared schema_version?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Prefer a dedicated policy schema_version so hooks/CI can assert compatibility; reconcile with any existing `aw check` JSON version at implementation.

### OQ-02: What exactly counts as an "authoring placeholder" for the draft-readiness predicate?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Start with the literal scaffold placeholders (`Concern: TODO.`, `Scope: TODO.`, `Scope-Paths: TODO`, `## Goal` TODO body, and `TODO`-bearing E/V leaves from ipd_authoring.py:120-160). Keep the predicate conservative: presence of ANY known scaffold placeholder means still-drafting; absence means ready-to-nudge. Refine the token set in implementation so it does not false-positive on legitimate prose containing the word "TODO".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
