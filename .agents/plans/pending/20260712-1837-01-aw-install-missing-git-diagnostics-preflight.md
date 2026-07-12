# IPD: `aw install` bypasses run_git_diagnostics (weaker pre-flight than the deprecated shim)

- Date: 2026-07-12
- Concern: correctness / release regression / entry-point parity. Discovered immediately after the
  first PyPI publish (1.2.0). The recommended CLI path `aw install` shows only a weak
  "uncommitted changes ... [y/N]" pre-flight, while the DEPRECATED `install-workflows.py` (which calls
  `engine.main()`) shows the engine's rich 3-option Git Diagnostics menu (pull --rebase / proceed /
  abort). So the primary, published path is WEAKER than the deprecated one: it silently drops the
  "pull latest first" and explicit "abort" options and the behind/ahead sync check. Users on a dirty
  or behind repo lose the safest option.
- Scope: `agent_workflows/cli.py` `_run_install` (route the pre-flight through
  `engine.run_git_diagnostics(plan)`; remove the redundant lighter dirty-repo warning, single source
  of truth per P8); reconcile the other install entry points that call `install_into_repo`
  (`_install_all`, and the `setup` flow) for consistency; a regression test asserting the CLI path
  invokes diagnostics; docs/DECISIONS. Patch release 1.2.1.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after the maintainer hit the bug
  live post-1.2.0 publish. Root-caused: `_run_install` (cli.py:327-345) calls `engine.install_into_repo`
  directly with its own `_preflight_warnings` + plain `_confirm`, never calling `run_git_diagnostics`.
  Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- Two install entry points diverge:
  - `install-workflows.py` -> `engine.main()` -> the engine flow calls `run_git_diagnostics(plan)`
    (engine.py:2591-2592) BEFORE installing. That function (engine.py:1339) is self-contained:
    git-available guard, `status --porcelain` dirty check, a bounded `git fetch`, behind/ahead sync,
    proceeds silently when clean+synced, and when interactive prints the 3-option menu
    ("[1] Pull ... [2] Proceed anyway [3] Abort", engine.py:1437-1439); returns True/False (abort).
    It already honors `is_interactive_session(plan)` and `--yes`/non-interactive.
  - `aw install` -> `cli.py:_run_install` (cli.py:300) -> `_preflight_warnings` (cli.py:267, a single
    WARN line for dirty/not-a-repo/would-downgrade) + `_confirm` (cli.py:233, plain [y/N]) ->
    `engine.install_into_repo` DIRECTLY (cli.py:339). It NEVER calls `run_git_diagnostics`.
- Sequencing detail (VERIFIED): today `build_install_plan` runs AFTER install in the CLI (cli.py:359,
  only to feed `print_summary`). To call `run_git_diagnostics(plan)` BEFORE install, the plan must be
  built earlier in `_run_install`. `run_git_diagnostics` needs only `plan.repo_root`, `plan.diff`, and
  interactivity, so an early `build_install_plan` is safe.
- Double-prompt risk (VERIFIED): `_confirm` asks "Install agent-workflows into <repo>?" and
  `run_git_diagnostics` asks the dirty/behind menu. These are DISTINCT questions; order them
  diagnostics-first (abort short-circuits before the install confirm) OR keep both but ensure a clean
  repo triggers neither extra prompt (`run_git_diagnostics` already returns True silently when
  clean+synced, and the would-downgrade warning stays in `_preflight_warnings`). Avoid asking the same
  thing twice.
- Other callers of `install_into_repo` (VERIFIED): `_install_all` (cli.py:426) and the `setup` flow
  (cli.py:674) also install without diagnostics. For entry-point parity they SHOULD get the same
  pre-flight, but `--yes`/non-interactive multi-repo runs must not become chatty (run_git_diagnostics
  already no-ops when non-interactive, printing warnings to stderr).
- `run_git_diagnostics` uses `git fetch` (a network call, 3s timeout) - already bounded and
  exception-guarded; acceptable for an interactive install pre-flight.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Route `_run_install` through `engine.run_git_diagnostics`.** Build the install plan for the target
   BEFORE installing (move/duplicate the `build_install_plan` call earlier in the per-repo loop), then
   call `run_git_diagnostics(plan)`; if it returns False (user chose Abort), skip that repo with a
   "skip: aborted" status and continue. Keep the existing `_confirm("Install ... into <repo>?")`
   AFTER a proceed, OR fold the install confirmation into the diagnostics outcome - decide during
   implementation to AVOID a double "are you sure" (see Step-0 double-prompt note). Recommended:
   diagnostics first (handles dirty/behind), then the single install `_confirm`.
