# IPD: Opt-in commit-scoped ipd-dependency-statement-gate hook delegating to the shared predicate

- Date: 2026-08-27
- Kind: child
- Concern: The child-02 `aw check`/lint enforcement can be bypassed by hand-editing an IPD's `Item-Dependencies` (or staging a malformed/cyclic statement) and committing directly. Spec 25kzda (2.10) calls for an OPT-IN, commit-scoped, type-scoped pre-commit hook that catches this at commit time, delegating to the SAME shared evaluator so hook and check never diverge - exactly the bklggrad `backlog-blocking-close-gate` / existing `ipd-status-untooled-gate` model.
- Scope: Add an opt-in local pre-commit hook `ipd-dependency-statement-gate`, mirroring `hooks/backlog_blocking_close_gate.py` / `hooks/status_untooled_gate.py`: (1) a hook module whose `check(repo_root) -> (exit, messages)` inspects the STAGED diff, and for each staged `.ipd.md` evaluates its dependency statement over the staged overlay + HEAD via the child-02 evaluator, refusing (exit 1) only when a staged IPD is malformed, unresolved-where-blocking, dangling, ambiguous, or introduces/participates in a cycle - printing the same rule IDs + recovery commands as `aw check`; (2) register a top-level shim verb (like `ipd-status-untooled-gate`) so the hook can invoke it; (3) opt-in installer wiring (`aw hooks install ipd-dependency-statement-gate`, or the existing hook-install mechanism) - NOT installed by default; idempotent; opt-out honored. Honest local-only limits documented (local, not cloned by default, `--no-verify` bypasses; `aw check`/CI is the portable authority). Never blocks an unrelated commit on a pre-existing finding in a file it did not touch (commit-scoped).
- Scope-Paths: agent_workflows/hooks/, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/engine.py, tests/
- Status: approved
- Set: ipddeps
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: mp88bl
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-301/302/303/304 fixed, PR-305 considered (no split)

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add an opt-in, commit-scoped, type-scoped `ipd-dependency-statement-gate` pre-commit hook that refuses a staged IPD with a malformed/unresolved/dangling/ambiguous/cyclic dependency statement, delegating to the child-02 shared evaluator so hook and `aw check` never diverge; honest local-only limits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the hook module + shim

- [ ] E-01 Add `hooks/ipd_dependency_statement_gate.py` with the exact `check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]` + `main(argv)` shape of `hooks/status_untooled_gate.py` (status_untooled_gate.py:33,48). INTERFACE NOTE (commit-scoping location): the existing analog delegates to a check_engine rule (`check_status_untooled`) that is ITSELF commit-scoped, but child 02's evaluator is REPO-WIDE (repo snapshot + IPD path set + phase). So this hook must (a) collect the STAGED `.ipd.md` paths, (b) build a STAGED-OVERLAY snapshot (staged blob content over HEAD) for resolution/graph context, and (c) call the child-02 evaluator with that overlay + the staged IPD path set, then keep only findings whose location is a staged file. If child 02's evaluator does not accept a staged-overlay snapshot + explicit path set, STOP - that is a child-02 interface requirement to reconcile before this child (strict order 02 -> 03), NOT a place to reimplement the dependency logic here. Refuse (exit 1) only on a staged malformed/dangling/ambiguous/cyclic statement (and `unresolved` only where the staged plan is simultaneously advancing to a blocking phase - see OQ-01), printing the SAME `check.ipd-dependency-*` rule IDs + recovery commands as `aw check`. Register the top-level shim verb (cli.py `add_parser` + dispatch, mirroring `ipd-status-untooled-gate` at cli.py:2659,7299). Document the honest local-only limits (local, not cloned by default, `--no-verify` bypasses, `aw check`/CI is the portable authority) in the module docstring, mirroring status_untooled_gate.py:15-24.
  - Depends on: none
  - Expected outcome: hook exits 1 with a teaching message (matching rule ID + recovery command) on a staged invalid/cyclic statement; exits 0 (fast no-op) on a valid statement, an unrelated commit, or a pre-existing finding in an UNTOUCHED file.
  - Execution state: pending

