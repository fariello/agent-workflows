# IPD: Add Blocks-Release to IPD schema recognized fields

- Date: 2026-08-24
- Kind: child
- Concern: The IPD linter's recognized-field set omits `Blocks-Release`. `agent_workflows/ipd_schema.py` parse records any field not in `META_RECOGNIZED` as an error, surfaced by `aw ipd lint` as IPD-M103 "unknown field" (verified by hand-adding the field to an approved IPD and running `aw ipd lint`). Because `aw ipd lint` gates execution (pre-execution/pre-transition checkpoints), a plan that carries the field currently FAILS lint and cannot be executed. Meanwhile `attention.py` already scans any artifact for `- Blocks-Release:`, so the toolkit is internally inconsistent.
- Scope: Add `Blocks-Release` to the IPD schema recognized-field set as an optional, single-valued field (a release id6 or `next`), so an IPD may legally carry it and lint clean at every phase. Add a regression test guarding against re-introducing IPD-M103. This is the foundation child of the vwios6ipd Set (Order 00 orchestrator uvsmmy); nothing else can be exercised until the schema accepts the field.
- Scope-Paths: agent_workflows/ipd_schema.py, tests/test_ipd_schema.py
- Status: approved
- Set: vwios6ipd
- Order: 1
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: si3mmt
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (spec-sync clarified to N/A)
- 2026-08-24 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 01 of vwios6ipd Set (schema recognition foundation).

## Goal

Make `Blocks-Release` a recognized-but-optional IPD metadata field so an IPD carrying `- Blocks-Release: next` (or a real release id6) lints CONFORMING at author/pre-execution/pre-transition/post-transition, eliminating the IPD-M103 "unknown field" error that currently blocks execution of any release-blocking plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Schema recognition

- [x] E-01 In `agent_workflows/ipd_schema.py`, add a module-level constant `META_BLOCKS_RELEASE = "Blocks-Release"` next to `META_SCOPE_PATHS` (~line 152), and append it to the `META_RECOGNIZED` frozenset union tuple (~line 162), mirroring the existing optional single-valued field `META_SCOPE_PATHS`. Do NOT add it to `META_REQUIRED` (it is optional). Confirm `_META_LINE_RE` already accepts the hyphenated field name (it does; no regex change).
  - Depends on: none
  - Expected outcome: `parse_metadata_block` no longer records `Blocks-Release` as an "unknown field", so `aw ipd lint` stops emitting IPD-M103 for a plan carrying it.
  - Execution state: performed

### Task group 2: Regression test

- [x] E-02 In `tests/test_ipd_schema.py`, add a regression test that (a) asserts `S.META_BLOCKS_RELEASE in S.META_RECOGNIZED` (mirroring the existing `META_SCOPE_PATHS` assertion at ~line 477), and (b) parses a minimal IPD metadata block carrying `- Blocks-Release: next` and asserts NO `MetaError`/"unknown field" is produced for that line. This guards against re-introducing IPD-M103.
  - Depends on: E-01
  - Expected outcome: the test fails on the pre-fix code (documenting the bug) and passes on the fixed code.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Project: Agent Workflows toolkit (Python 3.10+). Tests live in a flat `tests/` directory named `test_<area>.py`; run with `python3 -m pytest tests/`.
- Optional IPD metadata fields are declared as module constants and unioned into `META_RECOGNIZED` (canonical model: `META_SCOPE_PATHS` at `ipd_schema.py:152`). Required fields live in `META_REQUIRED` and MUST NOT include optional fields.
- IPD-M103 ("unknown field") is `C_META_UNKNOWN` in `ipd_lint.py:48`; it maps from a `MetaError(field, "unknown field")` produced in `ipd_schema.parse_metadata_block` (~`ipd_schema.py:208-209`).
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit maintainer | `META_RECOGNIZED` (`ipd_schema.py:158-163`) omits `Blocks-Release`; any IPD carrying it fails lint as IPD-M103, contradicting AGENTS.md which says a plan may carry the field. |
| F-02 | Med | QA | No regression test asserts an IPD with `Blocks-Release` lints clean, so the field could silently regress to "unknown field" again. |

## Proposed changes (ordered, validatable)

1. Add `META_BLOCKS_RELEASE = "Blocks-Release"` and include it in `META_RECOGNIZED` in `agent_workflows/ipd_schema.py`.
2. Add a regression test in `tests/test_ipd_schema.py` asserting recognition and clean parse of `- Blocks-Release: next`.

## Deferred / out of scope (with reason)