2. **Remove the redundant lighter dirty-repo warning from `_preflight_warnings`** (cli.py:279-283):
   the dirty-repo case is now owned by `run_git_diagnostics` (single source of truth, P8). KEEP the
   not-a-git-repo and would-downgrade warnings in `_preflight_warnings` (diagnostics does not cover
   those). Update the `_preflight_warnings` docstring (cli.py:271 "Uncommitted-changes warning is left
   to the interactive path") to reflect that diagnostics now owns it.
3. **Entry-point parity.** Apply the same diagnostics pre-flight to `_install_all` (cli.py:426) and the
   `setup` install flow (cli.py:674), so all interactive `aw` install paths match the engine/deprecated
   path. Confirm non-interactive/`--yes` multi-repo runs stay quiet (run_git_diagnostics no-ops when
   non-interactive). If parity for `_install_all`/`setup` proves to add risk (e.g. a fetch per repo in
   a large batch), scope it to `_run_install` for 1.2.1 and file the batch paths as a follow-on - decide
   with evidence during implementation, do not silently skip.
4. **Regression test.** In `tests/test_cli.py`, assert the CLI install path invokes the diagnostics
   pre-flight (e.g. monkeypatch/spy `engine.run_git_diagnostics` and assert it was called for a normal
   `aw install <dir>`; and that a False return aborts that repo without calling `install_into_repo`).
   This is the guard that would have caught the regression.
5. **Docs + DECISIONS + release.** DECISIONS entry (next free number, likely D75) recording the
   entry-point-parity bug and the single-source-of-truth fix. This is a user-facing behavior fix ->
   patch release **1.2.1** (cut via release-review Section 9 from a clean `v1.2.1` tag, per RELEASING.md
   / D74). Note in CHANGELOG.

## Deferred / out of scope

- Any redesign of `run_git_diagnostics` itself (it works; this is a routing/parity fix).
- Changing the deprecated `install-workflows.py` (it already behaves correctly).
- The pre-existing cosmetic items from the release-review (A8 old EXECUTED vocab, A9 discovery symlink
  guard, A10 roadmaps, CI-2 lint) - unrelated to this bug.

## Open questions (v1 leans for review)

1. Diagnostics-first then install-`_confirm`, or fold them into one prompt? (Lean: diagnostics first;
   keep the single install `_confirm` after a proceed - clean repos see only the install confirm, dirty
   repos see the diagnostics menu then the install confirm. Avoid a redundant "are you sure" pair; if
   it reads as double, drop the install `_confirm` when diagnostics already returned an explicit
   proceed.)
2. Parity scope: fix all three paths (`_run_install`, `_install_all`, `setup`) in 1.2.1, or just
   `_run_install` now and batch paths as a follow-on? (Lean: all three if low-risk; the batch fetch
   cost is bounded and diagnostics no-ops non-interactively. Confirm with evidence.)
3. Does a behind-remote repo in a NON-interactive `aw install --yes` change behavior? (Lean: no -
   run_git_diagnostics prints warnings to stderr and proceeds when non-interactive, matching today's
   engine behavior; verify.)

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY `agent_workflows/cli.py` (the install pre-flight routing + `_preflight_warnings`
   docstring/dirty-line removal; parity in `_install_all`/`setup` per OQ2), `tests/test_cli.py` (the
   regression test), `CHANGELOG.md`, and `DECISIONS.md` (next free number). Do NOT modify
   `run_git_diagnostics` itself or `install-workflows.py`. If a change seems to need more, STOP and
   report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Manually verify BOTH entry points
   now show the same 3-option menu on a dirty scratch repo, and that a clean repo + `--yes` is silent.
   Confirm `aw plan-names` clean.
4. COMMIT only this IPD's touched files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: the 1.2.1 patch is cut separately via release-review Section 9 (tag `v1.2.1` from a clean
   tree, build, GitHub Release, PyPI) after a human rung choice - NOT part of executing this IPD.

HARD MUST: paste the real test output; verify both entry points match; stay inside the scope fence;
never push. Not auto-executed; requires human approval.
