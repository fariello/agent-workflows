# Review findings: plan tx0q0e

- Subject-Id: tx0q0e
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-A01 (HIGH, fixed), PR-A02 (HIGH, fixed), PR-A03 (MEDIUM, fixed), PR-A04 (MEDIUM, fixed), PR-A05 (LOW, fixed), PR-A06 (LOW, fixed)

## Round 1

Reviewed at HEAD `9e65f433` in an isolated review lane. The plan file was already committed and
byte-identical to the lane input, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; it still reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

THIS PLAN'S ENTIRE VALUE IS ITS MEASUREMENTS, so I re-derived every one of them from the corpus
rather than reading any off the document. That was the right call: the plan's central argument
survives completely, and two of its supporting numbers do not.

WHAT SURVIVES, AND IT IS THE LOAD-BEARING PART. The headline claim is exact and reproduced exactly:
`check_citation_anchors` flags ZERO post-cutover citations. At authoring that was 0 of 247; at review
it is 0 of 331, and the zero is the one figure in this plan that has proved invariant under corpus
growth. The refusal-to-promote argument therefore stands untouched: a rule with no positives has an
undefined false-positive rate, so the measurement `hesb87` conditions its promotion on cannot be
computed, and promoting a silent rule would ship a gate that is both unjustified and inert. The
causal evidence also reproduced: the length-stratified pre-cutover flag rate falls monotonically at
92/66/40/21 percent (authored 91/65/41/22) across the four length bands, and post-cutover units are
median 581, mean 756, max 2861 characters with 80% over 300 (authored 580/725/2861/81%), so the
post-cutover corpus really is concentrated where the detector goes blind. The window-sensitivity
table reproduced at 40/30/18/12 percent against a denominator 34% larger (authored 40/30/17/13), and
the residual false-positive rate re-measured at 4% against the authored 5%. The mechanism claims are
correct by reading: `_citation_units` really does return the whole line for non-table text,
`_has_durable_anchor` really does accept any qualifying token anywhere in it and returns eagerly, and
`ipd_lint` really does reach non-gating status through `LintResult.advisories` rather than through
`artifact_core.drift_exit_code`. The `implemented` spec really can only transition to `superseded` or
`deferred`, so the no-transition reasoning is right, and I verified `aw specs note` works on that
exact Id-less file and is purely additive rather than leaving the executor to discover it.

WHAT DOES NOT SURVIVE IS F-6, AND IT IS THE FINDING THAT JUSTIFIES E-01 (PR-A01). F-6 claims that
proximity WITHOUT logical-unit grouping carries a 51% false-positive rate, because 37 of 73 flagged
citations have a durable anchor on an earlier line of the same bullet. I measured the symmetric
difference between the grouped and ungrouped variants directly at window 80: both flag 96 citations,
and each flags 8 the other does not. So grouping's effect on the flag set is roughly 8%, not 51
points of precision. The cause is structural rather than a counting slip, which is why re-measuring
will not recover the larger figure: only 12 of 213 citation-bearing structural lines (6%) are
continuation lines at all, and grouping can change a verdict only where a citation sits on a
continuation line AND its anchor sits on an earlier line of the same bullet AND that anchor falls
inside the window. Those conditions intersect rarely. E-01 IS STILL WORTH DOING and I did not
recommend dropping it: the continuation-line false positive is documented in the detector's own
docstring, so curing it is a correctness fix whose worth does not depend on frequency, and the plan
already forbids validating E-01 by a flag-count change, which is the instruction that keeps it honest.
What had to change is the CLAIM, because a plan asserting that two corrections are co-equal when one
carries nearly all the effect invites a future reader to conclude the cheap half was the important
one. E-01 now carries the measurement, V-01 requires the executor to report their own symmetric
difference and say which estimate it supports, and the proposed-changes list says E-02 does nearly
all the work.

F-2'S DISTANCE SPLIT IS AMBIGUOUS IN A WAY THAT MATTERS FOR THE FIX (PR-A02). F-2 reports 110 of 161
accepted anchors more than 80 characters from their citation. That is reproducible only against the
FIRST accepting token, which is what the eagerly-returning predicate uses (I measured 125 of 219 at
review HEAD). Measured against the NEAREST accepting token it is only 63 of 219. Both are true of
the same corpus, and the plan does not say which it took. The distinction is not pedantic: E-02
evaluates a window around each citation and accepts if ANY qualifying token falls inside, which is
nearest-token semantics, so the nearest-token figure is the one bounding how much blindness a
proximity window can remove. Quoting only the first-token number overstates the fix's headroom. Both
are now recorded with the semantics named.

