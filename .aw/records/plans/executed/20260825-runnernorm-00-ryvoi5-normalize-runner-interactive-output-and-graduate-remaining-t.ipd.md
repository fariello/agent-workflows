# IPD: Normalize runner interactive output and graduate remaining tools under aw

- Date: 2026-08-25
- Kind: orchestrator
- Concern: Follow-on work deferred by the awocrunner Set (which graduated the runipd/runagy IPD-runner drivers to `aw oc runipd` / `aw agy runipd`). Two gaps: (a) runipd's interactive render layer (`render_event`/`Palette`/`Heartbeat` plus coupled module-level helpers `_ANSI_CODES`/`_ANSI_RESET`/`_STATUS_COLOR`/`_ANSI_STRIP_RE`/`_strip_ansi`/`_one_line`, oc_runipd.py:142/108/196 and surrounding) is inline and unshared, so progress/streaming output would be duplicated per tool rather than normalized; (b) several source-checkout tools remain outside the packaged host-subcommand pattern: `tools/agy_run.py`, `tools/agy_sessions.py`, `tools/view-antigravity-jsonl.py`, `tools/pwatch.py`. Backlog item 1sdkvd (medium, non-blocking); the item itself notes it can be split renderer-vs-tool-graduation.
- Scope: (a) Extract runipd's `render_event`/`Palette`/`Heartbeat` streaming layer AND its tightly-coupled module-level helpers into a shared `agent_workflows` rendering utility so interactive/progress output is normalized across consumers, with runipd refactored to consume it (behavior-preserving). (b) Graduate the remaining source-checkout tools under the packaged host-subcommand + compat-shim pattern established by awocrunner (packaged core + `aw <host>` group + thin `tools/` shim): `agy_sessions.py -> aw agy sessions`, `view-antigravity-jsonl.py -> aw agy view`, `pwatch.py -> aw pwatch`. `tools/agy_run.py` graduation is GATED on OQ-02 (its relationship to the already-packaged `agent_workflows/agy_runipd.py` / existing `aw agy runipd` + `run`/`runagy` aliases must be resolved first, and the `aw agy run` name already ALIASES `aw agy runipd` at cli.py:2221 - a naming collision). Two children: 01 shared renderer + runipd refactor; 02 tool graduation (packaged cores + `aw agy`/`aw pwatch` groups + compat shims). Non-blocking; children are independent and may execute in either order.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_run.py, agent_workflows/agy_sessions.py, agent_workflows/agy_view.py, agent_workflows/pwatch.py, agent_workflows/cli.py, tools/, tests/
- Status: executed
- Set: runnernorm
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ryvoi5

## Workflow history
- 2026-08-29 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Finalize runnernorm-00 orchestrator: both children executed; OQ-02 resolved+implemented via ynix69; whole-Set verification evidenced (23/30/2/2680 passed). [Scope reconciliation - in-scope-unmodified agent_workflows/agy_run.py: children-implemented; in-scope-unmodified agent_workflows/agy_sessions.py: children-implemented; in-scope-unmodified agent_workflows/agy_view.py: children-implemented; in-scope-unmodified agent_workflows/cli.py: children-implemented; in-scope-unmodified agent_workflows/oc_runipd.py: children-implemented; in-scope-unmodified agent_workflows/pwatch.py: children-implemented; in-scope-unmodified agent_workflows/render_stream.py: children-implemented; in-scope-unmodified tests/: children-implemented; in-scope-unmodified tools/: children-implemented]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS (OQ-02 blocking); agy_run/aw-agy-run collision surfaced, citations fixed, execution contract added

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Normalize the runner's interactive output into a shared renderer (consumed by runipd) and graduate the remaining source-checkout tools (agy run/sessions/view, pwatch) under the packaged `aw <host>` + compat-shim pattern, per backlog 1sdkvd.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [x] E-01 After children 01-02 execute, confirm runipd uses the shared renderer (no inline duplicate) and each graduated tool runs via `aw agy sessions/view` / `aw pwatch` with a working compat shim, `agy_run.py` is dispositioned per OQ-02 with NO `aw agy run` alias collision, and the full suite is green.
  - Depends on: none
  - Expected outcome: shared renderer has a single definition consumed by runipd; `aw agy sessions/view` and `aw pwatch` invoke the packaged cores; shims forward; `agy_run.py` disposition matches the OQ-02 resolution (no colliding subcommand); suite green.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | shared renderer (dg28i9) | extract `render_event`/`Palette`/`Heartbeat` + coupled helpers into a shared utility; refactor runipd to consume it | none |
| 02 | graduate tools (puot79) | package agy sessions/view + pwatch cores; add `aw agy sessions/view` + `aw pwatch`; thin `tools/` compat shims; `agy_run.py` graduation gated on OQ-02 | none |

