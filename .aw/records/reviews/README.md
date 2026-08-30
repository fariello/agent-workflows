# .aw/records/reviews/

Typed plan-review findings: the machine-readable record of what a `/plan-review` actually found.

A review record (`<...>.review.md`) holds the reviewer's findings table (each row carrying a Severity
and a Decision) and, optionally, the judgement calls the reviewer resolved on its own authority. It
exists so a High or Blocker finding left unfixed is a FACT that tooling can read, rather than prose
buried in a plan's `## Workflow history` line and a session transcript.

## Why this tree exists

Before it, a review's severity classifications survived only as prose. The words `BLOCKER`, `HIGH`,
`Severity`, and `Remediation Risk` appeared zero times in `ipd_lint.py` and `check_engine.py`, so no
gate, check, or report could see them. Scraping them back out of transcripts is unreliable, because
many transcripts contain a verbatim copy of the plan-review workflow (which itself lists those words),
so a scrape conflates instructions with findings.

## Naming

The uniform artifact-naming grammar with the review facet:

```text
YYYYMMDD-<setid>-NN-<id6>-<slug>.review.md
```

`<id6>` is the REVIEWED PLAN's id6, not a fresh identifier. That is the load-bearing choice: the id6
is the repo's stable cross-tree handle (the same role it plays in `From-Backlog`, `From-Spec`, and
`Item-Dependencies`), so the join survives a plan rename. A separate id6 would add a second identity
with no join value and would need its own dangling check in both directions.

## Layout: flat, and reviews do not move

This tree is FLAT. A review does NOT move when the plan it reviewed moves from `plans/pending/` to
`plans/executed/`. That keeps `aw ipd finalize` a single-file transaction instead of one that has to
keep two locations in sync, which is a known class of bug in lifecycle state that is coupled across
locations.

A consequence worth stating plainly: the review file alone does not tell you the plan's disposition.
Look the plan up by its id6 when you need that.

## Rounds

Plans are re-reviewed routinely, so one file holds MULTIPLE rounds as repeated `## Round <N>`
sections, appended in order. The LAST round in the file is the CURRENT one.

Only the current round's findings are live. A gate must read current findings only, or a High raised
in round 1 and fixed in round 2 would block forever.

## Sections

Each `## Round <N>` contains:

- `### Findings` (required), whose columns are exactly the ones the plan-review workflow already
  emits: `ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution`
- `### Decisions` (optional), recording the reviewer's self-resolved judgement calls:
  `ID | Question | Chosen | Alternatives considered | Basis | Reversible`

A review with no autonomous decisions is valid and simply omits the `Decisions` section.

## Enums

Severity, least to most severe:

```text
low | medium | high | blocker
```

Decision, what the reviewer decided to do about the finding:

```text
fixed | deferred | open | replan
```

Only `fixed` counts as resolved. `deferred` is a deliberate decision NOT to fix, so it is unresolved
for gating purposes, as are `open` and `replan`.

## Metadata block

```text
- Plan-Id: <id6 of the reviewed plan>
- Reviewed-At: <YYYY-MM-DD>
- Reviewer: <tool/model that performed the review>
- Verdict: <the plan-review verdict>
```

A review whose `Plan-Id` resolves to no plan is reported by `aw check` as `check.review-dangling`.
That rule is ADVISORY (a warning, not an error): a review left behind by a superseded plan is untidy
rather than dangerous, so it never sets an exit code.

## The gate threshold

The `review_findings_gate` key in `.aw/config/project.json` sets which severity gates:

```json
{ "review_findings_gate": { "block_at": "high" } }
```

`block_at` accepts `medium`, `high`, `blocker`, or `off`. When the key is ABSENT the threshold is
`high`, so the gate is active by default; a malformed value also falls back to `high` rather than
silently disabling the gate. Only an explicit `off` disables it.

## Current status of enforcement

This tree and its format exist. Recording and reading findings by machine works today.

Enforcement does NOT exist yet: at present an unfixed High blocks nothing. Gating on unresolved
findings, cascading to dependent plans, and having the plan-review workflow emit these files
automatically are separate, sequenced pieces of work. Until those land, writing a review record is a
deliberate act by the reviewer.

## Tooling

The parser and writer live in `agent_workflows/review_findings.py`. The parser is pure and never
raises: a malformed row yields a diagnostic while the well-formed rows around it still parse, so one
bad row cannot blind a reader to the rest of the table.