EVERY COUNT HAS DRIFTED AND SOME WERE USED AS ACCEPTANCE BARS (PR-A03). The tree grew from 988 to
1067 plans in a day, taking 247 citations to 331 and the corrected variant's output from 73-across-32
to 98-across-45. The plan already asks for re-derivation in several places, which is to its credit,
but V-02, the required-tests section and the gate each still stated an absolute bar ("about 73",
"near the full 247"), and an executor comparing a correct 98 against 73 would read correct behavior
as a defect. Every bar is now a PROPORTION with the counts demoted to dated observations, and the
spec prose E-04 writes must follow the same discipline because a spec outlives its numbers.

THREE SMALLER FINDINGS. V-02 pins the `8i0xa7` worked case by name, which is fine until that plan's
text changes and the case stops reproducing, so it now carries a substitution instruction plus
review's own worst case (distance 1672 in plan `01reg8`). OQ-01 was `open` with `Owner: maintainer`
while being a question the repository can answer, and leaving it open meant the plan could not reach
a clean verdict; I resolved it on the strength of the window's stability across a 34% corpus growth
and recorded the reviewer as owner rather than forging a maintainer ruling. And the gate prescribed
moving the plan to `executed/` where the contract is `aw ipd finalize`, and it lacked the
make-and-justify scope instruction.

ONE THING I DELIBERATELY DID NOT FLAG. The plan's headline deliverable is a REFUSAL, which makes it
unusual, and I considered whether a plan whose main output is "do not do the thing" should instead be
a backlog note. It should not: it ships a real code fix, a spec amendment and tests, and the refusal
needs to be recorded against evidence precisely so `hesb87` is not reopened on a hunch. The plan's
own gate says the approval is unusual in shape and names both consequences a human is agreeing to,
which is exactly right and is better than most plans manage.