- Value validation (dangling-reference check: does `next`/id6 resolve to a real release record) is DEFERRED to child 03 (aw check), which owns cross-artifact reference validation. This child only makes the field RECOGNIZED so lint passes; recognition and validation are separate surfaces.
- The `aw ipd set --blocks-release` setter is child 02.

## Scope check

- Over-scope: none. Two files only.
- Under-scope: none. Recognition + regression guard is the complete schema-surface deliverable; validation and setter are separate children by design.

## Required tests / validation

- `python3 -m pytest tests/test_ipd_schema.py` passes, including the new regression test.
- Manual: add `- Blocks-Release: next` to a scratch copy of an approved IPD and run `aw ipd lint <file>`; confirm no IPD-M103 and overall CONFORMING.
- `pre-commit run --files agent_workflows/ipd_schema.py tests/test_ipd_schema.py`.

## Spec / documentation sync

- The IPD spec (`.aw/records/specs/20260726-1340-01-ipd-spec.spec.md:21`) enumerates the REQUIRED and CONDITIONAL metadata fields (`Date`, `Kind`, `Concern`, `Scope`, `Status`, `Author`, `Set`/`Order`, `Approval`, `Highest E allocated`, the Quarantine trio) but it does NOT enumerate the optional single-valued field set: it already OMITS the sibling optional field `Scope-Paths`. So the spec's list is not the authoritative optional-field enumeration (the code's `META_RECOGNIZED` is), and by the established pattern an optional field like `Blocks-Release` does NOT belong in that spec line. Treat spec sync as N/A here (matching how `Scope-Paths` was handled). Do NOT add `Blocks-Release` to spec line 21; if a future decision wants optional fields enumerated in the spec, that is a separate spec edit covering `Scope-Paths` and `Blocks-Release` together, out of scope for this child.

## Open questions

### OQ-01: Should the schema also assert single-valued shape (reject `- Blocks-Release: a, b`)?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED (non-blocking). Recognition alone fixes the lint gate. Shape/semantic validation (single value, resolvable target) belongs to the `aw check` validation surface in child 03, consistent with how backlog/specs validate the field. Recognizing the field does not require asserting its value shape at the schema layer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted `aw ipd lint` output on an IPD carrying `- Blocks-Release: next` showing CONFORMING (no IPD-M103); and a grep/snippet showing `META_BLOCKS_RELEASE` present in `META_RECOGNIZED`.
  - Observed evidence: (run-20260825T035151Z-1236581, commit 7ecfb0a) Source: `ipd_schema.py` now defines `META_BLOCKS_RELEASE = "Blocks-Release"` and unions it into `META_RECOGNIZED` (`+ (META_WATERMARK, META_APPROVAL, META_SCOPE_PATHS, META_BLOCKS_RELEASE)`). Real `aw ipd lint` demonstration: a copy of the conforming fixture `tests/fixtures/conforming-orchestrator.md` lints `disposition: conforming` both before and AFTER inserting `- Blocks-Release: next` after its `- Id:` line (previously the inserted line would have produced IPD-M103); and a grep confirms no `unknown field` for `Blocks-Release`. See DECISION 07-si3mmt-D1 (the plan arrived pre-marked before the code existed; this evidence is the real re-verified run).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest tests/test_ipd_schema.py` output showing the new regression test passing.
  - Observed evidence: (run-20260825T035151Z-1236581, commit 7ecfb0a) `python3 -m pytest tests/test_ipd_schema.py` -> `59 passed`, including the new `BlocksReleaseSchemaTests`: `test_blocks_release_is_recognized_but_not_required`, `test_blocks_release_line_parses_without_unknown_field_error`, `test_absent_blocks_release_is_not_a_metadata_error`, `test_present_blocks_release_is_not_a_metadata_error` (all ok). Whole suite `python3 -m pytest tests/` -> 2145 passed, 1 skipped. `pre-commit run --files agent_workflows/ipd_schema.py tests/test_ipd_schema.py` -> all hooks Passed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one small, cohesive concern (make `Blocks-Release` a recognized IPD field) plus its regression guard, confined to the schema module and its test.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and deferred to child 03. No blocking open question remains.
2. Scope fence: touch ONLY `agent_workflows/ipd_schema.py` and `tests/test_ipd_schema.py`. Do NOT touch `ipd_lint.py` (recognition alone suppresses IPD-M103; no lint-code change is needed). If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest tests/test_ipd_schema.py` and `aw ipd lint <file>`); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
