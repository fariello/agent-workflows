- Id: tk1gqo
- Status: open
- Blocks-Release: next
- Set: historder
- Priority: medium
- Work-Kind: bug
- Summary: aw check reports check.lifecycle-transition-invalid on conformant plans: _plan_status_events reverses inline history on a newest-first assumption while the repo's actual convention is oldest-first (9 diagnostics repo-wide, incl. approved plans)

## Workflow history
- 2026-09-09 open (aw set): GATE SATISFIED: spec 2vev8j is APPROVED (2026-09-09, aw set --by-human), so the storage contract this item waited on now exists and is signed off. Unblocked to open. WHAT THE SPEC SETTLES FOR THIS ITEM, restated so nobody re-litigates it: this item's framing question ('is inline ## Workflow history normatively OLDEST-FIRST or NEWEST-FIRST?') is answered NEITHER WAY. Spec 4.3 makes order EXPLICIT via a per-artifact monotonic seq, with the timestamp retained for display only, so the reader stops depending on direction at all: drop events.reverse() (still live at ipd_lifecycle.py:773), the date sort, and the lifecycle-rank tiebreak rather than swapping one for another. Spec 4.4 fixes this item's SECOND defect (tools stamping UTC while authors write local dates) as a separate change, because seq alone still leaves timestamps claiming an evening action happened tomorrow. THE PART THAT UNBLOCKS THIS ITEM'S IRREDUCIBLE RESIDUE: this item recorded 3 cross-day approved -> reviewed round trips that NO reader could distinguish from a real violation. The maintainer RULED during spec review (decision 4.8, recorded as finding SR-007) that a backward lifecycle edge is LEGAL as an explicit recovery transition. So those cases are RECLASSIFIED AS VALID, not suppressed, which is what lets check.lifecycle-transition-invalid reach 0 HONESTLY instead of by weakening the check. That distinction is the whole point of this item and must survive into the implementation. CARRY THIS WARNING INTO THE FIX, because the obvious implementation is wrong: 4.8 removes the forward-only invariant, so the transition table must ENUMERATE which backward edges are legal. An implementation that merely deletes the rank comparison would permit EVERY backward edge, which is NOT what was decided; treat any edge not enumerated as illegal and fail closed. Only approved -> reviewed is named so far. THIRD DEFECT FOUND WHILE WRITING THE SPEC, same class as this item's and live now: attention_contract.py:32-33 defines last_history_at as 'the date of the LAST record in file order' while the plan writers PREPEND (status_set.py:885), so for any tool-touched plan the attention view reads the OLDEST record and calls it the newest. Fix it in the same change. RE-MEASURED 2026-09-09: aw check plans still reports 15 check.lifecycle-transition-invalid; the heading is referenced by 18 modules, not the 19 this item's notes state. Corpus counts in this item (483 plans) and in the spec as authored (591) are both STALE and drifting fast (604 at review time) - re-derive at implementation, do not quote. STILL do not fix only the reader, and still do not reorder the plan histories: both were considered and rejected here, and the spec agrees. NEXT STEP: graduate to a plan citing spec 2vev8j (a plan may carry - From-Spec: 2vev8j), not a direct code change; this item is a bug report, and the design it needs is now approved.
- 2026-09-08 blocked (aw set): GATE RE-POINTED from ms06pi to spec 2vev8j, because ms06pi is now GRADUATED and the thing this item waits on is the storage CONTRACT, which the spec owns. THE SPEC ANSWERS THIS ITEM'S CENTRAL QUESTION, BUT NOT IN EITHER FORM THIS ITEM POSED IT. This item asks: 'is inline ## Workflow history normatively OLDEST-FIRST or NEWEST-FIRST?' and lays out the two branches. Spec 4.3 answers NEITHER: all four research reports independently reject inferring order from file position OR from dates, and make order EXPLICIT via a per-artifact monotonic seq, with the timestamp retained for display only. So this item's framing that the repo must PICK a direction is SUPERSEDED; the contract is to stop depending on direction at all, and the reader gets SIMPLER (drop events.reverse(), the date sort, and the lifecycle-rank tiebreak rather than replacing one with another). That also disposes of the SECOND DEFECT recorded here (tools stamping UTC while authors write local dates): spec 4.4 makes every writer UTC with local time a render-time concern only, and it is a SEPARATE fix because seq alone still leaves timestamps claiming an evening action happened tomorrow. WHAT THIS ITEM CONTRIBUTED THAT THE RESEARCH DID NOT: the four-writer survey recorded here (tools PREPEND, authors APPEND, specs/backlog REPLACE, record_history is order-free) is the evidence base for spec 4.3, and its warning 'do not fix only the reader' is now the spec's position rather than a note on a backlog item. A THIRD writer/reader disagreement was found while writing the spec and is recorded in it as out-of-scope: attention_contract.py:32-33 defines last_history_at as the LAST record in FILE ORDER while the plan writers PREPEND, so for any tool-touched plan the attention view reads the OLDEST record and calls it the newest. Same defect class as this item's, live now, and it should be fixed in the same change rather than discovered afterward. RE-MEASURED AT HEAD 57143149: events.reverse() is still live at ipd_lifecycle.py:773 (this item cites :638 and its 2026-09-08 note cites the reader generally; the line has moved twice), aw check plans reports 15 check.lifecycle-transition-invalid, and the heading is referenced by 18 modules, not the 19 this item's note states. Do NOT read 15 as improvement over the 21 that note reports without checking scope: the count tracks the corpus, which is now 591 plans against the 483 this item's family recorded. STILL BLOCKED, and correctly so: the spec is at to-review, not approved (the anti-self-approval floor requires a review record naming 2vev8j and none exists), and its OQ-1 is BLOCKING on a human policy call, namely whether backward lifecycle edges approved -> reviewed are legal. That question is THIS item's residual 3 cross-day round trips restated as policy: until a human answers it, no reader can be told which of them is a violation. Still do not fix only the reader, and still do not reorder the plan histories.
- 2026-09-08 blocked (aw set): GATE RE-POINTED from research prompt 27rjro to backlog ms06pi, for two reasons. FIRST, MECHANICAL: the prompt moved to reference/202609/ when the awmetastore set was promoted, so the old path-based Gate-Ref dangled. SECOND, AND THE REAL REASON: the research has LANDED (five reports adopted 2026-09-08, reconciled in 6mye7n), so the prompt is no longer the thing this item waits on. What it waits on is the STORAGE DECISION ms06pi owns, exactly as this item's own 2026-09-05 note said ('THE FIX FOR THIS LIVES IN ms06pi'). Gating on the answered prompt would have read as satisfied and invited a reader-only fix, which the maintainer ruling and this item both rejected. WHAT THE RESEARCH SETTLES FOR THIS ITEM SPECIFICALLY: the ordering contract question this item poses ('is inline ## Workflow history normatively OLDEST-FIRST or NEWEST-FIRST?') is answered NEITHER WAY. All four reports independently reject inferring order from file position or from dates, and instead make order EXPLICIT via a per-artifact monotonic seq integer, with the timestamp kept for display only. Sonnet 5 calls seq 'the one piece of this recommendation I would call non-negotiable'; GPT-5.6 puts the reason sharply: 'Timestamps are never the sequencing authority. That eliminates both the day-granularity defect and the UTC-versus-local-date inversion.' So this item's premise that the repo must PICK a direction is superseded: the fix is to stop depending on direction at all. That also disposes of the SECOND DEFECT this item records (tools stamping UTC while authors write local dates), which Sonnet 5 insists needs its own fix since neither change alone suffices. RE-MEASURED AT HEAD 57143149: events.reverse() is still live at ipd_lifecycle.py:773 (this item cites :638; the line moved) and aw check plans reports 15 check.lifecycle-transition-invalid, against the 9 recorded here and the 21 a 2026-09-08 sweep reported. Do NOT read the 15 as improvement without checking scope; the count moves with the corpus, which is now 591 plans / 15.6M chars, up from the 483 this item's family recorded. ONE ADDITION FOR WHOEVER FIXES THE READER: a THIRD writer/reader disagreement was confirmed in the contract text, beyond the ones this item catalogues. attention_contract.py:32-33 defines last_history_at as 'the date of the LAST record in file order' while plan writers PREPEND, so for any tool-touched plan the attention view reads the OLDEST record and calls it the latest. GPT-5.6 alone caught it. It is the same class of defect as this item's, is live now, and should be fixed in the same change rather than found afterward. STILL DO NOT fix only the reader, and still do not reorder the plan histories; both were considered and rejected here and nothing in the research reopens either.
- 2026-09-08 blocked (aw set): REFUSE TO GRADUATE UNTIL THE RESEARCH LANDS. Blocked (was open) so a future graduation attempt is refused by a typed gate rather than by prose an agent may skim past. The gate is research prompt 27rjro (status: todo, unconsumed), which owns the storage-design question this item is a SYMPTOM of; the fix is owned by ms06pi (Set awmetastore, also blocked on the same prompt). MAINTAINER RULING 2026-09-05, unchanged: research the storage question BEFORE touching the reader again; an interim reader patch that took the finding count from 15 to 3 was written, measured, and DELIBERATELY REVERTED rather than committed, and aw check plans stays red meanwhile BY DECISION. Re-measured 2026-09-08 at HEAD 44d4950d during a graduation sweep and NOT graduated for that reason. The defect has WORSENED: 21 check.lifecycle-transition-invalid diagnostics now, against the 9 this item records (12 on Set runanalytics, plus integpath, depreview, orchprobe). NEW SURVEY, which confirms 'do not fix only the reader' from the code: FOUR mutually incompatible orderings ship simultaneously and NO spec adjudicates any of them. Writers: status_set.apply_status_change PREPENDS newest-first (insert at status_set.py:885, contract comment :872-879, docstring :597), and it also serves aw ipd set, aw ipd dependencies set (via status_set.py:1515-1600) and aw ipd finalize (ipd_lifecycle.py:2511); specs._append_history (specs.py:341-365) and backlog._reattach_history (backlog.py:627-650) REPLACE, keeping only the latest line; set_records._inject_history_line (set_records.py:365) inserts at position 2; record_history.append (record_history.py:42-71) is append-only and order-free, and the IPD spec agrees (20260726-1340-01-ipd-spec.spec.md:23, 'append one dated line per workflow touch; never rewrite prior lines'), which BOTH the prepend writer and the replace writers contradict. Readers split the same way: plan_readiness.extract_newest_history_entry (plan_readiness.py:185-204) reads FIRST-as-newest and explicitly warns against 'fixing' it, and it feeds the AUTO-APPROVE path (plan_readiness.py:323, re-exported by oc_runipd.py:70/303 and agy_runipd.py:109); attention_contract.last_history_at (attention_contract.py:530-540) reads LAST-as-newest; ipd_lifecycle._plan_status_events (:751-772) reverses at :770-771. So two readers on the SAME section disagree by construction, and one of them gates auto-approval, which is why a reader-only patch is not merely incomplete but risky. The rule itself is check_engine.check_lifecycle_transitions (:1156-1212, rule constant :1152), scoped to pending/ only (:1176-1180), and it runs ALONGSIDE the authoritative - Status: read (:1165-1166), which is why this is warning-class and blocks no plan's execution. Only ONE written ordering statement exists anywhere and it is not normative: .aw/records/plans/README.md:127 says 'newest-first'. SECOND, SEPARABLE DEFECT re-verified and still live: status_set stamps history dates in UTC (status_set.py:599) while every other writer uses the LOCAL date (specs.py:334-339, backlog.py:330 and :633, record_history.py:59 and :168, releases.py:73, set_records.py:331), so an evening action is dated a day ahead of hand-authored lines in the same file; 724 of 2696 tracked history lines come from that UTC writer. TO UNBLOCK: consume research prompt 27rjro, then graduate through ms06pi. If a future agent is asked to graduate this item, the correct answer is to refuse and cite this gate.
- 2026-09-05 note (opencode its_direct/pt3-claude-opus-5-1m-us): THE FIX FOR THIS LIVES IN `ms06pi` (Set `awmetastore`), filed 2026-09-05 and gated on research prompt `27rjro`. This item is a SYMPTOM of the `awhistory` plans migration that `b0behn` explicitly deferred, not an independent parser bug: plans are the only tree still carrying full inline history (the sidecar holds 108 backlog / 19 specs / 1 plans), which is why the ambiguity appears here and nowhere else. THREE READER FIXES WERE MEASURED LIVE before concluding that: the shipped `events.reverse()` gives 15 findings; a stable sort by date gives 32, i.e. WORSE, because `date` is day-granular so a same-day burst carries no sequence and ties fall back to whichever writer touched the file last; and date-plus-lifecycle-rank gives 3, but it INFERS order from the forward-only invariant rather than knowing it and cannot represent the same-day re-review-after-approval that spec `25kzda:267` explicitly permits. The residual 3 are genuine cross-day `approved -> reviewed` round trips that NO reader can distinguish from a real violation, because the durable record does not carry enough information to reconstruct the sequence - a storage-design defect, not a parsing one. Maintainer ruled 2026-09-05 to research the storage question first (`tmp/notes.md` item 3), so that interim patch was written, measured, and DELIBERATELY REVERTED rather than committed; `aw check plans` stays red on this meanwhile, by decision. Do not fix only the reader.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

