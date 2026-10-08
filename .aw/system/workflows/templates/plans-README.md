# .aw/records/plans/

Your Implementation Plan Documents (IPDs), organized by lifecycle state. Plan files are
named `YYYYMMDD-HHMM-NN-<slug>.md` (the creating machine's local date and time; `NN` is a two-digit per-minute
sequence, with `00` reserved for an orchestrator plan and `01+` for ordinary/child plans;
`<slug>` is lowercase kebab-case).

The lifecycle:

- **`pending/`** - new or under review/implementation; awaiting approval.
- **`executed/`** - implemented, verified, and tested (terminal; `done/` is an accepted alias).
- **`superseded/`** - replaced by a better/subsequent plan; kept for the record.
- **`not-executed/`** - deliberately decided against, no replacement.
- **`reusable/`** - recurring plans re-run repeatedly (not a terminal state).

**Never file an un-run plan in `executed/`** (that falsely claims it was implemented).
Retire a plan by prepending a `RETIRED YYYY-MM-DD: <reason>; superseded by <path/commit>`
header and `git mv`ing it to `superseded/` or `not-executed/`. **Never silently delete a
plan** - retiring preserves the record and the reason.

**Private/brain-dir plans MUST be mirrored here.** If an agent keeps a plan/IPD in a
private, hidden, or tool-internal "brain"/memory/scratch dir (e.g. Antigravity/Gemini), it
MUST also keep an exact, conventions-compliant copy under `.aw/records/plans/` and move THAT copy
through the lifecycle; the tracked copy is the source of truth, the private copy is
disposable. (Also stated in the always-loaded `AGENT-WORKFLOWS` block.)

## Readiness status (front-matter)

The DIRECTORY records a plan's disposition (above); the plan's front-matter `Status:` line
records its READINESS within the lifecycle:

- `draft` - a stub or partial; not ready to review or execute.
- `to-review` - complete enough to critique; ready for `/plan-review` or a human. A
  normally-drafted plan is born here; use `draft` only for an explicit "capture now, finish
  later" stub.
- `reviewed` - `/plan-review` done and revisions applied; awaiting human sign-off.
- `approved` - a human signed off; ready to execute.
- `auto-approved` - ready to execute, cleared by an automated checker (e.g. `/verify-execution`)
  rather than a human; used for low-complexity mechanical correctives (D65). NOT human approval;
  set only by an automated checker, never by an executor fast-tracking its own work.
- Terminal (`executed` / `superseded` / `not-executed`) mirrors the directory; `reusable` is
  standing.

Each plan also keeps a `## Workflow history` section: an appended, dated line per workflow
that touched it (assess, plan-review, ...), so you can see the path a plan took. The
plan-mutating workflows commit (never push) as they go, so `git log` shows the progression.

## Ordered sets (optional `Set:` / `Order:` front-matter)

When several plans form ONE sequence meant to run in a specific order, tag them with two optional
front-matter fields (D82):

- `- Set: <lowercase-kebab id>` - shared by every plan in the set (e.g. `Set: editor-workflow`).
- `- Order: <n>` - the 1-based position within that set. Optional; a `Set:` with no `Order:` is an
  unordered grouping.

These are ADVISORY: they group related plans and make the intended run order queryable and visible
in the `aw ipd board` view (a "Sets" section), but they do NOT auto-execute, do NOT gate approval, and do
NOT change the `Status:` lifecycle. The human still approves and runs each plan. They are ORTHOGONAL
to the filename convention: the `YYYYMMDD-HHMM-NN-<slug>.md` name and the `NN` same-minute
disambiguator are unchanged. An agent may GROUP pending plans by adding these fields, but any change to
a set's membership, order, or id must be surfaced (in Workflow history) and confirmed with the human,
never done silently; set fields on plans already in a terminal directory are frozen history.

## Durable carrier vocabulary for obligations

Every outstanding obligation in an IPD (an item in `## Deferred / out of scope (with reason)` or an open or deferred question under `## Open questions`) must name a durable carrier before the plan reaches terminal execution. Once a plan reaches `executed`, it classes `done` in `aw attention`, so uncarried items would vanish from operational attention with no record.

The carrier gate recognizes three escapes:

1. **Handoff**: `- Carrier: <id6>`
   Names an open backlog item (file one with `aw backlog new`) or a pending plan. The referenced id6 must resolve to a live, non-terminal record; a dangling id6 or a terminal record (executed plan, completed backlog) is refused because nothing revisits it.
