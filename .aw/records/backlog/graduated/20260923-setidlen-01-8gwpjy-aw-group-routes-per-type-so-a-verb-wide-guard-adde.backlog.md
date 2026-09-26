- Id: 8gwpjy
- Status: graduated
- Graduated-To: grouptest
- Blocks-Release: next
- Set: setidlen
- Priority: medium
- Work-Kind: bug
- Summary: aw group routes per type, so a verb-wide guard added only to artifact_rename misses the plans and research backends

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set grouptest (commit 2c7068ca).
- 2026-09-23 created (aw backlog): aw group routes per type, so a verb-wide guard added only to artifact_rename misses the plans and research backends

## What is wrong

`aw group` LOOKS like one verb with one backend, and it is not. `artifact_types.py` routes it PER
TYPE: `plans` -> `plans_refs.run_set_assign` (`artifact_types.py:79`), `research` ->
`research_refs.run_set_assign` (`:86`), and everything else (`specs`, `prompts`, `backlog`,
`walkthroughs`, `roadmaps`, `releases`, `other`) -> `artifact_rename.run_group_generic`
(`:92`-`:118`).

So any policy check added to `run_group_generic` alone silently EXEMPTS the two most heavily used
trees, and the omission is hard to see because a spot check of `aw group specs` shows the guard
working.

## Why this is a bug rather than a refactor note

MEASURED while executing plan `x75obw` (2026-09-23). That plan's E-06 declared
`agent_workflows/artifact_rename.py` as the home of `aw group` (a path its review had already
corrected once, after finding `artifact_cli.py` does not exist). Implementing it there produced a
guard that refused an over-length `--set` on `aw group specs` while `aw group plans` and
`aw group research` still ACCEPTED one. It was closed in that plan by adding the same shared
validator to both `run_set_assign` entry points, at the cost of a scope widening.

The general defect remains: the next verb-wide policy added to `aw group` will hit the same trap,
and nothing detects it. The three backends also do not share a common front-door where argument
validation could live once.

## Suggested direction (not a design decision)

Either give `aw group` ONE shared pre-dispatch validation seam that every backend passes through, or
add a test that asserts, for EVERY type in `artifact_types`, that `aw group <type>` enforces the
checks the verb claims to enforce. The second is cheaper and would have caught this one.
