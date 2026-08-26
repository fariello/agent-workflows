# IPD: Optional opt-in pre-commit hook wired by aw install that refuses committing a blocking backlog item closed without a preserved-or-satisfied gate

- Date: 2026-08-25
- Kind: child
- Concern: The child-02 setter gate can be bypassed by hand-editing a backlog file (flip `Status: done`, move it to `done/`) and committing directly, which silently drops a release gate - exactly the hand-edit bypass the findings doc (bu9yij, section 7.7) says a local pre-commit hook should catch. `aw install` should OPTIONALLY (opt-in, not default - per the design decision) wire a local pre-commit hook that refuses to COMMIT a blocking backlog item closed to `done` without a preserved-or-satisfied gate, using the SAME shared predicate as the setter/check so they cannot diverge.
- Scope: Add an opt-in local pre-commit hook mirroring `agent_workflows/hooks/status_untooled_gate.py`: (1) a new hook module (e.g. `agent_workflows/hooks/backlog_blocking_close_gate.py`) whose `check(repo_root)` inspects the STAGED change and, for each backlog item whose staged content shows `Status: done` (or a move into `done/`) while it carries `Blocks-Release` and has no matching tool-history line, delegates to the child-02 `evaluate_blocking_close` predicate (commit-scoped, over the staged tree) and returns exit 1 with a teaching refusal when illegitimate; (2) installer wiring in `agent_workflows/engine.py` so `aw install` OFFERS to install it (interactive) or a flag enables it, fail-closed where the host supports it, opt-out available, idempotent; NOT installed by default. Honest limits documented (local only, not cloned by default, skippable with `--no-verify`; the portable authority is the child-02 `aw check` rule + CI). Adversarial/bypass tests: hand-edit-to-done without gate is refused; with a From-Backlog blocking plan / resolvable evidence / cleared Blocks-Release it passes; a non-blocking item close is unaffected; `--no-verify` documented as the (visible) escape.
- Scope-Paths: agent_workflows/hooks/, agent_workflows/engine.py, agent_workflows/check_engine.py, tests/, AGENTS.md
- Status: executed
- Set: bklggrad
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: f1dhht

## Workflow history
- 2026-08-26 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): opt-in backlog-blocking-close pre-commit hook + installer wiring; product committed 81d9acb (cli.py entry via c84d7ab, decision 04-f1dhht-D2), tests green (test_backlog_blocking_close_gate 12 + full suite 2267), terminal transition post-hoc [Scope reconciliation - in-scope-unmodified AGENTS.md: landed in 81d9acb; in-scope-unmodified agent_workflows/check_engine.py: landed in 81d9acb; in-scope-unmodified agent_workflows/engine.py: landed in 81d9acb; in-scope-unmodified agent_workflows/hooks/: landed in 81d9acb; in-scope-unmodified tests/: landed in 81d9acb]
- 2026-08-26 approved (aw set): status set to approved
- 2026-08-25 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (gate contract) FIXED, PR-002 (AGENTS.md Scope-Paths) FIXED, PR-003 (status) FIXED, PR-004 (commit-time SATISFIED reconstructability) FIXED; cross-IPD note to child 02 (persist SATISFIED evidence citation) recorded in the review report
- 2026-08-25 reviewed (aw set): plan-review: hardened (AGENTS.md Scope-Paths, commit-time SATISFIED reconstructability clarified, full execution-contract gate)

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add an opt-in local pre-commit hook, wired by `aw install`, that refuses to commit a release-blocking backlog item closed to `done` without a preserved-or-satisfied gate, delegating to the child-02 shared predicate so the hook, setter, and `aw check` never diverge. Catches the hand-edit bypass; honest local-only limits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the hook module

