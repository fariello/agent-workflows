# IPD: Phase 4: local git hooks that call the shared checker and emit teaching errors

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 4 + section 7.7: local git hooks give immediate, self-correcting feedback (High confidence as feedback, Med-low as a hard boundary - local, not cloned by default, skippable with `--no-verify`). The toolkit already has two commit-scoped gates (`hooks/status_untooled_gate.py`, `hooks/executed_transition_gate.py`) that delegate to `check_engine` rules, but there is no systematic pre-commit/pre-push layer calling the full phase-1 engine over the staged index + declared scope, and refusals do not uniformly TEACH the recovery path.
- Scope: Add/extend local git hooks that call the SHARED phase-1 engine (never a forked policy): (1) a pre-commit hook that runs the checker against the staged INDEX and the declared scope (Scope-Paths comparison from phase 3), refusing out-of-scope or invariant-violating staged trees with a TEACHING error (name the violated invariant + the exact `aw ...` recovery command, findings 4.4); (2) a pre-push hook that explains missing authorization and prevents accidental pushes (convenience/feedback, NOT an authority boundary); (3) fail-closed for security-sensitive rules where the host supports it; (4) contract tests for each hook (coverage, alternate tool paths, malformed input, disablement, fail-open behavior). Follow the established pattern: each hook `check(repo_root)` delegates to a single `check_engine` rule so hook and `aw check` never diverge (status_untooled_gate.py:33). Honest limits documented (local only, `--no-verify`); the authoritative boundary is phase-5 CI.
- Scope-Paths: agent_workflows/hooks/, agent_workflows/check_engine.py, agent_workflows/engine.py, tests/
- Status: draft
- Set: agentadhere
- Order: 5
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: diundn

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add local pre-commit/pre-push git hooks that call the shared phase-1 engine over the staged index + declared scope and refuse violations with teaching errors (violated invariant + exact recovery command), fail-closed where supported, with honest local-only limits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pre-commit + pre-push hooks

- [ ] E-01 Add/extend a pre-commit hook that runs the phase-1 engine against the staged index + declared scope, refusing out-of-scope/invariant-violating staged trees with a teaching error; add a pre-push hook that explains missing authorization and prevents accidental pushes. Each hook's `check(repo_root)` delegates to a single `check_engine` rule (status_untooled_gate.py:33 pattern); fail-closed for security-sensitive rules where supported.
  - Depends on: none
  - Expected outcome: a violating staged commit is refused with a teaching message; a push without authorization is explained/prevented; hooks reuse the shared engine.
  - Execution state: pending

### Task group 2: contract tests

- [ ] E-02 Add contract tests per hook: coverage, alternate tool paths, malformed input, disablement, and fail-open behavior; assert the teaching message names the invariant + recovery command.
  - Depends on: E-01
  - Expected outcome: each hook passes its contract test matrix.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `hooks/status_untooled_gate.py` (check + main, delegating to `check_engine.check_status_untooled`) and `hooks/executed_transition_gate.py` are the templates; install wiring for hooks lives in `engine.py`.
- Findings 7.7: fail closed for security-sensitive rules where the host supports it; local hooks are feedback, not authority; the authoritative boundary is CI (phase 5).
- Findings 5.3: a pre-commit hook can inspect the staged INDEX and enforce "staged paths within declared scope" but cannot reliably reconstruct the exact command (`git add -A`); enforce the invariant, not the syntax.

## Findings

The engine + two gate precedents exist; Phase 4 generalizes to a pre-commit/pre-push layer over the full engine with uniform teaching errors, honestly scoped as local feedback.

## Proposed changes (ordered, validatable)

1. `hooks/`: pre-commit (staged index + scope) and pre-push (authorization) delegating to `check_engine`.
2. `engine.py`: install wiring for the hooks (idempotent).
3. `tests/`: per-hook contract matrix + teaching-message assertions.

## Deferred / out of scope (with reason)

- Treating hooks as an authority boundary: explicitly NOT (local, skippable) - CI is the authority (phase 5).
- Host-specific pre-tool adapters (Claude/Codex/etc.): phase 6 (deferred set).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- A staged commit violating an invariant / declared scope is refused (exit 1) with a teaching message naming the invariant + recovery command.
- A pre-push without authorization is prevented/explained.
- Contract matrix per hook: coverage, alternate paths, malformed input, disablement, fail-open; security-sensitive rules fail closed where supported.
- Hook and `aw check` never diverge (same rule).

## Spec / documentation sync

- Document the hooks + honest local-only limits (`--no-verify`) in the installer docs and AGENTS.md.

## Open questions

### OQ-01: Install these hooks by default, or opt-in like the bklggrad hook?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Likely default-on for the pre-commit engine check (core feedback), opt-in for stricter gates; align with the bklggrad hook decision (opt-in) at implementation.

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


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
