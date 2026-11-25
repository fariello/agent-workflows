# IPD: Migrate surviving Workflow history section readers onto artifact_meta

- Date: 2026-11-24
- Kind: child
- Concern: Spec `4sd62s` C5 and AC-1 part (1) require a single metadata reader and writer (`agent_workflows/artifact_meta.py`) with no surviving `Workflow history` section parsers or heading regexes outside `artifact_meta.py` and `agent_workflows/migrations/m0001_*.py`. Plan `9o83cr` E-14 audited the codebase after the five split deletion parts (`q6epwc`, `snin8q`, `k6jd6l`, `e8420v`, `0xsx2n`) and found surviving `Workflow history` section readers across `attention.py`, `backlog.py`, `releases.py`, `specs.py`, `ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, and `check_engine.py` (tracked in backlog items `rzxd1x` and `q4gwp9`). Because `9o83cr` is read-only on production code and must verify zero survivors in `V-14`, this focused plan runs ahead of `9o83cr` (replacing E-01 of superseded monolith `rgva3w`).
- Scope: Migrate all surviving `Workflow history` section readers and `HISTORY_RECORD_RE` callers onto `artifact_meta.history_records` / `artifact_meta.history` across `attention.py`, `backlog.py`, `releases.py`, `specs.py`, `ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, `check_engine.py`, and `record_history.py`, with behavioral tests. Excludes prompt comment helpers (`t3t7za`), specs/backlog `^-` regexes (`fkvrc7`), `Scope-Paths` / widened readers (`75jciz`), and the `9o83cr` final audit.
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/attention.py, agent_workflows/backlog.py, agent_workflows/releases.py, agent_workflows/specs.py, agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, agent_workflows/check_engine.py, agent_workflows/record_history.py, tests/test_history_order.py, .aw/records/plans/pending/20261124-metastore-301-wgn3bl-migrate-surviving-workflow-history-section-readers-onto-arti.ipd.md
- Item-Dependencies: executed:0xsx2n, executed:e8420v, executed:k6jd6l, executed:q6epwc, executed:snin8q
- Status: to-review
- From-Spec: 4sd62s
- From-Backlog: rzxd1x
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: metastore
- Order: 301
- Highest E allocated: 4
- Id: wgn3bl
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 301 child plan (split from superseded `rgva3w` per maintainer decision 2026-11-25, ahead of `9o83cr`) covering `rzxd1x` and `q4gwp9`.

## Goal

Remove every surviving `Workflow history` section parser and local heading regex outside `agent_workflows/artifact_meta.py` and `agent_workflows/migrations/m0001_*.py`, routing all callers onto `artifact_meta.history_records` / `artifact_meta.history` ahead of `9o83cr`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Core record and board history readers (`rzxd1x`)

- [ ] E-01 Replace `Workflow history` section parsers in `agent_workflows/attention.py` (`_history_section_lines`), `agent_workflows/backlog.py` (`_WORKFLOW_HISTORY_HEADING_RE`), `agent_workflows/releases.py` (`_history_lines`), and `agent_workflows/specs.py` (`_history_lines`) with calls to `artifact_meta.history_records` or `artifact_meta.history`, adding any minimal read helper required in `agent_workflows/artifact_meta.py` and removing the local heading regexes.
  - Depends on: none
  - Expected outcome: zero local `Workflow history` section parsers remain in `attention.py`, `backlog.py`, `releases.py`, and `specs.py`, and existing attention, backlog, releases, and specs tests pass.
  - Execution state: pending

### Task group 2: Lifecycle, lint, and citation history readers (`q4gwp9`, `rzxd1x`)

