# Review findings: plan w5uowt

- Subject-Id: w5uowt
- Subject-Type: ipd
- Reviewed-At: 2026-10-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in a lane worktree at HEAD `f763f73f6`. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after with zero findings. No pre-review snapshot was owed: `git status --porcelain` was
empty, so the plan was committed and unmodified. NO PRODUCTION FILE WAS MODIFIED at the end of this
review: the three-site prototype written to drive the fix was reverted with `git checkout --`, the
`tmp/` probe directory was removed, and `git status --porcelain` is empty apart from the two planning
documents this review authored.

THE DEFECT, THE MECHANISM AND THE CELL ACCOUNTING ALL RE-MEASURED EXACTLY. F-01 reproduces verbatim:
a one-item queue with `action: "review"`, `status: "reviewed"`, a non-empty `attempts` list and
`review_integrated: False` renders `Outcome: COMPLETED` and, directly beneath the table,
`STRANDED WORK - NOT IN YOUR PROJECT:` followed by
`• rev001: REVIEW NOT INTEGRATED; its work is on its review lane (no branch recorded)`. F-02
reproduces: for that same item `review_integration_was_refused` is `True` while
`integration_was_refused` is `False`, which is precisely why the section prints and the headline does
not. F-04's 64-cell baseline reproduces CELL FOR CELL, including the sixteen statuses, the fourteen
REVIEW cells the fix changes, and the nine failure/blocked/interrupted statuses it must leave alone.
F-06 is exact and its point stands: `grep -c "render_stream" tests/test_run_summary_table.py` returns
`0`, while `tests/test_zero_dispatch_outcome.py` has 76 references and owns `_item`, `_state`,
`_outcome_word` and the sibling exec-stranded fence case, so the plan is right to decline the backlog
item's named target. F-08's import hazard was honored throughout (`render_stream.__file__` asserted
inside this lane before trusting any cell). F-09 holds: the recovery section keys only on the
predicate and ignores status.

