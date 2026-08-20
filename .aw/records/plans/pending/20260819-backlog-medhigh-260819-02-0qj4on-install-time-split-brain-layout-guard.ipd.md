# IPD: install-time split-brain layout guard

- Date: 2026-08-19
- Kind: child
- Concern: `aw install` into a repo that already carries BOTH `.aw/system` bookkeeping AND live `.agents/workflows` content (a half-migrated / mid-awphysical state) silently proceeds. `resolve_target_layout` (`agent_workflows/engine.py:88`) returns `"aw"` the moment `.aw/system` exists (D134/D136 "`.aw/system` present is authoritative"), so `install_into_repo` (`agent_workflows/engine.py:4511`) installs the `.aw/` bundle and pointer while the stale, still-live `.agents/workflows/` tree is left untouched. The result is a split-brain layout: two workflow bundles, two pointer targets, duplicate records read by `artifact_core.SCAN_ROOTS` (see D135). Add an install-time GUARD that DETECTS this and warns/refuses (never destructive without consent) instead of producing the mixed layout.
- Scope: add a pure detector for the split-brain condition and wire it into the `_run_install` per-repo pre-flight (`agent_workflows/cli.py:2249`) BEFORE the install confirm. Non-interactive/`--yes` default is fail-safe SKIP (never auto-migrate, never delete). Interactive offers migrate-now (delegating to the existing `MigrationManager`, same path as `_handle_legacy_migration`) or continue-anyway. No change to `resolve_target_layout` semantics. Ship a test asserting the guard fires on a split-brain fixture and does NOT fire on a clean `.aw/` or clean legacy repo. Close backlog u298fd.
- Status: approved
- Set: backlog-medhigh-260819
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 0qj4on
- Approval: maintainer (human), 2026-08-19: blanket-approved the backlog-medhigh-260819 Set for unattended execution.

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-19 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body drafted from investigation of `resolve_target_layout`/`install_into_repo`/`_run_install`/`_handle_legacy_migration` and DECISIONS D134/D135/D136; status to-review.
- 2026-08-19 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; PR-02-1 (HIGH under-scope) guard relocated from `_run_install` to the D85 single shared shell `_install_one` so `aw install all` and `aw setup` (which bypass `_run_install` and call `_install_one` directly at cli.py:2376/3256) are covered - findings/proposed-changes/scope/E-04/V-04 revised; PR-02-2 canonical serial-runner note (E-05/E-06/V-06/required-tests). Anchors verified (engine.py:88/165, cli.py:1898/2036/2155/2163/2257/2260). OQ-01 remains non-blocking OPEN (executor-owned, conservative default). Verdict per open question: REVIEWED - OPEN QUESTIONS; readiness NO-GO until OQ-01 is confirmed or the human accepts the conservative default at approval.

## Goal

Stop `aw install` from silently producing a split-brain layout when a repo carries both `.aw/system` bookkeeping and live `.agents/workflows` content, by adding a conservative install-time guard that detects the mixed state and (non-interactive default) refuses/skips with a clear message, or (interactive) offers to migrate or continue, and never deletes anything without explicit consent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: detector (engine)

- [x] E-01 Add a pure detector `detect_split_brain_layout(repo_root: Path) -> bool` in `agent_workflows/engine.py` near `resolve_target_layout` (`agent_workflows/engine.py:88`). Return True iff BOTH `(repo_root / AW_SYSTEM_DIR)` exists AND `(repo_root / WORKFLOWS_DIR)` holds real content. "Real content" = the `.agents/workflows/` directory exists and contains at least one non-empty regular file that is not filtered by `is_ignored_source_path` (`agent_workflows/engine.py:165`), i.e. ignoring `__pycache__`, `.pyc/.pyo`, and `:Zone.Identifier` streams. An empty or only-cruft `.agents/workflows/` is NOT split-brain (returns False). Do not mutate anything; no git calls.
  - Depends on: none
  - Expected outcome: `engine.detect_split_brain_layout(repo)` returns True for a repo with `.aw/system/` plus a non-empty `.agents/workflows/index.md`, and False when either side is absent or `.agents/workflows/` is empty/cruft-only.
  - Execution state: performed

