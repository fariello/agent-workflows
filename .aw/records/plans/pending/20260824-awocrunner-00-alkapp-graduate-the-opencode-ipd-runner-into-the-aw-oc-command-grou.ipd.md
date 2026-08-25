# IPD: Graduate the OpenCode IPD runner into the aw oc command group

- Date: 2026-08-24
- Kind: orchestrator
- Concern: `tools/ipdrunner/runipd.py` (the restartable, non-interactive OpenCode driver that reviews `to-review` plans and executes `approved` ones, persisting durable run state under `.aw/records/runs/`) is genuinely useful but only runnable from a source checkout: it is not packaged (no pyproject/MANIFEST reference), not installed by `aw install`, and the `aw` entrypoint (`agent_workflows.cli:main`) cannot reach it. Users of a pip-installed toolkit have no way to run it. The design ethos (versioning.py: runtime tools stay dumb once copied) argues against copying the 1696-line driver into every repo; instead its importable core should live in the `agent_workflows` package and be exposed as a first-class `aw oc runipd` subcommand.
- Scope: Graduate runipd into the toolkit as `aw oc runipd` (alias `aw opencode runipd`) by (1) moving its core into the package unchanged, (2) adding an `oc`/`opencode` host subcommand group that dispatches into it, (3) reducing `tools/ipdrunner/runipd.py` to a thin compatibility shim so existing invocations keep working, and (4) syncing docs and filing a non-blocking medium backlog item for output normalization and graduating the remaining tools (runagy/agy_run, pwatch, agy sessions/view). Behavior-preserving move; no redesign of the runner or its output rendering in this Set.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/cli.py, tools/ipdrunner/runipd.py, tools/ipdrunner/test_runipd.py, tests/, tools/README.md, .aw/records/backlog/
- Status: approved
- Set: awocrunner
- Order: 0
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: alkapp
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (whole-suite gate + path-preservation + runbook drift in cross-IPD validation), PR-002 (OQ-01 marked resolved)
- 2026-08-25 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; orchestrator to graduate runipd -> `aw oc runipd`, split into 4 dependency-ordered children. Scope deliberately limited to runipd; output normalization and the other tools (runagy, pwatch, agy sessions/view) are a non-blocking medium backlog item (filed by child 04).

## Goal

Make the OpenCode IPD runner available as `aw oc runipd` in any environment where `aw` is installed, without copying live driver code into consumer repos, and without changing the runner's behavior or its (well-liked) streamed progress output. This establishes the packaged-core + host-subcommand + compat-shim pattern that later tool graduations will reuse.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator does not itself edit code; each `E-*` below is the delivery of one child IPD. Execute the children in Order; mark an `E-*` complete only after that child is fully executed (its own V items verified and it has moved to `executed/`).

### Task group 1: Package the core

- [x] E-01 Deliver child IPD Order 01 (ckxgx4): move the runipd core into `agent_workflows/oc_runipd.py` unchanged (behavior-preserving), and migrate its test suite into the package test tree.
  - Depends on: none
  - Expected outcome: `agent_workflows/oc_runipd.py` exists with runipd's full logic; the migrated tests pass under `python3 -m pytest tests/`.
  - Execution state: performed

### Task group 2: Expose the subcommand

- [x] E-02 Deliver child IPD Order 02 (nfo184): add an `oc` (alias `opencode`) top-level subcommand group to `agent_workflows/cli.py` with a `runipd` subcommand that dispatches into `oc_runipd`, mirroring the existing group pattern (e.g. `ipd`/`plan`/`plans`).
  - Depends on: E-01
  - Expected outcome: `aw oc runipd ...` and `aw opencode runipd ...` invoke the packaged runner with parity to the standalone script's CLI.
  - Execution state: performed

### Task group 3: Compat shim

- [x] E-03 Deliver child IPD Order 03 (4tlkgj): reduce `tools/ipdrunner/runipd.py` to a thin shim that imports and delegates to `agent_workflows.oc_runipd`, preserving existing `python3 tools/ipdrunner/runipd.py ...` invocations and re-exports.
  - Depends on: E-01
  - Expected outcome: `python3 tools/ipdrunner/runipd.py ...` still works identically; no logic duplicated in the shim.
  - Execution state: performed

