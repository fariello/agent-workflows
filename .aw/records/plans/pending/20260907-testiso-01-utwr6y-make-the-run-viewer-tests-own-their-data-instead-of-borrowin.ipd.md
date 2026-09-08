# IPD: Make the run viewer tests own their data instead of borrowing the machine's live run tree

- Date: 2026-09-07
- Kind: child
- Concern: 14 tests in `tests/test_run_viewer.py` read the LIVE `.aw/records/runs/` tree instead of a fixture, and that directory is GITIGNORED box-local driver state. So they pass only on a machine that has run the driver and fail everywhere else: measured 2026-09-08 in a fresh `git clone` of this repository (`14 failed, 32 passed`, 0 run dirs) versus the primary checkout (`46 passed`, 135 run dirs). The failure message names the cause exactly: `AssertionError: run- not found in no matching runs found`, i.e. the test fails on a CORRECT program, because a tree with no run directories genuinely has no runs to list.
  THREE COMPOUNDING COSTS, from the backlog item. (1) CI cannot trust the suite: any clean checkout sees 14 failures on a healthy tree, which is the "gate that false-positives on correct behavior TRAINS agents to bypass it" failure mode recorded in `gjadwm`. (2) It nearly got good work discarded: the failures appeared while validating a merge and looked like the merge's fault; three separate experiments were needed to establish they were not. (3) It hides real breakage: with 14 known-failing tests in one file, a 15th real failure is invisible in the noise.
  IT ALSO BREAKS EVERY LANE WORKTREE, which the item did not know and which raises the priority. `.aw/records/runs/` is gitignored, so an isolated lane worktree gets ZERO run dirs and reproduces the fresh-clone failure exactly. Measured 2026-09-08 in this plan's own authoring worktree: 0 run dirs, `14 failed, 32 passed`, byte-identical failure set to the fresh clone. Since `aw oc run` isolates every item in a lane worktree BY DEFAULT, every executing agent sees these 14 failures in its baseline and must reason them away. That is exactly the "~32 failures inside a lane worktree" confusion observed tonight, of which these 14 are the largest single contributor.
- Scope: Convert the 14 live-tree-dependent cases in `tests/test_run_viewer.py` to own their data via a synthetic run tree, so the file passes in a fresh clone, in a lane worktree, and in the primary checkout alike. Add a guard that prevents regression. Touch NO production code: the CLI's behavior on an empty tree is already correct and must not change.
- Scope-Paths: tests/test_run_viewer.py, tests/test_run_viewer_isolation.py
- Item-Dependencies: none
- Status: to-review
- Set: testiso
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: utwr6y
- From-Backlog: agrlvw
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `agrlvw`. Every claim re-measured at HEAD rather than inherited: the item said 15 failures, the current count is 14 (verified in a fresh clone AND in a lane worktree, identical sets), so the plan states 14 and records the discrepancy rather than propagating the stale number. The lane-worktree reproduction is NEW evidence the item could not have had, and it is why this is worth doing before more plans execute: every isolated execution turn currently carries these 14 in its baseline.

## Goal

Make `tests/test_run_viewer.py` pass on a tree that has never run the driver, without weakening what it asserts, so a fresh clone, CI, and every lane worktree see a truthful suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: give the tests their own data

- [ ] E-01 BUILD A SHARED SYNTHETIC RUN TREE FIXTURE in `tests/test_run_viewer.py`, and reuse the pattern the file ALREADY contains rather than inventing one. `test_load_run_summary_fallback_report_md` (`tests/test_run_viewer.py:93-96`) and two other cases (`:238`, `:699`) already use `tempfile.TemporaryDirectory()`; the 14 failing cases are precisely the ones that skipped it. The fixture must write at least two `run-<ts>-<pid>/` directories under `<tmp>/.aw/records/runs/`, each with a `state.json` carrying the fields the viewer reads, so multi-run, filter, target-resolution, and `--latest-only` cases all have real material.
  DERIVE THE FIXTURE'S FIELD SET FROM THE READER, NOT FROM MEMORY. `run_viewer.discover_run_dirs` (`agent_workflows/run_viewer.py:1077-1089`) scans three roots (`.aw/records/runs`, `.aw/runs`, `.agents/runs`) for `run-`-prefixed directories. Read `load_run_summary` to enumerate which keys it consumes, and write exactly those; a fixture missing a key produces a test that passes for the wrong reason.
  - Depends on: none
  - Expected outcome: one fixture helper in the test module producing a self-contained run tree; no test reads the repository's own `.aw/records/runs/`.
  - Execution state: pending

