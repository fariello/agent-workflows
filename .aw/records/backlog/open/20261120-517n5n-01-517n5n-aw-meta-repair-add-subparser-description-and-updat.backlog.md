- Id: 517n5n
- Status: open
- Set: 517n5n
- Work-Kind: bug
- Priority: medium
- Summary: aw meta repair: add subparser description and update REQUIRED_LEAVES count in test_usage_refusal_agent_record
- Short-Description: aw meta repair: add subparser description and update REQUIRED_LEAVES count in test_usage_refusal_agent_record
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): aw meta repair: add subparser description and update REQUIRED_LEAVES count in test_usage_refusal_agent_record

## Problem

IPD `a5ijjx` added `aw meta repair <id6>` in `agent_workflows/cli.py`, causing two thorough-tier tests on `main` to fail:

1. `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description` fails with `['meta repair: empty description']` because the `meta repair` subparser does not pass a `description=` string.
2. `tests/test_usage_refusal_agent_record.py::test_exclusion_set_size_and_members` fails with `assert 70 == 69` because adding `meta repair` (which takes required positional `id6`) increased `REQUIRED_LEAVES` from 69 to 70.

## Expected behavior

Add a descriptive `description=` parameter to the `meta repair` subparser in `agent_workflows/cli.py` and update `tests/test_usage_refusal_agent_record.py::test_exclusion_set_size_and_members` for the new leaf so both tests pass in `aw suite --thorough`.

## Discovery context

Observed on `main` (`b61073951`) during `aw suite --thorough` in IPD `ffceq0`.