### Task group 4: Docs and backlog

- [x] E-04 Deliver child IPD Order 04 (suks59): update `tools/README.md` (and any doc referencing the driver path) to document `aw oc runipd`; file a non-blocking medium backlog item for normalizing interactive/progress output into a shared renderer and graduating the remaining tools (runagy/agy_run, pwatch, agy sessions, agy view).
  - Depends on: E-02, E-03
  - Expected outcome: docs describe the new command; a committed backlog item captures the deferred follow-on work.
  - Execution state: performed

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | 20260824-awocrunner-01-ckxgx4-extract-runipd-core-into-the-agent-workflows-package-unchang.ipd.md | Move runipd core to `agent_workflows/oc_runipd.py` unchanged; migrate tests | none |
| 02 | 20260824-awocrunner-02-nfo184-add-aw-oc-opencode-subcommand-group-dispatching-to-the-packa.ipd.md | Add `aw oc`/`aw opencode` group + `runipd` subcommand | 01 |
| 03 | 20260824-awocrunner-03-4tlkgj-reduce-tools-ipdrunner-runipd-to-a-thin-compatibility-shim.ipd.md | Reduce `tools/ipdrunner/runipd.py` to a delegating shim | 01 |
| 04 | 20260824-awocrunner-04-suks59-docs-sync-and-non-blocking-backlog-for-output-normalization.ipd.md | Doc sync for `aw oc runipd`; file the deferred-work backlog item | 02, 03 |

Dependency rationale: 01 (packaged core) is the foundation both 02 (subcommand imports it) and 03 (shim imports it) depend on. 02 and 03 are independent of each other and may run in either order once 01 lands. 04 documents the finished surface and so depends on both 02 and 03.

## Completion criteria (the whole Set is done only when)

- `agent_workflows/oc_runipd.py` contains the runipd core with behavior unchanged, covered by migrated tests that pass.
- `aw oc runipd ...` and `aw opencode runipd ...` run the packaged driver with CLI parity to the prior standalone script (start/resume/status/report subcommands and options).
- `python3 tools/ipdrunner/runipd.py ...` still works via a thin shim that duplicates no logic.
- `tools/README.md` documents `aw oc runipd`; a committed medium, non-blocking backlog item captures output normalization + remaining-tool graduation.
- The full suite (`python3 -m pytest tests/`) is green and `pre-commit` passes on touched files.
- Each child IPD's own validation passed with pasted evidence and each child moved to `executed/`.

## Cross-IPD validation

- After all four children execute, confirm there is ONE source of truth for the runner logic: `agent_workflows/oc_runipd.py`. Grep the repo to confirm `tools/ipdrunner/runipd.py` contains only shim/delegation code and no copied logic.
- Run the same runipd smoke invocation two ways (`aw oc runipd status <run-id>` and `python3 tools/ipdrunner/runipd.py status <run-id>`) against a fixture run dir and confirm identical output, proving the shim and the packaged command are the same code path.
- Whole-suite regression gate on the combined result: after the last child, run `python3 -m pytest tests/` on the merged HEAD and paste the actual green output. This is a hard gate, not just a completion-criteria bullet: the three test surfaces added by the children (`test_oc_runipd.py`, `test_oc_runipd_cli.py`, `test_oc_runipd_shim.py`) plus the pre-existing suite must all pass together (no cross-child regression from the move + wiring + shim landing on one tree).
- Path-resolution behavior preservation (verified during review): the runner resolves the runbook/manifest via repo-relative CLI args (`(repo / path).resolve()`, runipd.py:265) and builds a dynamic manifest (runipd.py:471) - it has NO `__file__`-relative dependency on the runbook/manifest data files. So the verbatim move to `agent_workflows/oc_runipd.py` does not break path resolution; confirm this still holds after the move (a `status`/`report` run against a fixture run dir works from the packaged command).
- Runbook filename drift (child 04): the runbook `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md` currently names the driver `ipdrunner.py` and prescribes `python3 tools/ipdrunner/ipdrunner.py ...` (runbook lines 4,47,61,90,98,108), but the actual script is `runipd.py`. When child 04 updates the runbook to present `aw oc runipd`, it MUST also correct this stale `ipdrunner.py` -> `runipd.py` name so the documented legacy/compat path is real. Verify no other doc repeats the wrong `ipdrunner.py` filename.

