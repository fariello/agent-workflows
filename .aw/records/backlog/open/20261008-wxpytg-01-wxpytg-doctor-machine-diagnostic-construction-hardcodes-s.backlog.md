- Id: wxpytg
- Status: open
- Blocks-Release: next
- Set: wxpytg
- Priority: low
- Work-Kind: bug
- Summary: Doctor machine diagnostic construction hardcodes severity error for every drift

## Workflow history
- 2026-10-08 created (aw backlog): Doctor machine diagnostic construction hardcodes severity error for every drift

Discovered during IPD 36sifo plan review (F-10). In doctor.py (around lines 2014-2022), Diagnostic construction hardcodes severity='error' for every drift in report.all_drift, rather than preserving the drift's real severity or enriching via check_engine.enrich_drift(d).severity. Sibling to the defect fixed by nwcf8j in attention.py.
