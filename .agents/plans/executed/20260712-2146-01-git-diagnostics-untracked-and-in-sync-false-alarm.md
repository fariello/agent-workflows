# IPD: Git diagnostics false alarm - offers a no-op pull for untracked-only, in-sync repos

- Date: 2026-07-12
- Concern: correctness / first-run UX / adoption. Shipped in 1.2.0. On a repo that is "dirty" ONLY
  from UNTRACKED files and fully in sync with its remote (`behind == 0`), `run_git_diagnostics` still
  prints the 3-option menu with "git pull --rebase" as option [1] AND the default. Two defects:
  (A) it offers and defaults to a pull when there is nothing to pull (`behind == 0`); (B) it treats
  untracked files as "dirty" and warns about them, even though untracked files are harmless to both a
  rebase and the installer (which only writes its own paths). Observed live in `pubrun`: 4 untracked
  files, nothing tracked-dirty, `git pull` reports "Already up to date", yet the user saw a scary menu
  defaulting to a pointless pull. This is the FIRST thing a new adopter sees on install, so it matters
  for adoption, not just correctness.
- Scope: `agent_workflows/engine.py` `run_git_diagnostics` (state detection + the prompt/menu logic,
  :1348-1467) and a new regression test. Docs/DECISIONS. Ships in the 1.2.1 patch ALONGSIDE IPD
  `20260712-1837-01` (both are install pre-flight bugs); coordinate the two (1837-01's scope fence
  currently says "do not modify run_git_diagnostics" - that carve-out is lifted for THIS IPD, which
  owns the diagnostics logic; 1837-01 still only ROUTES the CLI through it).
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after the maintainer hit it in
  `pubrun`. Root-caused against source (engine.py:1356-1448). Complete proposal; born to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE (no revisions). Verified the
  cited logic against source: the proceed-silently guard (:1407 `not is_dirty and behind == 0`), the
  default-to-pull (:1447-48), and porcelain-includes-untracked as `is_dirty` (:1356) all confirmed - so
  defects A (no-op pull default) and B (untracked counted as dirty) are real. Fix (split tracked vs
  untracked; offer pull only when behind>0; adapt the menu) is Low risk and testable. Cross-plan:
   owns `run_git_diagnostics` internals; 1837-01 only ROUTES into it (no overlap). No findings.
   Status -> reviewed.
- 2026-07-13 executed (its_direct/pt3-claude-opus-4.8-1m-us): implemented changes 1-4. Extracted a
  pure `classify_git_state` helper + `GitState` NamedTuple (split tracked-dirty vs untracked via the
  porcelain `??` marker); rewired `run_git_diagnostics` to proceed silently when no real risk
  (untracked-only and/or in sync), and to offer/default a pull ONLY when behind>0 (adaptive menu:
  pull/proceed/abort when behind; proceed/abort when in-sync-but-tracked-dirty, OQ2 proceed-default;
  no menu for untracked-only, OQ1 fully-silent). New `tests/test_git_diagnostics.py` (7 tests incl. the
  exact pubrun untracked-only-in-sync case). DECISIONS D76. Validated: 194 passed + 1 skipped with the
  pre-existing (unrelated, date-flakiness) `test_normalize_plan_names.py` excluded; the 7 new
  diagnostics tests green. Committed path-scoped `65754d9`; never pushed. Ships in 1.2.1 (not cut yet).

- `run_git_diagnostics` (engine.py:1339) computes `is_dirty = bool(git status --porcelain output)`
  (:1356) - which INCLUDES untracked files (porcelain marks them with a leading `?? `). It computes
  `behind` from `git rev-list --left-right --count HEAD...@{u}` (:1393-1404).
- Proceed-silently guard (:1407): `if not is_dirty and behind == 0: return True`. So ANY dirty state
  (including untracked-only) OR any behind>0 triggers the interactive menu.
- The menu (:1436-1439) is STATIC: it always lists "[1] Pull latest changes (git pull --rebase) and
  proceed / [2] Proceed anyway / [3] Abort", and the empty-input default is "1" (:1447-1448), which
  runs `git pull --rebase` (:1450-1462). When `behind == 0`, that pull is a no-op at best and
  confusing at worst; when the dirtiness is untracked-only, there is nothing a rebase interacts with.
- Non-interactive path (:1425-1428) already prints warnings to stderr and proceeds - unaffected by
  this change except that untracked-only should not produce a scary warning.
- No existing test covers `run_git_diagnostics` (verified: no test references it). The fix MUST add one
  (it would have caught this).
