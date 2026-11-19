- Id: vo0y6q
- Status: graduated
- Graduated-To: vo0y6q
- Set: vo0y6q
- Work-Kind: bug
- Priority: medium
- Summary: aw backlog new --apply against a records_backend=home target repo creates .aw/state/locks/meta-*.lock inside target instead of AW_HOME
- Short-Description: aw backlog new --apply against a records_backend=home target repo creates .aw/state/locks/meta-*.lock inside target instead of AW_HOME
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-19 graduated (aw backlog): graduated by run run-20261119T154304Z-4175732: rntx9a
- 2026-11-17 created (aw backlog): aw backlog new --apply against a records_backend=home target repo creates .aw/state/locks/meta-*.lock inside target instead of AW_HOME

## Problem

Observed on `main` (`8a1bdc631`) in `tests/test_records_root_accessor.py::test_home_records_reproduction_backlog`:

- Running `aw backlog new --apply --dir <target>` against a repository with `records_backend: "home"` in `.aw/config/project.json` creates `<target>/.aw/state/locks/meta-<id6>.lock`.
- Because no `.aw/.gitignore` exists in the fixture, `git status --porcelain --ignored` reports `?? .aw/state/` in `<target>`, failing the assertion that the target working tree remains clean.

## Acceptance criteria

- When `records_backend` resolves to `home` (`AW_HOME`), backlog creation places its metadata lock under the resolved `AW_HOME` state directory rather than `<target>/.aw/state/`.
- `tests/test_records_root_accessor.py::test_home_records_reproduction_backlog` passes.
