# IPD: Replace Scope-Paths bullet writer and widened front-matter readers via artifact_meta

- Date: 2026-11-24
- Kind: child
- Concern: Spec `4sd62s` C5 and AC-1 part (1) require a single metadata reader and writer (`agent_workflows/artifact_meta.py`). Plan `9o83cr` E-14 and `786w7r`'s widened multiline/`(?mi)` search identified one surviving metadata bullet writer (`artifact_refs._SCOPE_PATHS_LINE_RE` in `apply_scope_path_reference_rewrites`) plus surviving front-matter readers (`partition._ORCHESTRATOR_KIND_RE`, `review_basis._is_orchestrator_text`, `check_engine._TARGET_BULLET_RE` metadata branch, `check_engine._REVIEW_SUBJECT_ID_RE`, `coverage_record._FINGERPRINT_LINE_RE`, `coverage_record._CHECKED_LINE_RE`, `attention._FIELD_PATTERNS`, and `runner_shared._PROPOSAL_BULLET_RE` audit), tracked in open backlogs `avze51` and `hmtpj2`. This focused plan removes those surviving writers and readers ahead of `9o83cr` (replacing E-04 of superseded `rgva3w`).
- Scope: Rewrite `artifact_refs.plan_scope_path_reference_rewrites` / `apply_scope_path_reference_rewrites` to read and write via `artifact_meta` (deleting `_SCOPE_PATHS_LINE_RE`); retarget `partition._ORCHESTRATOR_KIND_RE`, `review_basis._is_orchestrator_text`, `check_engine._TARGET_BULLET_RE` (metadata branch), `check_engine._REVIEW_SUBJECT_ID_RE`, `coverage_record._FINGERPRINT_LINE_RE`, `coverage_record._CHECKED_LINE_RE`, and `attention._FIELD_PATTERNS` onto `artifact_meta`; audit `runner_shared._PROPOSAL_BULLET_RE` (move grammar helper into `artifact_meta` or classify explicitly if non-metadata body-prose escaping); and verify with behavioral tests.
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/artifact_refs.py, agent_workflows/partition.py, agent_workflows/review_basis.py, agent_workflows/check_engine.py, agent_workflows/coverage_record.py, agent_workflows/attention.py, agent_workflows/runner_shared.py, tests/test_partition.py, .aw/records/plans/pending/20261124-metastore-304-75jciz-replace-scope-paths-bullet-writer-and-widened-front-matter-r.ipd.md
- Item-Dependencies: executed:0xsx2n, executed:e8420v, executed:k6jd6l, executed:q6epwc, executed:snin8q
- Status: to-review
- From-Spec: 4sd62s
- From-Backlog: avze51
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: metastore
- Order: 304
- Highest E allocated: 4
- Id: 75jciz
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 304 child plan (split from superseded `rgva3w` per maintainer decision 2026-11-25, ahead of `9o83cr`) covering `avze51` and `hmtpj2`.

## Goal

Remove the surviving `Scope-Paths` bullet writer in `artifact_refs.py` and every widened-search front-matter metadata reader across `partition.py`, `review_basis.py`, `check_engine.py`, `coverage_record.py`, `attention.py`, and `runner_shared.py` ahead of `9o83cr`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: `Scope-Paths` bullet writer (`avze51`)

- [ ] E-01 Rewrite `artifact_refs.plan_scope_path_reference_rewrites` and `apply_scope_path_reference_rewrites` to read `Scope-Paths` via `artifact_meta` and write updated `Scope-Paths` via `artifact_meta.append` (or the canonical `artifact_meta` writer), deleting `artifact_refs._SCOPE_PATHS_LINE_RE`.
  - Depends on: none
  - Expected outcome: `artifact_refs.py` performs zero direct `Scope-Paths` bullet regex rewrites, and citation-rewrite tests pass.
  - Execution state: pending

### Task group 2: Widened front-matter metadata readers (`avze51`, `hmtpj2`)

- [ ] E-02 Replace `partition._ORCHESTRATOR_KIND_RE`, `review_basis._is_orchestrator_text`, `check_engine._TARGET_BULLET_RE` (metadata `Scope-Paths` branch), `check_engine._REVIEW_SUBJECT_ID_RE`, `coverage_record._FINGERPRINT_LINE_RE`, `coverage_record._CHECKED_LINE_RE`, and `attention._FIELD_PATTERNS` metadata reads with `artifact_meta` readers, and audit `runner_shared._PROPOSAL_BULLET_RE` (moving metadata grammar into `artifact_meta` or documenting non-metadata body-prose escaping explicitly).
  - Depends on: E-01
  - Expected outcome: zero unexcluded front-matter metadata regex readers survive in `partition.py`, `review_basis.py`, `check_engine.py`, `coverage_record.py`, `attention.py`, and `runner_shared.py`.
  - Execution state: pending

