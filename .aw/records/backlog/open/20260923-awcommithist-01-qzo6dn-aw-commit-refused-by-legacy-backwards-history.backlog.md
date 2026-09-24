- Id: qzo6dn
- Status: open
- Blocks-Release: next
- Set: awcommithist
- Priority: medium
- Work-Kind: bug
- Summary: aw commit refuses any edit to three plans whose PRE-EXISTING history records a backwards reviewed->to-review transition, so the tooled commit path is unusable on them

## Workflow history
- 2026-09-23 created (aw backlog): filed while executing m7gvuz: aw commit's plan half refuses on a pre-existing backwards history transition, forcing agents onto --no-plan and thereby skipping Scope-Paths enforcement

MEASURED 2026-09-23 at HEAD 5fea858f while executing m7gvuz (run-20260923T023317Z-3622079).

WHAT IS WRONG. `aw commit <plan> -- <paths>` runs the shared policy engine over the plan
and REFUSES on `check.lifecycle-transition-invalid` when the plan's OWN `## Workflow
history` records a backwards transition. Three pending plans carry exactly that today, and
none of the three records was written by the agent now trying to commit:

    20260907-orchprobe-00-yeh7gc  (reviewed -> to-review)
    20260907-orchprobe-03-m7gvuz  (reviewed -> to-review)
    20260829-rununify-00-5e4sb6

For m7gvuz the offending pair is a `2026-09-07 reviewed` entry followed by a `2026-09-08
to-review` entry, both predating this turn. Verified pre-existing by reverting the working
copy to HEAD and re-running `aw check`: the finding is IDENTICAL with a clean tree, so it is
a property of the committed file and not of any pending edit.

WHY IT MATTERS RATHER THAN BEING COSMETIC. The refusal is total, not scoped to the bad
field: it blocks committing ANY path under that plan's authority, including an evidence or
history-only records edit that touches nothing the finding is about. AGENTS.md makes the
tooled path mandatory ("You MUST commit through `aw commit`, not raw `git commit`"), so an
agent legitimately recording evidence on one of these three plans is left with no compliant
route and must fall back to `--no-plan`, which is documented for paths NO plan governs and
therefore SKIPS the Scope-Paths enforcement the plan half exists to apply. So the practical
effect of a stale history line is to DISABLE scope enforcement for that plan, which is the
opposite of what the gate wants.

NOTE THE TRANSITION IS ALSO ARGUABLY LEGITIMATE. Sending a `reviewed` plan back to
`to-review` after revisions is a real workflow move (the plan-review workflow does it), so
the predicate may be over-strict rather than the records being wrong. Decide which before
fixing: if backwards-to-`to-review` is legal, relax the predicate; if it is not, the three
records need a tooled correction, and either way `aw commit`'s plan half should not be
all-or-nothing on a history finding that is unrelated to the staged paths.

REPRODUCTION.

    aw commit --no-commit -m msg m7gvuz -- <any path>
    # aw commit: refusing - 1 finding(s) on ...m7gvuz...ipd.md:
    #   check.lifecycle-transition-invalid: recorded lifecycle transition
    #   'reviewed' -> 'to-review' is invalid: missing predecessor:
    #   backwards transition 'reviewed' -> 'to-review'

    aw check   # same finding on all three plans with a CLEAN working tree
