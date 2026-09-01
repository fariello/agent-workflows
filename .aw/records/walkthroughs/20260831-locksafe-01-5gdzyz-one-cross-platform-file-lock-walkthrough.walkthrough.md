# Walkthrough: one cross-platform file lock via filelock (IPD y6mfgo)

- Plan: `.aw/records/plans/executed/20260830-locksafe-01-y6mfgo-one-cross-platform-file-lock-via-filelock-replacing-every-ra.ipd.md`
- Id: 5gdzyz
- Target-Id: y6mfgo
- Set: locksafe
- Date: 2026-08-31
- Driver run: `run-20260831T153226Z-3424176`
- Measured at HEAD: `d4febb8e` (the commit the evidence below was taken at; the product commit follows it)

## What this is

The FULL validation evidence for plan `y6mfgo`, kept here because the IPD's `Observed evidence`
fields are single-line by format and this evidence is long-form command output. Each `V-*` field in
the plan carries a one-line summary and points here; nothing in the plan is a claim this file does
not substantiate.

## What changed, in one paragraph

`fcntl` is POSIX-only and SIX modules imported it at top level, so the package failed at IMPORT on a
non-POSIX host, before any of its own code (including any code that would report the limitation)
could run. This introduced ONE lock helper, `agent_workflows/platform_lock.py`, backed by `filelock`
(now the package's single declared runtime dependency), and routed every raw `fcntl` call site
through it. No lock's semantics changed. This does NOT make the runner work on Windows: it removes
one hard blocker, and the SIGINT/SIGTERM ladder plus the `os.killpg` process-tree kill remain
POSIX-only and were deliberately out of scope.

## Three things the plan got wrong, found by measuring rather than reading

Recorded here because each would have shipped a silent regression, and because the plan had already
been through /plan-review, so these are what a second pass at the real dependency found.

1. `filelock` opens its lock file with `O_CREAT | O_TRUNC`. So routing the three read-only PROBE
   sites through it (the plan's literal "all fifteen sites" instruction) would have BLANKED a live
   driver's `pid=` record on every `aw runs`, RESURRECTED lock files that `clean_shutdown`
   deliberately unlinked, and truncated lockfiles owned by the Antigravity application in
   `agy_sessions`. Fixed by splitting the contract: `acquire()` is filelock-backed, `probe_free()`
   uses the raw primitive with no `O_CREAT`/`O_TRUNC` and returns `None` where it cannot answer.
   (Decision `01-y6mfgo-D1`.)
2. `runner_shutdown.RunLockHandle` proves by INODE IDENTITY that the path it is about to unlink still
   names the inode it locked, which is what stops it deleting a lock another live process holds.
   `filelock` does not publish its descriptor, so a naive migration would have had to re-`open()` the
   path, turning that safety check into a tautology that always passes. Fixed by exposing the locked
   descriptor (`LockHandle.fileno`) and writing the `pid=` record through an `os.dup` of it.
   (Decision `01-y6mfgo-D4`.)
3. `filelock` is RE-ENTRANT per lock object where `fcntl.flock` is not. The plan's review had already
   caught this (F7); confirmed and guarded by constructing a fresh lock object per acquisition, with
   both a behavioral test and a characterization test so the premise cannot rot silently.

## Validation evidence


### V-01 validates E-01: the declared dependency, proven from a fresh venv

`git diff pyproject.toml` (measured at HEAD `d4febb8e`), the operative lines:
```diff
-# No runtime dependencies today (DECISIONS D44/D46). This is dependency MINIMIZATION,
-# not a prohibition (D138): add a runtime dep when it adds real value, weighing the cost
-# to users; prefer the stdlib when it does the job easily. Currently the stdlib suffices.
-dependencies = []
+# ONE runtime dependency, declared deliberately. Dependency MINIMIZATION is the operative
+# principle here, NOT a prohibition (DECISIONS D138, which clarifies D44/D46): add a runtime
+# dep only when it adds real value, weighing the cost to users; prefer the stdlib when it does
+# the job easily. Everywhere else the stdlib still suffices, and this is the only exception.
+#
+# WHY `filelock` EARNS IT. Six modules used to `import fcntl` at TOP LEVEL. `fcntl` is
+# POSIX-only, so on Windows the package failed at IMPORT, before any of its own code could run
+# ... `msvcrt.locking` locks a BYTE RANGE from the current file position rather than the whole
+# file, so two processes can lock DISJOINT ranges of the same file and BOTH believe they hold
+# an exclusive lock. That is a SILENT mutual-exclusion failure ...
+#
+# A version FLOOR, not a pin: `>=3` is where the modern `filelock` API ... has been stable
+#
+# DECLARED EVEN THOUGH IT ALREADY IMPORTS on a maintainer machine, where `filelock` is present
+# only as a TRANSITIVE dependency of something else. ... An accidental transitive install is
+# not a dependency.
+dependencies = ["filelock>=3"]
```
The stale `[test]` comment that said "the shipped package currently needs none" was corrected in the same pass to "needs only the one declared above", so the file does not contradict itself.
FRESH VENV, proving the dependency is provided by the DECLARATION and not by this machine. First, the venv is genuinely empty of it:
```
$ python3 -m venv cleanvenv && ./cleanvenv/bin/python -c "import importlib.util; print('filelock found:', importlib.util.find_spec('filelock') is not None)"
filelock found: False
$ ./cleanvenv/bin/python -m pip list
Package Version
------- -------
pip     26.2.1
```
Then the install pulls it in as a dependency of this package:
```
$ /tmp/.../cleanvenv/bin/python -m pip install .
Collecting filelock>=3 (from agent-workflows==1.3.0rc2.dev1764+gd4febb8e.d20260831)
  Downloading filelock-3.32.4-py3-none-any.whl.metadata (2.0 kB)
Downloading filelock-3.32.4-py3-none-any.whl (99 kB)
Building wheels for collected packages: agent-workflows
  ...
Installing collected packages: filelock, agent-workflows
Successfully installed agent-workflows-1.3.0rc2.dev1764+gd4febb8e.d20260831 filelock-3.32.4
```
NOTE, and it strengthens the floor claim: the clean resolve picked `filelock` **3.32.4**, NOT the 3.29.7 present transitively on this machine, so the `>=3` floor was exercised against a DIFFERENT version than development used. I re-ran the lock suites against it rather than assuming compatibility:
```
$ /tmp/.../cleanvenv/bin/python -m pytest tests/test_platform_lock.py tests/test_runner_stop.py \
    tests/test_runner_shutdown.py tests/test_run_viewer_liveness.py -o addopts="" -q -m ""
126 passed in 42.04s
```
That also exercises the one private-attribute dependency (`LockHandle.fileno`) against both versions, which is what V-03/D4 rely on.

### V-02 validates E-02: the helper's public contract

PUBLIC SURFACE:
```
__all__ = ['LockBusy', 'LockHandle', 'acquire', 'held', 'probe_free', 'release_raw', 'posix_primitive']
acquire (path: 'PathLike', *, blocking: 'bool' = False, timeout: 'Optional[float]' = None) -> 'LockHandle'
held (path: 'PathLike', *, blocking: 'bool' = False, timeout: 'Optional[float]' = None) -> 'Iterator[LockHandle]'
probe_free (path: 'PathLike') -> 'Optional[bool]'
release_raw (stream: 'Any') -> 'None'
posix_primitive () -> 'Optional[Any]'
LockHandle members: ['dup_stream', 'fileno', 'is_held', 'path', 'release']
LockBusy mro: ['LockBusy', 'BlockingIOError', 'OSError', 'Exception', 'BaseException', 'object']
```
NON-BLOCKING BY DEFAULT is visible in the signature (`blocking: bool = False`) and proven behaviorally, not just declared:
```
test_the_default_is_non_blocking default acquire (no blocking= argument): refused, did not wait
test_a_second_process_is_refused_immediately second PROCESS refused in 0.0003s with LockBusy (holder pid 3664401 still alive)
```
ALREADY-HELD IS DISTINGUISHABLE from other errors, and simultaneously compatible with what every migrated site already caught. `LockBusy` is its own type (so it can be caught specifically) while still being a `BlockingIOError` -> `OSError` carrying `EAGAIN` (so the pre-existing `except BlockingIOError`, `except OSError`, and `errno in (EACCES, EAGAIN, EWOULDBLOCK)` handlers all still work):
```
test_the_refusal_is_the_shape_runner_stop_dispatches_on refusal shape: LockBusy -> BlockingIOError -> OSError, errno=EAGAIN
```
A permission or filesystem failure is deliberately NOT converted to `LockBusy`: only `filelock.Timeout` (and the blocking-mode self-deadlock `RuntimeError`) map to it, so a real error is never misreported as contention.
NO SPECULATIVE BLOCKING MODE was added: the only blocking path is E-07's single documented exception, and it is mechanically fenced to one module:
```
test_no_blocking_mode_leaked_to_a_second_caller blocking callers: ['project_registry.py:280']
```
NOT RE-ENTRANT, which E-02 requires and which the cross-process test structurally cannot show:
```
test_a_second_acquire_in_the_same_process_is_refused same-process second acquire: refused with LockBusy (NOT re-entrant)
test_the_raw_filelock_object_would_have_been_reentrant characterization: a SHARED filelock object IS re-entrant (filelock 3.29.7); platform_lock avoids it with a fresh object
```
The second line is a CHARACTERIZATION test, so this is not folklore: if a future `filelock` stops being re-entrant per object, it fails and the fresh-object-per-acquire rule can be revisited deliberately.
NO POSIX-ONLY IMPORT. The module's entire import block is stdlib plus `filelock`:
```
$ grep -n "^import\|^from" agent_workflows/platform_lock.py
59:from __future__ import annotations
61:import contextlib
62:import errno
63:import os
64:from pathlib import Path
65:from typing import Any, Iterator, Optional, Union
67:import filelock
```
`fcntl` is reached ONLY through the guarded `posix_primitive()` accessor, asserted by test:
```
test_platform_lock_has_no_posix_only_import_of_its_own platform_lock's fcntl access is guarded, not a top-level import
```

### V-03 validates E-03: every call site migrated, message preserved

E-07 chose option (a), so the expected result is ZERO `fcntl` CODE references outside `platform_lock.py`. Measured at HEAD `d4febb8e`:
```
$ grep -rn "fcntl" agent_workflows/*.py | grep -v "^agent_workflows/platform_lock.py"
agent_workflows/project_registry.py:277:    # the bare `fcntl.LOCK_EX` here did. Converting it to the non-blocking default would change
agent_workflows/run_ledger_store.py:13:top-level ``import fcntl`` that made this module unimportable on a non-POSIX host.
agent_workflows/runner_stop.py:27:imports `fcntl`, and neither do the drivers. The lock now comes from `platform_lock`, the one
agent_workflows/runner_stop.py:1599:# import-time barrier is GONE: this module and both drivers no longer import `fcntl`, taking the lock
```
All four remaining hits are PROSE (comments and docstrings explaining the migration), not code. Stated precisely because "zero hits" would be a false claim: there are zero `fcntl.` CALLS and zero imports, which is the property that matters. Both are asserted by test rather than left to this grep:
```
test_no_module_carries_a_top_level_fcntl_import no top-level `import fcntl` anywhere in agent_workflows/
test_only_platform_lock_touches_the_primitive platform_lock is the only module that touches fcntl
```
And directly:
```
$ grep -rln "^import fcntl" agent_workflows/*.py
(no output)
```
OPERATOR-FACING MESSAGE, BEFORE AND AFTER. Before, `run_lock` caught `BlockingIOError` from the raw `flock`; after, it catches `platform_lock.LockBusy` (which IS a `BlockingIOError`, so the mapping is preserved by subtyping rather than by luck) and raises the identical string. Observed live in both drivers:
```
test_oc_run_lock_refuses_a_second_holder_with_the_documented_message
  oc_runipd.run_lock refusal: 'Run is already controlled by another process: run-x'
test_agy_run_lock_refuses_a_second_holder_with_the_documented_message
  agy_runipd.run_lock refusal: 'Run is already controlled by another process: run-y'
```
THE REGRESSION NET F9 ASKED FOR NOW EXISTS. Before this plan, `grep -rln 'already controlled by another process' tests/` returned NOTHING, so V-03's promise could only ever have been a manual one-off. It is now asserted by `tests/test_platform_lock.py::OperatorMessageTests`, in both drivers, plus a third test pinning the `pid=` record inside the lock file that `run_viewer` parses back out:
```
test_the_run_lock_still_records_the_pid_inside_the_lock_file
  driver.lock content while held: 'pid=3664389 started=2026-08-31T16:33:18+00:00'
```
That third assertion turned out to be load-bearing, not decorative: `filelock` opens with `O_CREAT | O_TRUNC`, so a naive migration silently BLANKS this record (see the decisions register, `01-y6mfgo-D1`).
`runner_shutdown.py`'s DEAD GUARD IS REMOVED, not left as a misleading branch. The `try: import fcntl / except ImportError: fcntl = None` block and both `if fcntl is not None:` / `if fcntl is None:` checks are gone; `lock_is_free` is now a one-line delegation to `platform_lock.probe_free`, and `RunLockHandle.release` calls `platform_lock.release_raw`. Confirmed by the two greps above (neither `runner_shutdown.py` nor any other module appears).

### V-04 validates E-04: mutual exclusion, and it FAILS against a byte-range lock

TWO PROCESSES, STATED EXPLICITLY: the holder is a real `subprocess.Popen` running a separate interpreter that acquires the lock and blocks on `stdin.read()`, so the parent controls the contention window. It is NOT two handles in one process. The pasted `holder pid` is a different PID from the test process, which is the evidence of that:
```
tests/test_platform_lock.py::MutualExclusionTests::test_a_second_process_is_refused_immediately
  second PROCESS refused in 0.0003s with LockBusy (holder pid 3664401 still alive)
PASSED
```
The 0.0003s also validates "IMMEDIATELY": a refusal that silently waited would be a hang, since callers convert it into an operator message.
RELEASE PATH FREES IT, again across processes (a child probe reports REFUSED while held, then ACQUIRED after release):
```
tests/test_platform_lock.py::MutualExclusionTests::test_release_frees_the_lock_for_another_process
  while held: REFUSED; after release: ACQUIRED (from a separate process)
PASSED
tests/test_platform_lock.py::MutualExclusionTests::test_release_is_idempotent PASSED
tests/test_platform_lock.py::MutualExclusionTests::test_the_lock_is_dropped_when_its_holder_dies
  lock free after the holder was SIGKILLed
PASSED
```
The SIGKILL case matters beyond E-04: every liveness probe in the package depends on the kernel dropping a lock on holder death.
FALSIFIABILITY AGAINST THE F3 BYTE-RANGE HAZARD. I did not assert this by argument; I BUILT a byte-range implementation with the `msvcrt.locking` semantics (lock ONE BYTE at the current file offset, via `fcntl.lockf` with a length of 1) and ran the same two-process exclusion scenario against it. Two processes at different offsets BOTH acquired the same lock file:
```
$ python3 run_falsify.py
process A holds the 'exclusive' lock (byte 0)
RESULT: process B ALSO ACQUIRED the same lock file -> MUTUAL EXCLUSION BROKEN
=> a cross-process exclusion test MUST fail here, which is what makes it a real test

Now asserting it the way tests/test_platform_lock.py does:
  test FAILED as required: MutualExclusionTests.test_a_second_process_is_refused_immediately would FAIL:
  expected LockBusy, but the second process acquired the same lock
```
So the test genuinely discriminates: it FAILS against a byte-range lock and PASSES against the whole-file lock. That is exactly the silent failure a hand-rolled Windows port would have shipped, and the decisive argument for the dependency (OQ-01).
NON-RE-ENTRANCY, the second mandatory half, which the cross-process test cannot reach because `filelock`'s counter is per-object inside one process:
```
tests/test_platform_lock.py::NonReentrancyTests::test_a_second_acquire_in_the_same_process_is_refused
  same-process second acquire: refused with LockBusy (NOT re-entrant)
PASSED
tests/test_platform_lock.py::NonReentrancyTests::test_the_refusal_is_the_shape_runner_stop_dispatches_on
  refusal shape: LockBusy -> BlockingIOError -> OSError, errno=EAGAIN
PASSED
```
Whole module, both halves and everything else in it:
```
$ python3 -m pytest tests/test_platform_lock.py -o addopts="" -m "" -q
28 passed in 3.64s
```

### V-05 validates E-05: the package imports with `fcntl` unavailable

The absence is simulated in a SUBPROCESS with a `sys.meta_path` import blocker installed BEFORE `agent_workflows` is imported. That ordering is the whole point: the defect was an import-time failure, so a patch applied after import could not detect it, and a `sys.platform` monkeypatch never could. The blocker self-verifies (`import fcntl` must raise, else the probe exits 2 with `SETUP-FAILED`), so the test cannot pass vacuously.
ALL NINE MODULES IMPORT (the six that carried a top-level `import fcntl`, plus `runner_shutdown`, `run_viewer`, and `platform_lock`):
```
tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_all_affected_modules_import_without_fcntl
  with fcntl BLOCKED, all 9 modules imported: IMPORTED-ALL
  STILL-EXCLUSIVE
  PROBE=None
PASSED
```
A LOCK IS STILL ACQUIRED AND STILL EXCLUDES, not merely imported (`filelock` falls back to its `SoftFileLock` backend, and a second acquire is still refused):
```
tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_the_lock_still_excludes_without_fcntl PASSED
```
AND THE PROBE DEGRADES HONESTLY, which is a property I added beyond the item's letter because getting it wrong would be dangerous: with no POSIX primitive the probe reports `None` (undetermined), NEVER `True`. Failing to prove a holder is alive is not proof it is dead, and callers project runs as abandoned on that answer:
```
tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_the_probe_reports_undetermined_without_the_posix_primitive
  with fcntl BLOCKED, probe_free reported None (undetermined), not True
PASSED
```
FAILS AGAINST PRE-FIX CODE. Under the SAME import blocker, the pre-fix SHAPE (a module whose top-level body runs `import fcntl`) raises, which is what makes the four tests above non-vacuous:
```
tests/test_platform_lock.py::ImportsWithoutFcntlTests::test_this_test_would_have_FAILED_before_the_fix
  falsifiability: PRE-FIX-SHAPE-FAILED: simulated non-POSIX host: no fcntl
PASSED
```
I reconstructed the pre-fix shape rather than checking out the old commit because the two are equivalent for this purpose and the reconstruction is self-contained in the test (it survives as a permanent guard, whereas a one-off checkout would not). The pre-fix premise itself is independently corroborated by the test this plan REPLACED, `test_a10s_first_half_is_recorded_as_blocked_not_silently_claimed`, which passed at the lane base by asserting each module DID contain `\nimport fcntl\n`.
HONEST SCOPE NOTE: this proves the package IMPORTS and LOCKS without `fcntl`. It does NOT prove the runner works on Windows, and I make no such claim: the SIGINT/SIGTERM ladder and the `os.killpg` process-tree kill remain POSIX-only and were deliberately out of scope.

### V-06 validates E-06: the notes to `2c122z` and `71vjbn`

NOTE ADDED TO `2c122z` (first line of its `## Workflow history`), naming `y6mfgo`:
```
- 2026-08-31 SUPERSEDED IN PART by plan `y6mfgo` (locksafe-01), which is now EXECUTED: do NOT build
  the `platform_lock` portion of this plan again. `y6mfgo` created `agent_workflows/platform_lock.py`
  and routed every raw `fcntl` call site in the package through it, backed by `filelock` ... That
  covers this plan's "cross-platform lock abstraction (`platform_lock`)" scope item and the `fcntl`
  half of E-01/E-02/E-03 here, including the `msvcrt.locking` BYTE-RANGE hazard this plan's own
  /plan-review caught as PR-002 ... STILL OWNED HERE and NOT done by `y6mfgo`: the Windows Job
  Object process-tree kill ... This plan's `Status` is UNCHANGED (`approved`, stranded pending
  `6knsrx`); only the note is added.
```
NOTE ADDED TO `71vjbn` (first line of its `## Workflow history`), naming `y6mfgo`:
```
- 2026-08-31 E-07/E-08 UNBLOCKED by plan `y6mfgo` (locksafe-01), now EXECUTED. The A10 platform
  question that blocked them has a FACTUAL answer ... `oc_runipd`, `agy_runipd`, `runner_stop`,
  `agy_sessions`, `project_registry` and `run_ledger_store` NO LONGER `import fcntl` at top level
  ... WHAT THE HONEST CLAIM MUST STILL SAY ...: the SIGINT/SIGTERM ladder needs POSIX signal
  semantics and the process-tree reap (`os.killpg`/`getpgid`) has no Windows equivalent, so the
  TRIGGERS remain POSIX-only ... Importing is not supporting; do not overstate it. ... This plan's
  `Status` is UNCHANGED (`approved`, still in `pending/`): E-07/E-08 and V-07/V-08 are unblocked
  but NOT executed, so it still cannot finalize.
```
BOTH `- Status:` LINES UNCHANGED (the `:210`/`:163` hits are OQ `Status: resolved` fields inside each plan's Open questions section, not the plan status):
```
$ grep -n "^- Status:" .aw/records/plans/pending/20260828-wtiso-06-2c122z*.ipd.md \
                       .aw/records/plans/pending/20260829-runstop-06-71vjbn*.ipd.md
.../20260828-wtiso-06-2c122z-...ipd.md:9:- Status: approved
.../20260829-runstop-06-71vjbn-...ipd.md:11:- Status: approved
```
Both still sit in `pending/` (unmoved), and each note names this plan's id6 so the link is traceable in both directions:
```
$ grep -c "y6mfgo" .../2c122z...ipd.md .../71vjbn...ipd.md
.../20260828-wtiso-06-2c122z-...ipd.md:1
.../20260829-runstop-06-71vjbn-...ipd.md:1
```

### V-07 validates E-07: the one blocking caller still WAITS

CHOICE: **(a)**, an explicit opt-in blocking acquire used by this one caller and nowhere else. Recorded in E-07 above BEFORE the code was written, and in the run's decisions register as `01-y6mfgo-D3`. RATIONALE as recorded: (a) preserves the site's waiting semantics exactly (the Scope's hard constraint) while still removing the POSIX-only import, which (b) cannot do; (b) would leave `project_registry.py` as the one module still unimportable on a non-POSIX host, defeating E-03's own acceptance criterion. The cost of (a), a blocking path that could hang a driver if misused, is mitigated by three things rather than merely accepted: opt-in, non-blocking DEFAULT, and a named single permitted caller.
THE DOCUMENTED CONTRACT MATCHES (a). From `platform_lock.py`'s module docstring:
```
BLOCKING IS OPT-IN AND HAS EXACTLY ONE CALLER. Every acquisition in this package is
non-blocking except one: ``project_registry.save_registry`` acquires a bare ``LOCK_EX`` and WAITS
for the registry lock. That behavior is preserved via ``blocking=True``, and it is the ONLY
caller permitted to pass it. Adding a second blocking caller needs its own justification,
because several callers turn the already-held case into an operator-facing refusal and an
accidental block would HANG a driver rather than fail it.
```
and from `acquire`'s own docstring: "``blocking=True`` waits for the holder instead, preserving the ONE pre-existing blocking acquisition (``project_registry.save_registry``). No other caller may use it". The signature makes the default explicit: `acquire(path, *, blocking: bool = False, timeout: Optional[float] = None)`.
THE SINGLE-CALLER RULE IS ENFORCED MECHANICALLY, not just documented:
```
tests/test_platform_lock.py::SingleOwnerTests::test_no_blocking_mode_leaked_to_a_second_caller
  blocking callers: ['project_registry.py:280']
PASSED
```
IT STILL WAITS, PROVEN WITH TWO PROCESSES, and the test is built so the happy path cannot satisfy it. The waiter is started WHILE the lock is held, must still be alive after a full second (proving it did not fail fast), and must then acquire once the holder releases:
```
tests/test_platform_lock.py::BlockingRegistryCallerTests::test_a_blocking_acquire_waits_for_the_holder_and_then_succeeds
  blocking waiter is still blocked while the holder holds the lock
  blocking waiter then succeeded: acquired-after-1.007s
PASSED
```
The `acquired-after-1.007s` is the evidence: it WAITED ~1s (exactly the holder's remaining lifetime) and then SUCCEEDED, rather than raising. Had blocking regressed to the non-blocking default, the waiter would have exited during the `time.sleep(1.0)` window and the `assertIsNone(waiter.poll())` would have failed with the message "the blocking acquire FAILED FAST instead of waiting: this is the semantic change `y6mfgo`'s Scope forbids".
THE CONTRAST CASE, so the test proves blocking is a real distinction and not a no-op:
```
tests/test_platform_lock.py::BlockingRegistryCallerTests::test_the_default_is_non_blocking
  default acquire (no blocking= argument): refused, did not wait
PASSED
```
THE REAL CALLER, end to end: four concurrent `project_registry.save_registry` processes all complete (none refused, nothing torn), which is the behavior a "fail if contended" regression would break:
```
tests/test_platform_lock.py::BlockingRegistryCallerTests::test_project_registry_writes_survive_real_contention
  4 concurrent registry writers all completed; final: {'projects': {'p2': {}}, 'registry_version': 1}
PASSED
```
NARROWED OQ-02 TEXT, appended to OQ-02 rather than replacing the original wording (so the record shows the change instead of hiding it):
```
FINAL NARROWED WORDING, as executed (E-07 chose option (a)): the helper offers a blocking mode
that is OPT-IN, defaults OFF, and has exactly ONE permitted caller, `project_registry.save_registry`
... The prohibition that survives is therefore not "no blocking mode" but "no SECOND blocking caller
without its own justification", and it is MECHANICALLY ENFORCED rather than left to prose ...
The original concern (an accidental block hangs a driver) is fully preserved by the non-blocking
DEFAULT, so a caller that forgets to think about it gets the safe behavior.
```

## Suite results

BASELINE at the lane base `bf631de4`, in the primary checkout, bare invocation:

```
$ python3 -m pytest
15 failed, 3817 passed, 3 skipped, 4 xfailed in 34.57s
```

The 15 failures are all `tests/test_run_viewer.py` and are the KNOWN worktree artifact recorded as
backlog `dh0uno` (state resolves relative to the worktree). They are pre-existing and unrelated.

AFTER, in the primary checkout at HEAD `d4febb8e`:

```
$ python3 -m pytest
3860 passed, 3 skipped, 4 xfailed in 38.22s
```

The accounting is exact and worth stating, because it shows nothing was quietly dropped:
3817 + 15 (the run_viewer failures, which pass in the primary tree) = 3832 pre-existing, plus 28 new
tests in `tests/test_platform_lock.py` = 3860.

FULL suite including `slow`:

```
$ python3 -m pytest -m ""
5 failed, 4257 passed, 3 skipped, 4 xfailed in 162.84s (0:02:42)
```

Those 5 failures were verified PRE-EXISTING by running the same selection in a clean worktree at the
lane base `bf631de4`:

```
$ python3 -m pytest -m "" tests/test_command_surface_declarations.py tests/test_cli_conformance_matrix.py \
    tests/test_cli.py tests/test_runner_stop_levels12.py
FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
FAILED tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
FAILED tests/test_runner_stop_levels12.py::Level2Tests::test_level_2_leaves_another_sets_runnable_item_queued_when_this_set_is_blocked
5 failed, 92 passed in 53.51s
```

Identical set, so ZERO regressions from this change.

Every pre-existing lock-related suite passes UNCHANGED, which is the plan's own regression criterion:

```
$ python3 -m pytest tests/test_runner_shutdown.py tests/test_run_viewer_liveness.py \
    tests/test_project_registry.py tests/test_run_ledger_store.py -o addopts="" -q -m ""
84 passed in 6.96s
```

Leak sanitizer:

```
$ python3 -m agent_workflows check-local-leaks . --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,
 "verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
```

## Tests that were CHANGED, and why that is not weakening them

Three test files were modified. Two are outside the plan's declared Scope-Paths, recorded as
decision `01-y6mfgo-D5`.

1. `tests/test_runner_stop_triggers.py`. Its `test_a10s_first_half_is_recorded_as_blocked_not_silently_claimed`
   ASSERTED that each of three modules still contained a top-level `import fcntl`. That was a premise
   TRIPWIRE, not a semantic guarantee: its own failure message read "premise changed - `fcntl` is no
   longer imported unconditionally, so orchestrator OQ-02's framing ... must be revisited", i.e. it was
   authored to fire exactly when this work landed. It is INVERTED, not deleted, and is now stronger:
   it checks SEVEN modules for the absence of the import and asserts `platform_lock` owns the single
   guarded one. Its sibling `test_no_second_lock_abstraction_was_added` forbade the NAME
   `platform_lock` in `runner_stop` as a proxy for "do not build one" (valid when the module did not
   exist); it now asserts the real property, that `runner_stop` DEFINES no lock primitive and consumes
   the shared module by identity.
2. `tests/test_runner_stop.py`. Two handler-safety tests patched `runner_stop.fcntl.flock` to record
   operation flags. That attribute no longer exists, so they now record the parameters passed to
   `platform_lock.acquire`. They assert the SAME property (no acquisition on either writer path may
   wait), and arguably more directly, since they observe the requested CONTRACT rather than one
   backend's bit flags. Falsifiability was verified rather than assumed: temporarily forcing
   `blocking=True` in `_sidecar_lock` makes both fail with
   `AssertionError: True is not false : a stop writer must never take a blocking acquire; it
   deadlocks a signal handler (recorded {'blocking': True, 'timeout': None})`, and they pass again
   once reverted.
3. `tests/test_packaging.py`. `test_wheel_declares_no_runtime_dependencies` asserted the wheel
   declares ZERO unconditional `Requires-Dist`. It is narrowed to an ALLOWLIST of exactly one
   (`filelock`) and renamed accordingly. This is not a loosening in substance: the gate now PINS the
   exact dependency set, so an unreviewed addition still fails, AND a silent DROP of the required
   dependency also fails (which the old blanket-zero assertion could never catch). The framing it was
   written under is the one DECISIONS D138 explicitly corrected: D46 stated a fact about the build of
   the day, and the "rule" reading was a later back-reference, never a policy.

## Honest limitations

- This does NOT make the runner work on Windows. It removes ONE blocker (the import-time failure).
  The signal handling and the process-tree kill remain POSIX-only for a different reason: there is no
  Windows equivalent to substitute, only a Job Object redesign, which `2c122z` still owns.
- `probe_free` answers only where the POSIX primitive exists, and returns `None` (undetermined)
  elsewhere. That is the same conservative contract both probe sites already documented, but it means
  a non-POSIX host cannot yet determine driver liveness.
- `LockHandle.fileno()` reads a private `filelock` attribute (`_context.lock_file_fd`, with a
  fallback to the older `_lock_file_fd`). This is contained to one accessor and asserted by a test
  that fails LOUDLY if a future `filelock` moves it, rather than silently degrading the inode check.
  Verified against both 3.29.7 (development) and 3.32.4 (clean resolve).
- The package now has a runtime dependency where it previously had none. That is a real cost to some
  users and was a deliberate, recorded trade (OQ-01, D138), not an oversight.
