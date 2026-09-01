# Walkthrough: `runstop` whole-Set verification (spec `c4gd2h` graceful quit)

- Date: 2026-09-01
- Kind: whole-Set verification record
- Target-Id: zpbx7o
- Spec: `c4gd2h` (runner lifecycle graceful quit)
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verified at: HEAD `33dc8264`

This is the record `zpbx7o` E-01 requires, written here because `.aw/records/walkthroughs/` is the
path its `Scope-Paths` declares for exactly this output. No product code was authored for it.

## Summary

All six children (`2ouj70`, `gq6m2u`, `1qxuke`, `foi1b3`, `m0z0ti`, `71vjbn`) are in
`.aw/records/plans/executed/`. Spec acceptance criteria A1-A10 hold, with A8 verified directly here
(no child claims it) and A10 recorded with an explicit platform limitation rather than a false pass.
CID-1 through CID-5 pass, with CID-1 and CID-5 checked by AST over `agent_workflows/` rather than by
text grep, as the plan demands.

ONE DEFECT WAS FOUND AND FIXED during this verification, which is the reason the Set did not finalize
on the first attempt: `make test-all` failed a level-2 wind-down test. It turned out to be a FIXTURE
fault, not a product defect, and it is recorded in full below because a "green after I touched it"
claim is worthless without the reasoning.

## The defect this verification caught (backlog `mzy2so`, fixed by `33dc8264`)

`tests/test_runner_stop_levels12.py::Level2Tests::
test_level_2_leaves_another_sets_runnable_item_queued_when_this_set_is_blocked` failed under
`make test-all`.

WHY IT WAS INVISIBLE. The test is `slow`-marked and `pyproject.toml` `addopts` carries
`-m 'not slow'`, so a bare `python3 -m pytest` reported `3996 passed` GREEN at the same commit. Only
`make test-all` (`-m ''`) surfaces it. This is a standing trap: routine "suite green" evidence in this
repo does NOT cover the `slow` tests that this Set depends on, which is precisely why V-01 demands
`make test-all` output.

IT WAS PRE-EXISTING, not caused by the 2026-09-01 session. Reproduced in a throwaway clone at
`5e5da9a0` (before `cdef9c90`, `9c643cf8`, `b2b2bf6c`, `362b3dd1`, `18142312`, `739450ee`,
`ab9127df`, `9c38db5b`): the same test fails there, among 20 failures at that commit against 5 at the
start of this verification.

ROOT CAUSE: two independent FIXTURE faults, each silently producing a dependency-FREE queue item, so
the driver correctly considered the item runnable and the product's gating was right all along.

1. `_PLAN_TEMPLATE` placed the metadata bullets BEFORE the `#` H1 title. The IPD spec defines the
   metadata block as "a bullet `- Field: value` list after the H1 title", and the shared structural
   reader (`ipd_lint.parse`, used by `oc_runipd._read_item_dependencies`) only sees the block in that
   position. Measured directly:

       template shape (fields before heading) -> ([], None)
       canonical order (heading first)        -> (['executed:zzzz99'], None)

2. The test injected a LEGACY `- Dependencies:` field, and its own inline comment asserted that the
   driver reads it via `oc_runipd._DEPS_RE`, "NOT the plan-schema `- Item-Dependencies:` field". Both
   halves are now false: `8guhs0` (lanetruth-03) deliberately DELETED `_DEPS_RE`, leaving the standing
   note at `oc_runipd.py:161-168` ("there is deliberately NO dependency regex here"), making
   `- Item-Dependencies:` the one canonical field. Confirmed: `hasattr(oc_runipd,'_DEPS_RE')` is
   `False` and `hasattr(oc_runipd,'_read_deps')` is `False`.

THE EDGE CHOICE IS LOAD-BEARING, and three shapes do not work. Recorded so they are not rediscovered:

- a NONEXISTENT id6 (`executed:zzzz99`) is `check.ipd-dependency-dangling`, and the dependency
  PREFLIGHT refuses the whole run before any session starts, so nothing runs and the level-2 behavior
  under test is never exercised. Observed: `runipd: dependency preflight failed: run refused before
  any session started`;
- an edge on the OTHER set's item (`executed:cb0001`) makes `ca0002` depth-1, so `cb0001` becomes a
  PREREQUISITE instead of the runnable competitor the case requires;
- a backlog edge naming an absent id6 is dangling for the same reason as the first.

The fixture now creates a REAL `open` backlog item (`bl0001`) and blocks `ca0002` on
`state:backlog:done:bl0001`: the edge RESOLVES, so preflight passes, yet stays UNSATISFIED during the
run, and because it is not an in-queue IPD it leaves `cb0001` at depth 0 as the genuine set-B
competitor the docstring describes.

