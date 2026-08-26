# IPD: From-Backlog link field: schema recognition on IPDs and backlog, aw ipd set --from-backlog setter, and dangling-reference check

- Date: 2026-08-25
- Kind: child
- Concern: The link between a backlog item and the IPD/IPD set that graduated from it is currently only ever recorded as informal prose (Concern text or a history line). Nothing machine-readable ties a plan back to the backlog item it satisfies, so the `bklggrad` close-legitimacy predicate (child 02) has no deterministic signal to confirm "a blocking plan inherited this item's release gate". Meanwhile `Blocks-Release` already demonstrates the exact recognized-but-optional field pattern this needs (ipd_schema.py:163 META_BLOCKS_RELEASE; releases.set_blocks_release_line; releases.check_blocks_release dangling scan). This child adds a parallel `From-Backlog` link field so the graduation relationship is first-class and checkable.
- Scope: Add a `From-Backlog: <id6>` metadata field, single-valued, recognized-but-OPTIONAL, that may appear on an IPD (and is tolerated on a backlog item for symmetry, though its primary home is the plan). (1) Schema: add `META_FROM_BACKLOG = "From-Backlog"` to `ipd_schema.META_RECOGNIZED` (NOT in META_REQUIRED, mirroring META_BLOCKS_RELEASE/META_SCOPE_PATHS) so an IPD carrying it lints clean (no IPD-M103). (2) Primitive + setter: add `releases`-style `set_from_backlog_line(text, value)` (or a sibling helper module) that idempotently writes/clears the line, and wire `aw ipd set --from-backlog <id6|->` in cli.py + status_set.py using the SAME hoisted-write pattern as `--blocks-release` (status_set.py:449-461), so it persists on a no-op transition too. (3) Dangling check: add a `check.from-backlog-dangling` rule (in releases.py or check_engine.py, folded into the cross-tree `aw check` sweep like check_blocks_release) that flags a `From-Backlog` value that does not resolve to an existing backlog item id6. Value validation lives in the check surface, not the schema layer (same split as Blocks-Release). This child delivers ONLY the field, setter, and dangling check; the close-legitimacy predicate that CONSUMES the link is child 02.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/backlog.py, tests/, AGENTS.md
- Status: executed
- Set: bklggrad
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ku93tn

## Workflow history
- 2026-08-26 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): From-Backlog link field, aw ipd set --from-backlog setter, and dangling check; product committed d9166fe, tests green (test_from_backlog 6 + full suite 2227), terminal transition completed post-hoc after clean-tree restored [Scope reconciliation - in-scope-unmodified AGENTS.md: landed in d9166fe; in-scope-unmodified agent_workflows/backlog.py: landed in d9166fe; in-scope-unmodified agent_workflows/check_engine.py: landed in d9166fe; in-scope-unmodified agent_workflows/cli.py: landed in d9166fe; in-scope-unmodified agent_workflows/ipd_schema.py: landed in d9166fe; in-scope-unmodified agent_workflows/releases.py: landed in d9166fe; in-scope-unmodified agent_workflows/status_set.py: landed in d9166fe; in-scope-unmodified tests/: landed in d9166fe]
- 2026-08-26 approved (aw set): status set to approved
- 2026-08-25 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (gate contract) FIXED, PR-002 (AGENTS.md Scope-Paths) FIXED, PR-003 (status) FIXED
- 2026-08-25 reviewed (aw set): plan-review: hardened (added AGENTS.md to Scope-Paths + full execution-contract gate)

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a machine-readable `From-Backlog: <id6>` link field (recognized-but-optional on IPDs), an `aw ipd set --from-backlog` setter, and a dangling-reference check, so the backlog->plan graduation relationship is first-class and deterministically checkable by the child-02 predicate. Mirrors the existing `Blocks-Release` field in every respect.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema recognition

- [x] E-02 Add `META_FROM_BACKLOG = "From-Backlog"` to `agent_workflows/ipd_schema.py` and include it in `META_RECOGNIZED` (alongside `META_BLOCKS_RELEASE`/`META_SCOPE_PATHS`), NOT in `META_REQUIRED`, with a doc comment matching the Blocks-Release precedent (recognition only stops IPD-M103; value validation lives in `aw check`).
  - Depends on: none
  - Expected outcome: an IPD carrying `- From-Backlog: <id6>` lints clean (no IPD-M103 "unknown field") at every phase.
  - Execution state: performed

