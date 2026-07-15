# IPD: Unify the two install orchestrators behind one canonical path (root cause of the CLI drift)

- Date: 2026-07-12
- Concern: architecture / single-source-of-truth (P8) / drift prevention. `engine.run()` (behind the
  thin `engine.main()` wrapper, used by `install-workflows.py`) and `cli._run_install` are TWO
  hand-maintained orchestrators of the SAME install operation: `run()` inlines the sequence (calling
  `install_all` directly), while the CLI path calls the shared core `install_into_repo`. That core
  returns a result dict and does NOT itself run the pre-flight (`run_git_diagnostics`), the summary
  (`print_summary`), or the commit prompt (`prompt_and_run_commit`) - each caller re-adds those around
  it. That is exactly how the 1.2.1 bug (IPD 1837-01: `aw install` missing `run_git_diagnostics`) arose:
  a step added to one orchestrator was never mirrored into the other. As long as two orchestrators
  exist, this class of drift will recur (this session's comms scaffolding went into a shared LEAF,
  `create_setup_artifacts`, so it did not add new drift - but the orchestration split remains).
- Scope: `agent_workflows/engine.py` + `agent_workflows/cli.py`: extract ONE canonical install
  orchestrator (a single function that runs pre-flight -> install_into_repo -> summary -> commit prompt,
  with parameters for interactivity/dry-run/yes) that BOTH `engine.run()` (behind `engine.main()` /
  `install-workflows.py`) and `cli._run_install` / `_install_all` / the `setup` flow call. Tests proving
  both entry points drive the identical sequence. Docs/DECISIONS. Internal refactor with NO intended
  user-facing behavior change; target a MINOR release (1.3.0) because it is a non-trivial internal
  change, not a patch.
- Status: executed
- Approval: approved by Gabriele 2026-07-15 (interactive)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised during /plan-review-long of IPD
  1837-01 when the maintainer asked whether the CLI and installer "should have a separate code base".
  Root-caused the opposite: they are duplicated orchestrators (not separate enough), which is the P8
  violation that produced the drift. 1837-01 patches the symptom for 1.2.1; this IPD removes the root
  cause for 1.3.0. Complete proposal; born to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE (no revisions). Verified
  against source: `install_into_repo` returns a dict and does NOT call diagnostics/summary/commit (each
  caller re-adds them - the drift root cause is real). Cross-plan check: touches engine.py + cli.py
  orchestration, lands AFTER and SUPERSEDES 1837-01's CLI wiring (correctly stated); no edit overlap
  with the 1.2.1 plans. Scope, deferrals (no behavior change; STOP-and-report if one is needed), and
  the single-orchestrator tests are sound. No BLOCKER/HIGH; no findings. Status -> reviewed.
- 2026-07-15 /plan-review RE-REVIEW (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS
  APPLIED. Triggered by heavy repo change since 2026-07-12 (this session executed D79-D82; engine.py grew
  comms scaffolding). Core thesis RE-VERIFIED still valid: `install_into_repo` (now engine.py:2645) is
  still a pure dict core, and TWO orchestrations still exist - `engine.run()` (engine.py:2704, inlines
  `install_all`) behind the thin `engine.main()` wrapper, vs. the CLI's `install_into_repo` path (cli.py
  :375/:479/:737). Findings: PR-001 (HIGH) ALL line anchors stale (install_into_repo 2471->2645,
  main 2654->2828, _run_install 300->328, etc.) - refreshed throughout. PR-002 (HIGH) the plan framed
  `engine.main()` as the inlined orchestrator, but `main()` is now a thin wrapper and the orchestration
  moved to `run()`; also 1837-01 has SHIPPED (executed), so its `_diagnostics_ok` wiring (cli.py:291) is
  LIVE and this IPD now SUBSUMES it (dependency satisfied) rather than "lands after" - reframed. PR-003
  (MEDIUM) pinned DECISIONS to D83 (D79-D82 taken) and refreshed test count 215->253. PR-004 (LOW)
  em -> em/en dashes. OQ1-OQ3 remain reasonable non-blocking implementation leans (OQ2 updated for the
  main/run split). No BLOCKER/HIGH left unfixed. Status stays reviewed (awaits human sign-off).
- 2026-07-15 approved by Gabriele (interactive), then EXECUTED (its_direct/pt3-claude-opus-4.8-1m-us).
  Hit a STOP-and-report at the study phase (the plan's "route ALL through ONE orchestrator" was too
  blunt: `_install_all` is intentionally terse); maintainer approved the refined narrower approach
  (recorded in the "Execution refinement" + "As-built" sections). Implemented D83: `install_into_repo`
  is the single step core (canonical README-then-artifacts order; returns `migrated`; accepts+forwards
  `yes`/`no_color`); `run()` now calls it; the 3 CLI sites forward the flags. Found + fixed a THIRD
  drift during execution (CLI path did not forward `yes`, so `aw install --yes` silently preserved
  customized shims - a real regression my first pass also re-triggered, caught by
  `test_customization_protection`, then fixed by threading `yes` through). Added
  `SingleSourceOrchestratorTests`. VALIDATION (actual): `python -m pytest -q` -> "254 passed, 1 skipped
  in 55.62s". Manual: `aw install` vs `install-workflows.py` on a clean repo -> IDENTICAL filesets;
  both proceed non-interactively on a dirty repo (exit 0); `aw install --yes` now overwrites a
  customized shim (D83 fix confirmed). 0 em/en dashes; scope fence held (engine.py, cli.py,
  test_installer.py + docs). DECISIONS D83 + CHANGELOG 1.3.0 (pending) + IPD as-built section. Status ->
  executed; git mv to executed/. Ship in 1.3.0 via release-review Section 9.

