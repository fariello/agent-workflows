# .agents/plans/

Your Implementation Plan Documents (IPDs), organized by lifecycle state. Plan files are
named `YYYYMMDD-HHMM-NN-<slug>.md` (UTC date and time; `NN` is a two-digit per-minute
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

## Readiness status (front-matter)

The DIRECTORY records a plan's disposition (above); the plan's front-matter `Status:` line
records its READINESS within the lifecycle:

- `draft` - a stub or partial; not ready to review or execute.
- `to-review` - complete enough to critique; ready for `/plan-review` or a human. A
  normally-drafted plan is born here; use `draft` only for an explicit "capture now, finish
  later" stub.
- `reviewed` - `/plan-review` done and revisions applied; awaiting human sign-off.
- `approved` - a human signed off; ready to execute.
- Terminal (`executed` / `superseded` / `not-executed`) mirrors the directory; `reusable` is
  standing.

Each plan also keeps a `## Workflow history` section: an appended, dated line per workflow
that touched it (assess, plan-review, ...), so you can see the path a plan took. The
plan-mutating workflows commit (never push) as they go, so `git log` shows the progression.
