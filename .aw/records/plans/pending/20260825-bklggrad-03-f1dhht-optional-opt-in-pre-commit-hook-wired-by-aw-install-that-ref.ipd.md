# IPD: Optional opt-in pre-commit hook wired by aw install that refuses committing a blocking backlog item closed without a preserved-or-satisfied gate

- Date: 2026-08-25
- Kind: child
- Concern: The child-02 setter gate can be bypassed by hand-editing a backlog file (flip `Status: done`, move it to `done/`) and committing directly, which silently drops a release gate - exactly the hand-edit bypass the findings doc (bu9yij, section 7.7) says a local pre-commit hook should catch. `aw install` should OPTIONALLY (opt-in, not default - per the design decision) wire a local pre-commit hook that refuses to COMMIT a blocking backlog item closed to `done` without a preserved-or-satisfied gate, using the SAME shared predicate as the setter/check so they cannot diverge.
- Scope: Add an opt-in local pre-commit hook mirroring `agent_workflows/hooks/status_untooled_gate.py`: (1) a new hook module (e.g. `agent_workflows/hooks/backlog_blocking_close_gate.py`) whose `check(repo_root)` inspects the STAGED change and, for each backlog item whose staged content shows `Status: done` (or a move into `done/`) while it carries `Blocks-Release` and has no matching tool-history line, delegates to the child-02 `evaluate_blocking_close` predicate (commit-scoped, over the staged tree) and returns exit 1 with a teaching refusal when illegitimate; (2) installer wiring in `agent_workflows/engine.py` so `aw install` OFFERS to install it (interactive) or a flag enables it, fail-closed where the host supports it, opt-out available, idempotent; NOT installed by default. Honest limits documented (local only, not cloned by default, skippable with `--no-verify`; the portable authority is the child-02 `aw check` rule + CI). Adversarial/bypass tests: hand-edit-to-done without gate is refused; with a From-Backlog blocking plan / resolvable evidence / cleared Blocks-Release it passes; a non-blocking item close is unaffected; `--no-verify` documented as the (visible) escape.
- Scope-Paths: agent_workflows/hooks/, agent_workflows/engine.py, agent_workflows/check_engine.py, tests/
- Status: draft
- Set: bklggrad
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: f1dhht

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add an opt-in local pre-commit hook, wired by `aw install`, that refuses to commit a release-blocking backlog item closed to `done` without a preserved-or-satisfied gate, delegating to the child-02 shared predicate so the hook, setter, and `aw check` never diverge. Catches the hand-edit bypass; honest local-only limits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the hook module

- [ ] E-02 Add `agent_workflows/hooks/backlog_blocking_close_gate.py` with a `check(repo_root) -> (exit_code, messages)` that inspects the staged change for a backlog item newly showing `Status: done` (or moved into `done/`) that carries `Blocks-Release`, and delegates the legitimacy decision to the child-02 `evaluate_blocking_close` predicate over the staged tree. Mirror `hooks/status_untooled_gate.py` structure (check + main). Document the honest local-only limits in the module docstring.
  - Depends on: none
  - Expected outcome: running the hook with a staged illegitimate blocking close returns exit 1 + a teaching message; a legitimate or non-blocking close returns exit 0. (Cross-IPD: delegates to bklggrad-02's `evaluate_blocking_close`; ordering tracked in the orchestrator dependency table.)
  - Execution state: pending

### Task group 2: opt-in installer wiring

- [ ] E-03 Wire the hook into `agent_workflows/engine.py` install path so `aw install` OFFERS it (interactive prompt) or enables it via an explicit flag; NOT installed by default; idempotent (no duplicate wiring); opt-out honored. Register it in the pre-commit hook chain alongside the existing gates.
  - Depends on: E-02
  - Expected outcome: a fresh install does NOT wire the hook unless accepted/flagged; when enabled, the pre-commit chain invokes it; re-install does not duplicate it.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `hooks/status_untooled_gate.py` is the exact template: a commit-scoped `check(repo_root)` delegating to a single `check_engine` rule so hook and check never diverge; `main()` prints refusals to stderr and exits 0/1.
- Existing terminal-transition pre-commit gate (`hooks/executed_transition_gate.py`) and the install wiring for these hooks show how the pre-commit chain is registered by the installer.
- Findings bu9yij section 7.7: local hooks are convenience/early-feedback and MUST fail closed for security-sensitive rules where the host supports it; the authoritative boundary is the `aw check` rule + CI, never the local hook alone.

## Findings

The hook is the bypass-catcher layer, not the authority. Its correctness reduces to "delegate to the child-02 predicate over the staged tree", so the risk is in commit-scoping (reading staged content) and install idempotency, not in the legitimacy logic.

## Proposed changes (ordered, validatable)

1. `hooks/backlog_blocking_close_gate.py`: staged-change inspector delegating to `evaluate_blocking_close`.
2. `engine.py`: opt-in install wiring (offer/flag, idempotent, opt-out), pre-commit chain registration.
3. `tests/`: hand-edit-to-done refused; each legitimacy path passes; non-blocking unaffected; install opt-in/idempotency; `--no-verify` escape documented.

## Deferred / out of scope (with reason)

- The predicate + setter/check gate: child 02 (dependency).
- CI/remote enforcement: out of scope here (local hook only); the portable authority is child-02's `aw check` rule, integrated into CI by the agentadhere Phase-5 child, not this set.

## Scope check

- Over-scope: none.
- Under-scope: none (hook + opt-in install wiring is the complete deliverable).

## Required tests / validation

- A staged commit that hand-edits a blocking backlog item to `done` with no preserved gate is REFUSED (exit 1) with a teaching message.
- The same commit passes when a `From-Backlog` blocking plan exists, or `--evidence`-style artifact is present, or `Blocks-Release` was cleared.
- A non-blocking item close, and an unrelated commit, are unaffected (exit 0).
- Install: fresh install does not wire the hook unless opted in; opt-in wires it; re-install is idempotent; opt-out removes/does-not-add it.

## Spec / documentation sync

- Document the opt-in hook in the installer docs and AGENTS.md (the release-gate section), including the honest local-only limits and `--no-verify` caveat.

## Open questions

### OQ-01: Should the hook also warn (not block) on blocking->parked at commit time, mirroring child-02's warn?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: The hook's job is the fail-closed `done` case; park/demote warnings are better surfaced by `aw check`/`attention` (non-commit-time). Default: hook gates `done` only, no park/demote warning at commit time.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: test that the hook refuses (exit 1) a staged hand-edit-to-done of a blocking item with no gate, and passes (exit 0) for each legitimacy path and for a non-blocking close; paste output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: install test: fresh install does not wire the hook unless opted in; opt-in wires it into the pre-commit chain; re-install is idempotent; opt-out honored; paste output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
