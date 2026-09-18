# IPD: Stop the analytics metric list advertising two metrics nothing computes and one that counts correctly-empty as missing

- Date: 2026-09-17
- Kind: child
- Concern: `aw runs query` offers seven metrics, two of which return nothing for every run ever recorded, and a third whose "missing" count is mostly not missing at all. Measured 2026-09-18 over 180 analyzed runs: `duration_seconds` and `event_count` each yield a sample size of ZERO for all 180 runs on BOTH hosts, because `run_analytics._metric_payload` never writes either key (verified: `duration_seconds` present in 0 of 180 cache entries, `event_count` in 0 of 180) even though the privacy allowlist permits both and 61 telemetry files carry a real `duration_seconds` value. Separately, `tokens` reports `missing_count` 3 of 5 on the Antigravity host and 29 of 174 on the OpenCode host, and I classified all 32: every one is CORRECTLY empty (19 no attempt dispatched, 3 orchestrate-only, 2 refused pre-launch by the clean-base gate, 4 running/interrupted with two 0-byte session files, 1 dependency-blocked, 1 no state.json). The decisive check found ZERO runs with a completed item, a non-empty session, and no tokens. So an operator reading these numbers sees three broken metrics where the truth is two unimplemented and one mislabelled.
- Scope: Make the metric surface honest in all three cases: compute the two missing metrics or remove them from the allowlist with the reason recorded, and separate "we failed to record this" from "there was nothing to record" in the missingness vocabulary. Does NOT change how any working metric is computed, does NOT change pricing or the cost caveat, and does NOT touch the report renderer.
- Scope-Paths: agent_workflows/run_analytics.py, agent_workflows/run_analytics_query.py, tests/test_run_analytics.py, tests/test_run_analytics_query.py
- Item-Dependencies: none
- Status: to-review
- Set: metgap
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 6krsym

## Workflow history

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored after the maintainer asked why tokens were missing from 3 of 5 Antigravity runs. INVESTIGATING THAT QUESTION PRODUCED TWO DIFFERENT FINDINGS, which is why this plan separates them rather than treating "three broken metrics" as one defect. The token answer is that nothing is broken: all 32 missing observations across both hosts are runs where no agent turn ever happened, and the decisive test (a completed item plus a non-empty session plus no tokens) returns ZERO cases. The real defects are next door: `duration_seconds` and `event_count` are in `AGGREGATE_METRICS` (`run_analytics_query.py:157`/`:160`) and in the privacy allowlist (`run_analytics_privacy.py:114`/`:169`), so they are advertised and permitted, but `_metric_payload` (`run_analytics.py:526`) never sets either, so `_numbers_for` (`:468`) counts every run as missing. Two metrics were shipped as reachable and are unreachable.

## Goal

Make every metric the query grammar offers either work or not be offered, and make a missing count mean
what an operator reads it as.

The measurement layer is sound and this plan must not re-open it: `wall_seconds` and
`observed_activity_seconds` are complete for all 180 runs on both hosts, tokens are complete for every
run that actually dispatched an agent, and the cost caveat already refuses to count an unpriced host as
zero. Three specific surfaces lie about that otherwise-honest corpus.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish what is measurable before changing any vocabulary

- [ ] E-01 RE-MEASURE THE THREE SURFACES AT EXECUTION HEAD, and refuse to proceed on this plan's figures. For each of the seven metrics in `AGGREGATE_METRICS`, report the sample size and missing count across the whole cached corpus, grouped by `host_kind`. Then state, per metric, whether any cache entry carries the key at all. This is the measurement that separates "the producer never writes it" from "the corpus happens to lack it", and the two need different fixes.
  - Depends on: none
  - Expected outcome: a pasted per-metric table (metric, entries carrying the key, sample size, missing count, per-host split) produced at execution HEAD, with the two zero-coverage metrics named explicitly.
  - Execution state: pending

