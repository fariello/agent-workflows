# IPD: Delete surviving legacy metadata parsers and writers found by 9o83cr E-14

- Date: 2026-11-24
- Kind: child
- Concern: Spec `4sd62s` C5 and AC-1 part (1) require a single metadata reader and writer (`agent_workflows/artifact_meta.py`) with no surviving legacy metadata parsers, writers, `Workflow history` section slicers, or `aw-prompt` comment helpers outside `artifact_meta.py` and `agent_workflows/migrations/m0001_*.py`. Plan `9o83cr` E-14 audited the codebase after the five split deletion parts (`q6epwc`, `snin8q`, `k6jd6l`, `e8420v`, `0xsx2n`) and found 19 surviving parser/locator hits plus widened-search front-matter literals and one `Scope-Paths` bullet writer (`artifact_refs._SCOPE_PATHS_LINE_RE`), tracked across six open backlog items (`ebbfmn`, `q4gwp9`, `hmtpj2`, `1h5eqc`, `vwkbd9`, `a0o7t0`). Because `9o83cr` is read-only on production code, this corrective child plan removes all surviving parsers and writers ahead of the attended cutover commit (`cxxmyv`).
- Scope: Consolidate and resolve all six surviving parser/writer cleanup backlog items (`ebbfmn`, `q4gwp9`, `hmtpj2`, `1h5eqc`, `vwkbd9`, `a0o7t0`) inside `Set: metastore`, wired directly ahead of `cxxmyv`. Retarget every surviving `^-` metadata regex, `Workflow history` section slicer, `aw-prompt` comment helper, and `Scope-Paths` bullet writer onto `artifact_meta`, then re-run both the `9o83cr` E-14 search audit and the widened multiline/flag-group search to confirm zero unexcluded parser or writer hits outside `artifact_meta.py` and `agent_workflows/migrations/m0001_*.py`. Excludes the attended log-format cutover itself (`cxxmyv`) and the unrelated pre-existing test budget/fixture items (`6o5aan`, `rryabb`, `vo0y6q`).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/artifact_refs.py, agent_workflows/artifact_rename.py, agent_workflows/attention.py, agent_workflows/backlog.py, agent_workflows/check_engine.py, agent_workflows/coverage_record.py, agent_workflows/ipd_lifecycle.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, agent_workflows/partition.py, agent_workflows/prompts.py, agent_workflows/releases.py, agent_workflows/review_basis.py, agent_workflows/runner_shared.py, agent_workflows/specs.py, tests/test_metadata_single_owner.py, .aw/records/plans/pending/20261124-metastore-300-rgva3w-delete-surviving-legacy-metadata-parsers-and-writers-found-b.ipd.md
- Item-Dependencies: executed:9o83cr
- Status: to-review
- From-Spec: 4sd62s
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: metastore
- Order: 300
- Highest E allocated: 6
- Id: rgva3w
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored consolidated corrective child plan for Set metastore (ahead of cxxmyv) covering 9o83cr E-14 survivors (ebbfmn, q4gwp9, hmtpj2, 1h5eqc, vwkbd9, a0o7t0).

## Goal

Eliminate every surviving legacy metadata parser, metadata writer, `Workflow history` section reader, and `aw-prompt` comment helper outside `agent_workflows/artifact_meta.py` and `agent_workflows/migrations/m0001_*.py` before the attended cutover commit (`cxxmyv`), closing backlog items `ebbfmn`, `q4gwp9`, `hmtpj2`, `1h5eqc`, `vwkbd9`, and `a0o7t0`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Workflow history and lifecycle readers (`1h5eqc`, `q4gwp9`)

