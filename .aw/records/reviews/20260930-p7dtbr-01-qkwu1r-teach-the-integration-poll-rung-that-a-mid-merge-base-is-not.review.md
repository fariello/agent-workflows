# Review findings: plan qkwu1r

- Subject-Id: qkwu1r
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `1351b8ef`. The plan file was committed and byte-identical to
the lane input (`diff` reported no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `clean` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize` reports `clean` after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator row check does not apply.

THE DIAGNOSIS AND ALL THREE DESIGN JUDGEMENTS SURVIVE, AND I RE-DROVE EVERY MEASUREMENT RATHER THAN
TRUSTING ANY. This is a well-built plan; the findings below are all in its validation bars, not its
analysis.

F-01 reproduces to the field, against the real rung on a real repository:

```
merge rc: 1
merge_in_progress: True
merge_head_commits: ['bcbd6477e9bcc69da91ba60476abb3c9e9fcef06']
overlap(['lanefile.txt']): []
overlap([]): []
status: UU other.txt
OUTCOME: PollOutcome(cleared=True, bound='dirt-cleared', polls=0, last_activity_age=10.0,
  detail='the overlapping dirty path cleared after 0 poll(s); integration is re-attempted through the full revalidate gate')
```

So the rung does report a clear base at zero polls while `MERGE_HEAD` is set, and F-02's sharpening is
correct and is the better framing: the detail sentence affirmatively states that "the overlapping dirty
path cleared" about a base where no dirt ever cleared and nothing was waited for. F-07 reproduces in the
same probe (`overlap([])` is `[]`, so an empty changed-file set also short-circuits to cleared).

F-04 reproduces INCLUDING its trap, which is the measurement that justifies adding no new bound:

```
fresh           merge_in_progress=True age=0.001367330551147461
files only      merge_in_progress=True age=0.4643270969390869
commits+files   merge_in_progress=True age=14400.001791715622
```

Backdating the working-tree mtimes ALONE leaves the age sub-second, because `main_last_activity_age` takes
the NEWER of HEAD commit time and dirty-file mtimes. So E-04's instruction to backdate BOTH is load-bearing,
and a case (c) that aged only the files would pass for the wrong reason. Backdating both exceeds the 3600s
default limit, so an abandoned mid-merge base does exit at the EXISTING staleness bound and a merge-specific
bound would be machinery whose need is disproven.

F-05 IS THE FINDING THAT MAKES THIS CHANGE SAFE AND IT IS CORRECT. I enumerated every use of the returned
outcome: `reattempt_deferred_integrations` writes `bound`, `polls`, `last_activity_age`, `detail` and
`cleared` into `item["integration_poll"]` and emits the same fields as an `ipd-integration-poll` event, and
NO ladder branch reads `outcome.cleared` to decide whether to attempt the integration (the
`integrate_under_repository_lock` call that follows is unconditional on it). `git grep` for
`integration_poll` finds only that write site plus one read in the terminal-resolution event. So the rung is
purely advisory and making it wait longer cannot change any refusal. F-06 holds too (both hosts are thin
delegating wrappers; `poll_for_integration_window` has exactly one non-test call site). F-08's three constant
values are byte-exact as quoted, and F-09's spec check holds (`grep` for all five literals across
`.aw/records/specs/` and `docs/` returns nothing; `records/runs/` is gitignored).

TWO MEASUREMENTS ARE WRONG, AND BOTH ARE VALIDATION BARS AN EXECUTOR WOULD HAVE CHECKED THEMSELVES AGAINST.
That is what makes them worth HIGH rather than LOW: each would have sent a careful executor hunting for a
defect in their own correct work.

FIRST (PR-001): F-03's REPLAY COUNT IS 1 OF 7, NOT 2 OF 7, AND THE AUTHORED SECOND CASE PROVABLY CANNOT BE
REACHED. I replayed `_try_once`'s real structure (overlap, then candidate merge check, then staleness
short-circuit, then poll increment) against all seven injected sequences read out of the two test files:

```
rs wall      -> wall     polls=3 reaches_merge_check=0
rs stale     -> stale    polls=0 reaches_merge_check=0
rs clears    -> cleared  polls=2 reaches_merge_check=1
rs unmeas    -> stale    polls=0 reaches_merge_check=0
cw wall      -> wall     polls=3 reaches_merge_check=0
cw stale     -> stale    polls=0 reaches_merge_check=0
cw unmeas    -> stale    polls=0 reaches_merge_check=0
TOTAL cases reaching new call: 1 of 7
```

The plan names the `test_runner_shared.py` unmeasurable-age case as the second reacher. It injects
`dirty=[['x']]*5`, so overlap is NEVER empty, and `ages=[None]*5` makes it exit `stale` at `polls=0` having
popped exactly one dirty element, so the list is never exhausted and the merge check is never consulted.
THE CONCLUSION IS UNCHANGED: the seam is still REQUIRED, because one reachable case against a nonexistent
`cwd` is one `FileNotFoundError` (re-verified: `merge_in_progress(Path('/nonexistent'))` raises
`FileNotFoundError [Errno 2]`). What changes is the BLAST RADIUS and therefore what V-06 may demand.
`tests/test_contention_wait.py` reaches the new call in NONE of its three cases, so it needs no change at
all, and V-06 as authored told the executor to explain a second reachable case that does not exist or else
"explain what prevented the raise, because F-03 measures that two cases reach the call" - an instruction
that would have had them doubting correct work.

SECOND (PR-002): THE TARGETED REGRESSION BASELINE IS `141 passed`, NOT `24 passed`. Measured per file at
review: `tests/test_runner_shared.py` 126, `tests/test_contention_wait.py` 10,
`tests/test_foreign_merge_refusal.py` 5, and the combined selection reports `141 passed in 31.67s`. An
executor comparing their post-change run against the authored 24 would have read it as having broken 117
tests. I did not find a reading on which 24 is right for that selection.

THE SUITE IS NOT GREEN AND THE PLAN WAS ALREADY HALF-RIGHT ABOUT THE BAR (PR-003). Bare
`python3 -m pytest` at review: `1 failed, 3498 passed, 2 skipped, 3 warnings in 106.98s`, 208 deselected.
The failure is `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`,
a pre-existing date-boundary bug pinning a workflow-history line against a hardcoded date the clock has
passed; it touches nothing this plan declares. Note V-07 ALREADY says to compare failing node ids rather
than totals, which is exactly the right instrument; what was missing was saying that the expected node-id
set is non-empty and that fixing it is forbidden.

A CROSS-PLAN FACT THE PLAN OMITS AND WHICH CHANGES WHOSE DECISION OQ-03 IS (PR-004). APPROVED sibling plan
`8o709f` declares `agent_workflows/runner_shared.py`, measured the SAME empty-input false clear
independently (its F-3 records `poll_for_integration_window(repo, [])` returning
`cleared=True, bound='dirt-cleared', polls=0`), and DEFERRED it in as many words: "whether that degenerate
input deserves its own refusal is a separate judgement about the poll's contract, and is not in this item's
scope". This plan's E-02 changes that behavior as a side effect (its own F-07) and OQ-03 resolves it. So
OQ-03 is answering a question a reviewed sibling explicitly left open rather than an unowned one, which is
worth recording because it is the kind of claim a later reader would otherwise have to rediscover. NO CODE
CONFLICT: that plan narrows `suppress` blocks elsewhere in the module and touches neither the rung nor any
`POLL_BOUND_*` value, and no other pending plan mentions the rung or the bound vocabulary. I did NOT add a
dependency edge: the runner isolates each item in its own worktree and revalidates on merge, so an edge
would delay both plans for no safety gain.

TWO SMALLER ONES. E-07 said to "try `aw backlog note <id6> --message ...`" and to "fall back to a hand edit
of the history section ONLY" if it refuses. The verb EXISTS and is documented for exactly this
(`aw backlog note --help` exits 0; the `aw backlog` help reads "records a history annotation WITHOUT
changing status"), so the conditional framing invited a hand edit of a records file that the plan's own
execution contract forbids elsewhere; the fallback is removed and a refusal is now a finding to report
(PR-005). And the gate carried no statement of the review outcome or of the two corrected bars, which a
reader arriving at the gate first would need (PR-006).

ONE THING I CHECKED AND DID NOT FLAG. OQ-01 resolves the wall-time-exit bound question to the merge value
on the strength of `PollOutcome`'s docstring purpose, and OQ-02 resolves the ordering to overlap-first on a
behavioral ground after measuring that cost does not decide it. Both resolutions are sound and I re-read the
docstring to confirm the first. I also did not flag the timing figures (1.71ms / 2.43ms): the plan already
says explicitly that no timing number is an acceptance bar and that they support the ORDERING argument only,
which is the correct treatment, and the ordering conclusion does not depend on them.

ALSO REPAIRED, AND WORTH RECORDING BECAUSE IT WAS LATENT RATHER THAN CAUSED BY REVIEW: the plan's authored
`## Workflow history` had its `draft` and `to-review` records in OLDEST-FIRST order, which inverts the
documented newest-first convention. Harmless while unnoticed, it became a real `aw check plans` error
(`check.lifecycle-transition-invalid`) the moment a third record was appended above them, because the parser
reads a date group forward and so saw `to-review` -> `draft`. Swapped; `aw check plans` now reports nothing
for this plan, and the `reviewed` transition itself was written through `aw ipd set reviewed` rather than by
hand, so the tooled record exists beside the narrative line.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric E (testing), Rubric G (executability) | Plan F-03 ("exactly 2 of 7 cases reach the new call") and V-06; replay of `_try_once` against all seven injected sequences reporting `1 of 7`; the `rs unmeas` case injecting `dirty=[['x']]*5` with `ages=[None]*5` | F-03's reachability count is wrong and the authored second case CANNOT be reached: the `test_runner_shared.py` unmeasurable-age case never has an empty overlap (so the merge check, placed after overlap, is never consulted) and exits `stale` at `polls=0`. Only the DIRT-CLEARS case reaches it. The conclusion (the seam is required) is unchanged, but V-06 demanded the executor name a second reachable case or else explain what prevented a raise that F-03 says must occur, which would have had them doubting correct work; and it implied `tests/test_contention_wait.py` needs a change when it reaches the call in none of its three cases. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | F-03 corrected with the per-case replay and an explicit statement that the authored second case cannot be reached; E-06's note corrected from "two of the four cases" to one, naming it, and stating `test_contention_wait.py` needs nothing; V-06 now states the EXPECTED answer (one call site in `test_runner_shared.py`, zero in `test_contention_wait.py`), makes a contention-wait change a finding to report, and forbids hunting for a second case. |
| PR-002 | HIGH | IN-SCOPE | Rubric E (honest baselines) | Plan's `## Required tests` ("Baseline ... at `24 passed`"); `pytest <three files> -o addopts=""` at review reporting `141 passed`; per-file 126 / 10 / 5 | The targeted regression baseline is off by 117 tests. An executor comparing a correct post-change run against the authored 24 would read it as a catastrophic regression of their own work, and the plan offers no reading on which 24 is right for that selection. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The bullet now carries the measured `141 passed` with the per-file breakdown, states plainly that the authored 24 was wrong and what it would have caused, and instructs re-derivation in the executing lane since these files grow as siblings land; new F-11 records both figures. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (honest baselines) | Plan's `## Required tests` ("BARE `python3 -m pytest` for the whole suite") and V-07; `python3 -m pytest` at review reporting `1 failed, 3498 passed, 2 skipped`, 208 deselected | The suite is not green, and neither the required-tests section nor V-07 said so, so an executor could misattribute the pre-existing `tests/test_backlog.py` date-boundary failure to their own change or try to fix it. The plan was already half-right: V-07 correctly says to compare failing NODE IDS rather than totals, which is the right instrument; what was missing was that the expected set is non-empty and that fixing it is out of scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The bare-suite bullet now carries the measured tail, names the failure and its cause, states the bar as an unchanged failing node-id set rather than zero failures, and forbids fixing it; V-07's whole-plan evidence clause says the same; new F-11 records it. |
| PR-004 | MEDIUM | UNDER-SCOPE | Rubric G (executability), cross-plan consistency | `grep -ln "poll_for_integration_window\|POLL_BOUND"` over pending plans returning only `8o709f` and this plan; `8o709f`'s `- Status: approved`, its F-3 row, its deferral bullet, and its `- Scope-Paths:` | The plan carries no cross-plan survey despite declaring a heavily contended module, and it misses that an APPROVED sibling measured the same empty-input false clear and explicitly DEFERRED it ("a separate judgement about the poll's contract, and is not in this item's scope"). This plan's E-02 changes that behavior and OQ-03 decides it, so OQ-03 is answering a reviewed sibling's open question rather than an unowned one, which a later reader would otherwise have to rediscover. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-10 records the sibling, the quoted deferral, and the measured absence of any code conflict; OQ-03 now states that it is answering a sibling's explicitly deferred question and that the answer is reversible; a `Cross-plan` bullet added to `## Scope check`. No dependency edge declared (the runner isolates and revalidates). |
| PR-005 | LOW | IN-SCOPE | Rubric G, records discipline | Plan E-07 ("try `aw backlog note ...`. If it refuses ... fall back to a hand edit") and V-07; `aw backlog note --help` exiting 0; `aw backlog --help` describing `note` as "records a history annotation WITHOUT changing status" | E-07 treats the existence of the right tool as unknown and pre-authorizes a hand edit of a records file as the fallback, which the plan's own execution contract forbids elsewhere ("Do NOT edit any file under `.aw/records/` by hand" is the standing repository rule for exactly this). The verb exists and does precisely what the item needs, so the conditional is both unnecessary and an invitation to the wrong route. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now states the verb exists with its help text quoted, mandates it, removes the hand-edit fallback, and makes a refusal a finding to report; V-07 requires the exact invocation and FAILS a hand edit unless the verb's refusal is pasted. |
| PR-006 | LOW | IN-SCOPE | Rubric G (gate completeness) | Plan's `## Approval and execution gate` | The gate states what the human is approving but records no review outcome and no readiness, and a reader who reaches the gate first would not learn that two authored validation bars were corrected, which is the single most useful thing for an executor to know before they start comparing numbers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A `REVIEW OUTCOME` paragraph added ahead of the execution contract, recording `reviewed` plus `- Readiness: go-pending-approval`, that `reviewed` is not approval, and naming both corrected bars so an executor does not chase the two phantom regressions. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | F-03's reachability count is wrong (1 of 7, not 2 of 7). Does that invalidate E-02's injectable-parameter design? | No: keep the seam, correct the count and the blast radius. | Removing the `merge_check` parameter and calling `merge_in_progress` unconditionally, rejected because ONE reachable case is still one `FileNotFoundError` against a nonexistent `cwd`, so the existing `test_runner_shared.py` rung-2 test would break. | Replay over all seven injected sequences showing `rs clears` reaches the call; `merge_in_progress(Path('/nonexistent'))` raising `FileNotFoundError [Errno 2]` re-verified at review. | yes |
| D-2 | An APPROVED sibling (`8o709f`) declares the same module and deferred the question OQ-03 decides. Declare a dependency edge, or record it? | Record it: new finding row, OQ-03 note, and a `Cross-plan` scope bullet. No edge. | Declaring `- Item-Dependencies:` on `8o709f`, rejected because it touches neither `poll_for_integration_window` nor any `POLL_BOUND_*` value, so neither plan needs the other, and an edge delays both. | `8o709f`'s `- Scope-Paths:` and the measured absence of any rung or bound reference in it; AGENTS.md records that the runner gives each item an isolated worktree and returns changes through the merge-and-revalidate gate. | yes |
| D-3 | E-07 pre-authorizes a hand edit of a backlog record if the tool refuses. Keep the fallback? | No: mandate `aw backlog note`, remove the fallback, make a refusal a reportable finding. | Keeping the conditional, rejected because the verb demonstrably exists and does exactly this, and the repository rule is not to hand-edit files under `.aw/records/`. | `aw backlog note --help` exits 0; `aw backlog --help` describes `note` as recording "a history annotation WITHOUT changing status". | yes |
| D-4 | The suite has a pre-existing failure. Fix it, or carry it? | Carry it; the plan now forbids fixing it. | Fixing it inside this plan, rejected as an undeclared out-of-scope edit to another party's test in a shared checkout; this plan declares four paths and none is that test. | The failure is a hardcoded date versus the current date in `tests/test_backlog.py`, touching nothing this plan declares; AGENTS.md's shared-checkout rule. | yes |
| D-5 | Should the plan's timing figures (1.71ms / 2.43ms) be flagged as drifting measurements? | No; no finding raised. | Adding a finding requiring re-derivation, rejected as redundant. | The plan already states explicitly that no timing number in it is an acceptance bar, that the figures are "live values from one machine under one load", and that they support the ORDERING argument only; the ordering conclusion rests on a behavioral reason that does not depend on them. | yes |