- [x] E-02 Add a companion `describe_split_brain(repo_root: Path) -> str` (or a small helper returning the two conflicting paths) in `agent_workflows/engine.py` that renders a single-line, non-color, agent-parseable message naming both live locations, e.g. `split-brain layout: .aw/system present AND live .agents/workflows content; run 'aw migrate-layout' to consolidate`. Pure string builder, no side effects. This is the text the CLI guard prints.
  - Depends on: E-01
  - Expected outcome: `engine.describe_split_brain(repo)` returns a stable, hyphen-only string naming `.aw/system` and `.agents/workflows`; no filesystem writes.
  - Execution state: performed

### Task group 2: wire the guard into the install pre-flight (CLI)

- [x] E-03 Add a CLI helper `_split_brain_guard(term, repo_root, args) -> str` in `agent_workflows/cli.py` modeled on `_exclude_guard` (`agent_workflows/cli.py:1898`) and `_handle_legacy_migration` (`agent_workflows/cli.py:2155`). Behavior: if `engine.detect_split_brain_layout(repo_root)` is False, return `"proceed"`. Otherwise print `term.status("warn", engine.describe_split_brain(repo_root))`. Fail-safe branch: when `getattr(args, "yes", False)` OR `not sys.stdin.isatty()`, do NOT install; print a skip line pointing at `aw migrate-layout` and return `"skip"` (mirror the `_exclude_guard` fail-safe at `agent_workflows/cli.py:1924`). Interactive branch: offer migrate-now via `_prompt_yes_no("Consolidate now with 'aw migrate-layout' (moves .agents/ content into .aw/)?", default=True)`; on yes, delegate to `MigrationManager(target_repo=str(repo_root)).execute_migration(target_backend="repository", leftover_disposition="defer")` (same call `_handle_legacy_migration` uses at `agent_workflows/cli.py:2199`), then re-check `detect_split_brain_layout`; if now False return `"proceed"`, else return `"skip"` with a message. On no, offer `_prompt_yes_no("Continue anyway and install into .aw/ beside the stale .agents/ tree?", default=False)`: yes returns `"proceed"`, no returns `"skip"`. Never delete `.agents/` here.
  - Depends on: E-02
  - Expected outcome: `_split_brain_guard` returns `"skip"` under `--yes`/non-interactive on a split-brain repo, `"proceed"` on a clean repo, and consolidates (or defers) interactively without deleting anything.
  - Execution state: performed

- [x] E-04 Wire the guard so it covers EVERY install entry point, not just `aw install <dir>`. Repository fact verified at review: `_install_one` (`agent_workflows/cli.py:2036`) is the SINGLE shared per-repo shell all entry points use (its docstring cites D85: `aw install <dir>`, `aw install all`, `aw setup`, engine `run()`); `_install_all` (calls `_handle_legacy_migration` then `_install_one` directly at `agent_workflows/cli.py:2376`) and `setup` (likewise at `agent_workflows/cli.py:3256`) do NOT go through `_run_install`'s loop. Therefore placing the guard only in `_run_install` would leave `aw install all` and `aw setup` unguarded. Guard at the ONE choke point instead: call `_split_brain_guard` at the TOP of `_install_one`, BEFORE `engine.install_into_repo(...)` (`agent_workflows/cli.py:2056`), and short-circuit with the "nochange"/skip return when it yields `"skip"` so no write happens. If the interactive migrate-now branch must still run relative to `_handle_legacy_migration`, run the split-brain detection first (it is a pure detector) and consolidate before `install_into_repo`. Confirm during execution that guarding in `_install_one` fires exactly once per repo for all three entry points and that the return value composes with the existing `"ok"/"nochange"/"failed"` tally.
  - Depends on: E-03
  - Expected outcome: a split-brain repo passed to `aw install <dir>`, `aw install all`, OR `aw setup` under `--yes` is skipped with the guard message and nothing is written; a clean repo installs unchanged through every entry point.
  - Execution state: performed

### Task group 3: tests + close backlog

