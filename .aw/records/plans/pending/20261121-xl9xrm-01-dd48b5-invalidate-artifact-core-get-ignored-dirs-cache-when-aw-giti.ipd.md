# IPD: Invalidate artifact_core.get_ignored_dirs cache when .aw/.gitignore or .git/index changes

- Date: 2026-11-21
- Kind: child
- Concern: `agent_workflows/artifact_core.py::get_ignored_dirs` caches `git ls-files --others --ignored --exclude-standard --directory` results in `_cached_ignored_dirs` using only `(resolved_root_str, gi_mtime, ex_mtime)`, where `gi_mtime` is root `.gitignore` mtime and `ex_mtime` is `.git/info/exclude` mtime. When a legacy `.agents/` repository runs an in-process dry run that creates `.aw/state/`, `git ls-files` reports `.aw` as an ignored-only directory and caches `.aw` as ignored. When layout migration then creates `.aw/.gitignore` and commits tracked files under `.aw/records/`, neither root `.gitignore` nor `.git/info/exclude` changes mtime, so subsequent in-process `artifact_core.iter_scan_files` calls treat `.aw` as ignored and return `[]`.
- Scope: Extend the cache key of `agent_workflows/artifact_core.py::get_ignored_dirs` and `_cached_ignored_dirs` to include `.aw/.gitignore` mtime (and `.git/index` mtime, resolving `.git` cleanly for both normal repositories and git worktrees where `.git` is a gitdir pointer file), and add a behavioral regression test in `tests/test_records_untracked_backend.py` exercising an in-process `.agents/`-to-`.aw/records/` transition without manually clearing `_cached_ignored_dirs`. EXCLUDES: changing gitignore policy or modifying `tests/test_m0001_any_repo.py` (`60mazt`).
- Scope-Paths: agent_workflows/artifact_core.py, tests/test_records_untracked_backend.py, .aw/records/plans/pending/20261121-xl9xrm-01-dd48b5-invalidate-artifact-core-get-ignored-dirs-cache-when-aw-giti.ipd.md
- Item-Dependencies: none
- Status: to-review
- Short-Description: Include .aw/.gitignore and .git/index mtimes in artifact_core._cached_ignored_dirs so in-process layout migration does not hide .aw/records/.
- Work-Kind: bug
- Priority: medium
- From-Backlog: xl9xrm
- Blocks-Release: next
- Set: xl9xrm
- Order: 1
- Highest E allocated: 02
- Author: antigravity/gemini
- Id: dd48b5

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-21 to-review (aw set): Authored review-ready child plan graduated from backlog xl9xrm
- 2026-11-21 draft (antigravity/gemini): created.

## Goal

Ensure `artifact_core.get_ignored_dirs` automatically invalidates its cache whenever `.aw/.gitignore` or `.git/index` changes (including in git worktrees), so in-process layout migrations never hide newly tracked `.aw/records/` files.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Extend ignored-dir cache key and add behavioral regression test

- [ ] E-01 Update `agent_workflows/artifact_core.py::get_ignored_dirs` and `_cached_ignored_dirs` to include two additional mtime/size tokens in the LRU cache key:
  1. `aw_gi_mtime`: stat `(st_mtime_ns, st_size)` (or `(-1, -1)` when absent) for `<repo_root>/.aw/.gitignore`.
  2. `git_index_stat`: stat `(st_mtime_ns, st_size)` (or `(-1, -1)` when absent) for the repository's git index file (handling both a normal `.git/index` directory and a worktree `.git` file pointing to `gitdir: ...`, and using `st_mtime_ns` + `st_size` so rapid same-second commits still invalidate the cache).
  Keep `.gitignore` and `.git/info/exclude` in the cache key using `(st_mtime_ns, st_size)` (handling worktree `commondir` for `info/exclude` when `.git` is a file) and preserve the `_is_repository_untracked_backend` discard of `.aw/records`.
  - Depends on: none
  - Expected outcome: `artifact_core.get_ignored_dirs` invalidates automatically when `.aw/.gitignore` or the git index changes, in both normal checkouts and git worktrees, without losing cache hits on unchanged trees.
  - Execution state: pending

