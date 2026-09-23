- Id: rwhbci
- Status: open
- Blocks-Release: next
- Set: closescope
- Priority: medium
- Work-Kind: bug
- Summary: The close-legitimacy HANDOFF arm can close a backlog item whose plan covers only part of it

## Workflow history
- 2026-09-23 created (aw backlog): Found executing dy9ymn. evaluate_blocking_close's HANDOFF arm accepts a close when some plan carries '- From-Backlog: <item>' AND the same '- Blocks-Release:'. It does NOT check that the plan's SCOPE covers the whole item, so a two-part item is closed when only one part is carried. MEASURED: x7wfyx names item A (tell the agent its remaining turn budget, a prompt change) and item B (the driver-side zero-work retry). It was closed done on 2026-09-22 citing plan dy9ymn - whose Scope says in terms 'EXCLUDES telling the agent its remaining turn budget, which is x7wfyx's other half'. The result is self-inconsistent: 'aw ipd lint' on dy9ymn reported check.ipd-uncarried-obligation TWICE, because two of its own obligations named x7wfyx as carrier and x7wfyx is now terminal. So the gate that exists to stop a dropped obligation dropped one. Worked around by filing successor 4bhxni and repointing both obligations. THE GATE IS STILL A STRICT IMPROVEMENT over nothing and must not be removed; the question is whether the handoff arm should require the plan to claim the WHOLE item (and how a plan would express that), or whether closing should warn when the citing plan's scope text excludes part of it. Note the release gate itself was NOT lost here - dy9ymn carries Blocks-Release: next - so this is an obligation-tracking hole rather than a release-gate hole.