2. **Satisfied by evidence**: `- Carrier-Evidence: <in-tree artifact path>`
   Cites an in-tree artifact demonstrating the obligation is already addressed (for example, a prior executed plan). The path must resolve to a valid in-tree artifact. Walkthrough paths are explicitly refused because walkthroughs carry no lifecycle status (`tracked=False`) and are never scanned by `aw attention`.
3. **Explicitly declined**: `- Carrier-Declined: <reason>`
   Declines the obligation explicitly with a non-empty rationale explaining why it requires no carrier. The merit of the reason is judged by the reviewer during plan review.

### Discharged carriers and the Carrier-Evidence remedy

A carrier that reaches `done` (backlog) or `executed` (plans) before your plan finishes turns the row into a refusal on purpose. A reader pointed at a closed item would assume the work is still pending elsewhere rather than finished. This commonly arises in an ordered Set where a later sibling plan declares an earlier sibling as a dependency and names it as a carrier.

When a carrier resolves to finished work, the pre-transition gate prints the exact `- Carrier-Evidence: <path>` line to paste in place of `- Carrier:`. You may optionally explain the context in the row's own prose; do not write an unparsed custom field for this note.

Do not use `Carrier-Declined` for work that has shipped. `Carrier-Declined` records an obligation as needing no carrier, whereas finished work shipped and should cite evidence instead.

### Carrier records durable ownership, not a dispatch gate

`Carrier` records durable ownership and is NOT a dispatch gate. Nothing in the lifecycle makes a plan wait for a carried question's answer: the pre-execution checkpoint refuses an open question only when it carries `Blocking: yes`. An approved plan with an open, non-blocking carried question can execute and reach `executed/` without waiting for the carrier.

To make a plan wait for a carried decision, declare the dependency explicitly with an edge:

```sh
aw ipd dependencies set <plan> state:backlog:<status>:<carrier>
```

`aw check plans` now reports carried open questions that declare no dependency edge on their carrier advisorily (`check.ipd-carrier-ungated` at `info` severity).

Beware the exact-status trap: `state:backlog:<status>:<carrier>` requires the carrier status to match EXACTLY. An edge written against `done` refuses while the carrier is `graduated` (handed off to a plan or spec, but code not yet written). Check the carrier's actual status with `aw attention` or `aw backlog list` before setting the edge, so the plan does not block on a decision that has already been handed off.

## Execution contract in every plan's gate

Every IPD's `Approval and execution gate` MUST carry an execution contract so the plan is
safe to hand to any agent from its path alone:

1. All open questions RESOLVED (or explicitly OPEN, in which case the plan is NO-GO).
2. A SCOPE FENCE naming the exact files/areas to touch, with "do not expand scope; if it
   seems to need more, STOP and report".
3. The HARD MUST honesty rule: when you report tests/validation passed, paste the ACTUAL
   runner output; never claim success you did not run.
4. Commit ONLY the plan's own changed files, path-scoped; never `git add -A`/bare/`-a`;
   never push.
5. The lifecycle transition on completion: the plan reaches `executed` ONLY through the gated
   finalize transaction, which performs the attributed history entry, the terminal `Status:`,
   the move, and the path-scoped lifecycle commit as one transaction; a hand-built `git mv`
   plus a `Status:` edit is NEVER a valid terminal transition, because it satisfies neither
   `IPD-S406` (non-generic actor plus nonempty summary) nor `IPD-M104` (`Approval:` cleared).
   Who runs it depends on how the plan is executed:
   - In a managed lane (`AW_EXECUTION_ROLE=worker`): the transition is the runner's; the executor
     must not run `aw ipd finalize`, but reports its result and stops.
   - Otherwise (executing by hand, or under `--no-self-finalize`): the executor runs
     `aw ipd finalize --actor '<agent/model>' --message '<summary>' --apply` itself.
   - If unsure which case applies, attempt finalize: an `AW-LIFECYCLE-ROLE-001` refusal is the
     expected, successful handoff, not a failure.
   Note that `git mv` remains correct ONLY for retirement to `superseded/` or `not-executed/`,
   which finalize deliberately does not perform.

This restates, at the plan level, the standing `AGENT-WORKFLOWS` execution contract (see the
managed block in `AGENTS.md` and `CONTRIBUTING.md`); `/plan-review` and `/plan-review-long`
verify it is present and add it if missing.
