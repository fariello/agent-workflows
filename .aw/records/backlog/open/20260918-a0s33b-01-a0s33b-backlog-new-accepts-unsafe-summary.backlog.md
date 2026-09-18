- Id: a0s33b
- Status: open
- Set: a0s33b
- Priority: medium
- Work-Kind: bug
- Summary: aw backlog new does not validate --summary against the contract its own checker enforces, so it writes an item that aw check backlog immediately flags backlog.summary-unsafe (over MAX_DESCRIPTIVE_LEN), instead of refusing at creation

## Workflow history
- 2026-09-18 created (aw backlog): Found by IPD diof9n while filing two defect items: both were written by aw backlog new with exit 0 and no warning, then flagged backlog.summary-unsafe by aw check backlog because the summaries exceeded attention_contract.MAX_DESCRIPTIVE_LEN (300). The creating verb should apply is_safe_descriptive and fail closed, so a creator cannot commit a nonconforming item. Fixed by hand in diof9n by shortening both summaries; the verb gap remains.
