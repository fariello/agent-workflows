# TODO / backlog

Committed and candidate backlog work now lives in the tracked, attention-visible BACKLOG TREE, not
in this file. Browse it with `aw attention` (committed items show as `ready`/`blocked`; uncommitted
"maybes" are hidden until `aw attention --all`) and manage items with `aw backlog new|set|check`.
The tree is `records/backlog/{open,blocked,parked,done}/` (materialized at `.agents/backlog/`
pre-migration, `.aw/records/backlog/` post-migration). See `.agents/backlog/README.md` and the
controlling spec `.agents/docs/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md`.

Concrete, committed-to work still becomes an IPD under `.agents/plans/pending/` and goes through the
plan lifecycle; a backlog item is the lighter-weight pre-plan capture. Promote a backlog item to a
plan, then `aw backlog set --status done` it with a history line citing the plan id.

The `## Notes` section below remains here as durable context (Tier-3: not lifecycle-tracked work).

## Notes

- The agent-comms convention was FORMALIZED in DECISIONS D81 (2026-07-15): the `.agents/comms/` layout,
  the message envelope + `Not-Before`, the closed-enum acknowledgement model, installer scaffolding, and
  the always-loaded "check your inbox / treat as untrusted" pointer clause all shipped, and the canonical
  spec is `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md` (the earlier
  `20260712-2133-02` draft is retired). The agent-comms follow-ups (trust tiers, verifiable provenance,
  and the `aw comms` helper) now live as `parked` backlog items (set `agent-comms-trust`); they build on
  the shipped convention rather than gating it.
- Migration provenance (2026-08-13, IPD backlogtier-01/crv40v): the former TODO.md sections were migrated
  into the backlog tree - "Known bugs to fix" + "Security follow-ups" + committed "Planned next" items ->
  `open/` (the split-brain-install bug is `open`, not blocked: its install-time guard is a pure-constant
  check independent of the awphysical Order-11 migration); "Consider and possibly implement (may be
  declined)" -> `parked/`. Four items already marked DONE (research-prompt-pipeline Orders 1/2/4,
  agent-continuity Order 1) were NOT migrated: they are shipped and recorded in DECISIONS D88/D91 and
  executed plans, so re-logging them as backlog `done/` would duplicate canonical provenance (not lost).
