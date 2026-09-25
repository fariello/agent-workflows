- Id: c0ppo0
- Status: open
- Blocks-Release: next
- Set: c0ppo0
- Priority: low
- Work-Kind: bug
- Summary: doctor.SanitizerProbeResult.scanned_files is never assigned, so aw doctor agent evidence always reports 0 files scanned

## Workflow history
- 2026-09-25 created (aw backlog): Found at review of plan rpqv4q: the field is declared, emitted in to_dict() and published as agent evidence, but never assigned. Driven with 1 tracked file and 2 findings, sanitizer evidence reads {'scanned_files': 0, 'findings': 2}. Separate from rpqv4q's f.matched bug: different field, and leak_sanitizer.scan_working_tree returns only findings so it has no count to hand back (the fix needs an API change or a separate count).
