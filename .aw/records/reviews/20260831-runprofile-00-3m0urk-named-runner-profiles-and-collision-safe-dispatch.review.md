# Review: Named runner profiles and collision-safe run-as dispatch (orchestrator)

- Plan-Id: 3m0urk
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `6a29f9c0`, working tree clean, all six Set members committed and unchanged
(pre-review snapshot correctly skipped). Structural preflight `aw ipd lint --phase author` reports
`conforming` for all six.

This orchestrator is well built on the axis it addresses. It carries eight numbered CID completion
criteria, a stated serial rationale ("Orders 02, 04, and 05 edit cli.py; Order 03 freezes the
host-specific grammar that Order 04 delegates to"), and it already reasons about `rununify` (`5e4sb6`)
explicitly, including CID-8 ("rununify is executed only after re-inventorying this behavior, never
from its older measurement snapshot") and a STOP instruction if extraction has already started. That
is exactly the right instinct, and it is why the finding below is about a DIFFERENT approved plan
rather than about sequencing discipline in general.

ONE BLOCKER, found by intersecting scope paths across the whole pending tree rather than by reading
the plans' prose.

1. PR-001, BLOCKER. The Set builds its entire user-facing grammar on the `aw run` noun, and APPROVED
   `runnamecollapse-01` (`0soncw`) RETIRES that noun. Measured: `aw run as` appears 16 times and
   `aw run ipd` 12 times across the Set, while `0soncw`'s own title is "Collapse run inspection under
   aw runs and retire the aw run noun" and its E-05 ships a deprecation stub that returns a NONZERO
   exit and a message naming `aw runs` for a stale `aw run` invocation. NO plan in this Set mentions
   `0soncw` or `runnamecollapse` even once (grep returns zero across all six files).

   THE TWO PLANS ARE COMPLEMENTARY, NOT CONTRADICTORY, WHICH IS WHY THIS IS A SEQUENCING FINDING AND
   NOT A REPLAN. `0soncw` states its intent plainly: it retires the noun "so the name is free for a
   future driver verb WITHOUT this plan taking on the default-host design that a real `aw run` would
   additionally require." This Set IS that future driver verb. So the correct relationship is
   `0soncw` FIRST (vacate the name, leaving a stub), then this Set (claim the vacated name for real
   dispatch). In that order both land cleanly.

   In the OPPOSITE order the outcome is a live breakage, not a merge conflict: `0soncw` would install
   a deprecation stub over a namespace this Set had just populated, so `aw run as gem` would begin
   printing "use `aw runs`" and exiting nonzero. Both plans also edit `cli.py` and `completion.py`, and
   `0soncw` additionally owns `command_surface.py`, where every new leaf and alias must be declared or
   CI fails.

The other measured collisions are real but ALREADY GOVERNED, so they are recorded as findings without
being raised as blockers: `3cm15q` shares `oc_runipd.py` with NINE approved plans (`1o4eif`, `2c122z`,
`58ha43`, `6knsrx`, `7p9n2v`, `97df1z`, `qcqhj7`, `rchpms`, `y0gg8o`), and `p0l1to`/`ygzq71`/`p7xhhm`
each share `cli.py` with six. The `wtiso` members of that list are the unmerged lane stack that
`6knsrx` exists to land, and this orchestrator's own "STOP and re-review all runner scopes" clause
covers the `rununify` case. What it does not cover is `0soncw`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. Sequencing / G. Plan executability | `0soncw` title and Concern ("retire the `aw run` noun"); its E-05 (`:103-108`) ships a nonzero-exit deprecation stub; its Scope-Paths include `cli.py`, `completion.py` AND `command_surface.py`. Measured across this Set: `aw run as` x16, `aw run ipd` x12; `grep -rln '0soncw\|runnamecollapse'` over all six plans returns NOTHING. | This Set builds its whole grammar on a noun an APPROVED plan is retiring, and never mentions that plan. The two are complementary (`0soncw` explicitly frees the name "for a future driver verb", which is this Set), so the fix is ORDERING, not redesign: `0soncw` must land FIRST. Reversed, `0soncw`'s stub would shadow the namespace this Set just populated and `aw run as <profile>` would start exiting nonzero with "use `aw runs`". | C:Low; U:Medium; S:Low; F:High; Overall:Medium (the fix is a recorded dependency and one CID; the RISK of leaving it is a live command breakage) | OPEN | Cannot be closed by an agent: it is a cross-Set execution-order decision between two artifacts the maintainer owns, and `0soncw` additionally carries its own unresolved blocking OQ-03 (how `aw runs` disambiguates a subcommand from a viewer target), so the prerequisite is not yet executable either. Escalated as blocking OQ-09 on this orchestrator with a recommended order. |
| PR-002 | MEDIUM | IN-SCOPE | B. Sequencing | Computed scope intersection: `3cm15q` <-> `oc_runipd.py` shared with 9 approved plans; `p0l1to`, `ygzq71`, `p7xhhm` <-> `cli.py` shared with 6 each (`0soncw`, `2c122z`, `58ha43`, `6knsrx`, `mjx7ne`, `rchpms`) | The Set's runner-facing children collide broadly with the approved `wtiso` lane stack and its lander `6knsrx`. This is partly governed already (CID-8 and the "STOP and re-review" clause cover `rununify`), but the `wtiso` stack is 26 unmerged commits across five lanes touching the same two files, and no CID names it. A child executing before those lanes land would be writing into files that are about to receive a large merge. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-4 naming the measured collision set per child, and extended the Set's sequencing note so the "STOP and re-review" instruction covers the `wtiso` lane stack and `6knsrx` explicitly, not only `rununify`. |
| PR-003 | LOW | UNDER-SCOPE | C. Clarity | `3m0urk`'s Scope-Paths is `.aw/records/plans/pending` only | The orchestrator declares a records-only scope, which is correct for a plan-of-plans, but that means the CID audit in its V-01 is the ONLY place the Set's cross-cutting claims are verified, and V-01 demands a single very large pasted audit. Not wrong, but a reviewer should know the Set has no other structural safety net. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-5; no scope change (widening an orchestrator's scope would be worse). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the `0soncw` conflict a REPLAN (the Set's grammar is wrong) or a SEQUENCING finding (the order is wrong)? | SEQUENCING. The grammar is sound; only the order is unstated. | REPLAN, i.e. re-author the Set onto a different verb. Rejected on `0soncw`'s own words: it retires the noun "so the name is free for a future driver verb", which is precisely this Set, so the intended end state already has `aw run` owned by a dispatcher. Re-authoring would discard a design both plans agree on. | `0soncw` Concern and `:28-31`; this Set's 16 `aw run as` + 12 `aw run ipd` references | yes |
| D-2 | Resolve the execution order myself, or escalate? | ESCALATE as a blocking open question, with a recommended order (`0soncw` first). | Deciding it here. Rejected for two reasons: it is a cross-Set order between two artifacts whose approval the maintainer owns, and `0soncw` itself still carries an unresolved BLOCKING OQ-03, so the prerequisite cannot be executed yet even if I picked the order. Resolving from evidence is only legitimate when the repository actually answers; here it does not. | `0soncw`'s own blocking OQ-03; plan-review Step 3 ("Never guess a human decision") | yes |

## Round 2

Opened 2026-09-04 at the maintainer's direction, to close round 1's PR-001 now that its stated
danger no longer exists and the ordering it asked for is machine-enforced. A NEW ROUND rather than an
edit to round 1: the gate reads only the CURRENT round, and rewriting a completed round would hide
that the finding was ever open (`.aw/records/reviews/README.md`, "Rounds").

NOTHING ABOUT THIS SET'S CODE CHANGED. What changed is the PREREQUISITE, and it changed in the
direction that removes the hazard:

1. `0soncw` NO LONGER RETIRES THE `aw run` NOUN. Round 1's BLOCKER rested on `0soncw` E-05 leaving
   `aw run` as a deprecation stub returning a NONZERO exit, which would have shadowed the namespace
   this Set populates. That was REVERSED by maintainer ruling 2026-08-31 (`0soncw` OQ-03): the
   surface splits BY DIRECTION, `aw run` SURVIVES as the WRITING verb, and only the nine READ-ONLY
   viewer leaves move to `aw runs`. `aw run as <profile>` was never among those nine.
2. `0soncw` E-05 NOW NAMES THIS SET EXPLICITLY as the intended consumer of the surviving noun: "it is
   the noun the `runprofile` Set then extends with `aw run as <profile>`", and it records the
   conclusion this finding reached: "the ordering (`0soncw` first, then `runprofile`) was settled".
3. `0soncw` IS NOW EXECUTABLE, which round 1 explicitly said it was not. Its OQ-03 was resolved
   2026-08-31 and its OQ-01 on 2026-09-03; it carries `Status: approved`, `Item-Dependencies: none`,
   and zero unresolved blocking questions (verified with `plan_readiness.has_unresolved_blocking_question`).
   So round 1's clause "the prerequisite is not executable yet either" is STALE.
4. THE ORDER IS NOW MACHINE-ENFORCED, not prose. Round 1 said "the fix is ORDERING, not redesign",
   but nothing in this Set's metadata encoded it. Orchestrator `3m0urk` now carries
   `- Item-Dependencies: executed:0soncw`, so the shipped pre-execution dependency preflight refuses
   the Set until `0soncw` reaches `executed`. That is what actually discharges the finding: a
   maintainer ruling in prose cannot stop a runner, and a declared edge can.

WHAT IS NOT CLAIMED. This round re-verifies the SEQUENCING premise only. It does not re-review this
plan's substance, and every other round-1 finding keeps the disposition round 1 gave it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | B. Sequencing / G. Plan executability | `0soncw` E-05 (now `:118-128`): "Do NOT retire the `aw run` noun. REVERSED BY MAINTAINER RULING 2026-08-31 (see OQ-03)... it is the noun the `runprofile` Set then extends with `aw run as <profile>`... the ordering (`0soncw` first, then `runprofile`) was settled"; `0soncw` OQ-03 and OQ-01 both `- Status: resolved`; `0soncw` `- Status: approved` with `- Item-Dependencies: none`; `3m0urk` now carries `- Item-Dependencies: executed:0soncw` | CARRIED FORWARD FROM ROUND 1 AND NOW RESOLVED. The finding was correct when raised: this Set built its grammar on `aw run` while an approved plan was retiring that noun, and no plan in the Set mentioned it. Both halves of the hazard are now gone - `0soncw` was re-scoped to KEEP `aw run` as the writing verb and to name this Set as its consumer, and `0soncw`'s own blocking question is resolved so it is executable. The residual requirement, that `0soncw` land FIRST, is now a declared dependency edge rather than a sentence in an open question. | C:Low; U:Low; S:Low; F:Low; Overall:Low (recording an edge the maintainer had already decided; no code or scope change) | FIXED | Maintainer decision 2026-08-31 (order) plus 2026-09-04 (encode it). `3m0urk` now declares `- Item-Dependencies: executed:0soncw`, so the pre-execution preflight enforces the order for the whole Set. Round 1's recommended order was adopted unchanged; nothing in this plan's scope or design was altered. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Close PR-001 by editing round 1's row, or by appending this round? | APPEND round 2, leaving round 1 intact. | Editing round 1's `OPEN` to `FIXED` in place. Rejected: the reviews README states rounds are appended rather than edited precisely so a superseded finding stops gating WITHOUT erasing that it was raised; an in-place edit would make the record claim the BLOCKER never existed. | `.aw/records/reviews/README.md` ("Rounds": the LAST round is current, only current findings are live); `review_findings.current_findings()` semantics | yes |
| D-2 | Put the enforcing edge on the orchestrator `3m0urk`, or on all six Set members? | ON THE ORCHESTRATOR ONLY. | An edge on each of the six children. Rejected: the children already chain to each other (`f2mrsw` -> `executed:0soncw` plus `p0l1to` -> `executed:f2mrsw` and onward), so one edge at Order 0 gates the Set's entry point, and six copies of one cross-Set fact invite six inconsistent answers - the same reasoning round 1's own D-1 used to escalate once rather than six times. | Round 1 D-1 on this Set; the per-child `Item-Dependencies` chain measured across Orders 1-5; `3m0urk` is Order 0 | yes |
