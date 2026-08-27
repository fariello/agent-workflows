# IPD: Extract runipd render_event/Palette/Heartbeat into a shared agent_workflows rendering utility

- Date: 2026-08-25
- Kind: child
- Concern: runipd's interactive streaming layer (`render_event`, oc_runipd.py:142; `Palette`, oc_runipd.py:108; `Heartbeat`, oc_runipd.py:196) is inline in `oc_runipd.py`, so any other consumer that wants normalized progress/streaming output must duplicate it. It should be a shared `agent_workflows` rendering utility.
- Scope: Extract `render_event`/`Palette`/`Heartbeat` (and any tightly-coupled helpers) into a new shared module (e.g. `agent_workflows/render_stream.py`), then refactor `oc_runipd.py` to import and use it, behavior-preserving (identical rendered output for the same event stream). No UX/behavior change; pure extraction + de-duplication. Add unit tests for the shared renderer (event -> rendered line, palette application, heartbeat lifecycle) and confirm runipd output is unchanged.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, tests/
- Status: approved
- Set: runnernorm
- Order: 1
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: dg28i9
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-runnernorm findings fixed (stub gate, V-01 evidence, stale citations); no open questions

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Extract runipd's `render_event`/`Palette`/`Heartbeat` streaming layer into a shared `agent_workflows` rendering utility and refactor runipd to consume it, behavior-preserving, so interactive output is normalized and reusable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: extract + refactor

- [x] E-01 Move `render_event` (oc_runipd.py:142), `Palette` (oc_runipd.py:108), `Heartbeat` (oc_runipd.py:196), and the tightly-coupled module-level helpers `_ANSI_RESET` (oc_runipd.py:64), `_ANSI_CODES` (oc_runipd.py:65), `_ANSI_STRIP_RE` (oc_runipd.py:76), `_STATUS_COLOR` (oc_runipd.py:79), `_strip_ansi` (oc_runipd.py:130), and `_one_line` (oc_runipd.py:134) into a new `agent_workflows/render_stream.py`; refactor `oc_runipd.py` to import them (its call sites at oc_runipd.py:1426/1446/1459/1571/1928 keep working, with `should_color` still supplied by the caller per OQ-01). Behavior-preserving (identical rendered output for the same event stream).
  - Depends on: none
  - Expected outcome: `render_stream` holds the single definitions; `oc_runipd` imports them; runipd output is byte-identical for a fixed event stream.
  - Done note (commit 275324a): created `agent_workflows/render_stream.py` holding the single definitions of `render_event`/`Palette`/`Heartbeat` + the coupled helpers `_ANSI_RESET`/`_ANSI_CODES`/`_ANSI_STRIP_RE`/`_STATUS_COLOR`/`_strip_ansi`/`_one_line`; `oc_runipd.py` now imports them and re-exports via `__all__`; `should_color` stays caller-owned per OQ-01; call sites (now at oc_runipd.py:1253/1273/1286/1398/1755 and the `_STATUS_COLOR` use at :1575 after the -141-line deletion) keep working.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The render layer lives at oc_runipd.py:108 (`Palette`), :142 (`render_event`), :196 (`Heartbeat`), plus coupled module-level helpers at oc_runipd.py:64-134 (`_ANSI_RESET`/`_ANSI_CODES`/`_ANSI_STRIP_RE`/`_STATUS_COLOR`/`_strip_ansi`/`_one_line`). It is used at the runipd streaming call sites: `Palette(should_color(...))` at oc_runipd.py:1426/1571/1928 and `Heartbeat(pal, ...)`/`render_event(line, pal)` at oc_runipd.py:1446/1459.
- `Palette` is constructed with `should_color(sys.stdout)`; `should_color` is itself DUPLICATED (oc_runipd.py:95, agy_runipd.py:100, term.py:74). Unifying it is deferred (OQ-01); the extracted renderer takes the color decision from its caller, so this refactor does not depend on that consolidation.
- awocrunner reduced `tools/ipdrunner/runipd.py` to a thin shim after packaging the core; the same packaged-core discipline applies to shared internals.

## Findings

Pure refactor: the risk is behavior drift, mitigated by a golden-output test over a fixed event stream before and after extraction.

## Proposed changes (ordered, validatable)

1. `render_stream.py`: new module holding `render_event`/`Palette`/`Heartbeat`.
2. `oc_runipd.py`: import from `render_stream`; delete inline definitions.
3. `tests/`: renderer unit tests + a golden runipd-output test proving no behavior change.

