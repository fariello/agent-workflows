# IPD: True install entry-point parity - batch paths must offer to commit (no silent-dirty) + finish the SystemExit isolation + release-review Lows

- Date: 2026-07-15
- Concern: correctness / single-source-of-truth (P8) / user-trust. A LIVE, high-impact bug: `aw install all`
  and `aw setup` call `engine.install_into_repo` (which STAGES the framework files) but never call
  `engine.prompt_and_run_commit`, so they install into every configured repo and NEVER prompt or commit -
  leaving the entire fleet DIRTY (staged) with no indication. The maintainer ran `aw setup`, said yes to
  "install all", and got ~30 dirty repos, no prompt, no commit. Meanwhile `aw install <dir>` and
  `install-workflows.py`/`engine.run()` DO call `prompt_and_run_commit`. This is the SAME
  incomplete-unification family as release-review REL-001 (the D85 F8 SystemExit fix landed only in the
  CLI batch paths, not in `engine.run()`): D83 unified the install STEPS but the commit/prompt and
  error-isolation SHELLS still diverge across the four entry points, contradicting the stated invariant
  that `aw setup` / `aw install` / `aw install <dir>` / `install-workflows.py` all behave the same.
- Scope: `agent_workflows/cli.py` (`_install_all`, the `setup` install loop) + `agent_workflows/engine.py`
  (`run()` isolation; the shared commit/summary shell) + tests; plus the release-review report-only Lows
  (REL-003/004/006/007) which are the same "finish the job" cleanup. NO change to install no-clobber/
  backup/staging safety. NO release cut.
- Status: executed
- Approval: approved by Gabriele 2026-07-15 (interactive)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-15 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised when the maintainer hit the
  silent-dirty-fleet bug live (aw setup -> install all -> 30 dirty repos, never committed/prompted), and
  from the report-only release-review (run 20260715-215056) which found REL-001 (SystemExit isolation
  missing in engine.run() multi-repo loop) and REL-003/004/006/007. Root-caused as the same incomplete
  entry-point unification D83 began. Maintainer decision: batch paths MUST offer to commit per-repo like
  single-repo (honoring --yes), i.e. TRUE parity - none may leave a repo silently dirty.