- [ ] E-02 REPOINT ALL 14 CASES AT THE FIXTURE. The three call sites that pass the live tree explicitly are `discover_run_dirs(Path("."))` (`tests/test_run_viewer.py:53`, `:59`) and a hardcoded live path `Path(".aw/records/runs/run-20260827T212958Z-2367239")` (`:140`); the remaining cases reach it implicitly through `cli.main([...])` / `run_viewer_cli` with `dir="."`. Every one must resolve against the fixture root instead.
  DO NOT WEAKEN AN ASSERTION TO MAKE A CASE PASS. The point is that the tests keep asserting the same behavior against data they own. In particular do NOT relax `assertIn("run-", ...)` into a truthiness check, and do NOT delete the multi-run or since-filter cases; those are the ones whose data dependency is real.
  IF A CASE GENUINELY NEEDS A REAL CORPUS, make it SKIP with a reason naming why, never fail. A skip is honest; a failure on a healthy tree is not. State in the plan's report how many cases (if any) took this route and why.
  - Depends on: E-01
  - Expected outcome: all 14 previously-failing cases pass against fixture data; no assertion is weakened; any case that cannot be converted skips with a stated reason.
  - Execution state: pending

### Task group 2: stop it from coming back

- [ ] E-03 ADD A REGRESSION GUARD in a NEW file `tests/test_run_viewer_isolation.py`, so the guard cannot be silently deleted alongside the thing it guards. The guard asserts that running the run-viewer suite does not depend on the repository's own run tree. Prefer a mechanical check over a prose convention: run the viewer suite (or its collected cases) with the repo's `.aw/records/runs/` made unreadable/redirected, and assert green.
  DO NOT implement this as a grep for the string `records/runs` in the test file. That is spoofable and brittle for the same reason `check.review-finding-unescalated` refuses substring matching over prose (`check_engine.py:2645-2647`): it would pass while an implicit `dir="."` still reached the live tree, which is how 11 of the 14 cases reach it today.
  - Depends on: E-02
  - Expected outcome: a guard that FAILS against today's `test_run_viewer.py` and passes after E-02, catching the implicit `dir="."` route rather than only the explicit one.
  - Execution state: pending

- [ ] E-04 SWEEP FOR THE SAME DEFECT CLASS ELSEWHERE and report it, because the item names this as worth checking in the same pass. Determine whether any other test reads gitignored box-local state: `.aw/records/history.jsonl`, `.aw/worktrees/`, `.aw/state/runtime/`, `.aw/records/runs/`. This item does NOT fix them; it produces the list.
  REPORT, DO NOT SILENTLY WIDEN. If the sweep finds more, file a backlog item (or name it in the report) rather than pulling it into this plan's scope, which is deliberately one file plus its guard. State the count even when it is zero, since "we looked and found none" is a different fact from "we did not look".
  - Depends on: E-03
  - Expected outcome: a stated list (possibly empty) of other tests reading gitignored box-local state, with a filed item or an explicit "none found"; no additional files edited by this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. For a narrowed run that needs per-test output, clear the defaults with `-o addopts=""` rather than fighting individual flags.
- `.aw/records/runs/` is gitignored box-local driver state (per-run queue, session logs, prompts, outcomes, locks). It never arrives with a clone and never arrives in a lane worktree.
- `tests/test_run_viewer.py` ALREADY uses `tempfile.TemporaryDirectory()` in three cases, so the isolation pattern is established in-file and needs no new dependency.
- This is a SHARED CHECKOUT with concurrent agents. Run `aw runs` before starting and never revert another party's uncommitted work.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | test isolation | 14 cases read the live run tree; they fail wherever the driver has not run. | fresh clone: `14 failed, 32 passed`, 0 run dirs; primary checkout: `46 passed`, 135 run dirs (both measured 2026-09-08) |
| F-2 | HIGH | lane worktrees | The same 14 fail in every isolated lane worktree, because the gitignored run tree does not travel. NEW evidence the item lacked. | this plan's authoring worktree: 0 run dirs, `14 failed, 32 passed`, failure set identical to the fresh clone |
| F-3 | MEDIUM | stale count | The item says 15 failures; the current number is 14. Stated here so the plan is not written against a number it cannot reproduce. | item text "15 failed, 4028 passed" versus measured `14 failed, 32 passed` at HEAD |
| F-4 | MEDIUM | reach | Only 3 of the 14 pass the live tree EXPLICITLY (`:53`, `:59`, `:140`); the other 11 reach it implicitly via `dir="."`. A fix or a guard that only handles the explicit route leaves 11 live. | `grep -c 'discover_run_dirs(Path("."))\|Path("\.aw/records/runs'` = 3 |
| F-5 | LOW | not the worktree phantom | This is NOT `dh0uno` (inner `aw` resolving state against a lane worktree, now `done`). Same file, similar count, different cause: this reproduces in a plain clone with no worktree at all. | `dh0uno` is in `backlog/done/`; the fresh-clone reproduction involves no worktree |
| F-6 | LOW | fixture precedent | The isolation pattern already exists in the same file, so E-01 reuses rather than introduces it. | `tests/test_run_viewer.py:93-96`, `:238`, `:699` |