## Deferred / out of scope (with reason)

- Normalizing the interactive/progress output (render_event/Palette/Heartbeat) into a shared `agent_workflows` renderer is DEFERRED: the runner's output is well-liked and must not change during this move; extracting a shared renderer is best done once a second consumer exists. Child 04 files this as a medium, non-blocking backlog item.
- Graduating the other tools (runagy/agy_run -> `aw agy run`, pwatch -> `aw pwatch`, agy_sessions -> `aw agy sessions`, view-antigravity-jsonl -> `aw agy view`) is DEFERRED to the same backlog item; runipd goes first to establish the pattern.
- Parallel/concurrent Set execution over the `aw ipd execute-set` dependency graph is a separate concern (a different Set) and is NOT part of this graduation.
- `untrack-workflow-artifacts.py` and `tools/awphysical/*` remain source-only maintainer tooling; they are not graduated.

## Scope check

- Over-scope: none. Confined to moving/exposing runipd and the doc/backlog follow-up.
- Under-scope: none. Covers packaging, the command surface, backward compatibility, and documentation/handoff of deferred work.

## Required tests / validation

- Each child ships its own tests/validation (migrated runipd tests; `aw oc runipd` CLI-parity test; shim-delegation test; doc/backlog presence checks). This orchestrator is validated by the children passing plus the two cross-IPD checks above.
- Whole-suite `python3 -m pytest tests/` green after the last child.

## Open questions

