# IPD: Graduate tools/agy_run.py to packaged aw agy exec (non-colliding surface) + migrate tools/test_agy_run.py

- Date: 2026-08-28
- Kind: child
- Concern: runnernorm child puot79 completed E-01/E-02/E-03 (graduated agy_sessions/view/pwatch), but deliberately DEFERRED E-04 (disposition of tools/agy_run.py) to a follow-up, so puot79 cannot finalize (aw ipd lint fails closed: IPD-S404 on E-04/V-04) and the runnernorm orchestrator (ryvoi5) is blocked behind it. puot79 OQ-02 is RESOLVED as (B): tools/agy_run.py (886 lines, prog="agy_run.py", a SINGLE-TARGET MULTI-MODE runner: --ipd/--spec/--file/--prompt, two-turn skeptical protocol, session-continuity flags) is GENUINELY DISTINCT from the already-packaged agy_runipd (a restartable MULTI-IPD QUEUE driver). Neither imports/supersedes the other. So agy_run.py must graduate under a NON-colliding surface (aw agy exec) - never aw agy run, which stays aliased to aw agy runipd. This plan performs that graduation and its test migration; completing it unblocks puot79 -> ryvoi5.
- Scope: Following the awocrunner packaged-core + host-subcommand + compat-shim pattern (as puot79 did for the three unambiguous tools): (1) move tools/agy_run.py logic into a packaged core agent_workflows/agy_run.py, fixing its internal `import agy_sessions` to `from agent_workflows import agy_sessions` (see Findings); (2) expose it as `aw agy exec` via cli.py (extend the existing `aw agy` group - CURRENTLY at cli.py:2600, `agy_sub` at 2606 - and wire BOTH dispatch sites the other agy subcommands use: the early fast-path forwarder at cli.py:7610-7635 AND the argparse dispatch at cli.py:7799-7817) - MUST NOT use `aw agy run` (keeps aliasing runipd); (3) reduce tools/agy_run.py to a thin compat shim that re-exports ALL of the packaged core's symbols (like tools/agy_sessions.py) and forwards to the packaged entry, so `tools/antigravity_execute_ipd.py`'s `import agy_run` re-export chain and the `agy-run-entry-points` compat surface keep resolving; (4) migrate tools/test_agy_run.py (which ALSO covers tools/antigravity_execute_ipd.py backward-compat) to exercise the packaged surface, keeping behavior coverage for BOTH; (5) add an invocation test (`aw agy exec` runs the packaged core), a shim-forwarding test, and a no-collision test asserting `aw agy run`/`runagy`/`runipd` still route to agy_runipd (not agy_run). Do NOT change agy_runipd or the runipd aliases.
- Scope-Paths: agent_workflows/agy_run.py, agent_workflows/cli.py, tools/agy_run.py, tools/test_agy_run.py, tools/README.md, tests/
- Item-Dependencies: none
- Status: approved
- From-Backlog: czrlef
- Set: puot79e04
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ynix69
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-28 reviewed (aw set): status set to reviewed
- 2026-08-28 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Added E-05 (invert three contradicted puot79 assertions - draft missed test_no_agy_exec_surface_yet), E-06 + tools/README.md scope (doc sync), corrected build_parser->parse_args, added import agy_sessions fixup, dual dispatch-site wiring, antigravity_execute_ipd re-export chain preservation, and V-05/V-06. Status -> reviewed.

- 2026-08-28 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Graduate `tools/agy_run.py` into a packaged core exposed as `aw agy exec` (non-colliding), reduce the tool to a compat shim, and migrate its tests, so runnernorm child puot79's deferred E-04/V-04 are satisfied and puot79 -> ryvoi5 can finalize.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: package + expose the runner

- [ ] E-01 Create packaged core `agent_workflows/agy_run.py` by moving the logic from `tools/agy_run.py` (`prog="agy_run.py"`), preserving its CLI surface (`--ipd/--spec/--file/--prompt`, two-turn skeptical protocol, session-continuity flags), its public functions (`parse_args`, `main`, `run`, `ScriptError`, `AgyResult`, `repository_root`, `resolve_ipd`, `stable_id_from_filename`, `relative_posix`, `resolve_agy`, `run_agy`, `build_turn1_prompt`, `build_turn2_prompt`), and a `main()` entry. Fix the internal `import agy_sessions` (tools/agy_run.py:809, used by `--list-sessions`) to `from agent_workflows import agy_sessions` so it resolves from the package, not from `tools/` on `sys.path`.
  - Depends on: none
  - Expected outcome: `agent_workflows/agy_run.py` importable; `agy_run.parse_args([...])` and `agy_run.main([...])` work; `--list-sessions` resolves the packaged `agy_sessions`; behavior parity with the pre-move tool. (NOTE: the tool exposes `parse_args`, NOT `build_parser`.)
  - Execution state: pending

