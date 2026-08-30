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

## Decisions: the audit trail for resolving instead of asking

The `plan-review` workflow tells a reviewer to resolve a question from authoritative evidence
rather than asking the maintainer. That rule is deliberate and it is right, but it converts
questions into SILENT CHOICES: a reviewer can make ten judgement calls, get one badly wrong, and
the maintainer discovers it only by reading the code it produced. The `### Decisions` section is
what removes the silence, so a wrong turn is findable AFTER the fact instead of invisible.

Both review variants require a row for EVERY question resolved from evidence instead of asked.
The columns:

| Column | Meaning |
|---|---|
| `ID` | `D-1`, `D-2`, ... within the round. |
| `Question` | What the reviewer would have asked the human. |
| `Chosen` | What it decided. |
| `Alternatives considered` | What it rejected. "None" is a claim, not a default. |
| `Basis` | The `path:line` or artifact that authorized it. |
| `Reversible` | `yes` or `no`, judged on the cost of being wrong. |

Read them back with one command:

```bash
aw reviews decisions                  # every recorded decision
aw reviews decisions --irreversible   # only the ones that cannot be undone
aw reviews decisions c621h9           # one reviewed plan
```

That verb is READ-ONLY and exits 0 even when nothing is recorded, because an empty audit trail is
a valid answer rather than a failure. It reports ALL rounds, not just the current one: a gate asks
"does this plan block today", so a superseded finding must stop counting, but an audit asks "what
did the agents decide", and a decision made in round 1 was still made.

### `Reversible`, and why it changes the obligation

`Reversible` is judged on the COST OF BEING WRONG, not on the reviewer's confidence:

- `yes`: a later maintainer can undo it by editing the plan or the code. Wrong costs a rewrite.
- `no`: it cannot be cleanly undone. Published interfaces, data or file migrations, deletions, a
  released artifact, anything another party may already depend on.

Recording alone is enough for a REVERSIBLE decision. It is NOT enough for an irreversible one,
which must ALSO be surfaced: either raised in the reviewed plan as an open question carrying
`- Blocking: yes` (so the existing pre-execution gate stops the run), or told to the maintainer
directly with that noted on the row. Resolving-instead-of-asking must never silently authorize a
change nobody can undo.

`check.review-decision-unescalated` reports an unescalated `Reversible: no` row as a WARNING. It
is a backstop for a reviewer who skipped the escalation step, not a substitute for doing it: the
preventive control is escalation at decision time. An empty or unrecognized `Reversible` cell is
treated as UNJUDGED (never silently as "reversible"), is visible in the listing, and is reported by
the same rule, because a blank is not a judgement.

Be precise about what that warning does, because "advisory" is easy to overread. A `warning` DOES
contribute to a nonzero `aw check` findings exit; only `info` severity is exempt from the exit
code. What this rule adds is no LIFECYCLE gate: unlike `check.review-finding-unescalated`, it is
not wired into any `aw ipd lint` checkpoint, it cannot refuse a `begin` or `finalize`, and it does
not block a dependency edge. So it can make a check run report findings, and it cannot stop a plan
from executing.

### This tree is the source of truth for review-time decisions

The tracked `.review.md` `## Decisions` section is THE record of what a reviewer decided on its own
authority. It is tracked deliberately: a decision that survives only in a session transcript or an
untracked scratch file is not auditable.

Do not confuse it with `agent_workflows/set_records.py`, which is a DIFFERENT and legitimate
register. That module serves `/exec-set` SET COORDINATION, not plan review, and its untracked
projections under `.aw/workflow-artifacts/` are deliberate ("the local authoritative run
convention"), not a location defect. They already have a tracked counterpart: the same module
writes a tracked walkthrough to `.aw/records/walkthroughs/`, and `promote_local_checkpoints`
promotes an untracked decision checkpoint into it before releasing another lane, specifically "so
a crash never loses a recorded decision". Two registers, two surfaces, both with a tracked source
of truth. A later agent should not "fix" either one into the other.

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

## Enforcement: unfixed gating findings must be escalated

A finding left `open` or `deferred` whose severity is at or above the gate threshold MUST also be
raised in the reviewed plan as an open question carrying `- Blocking: yes` and a `- Finding: <ID>`
subfield naming it:

```markdown
### OQ-03: F-7 leaves the malformed case fail-open; must it be reported?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: F-7
- Resolution or deferral rationale: pending a decision on fail-open vs fail-closed
```

One question may cover several findings (`- Finding: F-3, F-5`). The match is against the typed
`- Finding:` field, never the rationale prose, so an incidental mention of an id cannot satisfy the
rule.

`aw check` reports a violation as `check.review-finding-unescalated` (an error), and `aw ipd lint`
reports it at the `review-finalize` and `pre-execution` checkpoints. It is deliberately NOT checked at
`pre-transition`: by the time a plan finalizes, execution already happened, so a gating finding needed
to stop it earlier.

Only PENDING-lane plans are checked. Terminal plans (`executed/`, `superseded/`, `not-executed/`) are
grandfathered, the same way `check.ipd-draft-ready-to-review` and `check.lifecycle-transition-invalid`
scope themselves, so the existing corpus is never retroactively litigated.

### Why escalation, and not a direct block on the finding

There is deliberately NO second gate that blocks on the finding itself. The escalated open question is
caught by the pre-existing `pre-execution` gate on unresolved blocking questions, so the design reuses
one mechanism instead of keeping two in agreement.

Stated honestly, because the distinction matters: across this repo's executed plans, 28 of 28
`Blocking: yes` open questions are `resolved`. That is a CONSISTENCY fact, not a measured catch rate.
Part of it is tautological, since a blocking question may not be `deferred` (an independent structural
rule), leaving `resolved` as the only legal terminal state; and nothing records whether the checkpoint
gate ever actually stopped a run. The justification for reuse is fewer moving parts, not proven
infallibility.

### What this does and does not catch

The honest claim is narrow: **a RECORDED unfixed gating finding must be escalated.** It is not
"unfixed gating findings are now caught."

| Situation | Behavior |
|---|---|
| No `.review.md` for the plan | SILENT. Nothing to read, so nothing is enforced. |
| `.review.md` present but malformed/unparseable | REPORTED. A file that exists but cannot be trusted is an error, not an absence. |
| Threshold `off` | Rule disabled entirely. |

The absent case is the open evasion path, and it is the state of most plans: a reviewer who writes no
review record is outside deterministic reach. Fail-closing it would mass-fail the whole existing
corpus, so it stays silent by design. Closing that hole would mean gating EMISSION itself, which is
not implemented. This rule also cannot tell whether a severity was classified honestly; a Blocker
mislabeled `MEDIUM` passes.

## Tooling

The parser and writer live in `agent_workflows/review_findings.py`. The parser is pure and never
raises: a malformed row yields a diagnostic while the well-formed rows around it still parse, so one
bad row cannot blind a reader to the rest of the table.
