# IPD: Replace surviving specs and backlog front-matter regexes via artifact_meta bullet helper

- Date: 2026-11-24
- Kind: child
- Concern: Spec `4sd62s` C5 and AC-1 part (1) forbid `^-` metadata regex literals outside `agent_workflows/artifact_meta.py` and `agent_workflows/migrations/m0001_*.py`. Five surviving `^-` metadata regexes remain in `specs.py` and `backlog.py` (backlog `ebbfmn`, with a caller in `spec_citations.py`), and `artifact_meta.py` lacks a public helper listing every metadata bullet with its original key and duplicate values (backlog `vl7ybn`), which forces duplicate-bullet checks to scan lines manually. This focused plan adds the public bullet-inspection helper in `artifact_meta.py` and removes the surviving `^-` metadata regexes in `specs.py`, `backlog.py`, and `spec_citations.py` ahead of `9o83cr` (replacing E-03 of superseded `rgva3w`).
- Scope: Add a public metadata-bullet listing/duplicate-value helper in `agent_workflows/artifact_meta.py` (`vl7ybn`); replace `specs._SPEC_ID_RE`, `specs._TOP_KEY_RE`, the `^- Status:` match in `specs.run_migrate`, `specs._SPEC_ID_BULLET_RE`, and `backlog._TOP_KEY_RE` (plus any caller in `spec_citations.py` and `migrations/chain.py`) with `artifact_meta` readers (`ebbfmn`); and verify with behavioral tests.
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/specs.py, agent_workflows/backlog.py, agent_workflows/spec_citations.py, agent_workflows/migrations/chain.py, tests/test_backlog_metadata_duplicate_and_gate_summary.py, tests/test_specs.py, .aw/records/plans/pending/20261124-metastore-303-fkvrc7-replace-surviving-specs-and-backlog-front-matter-regexes-via.ipd.md
- Item-Dependencies: executed:0xsx2n, executed:e8420v, executed:k6jd6l, executed:q6epwc, executed:snin8q
- Status: to-review
- From-Spec: 4sd62s
- From-Backlog: ebbfmn
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: metastore
- Order: 303
- Highest E allocated: 4
- Id: fkvrc7
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 303 child plan (split from superseded `rgva3w` per maintainer decision 2026-11-25, ahead of `9o83cr`) covering `ebbfmn` and `vl7ybn`.

## Goal

Add a public metadata-bullet listing helper to `agent_workflows/artifact_meta.py` and eliminate all five surviving `^-` metadata regex literals in `agent_workflows/specs.py` and `agent_workflows/backlog.py` (plus callers in `spec_citations.py`) ahead of `9o83cr`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Public metadata-bullet listing helper in `artifact_meta.py` (`vl7ybn`)

- [ ] E-01 Add a public helper in `agent_workflows/artifact_meta.py` that returns every top-level metadata bullet with its original key and duplicate occurrences from artifact text, so callers inspecting duplicate keys never need local `^-` regexes or line-by-line loops over `parse_metadata_block`.
  - Depends on: none
  - Expected outcome: `artifact_meta` exposes a typed public bullet-inspection helper that preserves original key spelling and duplicate values.
  - Execution state: pending

### Task group 2: Replace `^-` metadata regexes in `specs.py`, `backlog.py`, and `spec_citations.py` (`ebbfmn`)

- [ ] E-02 Remove `specs._SPEC_ID_RE`, `specs._TOP_KEY_RE`, the `^- Status:` match in `specs.run_migrate`, `specs._SPEC_ID_BULLET_RE`, and `backlog._TOP_KEY_RE`, replacing them (and any callers in `spec_citations.py` or `migrations/chain.py`) with `artifact_meta.read_text` and the new `artifact_meta` bullet helper.
  - Depends on: E-01
  - Expected outcome: `specs.py`, `backlog.py`, and `spec_citations.py` contain zero `^-` metadata regex literals while preserving duplicate-bullet detection, spec id lookup, and `specs.run_migrate`.
  - Execution state: pending

