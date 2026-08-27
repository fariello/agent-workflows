- Id: sr47pt
- Status: open
- Set: researchtodo
- Priority: high
- Kind: feature
- Summary: Rename research status 'intake' -> 'todo' (intuitive 'you still need to do this'); migrate the 8 modules + existing docs; ride with 5tapom's state-advancement so 'todo' means genuinely-not-started

## Workflow history
- 2026-08-27 created (aw backlog): Rename research status 'intake' -> 'todo' (intuitive 'you still need to do this'); migrate the 8 modules + existing docs; ride with 5tapom's state-advancement so 'todo' means genuinely-not-started

Problem: research status `intake` is opaque - it does not tell a reader "you still need to do this research", and it is OVERLOADED (means both genuinely-unrun AND finished-but-unpromoted; see this session's sk94i0/40g511 sitting as `intake` despite being done+adopted). Decision: rename `intake` -> `todo` ('Status: todo' unambiguously = the reader must act; beats the passive/ambiguous `pending`). New research lifecycle: `todo` -> `active` -> `reference`/`archive`.

Scope: rename the status token across the ~8 modules that reference `intake` (`research_contract.py` STATUSES/HOT_STATUSES, `research_cmd.py` creation default, `research_index.py`, `research_archive.py`, `attention.py` + `attention_contract.py` classification, `cli.py`, `term.py`), migrate existing on-disk docs' frontmatter `status: intake` -> `status: todo`, and update INDEX regeneration. Keep the attention classification behavior (todo research = READY/needs-attention) identical - only the token changes.

Coupling: the rename fixes the NAME; the OVERLOAD (unrun vs done-but-unfiled) is fixed by spec 5tapom (`research-lifecycle-reliability`, tool-owned state advancement). Ride this rename WITH 5tapom's state-advancement work so `todo` means genuinely-not-started, not done-but-unadvanced. Cross-referenced in 5tapom. Origin: user - "what the hell does 'intake' even mean?"
