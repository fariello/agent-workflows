# IPD: Phase 2: atomic aw work/test/commit/finish primitives that produce evidence at the action boundary

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 2 + section 4.3/7.4: reliable adherence requires replacing a sequence of remembered duties with a smaller number of atomic actions that make the compliant path the EASY path and produce evidence at the action boundary. Today the workflow is a chain of separate remembered steps (start work, run tests, commit path-scoped, finalize), each an independent failure opportunity. There is no `aw work`/`aw test`/`aw commit`/`aw finish` wrapper that validates-then-acts and captures evidence.
- Scope: Add atomic workflow primitives (findings 7.4), each validating before mutating and calling the phase-1 `aw check` engine: (1) `aw work begin <ipd>` - validate the plan and create/associate an isolated worktree; (2) `aw test <ipd> -- <cmd>` - execute the test, capture stdout/stderr + exit + env metadata, bind evidence to the tree/commit; (3) `aw commit <ipd> -- <paths>` - compute allowed paths, refuse out-of-scope staged changes, run the checker, commit ONLY declared scope (REUSE the selfcommit `git_commit_helper` - no forked commit path); (4) `aw finish <ipd>` - check required evidence and perform valid non-authoritative transitions. Raw actions either blocked (where interception is reliable) or caught by a later deterministic failure; the wrapper must be the faster path. This child builds the primitives + their evidence capture; it does NOT build event-derived state (phase 3), hooks (phase 4), or CI (phase 5). Honest limit: local evidence is forgeable by a privileged local agent (findings 6.6); CI reproduction (phase 5) is the High-confidence boundary.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/work_cmd.py, agent_workflows/git_commit_helper.py, agent_workflows/worktree_lease.py, agent_workflows/ipd_lifecycle.py, tests/
- Status: draft
- Set: agentadhere
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 8dto0g

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add atomic `aw work begin` / `aw test` / `aw commit` / `aw finish` primitives that validate-then-act via the phase-1 engine and capture evidence at the action boundary, making the compliant path the easy path. `aw commit` reuses the selfcommit path-scoped helper.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: work + test

- [ ] E-01 Add `aw work begin <ipd>` (validate plan via `aw check`, create/associate an isolated worktree via `worktree_lease`) and `aw test <ipd> -- <cmd>` (run the command, capture stdout/stderr/exit/env, bind evidence to the tree/commit).
  - Depends on: none
  - Expected outcome: `aw work begin` validates + sets up a worktree; `aw test` runs and records bound evidence.
  - Execution state: pending

### Task group 2: commit + finish

- [ ] E-02 Add `aw commit <ipd> -- <paths>` computing allowed scope, refusing out-of-scope staged changes, running the checker, and committing ONLY declared scope by REUSING the selfcommit `git_commit_helper` (no forked commit path). Add `aw finish <ipd>` checking required evidence and performing valid non-authoritative transitions.
  - Depends on: E-01
  - Expected outcome: `aw commit` commits only in-scope paths and refuses out-of-scope; `aw finish` transitions only when evidence is present.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `worktree_lease.py` already manages isolated worktrees (and lists `.aw/records/runs/` as ignored) - reuse for `aw work begin`.
- `ipd_lifecycle.py` performs the finalize transition + path-scoped commit today; `aw finish`/`aw commit` should build on it, not duplicate.
- The selfcommit `git_commit_helper` (selfcommit set) is the path-scoped committer to reuse for `aw commit` - creates a cross-set dependency; sequence selfcommit first.

## Findings

Each primitive validates-then-acts using the phase-1 engine, turning remembered duties into one command that also emits evidence. The commit primitive is the highest-leverage (enforces path-scope deterministically), and it must reuse the shared helper.

## Proposed changes (ordered, validatable)

1. `work_cmd.py` (or similar) + `cli.py`: `aw work begin`, `aw test`, `aw commit`, `aw finish`.
2. Reuse `worktree_lease`, `git_commit_helper`, `ipd_lifecycle`, and the phase-1 engine.
3. `tests/`: per-command behavior + evidence capture + scope refusal.

## Deferred / out of scope (with reason)

- Event-derived state (phase 3), hooks (phase 4), CI (phase 5): separate children.
- Trusted CI test runner / non-forgeable evidence (phase 7): deferred set; local evidence here is honestly labeled forgeable.

## Scope check

- Over-scope: none.
- Under-scope: none (the four primitives + evidence capture are the phase-2 deliverable).

## Required tests / validation

- `aw work begin` validates the plan and creates/associates a worktree.
- `aw test` captures command/exit/output/env and binds it to a tree/commit.
- `aw commit` commits only declared-scope paths, refuses out-of-scope staged changes, and uses the shared helper (no `add -A`, no push).
- `aw finish` performs non-authoritative transitions only when required evidence exists; refuses otherwise.

## Spec / documentation sync

- Document the atomic commands in AGENTS.md (make them the default path) and each `--help`.

## Open questions

### OQ-01: Should `aw commit` hard-depend on the selfcommit helper, or ship a minimal internal committer if selfcommit has not landed?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Prefer a hard dependency on the selfcommit helper (one commit path); sequence selfcommit before this child. If scheduling forces it, a thin internal committer can be replaced later, but avoid a second permanent path.

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
