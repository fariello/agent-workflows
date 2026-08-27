# IPD: Opt-in commit-scoped ipd-dependency-statement-gate hook delegating to the shared predicate

- Date: 2026-08-27
- Kind: child
- Concern: The child-02 `aw check`/lint enforcement can be bypassed by hand-editing an IPD's `Item-Dependencies` (or staging a malformed/cyclic statement) and committing directly. Spec 25kzda (2.10) calls for an OPT-IN, commit-scoped, type-scoped pre-commit hook that catches this at commit time, delegating to the SAME shared evaluator so hook and check never diverge - exactly the bklggrad `backlog-blocking-close-gate` / existing `ipd-status-untooled-gate` model.
- Scope: Add an opt-in local pre-commit hook `ipd-dependency-statement-gate`, mirroring `hooks/backlog_blocking_close_gate.py` / `hooks/status_untooled_gate.py`: (1) a hook module whose `check(repo_root) -> (exit, messages)` inspects the STAGED diff, and for each staged `.ipd.md` evaluates its dependency statement over the staged overlay + HEAD via the child-02 evaluator, refusing (exit 1) only when a staged IPD is malformed, unresolved-where-blocking, dangling, ambiguous, or introduces/participates in a cycle - printing the same rule IDs + recovery commands as `aw check`; (2) register a top-level shim verb (like `ipd-status-untooled-gate`) so the hook can invoke it; (3) opt-in installer wiring (`aw hooks install ipd-dependency-statement-gate`, or the existing hook-install mechanism) - NOT installed by default; idempotent; opt-out honored. Honest local-only limits documented (local, not cloned by default, `--no-verify` bypasses; `aw check`/CI is the portable authority). Never blocks an unrelated commit on a pre-existing finding in a file it did not touch (commit-scoped).
- Scope-Paths: agent_workflows/hooks/, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/engine.py, tests/
- Status: draft
- Set: ipddeps
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: mp88bl

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add an opt-in, commit-scoped, type-scoped `ipd-dependency-statement-gate` pre-commit hook that refuses a staged IPD with a malformed/unresolved/dangling/ambiguous/cyclic dependency statement, delegating to the child-02 shared evaluator so hook and `aw check` never diverge; honest local-only limits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the hook module + shim

- [ ] E-01 Add `hooks/ipd_dependency_statement_gate.py` (`check(repo_root) -> (exit, messages)`) inspecting the staged diff; for each staged `.ipd.md`, evaluate its dependency statement over the staged overlay + HEAD via the child-02 evaluator; refuse (exit 1) only on a staged malformed/unresolved-blocking/dangling/ambiguous/cyclic statement, printing the same rule IDs + recovery commands. Register the top-level shim verb (like `ipd-status-untooled-gate`). Document local-only limits.
  - Depends on: none
  - Expected outcome: hook exits 1 with a teaching message on a staged invalid/cyclic statement; exits 0 on a valid one or an unrelated commit.
  - Execution state: pending

### Task group 2: opt-in install wiring

- [ ] E-02 Wire opt-in installation (`aw hooks install ipd-dependency-statement-gate` or the existing hook-install mechanism): NOT default; idempotent; opt-out honored; registered in the pre-commit chain alongside the existing gates.
  - Depends on: E-01
  - Expected outcome: fresh install does not add the hook unless opted in; opt-in wires it; re-install idempotent; opt-out removes/does-not-add.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `hooks/backlog_blocking_close_gate.py` and `hooks/status_untooled_gate.py` are the templates: commit-scoped `check(repo_root)` delegating to ONE `check_engine` rule; a top-level shim verb (`backlog-blocking-close-gate`, `ipd-status-untooled-gate`) is the hook entry point; opt-in install; `aw check`/CI is the backstop.
- Commit-scoping: only staged `.ipd.md` files are examined; never block an unrelated commit on a pre-existing finding in a file it did not touch.

## Findings

Correctness reduces to "delegate to child-02's evaluator over the staged tree"; the risk is commit-scoping (reading staged content) + install idempotency, not the dependency logic (which lives in child 02).

## Proposed changes (ordered, validatable)

1. `hooks/ipd_dependency_statement_gate.py`: staged-diff inspector delegating to the evaluator.
2. `cli.py`: the top-level shim verb.
3. `engine.py`: opt-in install wiring (idempotent, opt-out), pre-commit chain registration.
4. `tests/`: staged invalid/cyclic refused; valid/unrelated passes; commit-scoping; install opt-in/idempotency; `--no-verify` escape documented.

## Deferred / out of scope (with reason)

- The evaluator + `aw check`/lint rules: child 02 (dependency).
- CI enforcement: the portable authority is child-02's `aw check` rule (CI integration belongs to the runner/CI program, not this hook).

## Scope check

- Over-scope: none.
- Under-scope: none (hook + shim + opt-in install is the complete bypass-catcher deliverable).

## Required tests / validation

- A staged commit adding/editing an IPD to a malformed or cyclic `Item-Dependencies` is REFUSED (exit 1) with the matching rule ID + recovery command.
- A staged valid statement, and an unrelated commit, pass (exit 0).
- Commit-scoped: a pre-existing invalid statement in an untouched file does not block an unrelated commit.
- Install: fresh install does not wire the hook unless opted in; opt-in wires it; re-install idempotent.

## Spec / documentation sync

- Document the opt-in hook + `--no-verify` caveat in the installer docs / AGENTS.md release-gate/hook section.

## Open questions

### OQ-01: Should the hook block on `unresolved` at commit time, or only on structurally invalid/cyclic statements?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: `unresolved` on a draft is legitimate (honest stub); blocking it at commit would prevent committing work-in-progress drafts. Default: hook refuses only malformed/dangling/ambiguous/cyclic (and unresolved only where the staged plan is simultaneously advancing to a blocking phase); plain draft `unresolved` commits are allowed. Finalize in implementation, consistent with child 02's phase matrix.

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
