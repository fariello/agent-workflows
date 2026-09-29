- Id: 11pjkd
- Status: open
- Blocks-Release: next
- Set: sevvocab
- Priority: low
- Work-Kind: bug
- Summary: doctor renders leak_sanitizer's fail/warn severity vocabulary raw beside error/warning diagnostics

## Workflow history
- 2026-09-29 created (aw backlog): Carrier for an obligation deferred by plan nwcf8j (sevtruth), which fixes the doctor/attention severity surfaces but declines to unify two severity vocabularies.

`agent_workflows/leak_sanitizer.py` declares its own closed severity vocabulary (`fail` | `warn`) and translates it correctly at the `CommandResult` boundary. But `agent_workflows/doctor.py` renders that raw value into user-facing strings and into a machine payload whose sibling diagnostics use the `error`/`warning`/`info` vocabulary, so one payload carries two vocabularies for the same field.

This is a VOCABULARY MISMATCH, not a miscount or a severity inversion, which is why plan `nwcf8j` deferred it rather than folding it in: fixing it means choosing a canonical translation point, whereas that plan's changes only read a severity already in hand.

FIX SKETCH: translate at one boundary (most likely where doctor ingests sanitizer findings) so every severity leaving doctor uses the canonical three-value vocabulary, and pin it with a behavior test asserting no raw `fail`/`warn` reaches a rendered or serialized severity field.
