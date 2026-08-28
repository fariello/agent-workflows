# IPD: Graduate tools/agy_run.py to packaged aw agy exec (non-colliding surface) + migrate tools/test_agy_run.py

- Date: 2026-08-28
- Kind: child
- Concern: runnernorm child puot79 completed E-01/E-02/E-03 (graduated agy_sessions/view/pwatch), but deliberately DEFERRED E-04 (disposition of tools/agy_run.py) to a follow-up, so puot79 cannot finalize (aw ipd lint fails closed: IPD-S404 on E-04/V-04) and the runnernorm orchestrator (ryvoi5) is blocked behind it. puot79 OQ-02 is RESOLVED as (B): tools/agy_run.py (886 lines, prog="agy_run.py", a SINGLE-TARGET MULTI-MODE runner: --ipd/--spec/--file/--prompt, two-turn skeptical protocol, session-continuity flags) is GENUINELY DISTINCT from the already-packaged agy_runipd (a restartable MULTI-IPD QUEUE driver). Neither imports/supersedes the other. So agy_run.py must graduate under a NON-colliding surface (aw agy exec) - never aw agy run, which stays aliased to aw agy runipd. This plan performs that graduation and its test migration; completing it unblocks puot79 -> ryvoi5.
- Scope: Following the awocrunner packaged-core + host-subcommand + compat-shim pattern (as puot79 did for the three unambiguous tools): (1) move tools/agy_run.py logic into a packaged core agent_workflows/agy_run.py; (2) expose it as `aw agy exec` via cli.py (extend the existing `aw agy` group at cli.py:2212, dispatch alongside runipd at cli.py:7102) - MUST NOT use `aw agy run` (keeps aliasing runipd); (3) reduce tools/agy_run.py to a thin compat shim forwarding to the packaged entry; (4) migrate tools/test_agy_run.py to exercise the packaged surface, keeping behavior coverage; (5) add an invocation test (`aw agy exec` runs the packaged core), a shim-forwarding test, and a no-collision test asserting `aw agy run`/`runagy`/`runipd` still route to agy_runipd (not agy_run). Do NOT change agy_runipd or the runipd aliases.
- Scope-Paths: agent_workflows/agy_run.py, agent_workflows/cli.py, tools/agy_run.py, tools/test_agy_run.py, tests/
- Item-Dependencies: none
- Status: to-review
- From-Backlog: czrlef
- Set: puot79e04
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ynix69

## Workflow history
- 2026-08-28 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Graduate `tools/agy_run.py` into a packaged core exposed as `aw agy exec` (non-colliding), reduce the tool to a compat shim, and migrate its tests, so runnernorm child puot79's deferred E-04/V-04 are satisfied and puot79 -> ryvoi5 can finalize.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: package + expose the runner

- [ ] E-01 Create packaged core `agent_workflows/agy_run.py` by moving the logic from `tools/agy_run.py` (886 lines, `prog="agy_run.py"`), preserving its CLI surface (`--ipd/--spec/--file/--prompt`, two-turn skeptical protocol, session-continuity flags) and a `main()` entry.
  - Depends on: none
  - Expected outcome: `agent_workflows/agy_run.py` importable with a working `main()`/`build_parser`; behavior parity with the pre-move tool.
  - Execution state: pending

- [ ] E-02 Expose it as `aw agy exec` in `cli.py` (extend the existing `aw agy` group at cli.py:2212; dispatch alongside runipd at cli.py:7102). Do NOT register `aw agy run` (that alias stays mapped to `agy_runipd`).
  - Depends on: E-01
  - Expected outcome: `aw agy exec --help` shows the runner usage; `aw agy run`/`runagy`/`runipd` still route to `agy_runipd`.
  - Execution state: pending

### Task group 2: shim + test migration

- [ ] E-03 Reduce `tools/agy_run.py` to a thin compat shim that re-exports and forwards to `agent_workflows.agy_run` (as `tools/ipdrunner/runipd.py` was reduced), preserving `python3 tools/agy_run.py ...` behavior.
  - Depends on: E-01
  - Expected outcome: `tools/agy_run.py` is a shim; invoking it forwards to the packaged core with identical behavior.
  - Execution state: pending

- [ ] E-04 Migrate `tools/test_agy_run.py` (~37KB) to exercise the packaged surface, and add: an invocation test (`aw agy exec` runs the packaged core), a shim-forwarding test, and a no-collision test (`aw agy run`/`runagy`/`runipd` -> `agy_runipd`, never `agy_run`).
  - Depends on: E-02, E-03
  - Expected outcome: migrated + new tests pass; no-collision invariant proven.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- awocrunner pattern: packaged core in `agent_workflows/`, host-subcommand group in cli.py (`aw agy` at cli.py:2212, dispatch cli.py:7100-7102), thin `tools/` compat shim (`tools/ipdrunner/runipd.py`, `tools/ipdrunner/runagy.py`).