FOUND during `/aw plan-review` of Set `wslayout` (review record
`.aw/records/reviews/20260901-wslayout-00-rh5tt6-...review.md`, finding PR-009). Filed rather than worked
around, because the available workaround would make things worse.

THE SYMPTOM. `aw check plans` reports, for each affected plan:

    check.lifecycle-transition-invalid: recorded lifecycle transition 'to-review' -> 'draft' is invalid:
    missing predecessor: backwards transition 'to-review' -> 'draft'

THE CAUSE, measured not assumed. `ipd_lifecycle._plan_status_events` REVERSES the parsed inline history,
on an explicit assumption recorded in its own comment (`agent_workflows/ipd_lifecycle.py:637-638`):

    # Inline history is stored newest-first; reverse to oldest-first for derivation.
    events.reverse()

When a plan stores history OLDEST-FIRST, that reversal inverts the stream, so the derived first
transition runs backwards. Measured on the wslayout orchestrator:

    python3 -c 'from pathlib import Path; from agent_workflows import ipd_lifecycle as IL; \
    p=next(Path(".aw/records/plans/pending").glob("*wslayout-00-rh5tt6*.ipd.md")); \
    print([e[1] for e in IL._plan_status_events(p.read_text())])'
    -> ['to-review', 'draft']      # inverted: the file records draft FIRST, then to-review

