# IPD: aw ipd set --blocks-release and shared setter fix for plans and backlog

- Date: 2026-08-24
- Kind: child
- Concern: `aw ipd set` has no `--blocks-release` flag, so even once the schema recognizes the field a plan release blocker can only be set by hand-editing front matter. Worse, the underlying write path is broken: `aw backlog set open <id6> --blocks-release next` (status supplied positionally) routes through `status_set.apply_status_change`, whose only blocks_release write is guarded by `if rec.record_type == "specs"` (`status_set.py:416,449-455`), so for backlog (and plans) the `--blocks-release` value is silently dropped. This is bug 61qk4a. Fixing the setter for plans WITHOUT fixing the shared path would duplicate a broken code path.
- Scope: Add `--blocks-release <release-id6|next|->` to `aw ipd set` with the SAME semantics as the backlog/specs setters (resolve `next` to the single planned release, write/update the `- Blocks-Release:` front-matter field via the shared `releases.set_blocks_release_line` primitive, clear with `-`, append a workflow-history line), and fix `status_set.apply_status_change` so the blocks_release mutation applies to plans AND backlog (not only specs), root-causing bug 61qk4a. Child 02 of the vwios6ipd Set; depends on schema child 01.
- Scope-Paths: agent_workflows/cli.py, agent_workflows/status_set.py, agent_workflows/backlog.py, agent_workflows/releases.py, tests/test_status_set.py, tests/test_blocks_release.py
- Status: reviewed
- Set: vwios6ipd
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: efnn74

## Workflow history
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (precise hoist boundary+entrypoint note), PR-002 (specs anti-regression V-item)
- 2026-08-24 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 02 of vwios6ipd Set (setter + shared-path/61qk4a fix).

## Goal

Give `aw ipd set` a `--blocks-release` flag with backlog/specs parity, and fix the single shared setter path so plans and backlog both persist and clear the field, resolving bug 61qk4a in the same change rather than adding a second broken copy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fix the shared setter path (root cause, 61qk4a)