Children are independent (may execute in either order); orchestrator verifies. Child 02 must resolve OQ-02 (the `agy_run.py` vs already-packaged `agy_runipd` relationship + the `aw agy run` alias collision) before graduating `agy_run.py`; the other three tools are unaffected.

## Completion criteria (the whole Set is done only when)

- A shared rendering utility exists and runipd consumes it with unchanged behavior (01).
- `agy_sessions`/`view-antigravity-jsonl`/`pwatch` are packaged and invocable as `aw agy sessions/view` and `aw pwatch`, with thin `tools/` compat shims (02).
- `agy_run.py` is dispositioned per OQ-02: either graduated under a NON-colliding surface, or recorded as already-superseded-by-`agy_runipd` (with `tools/agy_run.py` reduced to a shim or retired), with no `aw agy run` alias collision.
- Full test suite green.

## Cross-IPD validation

- Single renderer definition (no duplicated `render_event`/`Palette`/`Heartbeat` + helpers).
- Graduated tools follow the awocrunner packaged-core + host-subcommand + compat-shim pattern (consistency with `aw oc runipd`).
- Discovered in review (blocking, feeds child 02): `agent_workflows/agy_runipd.py` (packaged, ~80KB) already backs `aw agy runipd` (aliases `run`/`runagy`, cli.py:2219-2221); `tools/agy_run.py` (886 lines, full logic, `prog="agy_run.py"`) is a SEPARATE still-un-shimmed Antigravity multi-mode runner. The plan's original "`agy_run.py -> aw agy run` (renamed runagy)" is factually wrong on two counts: (i) `aw agy run` already aliases `aw agy runipd`, so the proposed name collides; (ii) `agy_run.py` may already be superseded by `agy_runipd` (needs disposition, not a fresh graduation). OQ-02 must resolve this.

## Deferred / out of scope (with reason)

- Changing runner behavior/UX beyond normalization: out of scope (behavior-preserving extraction only).

## Scope check

- Over-scope: possible - `tools/agy_run.py` may already be superseded by the packaged `agy_runipd`; re-graduating it would be duplicate work. Gated behind OQ-02 to avoid it.
- Under-scope: the original plan did not surface the `agy_run.py`/`agy_runipd` relationship or the `aw agy run` alias collision (cli.py:2221); now captured in OQ-02 and Cross-IPD validation.

## Required tests / validation

Aggregate of children: renderer unit tests + a golden runipd-output test proving behavior is preserved; graduated-tool invocation tests via `aw agy sessions/view` + `aw pwatch` + shim-forwarding tests; and, per OQ-02, either an `agy_run.py`-superseded disposition (shim/retire, no new subcommand) or a non-colliding `agy_run` surface with its own invocation + shim tests. A test MUST assert no `aw agy run` collision with the existing `runipd` alias. Validation MUST paste the ACTUAL runner output (see V-01); never an un-run "tests pass" claim.

## Open questions

### OQ-01: Compat-alias policy for the graduated tools (sessions/view/pwatch)?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Provide a thin compat shim (as awocrunner did for runipd) so existing `tools/*.py` invocations keep working; finalize alias names in child 02. Applies to `agy_sessions`/`view-antigravity-jsonl`/`pwatch`; `agy_run.py` is handled by OQ-02.