- [ ] E-01 Migrate the surviving `Workflow history` section readers onto `artifact_meta.history_records` or `artifact_meta.history` (`1h5eqc`, `q4gwp9`): replace `attention._history_section_lines`, `backlog._WORKFLOW_HISTORY_HEADING_RE`, `releases._history_lines`, `specs._history_lines`, `ipd_lifecycle._plan_status_event_groups`, `ipd_lint.parse` history collection (`ipd_schema.H_WORKFLOW_HISTORY`), and `check_engine.check_spec_test_citations_for_text` heading slicing with calls to `artifact_meta`, and remove the local heading regexes.
  - Depends on: none
  - Expected outcome: zero local `Workflow history` section parsers or heading regexes remain in `attention.py`, `backlog.py`, `releases.py`, `specs.py`, `ipd_lifecycle.py`, `ipd_lint.py`, `ipd_schema.py`, and `check_engine.py`, and all existing tests for those modules pass.
  - Execution state: pending

### Task group 2: Prompt metadata comment helpers (`vwkbd9`)

- [ ] E-02 Move prompt `<!-- aw-prompt: ... -->` metadata parsing and rewriting into `artifact_meta.py` (`vwkbd9`): move `prompts.has_metadata_comment`, `prompts.inject_metadata_id6`, and `prompts.update_metadata_status` ownership into `artifact_meta.py`, replace `check_engine.validate_prompt_content`'s first-line `aw-prompt:` check with `artifact_meta.read_text(..., record_type="prompt")`, and replace `artifact_rename._MIRROR_ID_RE` and `artifact_rename._MANAGED_PROMPT_ID_RE` with `artifact_meta` readers.
  - Depends on: E-01
  - Expected outcome: no `aw-prompt` or managed-prompt metadata parser/writer remains outside `artifact_meta.py` and `migrations/m0001_*.py`, and prompt/rename/check tests pass.
  - Execution state: pending

### Task group 3: Surviving front-matter regex literals and `Scope-Paths` writer (`ebbfmn`, `a0o7t0`, `hmtpj2`)

- [ ] E-03 Remove the five surviving `^-` metadata regex literals in `specs.py` and `backlog.py` (`ebbfmn`): replace `specs._SPEC_ID_RE`, `specs._TOP_KEY_RE`, the `^- Status:` match in `specs.run_migrate`, `specs._SPEC_ID_BULLET_RE`, and `backlog._TOP_KEY_RE` with `artifact_meta` queries or `artifact_meta.read_text` / duplicate-field inspection.
  - Depends on: E-02
  - Expected outcome: `specs.py` and `backlog.py` contain zero `^-` metadata regex literals, while spec migration and duplicate-bullet checks preserve behavior.
  - Execution state: pending

- [ ] E-04 Replace the `Scope-Paths` bullet writer and surviving front-matter readers found by the widened search (`a0o7t0`, `hmtpj2`): rewrite `artifact_refs.plan_scope_path_reference_rewrites` / `apply_scope_path_reference_rewrites` to read via `artifact_meta` and write via `artifact_meta.append` (deleting `artifact_refs._SCOPE_PATHS_LINE_RE`); replace `partition._ORCHESTRATOR_KIND_RE`, `review_basis._is_orchestrator_text`, `check_engine._TARGET_BULLET_RE` (metadata `Scope-Paths` branch), `check_engine._REVIEW_SUBJECT_ID_RE`, `coverage_record._FINGERPRINT_LINE_RE`, `coverage_record._CHECKED_LINE_RE`, and `attention._FIELD_PATTERNS` metadata reads with `artifact_meta`; and audit `runner_shared._PROPOSAL_BULLET_RE` (move grammar helper into `artifact_meta` or classify explicitly if non-metadata body-prose escaping).
  - Depends on: E-03
  - Expected outcome: no metadata writer or front-matter bullet parser survives outside `artifact_meta.py` and `migrations/m0001_*.py`, and citation-rewrite, partition, coverage, and attention tests pass.
  - Execution state: pending

### Task group 4: Behavioral coverage and AC-1 re-audit

