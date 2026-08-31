# IPD: one cross-platform file lock via filelock, replacing every raw fcntl call site

- Date: 2026-08-30
- Kind: child
- Concern: `fcntl` is a POSIX-only stdlib module and SIX modules import it at top level, so on Windows the package crashes at import before any of its own code can run. That makes spec `c4gd2h` A10 unachievable as written (it promises a portable subset plus loud failure, which a program that cannot start cannot deliver) and it is why `71vjbn` had to stop with E-07/E-08 blocked: the agent was told to write the platform boundary into the help text and could not honestly say what that boundary is.
- Scope: Introduce ONE lock helper backed by `filelock`, declare `filelock` as a runtime dependency, and route every raw `fcntl.flock` call site through it. Excludes changing any lock's SEMANTICS (each stays exclusive/non-blocking exactly as it is today), excludes the process-tree kill and signal handling (POSIX-only for different reasons, not addressed here), and excludes writing the A10 platform claim itself (that is `71vjbn` E-07, unblocked by this plan).
- Scope-Paths: pyproject.toml, agent_workflows/platform_lock.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/agy_sessions.py, agent_workflows/project_registry.py, agent_workflows/run_ledger_store.py, agent_workflows/runner_stop.py, agent_workflows/runner_shutdown.py, tests/test_platform_lock.py
- Item-Dependencies: none
- Status: to-review
- Set: locksafe
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: y6mfgo
- Blocks-Release: next

## Workflow history

- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored at the maintainer's direction after `71vjbn` executed `partial` with E-07/E-08 blocked on the A10 platform question. The maintainer chose to FIX the portability rather than document a limitation, and chose `filelock` over a hand-rolled abstraction after I raised the `msvcrt.locking` byte-range hazard. That choice SUPERSEDES the `platform_lock` portion of approved plan `2c122z`, which planned to hand-roll the same thing (18 references there).

## Goal

Make the package importable and its locks correct on any platform, by having exactly one lock implementation instead of fifteen raw calls to a POSIX-only primitive.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one lock, declared and implemented

- [ ] E-01 Declare `filelock` as a RUNTIME dependency in `pyproject.toml`. Today `dependencies = []`. This is permitted and not a violation: DECISIONS D138 states the operative principle is dependency MINIMIZATION, not prohibition, and says to add one "only when it adds real value". Record the justification in the dependency comment beside the existing `[test]` notes, so a later reader does not mistake it for drift. DECLARE IT EVEN THOUGH IT IS ALREADY IMPORTABLE HERE: `filelock` 3.29.7 is present in this environment only as a transitive dependency of something else, and relying on that is exactly the class of bug the `pytest-randomly` comment in `pyproject.toml` already documents, where a maintainer venv works and a clean install does not. Pin a floor, not an exact version.
  - Depends on: none
  - Expected outcome: `pyproject.toml` declares `filelock` with a version floor and a comment citing D138; a clean install into a fresh venv provides it; the comment explains why a runtime dep was justified here.
  - Execution state: pending

- [ ] E-02 Create `agent_workflows/platform_lock.py` with ONE exclusive, non-blocking file-lock helper wrapping `filelock`. It must preserve TODAY'S semantics exactly: every existing call site uses `LOCK_EX | LOCK_NB`, i.e. take it exclusively and fail IMMEDIATELY if another holder has it, never wait. So the helper's default must be non-blocking with a distinguishable already-held outcome, because several callers convert that into an operator-facing message (`oc_runipd.run_lock` raises `DriverError("Run is already controlled by another process")`). Do NOT add a blocking mode "for completeness"; nothing needs it and an accidental block would hang a driver. Name the module `platform_lock` to match what `2c122z` already refers to (18 references), so that plan's prose still resolves.
  - Depends on: E-01
  - Expected outcome: one helper providing exclusive non-blocking acquire, release, and a distinguishable already-held signal; no blocking mode; the module imports cleanly on this platform and has no POSIX-only import of its own.
  - Execution state: pending

### Task group 2: migrate every call site, change no behavior

