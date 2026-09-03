- Id: f7w55w
- Status: done
- Set: awhistignore
- Priority: low
- Work-Kind: followup
- Summary: Revisit whether .aw/config/project.json should stay untracked or be committed, by observing how agy and other agents materialize it and whether it keeps changing, then either commit a sanitized shared copy or gitignore it as local state

## Workflow history
- 2026-08-20 set (aw backlog): status -> done

## Detail (moved verbatim out of the Summary field 2026-09-03)

This item carried its whole description in `- Summary:` at 328 characters against the 300-character
bound (`attention_contract.MAX_DESCRIPTIVE_LEN`), which is why `aw backlog check` reported
`backlog.summary-unsafe`. Original text, preserved unchanged:

> Revisit whether .aw/config/project.json should stay untracked/committed here: observe how agy and
> other agents materialize it and whether it keeps changing; if it is stable+portable, commit a
> sanitized shared project.json, if it churns like local state, gitignore it + note the local-only
> classification in spec 20260810-1447-01

The detail the shortened Summary drops is the DECISION RULE and its recording site: if the file proves
stable and portable, commit a sanitized shared `project.json`; if it churns like local state, gitignore
it AND record the local-only classification in spec `20260810-1447-01`
(`physical-aw-hierarchy-placement-and-migration`).