### OQ-01: Should the packaged module be named `oc_runipd.py` or a more generic `ipd_runner.py`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED in child 01 (ckxgx4 OQ-01) as `oc_runipd.py`: the runner is OpenCode-specific (it shells out to the `opencode` binary) and pairs with the `aw oc` group; a future `agy run` would get its own module. This orchestrator, children 02/03 (which import the module), and Scope-Paths all consistently use `oc_runipd.py`. Non-blocking; recorded resolved for cross-plan consistency.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: child 01 moved to `executed/`; pasted `python3 -m pytest tests/` output showing the migrated runipd tests passing; confirmation `agent_workflows/oc_runipd.py` exists.
  - Observed evidence: child `20260824-awocrunner-01-ckxgx4-extract-runipd-core-into-the-agent-workflows-package-unchang.ipd.md` is `Status: executed` under `.aw/records/plans/executed/` with its own V-01..V-03 all `Result: pass`; product commit ca04e63 (`feat(oc-runipd): extract runipd core into agent_workflows package unchanged (ckxgx4)`), evidence fb72860, finalize 41ef2ac. Re-verified live at HEAD 4d108b3: `agent_workflows/oc_runipd.py` exists (2257 lines, contains the full runner core including DriverError/Palette/Heartbeat/PlanRecord and the start/resume/status/report logic); migrated test surface `tests/test_oc_runipd.py` present. Whole suite `python3 -m pytest tests/` -> `2221 passed, 1 skipped in 17.39s` (includes the migrated runipd tests).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: child 02 moved to `executed/`; pasted output of `aw oc runipd --help` and `aw opencode runipd --help` and one real invocation (e.g. `aw oc runipd status <run-id>`) showing parity with the standalone script.
  - Observed evidence: child `20260824-awocrunner-02-nfo184-add-aw-oc-opencode-subcommand-group-dispatching-to-the-packa.ipd.md` is `Status: executed` under `.aw/records/plans/executed/` with its own V-01..V-03 all `Result: pass`; product commit 524782a (`feat(cli): add aw oc / aw opencode group dispatching to packaged runipd (nfo184)`), evidence 4692254, finalize 2844803. Re-verified live at HEAD 4d108b3: `aw oc runipd --help` and `aw opencode runipd --help` both print `usage: runipd [-h] {start,resume,status,report} ...` (the alias resolves to the same group), exit 0. Real invocation `aw oc runipd status --repo $PWD run-20260825T105819Z-1469310` succeeded (exit 0), rendering the run table (positions 01 rmwr8s executed, 02 uvsmmy executed, 03 alkapp running). CLI parity with the standalone script proven by the identical-output diff in V-03.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: child 03 moved to `executed/`; pasted output of `python3 tools/ipdrunner/runipd.py status <run-id>` matching the `aw oc runipd status <run-id>` output; a diff/snippet showing the shim contains only delegation.
  - Observed evidence: child `20260824-awocrunner-03-4tlkgj-reduce-tools-ipdrunner-runipd-to-a-thin-compatibility-shim.ipd.md` is `Status: executed` under `.aw/records/plans/executed/` with its own V-01/V-02 `Result: pass`; product commit 8ce7a09 (`refactor(runipd): reduce tools/ipdrunner/runipd.py to a thin compat shim (4tlkgj)`), evidence 2eb3791, finalize 0796d7c. Re-verified live at HEAD 4d108b3: `diff <(aw oc runipd status --repo $PWD run-20260825T105819Z-1469310) <(python3 tools/ipdrunner/runipd.py status --repo $PWD run-20260825T105819Z-1469310)` is EMPTY (identical output, both exit 0), proving the shim and packaged command are one code path. The shim (`tools/ipdrunner/runipd.py`, 39 lines) contains ONLY delegation: `sys.path` setup, `from agent_workflows import oc_runipd`, re-exports (`main = oc_runipd.main`, `DriverError`/`Palette`/`Heartbeat`/`PlanRecord`), and `raise SystemExit(oc_runipd.main(sys.argv[1:]))`; grep for `^def `/`^class ` in the shim returns nothing (no duplicated logic).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: child 04 moved to `executed/`; snippet of `tools/README.md` documenting `aw oc runipd`; path of the committed backlog item (via `aw backlog`) capturing output normalization + remaining-tool graduation.
  - Observed evidence: child `20260824-awocrunner-04-suks59-docs-sync-and-non-blocking-backlog-for-output-normalization.ipd.md` is `Status: executed` under `.aw/records/plans/executed/` with its own V-01/V-02 `Result: pass`; product commit 22da425 (`docs(oc-runipd): document aw oc runipd as primary + file deferred-work backlog (suks59)`), evidence e843be2, finalize 37c90e7. Re-verified live at HEAD 4d108b3: `tools/README.md:139` has a `## \`aw oc runipd\` (the OpenCode IPD runner)` section documenting the packaged command, the alias `aw opencode runipd`, and the compat shim. Committed backlog item `.aw/records/backlog/open/20260825-1sdkvd-01-1sdkvd-normalize-runner-output-and-graduate-tools.backlog.md` (Id 1sdkvd, Status open, Priority medium) captures output normalization + graduating runagy/pwatch/agy tools. Runbook drift corrected: `grep ipdrunner.py tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md` returns 0 matches (the stale `ipdrunner.py` filename is gone; the runbook now presents `aw oc runipd` and the `runipd.py` compat shim), and no other doc repeats the wrong filename.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (graduate the OpenCode IPD runner into `aw oc`) delivered as four dependency-ordered children, each a small single-surface change; splitting maximizes clean, independently-verifiable execution and keeps the behavior-preserving move separate from the CLI wiring and the compat shim.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and deferred to child 01. No blocking open question remains.
2. Scope fence: this orchestrator authors no code; execute children in Order (01 first; then 02 and 03 in either order; then 04), each under its own scope fence. Do NOT begin a child before its declared dependencies are `executed`. The move must be behavior-preserving: do NOT redesign the runner or its output during this Set.
3. Honesty rule (hard MUST): when reporting a child complete, rely on that child's pasted validation evidence; never mark an `E-*`/`V-*` here from narration.
4. Commit ONLY each child's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: this orchestrator moves to `executed/` only after all four children are `executed`, every V item here is verified with pasted evidence, the `## Workflow history` line is appended, and `Status: executed` is set, via the lifecycle workflow.