## Proposed changes (ordered, validatable)

1. Add a synthetic run-tree fixture to `tests/test_run_viewer.py`, with its field set derived from `run_viewer`'s readers (E-01).
2. Repoint all 14 cases at it, weakening no assertion, skipping-with-reason only where genuinely unavoidable (E-02).
3. Add `tests/test_run_viewer_isolation.py` guarding against the implicit `dir="."` route (E-03).
4. Sweep for the same defect class in other tests and report the list (E-04).

## Deferred / out of scope (with reason)

- FIXING any other test found by E-04's sweep: deliberately out of scope. This plan is one file plus its guard; a wider sweep becomes a different change with a different blast radius. E-04 files or names them instead.
- CHANGING `run_viewer` production code: not needed and forbidden here. "no matching runs found" on an empty tree is CORRECT behavior; the tests are wrong, not the program.
- CI running the suite in a fresh clone (the item's third suggestion): a workflow change with its own review surface. E-03's in-suite guard achieves the regression protection without touching CI.

## Scope check

- Over-scope: none. Two test files, no production code.
- Under-scope: this plan does NOT fix other box-local-state tests (E-04 reports them), does not change CI, and does not address `dh0uno`'s worktree state-fork (already `done`).

## Required tests / validation

`python3 -m pytest tests/test_run_viewer.py` green in THREE trees: the primary checkout, a fresh clone, and a lane worktree. Plus the bare full suite, judged on the delta from a self-measured baseline.

## Spec / documentation sync

N/A for specs: no contract changes, no production behavior change. No `.spec.md` file is touched, so nothing is declared in `- Scope-Paths:` for amendment.

## Open questions

### OQ-01: Should any case be allowed to keep reading a real corpus and SKIP when absent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as authored, in favor of ALLOWING it as a last resort with a stated reason, because the backlog item explicitly sanctions it ("If any case genuinely needs a real corpus, mark it so it SKIPS (not fails) when no run data is present, and say why in the skip reason"). E-02 carries that permission and requires the count and rationale to be reported, so the escape cannot be used silently to empty the file. A skip is honest; a failure on a healthy tree is not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the fixture helper's source, and paste the enumeration of `state.json` keys you derived from `run_viewer`'s readers with the symbol you read them from. State explicitly that the fixture writes under `<tmp>/.aw/records/runs/` and that `discover_run_dirs`'s other two roots (`.aw/runs`, `.agents/runs`) are either exercised or deliberately not, with the reason.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: THE LOAD-BEARING PROOF IS THREE TREES, not one. Paste `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q` output from (a) the primary checkout, (b) a FRESH `git clone` with 0 run dirs, and (c) a lane worktree with 0 run dirs. All three must show the same pass count and zero failures. Paste `ls .aw/records/runs/ | wc -l` for each tree alongside its result, since that number is what makes the (b)/(c) runs meaningful.
    Paste `git diff` for `tests/test_run_viewer.py` and confirm NO assertion was weakened: specifically show that any `assertIn("run-", ...)` still asserts the same string and that the multi-run, since-filter, and target-resolution cases still exist. State how many cases (if any) were converted to SKIP and quote each skip reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the guard FAILING against pre-change `tests/test_run_viewer.py` (`git stash` the E-02 change, run the guard, show it fail) and PASSING after. That before/after is the whole value of the item; a guard that passes both ways guards nothing.
    Prove it catches the IMPLICIT route (F-4), not only the explicit one: show the guard fails when a case reaches the live tree via `dir="."` with no literal `records/runs` string in the test body. Confirm the guard is NOT a grep over the test source.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the actual command(s) used to sweep for other tests reading gitignored box-local state (`.aw/records/history.jsonl`, `.aw/worktrees/`, `.aw/state/runtime/`, `.aw/records/runs/`) and their output. State the count even if ZERO, and for each hit either paste the filed backlog item id or state why it is a false positive. Confirm `git status --short` shows no file edited outside this plan's two Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`).

NO PRODUCTION CODE. If executing this appears to require a change under `agent_workflows/`, stop and report: the CLI's empty-tree behavior is correct and the defect is entirely in the tests. A change to `run_viewer.py` would be a different plan.

BASELINE HONESTY: measure the bare-suite baseline YOURSELF before touching anything and paste it. Do not trust a number from this plan or from a prior session; both runner modules are being edited by concurrent runs. Judge on the DELTA, and note that inside a lane worktree the pre-change baseline INCLUDES these 14 failures, so the delta is what proves the fix rather than an absolute count.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `agrlvw` (this plan carries `- From-Backlog: agrlvw` and inherits its `Blocks-Release: next`).