- [x] E-05 Add tests to `tests/test_installer.py`. Unit test on the detector: build three throwaway repos via `tempfile`/`init_repo` (see `tests/support.py`): (a) split-brain = create `.aw/system/workflows/` plus a non-empty `.agents/workflows/index.md` and assert `engine.detect_split_brain_layout` is True and `_split_brain_guard(term, repo, args_with_yes)` returns `"skip"`; (b) clean `.aw/` = only `.aw/system/` present, assert detector False and guard `"proceed"`; (c) clean legacy = only `.agents/workflows/` present (no `.aw/system`), assert detector False and guard `"proceed"`. Add a cruft-only case: `.aw/system/` plus a `.agents/workflows/__pycache__/x.pyc` only, assert detector False. Use a stub/`mock` Term and a simple args namespace (`yes=True`) for the guard-return assertions so no interactive input is needed.
  - Depends on: E-04
  - Expected outcome: the four assertions above pass in isolation (`python3 -m pytest tests/test_installer.py -p no:xdist -k split_brain`, or under stdlib unittest `python3 -m unittest tests.test_installer -k split_brain` on 3.12+ / a named `-m` method filter).
  - Execution state: performed

- [x] E-06 Run the FULL serial suite - canonical `make test-serial` (`python3 -m unittest discover -s tests -t .`); `python3 -m pytest -p no:xdist` is an equivalent serial run only when the `.[test]` extra is installed - and paste the actual tail. Then close backlog u298fd with `aw backlog set 20260815-awphysical-01-u298fd-install-split-brain-guard --status done` (confirm the item path/verb from `aw backlog --help`). Update `DECISIONS.md` only if a NEW cross-cutting decision was made (default: no new decision; this implements the D136 posture, so a short pointer note is optional, not required).
  - Depends on: E-05
  - Expected outcome: full suite green (pasted output), backlog u298fd shows `Status: done`.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Layout resolution is deterministic and `.aw/system` present is authoritative (`agent_workflows/engine.py:88`; DECISIONS D134/D136). The guard MUST NOT change this rule; it only refuses/warns when a live legacy tree co-exists.
- Non-interactive / `--yes` installs must never change things silently: `_confirm` (`agent_workflows/cli.py:1861`) and `_exclude_guard` (`agent_workflows/cli.py:1898`) already fail-safe SKIP without a TTY. The guard follows the same contract.
- Migration MOVES, never copy-and-retain (DECISIONS D135); consolidation delegates to `MigrationManager.execute_migration(..., leftover_disposition="defer")`, the exact call in `_handle_legacy_migration` (`agent_workflows/cli.py:2199`). Never delete `.agents/` from the guard.
- Cruft filtering is centralized in `is_ignored_source_path` (`agent_workflows/engine.py:165`); reuse it so `__pycache__`/`.pyc` do not count as "live content".
- Tests: `tests/test_installer.py` mixes pure-function unit tests and subprocess end-to-end tests; helpers `init_repo`/`SOURCE_WORKFLOWS`/`REPO_ROOT` live in `tests/support.py`. Stdlib `unittest` + pytest runner.

## Findings

| Anchor | Fact | Consequence for the guard |
| --- | --- | --- |
| `agent_workflows/engine.py:88` `resolve_target_layout` | Returns `"aw"` as soon as `.aw/system` exists, ignoring any `.agents/workflows` tree | This is the exact silent-split cause; guard must intercept before install writes |
| `agent_workflows/engine.py:4511` `install_into_repo` | Installs the `.aw/` bundle + pointer for `target_layout="aw"`; does not prune or notice a live `.agents/workflows/` | No self-healing today; the mixed layout persists |
| `agent_workflows/cli.py:2036` `_install_one` (D85 single shared shell) | The ONE per-repo orchestration ALL entry points use (`aw install <dir>`, `aw install all`, `aw setup`, engine `run()`); it calls `install_into_repo` first (`agent_workflows/cli.py:2056`) | Correct choke point for a pre-write guard so no entry point is missed |
| `agent_workflows/cli.py:2376` (`_install_all`) and `:3256` (`setup`) | Call `_handle_legacy_migration` then `_install_one` DIRECTLY, bypassing the `_run_install` loop | A guard placed only in `_run_install` would NOT cover `aw install all` / `aw setup`; guard in `_install_one` instead |
| `agent_workflows/cli.py:2163` `_handle_legacy_migration` `is_legacy_only` | False when `.aw/system` exists, so the split-brain repo skips migration handling | Guard cannot rely on this handler; it must detect independently before any write |
| `agent_workflows/cli.py:1924` `_exclude_guard` fail-safe | `--yes`/non-TTY -> skip, never auto-act | Reuse pattern for the guard's non-interactive default |
| DECISIONS D135 (`DECISIONS.md:2449`) | Migration MOVES via journal; two live copies == duplicate install | Consolidation, if chosen, uses MigrationManager; guard never deletes |
| DECISIONS D136 (`DECISIONS.md:2455`) | `.aw/system` authoritative; never auto-migrate without consent, never block CI | Guard = detect + warn/refuse, non-interactive default is skip-not-migrate |

