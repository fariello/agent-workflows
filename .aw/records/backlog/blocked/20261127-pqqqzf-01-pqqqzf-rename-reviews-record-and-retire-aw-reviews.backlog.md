- Id: pqqqzf
- Status: blocked
- Set: pqqqzf
- Work-Kind: followup
- Priority: medium
- Summary: Relocate and rename aw reviews record (for example to aw meta log-review) and remove top-level aw reviews before 2.0.0
- Short-Description: Relocate and rename aw reviews record (for example to aw meta log-review) and remove top-level aw reviews before 2.0.0
- Blocks-Release: f33nrj
- Gate-Kind: artifact
- Gate-Ref: cxxmyv

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 created (aw backlog): Filed during p06t7i review (g-2e41f7b9dfa2e5dc) so p06t7i can keep aw reviews record intact through the metastore cutover (cxxmyv) and retire top-level aw reviews cleanly before 2.0.0.

## Problem

Plan `p06t7i` (Set `cliverbs`, Order 02) retires `aw reviews decisions` in favor of `aw show review-decisions`, but must leave top-level `aw reviews` alive solely for `aw reviews record` so it does not conflict with the pending `metastore` cutover plan `cxxmyv` and `.aw/system/cutover/metastore-docs.cutover.patch`.

Keeping `aw reviews record` at top level in 2.0.0 creates two command-surface defects:

1. Plural `aw reviews` (a low-level metadata log writer) sits next to singular `aw review` (the Order 03 AI review runner from `xocj8i`).
2. The name `aw reviews record` is noun/verb ambiguous ("a review record" vs. "to record a review") and does not clearly communicate that it appends a structured review-round event to an artifact's schema-2 metadata log (primarily invoked by `/plan-review` and `/spec-review` workflows).

## Desired outcome

Once the `metastore` cutover (`cxxmyv`) lands and before 2.0.0 (`f33nrj`) ships:

1. Choose and document a clear, unambiguous home for the schema-2 review-event writer implemented in `agent_workflows/reviews.py::run_record` (recommended candidate: `aw meta log-review` or `aw meta record-review`, placing plumbing under `aw meta` rather than a top-level human verb).
2. Remove the top-level `aw reviews` parser and dispatch path from `agent_workflows/cli.py`, leaving singular `aw review` as the only review command at top level.
3. Update all references in approved specification `4sd62s` (Sections 4.1a and 4.2), `agent_workflows/cli.py`, `agent_workflows/reviews.py`, workflow prompts (`.aw/system/workflows/`), `tests/test_reviews_record_walkthrough_new.py`, `tests/test_usage_refusal_agent_record.py`, and user-facing docs under `docs/`.

## Acceptance criteria

- Running `aw reviews` exits 2 as an unrecognized command and `aw --help` lists no top-level `reviews` command.
- The relocated command (for example `aw meta log-review` or `aw meta record-review`) passes all existing behavioral tests from `tests/test_reviews_record_walkthrough_new.py` and `tests/test_usage_refusal_agent_record.py` with zero regressions.
- Zero stale `aw reviews record` references remain across `agent_workflows/`, `.aw/system/workflows/`, `tests/`, and `docs/`.
- `python3 -m pytest`, `python3 -m mypy`, `aw attention --check`, and `aw sanitize --agent` pass cleanly.
