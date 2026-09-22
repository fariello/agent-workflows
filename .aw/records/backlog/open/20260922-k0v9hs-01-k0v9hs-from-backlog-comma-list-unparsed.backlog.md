- Id: k0v9hs
- Status: open
- Blocks-Release: next
- Set: k0v9hs
- Priority: medium
- Work-Kind: bug
- Summary: A comma-separated From-Backlog value resolves to NOTHING: the shared regex matches a single token to end of line, so every gate and check reading it sees no source at all

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan lc4unl (planprio Order 03).

## Detail

WHAT IS WRONG. `check_engine._META_FROM_BACKLOG_RE` (`agent_workflows/check_engine.py:2767`) is

    (?m)^- From-Backlog:[ \t]*(\S+)[ \t]*$

so it matches ONE non-space token followed only by optional trailing whitespace and end of line. A
value naming two source items, which the corpus actually contains, matches NOTHING at all: not the
first id6, not a partial, nothing. The link is therefore invisible to every consumer of that regex
rather than half-read, which is why no existing check reports it.

REPRODUCED, not reasoned about. The live plan
`.aw/records/plans/pending/20260917-hostdedup-02-nmlx47-unify-the-twelve-small-divergent-symbols-behind-hostlabels.ipd.md`
carries `- From-Backlog: dstnso, 8hx3g3`, and both named items exist
(`.aw/records/backlog/open/20260917-dstnso-01-dstnso-execute-item-closure-forks-unclaimed.backlog.md`,
`.aw/records/backlog/open/20260916-rununify-01-8hx3g3-rununify-group-e-lane-prompt-flag.backlog.md`).
Driven in-process:

    >>> from agent_workflows import check_engine as ce
    >>> ce._META_FROM_BACKLOG_RE.findall(open(<that plan>).read())
    []

WHY IT MATTERS RATHER THAN BEING COSMETIC. That regex feeds the release-gate preservation machinery:
`_from_backlog_carrier_index`, `find_from_backlog_plans` / `_specs` / `_artifacts`, and through them
the close-legitimacy predicate `evaluate_blocking_close` plus the `aw check` rules
`check.blocking-item-closed-without-gate` and `check.from-backlog-gate-mismatch`. So a plan that
HAS graduated from a release-blocking item is not recognized as its HANDOFF carrier, and the
consequence runs both ways: `aw backlog set done` can refuse a legitimate close whose gate really was
handed off, and the gate-mismatch rule cannot compare a gate it cannot see. Note the FORWARD check
`check.from-backlog-dangling` is unaffected (an unparsed line simply is not scanned), so the corpus
looks clean while the handoff is silently unreadable.

WHETHER A COMMA LIST IS EVEN LEGAL is the first thing to settle, and it is a real question rather
than an obvious yes: `aw ipd set --from-backlog` takes a single value, and a plan graduating from two
items may instead be a sign the plan should be split. Either answer is a fix. If multi-source is
legal, the regex and its consumers must split on commas and the gate comparison must define what
"the same `Blocks-Release`" means across several sources. If it is not legal, a new deterministic
`aw check` rule must REFUSE the value so it cannot sit unread in the corpus, which is what happens
today.

HOW IT WAS NOTICED. Plan `lc4unl` derives its population as "pending plans with no resolvable
`- From-Backlog:`". Mirroring the shipped regex put `nmlx47` IN that population (18 plans); reading
the comma list put it OUT (17). The plan recorded the divergence as DECISION 15-lc4unl-D1 and chose
the semantic reading, because `nmlx47` demonstrably has a source to inherit from. The fix belongs
here, in the shared parser, not in a plan's one-off script; `lc4unl`'s `- Scope-Paths:` is the
pending plans tree and may not touch `check_engine.py`.
