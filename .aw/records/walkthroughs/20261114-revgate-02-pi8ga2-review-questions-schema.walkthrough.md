# Walkthrough: review prompt questions[] schema (pi8ga2)

- Date: 2026-11-14
- Set: revgate
- Commits: 2d0ccf156 (fix and tests)

## pi8ga2

In `run-20261114T042744Z-1314525`, two review turns (`iqhzse` and `kyl3m4`) found blocking `artifact_meta` defects, escalated `OQ-02` (`Blocking: yes`), and wrote `questions[]` in their outcome JSON files to park as `awaiting-human`. Because `agent_workflows/runner_shared.py::build_review_prompt` instructed isolated review turns to populate `questions[]` without providing `questions_schema_literal()`, both review agents guessed field names (`id`, `plan`, `finding`, `blocking`, `question`, `context`) and wrote `options` entries exceeding `QUESTION_OPTION_MAX_LENGTH` (120 characters). `validate_questions` marked both payloads `questions-malformed`, skipped `awaiting-human` parking, and forwarded both turns to `integrate_review_lane_branch`, which refused integration on `IPD-Q501` (`fail-merge`).

`agent_workflows/runner_shared.py::questions_schema_literal` now accepts `artifact_id6` (defaulting to `"id6"`) and states the item-count and character limits for `evidence` and `options` inline. `agent_workflows/runner_shared.py::build_review_prompt` embeds that schema block in isolated review prompts while keeping non-isolated review prompts unchanged.

## Validation

Targeted suite in `.aw/worktrees/revgate-qschema`:

```
python3 -m pytest tests/test_question_carrier.py tests/test_production_prompt_writing_standard.py tests/test_question_parking.py tests/test_review_sweep_lane_refusal_isolation.py
42 passed in 17.54s
aw backlog check: all backlog items conform. 1153 backlog items checked.
```
