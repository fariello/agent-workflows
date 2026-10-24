---
id: gczlvd
created: 20261023
set: revcost
order: 01
topic: []
model: 
kind: findings
status: todo
outcome: adopted
summary: okj4bg Section 5 report: review-cost questions, commands, missing data, corrected facts
consumed-by: [avg8qv]
---

# Research Findings: okj4bg Section 5 Report (Review-Cost Analysis)

## 1. Questions and Commands

The questions from prompt `okj4bg` Section 3 and their corresponding `aw runs query` commands:

- **Q1 (Token composition)**: Per phase (review, execute, verifier, recovery), and per attempt: new input, cache-read, cache-write, output, and reasoning tokens, with token and cost shares.
  - `aw runs query attempts --filter role=main --group-by phase --stat sum`
  - `aw runs query attempts --filter action=review --metric input,cache_read,cache_write,output,reasoning,steps,context_first,context_last,context_max`
- **Q2 (Steps and context)**: Per attempt: number of model steps, context size at first step, last step, and maximum; cost against step count.
  - `aw runs query attempts --filter action=review --group-by step_bucket --metric cost,steps`
- **Q3 (Session reuse)**: Per attempt: whether host session was new to the run or reused, and initial context size.
  - `aw runs query attempts --filter action=review --group-by session_origin --metric context_first,cost,steps`
- **Q4 (Tool use)**: Tool call counts and output bytes per tool; bash command families and files most often read.
  - `aw runs query tools --filter action=review`
- **Q5 (Run version and label)**: Group and filter by toolkit git commit and user run label.
  - `aw runs query attempts --group-by code_commit` (or `label`, `review_variant`, `repo_commit`)
- **Q6 (Model and source)**: Group and filter by model, with model source and coverage per phase.
  - `aw runs query attempts --group-by phase,model_source --metric steps --stat count`
- **Q7 (Redo counts)**: Per attempt and per model: re-asks, turn retries, refusals, and redo totals.
  - `aw runs query attempts --group-by model --metric redo_total,turn_retries,refusals,reasks --stat sum`
- **Q8 (Experiment comparison)**: For runs selected by label: plan id6, review variant, model, cost or tokens, steps, wall time, redo counts, and review outcome (disposition and Readiness).
  - `aw runs query experiment --filter label=<label>`
  - `aw runs query attempts --filter action=review --group-by readiness --metric cost,steps`
- **Q9 (Review steps)**: Grouping by review prompt step and pass number within a multi-prompt review.
  - Not recorded (see Section 2 for details).

## 2. Missing Data

The following data requested by prompt `okj4bg` is not currently recorded:

- **Review steps (Q9)**: requires recording which prompt of a multi-prompt review ran and the pass number for each prompt; specified in spec `k3yx72` Section 9.3 and built by its Section 15 Order 04.
- **Antigravity cost**: tokens are reported; no dollar price table is applied (prompt `okj4bg` Section 2 forbids invented prices).
- **Readiness on older runs**: runs started before plan `avg8qv` do not carry `review_readiness` on their review attempts, so they report `(not recorded)`.

## 3. Corrected Facts from Section 1

Facts in prompt `okj4bg` Section 1 checked against code:

- **F-03**: `okj4bg` Section 1 stated `state.json` has "no git commit and no user label". In the current codebase (since commit `131c9470d`), `state.json` records a `git` block (`commit`, `dirty`, `aw_version`), and `options` records `label` and `review_variant`.
- **F-04**: `okj4bg` Section 1 listed `defect-report-recorded` under relevant events as if it were a redo. `defect-report-recorded` fires on every recorded defect report, not only on a redo; the re-ask it may trigger is already counted through `defect_reasked` and the `defect-reask` session row, so it should not be counted as a redo.
- **Re-measurement**: run data not present in this workspace; facts checked against code only

## 4. Added Recording

- `review_readiness` is now recorded on every plan-review attempt in `state.json` on both hosts (`oc_runipd` and `agy_runipd` via `runner_shared.execute_item_core`), starting from plan `avg8qv`'s commit onward. It captures the plan's normalized `- Readiness:` front-matter value (`go`, `go-pending-approval`, `no-go`), or `None` if the review wrote no valid Readiness line.
- `readiness` is carried into attempt facts (`attempts.jsonl`, schema version 3), allowlists (`ATTEMPT_FILTER_FIELDS`, `ATTEMPT_GROUP_FIELDS`), `view_experiment` (with a `readiness` count map), and the dashboard.

## 5. Verification Output

Test command executed:
`python3 -m pytest -o addopts="" -n auto tests/test_run_analytics_review_cost.py tests/test_run_dashboard.py tests/test_rereview_reviewed_plan.py tests/test_defect_report.py`

Actual test runner summary:
`============================= 93 passed in 15.42s ==============================`
