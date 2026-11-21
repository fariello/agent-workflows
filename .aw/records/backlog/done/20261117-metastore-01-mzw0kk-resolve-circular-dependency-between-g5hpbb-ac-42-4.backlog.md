- Id: mzw0kk
- Status: done
- Graduated-To: mzw0kk
- Set: metastore
- Work-Kind: followup
- Priority: high
- Summary: Resolve circular dependency between g5hpbb AC-42(4)-(5) aw find/attention checks and Order 08 reader moves
- Short-Description: Resolve circular dependency between g5hpbb AC-42(4)-(5) aw find/attention checks and Order 08 reader moves
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 done (aw set): Completed by executed plan 60mazt (commit 592445def)
- 2026-11-18 graduated (aw set): Graduated to follow-up plan 60mazt (set mzw0kk)
- 2026-11-18 created (aw backlog): Resolve circular dependency between g5hpbb AC-42(4)-(5) aw find/attention checks and Order 08 reader moves

Plan g5hpbb E-07 requires tests/test_m0001_any_repo.py to assert AC-42 item (4) (aw find, aw attention --format json, and aw show <id6> --history on a migrated record) and item (5) (aw find before/after parity between legacy readers and log readers). However, g5hpbb Scope excludes moving any reader onto artifact_meta, while cdglt1 (Order 142), r81uvz (Order 27), dqutt8 (Order 28), and ffceq0 (Order 08) all declare Item-Dependencies: executed:g5hpbb. Until those reader moves land, aw attention --format json exits 1 (valid: false, attention.missing-status, attention.uninventoried-tree on .aw/records/meta) and aw find still uses legacy plans_index, research_index, and selectors rather than meta/*.jsonl logs. Re-sequence the aw find parity and aw attention --format json AC-42 assertions to run after Order 08 (or split them into a post-ffceq0 verification plan) and resolve e49gzt before running the full this-repository clone case in pytest.
