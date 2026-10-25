# IPD: Run the review pilot against the current plan-review and record the build-the-rest decision

- Date: 2026-10-24
- Kind: child
- Concern: Spec `k3yx72` rests on one assumption: that a tiered, multi-prompt review costs less than today's single-turn `/plan-review` without lower quality (Section 13.1 question 1). MD-20 builds only Stage 1 first and builds Stage 2 (Orders 03, 06, 07, 08, the rest of 05) only if a pilot supports that assumption. MD-19 fixes the pilot's shape: 9 plans (3 per expected tier) with planted defects, the current review against the proposed review (and, for `complex`, both groupings), 3 models, repeats to measure noise, and 3 blind judge models whose scores are averaged; 84 reviews and 252 judge runs (Section 13.3). Nothing has been run. The planning estimate is about $1,000 to $1,800 (Section 13.3), so the pilot spends real money and needs a human at the start.
- Scope: Prepare the 9 fixture plans and their planted-defect key; fix the quality rubric and its weights before any review is scored; run the 84 reviews through the runners with labels; run the 252 blind judge scorings; analyze cost, tool-output bytes, quality, run-to-run spread, judge disagreement, and self-scoring; apply the Section 13.5 pilot gate; record the result as a research report in Set `revsteps`; set the default `complex` grouping per Section 13.5; and, when the gate says BUILD THE REST, file a backlog item for authoring the Stage 2 plans. EXCLUDES the sized run (Section 13.3 stage 2), which runs only if the maintainer asks after reading the pilot and then needs its own plan carrying OQ-10 as `Blocking: yes`; EXCLUDES authoring Stage 2 plans themselves.
- Scope-Paths: tests/fixtures/review-pilot/**, tools/review_pilot.py, agent_workflows/review_sequence.py, .aw/records/research/**/*-revsteps-*-review-pilot*.md, .aw/records/backlog/**/*-revsteps-*.backlog.md, .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
- Item-Dependencies: executed:uiyoax, executed:is2xiv
- Status: to-review
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Attended: required
- Set: revsteps
- Order: 9
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: kk62qt

## Workflow history
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Decide, on measured cost and quality, whether the proposed review is worth finishing (spec MD-20), and record the evidence so the maintainer can check the decision.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: fixtures and rubric (fixed before any review)

- [ ] E-01 Choose 9 executed plans from `.aw/records/plans/executed/` as fixture sources: 3 the author expects to be `simple` (1 to 4 E-items, no `.spec.md` in scope, no tier question 2 module), 3 `standard`, 3 `complex` (above 10 E-items or naming a spec or a tier question 2 module). Copy each into `tests/fixtures/review-pilot/plans/` with `- Status: to-review`, `- Readiness:` removed, every checkbox reset to `[ ]`, every `Execution state` set to `pending` and every `Observed evidence` and `Result` cleared, and its `## Workflow history` replaced by one `to-review` line. Record the source id6, expected tier, and the reason in `tests/fixtures/review-pilot/manifest.json`.
  - Depends on: none
  - Expected outcome: 9 fixture plans, each passing `aw ipd lint --phase author` with no error.
  - Execution state: pending

- [ ] E-02 Plant three defects in each fixture (spec Section 13.3 V1): a `V-*` item whose `Required evidence` asks for no concrete evidence; a wrong file path in one E-item; and a changed CLI option that another command reads (an E-item renaming or removing an option whose other reader the plan does not mention). Record each planted defect (fixture, location, original text, planted text, harm if executed on a 1 to 3 scale) in `tests/fixtures/review-pilot/defects.json`. The key is never placed in any review prompt or review worktree.
  - Depends on: E-01
  - Expected outcome: 27 planted defects recorded with harm weights.
  - Execution state: pending