## Project conventions discovered (Step 0, RE-VERIFIED against source at re-review 2026-07-15)

NOTE: all line anchors below were REFRESHED at re-review; the original 2026-07-12 anchors had shifted
(this session's `engine.py` edits + earlier changes moved everything down, and `engine.main` was
thinned). The two-orchestrator DRIFT the plan targets is confirmed STILL PRESENT.

- `install_into_repo` (engine.py:2645) does file writes + returns a dict; it does NOT call
  `run_git_diagnostics`, `print_summary`, or `prompt_and_run_commit` (re-verified: none appear in its
  body). Pure batch-friendly core.
- `engine.main()` (engine.py:2828) is now a THIN wrapper: `return run(parse_args(argv))` + CTRL-C/EOF
  handling. The real orchestrator is `engine.run()` (engine.py:2704), which orchestrates:
  `run_git_diagnostics` -> `install_all` (INLINED, NOT via `install_into_repo`) -> the install steps ->
  `print_summary` -> `prompt_and_run_commit`. So the `install-workflows.py`/`aw run` path still INLINES
  the sequence rather than calling `install_into_repo`. (The plan originally named this path
  `engine.main`; the orchestration has since moved into `run()`, which `main()` merely wraps.)
- `cli._run_install` (cli.py:328) orchestrates: `_diagnostics_ok` (cli.py:291, the 1837-01 wrapper that
  runs `run_git_diagnostics`) + `_confirm` -> `install_into_repo` (cli.py:375) -> `print_summary` ->
  `prompt_and_run_commit`. `cli._install_all` (cli.py:434) and the `setup` flow (cli.py:737) are the
  other two `install_into_repo` call sites.
- So there are STILL effectively TWO install orchestrations: `engine.run()`'s inlined one (calls
  `install_all` directly), and the CLI's `install_into_repo`+wrapper one (three call sites). They share
  leaf helpers but not orchestration - the drift root cause is intact. Divergence to reconcile: the
  inlined `run()` steps vs. `install_into_repo`'s own set (confirm they are identical - a review-time
  TODO for execution).
- 1837-01 has SHIPPED (executed; `.agents/plans/executed/20260712-1837-01-...`). Its symptom fix is LIVE:
  `_diagnostics_ok` (cli.py:291) wires `run_git_diagnostics` into all three CLI install paths
  (`_run_install`/`_install_all`/`setup`). This IPD now SUBSUMES that live wiring: after unification the
  CLI's bespoke `_diagnostics_ok`/pre-flight/commit wiring is replaced by the shared orchestrator, while
  PRESERVING 1837-01's behavior and its `InstallDiagnosticsTests`. (The original "1837-01 ships first"
  dependency is therefore already SATISFIED.)
- Zero-dep, stdlib-only project; 253 tests; the install path is the most-tested surface
  (test_installer.py, test_cli.py, test_setup_artifacts.py, test_git_diagnostics.py) - a good safety net
  for a refactor.
- House rule: no em or en dashes in authored Markdown.

## Execution refinement (2026-07-15, recorded before implementing per STOP-and-report)

Studying the real code at execution revealed the plan's "route ALL entry points through ONE
orchestrator" wording was too blunt, and pinpointed the actual drift precisely. Refined (maintainer
approved) approach, which achieves the plan's GOAL (one shared orchestration core, no drift) without a
user-facing behavior change:

- `install_into_repo` (engine.py:2645) is ALREADY the single shared source of the install STEPS. The
  real drift is that `engine.run()` (engine.py:2704) RE-INLINES those same steps instead of calling it.
  Fix: make `run()` call `install_into_repo` for the steps, then do its own summary/commit shell from the
  returned dict. This removes the duplicate step sequence (the drift root cause).
- Two concrete drifts found + fixed HERE (per Step 3): (a) `run()` runs the README-ensurers BEFORE
  `create_setup_artifacts` while `install_into_repo` did the reverse (same filesystem outcome - disjoint
  no-clobber paths - but divergent); canonicalize on the `run()` order (READMEs then artifacts) in the
  ONE place (`install_into_repo`). (b) `install_into_repo` never returned `migrated`, yet
  `cli._run_install` reads `result.get("migrated")` (so the CLI summary silently omitted migrated files
  while `run()` showed them); make `install_into_repo` return `migrated` so both summaries match.