- [ ] E-03 Route all FIFTEEN raw `fcntl.` call sites through the helper and remove the six top-level `import fcntl` statements. MEASURED inventory so nothing is missed: `oc_runipd.py:1498`, `agy_runipd.py:1302`, `runner_stop.py:430`, `agy_sessions.py:38,39`, `project_registry.py:277,293`, `run_ledger_store.py:339,351`, and `runner_shutdown.py:256,280,283`. Note `runner_shutdown.py` ALREADY guards its import in a `try/except ImportError` with a `fcntl = None` fallback and an `if fcntl is not None:` check, which is the in-repo precedent for how carefully this was treated; that guard becomes unnecessary once the helper owns it, so remove the guard rather than leaving a dead branch. Preserve each site's existing ERROR HANDLING: `BlockingIOError` is what callers catch today, so the helper's already-held signal must reach them in a form each site still handles, or each site must be updated in the same pass.
  - Depends on: E-02
  - Expected outcome: zero `fcntl.` references remain in `agent_workflows/`; zero top-level `import fcntl`; every previously-caught already-held case is still caught and still produces the same operator-facing message.
  - Execution state: pending

- [ ] E-04 Prove the lock still EXCLUDES, which is the property that matters and the one a refactor can silently break. Add `tests/test_platform_lock.py` asserting from two separate PROCESSES (not two handles in one process, which can pass on a broken implementation) that the second acquisition of the same lock file fails immediately rather than succeeding or hanging. Also assert the release path frees it. THIS IS THE HAZARD THAT MOTIVATED CHOOSING `filelock` OVER HAND-ROLLING: Windows `msvcrt.locking` locks a BYTE RANGE from the current file position, not the whole file, so a naive port lets two processes lock disjoint ranges of one file and BOTH believe they hold it. A prior review of `2c122z` caught exactly that. The test must therefore be a real mutual-exclusion test, not a smoke test.
  - Depends on: E-03
  - Expected outcome: a two-process test shows the second acquire failing immediately; release frees the lock; the test FAILS against an implementation that locks only a byte range or that silently degrades to no-op.
  - Execution state: pending

- [ ] E-05 Prove the package now IMPORTS without `fcntl`, since that is the whole point. Simulate its absence (block the module in `sys.modules` or via an import hook) and assert every module in the E-03 inventory still imports. Do NOT settle for "it works on Linux": the defect is invisible on Linux by construction, so a test that does not simulate the absence tests nothing about the fix.
  - Depends on: E-03
  - Expected outcome: with `fcntl` unavailable, all six previously-affected modules import successfully and a lock can still be acquired; the same test fails against the pre-fix code.
  - Execution state: pending

- [ ] E-06 Record the consequence for the two plans this touches, in their records rather than only here. `2c122z`'s `platform_lock` portion is SUPERSEDED by this plan and must not be built twice; note it there so whoever executes that lane does not reimplement it. And `71vjbn` E-07/E-08 are UNBLOCKED, since the A10 platform question now has a factual answer; note it there too. Do NOT change either plan's status: `2c122z` is a stranded lane awaiting `6knsrx`, and `71vjbn` still needs its E-07/E-08 executed before it can finalize.
  - Depends on: E-04, E-05
  - Expected outcome: both plan records carry a dated note; neither plan's `Status` is changed; the notes name this plan's id6 so the link is traceable in both directions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- MEASURED: 15 `fcntl.` call sites across 6 modules with a top-level `import fcntl`, plus `runner_shutdown.py` which uses it behind a guarded import. Nothing else in the package touches it.