- [ ] E-02 Expose it as `aw agy exec` in `cli.py`: add an `exec` subparser to the `agy_sub` group (currently defined at cli.py:2606, alongside the `sessions`/`view` parsers at 2623/2633, capturing `nargs=REMAINDER` verbatim), AND wire BOTH dispatch sites the other agy subcommands use - the early fast-path forwarder (cli.py:7610-7635, where `sessions`/`view` are matched) AND the argparse dispatch (cli.py:7799-7817, the `if args.command in ("agy","antigravity")` block) - forwarding to `agent_workflows.agy_run.main`. Do NOT register `aw agy run` (that alias stays mapped to `agy_runipd`).
  - Depends on: E-01
  - Expected outcome: `aw agy exec --help` shows the runner usage from BOTH invocation forms; `aw agy run`/`runagy`/`runipd` still route to `agy_runipd`.
  - Execution state: pending

### Task group 2: shim + test migration + inversion + docs

- [ ] E-03 Reduce `tools/agy_run.py` to a thin compat shim that re-exports ALL module attributes of `agent_workflows.agy_run` (the `for _k,_v in vars(...).items()` pattern from tools/agy_sessions.py) and forwards `main` to it, preserving `python3 tools/agy_run.py ...` behavior. The full re-export is REQUIRED because `tools/antigravity_execute_ipd.py` does `import agy_run` and re-exports `ScriptError`/`AgyResult`/`resolve_ipd`/`run_agy`/etc. off it, and the `agy-run-entry-points` compat surface (compat_migration.py:272) asserts the import surface is unchanged - do NOT edit `antigravity_execute_ipd.py`; the shim's re-export must keep its chain resolving.
  - Depends on: E-01
  - Expected outcome: `tools/agy_run.py` is a shim; invoking it forwards to the packaged core with identical behavior; with `tools/` on `sys.path`, `import antigravity_execute_ipd` still resolves `resolve_ipd`/`run_agy`/etc.
  - Execution state: pending

- [ ] E-04 Migrate `tools/test_agy_run.py` (834 lines; it covers BOTH `agy_run` AND `antigravity_execute_ipd` backward-compat, e.g. the `antigravity_execute_ipd` re-export asserts at tools/test_agy_run.py:449-461) to exercise the packaged surface while KEEPING the `antigravity_execute_ipd` compat coverage, and add to `tests/test_agy_tools_graduation.py`: an invocation test (`aw agy exec` runs the packaged core), a shim-forwarding test (`tools/agy_run.py` re-exports `agent_workflows.agy_run`), and a no-collision test (`aw agy run`/`runagy`/`runipd` -> `agy_runipd`, never `agy_run`).
  - Depends on: E-02, E-03
  - Expected outcome: migrated + new tests pass; no-collision invariant proven; `antigravity_execute_ipd` backward-compat still verified.
  - Execution state: pending

- [ ] E-05 Invert the puot79 assertions in `tests/test_agy_tools_graduation.py` that this graduation contradicts (they WILL fail after E-01/E-02 otherwise): `NoAgyRunCollisionTests.test_no_agy_exec_surface_yet` (line 110, asserts `aw agy exec` does NOT exist), `AgyRunUntouchedTests.test_agy_run_tool_still_present_as_standalone` (line 155, asserts `prog="agy_run.py"` still in the tool), and `test_no_packaged_agy_run_core_yet` (line 162, asserts no packaged core). Rewrite each to the post-graduation expectation (exec surface EXISTS; tool is a shim; packaged core EXISTS). Keep `test_agy_run_still_routes_to_runipd` (line 99) UNCHANGED - it is the no-collision invariant that must still pass.
  - Depends on: E-02, E-03
  - Expected outcome: the three inverted assertions reflect the post-graduation state and pass; the no-collision invariant test is preserved and passes.
  - Execution state: pending

- [ ] E-06 Update `tools/README.md`: revise the `agy_run.py` section (line 5) to note the canonical `aw agy exec` surface and the `tools/agy_run.py` compat shim (mirroring the `aw agy sessions`/`aw agy view` sections), keep the `antigravity_execute_ipd.py` note (line 86) accurate given the shim, and note `aw agy run` remains the runipd alias.
  - Depends on: E-02, E-03
  - Expected outcome: `tools/README.md` documents `aw agy exec` and the shim; no stale claim that `tools/agy_run.py` holds the logic.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- awocrunner pattern: packaged core in `agent_workflows/`, host-subcommand group in cli.py (`aw agy` parser at cli.py:2600, `agy_sub` at 2606; the `sessions`/`view` subparsers at 2623/2633 are the template for adding `exec`), thin `tools/` compat shim (`tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`).
