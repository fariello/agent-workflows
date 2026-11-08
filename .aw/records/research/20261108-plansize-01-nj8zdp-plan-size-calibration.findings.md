---
id: nj8zdp
created: 20261108
set: plansize
order: 01
topic: [runner, ipd, sizing]
model: 
kind: findings
status: active
outcome: none-yet
summary: Calibrating IPD size caps against 425 runner execute turns: what predicts long or failed turns
consumed-by: []
---
# Findings: calibrating IPD size caps against runner history

Asked by the maintainer on 2026-11-08 after the metastore Set's step-complexity split, which used an uncalibrated cap of about 25 "units" per E-item. The question: what plan size actually predicts a long, retried or green-washed execute turn, measured on this repository's own runner history rather than guessed?

## Data

- Source: every runner session log under `.aw/records/runs/*/sessions/` (4,863 files), joined to the run's `state.json` queue to keep only `action: execute` turns. Result: 425 execute turns across 344 plans. Review and plan-authoring turns were excluded (1,431 and 608).
- Size, per plan, from its executed IPD file: E-item count, words in the E-items, Scope-Paths count, distinct code symbols named in E-items, total plan words.
- Actual change, per plan, from its own work commits (subject names the id6; `lifecycle(` and `.aw/` paths excluded): files touched, lines changed. 339 plans had attributable commits; 330 joined all three sources.
- Scripts and intermediate JSON were kept outside the repository (scratch); the method is reproducible from this description.

## What predicts turn length

Spearman rank correlation with the first execute attempt (330 plans):

| Measure | wall time | model steps | context at end |
|---|---|---|---|
| plan words | +0.59 | +0.54 | +0.22 |
| E-item count | +0.50 | +0.49 | +0.19 |
| E-item words | +0.50 | +0.44 | +0.16 |
| Scope-Paths count | +0.34 | +0.40 | +0.31 |
| lines changed | +0.27 | +0.20 | +0.25 |
| files changed | +0.22 | +0.20 | +0.24 |
| named symbols | +0.13 | +0.10 | +0.01 |

Size predicts length moderately; no measure predicts it strongly. Context at the end of a turn is weakly related to size.

Distribution (first attempt): wall time p50 37 min, p90 70 min, max 292 min; model steps p50 131; end context p50 244K, p90 405K tokens; E-items p50 5, p90 8.

## What predicts failure (the green-washing-relevant outcome)

First execute outcome by E-item count (327 plans with a recorded first finish):

| E-items | n | first turn finished cleanly `executed` |
|---|---|---|
| <= 3 | 65 | 66% |
| 4 to 5 | 111 | 62% |
| 6 to 7 | 94 | 60% |
| 8 or more | 57 | 40% |

Retried-or-over-90-minute rate by E-item count: 20% / 13% / 15% / 34% for the same bands (13 of 15 plans with more than 9 E-items failed or ran long). Plan word count shows no such cliff (56%, 52%, 56%, 65% clean across bands up to and over 11,000 words). The failure mode is item COUNT and item load, not prose length.

Scope-Paths: plans declaring more than 12 paths took longer (p50 58 min at 13 to 20 paths, 116 min above 20; small n) and retried more (29% at 9 to 12).

## The 7-hour turns were not caused by plan size

`2xwb9b` attempt 1 took 292 minutes for 98 model steps: 2.98 minutes per step against a corpus median of 0.28. It generated 9,362 output-plus-reasoning tokens per step against a corpus median of 793; 40 of its 98 steps reasoned more than 10,000 tokens, peaking at 28,051. The steps that reasoned longest were ordinary reads (`grep`, `sed -n`) of large modules, followed by deciding what to do next.

- Per-step time is NOT explained by context size: Spearman(end context, minutes per step) = +0.03 over 289 plans.
- The long-reasoning steps cluster in TIME: on 2026-11-06 from 04:00 to 10:00 UTC and on 2026-11-07 from 10:00 and 16:00 UTC, every turn running on `pt3-claude-opus-5.5-1m-us` with `variant: high` showed p90 reasoning of 12K to 19K tokens per step, including small review turns. Other hours on the same model and variant ran at 1K to 5K. The cause is unknown; the evidence points at the model/provider at those hours, not at the plans.
- The same model on the same night ran `1ajqaa` (10 E-items) at 1,458 tokens per step and 0.47 min per step.

So smaller plans reduce the blast radius of a slow period (less work lost to a stall, a retry carries less), but do not by themselves make a slow model fast.

## Green-washing proxy

Across 1,795 V-items in executed runner plans, 23% carry evidence that is a test pass count naming at most one unit; the median V-item names 1 unit (p75: 3). Evidence of that shape cannot show that every unit of an item was done.

## Calibrated caps (recommendation)

- E-items per plan: at most 5. Above 7 the first-turn clean rate drops from about 60% to 40%.
- Scope-Paths per plan: at most 8 (p90 of plans that finished cleanly in 45 minutes or less).
- Per E-item: one deliverable, about 1 file changed and about 200 lines (measured medians per E-item: 0.8 files, 171 lines; p90 1.9 files, 481 lines; 7 minutes, p90 12). An item whose measured units clearly exceed that is split.
- Evidence: each V-item names each unit it covers with its own mechanical check; a bare suite pass count is not sufficient evidence on its own.
- These caps target a first-attempt turn of about 30 to 45 minutes and the 60%+ clean band. They should be revisited after the next 50 execute turns.
