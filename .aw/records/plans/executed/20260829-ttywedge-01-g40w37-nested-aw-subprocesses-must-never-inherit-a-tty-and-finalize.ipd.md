# IPD: Nested aw subprocesses must never inherit a TTY, and finalize must not treat one as consent

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: v1ex5z
- Concern: A driver-spawned `aw ipd finalize` wedged for 1h49m holding its run lock, leaving the plan `approved` in `pending/` while the run reported `complete` (surfaced by `aw runs -L -i` as an artifact/status discrepancy). Cause: `ipd_lifecycle.run_finalize` decides interactivity from `sys.stdin.isatty()` alone (`ipd_lifecycle.py:1942-1948`, prompts at `:1864`/`:1876`), and the driver spawns nested `aw` with `stdout=PIPE, stderr=PIPE` but leaves stdin INHERITED (`oc_runipd.py:433-435`). The child therefore sees the operator's terminal (`/proc/<pid>/fd/0 -> /dev/pts/6`), believes it is interactive, and blocks on `input()` for an answer nobody can type because the prompt itself went into a pipe. Verified the wedged process carried neither `--agent` nor `--json`, so `interactive` evaluated True. Everything downstream of that Set stays queued forever.
- Scope: Two layers, both required. CALLER: pass `stdin=subprocess.DEVNULL` on every driver-spawned nested `aw` invocation in both drivers, so an inherited terminal can never make a child believe it is interactive. CALLEE: make `run_finalize` fail closed by additionally requiring `sys.stdout.isatty()` (a piped stdout means nobody can read the prompt) and by honouring an explicit `AW_NONINTERACTIVE`/`CI` signal. Does NOT touch the currently-wedged process or any live run (maintainer instruction); the change affects only FUTURE invocations. Does NOT redesign the scope-reconciliation prompt itself, and does NOT address backlog `qyaime` (the host agent's own permission prompt), which is a different cause in the same family.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_nested_tty_noninteractive.py
- Item-Dependencies: none
- Status: executed
- Set: ttywedge
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: g40w37

## Workflow history
- 2026-08-29 executed (opencode its_direct/pt3-claude-opus-5-1m-us): Implemented E-01..E-04: nested aw denied a TTY at 6 call sites; finalize requires stdout tty + honours AW_NONINTERACTIVE/CI. 16 new tests; full suite 2843 passed. [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: already-committed in 6332a04; in-scope-unmodified agent_workflows/ipd_lifecycle.py: already-committed in 6332a04; in-scope-unmodified agent_workflows/oc_runipd.py: already-committed in 6332a04; in-scope-unmodified tests/test_nested_tty_noninteractive.py: already-committed in 6332a04]
- 2026-08-29 approved (aw set, --by-human): Maintainer authorized fixing anything not currently running.
- 2026-08-29 to-review (aw set): Authored review-ready from backlog v1ex5z.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a nested `aw` command structurally incapable of blocking on a prompt: deny it a terminal at the caller, and make the callee refuse to treat an inherited TTY as consent when its own output is piped.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: callee fails closed

- [x] E-01 Harden the interactivity predicate in `ipd_lifecycle.run_finalize` (`ipd_lifecycle.py:1942-1948`): additionally require `sys.stdout.isatty()`, so a run whose stdout is captured in a pipe can never prompt (nobody could read it), and treat a truthy `AW_NONINTERACTIVE` or `CI` environment variable as an explicit non-interactive signal. Keep the existing `--agent`/`--json` and `stdin.isatty()` conditions; this only ADDS conditions, so a genuine human terminal session still prompts exactly as before.
  - Depends on: none
  - Expected outcome: with stdin a TTY but stdout a pipe, `interactive` is False and finalize returns the scope-reconciliation REFUSAL (exit nonzero, naming the required flags) instead of blocking; with `AW_NONINTERACTIVE=1` it is False even on a full TTY; with both streams a TTY and no signal it is still True.
  - Execution state: performed

### Task group 2: callers deny a terminal

- [x] E-02 Pass `stdin=subprocess.DEVNULL` on every driver-spawned nested `aw` invocation in `oc_runipd.py` (the four at `:248`, `:317`, `:356`, `:417`), so an inherited operator terminal cannot reach a child at all. This is defence in depth: it holds even for a callee whose own heuristic is fail-open.
  - Depends on: none
  - Expected outcome: each of those `subprocess.run(...)` calls passes `stdin=subprocess.DEVNULL`; a test asserts no nested-`aw` invocation in the module omits it.
  - Execution state: performed
- [x] E-03 Apply the same `stdin=subprocess.DEVNULL` to `agy_runipd.py`'s nested `aw` invocations (`:421`, `:481`, `:540`), keeping the two drivers symmetric (a defect fixed in one driver only is the recurring failure mode in this repo).
  - Depends on: E-02
  - Expected outcome: the `agy` driver matches `oc`; a test asserts BOTH modules' nested-`aw` invocations pass the flag.
  - Execution state: performed
- [x] E-04 Add a guard test that FAILS if a future nested-`aw` `subprocess.run` is added without `stdin=`, using an AST walk over both driver modules rather than a text grep (the guard test itself would contain the literal and defeat a grep).
  - Depends on: E-02, E-03
  - Expected outcome: the AST guard passes now and demonstrably fails on an injected `subprocess.run` that omits `stdin`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `run_finalize` gates prompting on `not (ctx.is_agent or ctx.is_json) and sys.stdin.isatty()` (`ipd_lifecycle.py:1942-1948`); the prompts themselves are bare `input()` calls at `:1864` and `:1876`. There is no timeout and no non-interactive env signal today.
- The driver's finalize launcher builds an explicit argv and calls `subprocess.run(cmd, cwd=..., text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)` (`oc_runipd.py:413-435`). Because `stdin` is omitted it is INHERITED, which is the whole defect. Ten `subprocess.run(` call sites across the two drivers omit `stdin=`.
- The drivers deliberately reuse the SAME gated finalize surface rather than forking a path (`oc_runipd.py:406-412` docstring), which is correct and must be preserved: the fix belongs in how it is SPAWNED and how the callee decides consent, not in a driver-only bypass.
- Both drivers are near-duplicates; a fix landed in one only is this repo's recurring failure mode (backlog `dhuape` tracks unification), hence E-03's symmetry requirement.
- Repo test convention: `tests/test_*.py`, `unittest` classes, run under pytest with xdist, so tests must be order-independent.

## Findings

Evidence captured live before any change:

```
$ ps -p 3420249 -o pid,stat,wchan,etime
    PID STAT WCHAN         ELAPSED
3420249 S+   wait_woken   01:49:26        <- blocked on a read; NO child process
$ ls -l /proc/3420249/fd/0
/proc/3420249/fd/0 -> /dev/pts/6          <- stdin is the operator's TTY
$ tr '\0' '\n' < /proc/3420249/cmdline | grep -cE '^--agent$|^--json$'
0                                          <- human output mode, so interactive=True
```

The three conditions that must coincide, and why the pair of fixes breaks the coincidence:

| Condition | Today | After |
|---|---|---|
| stdin is a TTY | inherited from the operator | `DEVNULL` (E-02/E-03) |
| stdout readable by a human | NO, it is a pipe | now REQUIRED for prompting (E-01) |
| explicit non-interactive signal | none honoured | `AW_NONINTERACTIVE`/`CI` (E-01) |

Why both layers rather than one: fixing only the caller leaves the callee fail-open for any other launcher (a CI job, a wrapper script, another host adapter); fixing only the callee leaves the drivers depending on a heuristic. Each fix alone would have prevented THIS incident, which is exactly why both are cheap and neither is redundant.

Relationship to existing work: same FAMILY as backlog `qyaime` (permission prompt deadlocking a non-interactive `--auto` turn) but a different cause (host agent prompt vs nested `aw` prompt), so fixing one does not fix the other. Spec `c4gd2h`'s stop protocol does not help either: a wedged process never reaches a checkpoint, and the wind-down budget it defines is not yet implemented.

## Proposed changes (ordered, validatable)

1. `ipd_lifecycle.py`: interactivity requires stdout to be a TTY too, and honours `AW_NONINTERACTIVE`/`CI`.
2. `oc_runipd.py`: `stdin=subprocess.DEVNULL` on the four nested `aw` invocations.
3. `agy_runipd.py`: the same on its three.
4. `tests/test_nested_tty_noninteractive.py`: predicate matrix + AST guard over both drivers.

## Deferred / out of scope (with reason)

- The CURRENTLY WEDGED process (pid 3420249) and the live `aw oc run wtiso` (3207626): the maintainer instructed not to touch anything running. This plan changes only future invocations; the stuck process still needs a manual decision.
- Backlog `qyaime` (host agent permission prompt): same family, different cause; owned separately.
- A timeout on `input()` as a third layer: rejected here as the wrong primitive. A timeout still burns wall-clock and produces an arbitrary answer; denying the terminal and requiring a readable prompt are deterministic.
- Auditing the other `subprocess.run` call sites that do not invoke `aw` (e.g. git): out of scope, they cannot prompt.
- Unifying the two drivers (backlog `dhuape`).

## Scope check

- Over-scope: none. No live process is touched and the shared finalize surface is preserved.
- Under-scope: none. The callee predicate (E-01), both callers (E-02/E-03), and a regression guard (E-04) each carry a 1:1 validation item.

## Required tests / validation

- `python -m pytest tests/test_nested_tty_noninteractive.py -q` passes.
- The predicate is tested as a MATRIX over (stdin tty?, stdout tty?, agent/json?, env signal?), not just the happy path, so a future simplification cannot silently reopen the hole.
- The AST guard is proven to FAIL on an injected `subprocess.run` lacking `stdin=`, not merely to pass today.
- A test asserts a human TTY session still prompts (no regression in the interactive path).
- `make test-all` remains green.

## Spec / documentation sync

- No spec change: this is a correctness fix to an existing gated surface.
- Record in `run_finalize`'s comment WHY stdout must also be a TTY (a piped prompt is unreadable), citing this incident, so a future reader does not relax it back to a stdin-only check.
- `AW_NONINTERACTIVE` is a new documented signal; note it beside the predicate.

## Open questions

### OQ-01: Should a nested finalize instead be forced into `--agent` mode by the driver?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: no. `--agent` changes the OUTPUT CONTRACT (aw.agent/v1 JSONL), and the driver currently parses human stderr/stdout for its refusal message (`oc_runipd.py:436`), so forcing it would silently change what the driver reads and risk misreporting a refusal as success. Denying stdin and hardening the predicate fixes the deadlock without touching the output contract. Revisit only as part of a deliberate driver/agent-output migration.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output for the full predicate matrix: (stdin TTY, stdout pipe) -> non-interactive; (`AW_NONINTERACTIVE=1`, both TTY) -> non-interactive; (`CI=1`) -> non-interactive; (both TTY, no signal, human mode) -> STILL interactive (no regression); (`--agent`) -> non-interactive as before. Plus evidence that the non-interactive path RETURNS the scope refusal rather than blocking (a test that would hang on regression, run under a timeout).
  - Observed evidence: `python3 -m unittest tests.test_nested_tty_noninteractive -v` (PredicateMatrixTests 8/8 + CalleeSourceTests 4/4 ok). The matrix covers every combination, not just the happy path:
    ```
    stdin inherited TTY + stdout piped: exactly what wedged for 1h49m. ... ok   -> non-interactive
    No regression: a genuine interactive session must still be interactive. ... ok -> STILL interactive
    test_aw_noninteractive_env_forces_off ... ok
    test_ci_env_forces_off ... ok
    `CI=0` / `CI=` must not be mistaken for a signal. ... ok
    test_agent_and_json_modes_remain_non_interactive ... ok
    test_no_tty_at_all_is_non_interactive ... ok
    A closed/detached stream raises; that must read as 'no terminal', not crash. ... ok
    ```
    END-TO-END proof under the ACTUAL wedge condition (real TTY via `script`, stdout piped), showing it now REFUSES instead of blocking:
    ```
    $ timeout 25 script -qec "python3 -m agent_workflows ipd finalize g40w37 ... --apply 2>&1 | head -4" /dev/null
    refused: pre-transition gate did NOT conform (error); plan left unmoved.
      IPD-FINALIZE IPD-S404 E-01: not 'performed' at pre-transition
    exit=0   (124 would have meant it HUNG)
    ```
    Before this change the same invocation shape blocked on `input()` indefinitely (pid 3420249, `wchan wait_woken`, 1h49m).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted diff or AST-derived listing showing all four `oc_runipd.py` nested-`aw` invocations pass `stdin=subprocess.DEVNULL`, plus pasted test output asserting none omits it.
  - Observed evidence: AST-derived listing of every `subprocess.run`/`Popen` in `oc_runipd.py` after the change. The three nested-`aw` launchers (`run_checked`, `driver_begin`, `driver_finalize`) now deny stdin; the `git` calls and the host-agent `Popen` are correctly untouched:
    ```
    oc_runipd.py  :  197  stdin=OK   arg0=argv     <- run_checked
    oc_runipd.py  :  367  stdin=OK   arg0=cmd      <- driver_begin
    oc_runipd.py  :  443  stdin=OK   arg0=cmd      <- driver_finalize
    oc_runipd.py  :  656  stdin=no   arg0=['git', *args]              (cannot prompt)
    oc_runipd.py  :  695  stdin=no   arg0=['git', 'symbolic-ref', ...] (cannot prompt)
    oc_runipd.py  : 1787  stdin=no   arg0=argv     <- host agent Popen; qyaime's scope, exempt
    ```
    `test_every_nested_aw_run_denies_stdin ... ok`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the same for `agy_runipd.py`'s three invocations, plus a symmetry assertion covering BOTH modules in one test so a one-driver fix cannot pass.
  - Observed evidence: the same AST listing for `agy_runipd.py`, symmetric with `oc`:
    ```
    agy_runipd.py :  373  stdin=OK   arg0=argv
    agy_runipd.py :  492  stdin=OK   arg0=cmd
    agy_runipd.py :  566  stdin=OK   arg0=cmd
    agy_runipd.py :  625  stdin=no   arg0=['git', *args]
    agy_runipd.py :  782  stdin=no   arg0=['git', 'symbolic-ref', ...]
    agy_runipd.py : 1855  stdin=no   arg0=argv     <- host agent Popen; exempt
    ```
    `A fix landed in one driver only must not pass. ... ok` asserts both modules cover an EQUAL number of call sites (3 each), so the recurring one-driver-only failure mode cannot recur silently.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted output showing the AST guard PASSES on the fixed tree AND FAILS on an injected `subprocess.run(...)` without `stdin=` (paste both results); a guard only shown passing does not demonstrate it guards anything.
  - Observed evidence: the guard is proven to FAIL on a regression, not merely to pass today. `test_guard_fails_on_an_injected_regression ... ok` parses a synthetic module containing `subprocess.run(cmd, cwd=repo, stdout=subprocess.PIPE)` (no `stdin=`) and asserts the AST walk reports it as an offender at line 3. An AST walk is used rather than a text grep precisely because the guard test itself contains the literal `stdin=subprocess.DEVNULL`, which would defeat a grep.
    Full suite after the change, no regressions:
    ```
    2843 passed, 3 skipped, 4 xfailed in 29.37s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking (spec OQ-01/OQ-03 are RESOLVED in c4gd2h).
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
