- Id: oboc47
- Status: open
- Set: rk25gap
- Priority: low
- Work-Kind: feature
- Summary: Build aw hooks install (spec 25kzda 2.10 names it as the user-facing hook install command)

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit of 25kzda (maintainer ruling: ungate the spec, file the unbuilt pieces as items).

Spec 25kzda Section 2.10 says the user-facing installation command for the opt-in dependency hook is `aw hooks install ipd-dependency-statement-gate`. At HEAD 5db4791c1 `aw hooks` is an invalid choice; hooks are wired via engine helpers. Either build the verb (covering every opt-in hook in agent_workflows/hooks/) or amend 25kzda 2.10 to name the real install path.