- 2026-07-15 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED
  (self-review with extra skepticism). Verified all findings against source: P-1 (prompt_and_run_commit
  only at cli.py:424 + engine.py:2845; _install_all/_run_setup lack it - CONFIRMED, independently proven
  by the live 30-repo silent-dirty incident + the cleanup), P-2 (engine.py run() install_into_repo call
  outside the try/except SystemExit), P-3 (run_rollback OSError-only guard), P-4 (NOTICE 2 dashes), P-5
  (multiple 3.8 refs in _compat.py/tests.yml), P-6 (make version-file doesn't touch index stamp); next D
  = D85. Findings: PR-001 (MEDIUM) strengthened the never-silent-dirty INVARIANT - on interactive DECLINE
  the batch paths must still print the "left staged; commit with X" line (not silently skip), and named
  `install all --yes` as the primary bulk regression target; PR-002 (MEDIUM) added an explicit
  BEHAVIOR-PRESERVATION guard so extracting the shared shell does not regress the working `_run_install`/
  `run()` single-repo behavior (only _install_all/setup gain commit, run() gains isolation), STOP-and-
  report otherwise; PR-003 (LOW) fixed a stray non-ASCII char in the DECISIONS bullet. OQ2 (batch prompt
  UX) resolved by the strengthened invariant; OQ1/OQ3 non-blocking leans. No unfixed BLOCKER/HIGH.
  Status -> reviewed (awaits human sign-off).
- 2026-07-15 approved by Gabriele (interactive), then EXECUTED (its_direct/pt3-claude-opus-4.8-1m-us).
  P-1: extracted `cli._install_one` (shared per-repo shell: install_into_repo -> print_summary -> status
  -> prompt_and_run_commit, SystemExit-isolated) and routed `_run_install` (behavior preserved),
  `_install_all`, and the `setup` loop through it - the two batch paths now commit/summarize instead of
  silently staging. P-2: wrapped `engine.run()`'s install_into_repo in except (Exception, SystemExit).
  P-3: run_rollback catches (OSError, ValueError) + warns. P-4: NOTICE dashes removed. P-5: _compat.py
  3.8->3.9 wording (tests.yml already accurate, left as-is). P-6: `make version-file` now syncs the
  index.md stamp (verified idempotent at 1.2.1). DECISIONS D85 + CHANGELOG 1.2.1. Fixed one
  behavior-preservation regression the tests caught (build_install_plan needs dry_run/no_backup/no_prune
  attrs the setup/install-all namespaces lack - filled with getattr defaults in _install_one) and updated
  the pre-existing isolation test's mock to the full result shape. Added regression tests:
  test_install_all_yes_commits_and_leaves_no_dirty (the headline bug), test_run_multi_repo_isolates_
  systemexit, test_rollback_survives_corrupt_created_files_record, NoticeStyleTests. VALIDATION (actual):
  `python -m pytest -q` -> "262 passed, 1 skipped in 61.22s". Manual: `aw install all --yes` on a
  throwaway 2-repo config COMMITTED both and left staged=0 (the exact bug, now fixed); non-interactive
  no-yes cleanly aborts (no silent-dirty). 0 em/en dashes. Status -> executed; git mv to executed/.

## Findings this IPD fixes (VERIFIED against source)

- P-1 [HIGH] `aw install all` (`cli._install_all`, cli.py:~479) and `aw setup` (the install loop,
  cli.py:~745) call `install_into_repo` but NEVER call `prompt_and_run_commit`, so they STAGE framework
  files in every repo and leave them uncommitted/unprompted. `_run_install` (cli.py:424) and
  `engine.run()` DO call it. Root cause: the commit/summary SHELL is duplicated per-entry-point, not
  shared, so `install all`/`setup` were written without it. USER IMPACT: a fleet install silently dirties
  every repo - exactly what happened.
- P-2 [MEDIUM] (= release-review REL-001) `engine.run()` multi-repo `--repo A B C` loop does not wrap the
  `install_into_repo` call (engine.py:~2809) in `except (Exception, SystemExit)`, so one repo's
  SystemExit (dir-conflict engine.py:927 / git-fail 676/700) aborts the whole batch. The D85 F8 fix
  landed in cli `_install_all`/`setup` but not here. Same isolation invariant, one path missed.
- P-3 [LOW] (REL-003) `run_rollback` catches only `OSError` reading `.created-files.json`; a corrupt
  record raises `JSONDecodeError` (ValueError) -> crashes before restoring (engine.py:~1846).
- P-4 [LOW] (REL-004) `NOTICE` has 2 em dashes (violates the no-dash rule; ships in the wheel/sdist).
- P-5 [LOW] (REL-006) stale "3.8 floor / 3.8-safe" wording vs declared `>=3.9` (`_compat.py:8-12`,
  `.github/workflows/tests.yml:27-29`).
- P-6 [LOW] (REL-007) `make version-file` bakes VERSION but does not sync the `index.md`
  `WORKFLOWS-VERSION` stamp in lockstep (both agree now, but a future cut could forget).

Deferred/optional: REL-002 (author email pyproject vs CITATION.cff) and REL-005 (stale CITATION
date-released) need a HUMAN decision (which email; date at tag time) - handled separately, not in this
IPD. REL-008 (unencoded PyPI URL name) is an optional nit; skip.

## Design (the real fix: one shared install-orchestration shell)

The DECISION (maintainer): all four entry points must behave the same - install AND offer to commit per
repo, honoring `--yes` (auto-commit non-interactive), never leaving a repo silently dirty.

- Extract/confirm a single shared per-repo orchestration function (building on D83's `install_into_repo`
  steps core) that does: pre-flight diagnostics -> `install_into_repo` (steps, staged) -> summary ->
  `prompt_and_run_commit` (auto under `--yes`, prompt otherwise), wrapped in the SystemExit-isolating
  try/except. Every entry point calls it:
  - `_run_install` (single + explicit multi-target): per-repo via the shared function (already close).
  - `_install_all`: loop the configured repos through the SAME shared function (this ADDS the missing
    summary + commit prompt + keeps R-4 isolation). Batch UX: per-repo prompt, or auto-commit under
    `--yes`; the terse one-line status stays as an ADDITIONAL summary, but the commit step is no longer
    skipped.
  - `setup` install loop: same shared function.
  - `engine.run()`: already calls install_into_repo + summary + prompt_and_run_commit; ADD the
    per-repo `except (Exception, SystemExit)` isolation (P-2) so it matches the CLI batch paths.
- The commit is path-scoped to the installer-touched files (already how `prompt_and_run_commit` works:
  it commits only `installed`/`pruned`/`artifacts`/`agents_status`/`.gitignore`, never `git add -A`).
- KISS/consistency: prefer ONE function both cli.py and engine.py call, so this class of drift cannot
  recur (the same P8 goal D83 had; D83 unified the steps, this unifies the shell).

INVARIANT the fix must guarantee (the real bug's root): NO entry point may leave a repo silently
staged-but-uncommitted. Under `--yes` it commits. WITHOUT `--yes`, if the user DECLINES the commit, the
run MUST still tell them the repo is left staged and how to commit it (the existing
`prompt_and_run_commit` already prints the `git commit -- <paths>` line on decline for the single-repo
path - the batch paths must inherit that same "here is what is left staged" output, not just skip
silently). "Silent-dirty" is the failure; an explicit "left staged, commit with X" on decline is
acceptable.

BEHAVIOR-PRESERVATION (guard against the fix regressing what works): the shared shell MUST reproduce
today's `_run_install` (single/explicit-target) and `engine.run()` (single-repo) behavior EXACTLY - D83
already routes both through `install_into_repo` + summary + `prompt_and_run_commit`, and that works. The
ONLY intended behavior CHANGES are: (1) `_install_all` and `setup` GAIN the summary + commit step (they
currently skip it - the bug); (2) `engine.run()` GAINS the per-repo SystemExit isolation (P-2). If
extracting the shared function would alter any other observable behavior, STOP and report.

## Proposed changes (ordered, validatable)

1. **P-1 (root cause):** route `_install_all` and the `setup` install loop through the shared
   install-and-commit orchestration so they run summary + `prompt_and_run_commit` per repo (auto under
   `--yes`, prompt otherwise). After this, no entry point leaves a repo silently staged-but-uncommitted:
   under `--yes` it commits; on interactive DECLINE it still prints the "left staged; commit with
   `git commit -- <paths>`" line (inherited from `prompt_and_run_commit`). NOTE the real-world bulk case
   is `install all --yes` (30 repos) - that path MUST auto-commit and is the primary regression target;
   the per-repo interactive prompt is correct for parity but is the minority path. Preserve `_run_install`
   and `run()` behavior EXACTLY (see BEHAVIOR-PRESERVATION above); the only new behavior is that
   `_install_all`/`setup` now commit/summarize instead of silently staging.
2. **P-2 (REL-001):** wrap `engine.run()`'s per-repo `install_into_repo` call in
   `except (Exception, SystemExit)` mirroring cli `_install_all`; set returncode=1, report, continue.
3. **P-3 (REL-003):** broaden the `run_rollback` record-read guard to `except (OSError, ValueError)` (or
   `json.JSONDecodeError`), warn on stderr, still restore backups.
4. **P-4 (REL-004):** replace the 2 em dashes in `NOTICE` with hyphens/parenthetical.
5. **P-5 (REL-006):** reword the "3.8" references to "3.9 floor" (or add an explicit best-effort note).
6. **P-6 (REL-007):** make `make version-file` also sync the `index.md` `WORKFLOWS-VERSION` stamp (or add
   a release-checklist test asserting they match), so bake-then-tag cannot drift the stamp.
7. **Tests:** (a) `install all` and `setup` COMMIT under `--yes` and PROMPT otherwise, and leave NO
   staged-but-uncommitted files in a repo after a `--yes` run (the direct regression for the reported
   bug); (b) `engine.run()` multi-repo isolates a SystemExit (parallel to
   `test_install_all_isolates_systemexit`); (c) `run_rollback` survives a corrupt `.created-files.json`;
   (d) a guard test that `NOTICE` has no em/en dashes; (e) a stamp-sync check for P-6.
8. **Docs/DECISIONS:** DECISIONS entry (D85, next free) recording that ALL install entry points share one
   orchestration shell (install + summary + commit, isolation, honoring --yes) - completing D83's
   unification so the "they all behave the same" invariant is actually enforced, not just intended. CHANGELOG
   under 1.2.1 (these are bug fixes to the pending patch).

## Deferred / out of scope

- REL-002 (author email) and REL-005 (citation date) - need a human decision; handle separately.
- REL-008 (URL encoding nit) - optional, skip.
- Any change to install no-clobber/backup/staging safety, or to `prompt_and_run_commit`'s
  path-scoped-commit set (only WHO calls it changes).
- Cleaning up the ~30 already-dirty repos - handled OUT OF BAND by a one-off script
  (`/tmp/opencode/aw-cleanup-installs.sh`, dry-run-first, commits only staged installer files
  path-scoped); not part of this repo's IPD.

## Open questions (v1 leans for review)

1. Batch `--yes` commit message: reuse the existing `"agent-workflows: sync via installer"` for all repos
   (Lean: yes - it is already the installer's message and matches the cleanup script).
2. `install all` WITHOUT `--yes` interactively: prompt per repo (Lean: yes, per the maintainer decision -
   true parity; a future `--yes`/`-y` is the bulk path). Confirm the per-repo prompt is not too noisy for
   30 repos, or whether `install all` should imply a single up-front "commit each? [Y/n]" that applies to
   all - Lean: per-repo prompt but honor --yes for the bulk case; revisit if noisy.
3. Shared-function shape: new `cli`-level helper vs. an `engine`-level orchestrator both call? (Lean:
   engine-level, so `install-workflows.py`/`engine.run()` and the CLI provably share it - same P8
   reasoning as D83.)

## Dependencies / sequencing

- Builds directly on D83 (shared steps core) and D85 (F8 isolation, partially landed). No dependency on
  other pending work (queue is otherwise empty). Target 1.2.1 (bug fixes to the pending patch).
- Closes release-review run 20260715-215056's REL-001/003/004/006/007 and the newly-found P-1; after this
  + the two human decisions (REL-002/005), the CONDITIONAL GO becomes a clean GO.

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY: `agent_workflows/cli.py`, `agent_workflows/engine.py`, `NOTICE`,
   `agent_workflows/_compat.py`, `.github/workflows/tests.yml`, `Makefile` (P-6), the relevant tests
   under `tests/`, `CHANGELOG.md`, and `DECISIONS.md` (D85, next free). Do NOT change install
   no-clobber/backup/staging safety, `prompt_and_run_commit`'s committed-path set, the versioning
   mechanism, or cut/tag/push a release. Do NOT touch the ~30 external repos (cleanup is out of band). If
   a fix seems to need more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write (and fix NOTICE's).
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output (new parity/isolation/rollback tests
   must pass). Manual: in a throwaway git repo, `aw install all --yes` (config -> that repo) COMMITS and
   leaves NO staged-but-uncommitted files; without `--yes` it PROMPTS; `install-workflows.py --repo good
   nonexistent` exits 1 and isolates. Confirm `aw plan-names` clean and the two plans-README stay
   byte-identical if touched (not expected).
4. COMMIT only this IPD's touched files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.

HARD MUST: paste the real test output; no entry point may leave a repo silently dirty after this; stay
inside the scope fence; do not touch external repos or cut a release; never push. Not auto-executed;
requires human approval.
