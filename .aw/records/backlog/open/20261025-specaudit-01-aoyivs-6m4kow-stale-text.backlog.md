- Id: aoyivs
- Status: open
- Set: specaudit
- Priority: low
- Work-Kind: followup
- Summary: Amend spec 6m4kow sections 0/6 and the stale runner refusal message after artdispatch

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Spec 6m4kow Sections 0 and 6 say a --type spec run refuses to queue specs, and that aw find specs --status is broken. Both are false at HEAD 5db4791c1: Set artdispatch (spec z7nbn1, implemented 2026-10-25) made QUEUEABLE_TYPES {ipd, spec, backlog} and dispatches to-review specs to /spec-review; backlog faov03 fixed find --status. The user-facing refusal message at runner_shared.py ~15322 still says per-type DISPATCH is not built. Amend the spec text and the message; then 6m4kow (all R-01..R-16 implemented) can move to implemented.