- Presentation shells are INTENTIONALLY different and are preserved (NOT forced identical): `run()` and
  `cli._run_install` show the full summary + per-repo commit prompt; `cli._install_all` is deliberately
  TERSE (one status line per repo, no full summary, no per-repo commit prompt) - a batch-UX choice, not
  drift. This is documented so it is not mistaken for drift later.

## Proposed changes (ordered, validatable)

1. **Extract one canonical orchestrator.** Introduce a single function (e.g.
   `engine.install_orchestrated(plan_or_args, *, interactive, run_diagnostics=True) -> result` OR grow
   `install_into_repo` to optionally run the full sequence) that performs: pre-flight
   (`run_git_diagnostics` when interactive) -> the install steps -> `print_summary` ->
   `prompt_and_run_commit`. It must reproduce today's `engine.main()` single-repo behavior EXACTLY.
2. **Route ALL entry points through it.** `engine.run()` (behind `engine.main()` / `install-workflows.py`),
   `cli._run_install`, `cli._install_all`, and the `setup` install flow all call the one orchestrator.
   Remove the CLI's bespoke pre-flight/commit wiring - including the now-LIVE `_diagnostics_ok`
   (cli.py:291, from shipped 1837-01) - in favor of the shared path, PRESERVING that behavior. Keep the
   CLI-only concerns that are genuinely CLI-specific (multi-repo loop, per-repo isolation,
   `_preflight_warnings` would-downgrade/not-a-repo notices).
3. **Reconcile any latent step differences** between engine.main's inlined sequence and
   install_into_repo (e.g. confirm both run the same README-ensurers / setup-artifacts / backup-prune
   steps). Any real difference found is itself a drift bug to fix here (record each).
4. **Tests: prove single-source.** Add tests asserting BOTH entry points (engine.main path and the CLI
   path) produce the same install result + invoke the same pre-flight/summary/commit sequence (spy the
   orchestrator or assert on observable effects). This is the structural guard against future drift.
   Preserve all 1837-01 tests (diagnostics called; abort; non-interactive not blocked).
5. **Docs + DECISIONS.** DECISIONS entry D83 (next free; D79-D82 taken this session) recording the
   two-orchestrators root cause, the unification, and that it subsumes 1837-01's (already-shipped)
   `_diagnostics_ok` symptom wiring. Note in ARCHITECTURE if the install flow is described there. Ship in
   1.3.0 (internal refactor, no user-facing behavior change intended, but non-trivial -> MINOR, cut via
   release-review Section 9 from a clean tag).

## As-built (2026-07-15 execution)

Implemented per the refinement above (D83):
- `install_into_repo` (engine.py): canonical step order (README-ensurers THEN `create_setup_artifacts`),
  now returns `migrated`, and accepts + forwards `yes`/`no_color` onto its internal `InstallPlan`.
- `engine.run()`: replaced its re-inlined step sequence with a call to `install_into_repo`, then drives
  its own summary/commit shell from the returned dict (using run()'s richer plan for the interactive UX).
- `cli._run_install` / `_install_all` / `setup`: forward `yes`/`no_color` into `install_into_repo`.
- Tests: `SingleSourceOrchestratorTests` (run() vs install_into_repo -> same fileset; `migrated` key
  present). 1837-01's `InstallDiagnosticsTests` and `test_customization_protection` preserved + green.
- A THIRD drift was found + fixed during execution (recorded in D83): the CLI path did not forward `yes`
  to the step core, so `aw install --yes` silently preserved customized shims (vs. `install-workflows.py
  --yes` which overwrote); now consistent.
- `_install_all` intentionally kept terse (no full summary/commit) - documented as a deliberate UX
  difference, NOT drift.

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
2. `engine.main()` is ALREADY thinned to `return run(parse_args(argv))` (verified at re-review). The
   real question is whether `engine.run()` (engine.py:2704) delegates to the new canonical orchestrator
   or is itself refactored into it. (Lean: make `run()` call the shared orchestrator so
   `install-workflows.py` and `aw` are provably the same path.)
3. Confirm there is NO intended behavior change; if reconciling step 3 surfaces a real difference (e.g.
   one path prunes backups and the other does not), is fixing it in-scope here? (Lean: yes - it is the
   same drift class; fix and record.)

## Dependencies / sequencing

- Dependency SATISFIED: IPD `20260712-1837-01` has EXECUTED (it is in `.agents/plans/executed/`; its
  `_diagnostics_ok` wiring is live in cli.py). This refactor subsumes that wiring while preserving its
  behavior + `InstallDiagnosticsTests`, removing the duplication. Target 1.3.0. No remaining
  cross-plan ordering blocker.

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY `agent_workflows/engine.py`, `agent_workflows/cli.py`, the install tests
   (`tests/test_cli.py`, `tests/test_installer.py`, `tests/test_setup_artifacts.py`,
   `tests/test_git_diagnostics.py` as needed), `ARCHITECTURE.md` (if it describes the install flow),
   `CHANGELOG.md`, and `DECISIONS.md` (D83, next free). Do NOT change the leaf helpers' behavior or
   `install-workflows.py`. NO user-facing behavior change; if one seems required, STOP and report.
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
