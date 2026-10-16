- Id: hbok5d
- Status: graduated
- Graduated-To: runledger
- Set: runledger
- Priority: low
- Work-Kind: chore
- Summary: Address runs decisions/questions raw markdown output and runs evidence/verify-ledger absolute path leaks

## Workflow history
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T212849Z-3382142: lpvcln
- 2026-10-16 created (aw backlog): Address runs decisions/questions raw markdown output and runs evidence/verify-ledger absolute path leaks

Two measured machine-surface gaps pinned by g5s94t:

1. (F-07) `runs decisions` and `runs questions` print raw markdown projections under both `--agent` and `--json` modes instead of structured JSON envelopes or dicts. Under `--agent` and `--json`, stdout cannot be parsed by `json.loads`.

2. (F-08) `runs evidence --agent` and `runs evidence --json` emit an absolute path for the "ledger" property, e.g. `{"chain_clean": true, "ledger": "/path/to/ledger.jsonl"}`. Additionally, `runs verify-ledger` prints `Ledger: /path/to/ledger.jsonl` in human mode. These absolute paths violate clean path relative conventions (D92).