- Every single call site uses `LOCK_EX | LOCK_NB`. There is no blocking or shared-lock use anywhere, which makes the helper's contract narrow and the migration mechanical.
- `runner_shutdown.py` already models the careful approach with `try: import fcntl / except ImportError: fcntl = None` and an `if fcntl is not None:` guard, whose comment reads "POSIX-only primitive; the module must stay importable without it." Someone already understood this problem in one file; this plan generalizes it.
- `filelock` 3.29.7 is ALREADY IMPORTABLE in this environment, but only transitively. E-01 declares it precisely because an accidental transitive install is not a dependency.
- DECISIONS D138 is the governing rule and it permits this: "the operative principle is DEPENDENCY MINIMIZATION, not prohibition... add one only when it adds real value". It also records that earlier stdlib-only choices were pragmatic preferences, not mandates.
- Spec `c4gd2h` A10 is the requirement this unblocks: "On a platform without POSIX signal semantics, the documented portable subset still provides level 1 and the out-of-band `stop` command, and the unsupported triggers fail loudly rather than silently doing nothing."

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | 6 modules | A top-level `import fcntl` makes the whole package unimportable on Windows, so nothing downstream of it can run, including any code that would report the limitation. | `grep -l '^import fcntl' agent_workflows/*.py` returns oc_runipd, agy_runipd, agy_sessions, project_registry, run_ledger_store, runner_stop |
| F2 | HIGH | spec `c4gd2h` A10 | A10 cannot be satisfied while F1 holds: a portable subset and a loud failure both require the program to start. This is why `71vjbn` executed `partial` with E-07/E-08 blocked rather than guessing a platform claim. | A10 text; `71vjbn` outcome JSON recording E-07/E-08 blocked on orchestrator OQ-02 |
| F3 | HIGH | `msvcrt.locking` | The hand-rolled path has a subtle correctness trap, which is the decisive argument for `filelock`: `msvcrt.locking` locks a BYTE RANGE from the current file position, so two processes can lock disjoint ranges of the SAME file and both believe they hold an exclusive lock, silently defeating mutual exclusion. A prior `2c122z` review found this independently. | that review's PR-002 finding; `msvcrt` documentation semantics |
| F4 | MED | `2c122z` | This plan SUPERSEDES that plan's `platform_lock` work (18 references there). Both would create the same module; letting both proceed guarantees a collision on a stranded lane that is already hard to land. | `grep -c platform_lock` in `2c122z` = 18 |
| F5 | MED | `pyproject.toml` | `filelock` being importable here is NOT evidence it is available to users: it is transitive. The file itself documents this failure mode for `pytest-randomly`, where a maintainer venv and a clean install ran different suites. Declare it. | `dependencies = []`; the `pytest-randomly` comment; `filelock.__version__` = 3.29.7 present but undeclared |
| F6 | LOW | `runner_shutdown.py` | One module already handles this correctly with a guarded import and a `fcntl is not None` check. Its guard becomes dead once the helper owns the concern and should be REMOVED rather than left as a misleading branch. | `runner_shutdown.py:47-49`, `:254` |

## Proposed changes (ordered, validatable)

1. Declare `filelock` with a justification citing D138 (E-01).
2. Add one exclusive non-blocking lock helper named `platform_lock` (E-02).
3. Migrate all 15 call sites and delete the 6 top-level imports plus the now-dead guard (E-03).
4. Prove mutual exclusion across two real processes (E-04).
5. Prove the package imports with `fcntl` absent (E-05).
6. Record the supersession in `2c122z` and the unblocking in `71vjbn` (E-06).

## Deferred / out of scope (with reason)

- WRITING THE A10 PLATFORM CLAIM. That is `71vjbn` E-07. This plan makes the claim writable by making the answer factual; it does not write it.
- THE PROCESS-TREE KILL AND SIGNAL HANDLING. `os.killpg`/`getpgid` and the SIGINT/SIGTERM ladder are also POSIX-only, but for a different reason (there is no Windows equivalent to substitute, only a Job Object redesign). A10's "portable subset" language anticipates exactly that split. Out of scope here.
- CHANGING ANY LOCK'S SEMANTICS. Every site stays exclusive and non-blocking. A refactor that also changes behavior cannot be validated by "the suite still passes".
- ACTUALLY SUPPORTING WINDOWS END TO END. This removes one hard blocker; it does not claim the runner works on Windows. Do not overstate the outcome.

## Scope check

- Over-scope: none. Each declared path either holds a call site being migrated, is the new module, or is the dependency declaration.
- `runner_shutdown.py` is declared even though it already guards its import, because F6's dead guard should be removed in the same pass rather than left behind.
- Under-scope: NONE OUTSTANDING. The call-site inventory is measured, not estimated, and stated in E-03 so a reviewer can check completeness by grep rather than by trust.
- CONTENTION WARNING: `oc_runipd.py`, `agy_runipd.py` and `runner_stop.py` are among the most-edited files in this repo and several lanes touch them. Re-read each immediately before editing and verify the staged set before committing.

## Required tests / validation