### OQ-02: What is `tools/agy_run.py`'s relationship to the packaged `agy_runipd`, and what surface does it graduate to (given `aw agy run` already aliases `aw agy runipd`)?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED as (B) GENUINELY DISTINCT, and now IMPLEMENTED. `agy_runipd` is a restartable MULTI-IPD QUEUE driver (start/resume/status/report, durable run dir, manifest); `tools/agy_run.py` was a SINGLE-TARGET MULTI-MODE runner (`--ipd/--spec/--file/--prompt`, two-turn skeptical protocol, session-continuity flags) with no queue/manifest/run-dir; neither imports nor supersedes the other. Disposition: graduated under the NON-colliding surface `aw agy exec` (never `aw agy run`, which keeps aliasing runipd). Delivered by child puot79's follow-up plan ynix69 (executed; graduation commit 4579ba8, merged 70235ff, finalized 6204abf). Verified in-repo: `agent_workflows/agy_run.py` packaged core exists; `tools/agy_run.py` reduced 886 -> 41 lines (compat shim); `aw agy run --help` -> `usage: runagy [-h] {start,resume,status,report} ...` (unchanged runipd alias) while `aw agy exec --help` -> the graduated runner; no-collision tests pass (2 passed). The `run`/`runagy` aliases were left UNCHANGED (no removal/repoint needed). Original analysis retained for the record: `agent_workflows/agy_runipd.py` already backs `aw agy runipd` (aliases `run`/`runagy`, cli.py:2219-2221) and `tools/ipdrunner/runagy.py` is already a thin shim to it. But `tools/agy_run.py` (886 lines, `prog="agy_run.py"`) is a SEPARATE un-shimmed multi-mode runner. Decide: (A) `tools/agy_run.py` is already superseded by `agy_runipd` -> disposition = reduce it to a shim (or retire with a RETIRED header), NO new subcommand, and drop it from child 02's graduation scope; or (B) it is genuinely distinct -> graduate it under a NON-colliding surface (NOT `aw agy run`, which aliases runipd - e.g. `aw agy exec` or another name), and add the `run` alias removal/repoint decision explicitly. Until resolved, child 02 MUST NOT touch `agy_run.py`. MUST be resolved before executing the `agy_run.py` portion of child 02.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of the repo's real test runner showing (a) the shared renderer's unit tests + the golden runipd-output test pass (byte-identical output for a fixed event stream) and that `render_event`/`Palette`/`Heartbeat` have a single definition (no inline duplicate in `oc_runipd.py`); (b) `aw agy sessions`, `aw agy view`, and `aw pwatch` invoke the packaged cores and their `tools/*.py` shims forward; (c) the `agy_run.py` disposition per OQ-02 (either a shim/retire with no new subcommand, or a non-colliding surface) with a test asserting no `aw agy run` collision; and (d) the full suite green (paste the actual pass/fail summary line). Also paste `aw ipd lint --phase pre-transition --agent <child>` conforming for children 01 and 02.
  - Observed evidence: (a) SHARED RENDERER - `grep -rn '^def render_event|^class Palette|^class Heartbeat' agent_workflows/*.py` shows the canonical definitions in `agent_workflows/render_stream.py` (`Palette:67`, `render_event:135`, `Heartbeat:228`) and `oc_runipd.py` CONSUMES them via `from agent_workflows.render_stream import (...)` at `oc_runipd.py:39` with an explicit re-export comment at `:53` (NO inline duplicate in oc_runipd). Renderer tests: `python3 -m pytest tests/test_render_stream.py -q -o addopts=""` -> `23 passed in 0.35s`. HONEST CAVEAT (out of this Set's declared scope, recorded not hidden): `agy_runipd.py` still carries its OWN `Palette:125` and `Heartbeat:247` and does not import `render_stream`; child dg28i9's Scope-Paths were `render_stream.py, oc_runipd.py, tests/` only, so the agy-side de-duplication was never in scope for this Set. It is a real remaining gap and is covered by the separate unify-runners backlog item (dhuape). (b) GRADUATED TOOLS - `aw agy sessions` -> `usage: agy sessions [-h] [-a] [--json] [directory]`; `aw agy view` -> `usage: agy view [-h] [--match TEXT] [--raw] [log]`; `aw pwatch` -> `usage: aw pwatch [-h] [-M STRING] ...`; shim-forwarding + invocation tests `python3 -m pytest tests/test_agy_tools_graduation.py tests/test_pwatch.py -q -o addopts=""` -> `30 passed in 1.36s`. (c) AGY_RUN DISPOSITION (OQ-02 option B, delivered by follow-up plan ynix69, executed) - `aw agy run --help` -> `usage: runagy [-h] {start,resume,status,report} ...` (STILL the runipd driver, no collision) while `aw agy exec --help` -> `usage: agy_run.py [-h] [--ipd IPD] [--spec SPEC] ...` (the graduated single-target runner); `tools/agy_run.py` reduced 886 -> 41 lines (compat shim); no-collision tests `-k "Collision or collision"` -> `2 passed, 18 deselected in 0.29s`. (d) FULL SUITE - `python3 -m pytest -p no:randomly` -> `2680 passed, 3 skipped in 25.05s`. Child lint: both children are in executed/ and `aw ipd lint --phase pre-transition` reports `legacy/not evaluated` for them (the linter does not re-evaluate terminal plans), so their conformance was established at their own finalize time (dg28i9 and puot79 both finalized through the gate; puot79 at 1f3e46b).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (orchestrator with two independent children; the only execution step here is whole-Set verification).

### Execution contract

1. Open questions: OQ-02 is BLOCKING for the `agy_run.py` portion of child 02 and MUST be resolved before that portion executes; while it is open, child 02 proceeds only for `agy_sessions`/`view`/`pwatch`, and the Set is NO-GO until OQ-02 is resolved and dispositioned. OQ-01 is non-blocking.
2. Scope fence: touch only the paths in Scope-Paths (renderer, `oc_runipd.py`, the packaged agy/pwatch cores, `cli.py`, `tools/`, `tests/`). Do NOT expand scope; if the work appears to need another file or a subcommand rename beyond OQ-02's resolution, STOP and report.
3. Honesty rule (hard MUST): when you report tests/validation passed, paste the ACTUAL runner output. Never claim a pass you did not run.
4. Commit only this Set's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: perform the terminal transition as a POST-GATE transaction via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` (workflow-history line, terminal `Status:`, `git mv` to `executed/`, index refresh, path-scoped lifecycle commit). It is NOT an `E-*`/`V-*` item. Do not move to `executed/` until every `E-*` is performed and every `V-*` is verified with concrete pasted evidence.