- [ ] E-02 DETERMINE WHETHER `duration_seconds` IS DERIVABLE, because that decides E-04 and is a measurement rather than a preference. Three candidate sources, each to be checked and reported: the telemetry stream already writes it (`run_analytics_telemetry.py:1343` sets `payload["duration_seconds"]`, and 61 telemetry files carry a value, one measured at 1246.461919); `Fact` already carries `started_at`/`ended_at`, which `_metric_payload` already emits; and `wall_seconds` already exists and may make the metric redundant. Report which source is authoritative and whether `duration_seconds` differs in MEANING from `wall_seconds` (if it does not, the honest fix is removal, not computation).
  - Depends on: E-01
  - Expected outcome: a written determination naming the authoritative source or the redundancy, with the telemetry field's own definition quoted and its relationship to `wall_seconds` stated.
  - Execution state: pending

- [ ] E-03 DETERMINE WHETHER `event_count` IS DERIVABLE from what Order 02's envelope already holds. The cache entry carries an `event_facts` LIST beside `metric_facts`, so a per-run event count may be a length rather than a new measurement. Check whether `event_facts` is populated for the runs that have telemetry, and whether a count over it is meaningful (a run with no telemetry has no events to count, which is a correctly-empty case and must not become a zero).
  - Depends on: E-01
  - Expected outcome: a written determination of whether `event_count` can be derived from `event_facts`, with the populated/unpopulated split measured across the corpus.
  - Execution state: pending

### Task group 2: make each metric either work or not be offered

- [ ] E-04 RESOLVE `duration_seconds` per E-02's finding, and do exactly one of two things rather than splitting the difference. If it is a distinct, derivable quantity, compute it in `_metric_payload` and omit it when absent (never zero-fill: that function's own docstring states "every absent value is OMITTED rather than zero-filled, which is what keeps the persisted form from asserting a count nobody observed"). If it is redundant with `wall_seconds`, REMOVE it from `AGGREGATE_METRICS` and record why in a comment at the removal site, so the next reader does not re-add it. Do NOT leave it advertised and uncomputed, which is today's state and the defect.
  - Depends on: E-02
  - Expected outcome: either a computed metric with a nonzero sample size across the corpus, or a removed metric with the redundancy recorded at the site; the pasted before/after sample size either way.
  - Execution state: pending

- [ ] E-05 RESOLVE `event_count` per E-03's finding, on the same do-one-or-the-other rule as E-04. If it is derivable from `event_facts`, compute it and omit it for a run with no events rather than reporting zero. If it is not, remove it from the allowlist with the reason recorded.
  - Depends on: E-03
  - Expected outcome: either a computed metric with a nonzero sample size, or a removed metric with the reason at the site; the pasted before/after either way.
  - Execution state: pending

### Task group 3: stop reporting correctly-empty as missing

- [ ] E-06 SEPARATE THE TWO KINDS OF ABSENCE in the missingness vocabulary, which is the surface that produced the maintainer's question. `_numbers_for` returns one `missing` count that folds together a value the producer failed to record and a value that could not exist because no agent turn happened. The distinction is already available: a run whose queue holds only an `orchestrate` action, a run refused by the clean-base gate before launch, a run with no attempt dispatched, and a run still `running`/`interrupted` all legitimately have no tokens. Report them apart. THE PRECEDENT TO FOLLOW IS IN THIS SAME LAYER: the data-quality view already separates "a field an older driver never wrote (unavailable)" from other gaps, and the cost caveat already states that excluded observations are "not counted as zero". Extend that discipline to the token metric rather than inventing a third vocabulary.
  - Depends on: E-01
  - Expected outcome: the token metric's absences reported in at least two classes (not-recorded versus nothing-to-record) with the per-class counts, and the existing `missing_count` field's meaning either preserved or its change documented for the agent record's consumers.
  - Execution state: pending

- [ ] E-07 PROVE THE HONEST NUMBERS AGAINST THE CLASSIFIED CORPUS, since the point of E-06 is that the current numbers mislead. For the token metric, show that the runs counted as nothing-to-record are exactly the ones with no dispatched agent turn, and that no run with a completed item and a non-empty session appears in either absence class. That last assertion is the load-bearing one: it is what proves no genuine token loss is being excused by the new vocabulary.
  - Depends on: E-06
  - Expected outcome: pasted counts per absence class, plus the explicit zero-result check that no completed-item-with-session run lacks tokens; a nonzero result there is a FINDING, not a rounding detail.
  - Execution state: pending