- `tests/test_platform_lock.py` must pass, with the mutual-exclusion test using TWO PROCESSES. A same-process double-acquire is not sufficient evidence and will pass against a byte-range implementation (F3).
- FALSIFIABILITY, both directions and both mandatory: the exclusion test must FAIL against an implementation that locks only a byte range or degrades to a no-op; the import test must FAIL against the pre-fix code with `fcntl` blocked.
- Every existing lock-related test must pass UNCHANGED. Locate them first (`tests/test_runner_shutdown.py` and anything asserting the "already controlled by another process" message) and treat a failure there as evidence the migration changed semantics, not as a test to update.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- VALIDATE IN THE PRIMARY CHECKOUT, not a scratch worktree: a detached worktree fails ~15 `test_run_viewer.py` tests that pass in the primary tree because state resolves relative to the worktree (backlog `dh0uno`).
- BASELINE IS A MEASUREMENT: `3812 passed, 3 skipped, 4 xfailed` at HEAD `07859307`. Take your own before/after readings with their HEAD; this repo moves hourly.
- Paste a clean-venv install proving `filelock` is actually provided by the declared dependency rather than by an accident of this machine.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- Spec `c4gd2h` A10 becomes ACHIEVABLE with this plan, but its text is unchanged and no spec edit is required. Record in the terminal history that A10's blocker is removed and that `71vjbn` E-07 can now state a factual boundary.
- `pyproject.toml`'s dependency comment must explain WHY this runtime dep was justified, citing D138, so the next reader does not treat `dependencies` becoming non-empty as an accident.
- If `platform_lock.py` gets a module docstring, state the non-blocking-only contract explicitly, so nobody later adds a blocking mode that could hang a driver.

## Open questions

### OQ-01: `filelock` or a hand-rolled abstraction?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `filelock`, by maintainer decision, and the technical argument supports it. The hand-rolled path (`2c122z`'s plan) must reimplement Windows locking with `msvcrt.locking`, whose byte-range semantics let two processes hold "exclusive" locks on one file simultaneously (F3) - a silent correctness failure that a prior review had already caught once. `filelock` handles that, is a single mature dependency, replaces 15 call sites with one import, and is permitted by D138 as a justified dependency. The cost is honest and small: the shipped package goes from zero runtime dependencies to one, which matters to some users, and it supersedes part of an approved plan (F4). Both are recorded rather than hidden.

### OQ-02: Should the helper offer a blocking mode?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. Every one of the 15 existing call sites uses `LOCK_EX | LOCK_NB`, so nothing needs blocking, and several callers convert the already-held case into an operator-facing refusal rather than a wait. Adding an unused blocking mode would create a way to hang a driver indefinitely for no current benefit. If a genuine need appears later it can be added with its own justification; speculative generality here is a hazard, not a courtesy.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `pyproject.toml` diff showing the declared dependency with its floor and the D138-citing comment. Paste a FRESH-VENV install transcript showing `filelock` arriving from this declaration; an import succeeding on the current machine does not demonstrate this, because it is already present transitively.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the helper's public surface. Show it is non-blocking by default and that the already-held case is distinguishable from other errors. Paste a grep proving no blocking mode was added, and that the module has no POSIX-only import.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -rn "fcntl" agent_workflows/` returning ZERO hits. Paste, for at least `oc_runipd.run_lock`, the before/after showing the already-held case still produces the same operator-facing message ("Run is already controlled by another process"). Confirm `runner_shutdown.py`'s dead `fcntl is not None` guard was removed rather than left.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the two-PROCESS exclusion test passing, and state explicitly that it uses two processes rather than two handles. Paste it FAILING against a byte-range-style implementation, which is the F3 hazard it exists to catch. Paste the release path freeing the lock.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the test importing all six previously-affected modules with `fcntl` made unavailable, and a lock still being acquired. Paste the SAME test failing against pre-fix code. A test that only passes on Linux without simulating the absence does not validate this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the dated notes added to `2c122z` and `71vjbn`, each naming this plan's id6. Paste both plans' `- Status:` lines showing they are UNCHANGED.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, under the thresholds. One concern: replace a POSIX-only primitive with one portable helper without changing any lock's behavior.

Open questions: BOTH RESOLVED. OQ-01 chooses `filelock` on the maintainer's decision plus the byte-range correctness argument. OQ-02 declines a blocking mode because nothing needs one and it would add a way to hang a driver.

Scope fence: touch ONLY the declared paths. Do NOT change any lock's semantics. Do NOT touch the signal handling or the process-tree kill (POSIX-only for a different reason, deliberately deferred). Do NOT write the A10 platform claim (that is `71vjbn` E-07). Do NOT change the status of `2c122z` or `71vjbn`. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT claim this makes the runner work on Windows: it removes ONE blocker, and the signal handling remains POSIX-only. Say that plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped, never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. Several sessions commit to this checkout concurrently and three of the declared files are among the most contended in it.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
