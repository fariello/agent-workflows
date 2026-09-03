- Id: av9hni
- Status: done
- Blocks-Release: next
- Set: awinstallfix
- Priority: high
- Work-Kind: bug
- Summary: aw install wizard writes to disk mid-interview and mishandles abort, leaving a partial .aw/ on ctrl-c or decline, reporting a false 'nothing changed', accepting a nonexistent companion, and leaving uninstall blind to the partial footprint (fixed by awinstallfix-01)

## Workflow history
- 2026-08-21 set (aw backlog): status -> done

## Detail (moved verbatim out of the Summary field 2026-09-03)

This item carried its whole description in `- Summary:` at 306 characters against the 300-character
bound (`attention_contract.MAX_DESCRIPTIVE_LEN`), which is why `aw backlog check` reported
`backlog.summary-unsafe`. Original text, preserved unchanged:

> aw install wizard writes to disk mid-interview and mishandles abort: partial .aw/ left on ctrl-c or
> final decline, false 'nothing changed', nonexistent companion silently accepted, uninstall blind to
> partial footprint, final install defaults No (spec 20260809-2211-01 conformance; fixed by
> awinstallfix-01)

Two facts the shortened Summary drops: the sixth defect, that the final install prompt DEFAULTED TO NO;
and the authority, that this was a conformance gap against spec `20260809-2211-01`
(`aw-project-layout-storage-wizard-and-state`). Both are recorded here so the shortening cost nothing.
