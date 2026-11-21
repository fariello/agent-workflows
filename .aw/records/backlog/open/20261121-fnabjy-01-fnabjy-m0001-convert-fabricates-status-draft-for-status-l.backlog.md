- Id: fnabjy
- Status: open
- Set: fnabjy
- Work-Kind: bug
- Priority: high
- Summary: m0001_convert fabricates status draft for status-less research-prompt and legacy research records causing attention.unknown-status and aw find status drift
- Short-Description: m0001_convert fabricates status draft for status-less research-prompt and legacy research records causing attention.unknown-status and aw find status drift
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): m0001_convert fabricates status draft for status-less research-prompt and legacy research records causing attention.unknown-status and aw find status drift


## Problem

`agent_workflows/migrations/m0001_convert.py::build_record_log` assigns `status = "draft"` whenever a `research` record has no `status` key in its front matter. Two groups of real records carry no research status:

1. Two-axis `research-prompt` records (8 tracked files in this repository: `8it88r`, `f79ve1`, `3nlmug`, `5ek188`, `nilw5h`, `q65sz3`, `ti73qs`, `bao493`), which intentionally omit hot status (`agent_workflows/attention.py::_research_record` states: "Two-axis research: prompts carry no hot status").
2. Legacy status-less research notes (such as `20260708-survey-notes.md` in `tests/migration_corpus.py::legacy_agents_layout`).

`"draft"` is not a member of `agent_workflows/research_contract.py::STATUSES` (`todo`, `active`, `reference`, `superseded`, `archived`). In addition, `agent_workflows/artifact_meta.py::parse_artifact_mirror` requires a strict two-key (`id` and `status`) front-matter mirror on every non-walkthrough and non-roadmap artifact, and `tests/test_m0001_review_conversion.py` asserts `st2.status == "draft"` for the `research-prompt` fixture `rs5002`.

Measured during IPD `60mazt` execution:

- On a disposable `git clone --no-hardlinks` of this repository: all 8 `research-prompt` records failed `aw attention --all --format json` after migration with `attention.unknown-status` (`research status 'draft'`), and failed spec `4sd62s` AC-42 item (5) `aw find --agent` parity (`"-"` before migration versus `"draft"` after migration; all other 4,923 records matched).
- On `legacy_agents_layout`: migrated `20260708-survey-notes.md` changed from `attention.missing-status` before migration to `attention.unknown-status` (`research status 'draft'`) after migration.

## Fix direction

1. Decide the metadata-v2 contract for status-less `research` records (`research-prompt` and legacy status-less research notes) under spec `4sd62s` (for example, omitting `status` in the checkpoint and permitting an `id`-only mirror for status-less research, or defining a valid status handling path across the mirror, log, and readers).
2. Update `agent_workflows/migrations/m0001_convert.py::build_record_log`, `agent_workflows/artifact_meta.py::parse_artifact_mirror` and mirror writers, `agent_workflows/migrations/m0001_verify.py`, `agent_workflows/attention.py::_research_record`, `agent_workflows/cli.py::_find_type_records`, and `tests/test_m0001_review_conversion.py` consistently.
3. Verify that all 8 `research-prompt` records in a disposable clone of this repository produce zero `attention.unknown-status` violations and preserve `aw find --agent` status parity before and after `aw migrate metadata --apply --force`.
