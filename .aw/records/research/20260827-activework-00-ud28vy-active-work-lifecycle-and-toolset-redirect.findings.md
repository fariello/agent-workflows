---
id: ud28vy
created: 20260827
set: activework
order: 00
topic: [lifecycle, multi-agent, liveness, claims, process-adherence, config, recovery]
model:
kind: findings
status: todo
outcome: none-yet
summary: Design: active-work lifecycle (drafting/reviewing/executing) via tool-owned liveness markers, dual-layer toolset-redirect nudge, staleness/takeover/recovery, and report-default/config-toggle repair (REVISABLE pre-implementation)
consumed-by: []
---

# Active-work lifecycle + toolset-redirect: design record

STATUS: design capture, **explicitly revisable before implementation**. This records the reasoning and
the decisions reached in a 2026-08-27 design discussion so they are not lost; it is NOT a frozen spec.
It will seed one or more specs (active-work lifecycle; frontmatter/instruction-file toolset directive)
and a blocking backlog item (command-based slash-command execution). Open threads are listed at the end.

## Problem

Work is run in parallel and multiple agents can touch the same repo. There is no reliable way to tell
that an artifact is being ACTIVELY worked on RIGHT NOW (vs merely at some readiness status). The
requested lifecycle adds active states:

`draft -> drafting -> to-review -> reviewing -> approved -> executing -> executed`

where `drafting`/`reviewing`/`executing` mean "an actor is on this now."

## Core tension and its resolution

A naive in-file `-ing` STATUS is a lie waiting to happen: a killed/forgotten agent leaves a permanent
false "executing" (the same "hand-typed status is unreliable" failure the process-adherence research
bu9yij documents). A pure lease/heartbeat is ALSO unreliable, because agents are trained to "jump in
and do the work" and skip custom tools, so they will not reliably call claim/heartbeat/release verbs.

Resolution - BELT AND SUSPENDERS, but with a corrected division of labor:
- The `-ing` marker IS written into the file (belt): it is what a barging-in agent actually reads and
  can pause on. This is the load-bearing behavioral nudge.
- Liveness metadata (suspenders) makes a forgotten marker DETECTABLE as stale, rather than a permanent
  lie. It is written at the same moment the marker is set.
- Recovery is driven by the NEXT reader + a deterministic staleness rule, NEVER by the dead worker
  running cleanup (we must assume the setter never runs a "done" path).

## Key correction: tools own liveness; agents do NOT hand-write markers

A toolless agent cannot produce a meaningful PID (it does not know the owning tool/session PID, and
`os.getpid()` of an incidental shell command is wrong). And crucially: if an agent had the wherewithal
to correctly hand-author structured liveness frontmatter, it has MORE than enough to just call
`aw set reviewing <id>` (the tool call is easier than replicating the fields). So there is no coherent
"can hand-write the marker but can't use the tool" scenario. Therefore:

- ONLY tools ever write the marker (owner + timestamp always; PID + host when a tool set it).
- Agents are never asked to hand-write liveness. Instead they are REDIRECTED to the toolset.

## The actor matrix (who sets the marker; is liveness reliable)

| # | Scenario | Marker set by | PID reliable? | Recovery implication |
|---|---|---|---|---|
| A | Tool launches an agent | the tool | Yes (same host) | Clean; tool sets + clears; staleness = PID-dead OR past max-age. |
| B | Agent uses the tool | the tool | Yes | Same as A; do not rely on the agent running "done" - use staleness. |
| C | Agent works WITHOUT the tool | nobody (redirect nudge is the only lever) | No | Common danger case: marker likely ABSENT. Backstop = the untooled-change commit gate + `aw check` finding, not a hand-marker. |
| D | User runs the tool | the tool | Yes | Clean; owner is human. |
| E | User edits manually | nobody | No | Like C; manual edit may not touch the marker at all; backstop = gate/check. |
| F | Tool -> agent -> tool -> ... | nested | Yes, but recursion risk | Needs a re-entrancy guard so a lineage does not re-claim/re-launch itself (OPEN thread). |