## Deferred / out of scope (with reason)

- Adopting the shared renderer in other tools: those tools are graduated in child 02; broad adoption can follow once they are packaged.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Unit tests: `render_event` maps sample events to expected lines; `Palette` applies/omits color per settings; `Heartbeat` lifecycle (enter/exit/interval).
- Golden test: runipd rendered output for a fixed event stream is identical before/after extraction.

## Spec / documentation sync

- N/A (internal refactor; no user-facing surface change).

## Open questions

### OQ-01: Should the shared renderer subsume the duplicated `should_color` TTY logic too?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: `should_color` is defined three times (oc_runipd.py:95, agy_runipd.py:100, term.py:74; `term.py` is the natural canonical home). Keep scope to the runipd render layer; the extracted renderer takes the color flag from its caller. Unifying the three `should_color` copies is a possible later consolidation, not required here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of the repo's real test runner showing (a) the new `render_stream` unit tests pass (`render_event` sample-event->line mapping; `Palette` applies/omits color per the flag; `Heartbeat` enter/exit/interval lifecycle); (b) a golden test proving runipd's rendered output for a fixed event stream is BYTE-IDENTICAL before and after extraction; (c) `render_event`/`Palette`/`Heartbeat` and the coupled helpers have a SINGLE definition in `render_stream.py` with no inline copy left in `oc_runipd.py` (e.g. a grep/import assertion); and (d) the full suite green (paste the actual pass/fail summary line).
  - Observed evidence: (a)+(b)+(c) new renderer tests `tests/test_render_stream.py`: `python3 -m pytest tests/test_render_stream.py -p no:randomly` -> `21 passed in 2.66s`; the 21 tests cover `RenderEventUnitTests` (event->line mapping), `PaletteUnitTests` (color applied/omitted per flag + status mapping + strip_ansi), `HeartbeatLifecycleTests` (disabled writes nothing / enabled emits while idle / touch+format), the GOLDEN `GoldenByteIdenticalTests` (`test_plain_transcript_is_byte_identical` pins the exact transcript for a fixed 9-event stream, `test_driver_reexport_produces_identical_transcript` proves the `oc_runipd` re-export yields the SAME transcript as `render_stream`, `test_colored_transcript_strips_back_to_plain`), and `SingleDefinitionTests` (identity `driver.Palette is render_stream.Palette` etc.; `inspect.getmodule(...) == agent_workflows.render_stream`; a source-inspection assertion that `oc_runipd` contains NO inline `class Palette:`/`class Heartbeat:`/`def render_event(`/`def _one_line(`/`def _strip_ansi(` and DOES `from agent_workflows.render_stream import`). (b') Behavior preservation across the existing runipd suite: `python3 -m pytest tests/test_oc_runipd.py tests/test_oc_runipd_cli.py tests/test_oc_runipd_shim.py tests/test_render_stream.py -p no:randomly` -> `86 passed in 3.16s` (the pre-existing `ProgressRendererTests`/`HeartbeatFormattingTests`, which call `driver.Palette`/`driver.render_event`/`driver.Heartbeat`, still pass unchanged). (d) full suite `python3 -m pytest -p no:randomly` -> `2321 passed, 1 skipped in 29.03s`. Ruff (pre-commit v0.4.4 default set) `ruff check --select E4,E7,E9,F agent_workflows/render_stream.py agent_workflows/oc_runipd.py` -> `All checks passed!`; commit 275324a's `ruff`/`ruff-format` pre-commit hooks Passed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (single cohesive concern: extract one render layer and refactor its one consumer).

### Execution contract

1. Open questions: OQ-01 is non-blocking (the `should_color` consolidation is explicitly deferred); no blocking questions remain.
2. Scope fence: touch only `agent_workflows/render_stream.py`, `agent_workflows/oc_runipd.py`, and `tests/` (per Scope-Paths). Behavior-preserving extraction only - no UX/output change. If it appears to need a `should_color` unification or another file, STOP and report.
3. Honesty rule (hard MUST): when you report tests/validation passed, paste the ACTUAL runner output; never claim a pass you did not run. The golden byte-identical test is the core evidence that behavior was preserved.
4. Commit only this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: as a POST-GATE transaction (not an `E-*`/`V-*` item) run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` to write the workflow-history line, set terminal `Status:`, `git mv` to `executed/`, refresh the index, and make the path-scoped lifecycle commit. Do not move to `executed/` until E-01 is performed and V-01 is verified with concrete pasted evidence.