### Task group 2: opt-in install wiring

- [ ] E-02 Wire opt-in installation by CLONING the tested `engine.create_backlog_close_gate_hook(repo_root, use_git, *, install, dry_run=False)` (engine.py:4456) precedent: a new `engine.create_dependency_gate_hook(...)` with the same `install`/`dry_run` params, idempotent (re-run does not duplicate), no-clobber (never edits the rest of a user's `.pre-commit-config.yaml`), opt-out honored (`install=False` writes nothing), returning `{created,skipped,notes}`; plus the hook-block/template constants mirroring `_BACKLOG_CLOSE_GATE_HOOK_ID`/`_BACKLOG_CLOSE_GATE_PRECOMMIT_BLOCK` (engine.py:4424-4449). It is NOT added to the default `PRE_COMMIT_HOOKS_BLOCK` setup path. NAMING DECISION (resolves the spec's `aw hooks install ipd-dependency-statement-gate` vs. the current mechanism): there is no `aw hooks` verb today (verified: `aw hooks --help` errors); the existing opt-in surface is the Python function above. Clone THAT function (the shippable, tested pattern) as the install mechanism for this Set. Adding a user-facing `aw hooks install <id>` CLI verb (the spec 2.10 wording) is a SEPARATE surface-redesign concern - if the human wants it in this Set, do it as an additional E-item; otherwise defer it and document the function as the opt-in mechanism.
  - Depends on: E-01
  - Expected outcome: default setup does NOT wire the hook; `create_dependency_gate_hook(..., install=True)` wires it (creates config if absent, appends block if config exists without it); re-run is idempotent (skipped, no duplicate); `install=False` writes nothing; `dry_run=True` reports without writing.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `hooks/status_untooled_gate.py` is the closest template (IPD/plan-scoped, staged-diff based): `check(repo_root: Optional[Path]=None) -> Tuple[int, List[str]]` + `main(argv)` (status_untooled_gate.py:33,48), delegating to ONE `check_engine` rule, fast no-op when nothing relevant is staged, honest local-only limits in the docstring (status_untooled_gate.py:15-24). Shim-verb registration: cli.py `add_parser` (cli.py:2659) + dispatch (cli.py:7299).
- INTERFACE DIFFERENCE from that template: `status_untooled_gate` delegates to `check_status_untooled`, a rule that is itself commit-scoped. Child 02's dependency evaluator is REPO-WIDE, so THIS hook owns the commit-scoping: build the staged overlay + staged IPD path set and pass them to the evaluator, then keep only findings on staged files (see E-01). This is an interface requirement on child 02, not new dependency logic here.
- Opt-in install precedent: `engine.create_backlog_close_gate_hook(repo_root, use_git, *, install, dry_run=False)` (engine.py:4456) - idempotent, no-clobber, opt-out, `{created,skipped,notes}`; NOT in the default setup path. `aw hooks install` does NOT exist yet (see E-02 naming decision).
- Commit-scoping: only staged `.ipd.md` files are examined; never block an unrelated commit on a pre-existing finding in a file it did not touch.

## Findings

Correctness reduces to "delegate to child-02's evaluator over the staged tree"; the risk is commit-scoping (reading staged content) + install idempotency, not the dependency logic (which lives in child 02).

## Proposed changes (ordered, validatable)

