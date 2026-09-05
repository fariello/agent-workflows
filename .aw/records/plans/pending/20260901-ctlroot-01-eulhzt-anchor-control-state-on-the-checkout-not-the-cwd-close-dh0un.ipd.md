# IPD: Anchor control state on the checkout, not the cwd (close dh0uno and retire wtiso)

- Date: 2026-09-01
- Kind: child
- Concern: Backlog `dh0uno` is still LIVE on `main`: `aw` composes its control paths as `repo_root/".aw"/state/...`, where `repo_root` is the caller's git worktree top-level. Under driver worktree isolation the agent runs with cwd inside a lane (`.aw/worktrees/<id6>`), so an inner `aw` resolves `<lane>/.aw/state/...` - a SECOND receipt/lock/journal store the driver (running from the main tree) cannot see, `git status` cannot show (gitignored), no branch diff carries (never committed), and lane teardown deletes. Measured before this fix: `receipt_dir(<main>)` and `receipt_dir(<lane>)` return two different directories. This plan closes `dh0uno` at its root with a minimal, self-contained change, and by doing so lets the stalled 7-plan `wtiso` Set be retired: `wtiso`'s Concern names exactly three live failures, and the other two are already closed on `main` (`xmqv5l` fixed in `cdef9c90`; `qyaime`'s unbounded hang bounded by the shipped `StallWatchdog`).
- Scope: The ONE control-root authority plus the three legacy control-path constructors that must route through it, the two now-redundant receipt-copy helpers, and the tests that pin the behavior. Does NOT port the 859-line `execution_context.py` + `path_resolver.py` machinery from lane `7p9n2v`, and does NOT relocate state out of the repository (that was `wtiso` Phase 4, which is being retired unlanded; see "Deferred").
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_statefork_dh0uno.py, tests/test_wtiso_characterization.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, .aw/records/backlog/open/
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: ctlroot
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: eulhzt
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved
- From-Backlog: dh0uno
- Blocks-Release: next

## Workflow history
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-03 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED. E-06/E-07 added for the new git dependency (spawn failure raised from a finally: and leaked the finalize lock; a git fork per path lookup), E-08 for the retired-Phase-4 successor gap, post-gate sequence corrected to run aw ipd begin first. Readiness go-pending-approval
- 2026-09-02 to-review (aw set): authored from completed work validated in an isolated clone; closes dh0uno at the control-root, replaces wtiso's invalid acceptance criterion with a falsifiable real-worktree regression suite

- 2026-09-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make control state (begin receipts, the finalize writer lock, finalize transaction journals) belong to the CHECKOUT rather than to whichever worktree is the caller's cwd, so a driver lane and the main tree resolve ONE control store. Product paths must keep resolving per-worktree, because finalize has to commit into the tree the agent actually edited.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one control-root authority

- [x] E-01 Add `ipd_lifecycle.checkout_control_root(start)`: the single function deciding where a checkout's `.aw` control root lives, keyed on `git rev-parse --path-format=absolute --git-common-dir` (every linked worktree of a checkout shares one common dir), with an explicit fallback to `start/.aw` when there is no checkout identity to collapse to.
  - Depends on: none
  - Expected outcome: a documented function that returns the MAIN worktree's `.aw` from any worktree of the checkout, and `start/.aw` for a plain/non-git/nonexistent directory. Uses the existing canonical `_git` wrapper rather than adding a second subprocess path.
  - Execution state: performed

- [x] E-02 Route the three legacy control-path constructors through it: `receipt_dir` (begin receipts) and `_runtime_dir` (finalize lock + transaction journals). Leave `_repo_root` returning the PRODUCT tree, and document why the two must not be conflated.
  - Depends on: E-01
  - Expected outcome: `receipt_dir`/`receipt_path_for`/`finalize_lock_path`/`finalize_journal_path` agree across worktrees; `_repo_root` still returns the lane for a lane.
  - Execution state: performed

### Task group 2: retire the copy that the fix makes redundant

- [x] E-03 Make `oc_runipd.sync_receipt_into_worktree` and its `agy_runipd` twin explicit deprecated no-ops, documenting that the copy is no longer load-bearing and that performing it would re-create the fork.
  - Depends on: E-02
  - Expected outcome: both helpers return None without touching the filesystem; their call sites keep working. Necessary, not merely tidy: with one resolved path, `shutil.copy2(src, dst)` now has `src == dst` and raised `shutil.SameFileError`.
  - Execution state: performed

### Task group 3: pin the fix and correct the tests that encoded the defect

- [x] E-04 Add `tests/test_statefork_dh0uno.py`: allocate a REAL `git worktree` and assert the control paths resolve identically from the main tree and the lane, that a receipt written from main is readable from the lane, that the PRODUCT tree still resolves per-worktree (guards the over-correction), and that the non-git fallback is preserved.
  - Depends on: E-02
  - Expected outcome: a test file that fails against pre-fix code and passes after.
  - Execution state: performed

- [x] E-05 Invert the pinned characterization test as its own note instructed, and correct the two driver isolation tests whose receipt assertion passed for the WRONG reason.
  - Depends on: E-03, E-04
  - Expected outcome: `test_receipt_is_copied_into_lane` becomes `test_no_second_receipt_authority_is_created_for_a_lane` using a real worktree; the two `test_main_tree_clean_during_turn_and_receipt_under_main` tests assert the receipt ANCHORS on the checkout and is CONSUMED by a clean finalize.
  - Execution state: performed

### Task group 4: make the new git dependency safe (added at review; see PR-001/PR-002)

- [ ] E-06 Make `checkout_control_root` TOTAL: no formerly-pure path accessor may raise because a git subprocess could not be SPAWNED. Wrap the `_git` call so `OSError` (which covers `FileNotFoundError` for a missing git and `BlockingIOError` for a fork/resource failure) falls back to `start/.aw`, exactly as the existing nonzero-returncode branch already does. Add the two regression tests to `tests/test_statefork_dh0uno.py`.
  - Depends on: E-01
  - Expected outcome: with `subprocess.run` raising `FileNotFoundError` and with it raising `OSError(EAGAIN)`, `receipt_dir`, `finalize_lock_path` and `release_finalize_lock` all RETURN a path instead of raising, and the returned path is `start/.aw/...`. MEASURED at review, pre-fix: all three raise. The `release_finalize_lock` case is the one that matters most: it is called from a `finally:` during finalize, so the raise both LEAKS the writer lock and REPLACES the real in-flight exception with a confusing git error (measured: `RuntimeError("THE REAL FINALIZE ERROR")` was masked by `FileNotFoundError`, and the lock file remained on disk). Do NOT catch bare `Exception`; catch `OSError` only, so a genuine programming error still surfaces.
  - Execution state: pending

- [ ] E-07 Memoize the checkout->control-root resolution so a path lookup is not a git fork. Cache keyed on the resolved `start` path, consulted by `checkout_control_root`; expose a documented cache-clearing hook and call it from the new tests' `setUp` so a test that builds a fresh worktree per case cannot read a stale entry.
  - Depends on: E-06
  - Expected outcome: MEASURED at review, pre-fix: 15 path lookups spawned 15 git subprocesses (~1.77 ms each). After E-07 a repeated lookup spawns ZERO additional processes. This matters because `receipt_dir`/`finalize_lock_path`/`finalize_journal_path` were PURE string composition before this plan and are called from loops and from error-message formatting (`ipd_lifecycle.py:1279,1707,1863,1992`), so the cost is now paid on paths that never expected to touch the filesystem. Correctness first: an entry must never be shared between two different `start` paths that resolve differently.
  - Execution state: pending

- [ ] E-08 File ONE backlog item recording the debt named in "Deferred / out of scope": that the out-of-repo control-state relocation has NO successor plan now that `58ha43` is retired unlanded, and that six modules plus spec `c4gd2h` OQ-03 still name retired plans as live owners. List the exact sites. Create it with `aw backlog new` (never hand-name it); do NOT set `Blocks-Release`, since nothing on `main` is broken by the absence.
  - Depends on: none
  - Expected outcome: one committed `.aw/records/backlog/open/*.backlog.md` item whose id6 is cited back into the Deferred entry, so `aw attention` can see the debt instead of it living only in this plan's prose. `aw backlog check` reports no NEW violation for it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_lifecycle._git` (`agent_workflows/ipd_lifecycle.py:1072`) delegates to `git_commit_helper._git`, described as "the single canonical git-subprocess runner ... so there is exactly one git wrapper across the codebase". E-01 therefore uses it rather than calling `subprocess.run` directly.
- `.aw/records/runs/` is gitignored (`.aw/.gitignore:15`) with ZERO tracked files, which is load-bearing for the Findings note about `test_run_viewer.py`.
- The receipt is CONSUMED on a clean finalize (`ipd_lifecycle.py:2047`, `receipt_path_for(...).unlink()` under "the transaction is cleanly complete"). Any test asserting the receipt still exists after a successful run is asserting a leak.
- `execute_item` passes the LANE as the finalize repo: `finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo` (`oc_runipd.py:5270`). This is what made the pre-fix orphan possible.
- Plans are scaffolded, never hand-named (`aw ipd scaffold`); this file was produced that way.

## Findings

- ROOT CAUSE, measured. `receipt_dir` was `repo_root.joinpath(".aw", *_RECEIPT_SUBDIR)` and `_runtime_dir` was `repo_root.joinpath(".aw","state","runtime")`. With a real worktree: main resolved `<main>/.aw/state/ipd-lifecycle` and the lane resolved `<lane>/.aw/state/ipd-lifecycle`. Two stores, one plan.
- THE HARM WAS ALREADY CONTAINED, which is why this is a correctness/debt fix and not an active outage. The driver marks an isolated turn `AW_EXECUTION_ROLE=worker` (`oc_runipd.py:4409`, `agy_runipd.py:2804`), and a worker-role `aw ipd begin|finalize` refuses with `AW-LIFECYCLE-ROLE-001` (`ipd_lifecycle.py:67`), so in normal operation nothing in-lane writes the forked copy. HONEST LIMIT, stated by that code itself: the role marker is an environment SELECTOR, not a boundary; a worker with shell access can unset it. The fork also still bit the driver's OWN in-lane finalize, which runs with the lane as its repo.
- THE PRE-EXISTING TESTS ENCODED THE DEFECT. `test_main_tree_clean_during_turn_and_receipt_under_main` (both drivers) asserted the main-tree receipt file still existed after a successful isolated run. That passed only BECAUSE of the fork: finalize ran with the lane as its repo and consumed the LANE's receipt, orphaning main's copy. With one store, a clean finalize correctly consumes it, so the old assertion inverts.
- THE PINNED CHARACTERIZATION TEST COULD NOT SEE THE FIX. `test_receipt_is_copied_into_lane` deliberately used two PLAIN directories, noting the copy "never consults git". That is exactly why it kept passing after the fix: with no checkout identity there is nothing to collapse, so the non-git fallback preserves the per-directory layout. Its own docstring said it should be inverted once the fork was closed; E-05 honors that with a real worktree.
- `wtiso`'s ACCEPTANCE CRITERION WAS INVALID and is deliberately not reused. The `wtiso` handoff and `lanectn` orchestrator (`h0zljh`:178) both claim ~15 `tests/test_run_viewer.py` failures in a fresh clone "are `dh0uno`". They are not: they are a gitignored-fixture artifact. Measured in a fresh clone at `53943a62` with NO fix applied: 15 failed; then, after copying in `.aw/records/runs/` and still with no fix, `36 passed`. That file's own module docstring already says the failures are fixture-driven and must not be read as a regression. A criterion that passes without the fix cannot demonstrate the fix.
- THE FINALIZE LOCK IS NOW GENUINELY SHARED, which is the intended fix and also a real behavior change worth naming rather than discovering later. `acquire_finalize_lock` refuses when a LIVE pid holds the lock (`ipd_lifecycle.py:238-276`) and the caller converts that into `EXIT_CANNOT_RUN` with no retry (`:1782-1786`). Before this fix two lanes each had their OWN lock file, so two concurrent in-lane finalizes could both "hold the lock" - the bug. After it, the second one correctly REFUSES. That is correct (the lock guards the shared plan manifest and the shared `pending/`->`executed/` move, which are checkout-global), but the refusal is not silent-safe by luck: it is safe because the driver records a finalize refusal and PRESERVES the lane rather than discarding work (`oc_runipd.py:5412-5431,5434-5447`). Verified reachable-but-bounded: no code path forks concurrent finalizes today (`ipd_set_executor.py` is a pure scheduler with no `Popen`/thread pool, and both drivers run their queue serially), so the contention is operator-driven (two `aw oc run` sessions in one checkout, which the maintainer notes is normal here). NOT changed by this plan: adding bounded retry/wait would be a new policy on a shipped surface. Recorded so the first operator to see `ipd finalize writer lock held by active PID` knows it is this plan's intended consequence.
- THE UPSTREAM PORT WAS REJECTED ON MEASUREMENT, not preference. Cherry-picking lane `7p9n2v`'s four commits onto `main` gives 1 clean + 1 conflicting (5 hunks across both drivers) + 2. The conflicting commit drags in `wtiso` Phase-1 code absent from `main` (lane-relative prompt assembly, `AW_MISSING_INPUT`, clean-base gate), i.e. it is not separable from an unlanded phase. The part that actually closes `dh0uno` is the `ipd_lifecycle` re-anchoring, reproduced here in ~50 lines instead of 859 plus a conflict.

## Proposed changes (ordered, validatable)

1. `agent_workflows/ipd_lifecycle.py`: add `checkout_control_root`; re-anchor `receipt_dir` and `_runtime_dir` on it; document `_repo_root` as PRODUCT-only.
2. `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`: `sync_receipt_into_worktree` becomes a documented no-op.
3. `tests/test_statefork_dh0uno.py`: new real-worktree regression suite.
4. `tests/test_wtiso_characterization.py`: invert the pinned receipt-copy test onto a real worktree.
5. `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`: correct the receipt assertion in both isolation tests.

## Deferred / out of scope (with reason)

- RELOCATING control state OUT of the repository (an XDG state dir) - `wtiso` Phase 4 `58ha43`. Not needed to close `dh0uno`: a single in-repo, gitignored control root already removes the fork. Because the location is now computed in ONE function, a later relocation is a small change.
- The typed `ExecutionContext`/`PathResolver` + AST guard from `7p9n2v`. Deliberately not ported: 859 lines and a 5-hunk conflict entangled with unlanded Phase-1 code, for an invariant this plan secures directly. Re-propose on merit if a future need appears.
- `wtiso` Phases 4-5 generally (~22 unlanded commits across lanes `58ha43`/`2c122z`): architecture built against a `main` that has since moved 300+ commits, addressing no named `wtiso` failure.
- The 5 pre-existing `make test-all` failures (CLI-surface declaration + one find-plans test). Proven pre-existing by a baseline run with this fix reverted; not this plan's to fix.
- Deleting the `wtiso` lane worktrees/branches. They hold 77 unique commits; pruning is a separate, human-gated decision.
- STALE IN-CODE POINTERS TO THE RETIRED PHASES, and the missing successor tracker for Phase 4 (added at review, PR-004/PR-005). Six modules still name `58ha43`/`2c122z`/`7p9n2v` or "wtiso Phase 4/5" as the live OWNER of unbuilt work (`agent_workflows/runner_stop.py:35,43-47`, `runner_shutdown.py:202,317`, `wtiso_gate.py:152-156,186`, `oc_runipd.py:1572`, `agy_runipd.py:789`), and spec `c4gd2h` OQ-03 (`- Status: implementing`) resolves the stop-request location by CITING `58ha43` E-01/E-02 and states the out-of-repo path "REQUIRES `wtiso` Phase 3+4 ... to be executed first". Those plans are now `superseded` and unlanded, so each pointer names a plan that will never run. Deliberately NOT fixed here: the retirement itself landed in `70b5338a`, a SEPARATE commit outside this plan's fence, and rewriting six modules' prose plus a spec's resolved OQ is a distinct concern that would blow this plan's scope and re-open a signed-off spec question. E-06 in the Spec / documentation sync section files the backlog item instead, so the debt is tracked where `aw attention` can see it rather than left in prose.

## Scope check

- Over-scope: none. Every touched path is a control-path constructor, a now-redundant copy helper, or a test pinning that behavior.
- Under-scope: none for `dh0uno`. `aw`'s OTHER cwd-relative control root, `state_root` in the two drivers (`oc_runipd.py:2750`, used for `.aw/records/runs/<run_id>`), is NOT re-anchored here: the driver always computes it from the main-repo `repo` argument, never from a lane, so it does not fork in practice. Named explicitly so the omission is a recorded decision rather than an oversight.

## Required tests / validation

Bare `python3 -m pytest` (the configured fast subset) plus `make test-all`, with the pre-existing failures identified BY NAME via a baseline run with the fix reverted. The new regression file must be shown to FAIL without the fix, since a test that cannot fail proves nothing.

## Spec / documentation sync

Backlog `dh0uno` moves to `done` citing this plan. The `wtiso` plans are retired to `superseded/` with banners citing where each of the three intents went. Both are ALREADY DONE and verified at review: `dh0uno` is at `.aw/records/backlog/done/20260828-statefork-01-dh0uno-...backlog.md` (`- Status: done`, closed in `72646cf5`), and the seven `wtiso` plans carry `RETIRED 2026-09-02` banners in `superseded/` (`70b5338a`).

Spec sync, CORRECTED at review. The original "N/A" was too strong. No spec claims the forked-control-root behavior, so nothing must be RETRACTED, and `7ckptx` (lane containment) is indeed a different concern. But spec `c4gd2h` (`- Status: implementing`) OQ-03 grounds its RESOLVED stop-request location on `wtiso` Phase 4 (`58ha43`) and declares that path blocked on Phase 3+4 executing first - and this plan's retirement of those phases makes that dependency unsatisfiable. The correct sync is therefore not an edit to `c4gd2h` (its resolved answer still describes where the flag WILL live, and `runner_stop.py` already resolves through the shared accessor so nothing is broken TODAY) but a tracked successor item, per the Deferred entry above.

E-08 below performs that sync.

## Open questions

### OQ-01: Should the control root be relocated out of the repository now, as wtiso Phase 4 intended?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: No. Resolved from repository evidence rather than deferred: the fork `dh0uno` describes is caused by cwd-relative RESOLUTION, not by in-repo LOCATION, so collapsing every worktree onto one in-repo root fully closes it (proved by the E-04 tests). Relocation is an independent concern (keeping machine state out of a product tree) that Phase 4 bundled with it, and it carries migration cost for existing receipts. Since the location is now decided in ONE function, deferring is cheap and reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: from a real lane worktree, `checkout_control_root(<lane>)` equals `checkout_control_root(<main>)`; and for a plain temp dir and a nonexistent dir it returns `<that dir>/.aw`. Pasted interpreter output plus the passing `NonGitFallbackTests`.
  - Observed evidence: from a real `git worktree`, `main receipt_dir: <clone>/.aw/state/ipd-lifecycle` and `lane receipt_dir: <clone>/.aw/state/ipd-lifecycle` -> `SAME (fixed): True`; `main runtime: <clone>/.aw/state/runtime` and `lane runtime: <clone>/.aw/state/runtime` -> `SAME (fixed): True`; plain temp dir -> `non-git fallback: /tmp/tmpyuvyigt7/.aw/state/ipd-lifecycle -> True`. `NonGitFallbackTests` (both cases, including the nonexistent dir) pass in the V-02 run.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the four control-path accessors agree across worktrees while `_repo_root` still differs; shown by `ReceiptStoreIsCheckoutScopedTests`, `RuntimeStateIsCheckoutScopedTests`, and `ProductTreeStaysPerWorktreeTests` passing.
  - Observed evidence: `python3 -m pytest tests/test_statefork_dh0uno.py` -> `9 passed` (rolled into the `119 passed in 5.61s` primary-checkout run in V-03). The pre-fix reproduction, for contrast, measured with two real worktrees: `main receipt_dir: <checkout>/.aw/state/ipd-lifecycle` vs `lane receipt_dir: <lane>/.aw/state/ipd-lifecycle` -> `FORKED (dh0uno reproduced): True`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the copy is inert, and no `*.receipt.json` exists anywhere under the lane's `.aw` after calling it (the `rglob` assertion in the inverted characterization test).
  - Observed evidence: in the PRIMARY checkout, `python3 -m pytest tests/test_statefork_dh0uno.py tests/test_wtiso_characterization.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` -> `119 passed in 5.61s`. Before E-03, the same suite failed 10 tests with `shutil.SameFileError: PosixPath('.../agy001.receipt.json') and PosixPath('.../agy001.receipt.json') are the same file`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: THE FALSIFIABILITY CHECK. With the `ipd_lifecycle` change reverted (`git stash`) and the new tests kept, the new file must FAIL; restored, it must PASS.
  - Observed evidence: in the PRIMARY checkout, `git stash push -- agent_workflows/ipd_lifecycle.py` then `python3 -m pytest tests/test_statefork_dh0uno.py` -> `8 failed, 1 passed in 2.02s`, naming `test_receipt_dir_does_not_fork_per_worktree`, `test_receipt_dir_anchors_on_the_main_worktree`, `test_receipt_path_for_agrees_across_worktrees`, `test_a_receipt_written_from_main_is_visible_from_the_lane`, `test_finalize_lock_is_exclusive_across_worktrees`, `test_finalize_journal_is_observable_across_worktrees`, and both `NonGitFallbackTests`. Fix restored -> `119 passed` (see V-03). The 1 pre-fix pass is `ProductTreeStaysPerWorktreeTests`, correctly: the product tree was never broken.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: whole-suite state, with `make test-all` failures shown pre-existing by a reverted-fix baseline.
  - Observed evidence: in the PRIMARY checkout, bare `python3 -m pytest` -> `4013 passed, 3 skipped, 4 xfailed in 64.70s` pre-commit and `4013 passed, 3 skipped, 4 xfailed in 50.88s` re-run after the commit. `make test-all` (measured in the validation clone) -> `5 failed, 4410 passed, 3 skipped, 4 xfailed`, the five being `test_zero_undeclared_parser_leaves`, `test_every_subparser_has_fuller_description`, `test_no_undeclared_parser_leaves`, `test_find_plans_agent_mode`, `test_every_declared_leaf_gets_a_full_scenario_row_set`. Baseline there with the fix reverted -> `13 failed`, i.e. the same 5 CLI failures plus the 8 expected new-test failures, proving the 5 are PRE-EXISTING and not mine. HONEST SCOPE NOTE: the `make test-all` numbers come from the clone, not this checkout; the bare-suite numbers above are from here.
  - Result: pass

- [ ] V-06 validates E-06
  - Required evidence: paste the two new tests passing, AND paste an interpreter transcript showing that with `subprocess.run` patched to raise `FileNotFoundError` (git absent) and separately `OSError(EAGAIN)` (fork failure), `receipt_dir`, `finalize_lock_path` and `release_finalize_lock` each RETURN rather than raise. Additionally show the `finally:`-masking case is gone: raise a sentinel exception with `release_finalize_lock` in the `finally:` under the patch, and show the SENTINEL propagates (not a git error) and the lock file is REMOVED. A test that only patches the return value proves nothing here; the failure mode is a RAISE from spawn.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste a counted measurement, in the same shape as the review's (count `subprocess.run` invocations whose argv starts with `git` across N repeated path lookups) showing 1 fork for the first lookup and 0 for the rest, versus the pre-fix 15-for-15. ALSO paste the full `tests/test_statefork_dh0uno.py` run, because the cache is the change most likely to make a per-worktree test read a stale entry: a green real-worktree suite is the correctness half of this V-item and the count is only the performance half.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the created item's path and id6, its `- Status: open` line, the absence of a `Blocks-Release` field, and `aw backlog check` output showing no new violation attributable to it (the repo already has 3 pre-existing `backlog.summary-unsafe` violations on unrelated items, measured at review; the count must not grow).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was AUTHORED FROM COMPLETED WORK: the change was developed and validated in a throwaway clone first, because the two files it touches (`oc_runipd.py`, `agy_runipd.py`) were occupied by two live `aw oc run` drivers in the shared checkout, and editing them under a running driver risks corrupting work in flight. Those runs have since ended (one died and was cleaned up by another agent), and the change was then RE-APPLIED and RE-VALIDATED in the PRIMARY checkout: the V-items above cite the primary-tree runs, including the reverted-fix falsifiability baseline, and say so explicitly where a number came from the clone instead. No evidence is remembered or expected.

The code landed in `6771e590` (path-scoped, 7 files, no push). A `ruff-format` hook rejected the first attempt and rewrapped two assertions; per the execution contract the staged set was RE-VERIFIED after that failure (it still contained only my 7 paths), the narrowed suite was re-run on the formatted code (`119 passed in 5.61s`), and the bare suite was re-run after committing (`4013 passed, 3 skipped, 4 xfailed in 50.88s`).

Execution contract: touch ONLY the declared Scope-Paths; path-scoped commits (`git commit -m msg -- <paths>`), never `git add -A`/bare/`-a`, never `--no-verify`, never push, never a tag or release. Before every commit run `git diff --cached --name-only` and `git restore --staged <path>` anything not mine - mandatory here, because a concurrent `antigravity` session is committing to this same checkout and a failed pre-commit hook can leave a co-worker's path staged. Re-verify after any failed commit attempt.

Post-gate lifecycle move, CORRECTED at review (PR-003). The original instruction jumped straight to `aw ipd finalize` and would have FAILED, because authoring-from-completed-work skipped `aw ipd begin`, so no receipt exists. MEASURED at review: `aw ipd finalize eulhzt ...` returns `refused: no begin receipt for eulhzt: run 'aw ipd begin' first (fail-closed: no receipt = no execution authority)`, naming `.aw/state/ipd-lifecycle/eulhzt.receipt.json`, and that file is absent while 24 sibling receipts are present. The sequence is therefore:

1. Get human approval (`aw ipd set approved ...`); `begin` gates on an approved plan.
2. `aw ipd begin <plan> --actor <agent/model>` FIRST, to create the receipt this plan never had.
3. Execute E-06, E-07 and E-08, which are the only items with work left; E-01..E-05 landed in `6771e590`.
4. Re-run bare `python3 -m pytest` in the PRIMARY checkout and paste it. Baseline measured at review on current HEAD: `4092 passed, 3 skipped, 4 xfailed`. `make test-all` additionally shows 5 PRE-EXISTING CLI-surface/find-plans failures, re-verified by name at review and NOT this plan's; do not report them as regressions and do not "fix" them here.
5. `aw ipd lint --phase pre-transition` (clean and verified at review).
6. `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`, and EXPECT to supply `--scope-ack` for every Scope-Paths entry E-06/E-07/E-08 did not touch. MEASURED at review by running the real `_reconcile_scope` against this plan's fence with an empty changed-set: finalize demands 7 acks and fails closed without them, printing the exact re-invocation. That is the designed missing-work check working correctly on a plan whose code landed before its receipt existed, not a bug; answer it honestly (`=landed-in-6771e590` for the paths already committed) rather than widening the fence to hide it.

Do not mark executed on the strength of the `/tmp` validation alone; the primary-tree run is the one that counts.