## Project conventions discovered (Step 0)

- OMIT, NEVER ZERO-FILL. `_metric_payload`'s docstring states the rule: "every absent value is OMITTED rather than zero-filled, which is what keeps the persisted form from asserting a count nobody observed." Any computation added by E-04 or E-05 must follow it, and a run with nothing to count must produce no key rather than a zero.
- ABSENCE IS ALREADY A FIRST-CLASS CONCEPT HERE. `_numbers_for`'s docstring: "an absent value is not zero: Order 05's four-state provenance exists for that distinction, and folding missingness into the sample would silently strengthen every statistic computed from it." So the layer already knows the distinction E-06 needs; it just publishes one count.
- THE COST CAVEAT IS THE MODEL TO COPY. The query layer already emits "35 of 180 observations had no value for this metric and were EXCLUDED, not counted as zero" for cost. That is the honest shape, and it is why the unpriced Antigravity host reads correctly rather than as free.
- THE PRIVACY PROJECTOR IS A BOUNDARY, NOT A FILTER. `_metric_payload` "deliberately does NOT sanitize anything: the projector is the boundary, and a filter here would be a second one." `duration_seconds` is already in `ALLOWED_METRIC_KEYS` and `ALLOWED_EVENT_KEYS`, so nothing needs widening for E-04; the gap is purely that the producer never emits it.
- `median` IS THE DEFAULT STATISTIC ON PURPOSE. Order 06 measured a right-skewed attempt-cost distribution (max 54.50 USD against a median of 11.79) and chose median because "a mean over that reads as a typical value while being none." Any new metric inherits that default and must not assume symmetry.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `run_analytics.py:526` (`_metric_payload`) | **`duration_seconds` IS ADVERTISED AND NEVER PRODUCED.** It appears in `AGGREGATE_METRICS` (`run_analytics_query.py:157`) and in the privacy allowlist (`run_analytics_privacy.py:114`, `:169`), but `_metric_payload` sets `run_id`, `phase`, `driver_generation`, `host_kind`, `status`, optionally `set_id`/`ipd_id6`/`position`/`attempt`/`model`/`started_at`/`ended_at`, tokens and cost, and never this key. So `_numbers_for` counts EVERY run as missing. | measured: `duration_seconds` present in 0 of 180 cache entries; sample size 0 for all 180 runs on both hosts |
| F2 | HIGH | same | **`event_count` IS ADVERTISED AND NEVER PRODUCED,** the same shape as F1. | measured: present in 0 of 180 cache entries; `metric_facts` keys are exactly `driver_generation, ended_at, host_kind, model, observed_activity_seconds, overlap_seconds, phase, quality_flags, run_id, started_at, status, token_total, tokens, unattributed_seconds, wall_seconds` |
| F3 | MEDIUM | telemetry vs the cache | **THE DATA FOR `duration_seconds` EXISTS AND IS NOT INGESTED.** `run_analytics_telemetry.py:1343` writes `payload["duration_seconds"]`, and 61 telemetry files carry a value (one measured at 1246.461919 seconds). So this is an ingestion gap rather than an unmeasurable quantity, which is what makes E-04's "compute it" branch live rather than theoretical. | `grep -l duration_seconds .aw/records/runs/run-*/telemetry/*` returns 61 files |
| F4 | MEDIUM | `run_analytics_query.py:468` (`_numbers_for`) | **A MISSING COUNT CONFLATES TWO OPPOSITE FACTS.** One `missing` integer covers both "the producer failed to record this" and "there was nothing to record". Measured on tokens: 32 absences across both hosts, and ALL 32 are the second kind. | classification of all 32: 19 no attempt dispatched, 3 orchestrate-only, 2 refused pre-launch, 4 running/interrupted, 1 dependency-blocked, 1 no state.json |
| F5 | MEDIUM | the same 32 | **THERE IS NO GENUINE TOKEN LOSS, WHICH IS THE FINDING THAT SIZES THIS PLAN.** The decisive check (a completed item, a non-empty session, and no token total) returns ZERO runs. Two of the four running/interrupted cases have 0-byte session files. So the corpus is complete for every run that dispatched an agent, and only the LABEL is wrong. | pasted zero-result check across all 180 entries |
| F6 | LOW | Antigravity specifically | AGY IS NOT SKIPPED AND NEEDS NO CHANGE, recorded because it was the maintainer's initial hypothesis. `wall_seconds` and `observed_activity_seconds` are complete for 5 of 5 agy runs; tokens are present for both agy runs that dispatched an agent; only `cost` is empty, correctly, since Gemini publishes no per-token price. | per-host measurement across the corpus |
| F7 | LOW | scope | THE REPORT RENDERER IS NOT IN SCOPE. A separate change (2026-09-18) wired Order 07's SPA into publication, so the report now renders these metrics faithfully, INCLUDING their emptiness. Fixing the metrics improves that report without touching it. | `run_analytics_cli._render_report_html` |