- [ ] E-03 Write the quality rubric `tests/fixtures/review-pilot/rubric.md` per spec Section 13.4, with weights fixed now: planted defects found (each weighted by its E-02 harm), false findings raised, correctness of the edits the review made, and design quality of the reviewed plan afterwards, each scored on a stated integer scale with anchored descriptions, and the formula that combines them into one score. Write the judge prompt `tests/fixtures/review-pilot/judge-prompt.md`: it gives the judge the fixture before the review, the plan and review record after it, the defect key, and the rubric, and never the method, model, or host that produced the review. Commit E-01 to E-03 (`aw commit kk62qt -- tests/fixtures/review-pilot`) BEFORE any review runs, so the rubric is provably fixed first.
  - Depends on: E-02
  - Expected outcome: a commit containing the fixtures, defect key, rubric, and judge prompt, dated before the first review attempt.
  - Execution state: pending

### Task group 2: running the reviews

- [ ] E-04 Write `tools/review_pilot.py`, a driver that for each cell of spec Section 13.3 (fixture, method, model, repeat) creates a scratch git repository from the current commit (`git worktree add` of the pilot commit into `tmp/review-pilot/<cell>/`, which is gitignored), copies in the fixture plan only, and runs one review with the runner in that repository: `aw oc run start --repo <dir> <id6> --action review --label pilot-<cell> --model <model> --review-mode {single|steps} --review-variant <current|grouped-6|single-12>` for the OpenCode models (`uri/its_direct/pt3-claude-opus-5.5-1m-us` variant high, `openai/gpt-6.1-sol` variant high) and the same through `aw agy run start --repo <dir>` for Gemini 3.8 Flash High. `--review-mode single` is the current `/plan-review`. Each cell gets a new session (V4). The driver writes one line per cell to `tmp/review-pilot/cells.jsonl` (cell key, run id, exit code), skips a cell already recorded as completed so it can be re-run after an interruption, and stops before starting a cell when the running total of recorded cost (read with `aw runs query attempts --filter label=pilot-* --metric cost --stat sum`) exceeds a `--budget` dollar argument.
  - Depends on: E-03
  - Expected outcome: `python3 tools/review_pilot.py --dry-run` prints 84 cells: simple 24, standard 24, complex 36.
  - Execution state: pending

