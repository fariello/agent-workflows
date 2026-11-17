- Id: o72vjz
- Status: open
- Set: metastore
- Work-Kind: bug
- Priority: medium
- Summary: Add graduated_to and from_plan to REGISTRY['spec'] in artifact_meta
- Release-Exempt-Kind: artifact
- Release-Exempt-Ref: 4sd62s

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-17 created (aw backlog): Add graduated_to and from_plan to REGISTRY['spec'] in artifact_meta

Spec 4sd62s Section 4.5a (GRADUATION_TARGETS) covers spec graduation targets and five existing specs carry - Graduated-To: while pqsx96 carries - From-Plan:, but REGISTRY['spec'] in agent_workflows/artifact_meta.py omits graduated_to and from_plan. m0001_convert preserves them in ## Graduated-To and ## From-Plan body sections.