- Dispatch happens at TWO sites for `aw agy <sub>`: an early fast-path forwarder (cli.py:7610-7635, where `runipd`/`run`/`runagy`, `sessions`, `view` are matched) AND the argparse dispatch (cli.py:7799-7817). Both MUST be wired for `exec`.
- `aw agy run`/`runagy` are aliases of `aw agy runipd` (cli.py:2607-2609 -> agy_runipd.main at 7613/7802). `aw agy run` is TAKEN; the new surface must be `aw agy exec`.
- puot79 already proved the pattern for agy_sessions/agy_view/pwatch and left the no-`aw agy run`-collision invariant tested (`tests/test_agy_tools_graduation.py::NoAgyRunCollisionTests`, `AgyRunUntouchedTests`).
- `tools/agy_run.py` exposes `parse_args` (NOT `build_parser`), uses a bare `import agy_sessions` internally (line 809), and is depended on by `tools/antigravity_execute_ipd.py` (`import agy_run` + symbol re-export) which `tools/test_agy_run.py` also tests.

## Findings

- OQ-02 (puot79) resolved (B): `agy_run.py` is genuinely distinct from `agy_runipd` (single-target multi-mode runner vs. multi-IPD queue driver); neither imports/supersedes the other. Graduation is therefore additive under a new surface, not a retire/shim-to-runipd.
- THREE puot79 tests contradict this graduation and will fail after E-01/E-02 unless inverted (E-05): (1) `NoAgyRunCollisionTests.test_no_agy_exec_surface_yet` (tests/test_agy_tools_graduation.py:110) asserts `aw agy exec` does NOT exist; (2) `AgyRunUntouchedTests.test_agy_run_tool_still_present_as_standalone` (:155) asserts `prog="agy_run.py"` is still in the tool; (3) `test_no_packaged_agy_run_core_yet` (:162) asserts no packaged core. (The original draft named only `AgyRunUntouchedTests` and missed the collision-suite test; corrected in review.)
- `test_agy_run_still_routes_to_runipd` (tests/test_agy_tools_graduation.py:99) is the no-collision invariant and must stay UNCHANGED and green after graduation.
- The tool exposes `parse_args`, not `build_parser` (tools/agy_run.py:79); V-01 evidence uses `parse_args`.
- `tools/agy_run.py:809` does a bare `import agy_sessions` for `--list-sessions`; moved into the package this must become `from agent_workflows import agy_sessions` (E-01), or `--list-sessions` breaks.
- `tools/antigravity_execute_ipd.py` (tools/antigravity_execute_ipd.py:14-16) does `import agy_run` and re-exports its symbols; `tools/test_agy_run.py:449-461` tests that chain. The E-03 shim must re-export ALL packaged symbols so this keeps resolving WITHOUT editing `antigravity_execute_ipd.py`. The `agy-run-entry-points` compat surface (compat_migration.py:272) asserts the import surface is unchanged; the full-re-export shim preserves it (no compat_migration edit needed).

## Proposed changes (ordered, validatable)

1. `agent_workflows/agy_run.py`: new packaged core (moved from the tool), with `import agy_sessions` -> `from agent_workflows import agy_sessions`.
2. `cli.py`: `aw agy exec` subparser + BOTH dispatch sites (fast-path + argparse); no `aw agy run` change.
3. `tools/agy_run.py`: reduced to a full-re-export compat shim (keeps the `antigravity_execute_ipd` chain resolving; `antigravity_execute_ipd.py` itself untouched).
4. `tools/test_agy_run.py`: migrated to the packaged surface, retaining `antigravity_execute_ipd` compat coverage.
5. `tests/test_agy_tools_graduation.py`: add invocation/shim/no-collision tests AND invert the three contradicted puot79 assertions (`test_no_agy_exec_surface_yet`, `test_agy_run_tool_still_present_as_standalone`, `test_no_packaged_agy_run_core_yet`), keeping `test_agy_run_still_routes_to_runipd` unchanged.
6. `tools/README.md`: document `aw agy exec` + the shim.

## Deferred / out of scope (with reason)

- Any change to `agy_runipd` or the `run`/`runagy`/`runipd` aliases: out of scope (must stay stable; only proven not to collide).
- `tools/antigravity_execute_ipd.py`: NOT edited. Its `import agy_run` + re-export chain keeps resolving via the E-03 full-re-export shim, so no change is required or permitted.

## Scope check

- Over-scope: none.
- Under-scope: none. The complete E-04 disposition is: packaged core (with import fixup) + `aw agy exec` surface (both dispatch sites) + full-re-export shim + test migration (incl. `antigravity_execute_ipd` compat) + inversion of the three contradicted puot79 assertions + doc sync.

## Required tests / validation

