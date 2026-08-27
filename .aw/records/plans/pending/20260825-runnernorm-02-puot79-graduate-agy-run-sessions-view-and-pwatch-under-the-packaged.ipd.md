# IPD: Graduate agy run/sessions/view and pwatch under the packaged host-subcommand + compat-shim pattern

- Date: 2026-08-25
- Kind: child
- Concern: Several source-checkout tools remain outside the packaged host-subcommand pattern that awocrunner established for the IPD runner (`aw oc runipd` + packaged core + thin `tools/` compat shim; the `aw oc`/`aw agy` groups are declared at cli.py:2193/2212 and dispatched at cli.py:7090/7100): `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, `tools/pwatch.py`. They should be graduated so they are invocable via `aw` and covered by the package. NOTE (found in review): `tools/agy_run.py` is a SEPARATE case - see OQ-02 - because `agent_workflows/agy_runipd.py` is already packaged as `aw agy runipd` (with `run`/`runagy` aliases, cli.py:2219-2221, dispatch cli.py:7102) and `tools/agy_run.py` (886 lines, `prog="agy_run.py"`) is still un-shimmed; the surface `aw agy run` is ALREADY taken by the runipd driver.
- Scope: Graduate the three unambiguous tools under the awocrunner packaged-core + host-subcommand + compat-shim pattern: (1) move each tool's logic into a packaged `agent_workflows` core module (`agy_sessions.py`, `agy_view.py`, `pwatch.py`); (2) expose `aw agy sessions`, `aw agy view`, and `aw pwatch` via cli.py (extending the existing `aw agy` group, cli.py:2212, and adding a top-level `aw pwatch`); (3) reduce each corresponding `tools/*.py` to a thin compat shim that forwards to the packaged entry (as `tools/ipdrunner/runipd.py` was reduced). `tools/agy_run.py` is GATED on OQ-02 and MUST NOT be touched until that question is resolved (its target surface cannot be `aw agy run`, which already aliases `aw agy runipd`). Add invocation tests (each `aw` subcommand runs the packaged core) and shim-forwarding tests, including a test asserting NO `aw agy run` collision. If child 01's shared renderer has landed, the graduated tools may consume it; if not, leave their output as-is (adoption is optional, not required for graduation).
- Scope-Paths: agent_workflows/agy_sessions.py, agent_workflows/agy_view.py, agent_workflows/pwatch.py, agent_workflows/cli.py, tools/agy_sessions.py, tools/view-antigravity-jsonl.py, tools/pwatch.py, tests/ (agent_workflows/agy_run.py + tools/agy_run.py are IN SCOPE only once OQ-02 is resolved; do not touch them before then)
- Status: approved
- Set: runnernorm
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: puot79
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS (OQ-02 blocking); agy_run collision split out and gated, scope right-sized, citations fixed, execution contract added

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Graduate `agy_sessions`/`view-antigravity-jsonl`/`pwatch` into packaged cores exposed as `aw agy sessions/view` and `aw pwatch`, with thin `tools/` compat shims, following the awocrunner pattern. `agy_run.py` is dispositioned separately per OQ-02 (its `aw agy run` surface already aliases the runipd driver).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

Do not execute the `agy_run.py` disposition (E-06) until OQ-02 is resolved.

### Task group 1: agy sessions/view

- [x] E-01 Move `tools/agy_sessions.py` and `tools/view-antigravity-jsonl.py` logic into packaged cores (`agent_workflows/agy_sessions.py`, `agent_workflows/agy_view.py`) and add `sessions`/`view` subcommands to the existing `aw agy` group in cli.py (declared cli.py:2212, dispatched cli.py:7100), forwarding REMAINDER as `aw agy runipd` does.
  - Depends on: none
  - Expected outcome: `aw agy sessions` and `aw agy view` invoke the packaged cores.
  - Done note (commit 48cf10a): `git mv`'d the two tools into `agent_workflows/agy_sessions.py` and `agent_workflows/agy_view.py` (content-preserving; `agy_view.main` now takes `argv`); added `aw agy sessions` and `aw agy view` (+ `view-antigravity-jsonl` alias) subparsers to the existing `aw agy` group and both early-dispatch (verbatim REMAINDER) and main-dispatch in cli.py.
  - Execution state: performed

### Task group 2: pwatch

- [x] E-02 Move `tools/pwatch.py` into a packaged `agent_workflows/pwatch.py` and expose a top-level `aw pwatch` subcommand in cli.py.
  - Depends on: none
  - Expected outcome: `aw pwatch` runs the packaged core.
  - Done note (commit 48cf10a): `git mv`'d `tools/pwatch.py` -> `agent_workflows/pwatch.py` (content-preserving; `prog` updated to `aw pwatch`); added a top-level `aw pwatch` subparser + early/main dispatch forwarding REMAINDER to `pwatch.main`.
  - Execution state: performed

### Task group 3: compat shims

- [x] E-03 Reduce `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, and `tools/pwatch.py` to thin compat shims that forward to their packaged entries (as `tools/ipdrunner/runipd.py` was reduced), preserving each tool's prior CLI behavior.
  - Depends on: E-01, E-02
  - Expected outcome: each of the three `tools/*.py` shims forwards to its packaged core and still works.
  - Done note (commit 48cf10a): each `tools/*.py` is now a thin shim (sys.path bootstrap + import packaged core + re-export all public/private attrs via `vars()` + delegate `main`), mirroring `tools/ipdrunner/runipd.py`. Verified `tools/watch-agy.py` (which `import pwatch` + calls `build_parser`/`main`) still works through the shim, and `tests/test_pwatch.py` (`import pwatch` from `tools/`) still passes via the re-exported symbols.
  - Execution state: performed

### Task group 4: agy_run disposition (gated on OQ-02)

- [ ] E-04 Disposition `tools/agy_run.py` per OQ-02: EITHER (A) reduce it to a shim / retire it as superseded by the packaged `agy_runipd` with NO new subcommand, OR (B) if genuinely distinct, graduate it under a NON-colliding surface (not `aw agy run`), adding a test that asserts no collision with the existing `run`/`runagy` runipd aliases (cli.py:2219-2221). Migrate/adapt `tools/test_agy_run.py` accordingly.
  - Depends on: none
  - Expected outcome: `agy_run.py` is dispositioned with no `aw agy run` collision; `tools/test_agy_run.py` passes against the chosen disposition. (GATED: blocked until OQ-02 is resolved - see the execution contract; not a code dependency.)
  - Execution note: OQ-02 is now RESOLVED as (B) genuinely distinct (see plan OQ-02 + run decision 03-puot79-D1). The DISPOSITION decision is made (graduate under a NON-colliding surface, recommended `aw agy exec`; NOT `aw agy run`, which keeps aliasing runipd). However, the actual graduation (886-line runner + 37KB test migration + its own surface design) is SPLIT OUT to a dedicated follow-up plan, as this plan's cohesion rationale explicitly permits; it is NOT executed in this turn. `tools/agy_run.py` and `tools/test_agy_run.py` are UNTOUCHED. The no-`aw agy run`-collision invariant is proven by `tests/test_agy_tools_graduation.py::NoAgyRunCollisionTests`. Deferred to follow-up (see run deferred 03-puot79-Q1).
  - Execution state: blocked

## Project conventions discovered (Step 0)

- awocrunner pattern: packaged core in `agent_workflows/`, host-subcommand group declared in cli.py (`aw oc` at cli.py:2193, `aw agy` at cli.py:2212) and dispatched at cli.py:7090/7100, thin `tools/` compat shim (`tools/ipdrunner/runipd.py`, and `tools/ipdrunner/runagy.py` already shims `agy_runipd`).
- The IPD runner is ALREADY graduated: `agent_workflows/agy_runipd.py` backs `aw agy runipd` with `run`/`runagy` aliases (cli.py:2219-2221) all routed to `agy_runipd.main()` at cli.py:7102. So `aw agy run` is taken.
- `tools/agy_run.py` (886 lines, `prog="agy_run.py"`) is a SEPARATE, still-un-shimmed Antigravity multi-mode runner; its relationship to `agy_runipd` is unresolved (OQ-02). `tools/test_agy_run.py` (37KB) tests it.
- Tools to graduate now (unambiguous): `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, `tools/pwatch.py`.

## Findings

Graduation of the three unambiguous tools is mechanical and precedented; the risk is preserving each tool's CLI surface behind the shim. `agy_run.py` is NOT mechanical: the plan originally proposed `aw agy run`, which collides with the existing runipd alias, and `agy_run.py` may already be superseded by the packaged `agy_runipd`. That case is gated on OQ-02 and split into its own E-item.

## Proposed changes (ordered, validatable)

1. `agent_workflows/agy_sessions.py`/`agy_view.py`/`pwatch.py`: packaged cores.
2. `cli.py`: add `aw agy sessions/view` to the existing `aw agy` group + a top-level `aw pwatch`.
3. `tools/agy_sessions.py`/`view-antigravity-jsonl.py`/`pwatch.py`: thin compat shims forwarding to packaged entries.
4. `agy_run.py`: dispositioned per OQ-02 (shim/retire, or non-colliding graduation); migrate `tools/test_agy_run.py`.
5. `tests/`: `aw` invocation tests + shim-forwarding tests + a no-`aw agy run`-collision assertion.

## Deferred / out of scope (with reason)

- The shared renderer extraction: child 01 (independent); graduated tools MAY consume it once landed, but adoption is not required for graduation.
- `agy_run.py` graduation surface/disposition: gated on OQ-02; not executed until resolved.

## Scope check

- Over-scope: possible for `agy_run.py` (may already be superseded by `agy_runipd`); gated behind OQ-02 to avoid duplicate graduation.
- Under-scope (found in review, now corrected): the original checklist proposed the colliding `aw agy run` surface and bundled three tools + cli group in one E-item; split, and the collision is now an explicit no-collision test.

## Required tests / validation

- `aw agy sessions`, `aw agy view`, and `aw pwatch` each run the packaged core (invocation tests).
- Each of the three graduated `tools/*.py` compat shims forwards to the packaged entry and preserves prior behavior.
- A test asserts `aw agy run` still resolves to the runipd driver (no collision introduced).
- Per OQ-02 disposition: `tools/test_agy_run.py` passes against the chosen `agy_run.py` disposition.
- Validation MUST paste the ACTUAL test-runner output (see V-items); never an un-run "tests pass" claim.

## Spec / documentation sync

- Update docs/READMEs to list `aw agy sessions/view` and `aw pwatch`; note the compat shims and the `agy_run.py` disposition decided in OQ-02.

## Open questions

### OQ-01: Should `aw agy view` keep the `view-antigravity-jsonl` name as an alias?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED (yes). The canonical surface is `aw agy view`; the old name is preserved two ways: (1) a thin compat shim at `tools/view-antigravity-jsonl.py` forwarding to the packaged core, and (2) a `view-antigravity-jsonl` subcommand ALIAS on `aw agy view` (cli.py). Both verified working.

### OQ-02: What is `tools/agy_run.py`'s relationship to the packaged `agy_runipd`, and what surface does it graduate to?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED as (B) GENUINELY DISTINCT (see run decision 03-puot79-D1 for full evidence). `agy_runipd` is a restartable MULTI-IPD QUEUE driver (start/resume/status/report, durable run dir, manifest); `tools/agy_run.py` is a SINGLE-TARGET MULTI-MODE runner (`--ipd/--spec/--file/--prompt`, two-turn skeptical protocol, session-continuity flags) with no queue/manifest/run-dir. Neither imports the other; `agy_runipd` does not supersede `agy_run`'s single-shot modes. Therefore `agy_run.py`, when graduated, MUST take a NON-colliding surface (recommended `aw agy exec`) - never `aw agy run`, which keeps aliasing `aw agy runipd` (verified: `aw agy run` still resolves to `runagy`). The `run`/`runagy` aliases are UNCHANGED. Per this plan's cohesion rationale, the actual graduation of `agy_run.py` (886 lines + 37KB test + its own surface design) is SPLIT OUT to a dedicated follow-up plan and is NOT executed here; `tools/agy_run.py` + `tools/test_agy_run.py` remain UNTOUCHED this turn. The no-collision invariant is proven by a test (V-03). E-04 is therefore deferred (see its Execution state); the three unambiguous tools are fully graduated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted test-runner output: `aw agy sessions` and `aw agy view` invoke the packaged cores (`agy_sessions.py`/`agy_view.py`), forwarding args correctly.
  - Observed evidence: `python3 -m pytest tests/test_agy_tools_graduation.py -p no:randomly` -> `15 passed in 1.59s`. `AgySessionsSurfaceTests` asserts `cli.main(["agy","sessions","--json","/some/dir"])` calls `agy_sessions.main(["--json","/some/dir"])` and the `antigravity` alias delegates identically, and `agy sessions --help` shows the core's help (prog `agy sessions`). `AgyViewSurfaceTests` asserts `cli.main(["agy","view","--raw","-"])` calls `agy_view.main(["--raw","-"])`, the `view-antigravity-jsonl` alias delegates, and `agy view --help` shows the core's help. Live: `python3 -m agent_workflows agy sessions --json` emits the JSON session list; `echo '{...}' | python3 -m agent_workflows agy view` formats the record.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Pasted test-runner output: `aw pwatch` runs the packaged `agent_workflows/pwatch.py` core.
  - Observed evidence: Part of the same `15 passed` run. `PwatchSurfaceTests` asserts `cli.main(["pwatch","-M","python","--once"])` calls `pwatch.main(["-M","python","--once"])` and `pwatch --help` shows the packaged core's help (prog `aw pwatch`). Live: `python3 -m agent_workflows pwatch --help` prints the packaged parser usage.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Pasted test-runner output: `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, and `tools/pwatch.py` each forward to their packaged entry and preserve prior behavior; plus a test asserting `aw agy run` still resolves to the runipd driver (no collision). Include the full-suite green summary line and `aw ipd lint --phase pre-transition --agent <this plan>` conforming.
  - Observed evidence: Same `15 passed` run. `CompatShimForwardingTests` loads each `tools/*.py` shim and asserts it re-exports the packaged module object and its public symbols (`shim.get_sessions is agy_sessions.get_sessions`, `shim.format_record is agy_view.format_record`, `shim.build_parser is pwatch.build_parser`, and `shim.main is <core>.main`). `NoAgyRunCollisionTests::test_agy_run_still_routes_to_runipd` asserts `cli.main(["agy","run"|"runagy"|"runipd","status","run-xyz"])` calls `agy_runipd.main(["status","run-xyz"])` and NEVER the sessions/view cores; live `python3 -m agent_workflows agy run --help` -> `usage: runagy ...`. Behavior preservation also confirmed by the pre-existing `tests/test_pwatch.py` (`import pwatch` from `tools/`) -> `10 passed`, and `tools/watch-agy.py --help` still works via the shim. FULL SUITE: `python3 -m pytest -p no:randomly` -> `2336 passed, 1 skipped`. Verifier correction: `aw ipd lint --phase pre-transition --agent <this plan>` does NOT conform while E-04/V-04 remain intentionally deferred: it reports exactly 2x IPD-S404 (`E-04: not 'performed' at pre-transition` line 58; `V-04: not 'pass' at pre-transition` line 137) and exits 1. This is the EXPECTED and correct state for the E-01..E-03 slice: the plan is deliberately NOT finalized to `executed/` while the agy_run graduation (E-04) is split to a follow-up plan. The three-tool graduation (E-01/E-02/E-03) is itself complete and validated.
  - Result: pass
- [ ] V-04 validates E-04
  - Required evidence: Pasted test-runner output for the OQ-02 disposition: either (A) `tools/agy_run.py` reduced to a shim/retired with no new subcommand, or (B) graduated under a non-colliding surface; and the migrated `tools/test_agy_run.py` passing.
  - Observed evidence: E-04 is BLOCKED (deferred): OQ-02 resolved to (B) genuinely distinct, and the graduation is split to a follow-up plan (run deferred 03-puot79-Q1); `tools/agy_run.py` is intentionally UNTOUCHED this turn, so there is no disposition artifact to validate here. The INVARIANT for E-04 that IS enforced now - no `aw agy run` collision - is proven by `NoAgyRunCollisionTests` (see V-03) plus `AgyRunUntouchedTests` (asserts `tools/agy_run.py` still carries `prog="agy_run.py"` and no packaged `agent_workflows/agy_run.py` exists), both in the `15 passed` run. `tools/test_agy_run.py` (unchanged) -> `42 passed`.
  - Result: blocked



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (graduate the remaining source-checkout tools under the packaged pattern). The E-items are per-tool sub-steps of that one concern; the `agy_run.py` disposition (E-04) is gated on OQ-02 and may be split into a separate follow-up plan if OQ-02 resolves it to a genuinely distinct tool needing its own surface design.

### Execution contract

1. Open questions: OQ-02 is BLOCKING for the `agy_run.py` disposition (E-04) and MUST be resolved before that item executes; while it is open, execute only E-01/E-02/E-03 for the three unambiguous tools, and the plan is NO-GO overall until OQ-02 is resolved. OQ-01 is non-blocking.
2. Scope fence: touch only the Scope-Paths (agy_sessions/agy_view/pwatch cores, cli.py, the three `tools/*.py` shims, tests). Do NOT touch `agy_run.py` until OQ-02 is resolved. If more seems needed, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/validation passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit only this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: as a POST-GATE transaction (not an `E-*`/`V-*` item) run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` to write the workflow-history line, set terminal `Status:`, `git mv` to `executed/`, refresh the index, and make the path-scoped lifecycle commit. Do not move to `executed/` until every `E-*` is performed and every `V-*` verified with concrete pasted evidence.
