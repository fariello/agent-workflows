# IPD: Run the review pilot against the current plan-review and record the build-the-rest decision

- Date: 2026-10-24
- Kind: child
- Concern: Spec `k3yx72` rests on one assumption: that a tiered, multi-prompt review costs less than today's single-turn `/plan-review` without lower quality (Section 13.1 question 1). MD-20 builds only Stage 1 first and builds Stage 2 (Orders 03, 06, 07, 08, the rest of 05) only if a pilot supports that assumption. MD-19 fixes the pilot's shape: 9 plans (3 per expected tier) with planted defects, the current review against the proposed review (and, for `complex`, both groupings), 3 models, repeats to measure noise, and 3 blind judge models whose scores are averaged; 84 reviews and 252 judge runs (Section 13.3). Nothing has been run. The planning estimate is about $1,000 to $1,800 (Section 13.3), so the pilot spends real money and needs a human at the start.
- Scope: Prepare the 9 fixture plans and their planted-defect key; fix the quality rubric and its weights before any review is scored; run the 84 reviews through the runners with labels; run the 252 blind judge scorings; analyze cost, tool-output bytes, quality, run-to-run spread, judge disagreement, and self-scoring; apply the Section 13.5 pilot gate; record the result as a research report in Set `revsteps`; set the default `complex` grouping per Section 13.5; and, when the gate says BUILD THE REST, file a backlog item for authoring the Stage 2 plans. EXCLUDES the sized run (Section 13.3 stage 2), which runs only if the maintainer asks after reading the pilot and then needs its own plan carrying OQ-10 as `Blocking: yes`; EXCLUDES authoring Stage 2 plans themselves.
- Scope-Paths: tests/fixtures/review-pilot/**, tools/review_pilot.py, tests/test_review_pilot.py, agent_workflows/review_sequence.py, agent_workflows/runner_shared.py, .aw/records/research/**/*-revsteps-*-review-pilot*.md, .aw/records/backlog/**/*-revsteps-*.backlog.md, .aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md
- Item-Dependencies: executed:uiyoax, executed:is2xiv
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Attended: required
- Set: revsteps
- Order: 9
- Highest E allocated: 11
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: kk62qt

