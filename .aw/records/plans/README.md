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

To transition a plan's status and move it between disposition directories, use `aw ipd set` or `aw set`:
- `aw ipd set <status> <id6|setid|fname>...` (e.g. `aw ipd set approved pl0001`, `aw ipd set to-review my-set`)
- `aw set approved <id6|setid|fname>...` (untyped, transitions plans, specs, prompts, backlog, or entire sets)

## Identity, sets, and the clustering filename grammar

Every plan carries a stable `- Id:` (a 6-char base36 citation handle that never changes across
renames/regrouping) and a `- Set:` grouping. Cite a plan by its `Id`; the tooling resolves it via the
manifest, so a plan can be re-slugged or regrouped without breaking citations (plans-adopter,
DECISIONS D124).

- `- Id: <id6>` - the stable handle (emitted by `aw ipd scaffold`, backfilled by `aw ipd sync`).
- `- Set: <terse-id> (<descriptive>)` - the terse id is the canonical grouping key (the leading
  token before the parenthetical); the parenthetical is a human-readable name. A SINGLETON is a set
  of one (no special-casing).
- `- Order: <n>` - the position within the set.

The plan FILENAME clusters by Set so members are adjacent in a name-sorted tree:
`YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`. Do NOT hand-name plans or hand-maintain the manifest; use
the `aw plans` verbs (below). Set membership/order changes on a plan already in a terminal directory
are a deliberate, tool-driven, citation-safe act (the plan BODY and workflow history stay immutable;
only the name/grouping is mutable via the stable `Id`).

## The plans manifest and weekly shards

- `aw plans index [--check]` regenerates `.aw/records/plans/INDEX.json` (every plan) and `INDEX.md` (a
  browse-by-`Set:` view, the most-recent Sets); `--check` fails on drift (missing/invalid `Id`,
  name-vs-metadata mismatch, stale view, dangling plan citation). `aw plans find` queries the
  manifest. This complements the disposition-grouped `STATUS.md`.
- `aw plans set-assign`/`mv` (re)assign a plan's Set/Order and optionally rename it to the clustering
  grammar, keeping the `Id` and rewriting citations.
- `aw plans archive` deep-shelves aged terminal plans into monthly `YYYYMM/` shards INSIDE their
  disposition dir (`executed/`, `superseded/`, `not-executed/`); `pending/` and `reusable/` stay
  flat. Shards are created on demand by this deliberate verb (never a background side effect); the
  manifest scan is recursive so sharded plans stay visible.

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
5. The lifecycle move on completion (`git mv` to the terminal directory, set `Status:`,
   append a `## Workflow history` line). The supported way to perform this terminal transition
   is `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`, which runs the
   pre/post-transition gates, verifies the changed paths stayed within the reviewed `Scope-Paths`
   against the `aw ipd begin` receipt's frozen base, writes the attributed history, moves the plan,
   refreshes the owned index fail-loud, and makes the path-scoped lifecycle commit in one atomic
   transaction (see `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md`).

This restates, at the plan level, the standing `AGENT-WORKFLOWS` execution contract (see the
managed block in `AGENTS.md` and `CONTRIBUTING.md`); `/plan-review` and `/plan-review-long`
verify it is present and add it if missing.