THE PLANS ARE NOT AT FAULT; THE ASSUMPTION IS THE SUSPECT PART. The repositorys ACTUAL practice is
OLDEST-FIRST. Sampled from `executed/` (i.e. a plan that completed the whole lifecycle),
`20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md` records
2026-07-23 draft -> 2026-07-25 reframed -> 2026-07-26 executed, oldest first. The `wslayout` plans follow
that same order. So they conform to practice and fail only against the parsers undocumented
expectation.

IT IS PRE-EXISTING AND SYSTEMIC, both verified:
- PRE-EXISTING: reconstructing the plans tree at the wslayout AUTHORING commit `7d222547` (before any
  review edit) and re-running `aw check plans` reproduces all 6 diagnostics. No review edit introduced
  them.
- SYSTEMIC: 9 `check.lifecycle-transition-invalid` diagnostics repo-wide. 6 on wslayout, 3 on unrelated
  plans, and notably two of those are APPROVED plans reporting `approved -> reviewed`:
  `20260830-...-01-6knsrx-land-the-six-verified-wtiso-lane-branches...ipd.md` and
  `20260830-runcodes-01-wlxkoz-the-deterministic-run-finding-code-vocabulary...ipd.md`, plus
  `20260829-...-01-0soncw-collapse-run-inspection-under-aw-runs...ipd.md` reporting `to-review -> draft`.