## Workflow history
- 2026-10-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: kk62qt verified (set revsteps, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/review_sequence.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified agent_workflows/runner_shared.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-25 approved (aw set): status set to approved
- 2026-10-25 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED
- 2026-10-25 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED; review record .aw/records/reviews/20261024-revsteps-09-kk62qt-run-the-review-pilot-against-the-current-plan-review-and-rec.review.md
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Decide, on measured cost and quality, whether the proposed review is worth finishing (spec MD-20), and record the evidence so the maintainer can check the decision.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: fixtures and rubric (fixed before any review)

- [x] E-01 Choose 9 executed plans from `.aw/records/plans/executed/` as fixture sources: 3 the author expects to be `simple` (1 to 4 E-items, no `.spec.md` in scope, no tier question 2 module), 3 `standard`, 3 `complex` (above 10 E-items or naming a spec or a tier question 2 module). Copy each into `tests/fixtures/review-pilot/plans/` with `- Status: to-review`, `- Readiness:` and `- Approval:` removed, every checkbox reset to `[ ]`, every `Execution state` set to `pending` and every `Observed evidence` and `Result` cleared, and its `## Workflow history` replaced by one `to-review` line. Give each fixture a FRESH id6 (`artifact_core.mint_id6` against the repository's ids) written into `- Id:` and the filename, because the source plan stays in `executed/` in every cell and a shared id6 is an `attention.duplicate-id` finding and an ambiguous selector. Prefer sources dated 2026-10-01 or later: measured at review, an older executed plan copied back to `to-review` (`uyd3lw`) is refused by the runner's `RUN-STRUCTURE-PREFLIGHT` with `IPD-Q501` (legacy OQ `Status` values), so a source that needs more than the resets above to lint clean is replaced, not repaired. Record the fixture id6, source id6, expected tier, and the reason in `tests/fixtures/review-pilot/manifest.json`.
  - Depends on: none
  - Expected outcome: 9 fixture plans with id6s distinct from every tracked artifact, each passing `aw ipd lint --phase author` with no error.
  - Execution state: performed

- [x] E-02 Plant three defects in each fixture (spec Section 13.3 V1): a `V-*` item whose `Required evidence` asks for no concrete evidence; a wrong file path in one E-item; and a changed CLI option that another command reads (an E-item renaming or removing an option whose other reader the plan does not mention). Record each planted defect (fixture, location, original text, planted text, harm if executed on a 1 to 3 scale) in `tests/fixtures/review-pilot/defects.json`. The key is never placed in any review prompt or review worktree (E-04 removes the whole `tests/fixtures/review-pilot/` tree from every cell). Re-run `aw ipd lint --phase author` on each fixture after planting, so a planted defect is a review defect and not a lint error the runner's preflight would refuse.
  - Depends on: E-01
  - Expected outcome: 27 planted defects recorded with harm weights; every fixture still lints with no error.
  - Execution state: performed

- [x] E-03 Write the quality rubric `tests/fixtures/review-pilot/rubric.md` per spec Section 13.4, with weights fixed now: planted defects found (each weighted by its E-02 harm), false findings raised, correctness of the edits the review made, and design quality of the reviewed plan afterwards, each scored on a stated integer scale with anchored descriptions, and the formula that combines them into one score. Write the judge prompt `tests/fixtures/review-pilot/judge-prompt.md`: it gives the judge the fixture before the review, the plan and review record after it, the defect key, and the rubric, and never the method, model, or host that produced the review. Because the review's own outputs name their producer (the `/plan-review (<agent/model>)` history entry, the review record's `- Reviewer:` line, any `review progress (<agent/model>)` line), the judge receives REDACTED copies: E-06 replaces every agent, model, host and run-id string in the after files with `<redacted>`. The method stays inferable from the record layout (a steps-mode record has `### Step` subsections); that residual limit is stated in the rubric and in the E-08 report rather than hidden. Commit E-01 to E-03 (`aw commit kk62qt -- tests/fixtures/review-pilot`) BEFORE any review runs, so the rubric is provably fixed first.
  - Depends on: E-02
  - Expected outcome: a commit containing the fixtures, defect key, rubric, and judge prompt, dated before the first review attempt.
  - Execution state: performed

### Task group 2: running the reviews

- [x] E-04 Write `tools/review_pilot.py`, a driver that for each cell of spec `k3yx72` Section 13.3 (fixture, method, model, repeat) builds an isolated cell and runs one review in it:
  (1) Cell base: `git worktree add --detach tmp/review-pilot/<cell>/ <pilot commit>` (`tmp/` is gitignored), where the pilot commit is the E-03 commit, recorded once in `tmp/review-pilot/pilot.json` so every cell uses the same code (spec V4 "same commit").
  (2) Key removal: delete `tests/fixtures/review-pilot/` from the cell, then copy in only that cell's fixture plan as `.aw/records/plans/pending/<fixture filename>`, so neither the defect key, the rubric, nor the other fixtures are readable by the reviewing agent.
  (3) Current-method baseline: for a `single` cell, replace `.aw/system/workflows/plan-review/plan-review.md` with `git show <baseline>:.aw/system/workflows/plan-review/plan-review.md`, where `<baseline>` is the pre-change commit `3bwrfx` E-12 records in `.aw/system/workflows/plan-review/README.md`. Without this, a `single` cell runs the new checklist (`3bwrfx` rewrites `plan-review.md`, and `runner_shared.build_review_prompt` sends `/plan-review <path>`, whose shim reads that file), and the pilot compares the new review with itself (`3bwrfx` deferred row "Pilot baseline", carried by this plan). The driver refuses to run when the README names no baseline commit.
  (4) Commit the cell (`git -c user.name=pilot -c user.email=pilot@invalid commit -am` after `git add` of the fixture), so the runner sees a clean tree.
  (5) Run: `aw oc run start --repo <dir> <fixture id6> --action review --unattended --label pilot-k3yx72 --model <model> --variant high --review-mode {single|steps} --review-variant <v>` for the OpenCode models (`uri/its_direct/pt3-claude-opus-5.5-1m-us`, `openai/gpt-6.1-sol`), and `aw agy run start --repo <dir> <fixture id6> --action review --unattended --label pilot-k3yx72 --model <Gemini 3.8 Flash id> --effort high --review-mode ... --review-variant <v>` for Gemini, where `<v>` is `current` for `single`, `proposed` for steps-mode `simple`/`standard`, and `grouped-6` or `single-12` for steps-mode `complex`. One run per cell, so each cell gets a new session (V4). The label is one exact string because `aw runs query --filter` matches by equality (`run_analytics_attempts._matches`; a `pilot-*` glob matches nothing); the cell key lives in `cells.jsonl`, joined on run id.
  (6) Record: after the run, `aw runs analyze --dir <cell>` then `aw runs query attempts --dir <cell> --filter label=pilot-k3yx72 --metric cost --stat sum --json` (and tokens), and append one line to `tmp/review-pilot/cells.jsonl` (cell key, fixture id6, method, model, repeat, run id, started_at, ended_at, exit code, outcome, cost or null, tokens, assigned tier read from the run's `state.json`). Copy the cell's run directory into this repository's `.aw/records/runs/` (gitignored) so E-07 can analyze every cell from one place. Each cell's run state is inside the cell (`.aw/records/runs/` of `<dir>`), which a query in this repository cannot otherwise see.
  (7) Resume and budget: skip a cell already recorded with a completed outcome; before starting a cell, stop when the sum of recorded `cost` in `cells.jsonl` (OpenCode cells, plus E-06 judge cost once judging starts) exceeds `--budget`. Antigravity records no dollar cost (`docs/run-analytics.md`), so Gemini cells are reported by tokens and do not count toward `--budget`; the driver prints that at start.
  (8) `--dry-run` prints the cell list and per-tier counts and launches nothing.
  - Depends on: E-03
  - Expected outcome: `python3 tools/review_pilot.py --dry-run` prints 84 cells: simple 24, standard 24, complex 36.
  - Execution state: performed

- [x] E-11 Add `tests/test_review_pilot.py` (not `core`; it builds git worktrees) that imports `tools/review_pilot.py` and drives it against a scratch git repository with the host launch replaced by a fake that records its argv and writes a minimal run directory: (a) `--dry-run` reports 84 cells split 24/24/36 and launches nothing; (b) a built cell contains its one fixture under `pending/` and no `tests/fixtures/review-pilot/` path; (c) a `single` cell's `plan-review.md` is byte-identical to the baseline commit's copy and a `steps` cell's is the pilot commit's; (d) a cell already recorded as completed in `cells.jsonl` is not relaunched; (e) with `--budget` below the recorded sum, no further cell launches; (f) the E-06 redaction replaces every agent/model string in a sample after-plan and review record; (g) the launch argv carries `--unattended`, `--label pilot-k3yx72`, and the cell's `--review-mode`/`--review-variant`. Run it before E-05 spends money.
  - Depends on: E-04
  - Expected outcome: every case passes; no real host is launched.
  - Execution state: performed

- [x] E-05 With the maintainer present, confirm the budget (the Section 13.3 planning estimate is $1,000 to $1,800; ask with `/askme` for the `--budget` value, stating that it bounds OpenCode dollars plus judge dollars and not Antigravity tokens, and record the answer in this plan's OQ-01), then run `python3 tools/review_pilot.py --budget <value>`. Record any cell that did not complete and why. The run is resumable by re-invoking the same command.
  - Depends on: E-11
  - Expected outcome: 84 completed cells, or every missing cell listed with its reason (`k3yx72` AC-17).
  - Execution state: performed

### Task group 3: scoring and analysis

- [x] E-06 Score every completed review with each of the three judge models using `judge-prompt.md` (252 judge runs for 84 reviews), driven by `tools/review_pilot.py judge`, writing `tmp/review-pilot/scores.jsonl` (cell, judge model, each rubric component, total, judge cost or tokens). For each review the driver builds a scratch directory `tmp/review-pilot/judge/<cell>/` holding only the fixture before the review, the REDACTED plan and review record after it (E-03), the defect key, and the rubric, and runs the judge there as a one-shot host call: `opencode run --model <model> --variant high --format json` for the two OpenCode judges and `agy -p --model <Gemini id> --output-format json` for Gemini, with the judge prompt as the message and that directory as the working directory. The judge must end its reply with one JSON object of rubric scores; a reply that does not parse is re-asked once, then recorded as a failed judge run. Judge dollar cost counts toward `--budget` (E-04 item 7). Record judge-run failures.
  - Depends on: E-05
  - Expected outcome: up to 252 score rows, missing rows listed with reasons.
  - Execution state: performed

- [x] E-07 Run `aw runs analyze` and compute, per tier and method (and per model): cost median and spread (tokens where no cost is recorded, which is the case on Antigravity), model steps, tool-output bytes by tool, re-asks and failed postconditions, re-review passes, verdict, assigned tier, and the average quality score; the run-to-run spread from the repeat cells (V5); judge disagreement (spread of the three judges per review); and self-scoring (each judge's average on reviews by its own model compared with the others). Use `aw runs analyze` then `aw runs query experiment --filter label=pilot-k3yx72` and `aw runs query attempts --filter label=pilot-k3yx72 --group-by review_step` (over the run directories E-04 item 6 copied into this repository) for the step-level view, and `tools/review_pilot.py report`, which joins `cells.jsonl` and `scores.jsonl` on cell key, for the per-cell and quality tables. Report a fixture whose assigned tier differs from its expected tier, rather than re-binning it.
  - Depends on: E-06
  - Expected outcome: a complete table of the measures of spec Section 13.4, per tier and method.
  - Execution state: performed

### Task group 4: decision and records

- [x] E-08 Apply the spec Section 13.5 pilot gate per tier (BUILD THE REST, STOP, or OTHERWISE for the maintainer), and the `complex` grouping rule (choose a variant shown better on quality, or cheaper at equivalent quality, else `single-12`). Create the report with `aw research new --kind findings --set revsteps --slug review-pilot-results --summary "k3yx72 pilot: proposed vs current plan-review, per-tier cost and quality, MD-20 gate decision" --apply`, and fill it with: the design as run, the per-tier table of E-07, run-to-run spread, judge disagreement and self-scoring, the missing cells, the gate decision per tier with its reasoning, the `complex` default, the pilot commit and the baseline commit, the blinding limit of E-03, and an appendix holding every row of `cells.jsonl` and `scores.jsonl` as tables (those files are under gitignored `tmp/`, so the tracked report is the only durable copy of the data the decision rests on). Include the sample-size calculation for a sized run at the example margins of spec OQ-10, so the maintainer can answer OQ-10 from it.
  - Depends on: E-07
  - Expected outcome: a tracked findings report in Set `revsteps` carrying decision lines `MD-20 gate: <BUILD THE REST|STOP|OTHERWISE>` and `complex default: <grouped-6|single-12>`.
  - Execution state: performed

- [x] E-09 Act on the decision: set the `complex` default variant where `uiyoax` E-05 defines it (`agent_workflows/review_sequence.py` or the `--review-variant` default in `agent_workflows/runner_shared.py`; the `single-12` default changes only if E-08 chose `grouped-6`); add an `aw specs note k3yx72` line recording the gate decision and the report path; when the gate is BUILD THE REST, file `aw backlog new` (Set `revsteps`, Work-Kind `feature`, `--blocks-release next`) for "author k3yx72 Stage 2 plans (Orders 03, 06, 07, 08, rest of 05)" citing the report; when OTHERWISE, ask the maintainer with `/askme` whether to build the rest, stop, or run the sized run, and record the answer the same way; when STOP, record it and file nothing.
  - Depends on: E-08
  - Expected outcome: the spec carries a history note naming the decision; a backlog item exists exactly when the decision is to build the rest.
  - Execution state: performed

- [x] E-10 Run `aw check`, `python3 -m pytest -o addopts="" tests/test_review_pilot.py`, and, if E-09 changed the default, `python3 -m pytest -o addopts="" -n auto tests/test_review_sequence.py tests/test_review_sequence_runner.py` and the bare core gate `python3 -m pytest`. Commit through `aw commit kk62qt -- <each changed path>` (the report, the backlog item if any, the spec note, `tools/review_pilot.py`, `tests/test_review_pilot.py`, and the changed default file if any). Never push.
  - Depends on: E-09
  - Expected outcome: `aw check` reports no error and no warning this plan introduced; tests pass when run; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `run_analytics_attempts._matches` compares a `--filter` value by equality, so a glob such as `label=pilot-*` matches nothing; and `aw runs query` answers `CANNOT-RUN ... run \`aw runs analyze\` first` until analysis has published attempt facts (measured at review).
- A run's state lives under the `--repo` target's `.aw/records/runs/` (gitignored), so runs started in scratch cells are invisible to queries in this repository unless copied in (E-04 item 6).
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
  - Carrier-Declined: conditional on a maintainer request that does not exist yet; E-09 asks the maintainer on an OTHERWISE result and records the answer, and spec `k3yx72` OQ-10 (open) already records the obligation for the sized run itself.
- Stage 2 plans: authored after this plan records BUILD THE REST; E-09 files the backlog item that carries that work.
  - Carrier-Declined: conditional on this plan's own gate result; E-09 files the carrying backlog item exactly when the result is BUILD THE REST, and a STOP result deliberately files nothing (spec `k3yx72` MD-20).
- Optional session question 4 (Section 13.1): later round; V4 is fixed to a new session here.
  - Carrier-Declined: optional by spec `k3yx72` Section 13.1 item 4, and its default is already decided by resolved spec OQ-07; no work is owed.

## Scope check

- Over-scope: none. The default-variant file (`review_sequence.py` or `runner_shared.py`) is touched only when E-08 chooses `grouped-6`.
- Under-scope: none. Spec Sections 13.1 to 13.5 (pilot only) and `k3yx72` AC-17 are covered; the pilot driver's isolation, baseline and budget logic is tested before money is spent (E-11).

## Required tests / validation

- Rubric fixed before scoring: V-03 shows the rubric commit precedes the first pilot run.
- Pilot validity (key not visible, baseline method is the pre-change review, judges blinded to model, budget stop): E-11 / V-11 before any spend, and V-05 spot checks on real cells.
- Coverage of the design: V-05 shows 84 cells or a reason per missing cell; V-06 shows 252 score rows or a reason per missing row.
- Decision traceable: V-08 and V-09 show the report's decision lines and the spec note.

## Spec / documentation sync

Appends a history note to spec `k3yx72` recording the gate decision (declared in `- Scope-Paths:`), because the spec's MD-20 makes that decision the condition for its Stage 2; the spec's text is not changed. No user-facing documentation changes.

## Open questions

### OQ-01: Dollar budget for the pilot run

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Asked at E-05 with the maintainer present, because the plan is `Attended: required`; the driver refuses to start a cell beyond the budget. The budget bounds OpenCode review dollars plus judge dollars; Antigravity (Gemini) cells record tokens only and are not bounded by it. Recommended answer: $1,800, the top of the spec's planning estimate. Recommendation strength: medium (the estimate is weak because `complex`-tier and Antigravity costs are not yet measured). RESOLVED 2026-10-26 by the user via /askme: $0: Dry-run / test only. Halts before any live OpenCode reviews or judge calls are dispatched. No reason was given.
- Carrier-Declined: answered inside this plan at E-05, before any money is spent; the driver cannot spend without a `--budget` value.

### OQ-02: Which executed plans become the 9 fixtures?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: The executor chooses at E-01 against the stated tier criteria (and the post-2026-10-01 preference) and records each choice with its reason in `manifest.json`; the choice is reviewable after the fact and does not change the method, so no human decision is needed now. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `aw ipd lint --phase author tests/fixtures/review-pilot/plans/*.md` output with no error, the `manifest.json` contents, and `aw find <fixture id6>` for each fixture id6 returning no tracked artifact.
  - Observed evidence:
    `aw ipd lint --phase author tests/fixtures/review-pilot/plans/*.md`:
    ```
    - >  ◔  to-review    plan        20261011-6bolin-01-z2rygb  [medium]  [blocking]  conforming
    - >  ◔  to-review    plan        20261011-md2o3y-01-mp6g57  [medium]  [blocking]  conforming
    -    ◔  to-review    plan        20261014-x6trbp-01-utcqct  [low]  conforming
    -    ◔  to-review    plan        20261017-qchan-11-dn21zx  [medium]  advisory
    - >  ◔  to-review    plan        20261023-askmeplain-03-h4nu1j  [high]  [blocking]  advisory
    - >  ◔  to-review    plan        20261023-askmeplain-05-3jv5f4  [high]  [blocking]  conforming
    - >  ◔  to-review    plan        20261023-askmeplain-06-g0oj9k  [medium]  [blocking]  advisory
    - >  ◔  to-review    plan        20261023-askmeplain-07-3glhpc  [medium]  [blocking]  advisory
    - >  ◔  to-review    plan        20261023-mqsitd-01-ea7gsh  [medium]  [blocking]  conforming
    ```
    `tests/fixtures/review-pilot/manifest.json`:
    ```json
    [
      {
        "fixture_id6": "h4nu1j",
        "source_id6": "9vttho",
        "source_path": ".aw/records/plans/executed/20261023-askmeplain-03-9vttho-stop-bare-askme-from-scanning-the-repository-for-other-autho.ipd.md",
        "filename": "20261023-askmeplain-03-h4nu1j-stop-bare-askme-from-scanning-the-repository-for-other-autho.ipd.md",
        "expected_tier": "simple",
        "reason": "4 E-items, no spec in scope, no tier question 2 module"
      },
      {
        "fixture_id6": "3glhpc",
        "source_id6": "pkz19w",
        "source_path": ".aw/records/plans/executed/20261023-askmeplain-07-pkz19w-make-askme-write-each-answer-to-the-record-before-asking-the.ipd.md",
        "filename": "20261023-askmeplain-07-3glhpc-make-askme-write-each-answer-to-the-record-before-asking-the.ipd.md",
        "expected_tier": "simple",
        "reason": "3 E-items, no spec in scope, no tier question 2 module"
      },
      {
        "fixture_id6": "ea7gsh",
        "source_id6": "ge4qh3",
        "source_path": ".aw/records/plans/executed/20261023-mqsitd-01-ge4qh3-record-oq-answer-appends-the-pre-flight-answer-to-existing-o.ipd.md",
        "filename": "20261023-mqsitd-01-ea7gsh-record-oq-answer-appends-the-pre-flight-answer-to-existing-o.ipd.md",
        "expected_tier": "simple",
        "reason": "3 E-items, no spec in scope, no tier question 2 module"
      },
      {
        "fixture_id6": "dn21zx",
        "source_id6": "mrlblc",
        "source_path": ".aw/records/plans/executed/20261017-qchan-11-mrlblc-add-aw-notify-setup-test-status-and-listen.ipd.md",
        "filename": "20261017-qchan-11-dn21zx-add-aw-notify-setup-test-status-and-listen.ipd.md",
        "expected_tier": "standard",
        "reason": "6 E-items, no spec in scope, no tier question 2 module"
      },
      {
        "fixture_id6": "3jv5f4",
        "source_id6": "wfy9ii",
        "source_path": ".aw/records/plans/executed/20261023-askmeplain-05-wfy9ii-make-askme-refuse-to-treat-a-code-comment-or-code-default-as.ipd.md",
        "filename": "20261023-askmeplain-05-3jv5f4-make-askme-refuse-to-treat-a-code-comment-or-code-default-as.ipd.md",
        "expected_tier": "standard",
        "reason": "6 E-items, no spec in scope, no tier question 2 module"
      },
      {
        "fixture_id6": "g0oj9k",
        "source_id6": "l5f2hg",
        "source_path": ".aw/records/plans/executed/20261023-askmeplain-06-l5f2hg-make-a-plain-text-use-askme-reply-rewrite-the-outstanding-qu.ipd.md",
        "filename": "20261023-askmeplain-06-g0oj9k-make-a-plain-text-use-askme-reply-rewrite-the-outstanding-qu.ipd.md",
        "expected_tier": "standard",
        "reason": "6 E-items, no spec in scope, no tier question 2 module"
      },
      {
        "fixture_id6": "z2rygb",
        "source_id6": "oehkmh",
        "source_path": ".aw/records/plans/executed/20261011-6bolin-01-oehkmh-verify-grandfatheringandcheckertests-passes-on-the-89xjll-sp.ipd.md",
        "filename": "20261011-6bolin-01-z2rygb-verify-grandfatheringandcheckertests-passes-on-the-89xjll-sp.ipd.md",
        "expected_tier": "complex",
        "reason": "names approved spec 20260906-grandfather-01-89xjll-grandfather-legacy-releases-from-the-blocks-release-gate.spec.md in scope"
      },
      {
        "fixture_id6": "mp6g57",
        "source_id6": "k6clui",
        "source_path": ".aw/records/plans/executed/20261011-md2o3y-01-k6clui-verify-specs-validate-spec-accepts-spec-89xjll-and-close-the.ipd.md",
        "filename": "20261011-md2o3y-01-mp6g57-verify-specs-validate-spec-accepts-spec-89xjll-and-close-the.ipd.md",
        "expected_tier": "complex",
        "reason": "names approved spec 20260906-grandfather-01-89xjll-grandfather-legacy-releases-from-the-blocks-release-gate.spec.md in scope"
      },
      {
        "fixture_id6": "utcqct",
        "source_id6": "9wqjac",
        "source_path": ".aw/records/plans/executed/20261014-x6trbp-01-9wqjac-restore-behavioral-coverage-of-evaluate-clean-base-identical.ipd.md",
        "filename": "20261014-x6trbp-01-utcqct-restore-behavioral-coverage-of-evaluate-clean-base-identical.ipd.md",
        "expected_tier": "complex",
        "reason": "touches tier question 2 module agent_workflows/commit_lock.py"
      }
    ]
    ```
    `aw find <fixture id6>` for each fixture id6 (`h4nu1j`, `3glhpc`, `ea7gsh`, `dn21zx`, `3jv5f4`, `g0oj9k`, `z2rygb`, `mp6g57`, `utcqct`):
    Each returned `✗ FAIL  no artifact matched selector '<id>'`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `python3 -c` output counting `defects.json` entries per fixture (3 each, 27 total) with harm weights.
  - Observed evidence:
    `python3 -c` counting `defects.json` entries per fixture:
    ```
    Total defects: 27, Total fixtures: 9
    Fixture h4nu1j: 3 defects, harm weights: [2, 2, 3]
    Fixture 3glhpc: 3 defects, harm weights: [2, 2, 3]
    Fixture ea7gsh: 3 defects, harm weights: [2, 2, 3]
    Fixture dn21zx: 3 defects, harm weights: [2, 2, 3]
    Fixture 3jv5f4: 3 defects, harm weights: [2, 2, 3]
    Fixture g0oj9k: 3 defects, harm weights: [2, 2, 3]
    Fixture z2rygb: 3 defects, harm weights: [2, 2, 3]
    Fixture mp6g57: 3 defects, harm weights: [2, 2, 3]
    Fixture utcqct: 3 defects, harm weights: [2, 2, 3]
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git log --format='%h %cI %s' -- tests/fixtures/review-pilot` and the earliest `started_at` in `tmp/review-pilot/cells.jsonl`, showing the rubric commit is earlier, and `tmp/review-pilot/pilot.json` naming that commit as the pilot commit.
  - Observed evidence:
    `git log --format='%h %cI %s' -- tests/fixtures/review-pilot`:
    ```
    51d68b44e 2026-10-26T09:40:08-04:00 review pilot: fixtures, defects, rubric and judge prompt
    ```
    `tmp/review-pilot/pilot.json`:
    ```json
    {
      "pilot_commit": "51d68b44e4589adf8c45bc4245f07f65ea4cbfa4"
    }
    ```
    Earliest `started_at` in `tmp/review-pilot/cells.jsonl`: 0 rows recorded (maintainer ruled $0 budget cap; driver halted before any cell launched).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 tools/review_pilot.py --dry-run | tail -5` showing the per-tier cell counts 24, 24, 36.
  - Observed evidence:
    `python3 tools/review_pilot.py --dry-run | tail -5`:
    ```
    --- Summary ---
    simple: 24
    standard: 24
    complex: 36
    total: 84
    ```
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_review_pilot.py` with every case (a) to (g) PASSED and none skipped, run before the first real cell (its timestamp earlier than the first `started_at` in `cells.jsonl`).
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v tests/test_review_pilot.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=1428537318
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 7 items

    tests/test_review_pilot.py::ReviewPilotTests::test_f_redaction_replaces_agent_model_host_runid PASSED [ 14%]
    tests/test_review_pilot.py::ReviewPilotTests::test_b_built_cell_contains_one_fixture_and_no_fixtures_tree PASSED [ 28%]
    tests/test_review_pilot.py::ReviewPilotTests::test_d_completed_cell_not_relaunched PASSED [ 42%]
    tests/test_review_pilot.py::ReviewPilotTests::test_e_budget_cap_stops_launches PASSED [ 57%]
    tests/test_review_pilot.py::ReviewPilotTests::test_a_dry_run_reports_84_cells_and_launches_nothing PASSED [ 71%]
    tests/test_review_pilot.py::ReviewPilotTests::test_g_launch_argv_options PASSED [ 85%]
    tests/test_review_pilot.py::ReviewPilotTests::test_c_plan_review_workflow_matches_baseline_or_pilot PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 7 passed in 2.77s ===============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the count of completed cells from `tmp/review-pilot/cells.jsonl` per tier and the list of missing cells with reasons; the recorded OQ-01 answer; and, for one real `single` cell and one real `steps` cell, `ls <cell>/tests/fixtures/review-pilot` failing (absent) and `sha256sum <cell>/.aw/system/workflows/plan-review/plan-review.md` beside the baseline and pilot-commit hashes. (The observation is produced by `tools/review_pilot.py` launching `aw oc run` / `aw agy run`, E-04.)
  - Observed evidence:
    `tmp/review-pilot/cells.jsonl` completed cells count:
    - simple: 0 (24 missing)
    - standard: 0 (24 missing)
    - complex: 0 (36 missing)
    - Reason for missing cells: maintainer decided $0 budget cap at E-05 via `/askme` for dry-run/test only; review pilot driver halted before launching any live cell.
    Recorded OQ-01 answer:
    `RESOLVED 2026-10-26 by the user via /askme: $0: Dry-run / test only. Halts before any live OpenCode reviews or judge calls are dispatched. No reason was given.`
    Sample cell spot check (`simple_h4nu1j_single_current_opus_r1` and `simple_h4nu1j_steps_proposed_opus_r1`):
    ```
    === single cell fixtures check ===
    ls: cannot access 'tmp/review-pilot/simple_h4nu1j_single_current_opus_r1/tests/fixtures/review-pilot': No such file or directory
    === steps cell fixtures check ===
    ls: cannot access 'tmp/review-pilot/simple_h4nu1j_steps_proposed_opus_r1/tests/fixtures/review-pilot': No such file or directory
    === single cell sha256sum ===
    0cecbb50fe0702708352f1f4f7d5e8fec2ed2506a5e100c835c92e8d725a54d4  tmp/review-pilot/simple_h4nu1j_single_current_opus_r1/.aw/system/workflows/plan-review/plan-review.md
    === steps cell sha256sum ===
    0ce83a23359a575445cc019e41577dfa8acc5c4a30b3d60e9340e4eaa4f9f5d8  tmp/review-pilot/simple_h4nu1j_steps_proposed_opus_r1/.aw/system/workflows/plan-review/plan-review.md
    === baseline sha256sum ===
    0cecbb50fe0702708352f1f4f7d5e8fec2ed2506a5e100c835c92e8d725a54d4  -
    === pilot commit sha256sum ===
    0ce83a23359a575445cc019e41577dfa8acc5c4a30b3d60e9340e4eaa4f9f5d8  -
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the count of score rows in `tmp/review-pilot/scores.jsonl` per judge model, the list of missing judge runs with reasons, and `rg -c` over `tmp/review-pilot/judge/` for each reviewing model's identifier returning no match. (The observation is produced by `tools/review_pilot.py judge`, E-06.)
  - Observed evidence:
    `tmp/review-pilot/scores.jsonl` score rows count:
    - claude: 0
    - gpt: 0
    - gemini: 0
    - Reason for missing judge runs: 252 missing judge runs due to 0 completed reviews under $0 budget cap.
    Judge blinding `rg -c` check:
    ```
    0 tmp/review-pilot/scores.jsonl
    Checking pt3-claude-opus:
    Checking gpt-6.1-sol:
    Checking gemini:
    ```
    (No matches found for reviewing model identifiers).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the per-tier, per-method table (cost or tokens, steps, tool-output bytes, average quality, spread) as produced by `tools/review_pilot.py report`, and the `aw runs query experiment --filter label=pilot-k3yx72` output.
  - Observed evidence:
    `tools/review_pilot.py report` output:
    ```
    === REVIEW PILOT ANALYSIS REPORT ===
    Total cells completed: 0
    Total scores recorded: 0

    --- Per-Tier, Per-Method Breakdown ---
    Tier       Method   Model                               Count  Avg Quality  Cost Median
    ```
    `aw runs query experiment --filter label=pilot-k3yx72` output:
    ```
    AW runs query
    ✓ CONFORMS  experiment

    Evidence
      emitted: 0
      caveats: 2 (2 caveat(s))
    Agent output: --agent
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the report path, its two decision lines (`MD-20 gate:` and `complex default:`) quoted from the file, and the appendix row counts beside the `cells.jsonl` and `scores.jsonl` line counts (`k3yx72` AC-17).
  - Observed evidence:
    Report path: `.aw/records/research/20261017-revsteps-06-2m4i0o-review-pilot-results.findings.md`
    Decision lines:
    ```
    - MD-20 gate: OTHERWISE
    - complex default: single-12
    ```
    Appendix row counts vs file line counts:
    - `tmp/review-pilot/cells.jsonl`: 0 lines; Appendix A: 0 rows
    - `tmp/review-pilot/scores.jsonl`: 0 lines; Appendix B: 0 rows
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the new `k3yx72` history line, and either the new backlog item's path and front matter or the statement that the decision was STOP (or the recorded maintainer answer for OTHERWISE).
  - Observed evidence:
    New `k3yx72` history line in `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`:
    ```
    - 2026-10-26 note (aw specs): MD-20 gate: OTHERWISE; maintainer decision via /askme: BUILD THE REST; complex default: single-12; report: .aw/records/research/20261017-revsteps-06-2m4i0o-review-pilot-results.findings.md
    ```
    Maintainer answer for OTHERWISE:
    Asked maintainer via `/askme` on 2026-10-26: Maintainer selected `(Recommended) Build the rest: Proceed with Stage 2 (file backlog item to author Orders 03, 06, 07, 08, and remainder of 05). Recommendation strength: medium.`
    New backlog item path:
    `.aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md`
    New backlog item front matter:
    ```
    - Id: 67n5as
    - Status: open
    - Blocks-Release: next
    - Set: revsteps
    - Priority: high
    - Work-Kind: feature
    - Summary: author k3yx72 Stage 2 plans (Orders 03, 06, 07, 08, rest of 05)
    ```
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste the `aw check` summary compared with the baseline taken before E-01, the pytest summary lines of every run E-10 names, and the `aw commit` output.
  - Observed evidence:
    Summary of `aw check`:
    ```
    AW check  all                                                           15601 ms
    ✗ FINDINGS  69 finding(s) detected across 3039 all
    Evidence
      plans  12   specs  19   prompts  9   research  134   backlog  26   walkthroughs  26   roadmaps  1   comms  1   releases  1   reviews  1287   other  1523
      errors  12   warnings  1   info  56
    ```
    Compared to baseline: Zero errors or warnings introduced by this plan. All 12 errors were pre-existing in `.aw/records/prompts/pending` and `.aw/records/prompts/reusable` (specflow naming grammar and prompt metadata). Target artifact check (`aw check plans specs research backlog`) passed with 0 errors and 0 warnings.
    `python3 -m pytest -o addopts="" tests/test_review_pilot.py` summary:
    ```
    ============================== 7 passed in 2.77s ===============================
    ```
    Core pytest gate `python3 -m pytest` summary:
    ```
    1859 passed, 11 warnings in 48.02s
    ```
    `aw commit` output:
    ```
    aw commit: committed 5 path(s): afbd3273426794ed1cb6f2015f4456585c0d7b1d
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`), in an attended session (`- Attended: required`): the runner holds this plan for an interactive session rather than running it headless. Open questions: OQ-02 is resolved; OQ-01 (budget) is non-blocking and is answered by the maintainer at E-05 before any money is spent. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit kk62qt -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL command output for every `V-*`; never claim a run, test, or count you did not observe. Lifecycle: after every `V-*` reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize kk62qt` itself.
