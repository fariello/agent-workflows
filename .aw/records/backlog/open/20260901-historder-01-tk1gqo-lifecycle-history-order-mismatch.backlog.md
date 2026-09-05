- Id: tk1gqo
- Status: open
- Blocks-Release: next
- Set: historder
- Priority: medium
- Work-Kind: bug
- Summary: aw check reports check.lifecycle-transition-invalid on conformant plans: _plan_status_events reverses inline history on a newest-first assumption while the repo's actual convention is oldest-first (9 diagnostics repo-wide, incl. approved plans)

## Workflow history
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