THE DECISION THIS NEEDS (a repository-contract question, not a per-plan fix): is inline
`## Workflow history` normatively OLDEST-FIRST or NEWEST-FIRST?

- If OLDEST-FIRST (which practice and the executed corpus suggest): the bug is the `events.reverse()` at
  `ipd_lifecycle.py:638` and the comment above it. Fix the parser; no artifact changes.
- If NEWEST-FIRST: then a large corpus of existing plans is non-conformant and needs a migration plus a
  documented, enforced ordering rule. That is much more expensive and should not be adopted by default
  merely because one function assumes it.

Either way the ordering contract must be WRITTEN DOWN (the IPD spec is the natural home) and enforced,
because today an author has no way to learn it except by tripping this rule.

DO NOT "FIX" THIS BY REORDERING PLAN HISTORIES. Reversing the six wslayout histories would satisfy the
parser while contradicting the convention every other plan follows, and would leave the 3 unrelated plans
still failing. That trades a visible tooling warning for an invisible corpus inconsistency. This was
considered and rejected during the review.

BLAST RADIUS TO CHECK WHEN FIXING: `_plan_status_events` feeds `derive_status_from_events` and the
`check.lifecycle-transition-invalid` rule (`agent_workflows/check_engine.py:1039-1052`), which the rule
docstring notes runs ALONGSIDE and does NOT override the authoritative `- Status:` read (`:1052`). That is
why this is a warning-class consistency defect rather than a gate failure, and why it does not block
execution of any plan. Also confirm `aw doctor` and any lifecycle-gate consumer agree after the change.