- [ ] E-02 Add a behavioral test in `tests/test_records_untracked_backend.py` that initializes a git repository with `.gitignore` ignoring `.aw/state/`, creates `.aw/state/` so `.aw` is initially an ignored-only directory, calls `get_ignored_dirs(repo)` (asserting `.aw` is initially ignored), then writes `.aw/.gitignore` plus a tracked file under `.aw/records/` and commits it in-process, and asserts that calling `get_ignored_dirs(repo)` and `iter_scan_files(repo)` WITHOUT clearing `_cached_ignored_dirs` no longer ignores `.aw` and returns the newly tracked file. Run `python3 -m pytest -o addopts="" -v tests/test_records_untracked_backend.py`, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Depends on: E-01
  - Expected outcome: The new behavioral test fails before E-01 and passes after E-01; `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition`, and `aw sanitize --agent` all pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/artifact_core.py::_cached_ignored_dirs` is an `@functools.lru_cache(maxsize=128)` called only by `agent_workflows/artifact_core.py::get_ignored_dirs`.
- `tests/test_records_untracked_backend.py` already imports and tests `artifact_core.get_ignored_dirs` on isolated `git init` repositories.
- Using `(st_mtime_ns, st_size)` prevents coarse filesystem timestamp granularity from masking two writes within the same second during fast automated tests.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `get_ignored_dirs` keys `_cached_ignored_dirs` only on `(resolved_root_str, gi_mtime, ex_mtime)`. | `agent_workflows/artifact_core.py::get_ignored_dirs`; observed in IPD `60mazt` on `legacy_agents_layout`, where `iter_scan_files(repo)` returned `[]` after `--apply` until `_cached_ignored_dirs.cache_clear()` was called. |

## Proposed changes (ordered, validatable)

1. Add `.aw/.gitignore` and resolved git `index` `(st_mtime_ns, st_size)` tokens to `get_ignored_dirs` / `_cached_ignored_dirs` in `agent_workflows/artifact_core.py` (`E-01`).
2. Add an in-process `.agents/`-to-tracked-`.aw/records/` regression test in `tests/test_records_untracked_backend.py` and run all gates (`E-02`).

## Deferred / out of scope (with reason)

- Removing the temporary `_cached_ignored_dirs.cache_clear()` workaround from `aw/lane/60mazt`'s unmerged `tests/test_m0001_any_repo.py`: belongs to `60mazt` when re-run.
  - Carrier: 60mazt

## Scope check

- Over-scope: none. Only `agent_workflows/artifact_core.py`, `tests/test_records_untracked_backend.py`, and this plan are modified.
- Under-scope: none. Handles both standard `.git/` repositories and worktree `.git` pointer files, plus sub-second mtime/size changes.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_records_untracked_backend.py`
- `aw suite` (core tier passes)
- `make typecheck` (0 mypy errors)
- `aw ipd lint --phase pre-transition` on this plan (`outcome: "clean"`)
- `aw sanitize --agent` (`outcome: "clean"`)

## Spec / documentation sync

N/A: internal cache invalidation bug fix with no public CLI or spec contract change.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result (which are reachable by construction), name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/artifact_core.py` summary showing `.aw/.gitignore` and resolved git `index` `(st_mtime_ns, st_size)` tokens included in the `_cached_ignored_dirs` cache key (including worktree `.git` file resolution).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste actual output from `python3 -m pytest -o addopts="" -v tests/test_records_untracked_backend.py`, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after review and approval (`approved` or `auto-approved`). Commit only files changed for this plan through `aw commit dd48b5 -- <paths>` (never `git add -A`, bare `git add`, `git commit -a`, or `--no-verify`; never push). Finalize to `.aw/records/plans/executed/` only via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