### Task group 3: Behavioral tests and widened-search validation

- [ ] E-03 Add or update behavioral tests in `tests/test_partition.py` (and affected citation-rewrite/coverage/attention tests) verifying `Scope-Paths` rewriting, orchestrator detection, coverage fingerprint checks, and attention field extraction through `artifact_meta` (zero source-reading assertions).
  - Depends on: E-02
  - Expected outcome: behavioral regression tests pass under `python3 -m pytest`.
  - Execution state: pending

- [ ] E-04 Run targeted pytest suites, `mypy` on all 8 modified source files, widened multiline/flag `rg -U` search over the 7 owned non-`artifact_meta` modules, and `aw sanitize`.
  - Depends on: E-03
  - Expected outcome: zero unexcluded metadata parser/writer hits remain in the owned files, pytest passes, `mypy` reports zero errors, and `aw sanitize` reports clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `4sd62s` C5 and AC-1 part (1) require `artifact_meta.py` to be the sole metadata reader and writer.
- Tests must test observable behavior only (no code-pinning assertions).
- Commit path-scoped via `aw commit 75jciz -- <paths>` in an isolated worktree.

## Findings

Tracked across open backlog items `avze51` and `hmtpj2`:
- `artifact_refs._SCOPE_PATHS_LINE_RE` (`apply_scope_path_reference_rewrites`).
- `partition._ORCHESTRATOR_KIND_RE`, `review_basis._is_orchestrator_text`, `check_engine._TARGET_BULLET_RE` (metadata branch), `check_engine._REVIEW_SUBJECT_ID_RE`, `coverage_record._FINGERPRINT_LINE_RE`, `coverage_record._CHECKED_LINE_RE`, `attention._FIELD_PATTERNS`, and `runner_shared._PROPOSAL_BULLET_RE`.

## Proposed changes (ordered, validatable)

1. Route `artifact_refs` `Scope-Paths` rewrites through `artifact_meta` (`E-01`).
2. Replace widened front-matter readers across `partition.py`, `review_basis.py`, `check_engine.py`, `coverage_record.py`, `attention.py`, and audit `runner_shared._PROPOSAL_BULLET_RE` (`E-02`).
3. Add behavioral regression tests (`E-03`) and run pytest, `mypy`, widened `rg -U`, and `aw sanitize` (`E-04`).

## Deferred / out of scope (with reason)

- `Workflow history` section readers are owned by Order 301 (`wgn3bl`).
  - Carrier: wgn3bl
- Prompt comment helpers are owned by Order 302 (`t3t7za`).
  - Carrier: t3t7za
- Specs/backlog `^-` regexes are owned by Order 303 (`fkvrc7`).
  - Carrier: fkvrc7
- Final AC-1 zero-survivors audit is owned by `9o83cr`.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none; strictly limited to `Scope-Paths` writer and widened front-matter metadata readers.
- Under-scope: none; covers every `avze51` and `hmtpj2` survivor ahead of `9o83cr`.

## Required tests / validation

- `python3 -m pytest tests/test_partition.py tests/test_readers_attention.py tests/test_orchestrator_readiness.py` plus citation-rewrite tests.
- `python3 -m mypy agent_workflows/artifact_meta.py agent_workflows/artifact_refs.py agent_workflows/partition.py agent_workflows/review_basis.py agent_workflows/check_engine.py agent_workflows/coverage_record.py agent_workflows/attention.py agent_workflows/runner_shared.py`
- Widened `rg -U` search over `artifact_refs.py`, `partition.py`, `review_basis.py`, `check_engine.py`, `coverage_record.py`, `attention.py`, and `runner_shared.py`.
- `aw sanitize`

## Spec / documentation sync

N/A: enforces existing approved spec `4sd62s` C5 and AC-1 part (1).

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "_SCOPE_PATHS_LINE_RE" agent_workflows/artifact_refs.py` showing zero hits, plus pytest output passing for `Scope-Paths` citation rewriting.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste widened `rg -U` output over `partition.py`, `review_basis.py`, `check_engine.py`, `coverage_record.py`, `attention.py`, and `runner_shared.py` showing zero unexcluded front-matter metadata parser hits, plus pytest output passing for those modules.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_partition.py` output with all behavioral tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste full pytest summary, `mypy` zero-error output across `artifact_meta.py`, `artifact_refs.py`, `partition.py`, `review_basis.py`, `check_engine.py`, `coverage_record.py`, `attention.py`, and `runner_shared.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: These 8 source files and 1 test file share the single widened-search front-matter parser/writer cleanup (`avze51` + `hmtpj2`) with 4 concise E-items.

Execute after human approval (`Status: approved`). Commit path-scoped via `aw commit 75jciz -- <paths>`; never push.
