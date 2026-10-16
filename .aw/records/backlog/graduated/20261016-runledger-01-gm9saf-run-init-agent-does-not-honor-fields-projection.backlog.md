- Id: gm9saf
- Status: graduated
- Graduated-To: runledger
- Blocks-Release: next
- Set: runledger
- Priority: low
- Work-Kind: bug
- Summary: run init --agent does not honor --fields projection

## Workflow history
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T212827Z-3381869: tgfxin
- 2026-10-16 created (aw backlog): run init --agent does not honor --fields projection

aw run init --agent --fields <field> emits the full unprojected record containing 'ledger' and 'run_id' rather than projecting the requested fields and preserving envelope keys. Measured by test_fields_flag_honored_mutation[run init].