## Proposed changes (ordered, validatable)

1. `agent_workflows/engine.py`: add `detect_split_brain_layout` (E-01) and `describe_split_brain` (E-02), pure, no side effects.
2. `agent_workflows/cli.py`: add `_split_brain_guard` (E-03) and call it at the top of `_install_one` (the D85 single shared shell) before `install_into_repo`, so all entry points (`aw install <dir>`, `aw install all`, `aw setup`) are covered (E-04).
3. `tests/test_installer.py`: add detector + guard-return tests over four fixtures (E-05).
4. Run full suite and close backlog u298fd (E-06).

## Deferred / out of scope (with reason)

- Auto-consolidating (moving `.agents/` into `.aw/`) without consent: OUT (D135/D136; destructive without explicit choice). Interactive migrate-now is offered but never forced.
- Pruning the stale `.agents/workflows/` tree during install: OUT (belongs to the migration/uninstall-sweep work, Order 09 `plt26j`).
- Changing `resolve_target_layout` semantics: OUT (D134/D136 keep `.aw/system` authoritative).
- Guarding `aw update`/`aw setup` paths separately: OUT unless execution shows they bypass `_run_install`/`_install_one` (confirm in E-04); if they do, note as a follow-up rather than expand scope here.

## Scope check

- Over-scope: none. The change is a detect+warn/refuse guard plus a test; no migration engine changes, no `resolve_target_layout` change.
- Under-scope: guarding at `_install_one` (the D85 single shared shell that `aw install <dir>`, `aw install all`, and `aw setup` all funnel through) closes the entry-point-coverage gap that a `_run_install`-only guard would leave. If execution finds a DISTINCT install path that reaches `install_into_repo` without passing through `_install_one` (e.g. a direct engine `run()` caller), record that as a new backlog item rather than widening this plan.

## Required tests / validation

- New unit + guard tests in `tests/test_installer.py` (E-05): detector True on split-brain fixture; False on clean `.aw/`, clean legacy, and cruft-only `.agents/workflows/`; `_split_brain_guard` returns `"skip"` under `--yes` on split-brain and `"proceed"` on both clean layouts.
- Full serial suite green: `make test-serial` (`python3 -m unittest discover -s tests -t .`), or `python3 -m pytest -p no:xdist` with the `.[test]` extra, with pasted tail (E-06).
- Backlog u298fd set to `done` and shown (E-06).

## Spec / documentation sync

- No spec change required; this implements the existing D136 posture ("never auto-migrate without consent, never block CI"). A one-line pointer in `DECISIONS.md` is optional and only if a genuinely new decision emerges during execution; default is N/A. No user-facing README prose is required beyond the guard's own runtime message.

## Open questions