## Proposed changes (ordered, validatable)

1. Re-measure all seven metrics per host at execution HEAD, naming which keys no cache entry carries (E-01).
2. Determine whether `duration_seconds` is distinct from `wall_seconds` or redundant with it (E-02), and whether `event_count` is derivable from `event_facts` (E-03).
3. Compute or remove `duration_seconds`, recording the reason at the site either way (E-04).
4. Compute or remove `event_count` on the same rule (E-05).
5. Split the missingness vocabulary so nothing-to-record is not reported as not-recorded (E-06).
6. Prove the new numbers against the classified corpus, including the zero-result loss check (E-07).

## Deferred / out of scope (with reason)

- HOW ANY WORKING METRIC IS COMPUTED. `wall_seconds`, `observed_activity_seconds`, `tokens`, `token_total` and `cost` are complete and correct for the runs that have them; this plan changes their REPORTING vocabulary at most, never their arithmetic.
- PRICING AND THE COST CAVEAT. Already honest, and the model this plan copies. The unpriced-host case needs no fix: Gemini publishes no per-token price, so there is no rate card to apply, and the caveat already refuses to report a false zero.
- THE REPORT RENDERER. Wired separately on 2026-09-18. It renders whatever the metrics say, so it improves for free and must not be edited here.
- BACKFILLING HISTORICAL RUNS. If E-04 makes `duration_seconds` computable, older cache entries still lack it until re-analyzed. `aw runs analyze --rebuild` already exists for that and needs no change; whether to rebuild is the operator's call, not this plan's.
- ADDING NEW METRICS. Out of scope. This plan makes the existing seven honest; a new one is a separate design question.

## Scope check

- Over-scope: none. Three named surfaces in two modules plus their tests.
- Under-scope: none for the reported defects. Backfill and the renderer are deferred above with reasons.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). The gate is no NEW failures.
2. For each metric E-04/E-05 COMPUTES: a pasted nonzero sample size across the real corpus, and a run with nothing to count shown producing NO key rather than a zero.
3. For each metric E-04/E-05 REMOVES: a pasted refusal from `aw runs query` naming it as not a valid metric, and the reason comment quoted from the removal site.
4. E-07's zero-result check: no run with a completed item and a non-empty session lacks tokens. This is the assertion that proves the new vocabulary excuses nothing.
5. The absence classes' counts shown summing to the previous single `missing` count, so the split is a partition rather than a re-measurement.
6. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change expected: the metric list is a query-grammar allowlist rather than a spec-defined
contract, and `- Scope-Paths:` declares no `.spec.md`. TWO THINGS THE EXECUTOR MUST CHECK RATHER THAN
ASSUME. First, if spec `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` enumerates the
queryable metrics, then REMOVING one is a contract change: declare that spec in `Scope-Paths` before
editing it, per the spec-amendment rule, and record the reason here. Second, `aw runs query --help` and
the `schema` view both advertise the metric list; if E-04 or E-05 removes a metric, both must stop
advertising it in the same change, or the help will promise something the grammar refuses.