- [x] E-02 Add `agent_workflows/hooks/backlog_blocking_close_gate.py` with a `check(repo_root) -> (exit_code, messages)` that inspects the staged change for a backlog item newly showing `Status: done` (or moved into `done/`) that carries `Blocks-Release`, and delegates the legitimacy decision to the child-02 `evaluate_blocking_close` predicate over the staged tree. Mirror `hooks/status_untooled_gate.py` structure (check + main). Document the honest local-only limits in the module docstring. Commit-time legitimacy is reconstructed from PERSISTED state only: HANDOFF (a `From-Backlog` blocking plan present in the tree) and DE-GATED (`Blocks-Release` absent from the staged item) are decidable from the staged tree; the SATISFIED path is honored at commit time ONLY if the evidence citation is durably recorded in the item (e.g. a tool-history/metadata line child 02 writes), since a transient `--evidence` CLI arg is not visible to the hook. Call the predicate WITHOUT an `evidence=` arg so it decides from persisted state.
  - Depends on: none
  - Expected outcome: running the hook with a staged illegitimate blocking close returns exit 1 + a teaching message; a legitimate close via HANDOFF or DE-GATED (both reconstructable from the staged tree) or a non-blocking close returns exit 0. (Cross-IPD: delegates to bklggrad-02's `evaluate_blocking_close`; requires child 02 to persist any SATISFIED evidence citation into the item if commit-time SATISFIED is to be honored - flagged to child 02; ordering tracked in the orchestrator dependency table.)
  - Execution state: performed

### Task group 2: opt-in installer wiring

- [x] E-03 Wire the hook into `agent_workflows/engine.py` install path so `aw install` OFFERS it (interactive prompt) or enables it via an explicit flag; NOT installed by default; idempotent (no duplicate wiring); opt-out honored. Register it in the pre-commit hook chain alongside the existing gates.
  - Depends on: E-02
  - Expected outcome: a fresh install does NOT wire the hook unless accepted/flagged; when enabled, the pre-commit chain invokes it; re-install does not duplicate it.
  - Execution state: performed

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
- The same commit passes when a `From-Backlog` blocking plan exists (HANDOFF) or `Blocks-Release` was cleared in the staged item (DE-GATED) - both reconstructable from the staged tree. If child 02 persists a SATISFIED evidence citation into the item, a commit carrying that persisted citation also passes; a transient CLI-only `--evidence` is NOT visible to the hook and is out of the hook's reach by design.
- A non-blocking item close, and an unrelated commit, are unaffected (exit 0).
- Install: fresh install does not wire the hook unless opted in; opt-in wires it; re-install is idempotent; opt-out removes/does-not-add it.

## Spec / documentation sync

- Document the opt-in hook in `AGENTS.md` (the release-gate section), including the honest local-only limits and `--no-verify` caveat. If an installer doc under `docs/` (e.g. `docs/host-adapters.md`) is also updated, add that path to `Scope-Paths` before executing.

## Open questions

### OQ-01: Should the hook also warn (not block) on blocking->parked at commit time, mirroring child-02's warn?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: The hook's job is the fail-closed `done` case; park/demote warnings are better surfaced by `aw check`/`attention` (non-commit-time). Default: hook gates `done` only, no park/demote warning at commit time.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-02 validates E-02
  - Required evidence: test that the hook refuses (exit 1) a staged hand-edit-to-done of a blocking item with no gate, and passes (exit 0) for each legitimacy path and for a non-blocking close; paste output.
  - Observed evidence: `tests/test_backlog_blocking_close_gate.py::HookBehaviorTests` (all `ok` in `python -m unittest tests.test_backlog_blocking_close_gate -v`, Ran 12 tests OK): `test_refuses_staged_hand_edit_to_done_without_gate` (rc==1, message names the item), `test_passes_handoff` (rc==0, a From-Backlog blocking plan present), `test_passes_degated` (rc==0, staged item carries no Blocks-Release), `test_non_blocking_close_unaffected` (rc==0), `test_no_op_when_nothing_staged` (rc==0; commit-scoped, historical done items grandfathered), `test_main_entry_exit_codes`. The hook (`agent_workflows/hooks/backlog_blocking_close_gate.py`) delegates to `check_engine.check_release_gate_consistency` filtered to `check.blocking-item-closed-without-gate` (the child-02 shared predicate; no re-implemented legitimacy logic), deciding from PERSISTED staged-tree state (no `evidence=` arg). CLI entry `aw backlog-blocking-close-gate` wired in cli.py (committed at HEAD via driver commit c84d7ab; see NOTE re attribution).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: install test: fresh install does not wire the hook unless opted in; opt-in wires it into the pre-commit chain; re-install is idempotent; opt-out honored; paste output.
  - Observed evidence: `tests/test_backlog_blocking_close_gate.py::InstallerWiringTests` (all `ok`): `test_default_setup_does_not_wire_hook` (the default `create_setup_artifacts` path does NOT wire it), `test_optout_writes_nothing` (`install=False` writes nothing), `test_optin_wires_hook` (writes the `backlog-blocking-close-gate` hook entry), `test_reinstall_is_idempotent` (re-run creates nothing; exactly one hook id), `test_appends_to_existing_config_without_clobber` (a user's existing hook preserved, ours appended), `test_dry_run_writes_nothing`. Installer writer `engine.create_backlog_close_gate_hook(repo, install=..., dry_run=...)` mirrors `create_local_leaks_backstop`'s opt-in/no-clobber/idempotent/dry-run semantics; NOT called by the default path.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Child 03 of the `bklggrad` Set; the LAST child. It DEPENDS on child 02 (the `evaluate_blocking_close` predicate it delegates to) - execute 02 (and 01) first. This hook is the bypass-catcher layer, NOT the authority; the authoritative boundary is child 02's `aw check` rule + CI (wired later by the agentadhere Phase-5 child). NOT installed by default; opt-in only.

Execution contract (binds any agent that executes this plan):

1. Open questions: OQ-01 is `Blocking: no` (the hook gates the `done` case only; park/demote warnings are surfaced by `aw check`/`attention`, not at commit time). No blocking question remains. If it becomes blocking, STOP and report.
2. Scope fence: touch ONLY the paths in `Scope-Paths` (`agent_workflows/hooks/`, `engine.py`, `check_engine.py`, `tests/`, `AGENTS.md`) plus this plan's own file. If an installer doc under `docs/` is updated, add it to `Scope-Paths` first. The hook MUST delegate to child 02's `evaluate_blocking_close` (no re-implemented legitimacy logic); it decides from PERSISTED staged-tree state (no transient `--evidence` arg). Do NOT expand scope; if it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when you report tests passed, paste the ACTUAL runner output for each V-item (hook refuses hand-edit-to-done, passes HANDOFF/DE-GATED and non-blocking; install opt-in/idempotent/opt-out). Never claim success you did not run.
4. Commits: commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push. (Note: this plan's own hook, once installed, gates commits; use `--no-verify` only if it spuriously blocks an in-scope commit, and report it.)
5. Lifecycle move on completion: perform the terminal transition via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT hand-edit the terminal transition.

This review and gate are NOT approval: human sign-off (`Status: approved`) is a separate, required step before execution.
