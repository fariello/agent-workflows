- Id: k899rl
- Status: open
- Set: rk25gap
- Priority: medium
- Work-Kind: feature
- Summary: Build tracked .prompt.md dispatch and the Run contract parser from spec 25kzda 3.5/4.10

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit of 25kzda (maintainer ruling: ungate the spec, file the unbuilt pieces as items).

Spec 25kzda Section 3.5 makes a tracked `.prompt.md` a runnable work item with an optional `## Run contract` section (Scope-Paths, Change-Policy, Expected-Paths, Check-Recipes, Commit), the `run unverifiable` phrase, and `--allow-unverifiable`/`--unverifiable-ok` handling; Section 4.10 gives its verification checklist. Not built at HEAD 5db4791c1: `runner_shared.queue_artifact_path` raises for type `prompt`, spec z7nbn1 Section 7 excluded prompt dispatch, and no Run-contract parser exists. Depends on the check-recipe registry format (25kzda 6.2), which is undecided.