- `aw agy run`/`runagy` are aliases of `aw agy runipd` (cli.py:2219-2221 -> agy_runipd.main, cli.py:7102). `aw agy run` is TAKEN; the new surface must be `aw agy exec`.
- puot79 already proved the pattern for agy_sessions/agy_view/pwatch and left the no-`aw agy run`-collision invariant tested (`tests/test_agy_tools_graduation.py::NoAgyRunCollisionTests`, `AgyRunUntouchedTests`).

## Findings

- OQ-02 (puot79) resolved (B): `agy_run.py` is genuinely distinct from `agy_runipd` (single-target multi-mode runner vs. multi-IPD queue driver); neither imports/supersedes the other. Graduation is therefore additive under a new surface, not a retire/shim-to-runipd.
- `AgyRunUntouchedTests` (puot79) currently asserts `tools/agy_run.py` still carries `prog="agy_run.py"` and that NO packaged `agent_workflows/agy_run.py` exists. This plan INVERTS that: it must update/replace that test so the new packaged module and shim are the asserted state (else that test will fail after graduation).

## Proposed changes (ordered, validatable)

1. `agent_workflows/agy_run.py`: new packaged core (moved from the tool).
2. `cli.py`: `aw agy exec` subcommand + dispatch; no `aw agy run` change.
3. `tools/agy_run.py`: reduced to compat shim.
4. `tools/test_agy_run.py` + `tests/`: migrated + invocation/shim/no-collision tests; update the puot79 `AgyRunUntouchedTests` expectation to the post-graduation state.

## Deferred / out of scope (with reason)

- Any change to `agy_runipd` or the `run`/`runagy`/`runipd` aliases: out of scope (must stay stable; only proven not to collide).

## Scope check

- Over-scope: none.
- Under-scope: none (core + surface + shim + test migration is the complete E-04 disposition).

## Required tests / validation

- `aw agy exec --help` shows the runner usage; the packaged core runs.
- `aw agy run`/`runagy`/`runipd` still route to `agy_runipd` (no-collision test).
- `tools/agy_run.py` shim forwards to the packaged core; behavior preserved.
- Migrated `tools/test_agy_run.py` passes; the puot79 `AgyRunUntouchedTests` is updated to the post-graduation expectation and passes.
- Full suite green.

Validation command: `python3 -m pytest tools/test_agy_run.py tests/test_agy_tools_graduation.py -q` plus a full-suite run `python3 -m pytest -p no:randomly -q` (paste ACTUAL runner output; do not claim success unrun).

## Spec / documentation sync

- Update docs/READMEs listing `aw agy` subcommands to include `aw agy exec`; note the `tools/agy_run.py` compat shim and that `aw agy run` remains the runipd alias.

## Open questions

### OQ-01: Retire the shim eventually, or keep it indefinitely?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Keep the thin compat shim (matches the awocrunner precedent for the other graduated tools); a future deprecation is a separate concern, not required for E-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output showing `python3 -c "import agent_workflows.agy_run as m; m.build_parser()"` (or equivalent) succeeds and the packaged core exposes the runner's CLI surface; behavior-parity assertion against the pre-move tool.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `aw agy exec --help` output (packaged runner usage) AND a test asserting `cli.main(["agy","run"|"runagy"|"runipd", ...])` routes to `agy_runipd.main` (never `agy_run`) - the no-collision invariant.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted test output where the `tools/agy_run.py` shim re-exports/forwards to `agent_workflows.agy_run` and `python3 tools/agy_run.py --help` still works.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `python3 -m pytest tools/test_agy_run.py tests/test_agy_tools_graduation.py -q` output (migrated + new invocation/shim/no-collision tests pass; the updated `AgyRunUntouchedTests`/post-graduation expectation passes) AND a full-suite `python3 -m pytest -p no:randomly -q` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (graduate agy_run.py under aw agy exec + migrate its tests); E-items are ordered sub-steps of that single deliverable.

Execution contract:

1. Open questions: OQ-01 resolved; execution requires explicit human approval.
2. Scope fence: touch ONLY `agent_workflows/agy_run.py`, `agent_workflows/cli.py`, `tools/agy_run.py`, `tools/test_agy_run.py`, `tests/`. Do NOT change `agy_runipd` or the `run`/`runagy`/`runipd` aliases (only prove no collision). If more seems needed, STOP and report.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output (`python3 -m pytest tools/test_agy_run.py tests/test_agy_tools_graduation.py -q` and the full-suite run); never claim success you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.

Follow-up (out of this plan's scope, but the reason it exists): once this is executed, puot79's E-04/V-04 can be marked performed (citing this plan), puot79 finalizes -> `executed/`, then the runnernorm orchestrator ryvoi5 finalizes.