## Open questions

### OQ-01: If `duration_seconds` turns out to be redundant with `wall_seconds`, remove it or keep it as an alias?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because E-02 measures the relationship first and E-04 implements REMOVAL by default, which is the honest direction and is trivially reversible. FOR REMOVAL: a metric that duplicates another under a second name doubles the surface an operator must understand and invites the question of why the two disagree when one is empty. FOR AN ALIAS: an external consumer may already query `duration_seconds` by name, and refusing a name that used to be accepted is a breaking change to the query grammar even though it never returned data. Recorded because it is a public-contract call, and because the answer depends on E-02's measurement, which does not exist yet.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted per-metric table at execution HEAD covering all seven metrics in `AGGREGATE_METRICS`, each with entries-carrying-the-key, sample size, missing count, and the per-`host_kind` split. The two zero-coverage metrics must be named explicitly rather than left for the reader to spot. A table without the entries-carrying-the-key column does NOT satisfy this item: that column is what distinguishes an unwritten key from an empty corpus.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the written determination for `duration_seconds` quoting the telemetry field's own definition and stating whether it differs in MEANING from `wall_seconds`. If the finding is redundancy, the two values must be compared on at least one real run to show they measure the same thing; if distinct, the difference must be stated in one sentence an operator would understand.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the measured populated/unpopulated split of `event_facts` across the corpus, and the written determination of whether a count over it is meaningful. Explicit statement that a run with no telemetry yields NO key rather than a zero.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: EITHER a pasted nonzero sample size for `duration_seconds` over the real corpus plus a run with no value shown omitting the key entirely, OR the pasted `aw runs query` refusal of the removed metric plus the reason comment quoted from the removal site. A half-state (still advertised, still uncomputed) fails this item, since that is the defect.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the same two-branch evidence for `event_count`, on the same rule: computed with a nonzero sample and an omitted-not-zero case, or removed with its refusal and its reason quoted.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the token metric's absences pasted in their classes with per-class counts, AND those counts shown to SUM to the single `missing` count the same query reported before the change. The sum is what proves this is a partition of the same population rather than a new measurement. PLUS a statement of whether the `missing_count` field in the agent record changed meaning, and if so, what a consumer must do.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted zero-result check showing NO run has a completed item, a non-empty session, and no token total. Paste the check itself, not only its verdict, because a check that silently matched nothing would produce the same clean answer as a correct one. If the result is nonzero, paste it and record it as a finding rather than adjusting the classes to absorb it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (7 E-items in 3 task groups, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute with REMOVAL if E-02 finds
redundancy, and do not invent an alias. SCOPE FENCE: this plan declares two analytics modules and their
two test files; an out-of-scope edit must be made only if genuinely required and then JUSTIFIED to
`aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a
`--scope-ack`. THE THREE THINGS THIS PLAN MUST NOT DO, each stated because each is a shortcut to a
green test. FIRST, do not ZERO-FILL a metric to make its sample size nonzero: `_metric_payload`'s own
docstring forbids it, and a zero asserts a count nobody observed. SECOND, do not leave a metric
advertised and uncomputed, which is today's state; E-04 and E-05 each demand one of two outcomes and a
half-state fails their V-items. THIRD, do not let E-06's new absence classes absorb a genuine gap: V-07's
zero-result check exists precisely so a real token loss cannot be relabelled as nothing-to-record, and a
nonzero result there is a FINDING to report rather than a class to widen. THE HARD-MUST HONESTY RULE:
paste the ACTUAL command and query output for every `V-*`; never claim a measurement not taken, and
paste the check itself where a V-item asks for it, because a check that matched nothing looks identical
to a check that passed. Commit path-scoped (`git commit -m msg -- <paths>`); never `git add -A`; never
push. Before every commit run `git diff --cached --name-only` and unstage anything not yours; this is a
shared checkout with concurrent sessions. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