### Task group 2: write primitive + setter

- [x] E-03 Add a `set_from_backlog_line(text, value)` primitive (in `agent_workflows/releases.py` next to `set_blocks_release_line`, or a small sibling helper) that idempotently inserts/replaces/removes the `- From-Backlog:` line (value `-`/None clears), anchored after `- Status:`/`- Id:` exactly like the Blocks-Release primitive.
  - Depends on: none
  - Expected outcome: `set_from_backlog_line` round-trips (set, overwrite, clear) leaving other metadata structure unchanged.
  - Execution state: performed
- [x] E-04 Wire `aw ipd set --from-backlog <id6|->` in `agent_workflows/cli.py` (new arg on the `ipd set` parser, `dest="from_backlog"`) and apply it in `agent_workflows/status_set.py` using the SAME hoisted, status-branch-independent write pattern as `--blocks-release` (status_set.py:449-461), so it persists even on a no-op (same-status) transition.
  - Depends on: E-03
  - Expected outcome: `aw ipd set <status> <plan> --from-backlog 3gr7fk` writes the field and persists on a same-status call; `--from-backlog -` clears it.
  - Execution state: performed

### Task group 3: dangling-reference check

- [x] E-05 Add a `check.from-backlog-dangling` rule (a `check_from_backlog` scan in `releases.py` or `check_engine.py`, folded into the cross-tree `aw check` sweep the same way `check_blocks_release` is at check_engine.py:604) that flags any `From-Backlog: <id6>` that does not resolve to an existing backlog item id6.
  - Depends on: E-02
  - Expected outcome: `aw check` reports `check.from-backlog-dangling` for a plan whose `From-Backlog` names a nonexistent backlog id6, and is clean when it resolves.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `Blocks-Release` is the exact precedent to mirror: schema recognition (ipd_schema.py:163-169), idempotent write primitive (releases.set_blocks_release_line:93), hoisted status-branch-independent setter write (status_set.py:449-461, the 61qk4a fix), and a dangling cross-tree check folded into `aw check` (releases.check_blocks_release:137, wired at check_engine.py:604).
- Recognized-but-optional fields must be added to `META_RECOGNIZED` but NOT `META_REQUIRED`, or every existing pending plan fails the always-on author metadata check (the grandfather guarantee).

## Findings

The graduation link has no machine-readable representation today; child 02's predicate requires one to deterministically confirm a handoff. `From-Backlog` is the minimal addition and has a complete, tested precedent in `Blocks-Release`.

## Proposed changes (ordered, validatable)

1. `ipd_schema.py`: recognize `From-Backlog`.
2. `releases.py`: `set_from_backlog_line` primitive + `check_from_backlog` dangling scan.
3. `cli.py` + `status_set.py`: `aw ipd set --from-backlog` (hoisted write).
4. `check_engine.py`: fold `check_from_backlog` into the cross-tree sweep.
5. `tests/`: schema-accepts + lint-clean, set/clear/no-op-persist, dangling flagged / resolving clean.

## Deferred / out of scope (with reason)

- The close-legitimacy predicate and `aw backlog set done` gate that CONSUME this link: child 02.
- The pre-commit hook: child 03.

## Scope check

- Over-scope: none.
- Under-scope: none (field + setter + dangling check are the complete deliverable for this child).

## Required tests / validation

- Schema: an IPD with `- From-Backlog: <id6>` lints CONFORMING at author/pre-execution/pre-transition phases (guards against re-introducing IPD-M103).
- Setter: set, overwrite, clear, and same-status no-op persist all work via `aw ipd set --from-backlog`.
- Check: `check.from-backlog-dangling` fires on a nonexistent target and is clean on a resolving one.

## Spec / documentation sync

- Update AGENTS.md "Release gates" (or a new note) to document `From-Backlog` alongside `Blocks-Release`, and `aw ipd set --help`.

## Open questions