THE SUBSTANTIVE FINDING IS PR-001, and it exists because the world moved under the plan. Sibling plan
`entv1d` has EXECUTED since authoring and its deliverable is exactly the predicate this ladder needs,
so the plan's prescribed implementation is no longer the right one even though its prescribed BEHAVIOR
is unchanged. This was established by driving the corrected fix, not by reasoning about it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric C (use existing canonical mechanisms, avoid duplicate paths); the plan's own "ONE PREDICATE, MANY SURFACES, NEVER A SECOND COPY" convention note | `agent_workflows/render_stream.py` `work_did_not_land` ("This is the one question the exit code and the headline must both ask so the two cannot drift"); `git log --oneline -S "def work_did_not_land" -- agent_workflows/render_stream.py` -> `12804f8c8 work(entv1d)`; `agent_workflows/runner_shared.py` importing and calling it at two exit-code sites; the plan's E-03, OQ-02 and Step 0 convention bullet | **E-03 PRESCRIBES HAND-ROLLING A DISJUNCTION THAT ALREADY SHIPS, WHICH DEFEATS THE ANTI-DRIFT PROPERTY IT WAS ADDED FOR.** The plan instructs the executor to ask `review_integration_was_refused` in addition to `integration_was_refused` at three ladder sites. Since authoring, `entv1d` executed and added `work_did_not_land`, which composes exactly those two and whose docstring names the HEADLINE (this plan) as the second surface that must ask it. Writing `A or B` by hand at three sites would create a second copy of a shipped composition, so a future change to what "stranded" means would have to be made in two places - the precise drift the symbol prevents - and it contradicts the convention this plan's own Step 0 section records. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires calling `work_did_not_land` at all three sites and forbids a hand-rolled disjunction; its expected outcome, the Proposed-changes list, `- Scope:`, the Goal, V-03 and the scope fence were all swept to match. DEMONSTRATED rather than asserted: the substitution was applied at review HEAD and the 64-cell probe re-run, yielding exactly F-04's fourteen changed REVIEW cells and ZERO changed EXEC cells, so the corrected implementation is behaviorally identical to the original prescription (new F-10). The twin-tuple hazard was independently confirmed by counting occurrences: the success-guard line appears exactly twice and the `STRANDED` arm once, so a correct diff touches three conditions. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (plan executability); evidence freshness | `ls .aw/records/plans/executed/*entv1d*` resolving with `- Status: executed`; `grep -rn "work_did_not_land" agent_workflows/` naming `runner_shared.py`; the plan's F-03, F-07 and OQ-02 | **TWO FINDINGS AND AN OPEN QUESTION DESCRIBE A WORLD THAT NO LONGER EXISTS.** F-03 states `review_integration_was_refused` "HAS EXACTLY ONE CONSUMER"; it now has two, the second being the composed `work_did_not_land`, which `runner_shared` consumes at two exit-code sites. F-07 describes `entv1d` as "Approved plan ... `pending/`, `- Status: approved`"; it is executed. OQ-02 reasons carefully about whether to declare a dependency edge on a plan that has already run, which is unanswerable rather than merely answered. Each finding's CONCLUSION survives - no ladder site asks the review question, and no edge is owed - but an executor reading them would coordinate against a plan that has already landed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-03 rewritten as SUPERSEDED with the new consumer census and an explicit note that its mechanism conclusion is unchanged; F-07 rewritten as STALE, recording that every substantive claim in it still holds but is now history, and that its landing retires the ordering question; OQ-02 gains a resolution update recording that the question is moot and that its own anticipated contingency has become E-03's instruction. The Goal paragraph now states that `entv1d`'s landing SIMPLIFIES this plan rather than complicating it. |
| PR-003 | LOW | IN-SCOPE | live-artifact re-derivation convention | `python3 -m pytest tests/test_backlog.py -o addopts="" -q -k release_exempt_setter_roundtrip` -> `1 passed`; bare `python3 -m pytest` with the prototype -> `3818 passed, 2 skipped, 3 warnings` | **THE "EXPECTED" PRE-EXISTING FAILURE IS GONE, SO THE VALIDATION BAR NOW BRACES AN EXECUTOR FOR THE WRONG OUTCOME.** F-05 and Required-tests item 1 both lead with `1 failed, 3414 passed` and a date-rollover flake in `test_release_exempt_setter_roundtrip_and_parity`. Re-measured at review that test passes on its own and the full suite with the prototype applied is FULLY GREEN at `3818 passed, 2 skipped`. The plan's own text already allowed for this, so it is not wrong, but an executor reading F-05 first would treat a genuine new failure as the expected one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Required-tests item 1 now leads with "EXPECT A FULLY GREEN RUN", states that any failure is a REGRESSION with the one named exception, and instructs the executor to RE-DERIVE the count rather than compare against `3818` or `3414` (both live populations). F-05 carries an inline correction pointing at the new F-11, which records both re-measurements. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `entv1d` landed a composed predicate mid-flight. Should E-03 keep naming the two predicates separately, or switch to calling `work_did_not_land`? | Switch to `work_did_not_land` at all three sites, and forbid a hand-rolled disjunction. | (a) Keep the two-predicate spelling: rejected because it duplicates a shipped composition, so a future change to the meaning of "stranded" would need editing in two places, which is exactly the drift `work_did_not_land`'s docstring says it exists to prevent, and it contradicts the plan's own recorded "NEVER A SECOND COPY" convention. (b) Mark the plan `REPLAN` because its premise moved: rejected as disproportionate - the DEFECT, the cell accounting, the test siting and all six E-05 cases are untouched, and the change is a one-symbol substitution at the same three sites. (c) Leave the choice to the executor as OQ-02 originally permitted: rejected because a MAY on a now-settled fact invites the duplicate, and the review has measured which spelling is correct. | `work_did_not_land`'s docstring names the exit code and the headline as the two surfaces that must ask one question; `runner_shared` already consumes it, proving it exported and callable; the substitution was driven at review HEAD and produced exactly F-04's fourteen REVIEW cells with zero EXEC cells, so behavior is identical; the plan's Step 0 section already records the convention. | yes |
| D-2 | `entv1d` has executed, so F-03, F-07 and OQ-02 are stale. Rewrite them, or leave them as point-in-time records with a note? | Rewrite each in place as SUPERSEDED or STALE, preserving the original claim, the measurement that replaced it, and an explicit statement of which conclusions survive. | (a) Leave them untouched as honest authoring-time snapshots: rejected because an executor coordinating against a plan described as `pending/` and `approved` would look for a plan to wait on or merge with, and F-03's "exactly one consumer" would make the duplicate-disjunction mistake look safe. (b) Delete the stale rows: rejected because the original measurements were true when taken and deleting them destroys the audit trail of why the plan was shaped as it was. | The repository's convention of recording a superseded measurement beside its replacement rather than overwriting it (used by this plan's own F-05 row and by neighbouring reviewed plans); `ls` and `git log -S` both re-measured at review; each finding's surviving conclusion verified independently by reading the three ladder conditions and both predicate bodies. | yes |

### Deferred and open

(none)

OQ-01 remains `resolved` and this review did not reopen it, but it was independently re-verified
because it is the one consequence a human should weigh: the fourteen changed cells include ten beyond
the obvious four, and the resolution rests on two measurable claims that both hold at review HEAD.
The EXEC shape already renders `STRANDED` for `queued`, `not-attempted` and `retired` (confirmed in
the baseline's EXEC column, unchanged by the fix), and `format_stranded_work_section` ignores status
entirely, so the body already names those items stranded. Fencing the review shape would therefore
create a second inconsistency of exactly the kind the plan exists to remove. OQ-02 is `resolved` and
now moot; see PR-002.