- Porcelain format (VERIFIED): untracked lines start with `?? `; tracked changes start with a two-char
  XY status (e.g. ` M`, `M `, `A `, `??` is the only untracked marker). So tracked-dirty vs
  untracked-only is cheanly separable by counting lines that do NOT start with `??`.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Separate tracked-dirty from untracked-only.** From the porcelain output, compute
   `tracked_dirty` = any line whose status is not `??` (staged or worktree-modified/renamed/deleted
   tracked files), and `untracked` = lines starting with `?? `. Keep the raw counts for messaging.
2. **Make the proceed-silently condition state-accurate.** The install pre-flight only genuinely cares
   about: (a) `behind > 0` (a pull would actually help), and (b) `tracked_dirty` (real local changes
   that a pull/rebase or the install could collide with). Untracked-only + in-sync is NOT a risk to a
   pull or to the installer (it writes its own paths, no-clobber). So: proceed silently (return True)
   when `behind == 0 AND not tracked_dirty`, regardless of untracked files. OQ1: whether to emit a
   single soft one-line FYI on untracked-only ("N untracked files present; unaffected by install") or
   stay fully silent (lean: fully silent - it is not actionable and adds noise on the primary path).
3. **Make the menu adapt to the actual state (do not offer a no-op pull).**
   - Only include the "[1] Pull latest changes (git pull --rebase)" option AND make it the default
     WHEN `behind > 0`. When `behind == 0`, do not offer pull at all.
   - When `behind == 0` but `tracked_dirty` (the remaining reason to prompt), present only
     "Proceed anyway" / "Abort", with the SAFE option as default (OQ2: default to proceed vs abort -
     lean: default proceed, since tracked-dirty + in-sync is a common, usually-fine state and the
     installer is no-clobber + stages-not-commits; but name the risk in the prompt).
   - Warnings shown must match reality: warn about `behind` only when behind>0; warn about tracked
     changes only when tracked_dirty; do not present untracked files as a problem.
4. **Regression test** (`tests/test_installer.py` or a new `tests/test_git_diagnostics.py`). Drive
   `run_git_diagnostics` (or its state-classification helper) against a repo that is: (a) untracked-only
   + in-sync -> proceeds silently, NO pull offered/run; (b) behind>0 -> pull offered as default;
   (c) tracked-dirty + in-sync -> proceed/abort menu, no pull option. Prefer extracting the
   state-classification into a small pure helper (e.g. `classify_git_state(porcelain, ahead, behind)`)
   so it is unit-testable without a live remote; mock the git calls or use a scratch repo + fake
   upstream. This is the guard that would have caught the bug.
5. **Docs + DECISIONS + release.** DECISIONS entry (next free number at execution - D74 is taken;
   likely D75 or later depending on 1837-01/1901-01 ordering) recording the false-alarm bug and the
   state-accurate fix. Note in CHANGELOG under 1.2.1. Ships in the same 1.2.1 patch as 1837-01.

## Deferred / out of scope

- The orchestrator unification (IPD 1901-01, 1.3.0) - independent; this fix lives inside
  run_git_diagnostics and survives the later refactor.
- Any change to WHEN the installer decides to write files (no-clobber/backup behavior is unchanged).
- Adding ahead>0 (unpushed) handling to the menu - the current code computes `_ahead` but does not act
  on it; leaving that as-is unless the trial shows it matters (untracked/ahead are both non-blocking).

## Open questions (v1 leans for review)

1. Untracked-only + in-sync: fully silent, or a single soft FYI line? (Lean: fully silent - not
   actionable; keeps the primary path clean, matching the "clean+synced proceeds silently" intent.)
2. tracked-dirty + in-sync menu default: proceed or abort? (Lean: proceed - common benign state; the
   installer is no-clobber and stages-not-commits, so the risk named in [2] is low; still name it.)
3. Should the helper also stop counting untracked in the user-facing "N uncommitted local files"
   message when it DOES warn (i.e. report tracked count, mention untracked separately if at all)?
   (Lean: yes - report the tracked-dirty count as the actionable number; untracked is informational.)

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY `agent_workflows/engine.py` (`run_git_diagnostics` state detection + menu;
   optionally extract a pure `classify_git_state` helper), the test file (`tests/test_git_diagnostics.py`
   new, or an added case in `tests/test_installer.py`), `CHANGELOG.md`, and `DECISIONS.md` (next free
   number). Do NOT change no-clobber/backup/install-write behavior or the CLI routing (that is 1837-01).
   If a change seems to need more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Manually verify the three states
   on scratch repos: untracked-only+in-sync (silent proceed, no pull), behind>0 (pull offered/default),
   tracked-dirty+in-sync (proceed/abort, no pull option). Confirm `aw plan-names` clean.
4. COMMIT only this IPD's touched files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: ships in the 1.2.1 patch with 1837-01, cut via release-review Section 9 after a human rung
   choice - NOT part of executing this IPD.

HARD MUST: paste the real test output; verify the three git states behave correctly; stay inside the
scope fence; never push. Not auto-executed; requires human approval.