- [ ] E-05 Extend `tests/test_metadata_single_owner.py` with behavioral tests exercising prompt comment writes, `Scope-Paths` citation rewrites, and history/spec/backlog readers through `artifact_meta` (asserting real outputs, exit codes, and file bytes; no code-pinning source inspection).
  - Depends on: E-04
  - Expected outcome: new behavioral cases in `tests/test_metadata_single_owner.py` pass under `python3 -m pytest`.
  - Execution state: pending

- [ ] E-06 Re-run the four `9o83cr` E-14 `rg` searches plus the widened multiline/inline-flag search (`rg -U` for `^-` patterns), targeted pytest suites, `mypy` on modified modules, `aw ipd lint`, and `aw sanitize`.
  - Depends on: E-05
  - Expected outcome: zero unexcluded metadata parser or writer hits survive outside `artifact_meta.py` and `migrations/m0001_*.py`, and all validation checks pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `4sd62s` C5 requires one metadata reader and writer (`agent_workflows/artifact_meta.py`), verified by AC-1 part (1) in `9o83cr` E-14 and re-verified ahead of `cxxmyv`.
- Tests must assert observable behavior and outcomes only (no `inspect`, `ast`, regex, or source-text code-pinning assertions).
- Commits must be path-scoped via `aw commit rgva3w -- <paths>`.

## Findings

| Source backlog | Module / symbols | Defect class |
|---|---|---|
| `1h5eqc` | `attention._history_section_lines`, `backlog._WORKFLOW_HISTORY_HEADING_RE`, `releases._history_lines`, `specs._history_lines`, `ipd_lint.parse` (`ipd_schema.H_WORKFLOW_HISTORY`), `check_engine.check_spec_test_citations_for_text` | Surviving `Workflow history` section readers |
| `q4gwp9` | `ipd_lifecycle._plan_status_event_groups` (and remaining `HISTORY_RECORD_RE` callers) | Surviving `Workflow history` reader / legacy regex dependency |
| `vwkbd9` | `prompts.has_metadata_comment`, `prompts.inject_metadata_id6`, `prompts.update_metadata_status`, `check_engine.validate_prompt_content`, `artifact_rename._MIRROR_ID_RE`, `artifact_rename._MANAGED_PROMPT_ID_RE` | Surviving `aw-prompt` / mirror metadata readers and writers |
| `ebbfmn` | `specs._SPEC_ID_RE`, `specs._TOP_KEY_RE`, `specs.run_migrate` (`^- Status:`), `specs._SPEC_ID_BULLET_RE`, `backlog._TOP_KEY_RE` | Five surviving `^-` metadata regex literals |
| `a0o7t0` | `artifact_refs._SCOPE_PATHS_LINE_RE` (`apply_scope_path_reference_rewrites`), `partition._ORCHESTRATOR_KIND_RE`, `review_basis._is_orchestrator_text`, `runner_shared._PROPOSAL_BULLET_RE`, `check_engine._TARGET_BULLET_RE` | Surviving `Scope-Paths` metadata writer and widened front-matter readers |
| `hmtpj2` | `check_engine._REVIEW_SUBJECT_ID_RE`, `coverage_record._FINGERPRINT_LINE_RE`, `coverage_record._CHECKED_LINE_RE`, `attention._FIELD_PATTERNS` (and audit of `_GRADUATED_LINE_RE`, `_IMPLEMENTING_LINE_RE`, `_HISTORY_ATTRIB_RE`, `_COVERAGE_HIST_RE`, `_HISTORY_RECORD_PARTS_RE`, `_OQ_FINDING_REF_RE`) | Multiline or `(?mi)` metadata regexes missed by the one-line search |

## Proposed changes (ordered, validatable)

1. Route all `Workflow history` section readers (`E-01`) through `artifact_meta.history_records` / `artifact_meta.history`.
2. Consolidate `aw-prompt` comment parsing and updates into `artifact_meta.py` (`E-02`).
3. Remove the five surviving `^-` metadata regexes in `specs.py` and `backlog.py` (`E-03`).
4. Route `Scope-Paths` rewrites through `artifact_meta.append` and replace widened front-matter readers (`E-04`).
5. Add behavioral tests in `tests/test_metadata_single_owner.py` (`E-05`) and re-run the AC-1 search audit (`E-06`).