PID is meaningful only when a tool set it and only on the same host (A/B/D/F). For C/E there is no live
PID, so timestamp + max-age is the universal signal; PID is an optional strengthener when present and
same-host. Staleness rule: `PID-dead-on-this-host OR past-max-age`; cross-host or PID-absent -> age only.

## Decisions reached (revisable)

1. **Marker ownership:** tools only. Fields: `owner`/actor (always), `set-at` ISO timestamp (always),
   `pid` + `host` (when a tool set it, optional). No agent hand-writes it.
2. **Redirect nudge, dual-layer:** (a) a TOOL-GENERATED frontmatter banner on every managed artifact
   directing any actor to route lifecycle mutations through `aw`; (b) a directive in the installer's
   managed pointer block of the always-loaded host instruction files (AGENTS.md, CLAUDE.md, GEMINI.md,
   SKILL.md, etc.). Belt (per-artifact, just-in-time at the decision point) + suspenders (always-loaded,
   cross-host). Frontmatter SCREAMS; it does not enforce.
3. **Enforcement is the deterministic backstop, not the banner:** `aw check`/attention emit findings
   (`missing-frontmatter-banner`, `untooled-status-change` [precedent: the existing
   `ipd-status-untooled-gate`], `stale-active-marker`); the commit gate catches untooled edits. Prose
   is probabilistic; the gate + check is the authority.
4. **Staleness detection:** timestamp + max-age universally; PID/host liveness probe strengthens it when
   a tool set it on the same host. Next reader / `aw attention` judges; no dependence on the dead worker.
5. **Takeover:** a second agent may reclaim a marker ONLY once it is provably stale (past threshold),
   and MUST record the takeover (who, when, superseding whom) so history shows a reclaim, not a silent
   stomp. Fresh markers are respected (back off / pick other work).
6. **`executing` recovery:** a killed `executing` is `unknown_outcome` until a deterministic check
   reconciles actually-changed paths vs frozen scope (reuse the run-ledger / `ipd begin` receipt +
   containment model); only then resume or roll back; the marker reverts to `approved` only after
   containment.
7. **Detect-and-repair stance:** read verbs (`aw check`/`find`/`doctor`) stay READ-ONLY by default and
   REPORT gaps; repair only with explicit `--fix`/`--apply` (precedent: `sanitize --fix`). BUT the
   default is CONFIG-DRIVEN: an `aw config` key may flip the default to auto-fix, in which case
   `--no-fix` opts out per-invocation. This preserves the read-only guarantee + parallel-agent safety
   out of the box while allowing a repo to opt into auto-repair.
