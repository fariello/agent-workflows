# Review findings: plan bwo8hp

- Subject-Id: bwo8hp
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0d6e70a5` in a lane worktree (the plan was authored at `231ded51`, five merges
earlier). Structural preflight `aw ipd lint --phase author --agent` CONFORMED before revision
(exit 0, `findings: 0`) and `--phase review-finalize --agent` conforms after revision with zero
findings. No pre-review snapshot was owed: the plan was committed and unmodified, and
`git status --short` was empty at review start. The plan carries `- Kind: child`, so the
`IPD-S407` orchestrator checklist-row check does not apply. No production code and no workflow body
was modified by this review; the two workflow-body hashes, the gate exemptions, and the history-
predicate behavior were all measured with probes that were fully reverted.

THE PLAN'S DIAGNOSIS IS ENTIRELY CORRECT AND ITS CHOSEN ROUTE IS THE RIGHT ONE. Every one of the
eleven authored findings was independently re-derived, and the three that carry the plan's
argument reproduce word for word. F-01: `u23gbn` V-02's `Required evidence` contains the demand
verbatim, once. F-02: both contradicting sentences are present verbatim, E-06's
"in this ordering a refusal leaves the commit UNREACHABLE FROM main ... so it is NOT
`PHASE_COMMITTED_INCOMPLETE`" and V-06's "`PHASE_COMMITTED_INCOMPLETE` would be a FALSE
classification", with `PHASE_COMMITTED_INCOMPLETE` occurring 12 times in that file. F-03: the
`Observed evidence` block opens by reporting the demand unsatisfiable by construction and pastes
the measurement. F-04 was exercised END TO END at review rather than trusted: a probe note inserted
as the first history record and staged produced `git diff --cached --numstat` = `1 0`,
`ipd-executed-gate` exit 0 and `ipd-status-untooled-gate` exit 0, after which the probe was fully
reverted leaving `git status --short` empty and zero matches for the probe string. Both exemptions
were then confirmed AT SOURCE, not inferred: `check_engine.check_status_untooled`'s docstring and
body skip `/executed/` paths and fire only on a changed staged `- Status:`, and the executed gate
binds its exemption to `same_plan_at_head` with `moved_into_executed`/`gained_executed` false.
F-07 reproduces exactly (`aw ipd note` -> `invalid choice: 'note'`). F-09 reproduces digit for
digit against `manifest.hash_content`. F-10's precedent reads as described in the `x7i14a` review
record's PR-801 row and D-2.

THE MATERIAL FINDINGS ARE ABOUT THE PLAN'S MEASUREMENTS AND ANCHORS, NOT ITS DESIGN. Nothing in
the four E-items was removed or re-scoped; the route (append-only note, sweep obligation in both
revise steps, third disposition case in Dimension 1) survives review intact, and the Deferred
refusal of a deterministic lint rule is strengthened rather than weakened. What review changed is
the EVIDENCE the plan rests on and the executability of three edit anchors.

THE MOST CONSEQUENTIAL FINDING IS PR-003, AND IT WOULD HAVE COST THE EXECUTOR REAL CONFUSION. All
three of the plan's edit anchors are quoted as whole SENTENCES, and all three sentences are
line-wrapped in their files, so each matches nothing as a single-line string. Measured with
`str.count()` on the file text: `plan-review.md`'s "When a finding spans plans, fix it in the
owning plan and cross-reference it from dependent plans." -> 0 single-line occurrences (it wraps
after "cross-reference it"); `02-review-and-revise.md`'s "For cross-plan findings, fix the owning
plan and cross-reference dependent plans. Do not duplicate requirements." -> 0 (it wraps after
"cross-reference dependent"); `intent-audit.md`'s "A requirement whose `V-*` evidence is empty or
was never run is NOT satisfied, regardless of the `E-*` checkbox" -> 0 (it wraps after "empty
or"). V-03 and V-04 compounded this by instructing the executor to PROVE the anchors were hit by
showing those context lines. An executor grepping for any of the three would have gotten zero hits
and reasonably concluded the anchor had been removed, on a plan whose entire subject is a stale
quotation surviving a correction. All three anchors are now stated as verified-unique single-line
FRAGMENTS, with the wrap widths named and the file-end boundaries given so a hunk cannot land
outside its section.

THE SECOND MATERIAL FINDING IS PR-001: THE AUTHORED SUITE BASELINE IS SPENT AND WOULD HAVE READ AS
A 60-TEST REGRESSION. Authoring recorded `2935 passed, 2 skipped, 3 warnings in 44.07s` at
`231ded51`. Re-measured at review on a clean worktree at `0d6e70a5`, the bare suite reports
`1 failed, 2995 passed, 2 skipped, 3 warnings in 62.88s`. Sixty tests arrived in the five plans
merged since. Worse for the executor, the ONE failure is pre-existing and unrelated:
`tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once`
fails at `assert not sat` (`tests/test_dependency_block_reporting.py:122`) because it hardcodes the
dependency `executed:5o1jye` and `5o1jye` has since reached `executed/`, so the edge it expects
unsatisfied is now satisfied. It reproduces with zero staged or unstaged changes. A plan whose
honesty rule tells the executor to paste the real summary and compare it against `2935 passed`
would have handed them a red suite and a 60-test gap to explain on a four-file prose change. The
requirement now names the exact node id as the expected pre-existing red, states the bar as
"that one node id and no other, count at or above 2995", and cites `verify-execution` Dimension 3's
attribution rule. The companion command's baseline was also corrected: `3 passed in 0.13s` was the
FIRST MODULE ALONE, while the command the plan writes runs the PAIR, which is `33 passed in 0.90s`.

THE THIRD IS PR-002, WHICH STRENGTHENS THE PLAN'S OWN DEFERRED REFUSAL. F-03 claimed exactly THREE
V-items in 797 executed plans report their demand unsatisfiable, and that number is the stated
basis for refusing a deterministic lint rule. Re-measured over all 802 executed plans with a wider
pattern set, the scan returns 24 matching items, of which about four are genuine members: the rest
are a test class NAME (`AnUnsatisfiableDependencyBlocksRatherThanStalls` in `ty3cj6` V-02), a
refusal CODE (`REFUSE_UNSATISFIABLE_DEPENDENCY`, four items in `jdn790`), an `assertIs` form
described as unsatisfiable (`li44r9` V-02), and a sentence about tests that "cannot exist while the
change is stashed" (`97df1z` V-03). The corrected measurement is a BETTER refusal than the authored
one: a keyword-level rule is wrong five times in six before it attempts the semantic half at all,
which is a precision argument rather than a volume argument.

AND THE MISSED CASE IS THE PLAN'S BEST ARGUMENT, recorded as new F-12. `76fgt1` (executed
2026-09-28, present in the tree at the authoring HEAD and so missable by the narrower pattern
rather than merely newer) shipped a V-item of exactly the same shape: V-03 as authored required
`aw oc profile add --help` "showing ... `--agent` absent", which is false because `p_ocp_add`
declares `parents=[common]`. Its REVIEW caught it (F-10, escalated to OQ-03) and inverted the
requirement in place before execution, recording in the V-item itself that the old wording "is
FALSE and unsatisfiable", and its F-10 names precisely the hazard E-03 exists to avert: "An
executor taking V-03 literally would find the requirement unmeetable and could 'fix' it by removing
`--agent` from the shared parent". So the class recurs, and the two instances differ only in
whether review caught it: caught cost one findings row, missed cost an execution-time contradiction
and this plan. That is the measured case for the revise-step obligation, and it is now in the Goal
and in the Deferred entry as the positive control.

PR-004 IS THE ONE FINDING ABOUT THE PLAN'S SUBSTANCE RATHER THAN ITS EVIDENCE, and it is a real
under-scope. E-03 was to write the obligation in the backlog item's own words, "sweep every V-item
that quotes the old one". That framing is narrower than the failure, and `u23gbn` proves it in its
own text: E-06's corrected bullet ends "rather than inheriting E-02's wording", so the first stale
sibling round 3 met was an **E**-item it noticed and instructed around, and the one it MISSED was a
V-item. A `V-*`-only rule would not have flagged what that round already half-saw. E-03 now scopes
the obligation over every item, field and prose block (`E-*`, `V-*`, findings, `## Proposed
changes`, the gate, `- Scope-Paths:`), and adds that the sweep runs against the plan as it NOW
READS rather than against the reviewer's own diff, since round 3 was correcting round 2. Recorded
as new F-13 and OQ-03.

PR-005 AND PR-006 ARE SMALL BUT WOULD EACH HAVE FAILED A VALIDATION ITEM. PR-005: E-01 and E-04
both describe `u23gbn` V-02 as pasting a `git merge-base --is-ancestor` measurement, and that
literal string is NOT in V-02's evidence block (it pastes the RESULT, `is the abandoned commit an
ancestor of HEAD: False`; the `git merge-base` spelling belongs to the sibling V-06). E-01's note
would have sent the next reader looking for absent text, and E-04's calibrated example would have
taught an auditor to accept a paraphrase while claiming to demand a measurement. PR-006: V-01
instructs driving `plan_readiness.is_plan_review_approved` against the file, and that function
takes a `Path` (it calls `plan_path.read_text(...)`) while its companion
`extract_newest_history_entry` takes TEXT; passing text raises
`AttributeError: 'str' object has no attribute 'read_text'`, which cost a probe attempt at review.
The same finding widened F-08, which had probed only ONE of several consumers of the section E-01
inserts into: `newest_verdict`, `history_has_review_record` and `ipd_lifecycle._plan_status_events`
were each driven before and after and are all unchanged, so the placement is now verified against
four predicates rather than one.

PR-009 IS A FALSE CITATION PROPPING UP A CORRECT DECISION, which is worth fixing precisely because
the decision survives. The `spec-review.md` exclusion was justified by claiming
`test_the_body_does_not_apply_the_ipd_ev_rubric` "fails the body for mentioning an E/V bijection",
so copying the sweep rule there "would trip a live test". Read in full, that test fails only on the
LITERAL strings `E/V-bijection` or `E/V bijection`; a sweep sentence never using that exact phrase
would not trip it. The exclusion is right on the DESIGN ground (`spec-review.md`'s revise step
sharpens requirements and acceptance criteria, and a spec carries no `E-*`/`V-*` checklist for a
corrected wording to leave stale, which that body's own "WHAT IS LOCAL TO THIS WORKFLOW is exactly
two things" sentence confirms). Left as authored, a later reader would discover the test never said
what was claimed and reopen a settled decision.

WHAT REVIEW DELIBERATELY DID NOT DO, stated because each was considered. It did not add a test:
the plan's Deferred reasoning under the 2026-09-26 no-source-text-pins ruling is correct, and F-11
was instead strengthened by READING both candidate modules rather than only running them,
confirming that neither section locator in `test_plan_review_feasibility_rule.py` reaches section
2.4 or `02-review-and-revise.md` section 3, and that E-03's long-form hunk lands in a different
file from the one that module reads. It did not touch the `- Blocks-Release: next` gate or the
`- From-Backlog: rv2ccz` link, both of which `aw check release-gates` confirms resolve
(`CONFORMS 328 release-gates checked`, 0 errors). It did not widen scope to reconcile the
four-versus-five classification-vocabulary drift between `intent-audit.md` ("done / partial /
missing / diverged") and `verify-execution.md` Step 2 (which adds `over-scope`), because the second
file is outside this plan's fence; that discrepancy is now RECORDED in F-06 and E-04 so the
executor neither tidies it nor introduces a third list. And it did not disturb the four existing
`aw check plans` errors, none of which names this plan.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing and verification | plan `- Required tests / validation` first bullet, "BASELINE MEASURED AT AUTHORING ... `2935 passed, 2 skipped, 3 warnings in 44.07s`"; re-measured `python3 -m pytest` at `0d6e70a5` -> `1 failed, 2995 passed, 2 skipped, 3 warnings in 62.88s`; `tests/test_dependency_block_reporting.py:122` `assert not sat` | THE AUTHORED SUITE BASELINE IS SPENT AND THE TREE IS ALREADY RED FOR AN UNRELATED REASON. Sixty tests arrived in the five plans merged after `231ded51`, so comparing against `2935 passed` reads as a 60-test regression; and the single failure, `test_drain_and_cascade_mapped_reasons_rendered_once`, is pre-existing and reproduces with an empty `git status --short`, caused by the test hardcoding `executed:5o1jye` after `5o1jye` reached `executed/`. The plan's own honesty rule would have handed the executor a red suite and an unexplainable gap on a four-file prose change, which is exactly the mis-attribution `verify-execution` Dimension 3 exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low (a measurement correction) | FIXED | Replaced the spent baseline with the re-measured one, named the exact pre-existing failing node id with its cause and its clean-tree reproduction, set the bar as "that one node id and no other, count at or above 2995", and told the executor to state which case they observed if a concurrent fix has landed. Also corrected the companion command's baseline from `3 passed in 0.13s` (first module alone) to `33 passed in 0.90s` (the pair, which is the command). |
| PR-002 | MEDIUM | IN-SCOPE | Step 1 evidence / Deferred reasoning | F-03 "exactly THREE `V-*` items ... across all 797 executed plans"; re-scan at review over 802 files -> 24 matches; `ty3cj6` V-02, `jdn790` V-03/04/05/10, `li44r9` V-02, `97df1z` V-03 read in full | F-03'S CORPUS COUNT IS THE STATED BASIS FOR REFUSING A LINT RULE AND IT DOES NOT REPRODUCE. A wider pattern set returns 24 items where the plan claims three, and it also MISSES a genuine member (`76fgt1` V-03, see PR-007). The authored number is not merely stale: it is the load-bearing premise of the Deferred entry, so an executor or auditor re-running the scan would find the refusal resting on a figure they cannot reproduce. | C:Low; U:Low; S:Low; F:Low; Overall:Low (a re-measurement plus a stronger argument) | FIXED | F-03 re-measured at 802 files with the wider pattern set, the 24 hits classified, and the four genuine members named. The Deferred entry now rests on PRECISION (20 of 24 vocabulary hits are false positives, so a keyword rule is wrong five times in six) rather than on volume alone, which is a stronger refusal than the authored one. Also corrected "roughly 40 lines" to the measured 64. |
| PR-003 | HIGH | IN-SCOPE | G. Plan executability | `plan-review.md` cross-plan sentence, `02-review-and-revise.md` cross-plan sentence, `intent-audit.md` empty-or-never-run sentence: each quoted as a whole sentence in E-03, E-04, V-03 and V-04; `str.count()` on each file text -> 0 single-line occurrences for all three | ALL THREE EDIT ANCHORS ARE QUOTED AS SENTENCES AND ALL THREE ARE LINE-WRAPPED, SO NONE MATCHES AS A STRING. `plan-review.md`'s wraps after "cross-reference it", `02-review-and-revise.md`'s after "cross-reference dependent", `intent-audit.md`'s after "evidence is empty or". V-03 and V-04 compound it by requiring the executor to PROVE the anchor was hit by showing those context lines. An executor grepping any of the three gets zero hits and reasonably concludes the anchor was removed, on a plan whose own subject is a stale quotation surviving a correction. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium (three anchors, each verifiable in one command) | FIXED | Each anchor restated as a verified-unique SINGLE-LINE fragment in both its E-item and its V-item, with each file's wrap width named so added text matches, and with the section END boundaries given (the long form's section 3 ends at `## Exit gate`; `intent-audit.md`'s rule must sit above `## Dimension 2`) so a hunk cannot land outside its section. Added a `## Project conventions` entry recording that these bodies hard-wrap and that `str.count()` rather than a multi-line `grep` is the reliable uniqueness check. |
| PR-004 | MEDIUM | UNDER-SCOPE | D. Anti-regression / G. Plan executability | `u23gbn` E-06 bullet "classify it by what actually happened and say which, rather than inheriting E-02's wording"; backlog `rv2ccz` final paragraph "sweep every V-item that quotes the old one"; E-03's `WHAT THE INSTRUCTION MUST SAY` bullet as authored | THE SWEEP OBLIGATION WAS SCOPED TO `V-*` ITEMS AND WOULD HAVE MISSED THE CASE `u23gbn` ITSELF SHOWS FIRST. E-06's corrected bullet ends "rather than inheriting E-02's wording", so the first stale sibling round 3 encountered was an **E**-item it noticed and instructed around; the one it then missed was a V-item. A `V-*`-only rule is blind to half the observed failure and would not have flagged what that round already half-saw. Copying the backlog item's phrasing verbatim would ship a rule narrower than the evidence supporting it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (the rule's coverage is the deliverable) | FIXED | E-03 now scopes the obligation over every item, field and prose block (`E-*`, `V-*`, findings, `## Proposed changes`, the gate, `- Scope-Paths:`), and adds that the sweep runs against the plan AS IT NOW READS rather than against the reviewer's own diff, since round 3 was correcting round 2's wording. Recorded as F-13 and OQ-03 (D-4). |
| PR-005 | MEDIUM | IN-SCOPE | Step 1 evidence | E-01 fourth bullet and E-04 second bullet, both "the `git merge-base --is-ancestor` measurement"; `u23gbn` V-02 `Observed evidence` -> `merge-base` absent (0 matches); the string appears in the sibling V-06 | BOTH E-ITEMS MISQUOTE THE EVIDENCE THEY POINT AT. V-02's block pastes the RESULT (`is the abandoned commit an ancestor of HEAD: False`, beside `classification: refused-would-overwrite`, `git rc: 1`, `HEAD unmoved: True`), not a `git merge-base` command line, which belongs to V-06. E-01's note would send the next reader hunting for text that is not there, defeating the findable-pointer deliverable; and E-04's calibrated example would teach an auditor to accept a paraphrase in the very rule that demands a measurement. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both bullets now describe the measurement as the block records it (the ancestry RESULT), name where the `git merge-base` spelling actually lives, and state why the distinction matters. V-04 additionally requires `grep -c "merge-base"` over both the added hunk and V-02's evidence block, expecting `0` on each. |
| PR-006 | MEDIUM | IN-SCOPE | E. Testing and verification | V-01 second bullet; `plan_readiness.is_plan_review_approved` body (`text = plan_path.read_text(encoding="utf-8")`); observed `AttributeError: 'str' object has no attribute 'read_text'` when driven with text; F-08 as authored | V-01'S PROBE INSTRUCTION IS UNRUNNABLE AS WRITTEN AND F-08 UNDER-TESTS THE PLACEMENT. The two functions take different argument types (`is_plan_review_approved` a `Path`, `extract_newest_history_entry` the TEXT), which cost a probe attempt at review. Separately, F-08 measured only `is_plan_review_approved`, and it is not the only consumer of the section E-01 inserts into, so the safety claim for a first-position insertion rested on one predicate out of several. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium (the placement safety claim is load-bearing) | FIXED | V-01 now names both signatures and requires driving on temp-file copies. F-08 and V-01 both widened to four consumers, each driven before and after with a note-token probe in E-01's exact position and each unchanged: `newest_verdict` stays `('neutral', <the 2026-09-13 round-3 record>)`, `history_has_review_record` stays `True`, and `_plan_status_events` stays at 8 events with the same first event. Any of the four changing is now an explicit validation failure. |
| PR-007 | MEDIUM | IN-SCOPE | A. Correctness (evidence completeness) | `.aw/records/plans/executed/20260928-zy1okf-01-76fgt1-...ipd.md` F-10 row, OQ-03, V-03 `Required evidence` second paragraph; present in the tree at `231ded51` | A SECOND, LATER INSTANCE OF THE EXACT CLASS EXISTS AND THE PLAN DOES NOT CITE IT, THOUGH IT IS THE PLAN'S BEST ARGUMENT. `76fgt1` V-03 as authored demanded `--agent` be absent from `aw oc profile add --help`, which is false by design (`p_ocp_add` declares `parents=[common]`). Its review caught and inverted it before execution, and its F-10 names the exact hazard E-03 is for: an executor taking the stale demand literally "could 'fix' it by removing `--agent` from the shared parent". The plan argued from a single instance while a second one, showing the remedy working, sat in the corpus at its own authoring HEAD. | C:Low; U:Low; S:Low; F:Low; Overall:Low (additive evidence) | FIXED | Added F-12 recording the case and the caught-versus-missed contrast, added a Goal paragraph making recurrence the argument for the process half rather than the pointer, and folded `76fgt1` into the Deferred entry on the other corpus cases as the POSITIVE control (it needs nothing done because its correction already happened at review). |
| PR-008 | LOW | IN-SCOPE | F. KISS / honest documentation | E-04 fourth bullet "(done / partial / missing / diverged)"; `verify-execution.md` Step 2 bullet list (five values, adding `over-scope`); `intent-audit.md` Dimension 1 sentence (four values) | E-04 RESTATES A FOUR-VALUE VOCABULARY THAT THE AUTHORITY IT CITES DEFINES WITH FIVE, and separately leaves unsaid WHICH value the new passing case receives. The four-versus-five drift is pre-existing between the two files; the omission is this plan's, and it is the one thing an auditor actually has to write down, so leaving it implicit reintroduces the invented-disposition problem E-04 exists to remove. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now names `done` as the classification with the reason (the requirement the item protected WAS met and is pinned by a named test, so `partial` understates it and `diverged` asserts something untrue), refers to the Step 2 vocabulary BY REFERENCE instead of restating any list, and records the four-versus-five drift as deliberately out of fence so the executor neither tidies it nor adds a third list. F-06 and the Expected outcome updated to match. |
| PR-009 | LOW | IN-SCOPE | Step 1 evidence | Deferred entry on `spec-review.md`; `tests/test_spec_review_attestation.py::test_the_body_does_not_apply_the_ipd_ev_rubric` read in full (it tests only for the literal `E/V-bijection` / `E/V bijection`) | THE `spec-review.md` EXCLUSION RESTS ON A FALSE TEST CLAIM, THOUGH THE EXCLUSION ITSELF IS CORRECT. The plan asserts that test "fails the body for mentioning an E/V bijection" so copying the rule there "would trip a live test"; the test fails only on two literal strings, and a sweep sentence not using them would pass. Left standing, a later reader discovers the citation is wrong and reopens a settled decision. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The exclusion is kept and re-grounded on the DESIGN reason (`spec-review.md`'s revise step sharpens requirements and acceptance criteria, and a spec carries no `E-*`/`V-*` checklist for a corrected wording to leave stale, per that body's own "WHAT IS LOCAL TO THIS WORKFLOW is exactly two things"), with the test's actual assertion stated so the correction is visible rather than silently swapped. |
| PR-010 | LOW | IN-SCOPE | Step 1 evidence | F-05 "returns exactly three hits"; re-measured `grep -rniE` over the four workflow dirs -> 5 hits at both `0d6e70a5` and `231ded51` | F-05 UNDER-COUNTS ITS OWN SCAN BY TWO. The scan returns five hits, not three, at the authoring HEAD as well as at review, so it is a miscount rather than drift. Every hit is still unrelated and zero fall in `plan-review/` or `plan-review-long/`, so the CONCLUSION is untouched; but an executor re-running the scan would see five where the plan promised three and have to decide whether the plan or the tree was wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 and E-03's opening sentence both corrected to five hits, each classified (three about a bare `git add -A` sweeping a co-worker's files, two about a mechanical rename sweep), with the conclusion restated and the note that the same scan returns five at `231ded51` too. |
| PR-011 | LOW | IN-SCOPE | F. KISS / honest documentation | E-01 second bullet (use "a NOTE token"); `_PLAN_STATUS_VOCAB` = the ten transition tokens; census of leading history tokens across 802 executed plans -> `note` used 5 times | E-01 SAYS "A NOTE TOKEN" WITHOUT NAMING THE LITERAL TOKEN OR SHOWING IT HAS PRECEDENT, which invites each executor to coin their own (`annotation`, `correction`, `amended`). Each would be equally skipped by `_plan_status_events`, so nothing breaks, but the section whose READABILITY is this plan's entire deliverable accumulates a new spelling. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now specifies the literal token `note`, grounds it in the measured vocabulary (outside `_PLAN_STATUS_VOCAB`, so skipped as a transition) and in the corpus census (already used 5 times across 802 executed plans), and forbids coining an alternative. |
| PR-012 | LOW | UNDER-SCOPE | G. Plan executability | E-03 `KEEP IT SHORT` bullet; the plan's own Goal paragraph "WHAT THIS GOAL DELIBERATELY DOES NOT CLAIM" | E-03 GIVES NO LENGTH TARGET AND DOES NOT CARRY THE GOAL'S OWN NON-CLAIM INTO THE INSTRUCTION TEXT. "Keep it short" without a number invites either a one-line rule too thin to follow or a rubric-sized block in a step; and the Goal explicitly refuses to claim the class is now prevented, a limit the added prose could easily overclaim past. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now targets roughly 6 to 10 lines per file (obligation, named case, grep help, executed-plan disposition, and no more) and explicitly forbids writing any sentence asserting the contradiction "can no longer ship", naming that as the overclaim the Goal refuses. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The authored suite baseline no longer describes the tree AND the tree has an unrelated red. Correct the baseline, drop the baseline, or fix the failing test? | CORRECT the baseline and NAME the pre-existing failure as expected, with its node id, cause and clean-tree reproduction; do not touch the test. | (a) Fix `test_drain_and_cascade_mapped_reasons_rendered_once` - rejected: it is a live defect in a test file outside this plan's four `- Scope-Paths:`, owned by whoever hardcoded `executed:5o1jye`, and fixing it here would be exactly the out-of-fence edit the scope check forbids. (b) Drop the baseline entirely - rejected: the plan's honesty rule requires comparing against something, and with no stated expectation the executor cannot distinguish the pre-existing red from one they caused. (c) Leave `2935` and let the executor work it out - rejected: it presents as a 60-test regression plus an unexplained failure on a prose-only change, which is the single most likely way this plan produces a false INCOMPLETE. | `python3 -m pytest` at `0d6e70a5` on a clean tree -> `1 failed, 2995 passed, 2 skipped`; `git status --short` empty; `tests/test_dependency_block_reporting.py:122`; `5o1jye` present in `.aw/records/plans/executed/`; `verify-execution` Dimension 3's attribution rule | yes |
| D-2 | All three edit anchors are quoted as sentences that do not exist as single-line strings. Re-quote as fragments, or tell the executor to match loosely? | RE-QUOTE as verified-unique single-line fragments, and add the wrap widths and section-end boundaries. | (a) Instruct a loose/normalized match - rejected: it weakens the uniqueness guarantee that stops the edit landing twice or in the wrong section, which is the whole purpose of naming an anchor. (b) Reflow the three sentences onto single lines first - rejected: that is an unrequested edit to three shipped bodies, it would enlarge every diff V-03 and V-04 must inspect, and it would fight each file's existing convention. (c) Leave it and let the executor adapt - rejected: on a plan about stale quotations surviving corrections, shipping three anchors that match nothing is self-defeating, and V-03/V-04 actively instruct proving the unmatchable strings. | `str.count()` on each file text -> 0 single-line occurrences for all three sentences, 1 for each chosen fragment; the wrapped forms located and read; `## Exit gate` and `## Dimension 2` as the section-end boundaries | yes |
| D-3 | F-03's corpus count does not reproduce (24 matches, not 3) and the Deferred lint refusal cites it. Correct the number, or restate the refusal on different grounds? | BOTH: correct the measurement and re-ground the refusal on PRECISION rather than volume. | (a) Just change 3 to 24 - rejected: 24 is the VOCABULARY match count, not the class size, so publishing it bare would make the Deferred entry read as if the class were eight times larger than it is and would weaken a refusal the evidence actually strengthens. (b) Drop the corpus argument and refuse on semantics alone - rejected: the semantic argument was already there, and the measurement is what makes it checkable rather than asserted. (c) Leave the authored number - rejected: it is the load-bearing premise of the refusal and an auditor re-running the scan cannot reproduce it. | Re-scan over 802 executed plans, splitting on `- [x] V-` within `## Validation and cross-check` and matching only after `Observed evidence`; the 24 hits read and classified individually; `ty3cj6`, `jdn790`, `li44r9`, `97df1z` identified as vocabulary false positives | yes |
| D-4 | Should the sweep obligation be scoped to `V-*` items as backlog `rv2ccz` phrases it, or to every item that quotes the replaced wording? | EVERY item, field and prose block, and say the sweep runs against the plan as it now reads rather than against the reviewer's own diff. | (a) Follow the item's wording literally - rejected: it ships a rule narrower than the evidence supporting it, and `u23gbn` E-06's "rather than inheriting E-02's wording" proves the first stale sibling in this very case was an E-item. (b) Widen it to any cross-plan wording as well - rejected as gold-plating: the cross-plan case is already covered by the adjacent sentence the rule anchors on, and the failure measured here is within a single plan. | `u23gbn` E-06 bullet read in full; backlog `rv2ccz` final paragraph; `u23gbn` history showing round 3 correcting round 2 | yes |
| D-5 | `intent-audit.md` names four classifications where `verify-execution.md` Step 2 defines five. Fix the drift, or work around it? | WORK AROUND IT: refer to the Step 2 vocabulary by reference, name only the one value this rule assigns (`done`), and RECORD the drift as deliberately out of fence. | (a) Reconcile the two lists - rejected: `verify-execution.md` is outside the four declared `- Scope-Paths:` and E-04 explicitly forbids touching it, so reconciling would breach the fence on a plan whose own subject is scope discipline. (b) Restate the four-value list as authored - rejected: it propagates the drift into new text. (c) Say nothing about it - rejected: an executor would likely "tidy" it, or a later reader would read the omission as an oversight. | `intent-audit.md` Dimension 1 sentence (four values); `verify-execution.md` Step 2 bullet list (five, adding `over-scope`); the plan's `- Scope-Paths:` | yes |
| D-6 | The `spec-review.md` exclusion cites a test that does not say what is claimed. Keep the exclusion, or re-open it? | KEEP the exclusion and re-ground it on the design reason, stating the test's actual assertion. | (a) Re-open and add `spec-review.md` to scope - rejected: a spec carries no `E-*`/`V-*` checklist, so the rule's subject is absent, and that body's own "WHAT IS LOCAL TO THIS WORKFLOW is exactly two things" sentence excludes it. (b) Leave the false citation, since the conclusion is right - rejected: a wrong basis under a right decision is how a settled decision gets reopened, and this plan's whole subject is a stale claim outliving its correction. | `tests/test_spec_review_attestation.py::test_the_body_does_not_apply_the_ipd_ev_rubric` read in full (tests only the literal `E/V-bijection` / `E/V bijection`); `spec-review.md`'s SHARED table and its section 2.4 | yes |