Bare suite at review HEAD: `3387 passed, 2 skipped, 3 warnings in 57.68s`, 207 deselected.
`tests/test_ipd_lint.py`: `54 passed in 4.63s`. `aw specs check --agent`:
`"outcome":"clean","checked":38,"findings":0`. My one mutating probe (`aw specs note` on the target
spec) was reverted with `git checkout --` and the tree confirmed clean; no production file was
modified by this review.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | HIGH | IN-SCOPE | Evidence accuracy / D. Anti-regression (a finding that misattributes which correction does the work) | At HEAD `9e65f433`, the same predicate at window 80 with and without logical-unit grouping: `grouped flags: 96, ungrouped flags: 96, ungrouped-only (cured BY grouping): 8, grouped-only: 8`. Continuation-line census: `citation-bearing structural lines: 213; of which CONTINUATION lines: 12 (6%)` | **F-6 claims proximity without grouping carries a 51% false-positive rate (37 of 73 flags anchored on an earlier line of the same bullet); measured, grouping changes 8 of 96, roughly 8%.** The cause is structural and will not re-measure upward: grouping can only change a verdict where a citation sits on a continuation line AND its anchor sits on an earlier line of the same bullet AND that anchor is inside the window, and only 6% of citation-bearing lines are continuations at all. E-02 does nearly all the work. E-01 remains worth doing (it cures a defect the detector's own docstring documents, and its worth does not depend on frequency), but a plan asserting the two corrections are co-equal invites a later reader to keep the cheap half and drop the effective one | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-11 records the symmetric difference, the continuation-line census and the structural reason. F-6 RETAINED with its original text and marked superseded, so the correction is visible rather than erased, noting that its second half (grouping alone still flags 0) does reproduce and does establish E-02's necessity. E-01 gains a paragraph stating its measured contribution, why it is still included, and an instruction not to expect a large precision gain. Its expected outcome and V-01 now require the executor to report their OWN symmetric difference and say which estimate it supports. `- Concern:` and proposed-changes item 1 updated |
| PR-A02 | HIGH | IN-SCOPE | Evidence accuracy (an ambiguous measurement that overstates the fix's headroom) | Two passes over the same 219 post-cutover accepted-anchor units at HEAD `9e65f433`: first-accepting-token distances give `>80: 125, <=80: 94`; nearest-accepting-token distances give `>80: 63, <=80: 156`. `_has_durable_anchor` returns on the FIRST accepting token; E-02's window accepts if ANY token falls inside it | **F-2's 110-versus-51 split is reproducible only against the FIRST accepting token, and the plan does not say which it measured.** Against the NEAREST token, which is the semantics E-02's window actually implements, only 63 of 219 anchors are beyond 80 characters rather than 125. Both figures are true; citing only the first-token one overstates how much of the blindness a proximity window can remove, which is the quantity the whole fix is justified by | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-10 records both measurements with their semantics named, states that the nearest-token figure is the one the fix answers to, and gives review's worst first-token case (distance 1672, plan `01reg8`, anchored by a pasted `python3 -m agent_workflows specs note ...` command). `- Concern:` now states which token each figure refers to and which one bounds the fix |
| PR-A03 | MEDIUM | IN-SCOPE | G. Plan executability (live-population counts used as acceptance bars) | At HEAD `9e65f433`: 1067 plans (authored 988), 355 post-cutover (276), 331 citations (247), 219 citation-bearing units (161), corrected variant flags 98 across 45 plans (73 across 32). Structural claims all survive: base flags exactly 0 of 331; gradient 92/66/40/21; windows 40/30/18/12; residual FP 4% | **Every corpus count has moved in one day, and V-02, the required-tests section and the gate each state an absolute bar ("base must reproduce 0 of about 247", "after must be nonzero, about 73 across about 32 plans", "near the full 247").** An executor comparing a correct 98 against 73 would read correct behavior as a defect, or worse, tune the window to hit the stale number. The plan already asks for re-derivation in places, which makes the remaining absolute bars the inconsistency rather than the rule | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-12 records the full drift alongside every structural claim that survived it. Every bar restated as a PROPORTION (base exactly 0; after roughly 30% of the re-derived denominator) with counts demoted to dated observations, in E-02's expected outcome, the required-tests section, V-02 and the gate. E-04 additionally instructed to write the spec prose with proportions and dated measurements rather than bare counts, since a spec outlives its numbers |
| PR-A04 | MEDIUM | IN-SCOPE | E. Testing (a required evidence item pinned to a mutable third-party artifact) | V-02 requires the `8i0xa7`-shaped case showing `tests/test_role_declaration_guard.py:80` anchored by a token 835 characters away. That plan is another artifact in a shared checkout and may be edited or retired | **V-02's central worked example is pinned to another plan's current text, so the item becomes unsatisfiable if that plan changes, with no stated fallback.** An executor meeting that would either report the item unverifiable or, worse, paste a near-miss and call it the case | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now instructs that if the case no longer reproduces, say so and substitute an equivalent far-token case found in the executor's own corpus pass, and supplies review's own worst case (`host_sandbox_profile.py:107-111` in plan `01reg8`, distance 1672) as a concrete alternative |
| PR-A05 | LOW | IN-SCOPE | G. Plan executability (an open question the repository can answer, blocking a clean verdict) | OQ-01 read `- Status: open`, `- Owner: maintainer`. Review re-derived the sensitivity table against a denominator 34% larger and every percentage landed within one point (40/30/18/12 versus 40/30/17/13); residual FP re-measured 4% versus 5% | **OQ-01 asks whether 80 characters is the right window or whether the unit should be a sentence, and leaves it open for the maintainer, when the repository's own corpus answers it.** A character window whose precision/recall curve is unchanged by a third more corpus is an empirically stable proxy, and the question is a matter of reviewer judgement about a tunable constant rather than a maintainer's decision about scope or risk | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved with the stability measurement as its basis, recorded as D-1. `- Owner:` set to `reviewer` with an explicit note that it is NOT a maintainer ruling, and the resolution states why sentence segmentation is the worse trade over this repository's prose and that overturning the constant later costs one line |
| PR-A06 | LOW | IN-SCOPE | G. Plan executability (gate wording) | Gate: "before the plan moves to `.aw/records/plans/executed/`"; no scope-reason instruction; no baseline re-derivation instruction in the contract paragraph | **The gate describes the terminal transition as a move rather than naming `aw ipd finalize` with conditional ownership, and omits the make-and-justify scope instruction.** Minor, but this plan carries a declared spec edit, so the reconciliation path is more load-bearing here than usual | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: `aw ipd finalize` with conditional runner/executor ownership, the make-and-justify `--scope-reason` instruction, and baseline re-derivation by failing node id with review's measured suite figures as history. The stop-condition paragraph now judges against a proportion rather than the stale 247 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 (`- Owner: maintainer`, `- Status: open`): is 80 characters the right proximity window, or should the unit be a sentence rather than a character count? | KEEP the 80-character window; resolve the question rather than leaving it for the maintainer | (a) Leave it `open` for the maintainer as authored; (b) adopt sentence segmentation; (c) make the window adaptive to unit length | Option (a) would ask the human what the corpus answers, and would also hold the plan at `NO-GO` for a question its own author judged non-blocking. The measurement is the argument: re-deriving the sensitivity table against a denominator 34% larger returned 40/30/18/12 percent against the authored 40/30/17/13, with the residual false-positive rate at 4% versus 5%, so 80 sits at the same measured knee in both passes. A proxy whose precision/recall curve is invariant to a third more corpus is empirically stable, which is precisely what the question doubted. Option (b) would replace a measured proxy with an unmeasured one over prose that is close to the worst case for a sentence splitter (dense multi-clause sentences containing backticked code with periods), trading a known 4% for an unknown rate and a larger blast radius. Option (c) was tempting and rejected: it would make the constant unreadable and untunable, and the length-stratified data give no evidence that the right window varies with unit length rather than that long units simply contain more noise. The shipped value is a module-level constant, so overturning this costs one line and no plan | yes |
| D-2 | PR-A01: F-6's 37-of-73 could not be reproduced and measured 8-of-96. Drop E-01, or keep it with a corrected justification? | KEEP E-01, correct its justification, and require the executor to report their own measurement | (a) Drop E-01 as low-value and ship E-02 alone; (b) keep E-01 and leave F-6 as written; (c) rewrite F-6 in place to say 8 | Option (a) is the tempting efficiency and is wrong on the merits: the continuation-line false positive is documented in `check_citation_anchors`'s own docstring as a KNOWN defect, so curing it is a correctness fix independent of frequency, and the 8 citations it cures are 8 authors correctly told nothing. Dropping it would also leave the docstring's admission of a defect standing with no fix in sight. Option (b) is the finding: a plan claiming the two halves are co-equal invites a later reader to keep the cheap half and drop the effective one, which is the opposite of what the measurement supports. Option (c) destroys the audit trail, which matters more than tidiness here because the authored number was not a typo but a differently-computed quantity, and a future reader needs to see that two parties measured and disagreed. Retaining F-6 marked superseded, adding F-11, and making V-01 demand a third independent measurement is the shape that survives a fourth reader | yes |
| D-3 | PR-A02: F-2's distance figure is reproducible only against the first accepting token. Correct it, or record both? | RECORD BOTH with their semantics named, and state which one bounds the fix | (a) Replace F-2's figure with the nearest-token number; (b) leave F-2 as written, since it is reproducible under one reading; (c) call F-2 wrong | Option (c) would be false: F-2's number is exactly right for the token `_has_durable_anchor` actually returns on, and the workflow's own guidance warns that rejecting a citation the reviewer merely failed to re-derive is worse than under-reporting drift. Option (a) loses real information, because the first-token distance is what characterises the CURRENT blindness (an eagerly-returning predicate really does accept a token 1672 characters away) while the nearest-token distance is what characterises the fix's HEADROOM. Both quantities are load-bearing for different halves of the argument. Option (b) leaves a reader to assume the two are the same, which overstates the headroom by roughly double. Recording both with the semantics named costs one finding row and makes the fix's justification honest | yes |
| D-4 | PR-A03: every corpus count has drifted. Update the numbers, or change the bars into proportions? | Change the BARS to proportions, record the drift as a dated finding, and keep both count sets as history | (a) Update each count to the review-HEAD value; (b) delete the counts and state only the properties; (c) leave them, since the plan already says to re-derive | Option (a) rots again, and faster than it looks: these moved 34% in ONE day and this plan executes after further merges, so a refreshed count is a bar that is wrong by the time it is read. Option (b) throws away the most persuasive evidence in the plan, since the argument rests on a specific zero against a specific denominator and on a gradient whose shape is the causal claim. Option (c) is the inconsistency the finding names: the plan asks for re-derivation in prose while three separate places still state an absolute bar, and under time pressure an executor follows the concrete number. Proportions as bars with counts as dated observations preserves the evidence and removes the trap, which is how the repository handles other live-population criteria | yes |