- [ ] E-01 In `agent_workflows/status_set.py`, hoist ONLY the blocks_release mutation block (`status_set.py:449-455`) OUT of the `if rec.record_type == "specs":` guard (`status_set.py:416`) so `apply_status_change` applies `--blocks-release` for `plans` and `backlog` records too, always going through the shared `releases.set_blocks_release_line(text, value)` primitive (`releases.py:93-108`). LEAVE the specs-only gate-field handling (`status_set.py:417-447`, the Gate-Kind/Gate-Ref/Gate-Summary logic) exactly where it is, inside the specs guard - do NOT move it. Preserve existing spec behavior (a spec's blocks_release still writes as before, now via the shared post-guard step). Ensure the write happens even on a same-status (no-op) transition, since `apply_status_change` already rewrites the file idempotently. Preserve the existing join/split idempotency (`"\n".join(new_lines)` -> `set_blocks_release_line` -> `.splitlines()`) so the hoisted step does not alter trailing metadata structure for plans/backlog layouts.
  - Depends on: none
  - Expected outcome: `aw backlog set open <id6> --blocks-release next` (positional status form) persists the field; bug 61qk4a is fixed at the shared path; spec setter behavior is unchanged; the two backlog entrypoints stay distinct (positional-status -> `status_set.apply_status_change`; `--status` form -> `backlog.run_set` at `backlog.py:467`), each reaching the same shared primitive, with no double-write (the dispatch at `cli.py:6900-6916` makes them mutually exclusive).
  - Execution state: pending

### Task group 2: Add the aw ipd set --blocks-release flag

- [ ] E-02 In `agent_workflows/cli.py`, add a `--blocks-release <release-id6|next|->` argument to the `aw ipd set` subparser (near `cli.py:921`) and thread its value through to `status_set.run_set_command(..., scoped_type="plans", ...)` (dispatched at `cli.py:6792-6800`), mirroring how `aw set`/`aw backlog set`/`aw specs set` accept and pass the flag. When provided, the value flows into `apply_status_change` and is written via the shared primitive fixed in E-01; a `blocks-release-set`/`blocks-release-clear` workflow-history line is appended consistent with the backlog/specs setters.
  - Depends on: E-01
  - Expected outcome: `aw ipd set --blocks-release next <plan-id6>` writes `- Blocks-Release: next`; `--blocks-release -` clears it; a workflow-history line is appended.
  - Execution state: pending

### Task group 3: Tests for the setter and the 61qk4a regression

- [ ] E-03 In `tests/test_status_set.py`, add tests that `status_set.run_set_command(["open", <id6>], scoped_type="backlog", ... blocks_release="next")` PERSISTS the field even when status is unchanged (61qk4a regression), and that the same for `scoped_type="plans"` writes/clears the field. Assert the workflow-history line is appended. Include a specs anti-regression case: a `scoped_type="specs"` set with `blocks_release="next"` still writes the field exactly as before the hoist (proving widening the write path did not regress the specs surface it was originally scoped to).
  - Depends on: E-01, E-02
  - Expected outcome: a test that fails on pre-fix code (field dropped for backlog/plans) and passes after; explicit 61qk4a guard; specs behavior demonstrably unchanged.
  - Execution state: pending

- [ ] E-04 In `tests/test_blocks_release.py`, add an end-to-end test invoking `aw ipd set --blocks-release next <plan-id6>` on a fixture IPD and asserting the front-matter field is present and the plan still lints CONFORMING (relies on child 01 schema fix), plus a `--blocks-release -` clear assertion and a `next`-resolution assertion.
  - Depends on: E-01, E-02
  - Expected outcome: end-to-end proof the ipd setter writes, clears, and resolves `next`, and the result lints clean.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The shared low-level primitives are `releases.set_blocks_release_line` (idempotent write/clear, `releases.py:93-108`) and `releases.resolve_release` (`next` -> single planned release, `releases.py:111-131`). All setter call sites MUST use these rather than duplicate logic.
- `aw ipd set` dispatches to `status_set.run_set_command(..., scoped_type="plans")` (`cli.py:6792-6800`); `apply_status_change` (`status_set.py:348`) performs the per-record mutation and already rewrites the file idempotently on a same-status transition.
- The backlog `--status` form (`backlog.run_set`, `backlog.py:464-475`) DOES handle blocks_release, but the positional-status form routes through `status_set` and is the broken path (61qk4a).
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit maintainer | `apply_status_change` only writes blocks_release for `record_type == "specs"` (`status_set.py:416,449-455`); backlog/plans silently drop `--blocks-release`. Root cause of 61qk4a. |
| F-02 | High | Toolkit user | `aw ipd set` has no `--blocks-release` flag, so a plan release blocker can only be hand-edited even after the schema recognizes the field. |
| F-03 | Med | Maintainer | Blocks-release write logic is duplicated across `backlog.run_set`, `specs.run_set`, and `status_set.apply_status_change`; fixing only the ipd path would add a fourth copy. Consolidate on the shared primitive. |

## Proposed changes (ordered, validatable)

1. Lift the blocks_release mutation in `apply_status_change` out of the specs-only guard so plans and backlog persist it via the shared primitive (fixes 61qk4a).
2. Add `--blocks-release` to the `aw ipd set` subparser and thread it into `run_set_command`.
3. Add a 61qk4a regression test (backlog positional-status persist) plus plans write/clear tests in `test_status_set.py`.
4. Add an end-to-end `aw ipd set --blocks-release` test in `test_blocks_release.py` (write/clear/resolve-next, lints clean).

## Deferred / out of scope (with reason)

- Dangling-reference validation of the written value (does `next`/id6 resolve to a live release) is owned by child 03 (`aw check`). This child writes the value using the shared primitive; it does not add the plan-side `check` path.
- The schema recognition of the field is child 01 (a hard dependency of E-04's lint-clean assertion).

## Scope check

- Over-scope: none. Confined to the setter surfaces and the shared write path.
- Under-scope: none. Covers the ipd setter flag, the shared-path root cause (61qk4a), and regression coverage for both.

## Required tests / validation

- `python3 -m pytest tests/test_status_set.py tests/test_blocks_release.py` green, including the new 61qk4a regression and ipd-setter tests.
- Manual: `aw ipd set --blocks-release next <plan-id6>` then `aw ipd lint <plan>` CONFORMING; `aw ipd set --blocks-release - <plan-id6>` removes the line; `aw backlog set open <backlog-id6> --blocks-release next` persists the field.
- `pre-commit run --files agent_workflows/cli.py agent_workflows/status_set.py agent_workflows/backlog.py agent_workflows/releases.py tests/test_status_set.py tests/test_blocks_release.py`.

## Spec / documentation sync

- AGENTS.md "Release gates" already documents `aw ipd set ... --blocks-release next` as the intended setter; once this lands the documentation becomes true. Verify no separate help/spec text needs an added flag line; update the `aw ipd set` help string if it enumerates flags.

## Open questions

### OQ-01: Should `next` be resolved to a concrete id6 at write time, or stored as the literal `next`?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to match existing backlog/specs behavior exactly. Today the setters store the raw value (`next` stays `next`) and resolution is deferred to the `check` path (`resolve_release` is not called before writing). This child MUST match that behavior for parity; do not diverge. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted test output showing a backlog record's `Blocks-Release` persists through `status_set.run_set_command` with unchanged status (61qk4a); before/after front-matter snippet.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted terminal output of `aw ipd set --blocks-release next <plan-id6>` and `aw ipd set --blocks-release - <plan-id6>` showing the field written then cleared, and the appended workflow-history line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_status_set.py` output with the new backlog-persist (61qk4a), plans write/clear, AND specs-unchanged anti-regression tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest tests/test_blocks_release.py` output with the ipd-setter end-to-end (write/clear/resolve-next + lint-clean) test passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (the blocks-release setter for plans) whose correct implementation requires fixing the shared write path it depends on; 61qk4a is folded in because it is literally the same code path, not a separate change.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and resolved as "match existing backlog/specs behavior (store literal `next`)". No blocking open question remains.
2. Scope fence: touch ONLY the files in Scope-Paths. Route all blocks-release writes through `releases.set_blocks_release_line`; do NOT add a new duplicate write path. Do NOT change the schema (child 01) or the check engine (child 03). If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest ...`, the `aw ipd set`/`aw backlog set` terminal output); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
