- Id: s4pys7
- Status: graduated
- Graduated-To: s4pys7
- Set: s4pys7
- Priority: low
- Work-Kind: followup
- Summary: Agent turns can still write the operator's AW_HOME (registry, caches): decide what to contain now that user config is contained

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: 1vwjdl
- 2026-10-12 created (aw backlog): filed while graduating btw02e (plan 9y27t2)

## Context

Plan `9y27t2` (backlog `btw02e`) contains an agent turn's writes to the operator's user CONFIG directory via `AW_CONFIG_DIR`. It deliberately does NOT redirect `AW_HOME` (the home records backend, project registry and run-analytics caches under `~/.aw/projects/`), because redirecting it would break a `records_backend: home` project, whose records live there and which the agent must be able to write. An agent turn can therefore still mutate `AW_HOME` state outside its lane.

## Ask

Decide which `AW_HOME` writes an agent turn legitimately needs (records for the home backend) versus incidental ones (registry, caches), and contain the incidental ones, or record a ruling that `AW_HOME` stays shared. Measure first: list what a normal execute turn writes under `AW_HOME`.

## Provenance
- From-Plan: 9y27t2
- Related: btw02e