### OQ-01: Should a backlog item also be allowed to carry From-Backlog, or is it plan-only?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Primary home is the plan (the plan points back at the item). Tolerating it on a backlog item is harmless symmetry but unnecessary; default to plan-only recognition unless child 02 needs the reverse pointer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-02 validates E-02
  - Required evidence: a test asserting an IPD carrying `- From-Backlog: <id6>` lints CONFORMING at author/pre-execution/pre-transition phases (no IPD-M103); paste the passing test output.
  - Observed evidence: `tests/test_from_backlog.py::FromBacklogSchemaTests` (`test_field_is_recognized` asserts `From-Backlog` in `META_RECOGNIZED` and not in `META_REQUIRED`; `test_lints_clean_with_from_backlog` writes `- From-Backlog: aaa111` onto the conforming orchestrator fixture and runs `aw ipd lint --agent`, asserting rc==0 and no `IPD-M103`). Both `ok` in `python -m unittest tests.test_from_backlog -v` (Ran 6 tests ... OK). Live: `aw ipd lint --agent <this plan>` -> `{"outcome":"clean","exit":0,...}`. Schema edit `agent_workflows/ipd_schema.py`: `META_FROM_BACKLOG = "From-Backlog"` appended to `META_RECOGNIZED` (not `META_REQUIRED`). Product commit d9166fe.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: a unit test that `set_from_backlog_line` sets, overwrites, and clears the line idempotently without disturbing other metadata; paste output.
  - Observed evidence: `tests/test_from_backlog.py::FromBacklogPrimitiveTests::test_set_overwrite_clear_round_trip` (`ok`): sets (anchored after `- Status:`), overwrites (asserts exactly one `From-Backlog` line remains), clears with `-` and with `None`, asserts `- Status: open` untouched. Part of the 6-test `OK` run. Primitive `set_from_backlog_line` in `agent_workflows/releases.py`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: a test that `aw ipd set --from-backlog <id6>` writes the field, persists on a same-status (no-op) transition, and clears with `-`; paste output.
  - Observed evidence: `tests/test_from_backlog.py::IpdSetFromBacklogE2ETests::test_write_noop_persist_and_clear` (`ok`): `aw ipd set <same-status> fix000 --from-backlog aaa111` (NO-OP same-status transition) persists the `- From-Backlog: aaa111` line, the plan still lints clean (no IPD-M103), then `--from-backlog -` clears it. Write hoisted in `agent_workflows/status_set.py` OUTSIDE the specs-only guard via the shared `releases.set_from_backlog_line` primitive; arg wired in `agent_workflows/cli.py`. Part of the 6-test `OK` run.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: a test that `aw check` fires `check.from-backlog-dangling` on a nonexistent target and is clean on a resolving one; paste output.
  - Observed evidence: `tests/test_from_backlog.py::FromBacklogDanglingCheckTests` (`test_dangling_flagged` -> plan with `From-Backlog: nosuchid` yields a `check.from-backlog-dangling` Drift naming the plan; `test_resolving_clean` -> with matching backlog item `aaa111` present, zero such Drift). Both `ok`. `check_from_backlog` folded into the cross-tree sweep in `agent_workflows/check_engine.py` next to `check_blocks_release`. Live: `aw check all --agent` reported 65 pre-existing findings, ZERO of rule `check.from-backlog-dangling` (no false positives).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Child 01 of the `bklggrad` Set; it has no cross-plan prerequisite (the orchestrator table lists `Depends on: none`) and delivers only the `From-Backlog` field, setter, and dangling check. Children 02 and 03 CONSUME this; do not implement their predicate/hook here.

Execution contract (binds any agent that executes this plan):

1. Open questions: OQ-01 is `Blocking: no` (plan-only recognition is the default; the reverse pointer is only added if child 02 needs it). No blocking question remains. If OQ-01 becomes blocking during execution, STOP and report.
2. Scope fence: touch ONLY the paths in `Scope-Paths` (the six `agent_workflows/*.py` modules, `tests/`, and `AGENTS.md` for the "Release gates" doc note named in Spec / documentation sync) plus this plan's own file. Do NOT expand scope; if it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when you report tests passed, paste the ACTUAL runner output for each V-item's test (schema-lint-clean, setter round-trip, no-op persist, dangling fires/clean). Never claim success you did not run.
4. Commits: commit ONLY this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: perform the terminal transition via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` (runs the pre/pre-transition/post-transition gates, verifies changed paths stayed within `Scope-Paths`, appends the attributed history line, sets `Status: executed`, `git mv`s to `.aw/records/plans/executed/`, and makes the path-scoped lifecycle commit). Do NOT hand-edit the terminal transition.

This review and gate are NOT approval: human sign-off (`Status: approved`) is a separate, required step before execution.
