- Id: c4q9e8
- Status: done
- Graduated-To: c4q9e8
- Set: c4q9e8
- Priority: low
- Work-Kind: followup
- Summary: aw runs does not show discarded agent user-config changes recorded by a run

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD swpf3q executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-c4q9e8-01-swpf3q-surface-discarded-agent-user-config-changes-per-run-in-aw-ru.ipd.md); evidence .aw/records/plans/executed/20261014-c4q9e8-01-swpf3q-surface-discarded-agent-user-config-changes-per-run-in-aw-ru.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: swpf3q
- 2026-10-12 created (aw backlog): filed while graduating btw02e (plan 9y27t2)

## Context

Plan `9y27t2` (backlog `btw02e`) discards an agent turn's user-config writes and records each as an `agent-user-config-discarded` event in the run's `events.jsonl`, printing them at turn end and in the end-of-run report. `aw runs` (the cross-run view) does not show them, so an operator reviewing an old run later cannot see that an agent tried to change their config.

## Ask

Surface the count and keys of discarded user-config changes per run in `aw runs` (human and `--json`), reading the same durable events.

## Provenance
- From-Plan: 9y27t2
- Related: btw02e
