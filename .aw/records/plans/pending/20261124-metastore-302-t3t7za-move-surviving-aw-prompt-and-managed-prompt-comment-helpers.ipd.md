# IPD: Move surviving aw-prompt and managed-prompt comment helpers into artifact_meta

- Date: 2026-11-24
- Kind: child
- Concern: Spec `4sd62s` C5 and AC-1 part (1) require all artifact metadata readers and writers to live exclusively in `agent_workflows/artifact_meta.py` (plus `agent_workflows/migrations/m0001_*.py`). Plan `9o83cr` E-14 found surviving `<!-- aw-prompt: ... -->` and `<!-- aw-managed-prompt: ... -->` metadata parsers and writers in `prompts.py`, `check_engine.py`, and `artifact_rename.py` (with callers in `cli.py` and `status_set.py`), tracked in backlog `iedbnn`. This focused plan consolidates those helpers into `artifact_meta.py` ahead of `9o83cr` (replacing E-02 of superseded `rgva3w`).
- Scope: Move `has_metadata_comment`, `inject_metadata_id6`, and `update_metadata_status` ownership into `agent_workflows/artifact_meta.py`; retarget `prompts.py`, `check_engine.py`, `artifact_rename.py`, `cli.py`, and `status_set.py` onto `artifact_meta` prompt readers/writers; and verify with behavioral tests in `tests/test_prompts_set_surface.py`.
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/prompts.py, agent_workflows/check_engine.py, agent_workflows/artifact_rename.py, agent_workflows/cli.py, agent_workflows/status_set.py, tests/test_prompts_set_surface.py, .aw/records/plans/pending/20261124-metastore-302-t3t7za-move-surviving-aw-prompt-and-managed-prompt-comment-helpers.ipd.md
- Item-Dependencies: executed:0xsx2n, executed:e8420v, executed:k6jd6l, executed:q6epwc, executed:snin8q
- Status: to-review
- From-Spec: 4sd62s
- From-Backlog: iedbnn
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Set: metastore
- Order: 302
- Highest E allocated: 4
- Id: t3t7za
- Author: antigravity

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-24 to-review (antigravity): authored Order 302 child plan (split from superseded `rgva3w` per maintainer decision 2026-11-25, ahead of `9o83cr`) covering `iedbnn`.

## Goal

Consolidate every `aw-prompt` and `aw-managed-prompt` metadata comment parser and writer into `agent_workflows/artifact_meta.py` so zero prompt metadata regexes or writers remain in `prompts.py`, `check_engine.py`, or `artifact_rename.py` ahead of `9o83cr`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Move prompt comment helpers into `artifact_meta.py`

- [ ] E-01 Move prompt metadata comment detection, `id6` injection, and status updates (`has_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`) into `agent_workflows/artifact_meta.py` and update callers in `agent_workflows/prompts.py`, `agent_workflows/cli.py`, and `agent_workflows/status_set.py` so `prompts.py` carries no local `aw-prompt` regexes or comment writers.
  - Depends on: none
  - Expected outcome: `prompts.py`, `cli.py`, and `status_set.py` delegate all prompt metadata comment reads and writes to `artifact_meta.py`, preserving prompt creation and status transitions.
  - Execution state: pending

### Task group 2: Retarget `check_engine.py` and `artifact_rename.py`

- [ ] E-02 Replace `check_engine.validate_prompt_content`'s first-line `aw-prompt:` check with `artifact_meta.read_text(..., record_type="prompt")`, and replace `artifact_rename._MIRROR_ID_RE` and `artifact_rename._MANAGED_PROMPT_ID_RE` with `artifact_meta` readers.
  - Depends on: E-01
  - Expected outcome: zero `aw-prompt` or `aw-managed-prompt` regexes remain in `check_engine.py` and `artifact_rename.py`, while prompt validation and rename continue to enforce existing contracts.
  - Execution state: pending

### Task group 3: Behavioral tests and validation