### OQ-01: Should a stale `.agents/workflows/` that contains ONLY a pointer/AGENTS shim (no workflow bodies) count as split-brain?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: Default to the conservative E-01 rule (any non-cruft non-empty regular file under `.agents/workflows/` counts). If execution finds this over-fires on freshly-migrated repos that legitimately retain an empty `.agents/` skeleton, narrow the rule to "contains at least one `.md` body other than a pure pointer" and add a fixture; record the refinement in the walkthrough. Not blocking because the conservative rule only ever refuses/warns, never deletes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: a pytest assertion (pasted) showing `detect_split_brain_layout` True for `.aw/system` + non-empty `.agents/workflows/index.md`, False when `.agents/workflows/` is absent or holds only a `.pyc`/`__pycache__` file.
  - Observed evidence: `SplitBrainLayoutGuardTests.test_detect_split_brain_layout_true_on_split_brain`, `test_detect_split_brain_layout_false_on_clean_aw`, `test_detect_split_brain_layout_false_on_clean_legacy`, `test_detect_split_brain_layout_false_on_cruft_only`, and `test_detect_split_brain_layout_false_on_empty_agents_dir` all passed in `tests/test_installer.py`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted call/assert showing `describe_split_brain(repo)` returns a hyphen-only string naming both `.aw/system` and `.agents/workflows` and pointing at `aw migrate-layout`; no filesystem mutation (repo tree unchanged before/after the call).
  - Observed evidence: `SplitBrainLayoutGuardTests.test_describe_split_brain_contents_and_no_side_effects` passed, asserting `describe_split_brain(repo)` returns `"split-brain layout: .aw/system present AND live .agents/workflows content; run 'aw migrate-layout' to consolidate."` and `tree_before == tree_after`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted test output where `_split_brain_guard` with `args.yes=True` on a split-brain fixture returns `"skip"` and no files were written into `.aw/` or `.agents/`; on a clean repo returns `"proceed"`.
  - Observed evidence: `SplitBrainLayoutGuardTests.test_split_brain_guard_returns_skip_on_yes`, `test_split_brain_guard_returns_skip_on_non_interactive`, `test_split_brain_guard_returns_proceed_on_clean_repos`, `test_split_brain_guard_interactive_migrate_now`, `test_split_brain_guard_interactive_continue_anyway`, and `test_split_brain_guard_interactive_decline_all` passed with `tree_before == tree_after`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: a subprocess or in-process assertion (pasted) that a split-brain repo is skipped with no new writes (git status / dir listing before == after) and the guard skip line is printed under `aw install <repo> --yes` AND under at least one of `aw install all --yes` / `aw setup ... --yes` (proving the `_install_one` choke point covers the non-`_run_install` entry points); a clean repo still installs through each path.
  - Observed evidence: `SplitBrainLayoutGuardTests.test_install_one_skips_split_brain_repo_without_writes`, `test_cli_install_split_brain_repo_skips_without_writes`, `test_cli_install_all_skips_split_brain_and_installs_clean`, and `test_cli_setup_skips_split_brain_repo` passed; split-brain repos were skipped with 0 files written while clean repos were installed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_installer.py -p no:xdist -k split_brain` output (pasted) showing all four fixture cases pass.
  - Observed evidence: `python3 -m pytest tests/test_installer.py -p no:xdist -k split_brain` returned 16 passed in 3.42s.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: full-suite tail from `make test-serial` (`python3 -m unittest discover -s tests -t .`), or `python3 -m pytest -p no:xdist` with the `.[test]` extra (pasted, showing passed/failed counts) AND the `aw backlog` output (or file read) showing u298fd `Status: done`.
  - Observed evidence: `python3 -m unittest discover -s tests -t .` passed (Ran 1213 tests in 212.961s, OK (skipped=1)), and `aw backlog set ... --status done` moved item to `.aw/records/backlog/done/20260815-awphysical-01-u298fd-install-split-brain-guard.backlog.md` with `Status: done`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: an executing agent commits ONLY the files it changed, path-scoped (`git commit -m <msg> -- agent_workflows/engine.py agent_workflows/cli.py tests/test_installer.py <backlog-file>`), never `git add -A`/`-a` and never `git push`. When it reports tests passed it MUST paste the ACTUAL `python3 -m pytest -p no:xdist` output, not a claim. This Order has NO hard dependency on Order 01 (`m2h1z4`) because the guard does not import `tools.awphysical`; it only reuses `MigrationManager` for the optional interactive consolidate path, which is already shipped. If execution touches or exercises the migration import path (e.g. verifying the interactive consolidate in a pip-installed context), it depends on Order 01 having shipped `agent_workflows/layout_inventory`; sequence after Order 01 in that case. After all `V-*` items carry concrete evidence and `aw ipd lint --phase pre-transition` conforms, `git mv` this plan to `.aw/records/plans/executed/` and set `Status: executed`; if any validation fails, STOP and report rather than moving the plan.
