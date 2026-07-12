# IPD: Unify the two install orchestrators behind one canonical path (root cause of the CLI drift)

- Date: 2026-07-12
- Concern: architecture / single-source-of-truth (P8) / drift prevention. `engine.main()` and
  `cli._run_install` are TWO hand-maintained orchestrators of the SAME install operation. The shared
  core `install_into_repo` returns a result dict and does NOT itself run the pre-flight
  (`run_git_diagnostics`), the summary (`print_summary`), or the commit prompt
  (`prompt_and_run_commit`) - each caller re-adds those around it. That is exactly how the 1.2.1 bug
  (IPD 1837-01: `aw install` missing `run_git_diagnostics`) arose: a step added to one orchestrator was
  never mirrored into the other. As long as two orchestrators exist, this class of drift will recur.
- Scope: `agent_workflows/engine.py` + `agent_workflows/cli.py`: extract ONE canonical install
  orchestrator (a single function that runs pre-flight -> install_into_repo -> summary -> commit prompt,
  with parameters for interactivity/dry-run/yes) that BOTH `engine.main()` (used by the deprecated
  `install-workflows.py`) and `cli._run_install` / `_install_all` / the `setup` flow call. Tests proving
  both entry points drive the identical sequence. Docs/DECISIONS. Internal refactor with NO intended
  user-facing behavior change; target a MINOR release (1.3.0) because it is a non-trivial internal
  change, not a patch.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised during /plan-review-long of IPD
  1837-01 when the maintainer asked whether the CLI and installer "should have a separate code base".
  Root-caused the opposite: they are duplicated orchestrators (not separate enough), which is the P8
  violation that produced the drift. 1837-01 patches the symptom for 1.2.1; this IPD removes the root
  cause for 1.3.0. Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- `install_into_repo` (engine.py:2471) does file writes + returns a dict; it does NOT call
  `run_git_diagnostics`, `print_summary`, or `prompt_and_run_commit` (verified: none appear in its
  body 2471-2517). Its docstring even says it "reuses the exact same engine steps as the single-repo
  `run()` path" - acknowledging a parallel path exists.
- `engine.main()` (engine.py:2654; install loop ~2585-2650) orchestrates: `run_git_diagnostics` ->
  inlined install steps (install_all/prune_stale/update_agents_pointer/gitignore/three README
  ensurers/create_setup_artifacts/save_created_files_record/prune_old_backups) -> `print_summary` ->
  `prompt_and_run_commit`. This INLINES the sequence rather than calling `install_into_repo`.
- `cli._run_install` (cli.py:300) orchestrates: `_preflight_warnings` (NOT run_git_diagnostics) +
  `_confirm` -> `install_into_repo` -> `print_summary` -> `prompt_and_run_commit`.
- So there are effectively TWO install sequences: engine.main's inlined one, and the
  install_into_repo + CLI-wrapper one. They share leaf helpers but not orchestration. Divergences found
  so far: the pre-flight (run_git_diagnostics vs _preflight_warnings) and, subtly, engine.main inlines
  create_setup_artifacts/README-ensurers while install_into_repo does its own set (must be reconciled
  to confirm they are actually identical - a review-time TODO for this IPD).
- 1837-01 (reviewed, 1.2.1) will add run_git_diagnostics to the CLI paths as a SYMPTOM patch. This IPD
  supersedes that patch's approach by making a single orchestrator, so after this lands the CLI's
  bespoke pre-flight wiring is replaced by the shared path. Sequencing: 1837-01 ships first (fast fix);
  this refactor lands on top and should PRESERVE 1837-01's behavior (and its tests) while removing the
  duplication.
- Zero-dep, stdlib-only project; 215 tests; the install path is the most-tested surface
  (test_installer.py, test_cli.py, test_setup_artifacts.py) - a good safety net for a refactor.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Extract one canonical orchestrator.** Introduce a single function (e.g.
   `engine.install_orchestrated(plan_or_args, *, interactive, run_diagnostics=True) -> result` OR grow
   `install_into_repo` to optionally run the full sequence) that performs: pre-flight
   (`run_git_diagnostics` when interactive) -> the install steps -> `print_summary` ->
   `prompt_and_run_commit`. It must reproduce today's `engine.main()` single-repo behavior EXACTLY.