1. `hooks/ipd_dependency_statement_gate.py`: staged-overlay inspector delegating to the child-02 evaluator (clone `status_untooled_gate.py` shape).
2. `cli.py`: the top-level shim verb (`add_parser` + dispatch, mirroring `ipd-status-untooled-gate`).
3. `engine.py`: `create_dependency_gate_hook` opt-in install (clone `create_backlog_close_gate_hook`) + hook-block/template constants; NOT in the default setup path.
4. `check_engine.py`: only if child 02's evaluator needs a thin staged-overlay adapter entry point (no dependency-rule logic here).
5. `tests/`: staged invalid/cyclic refused with matching rule ID; valid/unrelated/untouched-file passes; commit-scoping; install opt-in/idempotency/dry-run/opt-out; `--no-verify` escape documented.

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
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `unresolved` on a draft is legitimate (honest stub); blocking it at commit would prevent committing work-in-progress drafts. RESOLVED (see gate "Open questions resolved"): hook refuses only malformed/dangling/ambiguous/cyclic, and `unresolved` ONLY where the staged plan is simultaneously advancing to a blocking phase; plain draft `unresolved` commits are allowed. Consistent with child 02's phase matrix.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: A pytest/git transcript over a temp repo shows: (a) staging an IPD whose `Item-Dependencies` is MALFORMED -> hook `check()` returns exit 1 with the `check.ipd-dependency-malformed` rule ID + its recovery command in the message; (b) staging IPDs that form an IPD->IPD CYCLE -> exit 1 with `check.ipd-dependency-cycle`; (c) staging a DANGLING edge -> exit 1 with `check.ipd-dependency-dangling`; (d) staging a VALID statement -> exit 0; (e) an UNRELATED commit (no staged `.ipd.md`) -> exit 0 fast no-op; (f) COMMIT-SCOPING: a pre-existing invalid statement in an UNTOUCHED file does NOT block a commit that stages only an unrelated file -> exit 0; (g) the messages/rule IDs are byte-identical to what `aw check` prints for the same fixture (proving delegation to the one shared evaluator, no divergence). Paste each transcript + exit code. Falsifiable: the hook reporting a finding on an untouched file, or a rule ID differing from `aw check`, fails.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A pytest exercising `create_dependency_gate_hook` shows: default setup (`aw setup`/the normal path) does NOT contain `ipd-dependency-statement-gate` in `.pre-commit-config.yaml`; `install=True` on a repo with no config CREATES the config with the hook; `install=True` on a repo with an existing config APPENDS the block without editing the rest; a SECOND `install=True` is idempotent (skipped, no duplicate id); `install=False` writes nothing; `dry_run=True` reports intended changes without writing. Paste the test output and the resulting config block. Also confirm the module docstring documents the `--no-verify` bypass + `aw check`/CI backstop.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Open questions resolved

- OQ-01 (block on `unresolved` at commit time, or only structurally invalid/cyclic): RESOLVED, consistent with child 02's phase matrix (spec 2.10) - a plain draft carrying `unresolved` is a legitimate honest stub and MUST be committable, so the hook refuses only malformed/dangling/ambiguous/cyclic, and refuses `unresolved` ONLY when the staged plan is simultaneously advancing to a blocking phase (its staged `Status` moves to `to-review`/`reviewed`/`approved` or later). Blocking a plain work-in-progress `unresolved` commit is explicitly NOT done. Not a blocker. See OQ-01 above.

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` (`hooks/`, `check_engine.py`, `cli.py`, `engine.py`, `tests/`). This child delivers the hook module + shim verb + opt-in install ONLY. It MUST delegate to child 02's (`ovbnyq`) shared evaluator - do NOT reimplement any parse/resolve/graph/cycle logic here; the only new logic is staged-overlay collection + commit-scoping + install wiring. If child 02's evaluator symbol is absent or does not accept a staged-overlay snapshot + path set, STOP (strict order 01 -> 02 -> 03; 02 must land first). Do NOT add CI enforcement (the portable authority is child 02's `aw check` rule). If a change needs a file outside `Scope-Paths`, STOP and report.
- One-predicate rule (hard MUST): the hook calls the SAME child-02 evaluator that `aw check`/`aw ipd lint` call; a grep must show no duplicated dependency parse/resolve/graph logic in `hooks/`. The V-01 byte-identical-message check proves this.
- Honesty rule (hard MUST): when a V-item claims the hook refused/passed or the suite is green, paste the ACTUAL runner output (the real `pytest`/hook-invocation/`git commit` transcript + exit code); never claim a pass you did not run.
- Commit rule: commit ONLY files this child changed, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).