8. **Grow `aw config`:** capture more default-behavior toggles in the config file generally (fix/no-fix
   here; also relevant: selfcommit's commit-on-mutation default, hook-install defaults). Treat
   "expand the config surface for default behaviors" as its own design thread.

## Emerging spec shape (to be authored next, then revisited before implementing)

- SPEC A - active-work lifecycle: the seven-state model, the tool-owned marker schema + liveness,
  staleness rule, takeover-past-threshold-and-record, `executing`-reconcile-before-resume/rollback.
- SPEC B - toolset-redirect directive: tool-generated per-artifact frontmatter banner + managed
  directive in host instruction files; the `missing-frontmatter-banner` finding + opt-in/config repair;
  which normally-read-only verbs gain detect-and-(opt-in)-repair.
- Update SPEC 25kzda: reference the active states in its dispatch/lifecycle sections.
- Cross-reference SPEC 5tapom (research-lifecycle-reliability): same "tool-owned state, not hand-typed"
  principle; and it is the answer to "which research needs attention" (see below).
- BLOCKING BACKLOG ITEM: research command-based execution of slash commands (/plan-review,
  /release-review) for better control of who-works-on-what and multi-step activities.

## Answer to "which research needs attention?" (Q3) - and a live gap

Research already has: 4-state status (`intake`->`active`->`reference`/`archive`), `outcome`
(`none-yet`/`adopted`/`informational`/`rejected`), and `consumed-by`. `aw attention` already treats
unrun `intake` as READY (needs attention), reclasses stale/consumed `intake` to PARKED (hidden), and
`active` as ACTIVE. `aw research pending` lists unrun prompt-sets.

LIVE GAP (demonstrated by this very session): finished-but-unadvanced `intake` docs look identical to
never-touched ones. My own `sk94i0` and `40g511` show as `intake` in the board despite being finished
and `adopted`/`consumed-by 25kzda`. This is exactly the H2 reliability gap SPEC 5tapom
(`research-lifecycle-reliability`, currently `to-review`) was written to close: status never advances
after creation, so "needs attention" is only as good as hand-advancement. RESOLUTION PATH: 5tapom's
tool-owned state-advancement + the same active-work/liveness principle here. Interim answer to the
question: `aw research pending` (unrun) + `aw attention` (READY research) are the signals today; they
are reliable for UNRUN detection but not yet for FINISHED-but-unadvanced detection until 5tapom lands.

## Open threads (settle before implementing)

- Re-entrancy guard for scenario F (tool->agent->tool): lineage/run-id on the claim so a tool refuses to
  re-claim within its own lineage (leading candidate) vs a depth guard vs forbidding nesting in v1.
- Exact staleness thresholds (per state? per host? configurable default via aw config).
- Banner content + placement (frontmatter field vs comment; how loud; per-type wording).
- Which read-only verbs gain detect-and-repair, and the precise config key(s) + names.
- Whether `executing`-recovery is designed here or deferred to the runner program (where containment
  already lives).
- Interaction of the new active states with the existing `auto-approved` tier and the draft-readiness
  nudge (agentadhere) and the `Item-Dependencies` gates (ipddeps).

## Addendum (2026-08-27): uniform `Summary` field for board-renderable descriptions

Finding: `aw att` shows no per-artifact description - it renders `[type] path (status)` only. Two causes:
(1) the attention `Item` model has no description field; (2) types carry a description INCONSISTENTLY -
backlog/research/releases have a `Summary`/`summary` field, but specs and IPDs use only their H1 title
(`# Spec:`/`# IPD:`) + `- Concern:`, and walkthroughs/roadmaps rely on the filename slug + H1. So a
description is parsable per-type but there is no single field a reader can use blindly across all types.
This is why finished-but-unadvanced `intake` docs (e.g. this one) look like undifferentiated noise on
the board: it cannot show WHAT an artifact is, only WHERE it is.

DECISION (revisable): standardize on the incumbent field name **`Summary`**, uniform across ALL managed
artifact types, CONTRACTED as a single bounded, control-char-free line (generalize the existing
`backlog.summary-unsafe` one-line rule to every type). Add `Summary` to the types that lack it
(specs, plans/IPDs, walkthroughs, roadmaps); keep it on backlog/research/releases. Solve the
length-ambiguity of the word "Summary" via the CONTRACT (must be one line, bounded length), NOT via a
longer field name like `Short-Description` - a longer name that still permits multi-line content would
not actually enforce brevity, and renaming three existing types' fields is churn for a clarity gain the
contract already delivers. One field, one meaning, enforced brevity, zero rename.

Consequences for the spec pass:
- Fold into SPEC B (toolset-redirect/frontmatter): "every managed artifact carries a tool-maintained,
  single-line `Summary` field" becomes part of the frontmatter contract the tool maintains + the
  `aw check`/repair surface validates (same report-default/config-toggle-autofix stance as the banner).
- `aw att` (and the attention `Item` model) gains a `summary` field read from each artifact's `Summary`
  and renders it as the one-line per-row description. Extractor reads the uniform field (no per-type
  special-casing once all types carry it; a transition window may fall back to H1/slug for not-yet-
  migrated artifacts).
- The one-line `Summary` contract also feeds the "which research needs attention" clarity (Q3): a board
  that shows each row's Summary distinguishes a finished design record from an unrun prompt at a glance.
