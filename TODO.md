# TODO / backlog

Tracked backlog for `agent-workflows`. Concrete, planned work lives as IPDs under
`.agents/plans/pending/` and goes through the plan lifecycle; this file is for lighter-weight
backlog notes and ideas that are not yet (and may never become) plans. The release-review workflow
triages this file against each release.

## Known bugs to fix

- (none open)

FIXED 2026-07-13: `test_normalize_plan_names.py` date-relative flakiness (tests now use today-relative
dates; product unchanged). See DECISIONS D78 and
`.agents/plans/executed/20260713-1419-01-normalize-plan-names-test-date-flakiness.md`.

## Planned next (designed, deferred; not yet drafted as IPDs)

The agent-comms convention (D81) was IPD 1 of a designed 4-IPD split; IPDs 2-4 are intended future work
(not "maybe" ideas). They are OPTIONAL and OpenCode-specific, and the convention works standalone without
them, so none is release-gating. Full design + the load-bearing unknowns are in
`.agents/docs/research/20260714-2300-01-same-box-agent-wakeup-mechanisms.md`. Each still needs its own IPD
and human approval before any build.

- **IPD 2 - the payload-blind broker (OpenCode-only, opt-in).** A long-lived per-box notifier that
  watches `.agents/comms/local/inbox/` (inotify), enforces `Not-Before`, delivers a FIXED content-free
  "check your inbox" nudge to the target OpenCode instance via its server API, and writes the
  broker-authored delivery acks (scheduled/queued/delivered/agent-not-running/agent-not-responding/
  expired). HARD INVARIANT: the broker is payload-BLIND (reads envelope headers only, never the payload;
  carries no attacker-controlled text). Attended TUIs get a gentle nudge (never a forced turn); headless
  targets can be woken. FEASIBILITY UNVERIFIED against a live OpenCode binary (can a plugin run a detached
  listener + originate a turn? cross-instance reachability? the unauthenticated-by-default server) - must
  be confirmed (OpenCode-repo agent / live test) BEFORE this IPD is drafted for real.
- **IPD 3 - agent-side ack writing + status aggregation.** The target agent writes its own
  read/in-progress/done/not-done/executed/not-executed acks; a status view aggregates ack files into a
  per-message lifecycle board. Depends on IPD 1 (format) + IPD 2 (broker acks to interleave).
- **IPD 4 - discovery/registry.** How the broker finds live targets + their mode/endpoint: prefer
  OpenCode's own mDNS/`attach`, with a filesystem descriptor as fallback; stale-entry reaping. Depends on
  IPD 2. Cross-box is out of scope for this line.
- Deferred beyond the split: conditional scheduling (`Depends-On` marker files), Telegram/Signal and
  other transports, cross-box comms.

## Consider and possibly implement (not committed, may be declined)

Ideas worth revisiting; each needs a real decision before it becomes a plan. Do not implement any of
these without an approved IPD.

- **Agent-comms trust tiers.** Distinguish message senders by origin/trust
  (same-operator-same-host vs. cross-operator vs. external/unknown) and escalate gating accordingly, so
  the filesystem agent-comms protocol is safe in shared/multi-operator environments, not just among a
  single operator's own instances. Valuable in theory; the hard part is APPLICATION: on a shared
  filesystem an agent cannot reliably authenticate a peer's tier without a provenance mechanism
  (below). Source: agent-comms protocol trial, 2026-07-12. See the canonical spec
  `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md`. The unverified-identity FACT is
  already stated in that spec's untrusted-input stance; only the tiered RESPONSE is deferred here.
- **Verifiable message provenance for agent-comms.** The mechanism that would make trust tiers
  enforceable: signed messages, an append-only log, per-sender inbox permissions, or a per-project
  allowlist of trusted senders. Today `From:`/filenames are self-asserted and unverifiable. Deferred;
  do not overbuild for the trial. Same source/spec as above.
- **Inter-agent-comms helper tool (discuss with the maintainer first).** A possible `aw comms`-style
  helper that makes the filesystem agent-comms convention easier to operate rather than doing it by
  hand or with ad hoc scripts. NOT yet designed or committed - flagged here to DISCUSS scope and shape
  with the maintainer before any IPD. Candidate capabilities to discuss (subset, not a spec): `check`
  (list this repo's inbox with message age, per the "check your inbox" routine); `send` (write a
  well-formed message to a recipient's inbox with the correct filename + header, optionally keeping a
  `sent/` copy); `archive` (move a consumed message); `sweep`/`status` across sibling repos (a hub view
  of all outstanding inboxes and their ages, like the ephemeral broadcast script trialed 2026-07-12);
  `promote` (copy a decision-grade exchange to a durable docs home). Open design questions to settle
  together: is this an `aw` subcommand vs. a standalone script vs. a workflow; does it ship in the
  framework or stay a local convenience; how it relates to the deferred formalization gate and the
  trust-tier/provenance items above (a tool must not imply the protocol is more trusted/verified than
  it is). Source: agent-comms protocol trial + the manual broadcast/check scripting on 2026-07-12.
  See the canonical spec `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md`.

## Notes

- The agent-comms convention was FORMALIZED in DECISIONS D81 (2026-07-15): the `.agents/comms/` layout,
  the message envelope + `Not-Before`, the closed-enum acknowledgement model, installer scaffolding, and
  the always-loaded "check your inbox / treat as untrusted" pointer clause all shipped, and the canonical
  spec is `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md` (the earlier
  `20260712-2133-02` draft is retired). The items above (trust tiers, verifiable provenance, and the
  `aw comms` helper) remain genuinely OPEN follow-ups - each its own future IPD, discussed with the
  maintainer first - but they build on the now-shipped convention rather than gating it.