## Deferred / out of scope (with reason)

- The attended metadata log-format cutover commit is owned by `cxxmyv`.
  - Carrier: cxxmyv
- Pre-existing core test budget overrun (`6o5aan`), stale-stop resume test failures (`rryabb` / `z6wodh`), and home-records target state lock test (`vo0y6q` / `rntx9a`) are independent of AC-1 parser ownership.
  - Carrier: 6o5aan
  - Carrier: z6wodh
  - Carrier: rntx9a

## Scope check

- Over-scope: none; edits are limited to the surviving parser/writer modules, `artifact_meta.py`, `tests/test_metadata_single_owner.py`, and this plan.
- Under-scope: none; all 19 E-14 survivors plus the widened-search hits across all six backlog items are covered ahead of `cxxmyv`.

## Required tests / validation

- `python3 -m pytest tests/test_metadata_single_owner.py` plus affected module test files (`tests/test_prompts*.py`, `tests/test_specs*.py`, `tests/test_backlog*.py`, `tests/test_artifact_refs*.py`, `tests/test_partition*.py`, `tests/test_coverage*.py`, `tests/test_ipd_lifecycle*.py`).
- `python3 -m mypy` on all modified modules.
- Re-run of the four `9o83cr` E-14 `rg` commands plus widened multiline/flag search confirming zero unexcluded parser or writer hits outside `artifact_meta.py` and `migrations/m0001_*.py`.
- `aw sanitize` and `aw ipd lint --phase pre-transition`.

## Spec / documentation sync

N/A: this plan brings implementation into full conformance with existing approved spec `4sd62s` C5 and AC-1 part (1); post-cutover documentation updates remain owned by `90iqr1` and `cxxmyv`.

## Open questions

None. All scope decisions were resolved by the maintainer on 2026-11-24 when authorizing this consolidated cleanup child plan in `Set: metastore` ahead of `cxxmyv`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "Workflow history" agent_workflows/attention.py agent_workflows/backlog.py agent_workflows/releases.py agent_workflows/specs.py agent_workflows/ipd_lifecycle.py agent_workflows/ipd_lint.py agent_workflows/ipd_schema.py agent_workflows/check_engine.py` showing zero section-reader hits, plus pasted `python3 -m pytest` output for attention, backlog, releases, specs, ipd_lifecycle, and ipd_lint tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "aw-prompt|aw-managed-prompt" agent_workflows/prompts.py agent_workflows/check_engine.py agent_workflows/artifact_rename.py` showing zero parser/writer hits, plus pasted `python3 -m pytest` output for prompt, rename, and check_engine tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/specs.py agent_workflows/backlog.py` showing zero hits, plus pasted `python3 -m pytest` output for specs and backlog duplicate-bullet/migration tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste widened regex search output over `agent_workflows/artifact_refs.py`, `agent_workflows/partition.py`, `agent_workflows/review_basis.py`, `agent_workflows/check_engine.py`, `agent_workflows/coverage_record.py`, and `agent_workflows/attention.py` showing zero unexcluded metadata parser/writer hits, plus pasted `python3 -m pytest` output for citation-rewrite, partition, coverage, and attention tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_metadata_single_owner.py` output with all cases passing, confirming zero code-pinning source reads in the test file.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the four `9o83cr` E-14 `rg` commands filtered by the exclusion list showing zero surviving parser/writer hits outside `artifact_meta.py` and `migrations/m0001_*.py`, plus pasted `mypy` and `aw sanitize` outputs.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `executed:9o83cr`. Commit only path-scoped files via `aw commit rgva3w -- <paths>`; never push. Finalize through `aw ipd finalize` (or runner self-finalize) after all `E-*` are `performed` and all `V-*` are `pass`.