WHY I DID NOT STOP AT FIRST GREEN, which is the part worth inheriting. My first fix used
`executed:cb0001` and the test PASSED. Sabotage-checking showed it passed VACUOUSLY: forcing the
dependency gate to always succeed (`if True:` in place of `if satisfied:`) still left it GREEN,
because `ca0002` stayed queued due to the STOP rather than due to the gate. A passing test that
cannot fail is worse than a failing one. The corrected fixture is sabotage-verified TWICE:

    SABOTAGE A: dependency gate always passes  -> 1 failed   (correctly detects)
    SABOTAGE B: level-2 boundary never declines -> 1 failed   (correctly detects)
    RESTORED (product untouched, 0 diffs)       -> 20 passed

## Spec acceptance criteria A1-A10

A1-A7 and A9 are exercised by the Set's shipped `slow`-inclusive suites, which I RE-RAN at this HEAD
rather than quoting the children:

    tests/test_runner_stop.py                54 passed
    tests/test_runner_stop_levels12.py       20 passed
    tests/test_runner_stop_level3.py         49 passed
    tests/test_runner_stop_level4.py         41 passed
    tests/test_runner_stop_triggers.py       52 passed
    tests/test_runner_shutdown.py            27 passed
    tests/test_run_viewer_liveness.py        17 passed
    ---------------------------------------------------
    260 tests, 0 failures

- A1/A3 (single SIGINT, SIGTERM: turn completes or stops at a safe checkpoint; R1-R4 hold): covered by
  `test_runner_stop.py` + `test_runner_shutdown.py`. The R1-R4 invariant block is observable in live
  driver output, e.g. captured during this verification: `clean shutdown: all invariants satisfied` /
  `children_reaped (R1): ok` / `lock_released (R2): ok - lock file removed; lock free=True` /
  `ledger_coherent (R3): ok - 3 item(s), all in a defined state` / `tree_observed (R4): ok - 4 dirty
  path(s) left exactly as found (nothing stashed, reset, or moved)`.
- A2 (triple SIGINT -> level 4, `unknown_outcome`, escalation 1 -> 3 -> 4 recorded): `test_runner_stop_level4.py`.
- A4/A5 (`stop --after-set`; bogus run-id exits nonzero and mutates nothing): `test_runner_stop_triggers.py`,
  and the level-2 boundary case in `test_runner_stop_levels12.py` fixed above. Live level-2 output
  observed: `stop requested: level 2 (after-set); boundary = next set, finishing set sca` and
  `deliberate stop (level 2, after-set): 1 item(s) left queued, not started: cb0001`.
- A6 (a force-stopped `unknown_outcome` item is not blindly resumed): `test_runner_stop_level4.py` plus
  CID-4 below.
- A7 (wind-down exceeding its budget escalates and still satisfies R1-R4): `test_runner_stop_triggers.py`
  (`BudgetBreachWatch` / `EscalationWatch`).
- A9: see CID-1.

### A8, verified HERE because no child owns it

The plan states plainly that A8 is claimed by no child and must be verified directly or recorded
UNVERIFIED. It is VERIFIED, and the honest finding is narrower than A8's wording implies.

    python3 -m pytest tests/test_runner_shutdown.py -m '' -k pins_hard_abort  ->  1 passed

The owning test is
`test_pins_hard_abort_leaves_the_lock_file_while_the_lock_itself_is_free`, and its docstring records
the correction that matters: a hard-killed (SIGKILL) driver DOES leave `driver.lock` on disk holding a
DEAD pid, which is the real observable residue, but that file does NOT block a later run, because the
kernel drops an `flock` when its holder dies (`runner_shutdown.py:27`). The test asserts BOTH halves
deliberately and explicitly refuses to pin "a stale lock blocks the next run", which is a defect that
does not exist. Detection is by ACQUIRABILITY, which `run_viewer.driver_holder_state` treats as the
authoritative liveness signal, and that reconciliation side passes `17 passed`
(`tests/test_run_viewer_liveness.py`).

So A8's substance holds - a SIGKILL bypass is DETECTED and REPORTED by the next run's reconciliation,
demonstrating the shared routine covers crash as well as stop - while the specific phrase "stale lock"
should be read as "stale lock FILE with a dead pid", not "a lock that blocks".

### A10, recorded with its limitation rather than passed

OQ-02 requires naming which rows were verified on Windows. NONE WERE. I have no Windows host in this
session, and no row of A10 was executed on Windows. What IS verifiable, and what the code itself
claims (`runner_stop.py:28-34`), is deliberately narrow:

- the module and both drivers now IMPORT on a non-POSIX host, which removes an import-time barrier and
  nothing more;
- the SIGINT/SIGTERM ladder still requires POSIX signal semantics, and the process-tree kill
  (`os.killpg`/`getpgid`) still has no Windows equivalent. `runner_shutdown.py:181` degrades via
  `getattr(signal, "SIGKILL", signal.SIGTERM)`;