- `aw agy exec --help` shows the runner usage from both invocation forms; the packaged core runs.
- `aw agy run`/`runagy`/`runipd` still route to `agy_runipd` (no-collision test, unchanged).
- `tools/agy_run.py` shim re-exports/forwards to the packaged core; behavior preserved; `--list-sessions` still resolves the packaged `agy_sessions`.
- `tools/antigravity_execute_ipd.py` backward-compat (`resolve_ipd`/`run_agy`/etc.) still resolves via the shim.
- Migrated `tools/test_agy_run.py` passes; the three inverted puot79 assertions reflect the post-graduation state and pass.
- Full suite green.

Validation command: `python3 -m pytest tools/test_agy_run.py tests/test_agy_tools_graduation.py -q` plus a full-suite run `python3 -m pytest -p no:randomly -q` (paste ACTUAL runner output; do not claim success unrun).

## Spec / documentation sync

- Update `tools/README.md` (the `agy_run.py` section at line 5) to list `aw agy exec` and note the `tools/agy_run.py` compat shim, mirroring the `aw agy sessions`/`aw agy view` sections; keep the `antigravity_execute_ipd.py` note (line 86) accurate; note `aw agy run` remains the runipd alias. (No other tracked doc lists the `aw agy` subcommands.)

## Open questions

### OQ-01: Retire the shim eventually, or keep it indefinitely?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Keep the thin compat shim (matches the awocrunner precedent for the other graduated tools); a future deprecation is a separate concern, not required for E-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output showing `python3 -c "import agent_workflows.agy_run as m; m.parse_args(['7cvh9t'])"` succeeds (the packaged core exposes `parse_args`/`main` and the `--ipd/--spec/--file/--prompt` surface) AND that `--list-sessions` resolves the packaged `agy_sessions` (the `from agent_workflows import agy_sessions` fixup applied, not a bare `import agy_sessions`); behavior-parity assertion against the pre-move tool.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `aw agy exec --help` output (packaged runner usage) AND a test asserting `cli.main(["agy","run"|"runagy"|"runipd", ...])` routes to `agy_runipd.main` (never `agy_run`) - the no-collision invariant.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted test output where the `tools/agy_run.py` shim re-exports/forwards to `agent_workflows.agy_run`, `python3 tools/agy_run.py --help` still works, AND (with `tools/` on `sys.path`) `import antigravity_execute_ipd` still resolves `resolve_ipd`/`run_agy` off the shim's re-export - proving `antigravity_execute_ipd.py` was not broken and did not need editing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted `python3 -m pytest tools/test_agy_run.py tests/test_agy_tools_graduation.py -q` output (migrated tests pass, incl. the retained `antigravity_execute_ipd` compat coverage; new invocation/shim/no-collision tests pass) AND a full-suite `python3 -m pytest -p no:randomly -q` result.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted test output showing the three inverted assertions pass in their post-graduation form (`aw agy exec` surface EXISTS; `tools/agy_run.py` is a shim; packaged `agent_workflows/agy_run.py` EXISTS) AND that `NoAgyRunCollisionTests.test_agy_run_still_routes_to_runipd` (line 99) remains UNCHANGED and green.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted diff/excerpt of `tools/README.md` showing the `agy_run.py` section now documents `aw agy exec` and the compat shim, and the `antigravity_execute_ipd.py` note remains accurate.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (graduate agy_run.py under aw agy exec + migrate/repair its tests + doc sync); E-01..E-06 are ordered sub-steps of that single deliverable. E-05 (invert the three contradicted puot79 assertions) and E-06 (README) were split out in review because they are distinct test-surfaces/artifacts from the E-04 migration.

Execution contract:

1. Open questions: OQ-01 resolved; execution requires explicit human approval.
2. Scope fence: touch ONLY `agent_workflows/agy_run.py`, `agent_workflows/cli.py`, `tools/agy_run.py`, `tools/test_agy_run.py`, `tools/README.md`, `tests/`. Do NOT edit `tools/antigravity_execute_ipd.py` (its `import agy_run` chain must keep resolving via the E-03 shim). Do NOT change `agy_runipd` or the `run`/`runagy`/`runipd` aliases (only prove no collision). If more seems needed, STOP and report.
3. Honesty rule (HARD MUST): when you report tests/validation passed, paste the ACTUAL runner output (`python3 -m pytest tools/test_agy_run.py tests/test_agy_tools_graduation.py -q` and the full-suite run); never claim success you did not run.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: verify all V items with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed.

Follow-up (out of this plan's scope, but the reason it exists): once this is executed, puot79's E-04/V-04 can be marked performed (citing this plan), puot79 finalizes -> `executed/`, then the runnernorm orchestrator ryvoi5 finalizes.
