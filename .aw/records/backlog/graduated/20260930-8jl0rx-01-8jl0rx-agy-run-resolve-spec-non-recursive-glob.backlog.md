- Id: 8jl0rx
- Status: graduated
- Graduated-To: 8jl0rx
- Blocks-Release: next
- Set: 8jl0rx
- Priority: high
- Work-Kind: bug
- Summary: Fix non-recursive spec resolution in agy_run.resolve_spec

## Workflow history
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: a6ootg
- 2026-09-30 created (aw backlog): Fix non-recursive spec resolution in agy_run.resolve_spec

`agy_run.resolve_spec` enumerates candidate specifications with non-recursive `d.glob("*.md")` over `.agents/docs/specs` and `.aw/records/specs`. Following the `specdirs` migration (`2fa65732`) which moved specifications into status subdirectories (`draft/`, `approved/`, `implemented/`, `superseded/`), the non-recursive glob sees only `README.md` at the specs root and resolves zero of the repository specifications.

Measured at authoring HEAD: calling `resolve_spec` raised `No specification matching ... found` for a bare filename, for a bare id6 (`pqsx96`), and for a flat-looking full path, breaking `aw agy exec --spec` / Spec Mode for every specification in the repository.

Fix precedent:
`specs._spec_files` already solved this exact issue. Crucially, its docstring records that `rglob` alone is not the complete fix: non-recursion previously masked the lack of an ignored-path filter, so a recursive walk must also filter candidate paths through `core.is_ignored_path`/`core.get_ignored_dirs` to prevent returning gitignored specs.

Why the prior audit missed this:
Executed plan `y4bdoz` ("Make every spec reader recursive") asserted "A package-wide grep ... finds exactly ONE non-recursive site, `specs.py:89`". However, `tools/agy_run.py` existed since `1ca197c7` (2026-08-16) and graduated into `agent_workflows/agy_run.py` at `4579ba87` (2026-08-28), both prior to `y4bdoz` 2026-09-10 review. The grep was incomplete, and `resolve_spec` has zero test coverage (no tests reference the symbol), allowing the breakage to go undetected.
