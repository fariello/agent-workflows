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

## Security follow-ups (OpenCode shared-host finding, D86/D87)

Not framework bugs; external-tool finding with coordinated-disclosure obligations. See advisory
`.agents/docs/research/20260716-0850-01-opencode-unauthenticated-local-server-advisory.md`.

- **Coordinated disclosure to OpenCode maintainers (OPEN).** Send the private report (repro + fix proposal:
  UNIX 0700 socket / require-auth config key / UID check / redact secrets from `/config` / honor permission
  policy on API-injected tool calls). Start the 30-45 day clock; go public only if unfixed by the deadline.
  Human owns whether/when it is sent.
- **HPC user warning (guidance ready).** Circulate the hardening how-to
  (`20260716-0850-02-...`). Consider a LOUD shared-host warning in the framework installer only if we decide
  the framework should carry it (would cite D86/D87); not yet committed.

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
  targets can be woken. FEASIBILITY NOW CONFIRMED (live test + source-grounded consult, 2026-07-16; see
  `.agents/docs/research/20260716-0850-03-broker-feasibility-confirmation.md`): cross-instance
  delivery/wake works; there is NO discovery API (port must be injected / scraped / enumerated); a plugin
  and an external daemon share the same HTTP-client channel (external daemon is cleaner); `OPENCODE_SERVER_PASSWORD`
  Basic auth (user `opencode`) works. This IPD can now be drafted. HARD INVARIANT reinforced by the D86
  security finding: the broker is payload-BLIND (reads envelope headers only; never a filesystem-to-injection path).
- **IPD 3 - agent-side ack writing + status aggregation.** The target agent writes its own
  read/in-progress/done/not-done/executed/not-executed acks; a status view aggregates ack files into a
  per-message lifecycle board. Depends on IPD 1 (format) + IPD 2 (broker acks to interleave).
- **IPD 4 - discovery/registry.** How the broker finds live targets + their mode/endpoint: prefer
  OpenCode's own mDNS/`attach`, with a filesystem descriptor as fallback; stale-entry reaping. Depends on
  IPD 2. Cross-box is out of scope for this line.
- Deferred beyond the split: conditional scheduling (`Depends-On` marker files), Telegram/Signal and
  other transports, cross-box comms.

### Research-prompt pipeline + surveyor/producer workflows (ordered Set; all 1.3.0-era)

An ordered Set of future IPDs that came out of the 2026-07-16 discussion on where run-once/research
prompts and their results live. They sit BEHIND the OpenCode security disclosure and the 1.2.1 patch.
Each needs its own IPD + `/plan-review` + human approval before any build. Order matters (later items
consume earlier ones). Grounding: DECISION D88 (filesystem-encoded state, extends P5); the `.agents/prompts/`
staging concept is already blessed by D50 / IPD `20260712-1544-01` but is not scaffolded in this repo.

- **Order 1 - DONE (D88).** Codify the filesystem-encoded-state principle (location over contents for
  surveyed state, with boundaries) by extending GUIDING_PRINCIPLES P5. This is the rationale the rest cite.
  Completed this session (`GUIDING_PRINCIPLES.md` P5 + D88); listed here for the Set's provenance.
- **Order 2 - scaffold `.agents/prompts/` + document the research-prompt->results convention.** Create the
  `.agents/prompts/` lifecycle buckets (mirroring the plan buckets: `pending/`, `reusable/`, `executed/`,
  `superseded/`, `not-executed/`) in THIS repo, and document that run-once/research prompts stage there
  (glanceable state via `ls .agents/prompts/pending/`), move through the buckets as they progress, and
  their RESULTS are durable artifacts filed under `.agents/docs/research/<topic>/`; `.agents/docs/prompts/`
  stays the evergreen reusable library (unchanged). DONE AHEAD (this session): the OpenCode verification
  runbook (`20260716-1342-02`) and its human-protocol companion (`20260716-1342-01`) were `git mv`d from
  `.agents/docs/research/` into `.agents/prompts/reusable/`, with the runbook's RESULTS destination pointed
  at `.agents/docs/research/opencode-security/`; the advisory / hardening how-to / broker-feasibility
  ANALYSIS notes stay in `research/`. STILL TO DO under this IPD: scaffold the full `.agents/prompts/`
  bucket set + a `.agents/prompts/README.md` documenting the convention, and re-issue the corrected runbook
  path (`.agents/prompts/reusable/...`) for the accompanying email. Depends on Order 1.
- **Order 3 - `/whatnext` workflow (surveyor; read-only, recommend-don't-act).** A `.agents/workflows/whatnext/`
  prose runbook that aggregates state by LISTING the tree (plans via Status/Set/Order, `.agents/prompts/pending/`,
  comms inbox headers only + untrusted, TODO sections, pending research) and proposes an ordering WITH REASONS.
  Never mutates, never acks, never moves anything. Portable to any agent; promote deterministic parts to an
  `aw whatnext` CLI helper later if it proves useful. Consumes Order 2's tree. (You chose two separate IPDs
  for this and the convention.)
- **Order 4 - `/research [topic]` workflow (producer; prompt-authoring walk-through).** A walk-through that
  clarifies the research question, drafts a house-conformant prompt into `.agents/prompts/pending/`
  (ENFORCING the AGENTS.md handoff-prompt rules: upload-ready, self-contained, no user-instructions inside,
  returns a downloadable `.md`), tells the operator how to run it (external LLM vs agent-run), and states
  where results go (`research/<topic>/`). Scope is narrow-to-medium (prompt authoring + filing), NOT a
  do-everything research blob overlapping `/assess` or `/spec`. Natural producer for the pipeline `/whatnext`
  surveys. Depends on Order 2.
- **Order 5 - OPEN: should the installer scaffold `.agents/prompts/`?** Decide whether `aw install` should
  create the `.agents/prompts/` skeleton (closing the current "agent-workflows does not manage a prompts dir;
  set it up by hand" gap from IPD `0501-03`), the way it now scaffolds `.agents/comms/`. Needs a decision
  before implementation. Depends on Order 2.

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