WHY IT MATTERS DESPITE BEING NON-BLOCKING: 9 warnings that no plan author can correctly resolve train
readers to ignore a real consistency rule. The repo already has a recorded instance of that exact failure
mode in backlog `gjadwm`: "a gate that false-positives on correct behavior TRAINS agents to bypass it."

DECISIVE NEW EVIDENCE (observed 2026-09-01, while approving spec `kw5y2s` with `aw spec set`): THE TOOLS
AND THE AUTHORS DISAGREE INSIDE THE SAME FILE. Running the three legal transitions
`draft -> to-review -> reviewed -> approved` via `aw spec set` PREPENDED each new line to the TOP of
`## Workflow history`, producing this order in `kw5y2s`:

    - 2026-09-02 approved (aw set, --by-human): ...     <- newest, written by the TOOL
    - 2026-09-02 reviewed (aw set): ...                 <- written by the TOOL
    - 2026-09-02 to-review (aw set): ...                <- written by the TOOL
                                                        <- blank line
    - 2026-09-01 draft (antigravity): ...               <- oldest, written by the AUTHOR
    - 2026-09-01 corrected (opencode/...): ...          <- written by the AUTHOR, oldest-first

So the STATUS-SETTING TOOLS write NEWEST-FIRST (consistent with `ipd_lifecycle.py:637-638`), while HUMAN
and AGENT AUTHORS write OLDEST-FIRST (consistent with the executed-plan corpus). A file touched by both
ends up with two opposite orderings separated by a blank line, and no reader or parser can be right about
both halves. This is the same defect surface as `aw ipd dependencies set` prepending its line to the four
`wslayout` children, which is what first exposed the issue.

That makes the contract question sharper, and answerable from the tools' own behavior rather than from
taste: the WRITERS already implement newest-first. Either (a) newest-first is normative, in which case the
authoring convention and the whole oldest-first corpus need a documented migration, or (b) oldest-first is
normative, in which case both the writers (`status_set`/`aw spec set`, `aw ipd dependencies set`) AND the
`events.reverse()` reader must change. Do NOT resolve it by fixing only the reader: that would leave the
writers producing history in an order the corpus contradicts.

SECOND, SEPARATE DEFECT OBSERVED IN THE SAME RUN (worth its own item if confirmed): `aw spec set` stamped
`2026-09-02` while the local date was `2026-09-01`. Measured at the moment of the run:
`date -> 2026-09-01`, `date -u -> 2026-09-02T01:11:42Z`, `date +%z -> -0400`. The tool is stamping history
dates in UTC rather than local time, so any action taken during the local evening is dated one day in the
future relative to every hand-authored line in the same file. That corrupts date-ordered reasoning about
history (including any fix to the ordering question above) and makes an artifact appear to record events
before they were authorized.