### Task group 3: Behavioral tests and validation

- [ ] E-03 Add or update behavioral tests in `tests/test_backlog_metadata_duplicate_and_gate_summary.py` and `tests/test_specs.py` covering duplicate metadata keys, `specs.run_migrate`, and spec id lookup via `artifact_meta` (no source-reading assertions).
  - Depends on: E-02
  - Expected outcome: all duplicate-bullet, spec-id, and spec-migration behavioral tests pass.
  - Execution state: pending

- [ ] E-04 Run targeted pytest suites, `mypy` on all 5 modified source files, `rg` confirming zero `^-` metadata regex literals in `specs.py`, `backlog.py`, and `spec_citations.py`, and `aw sanitize`.
  - Depends on: E-03
  - Expected outcome: all tests pass, `mypy` reports zero errors, `rg` reports zero hits, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `4sd62s` C5 and AC-1 part (1) forbid `^-` metadata regexes outside `artifact_meta.py` and `migrations/m0001_*.py`.
- Tests must test observable behavior only (no code-pinning source inspection).
- Commit path-scoped via `aw commit fkvrc7 -- <paths>` in an isolated worktree.

## Findings

Tracked across open backlog items `ebbfmn` and `vl7ybn`:
- `specs._SPEC_ID_RE`, `specs._TOP_KEY_RE`, `specs.run_migrate` (`^- Status:`), `specs._SPEC_ID_BULLET_RE`, `backlog._TOP_KEY_RE` (plus callers in `spec_citations.py`).
- Missing public `artifact_meta` bullet-listing/duplicate-key helper (`vl7ybn`).

## Proposed changes (ordered, validatable)

1. Add the public metadata-bullet listing helper in `artifact_meta.py` (`E-01`).
2. Remove the five surviving `^-` regexes in `specs.py` and `backlog.py` and retarget `spec_citations.py` (`E-02`).
3. Add behavioral tests (`E-03`) and run pytest, `mypy`, `rg`, and `aw sanitize` (`E-04`).

## Deferred / out of scope (with reason)

- `Workflow history` section readers are owned by Order 301 (`wgn3bl`).
  - Carrier: wgn3bl
- Prompt comment helpers are owned by Order 302 (`t3t7za`).
  - Carrier: t3t7za
- `Scope-Paths` writer and widened front-matter readers are owned by Order 304 (`75jciz`).
  - Carrier: 75jciz
- Final AC-1 zero-survivors audit is owned by `9o83cr`.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none; strictly limited to `artifact_meta` bullet inspection and `specs`/`backlog`/`spec_citations` `^-` regex removal.
- Under-scope: none; covers every `ebbfmn` and `vl7ybn` item ahead of `9o83cr`.

## Required tests / validation

- `python3 -m pytest tests/test_backlog_metadata_duplicate_and_gate_summary.py tests/test_specs.py`
- `python3 -m mypy agent_workflows/artifact_meta.py agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/spec_citations.py agent_workflows/migrations/chain.py`
- `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/spec_citations.py`
- `aw sanitize`

## Spec / documentation sync

N/A: enforces existing approved spec `4sd62s` C5 and AC-1 part (1).

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste pytest output proving the new `artifact_meta` bullet-listing helper preserves original key spelling and duplicate occurrences.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/spec_citations.py` showing zero hits, plus pytest output passing for `specs`, `backlog`, and `spec_citations`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_backlog_metadata_duplicate_and_gate_summary.py tests/test_specs.py` output with all behavioral tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste full pytest summary, `mypy` zero-error output across `artifact_meta.py`, `specs.py`, `backlog.py`, `spec_citations.py`, and `migrations/chain.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after human approval (`Status: approved`). Commit path-scoped via `aw commit fkvrc7 -- <paths>`; never push.
