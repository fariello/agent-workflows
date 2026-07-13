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

## Consider and possibly implement (not committed, may be declined)

Ideas worth revisiting; each needs a real decision before it becomes a plan. Do not implement any of
these without an approved IPD.

- **Agent-comms trust tiers.** Distinguish message senders by origin/trust
  (same-operator-same-host vs. cross-operator vs. external/unknown) and escalate gating accordingly, so
  the filesystem agent-comms protocol is safe in shared/multi-operator environments, not just among a
  single operator's own instances. Valuable in theory; the hard part is APPLICATION: on a shared
  filesystem an agent cannot reliably authenticate a peer's tier without a provenance mechanism
  (below). Source: agent-comms protocol trial, 2026-07-12. See
  `.agents/docs/specs/20260712-2133-02-agent-comms-protocol-draft.md` (open questions 7-8). The
  unverified-identity FACT is already stated in that spec's injection section; only the tiered RESPONSE
  is deferred here.
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
  See `.agents/docs/specs/20260712-2133-02-agent-comms-protocol-draft.md` (open question 5, `aw comms`).

## Notes

- The agent-comms protocol itself is on trial (see the draft spec); formalizing it into the framework
  (installer scaffolding, tooling such as an `aw comms` helper, an always-loaded pointer) is gated on
  the trial and would be its own IPD.