- [ ] E-03 Add or update behavioral tests in `tests/test_prompts_set_surface.py` exercising prompt comment creation, `id6` injection, status updates, `validate_prompt_content`, and prompt rename via `artifact_meta` (asserting real outputs and file bytes; zero code-pinning source reads).
  - Depends on: E-02
  - Expected outcome: all prompt comment behavioral tests pass under `python3 -m pytest`.
  - Execution state: pending

- [ ] E-04 Run targeted pytest suites (`tests/test_prompts_set_surface.py` and prompt/rename/check tests), `mypy` on all 6 modified source files, `rg` over `prompts.py`, `check_engine.py`, and `artifact_rename.py`, and `aw sanitize`.
  - Depends on: E-03
  - Expected outcome: zero `aw-prompt` / `aw-managed-prompt` parser/writer hits remain outside `artifact_meta.py` and `migrations/m0001_*.py`, pytest passes, `mypy` is clean, and `aw sanitize` passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Spec `4sd62s` C5 and AC-1 part (1) require `artifact_meta.py` to be the sole metadata reader and writer.
- Tests must test observable behavior only (no source-reading assertions).
- Commit path-scoped via `aw commit t3t7za -- <paths>` in an isolated worktree.

## Findings

Tracked in open backlog `iedbnn`:
- `prompts.has_metadata_comment`, `prompts.inject_metadata_id6`, `prompts.update_metadata_status` (and callers in `cli.py`, `status_set.py`).
- `check_engine.validate_prompt_content`, `artifact_rename._MIRROR_ID_RE`, `artifact_rename._MANAGED_PROMPT_ID_RE`.

## Proposed changes (ordered, validatable)

1. Move prompt comment helpers into `artifact_meta.py` and retarget `prompts.py`, `cli.py`, and `status_set.py` (`E-01`).
2. Retarget `check_engine.py` and `artifact_rename.py` onto `artifact_meta` readers (`E-02`).
3. Add behavioral tests in `tests/test_prompts_set_surface.py` (`E-03`) and validate with pytest, `mypy`, `rg`, and `aw sanitize` (`E-04`).

## Deferred / out of scope (with reason)

- `Workflow history` section readers are owned by Order 301 (`wgn3bl`).
  - Carrier: wgn3bl
- Specs/backlog `^-` regexes are owned by Order 303 (`fkvrc7`).
  - Carrier: fkvrc7
- `Scope-Paths` writer and widened front-matter readers are owned by Order 304 (`75jciz`).
  - Carrier: 75jciz
- Final AC-1 zero-survivors audit is owned by `9o83cr`.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none; strictly limited to prompt metadata comment helpers and their callers.
- Under-scope: none; covers every `iedbnn` survivor ahead of `9o83cr`.

## Required tests / validation

- `python3 -m pytest tests/test_prompts_set_surface.py` plus rename and check_engine prompt tests.
- `python3 -m mypy agent_workflows/artifact_meta.py agent_workflows/prompts.py agent_workflows/check_engine.py agent_workflows/artifact_rename.py agent_workflows/cli.py agent_workflows/status_set.py`
- `rg -n "aw-prompt|aw-managed-prompt" agent_workflows/prompts.py agent_workflows/check_engine.py agent_workflows/artifact_rename.py`
- `aw sanitize`

## Spec / documentation sync

N/A: enforces existing approved spec `4sd62s` C5 and AC-1 part (1).

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "aw-prompt|aw-managed-prompt" agent_workflows/prompts.py` showing zero hits, plus pytest output passing for prompt creation and status transitions in `prompts.py`, `cli.py`, and `status_set.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "aw-prompt|aw-managed-prompt|_MIRROR_ID_RE|_MANAGED_PROMPT_ID_RE" agent_workflows/check_engine.py agent_workflows/artifact_rename.py` showing zero hits, plus pytest output passing for `validate_prompt_content` and prompt rename.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_prompts_set_surface.py` output with all behavioral tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste full pytest summary, `mypy` zero-error output across `artifact_meta.py`, `prompts.py`, `check_engine.py`, `artifact_rename.py`, `cli.py`, and `status_set.py`, and `aw sanitize` clean output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after human approval (`Status: approved`). Commit path-scoped via `aw commit t3t7za -- <paths>`; never push.