- [ ] E-02 Replace `ipd_lifecycle._plan_status_event_groups`, `ipd_lint.parse` history collection (`ipd_schema.H_WORKFLOW_HISTORY`), `check_engine.check_spec_test_citations_for_text` heading slicing, and any remaining `HISTORY_RECORD_RE` callers in `record_history.py` / `ipd_lifecycle.py` / `specs.py` with `artifact_meta` history readers.
  - Depends on: E-01
  - Expected outcome: zero local `Workflow history` section parsers or legacy `HISTORY_RECORD_RE` dependencies remain in `ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, `check_engine.py`, and `record_history.py`.
  - Execution state: pending

### Task group 3: Behavioral regression tests and audit verification

- [ ] E-03 Add or update behavioral tests in `tests/test_history_order.py` exercising `Workflow history` reading through `attention`, `backlog`, `releases`, `specs`, `ipd_lifecycle`, and `check_engine` (asserting observable outputs and exit codes; zero code-pinning source reads).
  - Depends on: E-02
  - Expected outcome: behavioral tests verify history ordering, lifecycle transition groups, and spec citation checks through `artifact_meta`.
  - Execution state: pending

- [ ] E-04 Run targeted pytest suites across the affected modules, `mypy` on all modified source files, `rg` confirming zero surviving `Workflow history` section readers in the owned modules, and `aw sanitize`.
  - Depends on: E-03
  - Expected outcome: all targeted tests pass, `mypy` reports zero errors on modified modules, `rg` reports zero surviving section-reader hits in the owned files, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `4sd62s` C5 and AC-1 part (1) require `agent_workflows/artifact_meta.py` to be the sole metadata and history reader.
- Tests must test observable behavior only (no `inspect`, `ast`, regex, or source-reading assertions).
- Commit path-scoped via `aw commit wgn3bl -- <paths>` in an isolated worktree.

## Findings

Tracked across open backlog items `rzxd1x` and `q4gwp9`:
- `attention._history_section_lines`, `backlog._WORKFLOW_HISTORY_HEADING_RE`, `releases._history_lines`, `specs._history_lines`.
- `ipd_lifecycle._plan_status_event_groups`, `ipd_lint.parse` (`ipd_schema.H_WORKFLOW_HISTORY`), `check_engine.check_spec_test_citations_for_text`, and remaining `record_history.py` / `ipd_lifecycle.py` `HISTORY_RECORD_RE` callers.

## Proposed changes (ordered, validatable)

1. Retarget `attention.py`, `backlog.py`, `releases.py`, and `specs.py` onto `artifact_meta` history readers (`E-01`).
2. Retarget `ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, `check_engine.py`, and `record_history.py` onto `artifact_meta` history readers (`E-02`).
3. Add behavioral regression tests in `tests/test_history_order.py` (`E-03`) and run targeted pytest, `mypy`, `rg`, and `aw sanitize` (`E-04`).

## Deferred / out of scope (with reason)

- Prompt comment helpers are owned by Order 302 (`t3t7za`).
  - Carrier: t3t7za
- Specs/backlog `^-` regexes are owned by Order 303 (`fkvrc7`).
  - Carrier: fkvrc7
- `Scope-Paths` writer and widened front-matter readers are owned by Order 304 (`75jciz`).
  - Carrier: 75jciz
- Final AC-1 zero-survivors audit is owned by `9o83cr`.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none; strictly limited to `Workflow history` section readers and their `artifact_meta` helpers.
- Under-scope: none; covers every `rzxd1x` and `q4gwp9` survivor ahead of `9o83cr`.

## Required tests / validation

- `python3 -m pytest tests/test_history_order.py tests/test_ipd_lifecycle.py tests/test_readers_attention.py tests/test_specs.py`
- `python3 -m mypy agent_workflows/artifact_meta.py agent_workflows/attention.py agent_workflows/backlog.py agent_workflows/releases.py agent_workflows/specs.py agent_workflows/ipd_lifecycle.py agent_workflows/ipd_lint.py agent_workflows/ipd_schema.py agent_workflows/check_engine.py agent_workflows/record_history.py`
- `rg -n "Workflow history" agent_workflows/attention.py agent_workflows/backlog.py agent_workflows/releases.py agent_workflows/specs.py agent_workflows/ipd_lifecycle.py agent_workflows/ipd_lint.py agent_workflows/ipd_schema.py agent_workflows/check_engine.py`
- `aw sanitize`

## Spec / documentation sync

N/A: enforces existing approved spec `4sd62s` C5 and AC-1 part (1).

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "Workflow history" agent_workflows/attention.py agent_workflows/backlog.py agent_workflows/releases.py agent_workflows/specs.py` showing zero section-parser hits, plus pytest output passing for `attention`, `backlog`, `releases`, and `specs`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "Workflow history|HISTORY_RECORD_RE" agent_workflows/ipd_lifecycle.py agent_workflows/ipd_lint.py agent_workflows/ipd_schema.py agent_workflows/check_engine.py agent_workflows/record_history.py` showing zero section-parser hits, plus pytest output passing for `ipd_lifecycle`, `ipd_lint`, and `check_engine`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_history_order.py` output with all behavioral tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste full pytest summary, `mypy` zero-error output across `artifact_meta.py`, `attention.py`, `backlog.py`, `releases.py`, `specs.py`, `ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, `check_engine.py`, and `record_history.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: All 10 source files share one narrow concern (migrating surviving `Workflow history` section readers onto `artifact_meta.history_records` / `artifact_meta.history`) and have only 4 E-items; splitting further would scatter a single shared `artifact_meta` history-reader migration.

Execute after human approval (`Status: approved`). Commit path-scoped via `aw commit wgn3bl -- <paths>`; never push.