No `Reversible: no` decision was made. Every decision above is a wording, measurement, or evidence
correction inside one pending plan and one review record; each is undone by editing the plan, and
none touches code, a published interface, a migration, or an executed record. Nothing was escalated
as a `- Blocking: yes` question, and the two pre-existing open questions (OQ-01, OQ-02) were already
`resolved` and non-blocking with rationale that survives review; OQ-03 was ADDED by this review to
carry D-4 and is likewise non-blocking, since the widening is a wording change inside E-03 that adds
no scope path and no deliverable.

No finding is left `OPEN` or `DEFERRED`, so no escalation into the plan as a `- Blocking: yes`
question is owed under the `review_findings_gate.block_at` (default `HIGH`) rule: both HIGH findings
(PR-001, PR-003) are `FIXED` in place.

### Structural and consistency checks at review

- `aw ipd lint --phase author --agent` before revision: `outcome: clean`, `exit 0`, `findings: 0`.
- `aw ipd lint --phase review-finalize --agent` after revision: `outcome: clean`, `exit 0`,
  `findings: 0`.
- `aw check release-gates`: `CONFORMS 328 release-gates checked`, 0 errors, 0 warnings, so
  `- Blocks-Release: next` and `- From-Backlog: rv2ccz` both resolve.
- `aw check plans`: 4 pre-existing errors, none naming this plan (three
  `check.ipd-uncarried-obligation` on `4er1ev`, `q5l2r3` and `gvf2sq`, plus the cross-tree
  collisions placeholder).
- `python3 -m pytest tests/test_plan_review_feasibility_rule.py tests/test_spec_review_attestation.py -o addopts=""`:
  `33 passed in 0.90s`.
- Bare `python3 -m pytest` on a clean tree: `1 failed, 2995 passed, 2 skipped, 3 warnings in 62.88s`,
  the one failure pre-existing and unrelated (see PR-001).
- Probe hygiene: the F-04 gate probe and the F-08 predicate probes were all reverted;
  `git status --short` was empty before the revision edits began and the only files this review
  modified are the plan and this record.