2. **Route ALL entry points through it.** `engine.main()` (and thus `install-workflows.py`),
   `cli._run_install`, `cli._install_all`, and the `setup` install flow all call the one orchestrator.
   Remove the CLI's bespoke pre-flight/commit wiring in favor of the shared path (subsuming 1837-01's
   change once this lands). Keep the CLI-only concerns that are genuinely CLI-specific
   (multi-repo loop, per-repo isolation, `_preflight_warnings` would-downgrade/not-a-repo notices).
3. **Reconcile any latent step differences** between engine.main's inlined sequence and
   install_into_repo (e.g. confirm both run the same README-ensurers / setup-artifacts / backup-prune
   steps). Any real difference found is itself a drift bug to fix here (record each).
4. **Tests: prove single-source.** Add tests asserting BOTH entry points (engine.main path and the CLI
   path) produce the same install result + invoke the same pre-flight/summary/commit sequence (spy the
   orchestrator or assert on observable effects). This is the structural guard against future drift.
   Preserve all 1837-01 tests (diagnostics called; abort; non-interactive not blocked).
5. **Docs + DECISIONS.** DECISIONS entry (next free number) recording the two-orchestrators root cause,
   the unification, and that it supersedes 1837-01's symptom wiring. Note in ARCHITECTURE if the install
   flow is described there. Ship in 1.3.0 (internal refactor, no user-facing behavior change intended,
   but non-trivial -> MINOR, cut via release-review Section 9 from a clean tag).

## Deferred / out of scope

- Any user-facing behavior CHANGE (this is a no-behavior-change refactor; if a behavior difference is
  discovered, it is a separate finding, not silently altered).
- The 1837-01 symptom patch itself (ships first for 1.2.1; this refactor lands after and subsumes it).
- Redesigning `run_git_diagnostics`, `print_summary`, or `prompt_and_run_commit` internals.

## Open questions (v1 leans for review)

1. Shape of the canonical orchestrator: grow `install_into_repo` (add optional interactive
   pre-flight/summary/commit params) vs. a NEW `install_orchestrated()` that wraps it? (Lean: a new
   wrapper `install_orchestrated()` so `install_into_repo` stays the pure, batch-friendly, dict-returning
   core; the wrapper adds the interactive shell. Cleaner separation.)
2. Does `engine.main()` keep existing (delegating to the wrapper) or is it thinned to just argv-parsing
   + delegate? (Lean: thin it to parse -> delegate, so `install-workflows.py` and `aw` are provably the
   same path.)
3. Confirm there is NO intended behavior change; if reconciling step 3 surfaces a real difference (e.g.
   one path prunes backups and the other does not), is fixing it in-scope here? (Lean: yes - it is the
   same drift class; fix and record.)

## Dependencies / sequencing

- Depends on IPD `20260712-1837-01` shipping FIRST (1.2.1 symptom fix). This refactor lands after and
  preserves its behavior + tests while removing the duplication. Target 1.3.0.

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY `agent_workflows/engine.py`, `agent_workflows/cli.py`, the install tests
   (`tests/test_cli.py`, `tests/test_installer.py`, `tests/test_setup_artifacts.py` as needed),
   `ARCHITECTURE.md` (if it describes the install flow), `CHANGELOG.md`, and `DECISIONS.md` (next free
   number). Do NOT change the leaf helpers' behavior or `install-workflows.py`. NO user-facing behavior
   change; if one seems required, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Manually verify BOTH entry points
   (`aw install <dir>` and `install-workflows.py`) produce identical behavior on clean / dirty /
   non-interactive repos. Confirm `aw plan-names` clean.
4. COMMIT only this IPD's touched files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: 1.3.0 is cut separately via release-review Section 9 after a human rung choice.

HARD MUST: paste the real test output; no user-facing behavior change without STOP-and-report; stay
inside the scope fence; never push. Not auto-executed; requires human approval.