- A10's second half (unsupported triggers must fail LOUDLY, not silently no-op) IS implemented:
  `install_stop_signal_handlers` returns a per-trigger status and `render_trigger_support` renders
  whatever could not be installed.

The in-module comment states the standard this record honors: "the signal triggers require a POSIX
host, and NO text here may promise a working Windows subset."

## Cross-IPD drift checks CID-1 to CID-5

### CID-1 (exactly ONE cleanup routine; spec R5, A9) - PASS, by AST over `agent_workflows/`

Checked by AST, not text grep, and repo-wide rather than per-file, exactly as CID-3 warns is necessary
(a per-file check would pass while two byte-identical copies exist):

    terminate_process:  agy_runipd.py:2580 DELEGATES
                        oc_runipd.py:3994  DELEGATES
                        runner_shutdown.py:126 IMPLEMENTS
    clean_shutdown:     runner_shutdown.py:434 IMPLEMENTS
    _signal:            runner_shutdown.py:153 IMPLEMENTS

The classifier distinguishes a real body from a pure delegation (a single expression statement). Both
driver copies are now thin wrappers that call `runner_shutdown.terminate_process(...)`, so the
byte-identical duplication CID-3 measured has been REMOVED and exactly one implementation remains.
Corroborating: the escalation primitive appears once - `os.killpg` at `runner_shutdown.py:158` is the
only call site in the package (the two other matches are comments), and the SIGKILL escalation only at
`runner_shutdown.py:181`.

### CID-2 (no second stop-flag path, no raw `<repo>/.aw/state` construction) - PASS

No `.aw/state` path construction outside the shared accessors; the remaining matches in
`agent_workflows/*.py` are docstrings and comments (`actions.py:4-5`, `agy_runipd.py:569`, `:1092`,
`artifact_core.py:188` which is a declared constant list).

### CID-3 (both drivers expose the same four levels and the same `stop` verb) - PASS

Both drivers delegate to the one shared implementation (CID-1 table above), so no level can exist in
one driver only. The duplication CID-3 was written to catch is gone.

### CID-4 (the `unknown_outcome` resume refusal is wired INTO the real requeue path) - PASS

Exercised through the real entry point by `tests/test_runner_stop_level4.py` (41 passed), not by
calling the refusal helper directly.

### CID-5 (no second lock abstraction, no second process-tree reaper) - PASS, by AST

    exclusive_file_lock:  (absent on main)
    _kill_process_tree:   (absent on main)
    RunLockHandle:        runner_shutdown.py:193

Exactly one lock handle, and the two `wtiso` Phase 5 (`2c122z`) symbols are correctly ABSENT from main
rather than forked into this Set, which is the deferral P8 requires.

## `make test-all` (required by V-01, because a bare run deselects `slow`)

    4 failed, 4394 passed, 3 skipped, 4 xfailed in 155.51s (0:02:35)

Before the `mzy2so` fix this was `5 failed`. The improvement is exactly the level-2 test.

THE 4 REMAINING FAILURES ARE PRE-EXISTING AND OUT OF THIS SET'S SCOPE, stated rather than waved
through:

    tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves
    tests/test_cli.py::test_every_subparser_has_fuller_description
    tests/test_cli_conformance_matrix.py::test_no_undeclared_parser_leaves
    tests/test_cli_conformance_matrix.py::test_every_declared_leaf_gets_a_full_scenario_row_set

All four are CLI-surface DECLARATION checks, not runner behavior. The first reports
`AssertionError: 65 != 0 : Found undeclared parser leaves`. All four were reproduced at `5e5da9a0`,
before this session's commits. Attribution, and its limit: `command_surface.py` and `cli.py` are in
approved plan `0soncw`'s `Scope-Paths`, and `0soncw` is chartered for exactly this surface, so it is
the plausible owner. I did NOT confirm that `0soncw` intends to close these specific assertions, so
treat the ownership as probable, not established.

## Per-child evidence quality

Every child is `executed` with real observed evidence, not prose:

| child | V-items | all pass | empty evidence lines |
| --- | --- | --- | --- |
| `2ouj70` | yes | yes | 0 |
| `gq6m2u` | yes | yes | 0 |
| `1qxuke` | yes | yes | 0 |
| `foi1b3` | yes | yes | 0 |
| `m0z0ti` | yes | yes | 0 |
| `71vjbn` | yes | yes | 0 |

## Honest limits of this record

1. A1-A8 are verified through the Set's own automated suites plus live driver output observed during
   this session, NOT by a human sitting at a terminal sending signals to a long-running production
   run. The suites drive real subprocesses and real signals, which is why I treat them as satisfying
   the criteria, but that substitution is stated rather than hidden.
2. A10 is explicitly NOT verified on Windows. No row was.
3. The 4 residual `make test-all` failures are out of scope here and remain open; their attribution to
   `0soncw` is probable, not confirmed.
4. This record does not assert anything about `dh0uno` or the unmerged `wtiso` lanes, which are
   separate work.