- [ ] E-05 With the maintainer present, confirm the budget (the Section 13.3 planning estimate is $1,000 to $1,800; ask with `/askme` for the `--budget` value and record the answer in this plan's OQ-01), then run `python3 tools/review_pilot.py --budget <value>`. Record any cell that did not complete and why. The run is resumable by re-invoking the same command.
  - Depends on: E-04
  - Expected outcome: 84 completed cells, or every missing cell listed with its reason (AC-17).
  - Execution state: pending

### Task group 3: scoring and analysis

- [ ] E-06 Score every completed review with each of the three judge models using `judge-prompt.md` (252 judge runs for 84 reviews), driven by `tools/review_pilot.py judge`, writing `tmp/review-pilot/scores.jsonl` (cell, judge model, each rubric component, total). The judge runs in its own scratch directory holding only the before and after files, the key, and the rubric. Record judge-run failures.
  - Depends on: E-05
  - Expected outcome: up to 252 score rows, missing rows listed with reasons.
  - Execution state: pending

- [ ] E-07 Run `aw runs analyze` and compute, per tier and method (and per model): cost median and spread (tokens where no cost is recorded, which is the case on Antigravity), model steps, tool-output bytes by tool, re-asks and failed postconditions, re-review passes, verdict, assigned tier, and the average quality score; the run-to-run spread from the repeat cells (V5); judge disagreement (spread of the three judges per review); and self-scoring (each judge's average on reviews by its own model compared with the others). Use `aw runs query experiment --filter label=pilot-*` and `aw runs query attempts ... --group-by review_step` for the step-level view, and `tools/review_pilot.py report` for the quality joins. Report a fixture whose assigned tier differs from its expected tier, rather than re-binning it.
  - Depends on: E-06
  - Expected outcome: a complete table of the measures of spec Section 13.4, per tier and method.
  - Execution state: pending

### Task group 4: decision and records

- [ ] E-08 Apply the spec Section 13.5 pilot gate per tier (BUILD THE REST, STOP, or OTHERWISE for the maintainer), and the `complex` grouping rule (choose a variant shown better on quality, or cheaper at equivalent quality, else `single-12`). Create the report with `aw research new --kind findings --set revsteps --slug review-pilot-results --summary "k3yx72 pilot: proposed vs current plan-review, per-tier cost and quality, MD-20 gate decision" --apply`, and fill it with: the design as run, the per-tier table of E-07, run-to-run spread, judge disagreement and self-scoring, the missing cells, the gate decision per tier with its reasoning, and the `complex` default. Include the sample-size calculation for a sized run at the example margins of spec OQ-10, so the maintainer can answer OQ-10 from it.
  - Depends on: E-07
  - Expected outcome: a tracked findings report in Set `revsteps` carrying decision lines `MD-20 gate: <BUILD THE REST|STOP|OTHERWISE>` and `complex default: <grouped-6|single-12>`.
  - Execution state: pending

- [ ] E-09 Act on the decision: set the `complex` default variant in `agent_workflows/review_sequence.py` (the `single-12` default of Order 04 E-05 changes only if E-08 chose `grouped-6`); add an `aw specs note k3yx72` line recording the gate decision and the report path; when the gate is BUILD THE REST, file `aw backlog new` (Set `revsteps`, Work-Kind `feature`, `--blocks-release next`) for "author k3yx72 Stage 2 plans (Orders 03, 06, 07, 08, rest of 05)" citing the report; when OTHERWISE, ask the maintainer with `/askme` whether to build the rest, stop, or run the sized run, and record the answer the same way; when STOP, record it and file nothing.
  - Depends on: E-08
  - Expected outcome: the spec carries a history note naming the decision; a backlog item exists exactly when the decision is to build the rest.
  - Execution state: pending

- [ ] E-10 Run `aw check` and, if E-09 changed `review_sequence.py`, `python3 -m pytest -o addopts="" -n auto tests/test_review_sequence.py tests/test_review_sequence_runner.py` and the bare core gate `python3 -m pytest`. Commit through `aw commit kk62qt -- <each changed path>` (the report, the backlog item if any, the spec note, `tools/review_pilot.py`, and `review_sequence.py` if changed). Never push.
  - Depends on: E-09
  - Expected outcome: `aw check` reports no error and no warning this plan introduced; tests pass when run; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `--label` and `--review-variant` are recorded in `state.json` `options` and are attempt-grain filter and group-by fields (`run_analytics_attempts.ATTEMPT_FILTER_FIELDS`); `aw runs query experiment` reports per plan, variant, and model (`run_analytics_attempts.view_experiment`).
- `aw oc run start` and `aw agy run start` accept `--repo <dir>`, which lets each cell run in its own scratch repository; `tmp/` is gitignored (`.gitignore` entry `tmp/`).
- `- Attended: required` makes the runners hold the plan for an interactive session instead of running it headless (spec `20260802-1904` Section 4.4); this plan needs it because E-05 spends money on a budget the maintainer sets and E-09 may need a maintainer decision.
- Antigravity records no dollar cost (`docs/run-analytics.md`, "What is not recorded yet"); cost comparisons on that host use tokens.
- `run_analytics_statistics.MINIMUM_SAMPLE_SIZE = 12` withholds medians for small groups; per-tier pilot groups are smaller, so E-07 reports raw values and spreads from the cell rows, not the withheld medians.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | Spec `k3yx72` Section 13.3 count: simple 24, standard 24, complex 36 | 84 reviews and 252 judge runs, matching AC-17. |
| F-02 | `opencode models` lists `openai/gpt-6.1-sol` and `uri/its_direct/pt3-claude-opus-5.5-1m-us`; `aw oc profile list` shows `gem` as `google/gemini-3.8-flash` on OpenCode | Gemini must run on Antigravity per spec V3, not through the OpenCode `gem` profile. |
| F-03 | `tests/fixtures/` exists and holds static test inputs | Fixture plans live there; they are not plans in `.aw/records/plans/`, so the runner never queues them in this repository. |

## Proposed changes (ordered, validatable)

1. E-01 to E-03: fixtures, defects, rubric, committed first.
2. E-04, E-05: driver and the attended run.
3. E-06, E-07: blind scoring and analysis.
4. E-08 to E-10: report, decision, records, commit.

## Deferred / out of scope (with reason)

- Sized run (spec Section 13.3 stage 2): only if the maintainer asks after reading the report; it then needs its own plan carrying OQ-10 as `Blocking: yes` (spec Section 15 Order 09 row).
- Stage 2 plans: authored after this plan records BUILD THE REST; E-09 files the backlog item that carries that work.
- Optional session question 4 (Section 13.1): later round; V4 is fixed to a new session here.

## Scope check

- Over-scope: none. `review_sequence.py` is touched only when E-08 chooses `grouped-6`.
- Under-scope: none. Spec Sections 13.1 to 13.5 (pilot only) and AC-17 are covered.

## Required tests / validation

- Rubric fixed before scoring: V-03 shows the rubric commit precedes the first pilot run.
- Coverage of the design: V-05 shows 84 cells or a reason per missing cell; V-06 shows 252 score rows or a reason per missing row.
- Decision traceable: V-08 and V-09 show the report's decision lines and the spec note.

## Spec / documentation sync

Appends a history note to spec `k3yx72` recording the gate decision (declared in `- Scope-Paths:`), because the spec's MD-20 makes that decision the condition for its Stage 2; the spec's text is not changed. No user-facing documentation changes.

## Open questions

### OQ-01: Dollar budget for the pilot run

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Asked at E-05 with the maintainer present, because the plan is `Attended: required`; the driver refuses to start a cell beyond the budget. Recommended answer: $1,800, the top of the spec's planning estimate. Recommendation strength: medium (the estimate is weak because `complex`-tier and Antigravity costs are not yet measured).

### OQ-02: Which executed plans become the 9 fixtures?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Chosen at E-01 by the executor against the stated tier criteria and recorded in `manifest.json` with reasons; the choice is reviewable after the fact and does not change the method. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw ipd lint --phase author tests/fixtures/review-pilot/plans/*.md` output with no error, and the `manifest.json` contents.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -c` output counting `defects.json` entries per fixture (3 each, 27 total) with harm weights.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git log --format='%h %cI %s' -- tests/fixtures/review-pilot` and the earliest `started_at` among `pilot-*` attempts from `aw runs query attempts --filter label=pilot-* --json`, showing the rubric commit is earlier.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 tools/review_pilot.py --dry-run | tail -5` showing the per-tier cell counts 24, 24, 36.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the count of completed cells from `tmp/review-pilot/cells.jsonl` per tier and the list of missing cells with reasons; and the recorded OQ-01 answer. (The observation is produced by `tools/review_pilot.py` launching `aw oc run` / `aw agy run`.)
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the count of score rows in `tmp/review-pilot/scores.jsonl` per judge model and the list of missing judge runs with reasons.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the per-tier, per-method table (cost or tokens, steps, tool-output bytes, average quality, spread) as produced by `tools/review_pilot.py report`, and the `aw runs query experiment --filter label=pilot-*` output.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the report path and its two decision lines (`MD-20 gate:` and `complex default:`) quoted from the file.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the new `k3yx72` history line, and either the new backlog item's path and front matter or the statement that the decision was STOP (or the recorded maintainer answer for OTHERWISE).
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the `aw check` summary compared with the baseline taken before E-01, any pytest summary lines run, and the `aw commit` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`), in an attended session (`- Attended: required`): the runner holds this plan for an interactive session rather than running it headless. Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit kk62qt -- <paths>`; never push. Paste actual output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
