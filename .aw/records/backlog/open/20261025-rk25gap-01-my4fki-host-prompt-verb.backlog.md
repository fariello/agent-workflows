- Id: my4fki
- Status: open
- Set: rk25gap
- Priority: low
- Work-Kind: feature
- Summary: Build aw <host> prompt (--text/--file) one-shot verb from spec 25kzda 1.3

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit of 25kzda (maintainer ruling: ungate the spec, file the unbuilt pieces as items).

Spec 25kzda Section 1.3 and 2.1 specify `aw <host> prompt (--text <text> | --file <path>)`: a one-shot host interaction that reports transport success only, never `verified`, performs no lifecycle transition, and does not use the run-and-verify success exit code. Not built: `aw oc prompt` is an invalid choice at HEAD 5db4791c1 (audit 2026-10-25).
