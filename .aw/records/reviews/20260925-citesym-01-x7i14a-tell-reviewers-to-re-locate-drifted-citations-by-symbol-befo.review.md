# Review: Tell reviewers to re-locate drifted citations by symbol before calling them false

- Subject-Id: x7i14a
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was correctly skipped per
Step 1. Structural preflight `aw ipd lint --phase author --agent` reported `conforming` (exit 0)
before review and again at `--phase review-finalize` after the revisions.

ALL FIVE AUTHORED FINDINGS VERIFY, and so does every edit anchor, which is what makes this plan
executable as prose work. Each of the four target strings exists verbatim: `plan-review.md` item
`4. Verify material claims with `path:line` evidence.`,
`plan-review-long/01-discover-and-snapshot.md` item
`4. Verify material claims with `path:line` citations.`, `spec-review.md` item 4 opening
`Verify material claims with `path:line` evidence. A spec's measured claim` with the
`re-measure it rather than trusting it` sentence on the following line, and
`verify-execution.md`'s `- **Evidence discipline**: re-open the actual `path:line` and diff` bullet.
F-3's grep reproduces exactly: a case-insensitive search for `symbol` across all four workflow
directories returns exactly two lines, both the unrelated scope-fence sentence
`prerequisite whose symbols are absent`. F-2 reproduces word for word: `mzc019`'s Scope OUT clause
contains `any change to how REVIEWS cite code`. The `intent-audit.md` inheritance claim is real
(`Core discipline (inherited from `verify-execution.md`)`). And F-5 holds: `pyproject.toml` line 131
force-includes `".aw/system"`, and `git ls-files` shows no second `plan-review.md` besides the four
host shims.

THE FIRST MATERIAL FINDING IS A PARITY GAP THE PLAN CREATED WHILE FIXING ONE. E-01 bundled two
different edits into one item: the Step 1 disposition rule, and an amendment to
`plan-review.md`'s `- **Evidence:** `path:line`.` field recommending a symbol beside the path. But
THREE workflows declare an `Evidence` field: that one, `plan-review-long/02-review-and-revise.md`'s
`- Evidence: `path:line`.`, and `spec-review.md`'s `Evidence (`path:line`)` clause. The plan's Scope
check consciously excluded the second on the reasoning that the recommendation is "optional guidance",
which does not survive contact with the parity contract both files assert in their own words
(`plan-review-long/README.md`: "Kept in deliberate parity with the single-file";
`plan-review.md`: "The two variants are otherwise kept in deliberate parity"). Shipping a
survivable-citation recommendation on one findings table of three, in a plan whose entire subject is
citations decaying, is the drift it exists to stop. Split out as E-02 covering all three, with
`02-review-and-revise.md` added to `Scope-Paths`.

THE SECOND IS A TENSION WITH THE PLAN'S OWN CITED AUTHORITY, and it is the finding I expected to be
wrong and was not. Spec `ipd-structure-and-linting` Section 10.2 is the basis the plan leans on four
times. That section says, in terms: "REVIEW IS NOT THE REMEDY, which is why this is a contract rule
rather than a reviewer instruction", and backs it with a measurement - plan `216rgg` "was reviewed
twice and its history records that every line number in it was measured at HEAD. That record was TRUE
when written. No amount of verification can preserve a reference type that expires by construction."
A plan that adds a reviewer instruction while citing that paragraph as support needs to say which
question it is answering, or a reader reasonably concludes the spec already rejected it. The
distinction is real and the plan is on the right side of it: Section 10.2's own closing sentence says
"the correct posture toward an older plan's offset is to treat it as a HINT and locate the construct
by symbol" - a DISPOSITION for drift already present - and it states that posture only in the IPD
spec, where no reviewer is pointed at it (which is the plan's own F-4). So the fix is framing, not
scope: the Goal now states plainly that this is not prevention and not verification, and names the
prevention (the shipped authoring rule) so the two halves are not confused.

THE THIRD IS A MEASUREMENT TAKEN THE WRONG WAY, whose corrected answer changes what the executor
should expect. The plan's conventions note says `managed-sections.json` records a sha256 for
`plan-review.md` that already mismatches (`7c98...` recorded vs `48fb...` actual) and that the
executor should not treat a mismatch as caused by this plan. The headline is right and useful. But the
hash is over a NORMALIZED view (`manifest.hash_content` -> `normalize_for_hash`), not raw bytes, so
the `48fb...` figure is a raw digest and answers a different question, and the note implies the
situation is uniform across the targets. Re-measured with the real function: `plan-review.md`
recorded `7c986280` against actual `12e2b616` (stale), `verify-execution.md` recorded `2df1a769`
against `2c8f3c24` (stale), `spec-review.md` NOT TRACKED AT ALL, and
`01-discover-and-snapshot.md` recorded `132091c9` against actual `132091c9` - a MATCH. So one of the
four edits introduces a new mismatch rather than joining an existing one, and the executor told "do
not treat a mismatch as caused by this plan" would be wrong about that file. I traced the consequence
rather than leaving it as a worry: `engine.plan_uninstall` classifies an owned file whose content no
longer matches its record as `drifted`, and `uninstall_repo`'s docstring states "a user-EDITED
(drifted) owned file is PRESERVED by default and reported, removed only when `force` is set". So the
cost is that `aw uninstall` keeps the file rather than removing it; it is not an install-time refusal
and it gates nothing in CI, and no test reads this repository's own manifest. That is a small, bounded
consequence and it is worth stating precisely so nobody hand-edits an installer-owned artifact to
"fix" it.

PR-804 is a live test guard the plan walks into. `tests/test_spec_review_attestation.py` asserts
against the real `.aw/system/workflows/spec-review/spec-review.md`, including a NEGATIVE per-line scan:
any line matching `^.*aw ipd lint.*$` must contain one of `NOT`/`not`/`NEVER`/`never`/`IPD-only`/
`preflight`/`runs`, and any line mentioning `- Readiness:` must carry a prohibition token. It also
forbids restating `plan-review`'s severity glosses and the tokens `E/V-bijection` / `E/V bijection`.
E-04 adds a sentence to exactly that file. The file passes 30/30 today, so a failure after E-04 would
be attributable - but only if it is run then, rather than surfacing in the bare suite several items
later. E-04 now names the constraints and requires that test run immediately.

PR-805 is the honesty half of the scope decision. Backlog `yos8rq` enumerates roughly twenty citation
sites across the four workflows; the plan edits four (now five) and says nothing about the rest. Most
of the omissions are correct - a `<path:line>` placeholder in a report-table row is a column label, not
an instruction about gathering evidence - but "correct and unstated" is how a later reader concludes the
plan missed them. The Scope check now lists what is deliberately untouched and why, so the judgement is
reviewable rather than invisible.

PR-806 is a gate the plan fails today. OQ-01 is `Status: open` and owes a TYPED durable carrier;
`evaluate_durable_carrier` returned one `error`-severity drift, which also gates
`aw ipd lint --phase pre-transition`. Added `- Carrier: yos8rq`, the source item, which is the durable
home for this wording decision. I did NOT resolve the question itself: batched-LOW versus no-finding is
a genuine maintainer wording choice, and the plan's default is reasonable. What I did add is evidence
for that default, which brings me to the finding I think is the most substantive of the set.

F-9 IS THE ONE THAT CHANGES WHAT THE RULE SHOULD SAY. The plan's disposition warns about treating
stale lines as false claims, but never names which error direction is costlier, and this repository has
MEASURED the expensive one. Backlog `88manw` (still `open`, `Work-Kind: bug`, `Blocks-Release: next`)
records that plan `si24ia`'s review finding PR-305 "rejected a correct spec section citation and
substituted a wrong one": the plan cited spec section 2.1 four times, the review declared that wrong
and named section 1.1 plus a line number, and the plan was right - line 211 is inside 2.1. The item's
own reasoning is exactly this plan's subject: "the plan review finding is DURABLE, tracked, and wrong,
so the next reader who trusts it is sent to the wrong section and may propagate the error, which is
precisely what happened once already in this chain." Two consequences. First, the rule must say that
rejecting a citation the reviewer merely failed to re-locate is worse than under-reporting drift,
because the finding outlives the drift. Second, that case is a SPEC-SECTION anchor, not a code symbol,
so a rule phrased only around `module.function` does not cover the one failure on record. Both are now
in E-01, and the `88manw` evidence is what I added to OQ-01's rationale in favour of the batched-LOW
default over silence.

ON RIGHT-SIZING. Five items became seven. E-01 was doing two things (a step rule and a findings-field
recommendation across parity files) and is now two items; E-06 is a one-command baseline that exists
because V-01's original claim about it was false. Each item is one file-region edit with its own
evidence. Nothing here warrants a child plan.

ON VALIDATION. V-01 asserted the pre-edit grep "returns none before", which is false: it returns two
unrelated scope-fence lines. That is a small error with a real cost, because an executor checking it
literally would read a contaminated baseline as a defect. E-06/V-06 now record the actual pre-edit
matches so the after-grep is read as a delta.

The plan is correctly `Work-Kind: chore` with no `Blocks-Release:`: source item `yos8rq` is
`Work-Kind: chore` and carries no gate, so nothing is owed or inherited. `aw check release-gates`
reports `findings: 0`. `aw sanitize --agent` is clean. The plan's Spec/documentation sync N/A is right -
it changes no spec, and correctly does NOT propose amending Section 10.2, which would be the
over-reach here. `tests/test_spec_review_attestation.py` and `tests/test_installer.py` pass 30/30
together at review, which is the baseline E-07 compares against.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | MEDIUM | UNDER-SCOPE | C. Architecture (duplicate path drift) / F. Principles | `plan-review.md` `- **Evidence:** `path:line`.`; `plan-review-long/02-review-and-revise.md` `- Evidence: `path:line`.`; `spec-review.md` "Classify each with Severity, Scope, Area, Evidence (`path:line`)"; `plan-review-long/README.md` "Kept in deliberate parity with the single-file"; `plan-review.md` "The two variants are otherwise kept in deliberate parity" | THE PLAN WOULD SHIP ITS OWN RECOMMENDATION ON ONE FINDINGS TABLE OF THREE. Three workflows declare an `Evidence` field and E-01 amended only `plan-review.md`'s, with the Scope check consciously excluding the mirror as "optional guidance". That does not survive the parity contract both files assert in their own words, and it is self-defeating in particular: a plan whose subject is citations decaying would leave two of three reviewer-facing evidence declarations telling reviewers to record the bare format it is trying to make survivable. | C:Low; U:Low; S:Low; F:Low; Overall:Low (three identical prose appends) | FIXED | Split E-01 into E-01 (the Step 1 disposition rule) and a new E-02 applying the recommendation to ALL THREE `Evidence` declarations with identical wording. Added `plan-review-long/02-review-and-revise.md` to `Scope-Paths` and to the Scope field. V-02 requires the three hunks side by side plus proof `report-template.md` is absent from the diff. Added F-6. |
| PR-802 | MEDIUM | IN-SCOPE | F. Honest documentation / G. Plan executability (framing against the cited authority) | spec `ipd-structure-and-linting` Section 10.2: "REVIEW IS NOT THE REMEDY, which is why this is a contract rule rather than a reviewer instruction"; "`216rgg` was reviewed twice and its history records that every line number in it was measured at HEAD. That record was TRUE when written. No amount of verification can preserve a reference type that expires by construction"; and its closing "the correct posture toward an older plan's offset is to treat it as a HINT and locate the construct by symbol" | THE PLAN CITES AS ITS BASIS A SECTION THAT EXPLICITLY REJECTS "A REVIEWER INSTRUCTION" AS THE REMEDY, and never distinguishes the two questions. The plan is on the right side of the distinction - Section 10.2's own closing sentence states a reader-side DISPOSITION and states it only in the IPD spec, where no reviewer is pointed at it (the plan's own F-4) - but nothing in the plan says so, so a maintainer reading Section 10.2 would reasonably conclude the question was already closed against this change, and an executor could write prose that over-claims prevention. | C:Low; U:Low; S:Low; F:Low; Overall:Low (framing paragraph; no scope change) | FIXED | Added a "WHAT THIS IS NOT" paragraph to the Goal stating plainly that the plan does not claim to prevent drift or make review the remedy, naming the shipped authoring rule as the prevention, and identifying the disposition question as the one Section 10.2 leaves to the reader while pointing no reviewer at it. E-01 now cites Section 10.2 as stating the posture "for authors and, for an older plan's offset, for readers". Added F-10. |
| PR-803 | MEDIUM | IN-SCOPE | A. Correctness (a measurement taken the wrong way, generalized too far) | `manifest.hash_content` hashes `normalize_for_hash(text)`, not raw bytes; re-measured with it: `plan-review.md` recorded `7c986280` vs actual `12e2b616`; `verify-execution.md` `2df1a769` vs `2c8f3c24`; `spec-review.md` NOT TRACKED; `01-discover-and-snapshot.md` `132091c9` vs `132091c9` (MATCH); `engine.plan_uninstall` classifies a non-matching owned file `drifted`; `uninstall_repo` docstring "PRESERVED by default and reported, removed only when `force` is set" | THE CONVENTIONS NOTE IS RIGHT IN ITS HEADLINE AND WRONG IN ITS GENERALIZATION, and the wrong part is the part an executor acts on. It cites a RAW digest (`48fb...`) for a NORMALIZED hash, and it tells the executor not to treat a hash mismatch as caused by this plan - but `01-discover-and-snapshot.md` currently MATCHES, so E-03 genuinely does cause a new mismatch, and `spec-review.md` is not tracked at all. Without the correction an executor either ignores a mismatch it did cause or, worse, hand-edits the installer-owned manifest to reconcile it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the conventions note with the normalization mechanism, all four re-measured states, and the traced consequence (`aw uninstall` PRESERVES a drifted owned file; not an install refusal, gates nothing in CI, no test reads this repo's own manifest). E-03 states that its target matched before and does not after, that this is expected, and forbids hand-editing `managed-sections.json`. V-03 requires a positive statement plus proof the manifest is absent from the diff. Added F-7. |
| PR-804 | MEDIUM | UNDER-SCOPE | E. Testing and verification (a live guard the edit can trip) | `tests/test_spec_review_attestation.py::test_every_mention_of_a_forbidden_act_is_a_prohibition` scans `^.*aw ipd lint.*$` (allowed tokens `NOT`/`not`/`NEVER`/`never`/`IPD-only`/`preflight`/`runs`) and `^.*- Readiness:.*$` per RAW line; `test_the_body_does_not_restate_the_shared_severity_glosses`; `test_the_body_does_not_apply_the_ipd_ev_rubric`; 30/30 passing at review | E-04 ADDS A SENTENCE TO A FILE UNDER LIVE PER-LINE ASSERTIONS AND THE PLAN DOES NOT MENTION THEM. A disposition sentence naming a severity, or mentioning the linter in passing, can fail a NEGATIVE scan that reads one raw line at a time. The plan's only validation for E-04 was a diff, and its only test step was the bare suite at the very end, so a failure would surface several items later with its attribution lost - on a plan whose own conventions correctly note that prose pins were removed from this repository, which makes the surviving per-line scans easy to forget. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-8 enumerating the guards. E-04 now names each constraint (do not mention `aw ipd lint` in the new sentence; name a severity LEVEL without glossing it) and requires `tests/test_spec_review_attestation.py` be run immediately after that item. V-04 requires the 30-passed output beside the diff. A conventions bullet records that this file carries live assertions. |
| PR-805 | LOW | IN-SCOPE | G. Plan executability (an unstated scope judgement) | Backlog `yos8rq` enumerates `plan-review.md:107`/`:173`/`:260`/`:555`/`:571`, `plan-review-long` `01:67`/`02:30`/`report-template.md:22`, `spec-review.md:42`/`:134`/`:167`/`:309`/`:375`/`:392`, `verify-execution.md:15`/`:94`/`:111`/`:198`/`:211`, `intent-audit.md:8`/`:12`/`:26`/`:45`; the plan edits four of them and the Scope check says only "none" for over-scope | THE PLAN DROPS ABOUT FIFTEEN SITES THE SOURCE ITEM NAMES AND EXPLAINS ONLY ONE OMISSION. Most exclusions are correct (a `<path:line>` placeholder in a report-table row is a column label, not an evidence-gathering instruction; `intent-audit.md` inherits by its own words), but an unstated correct judgement is indistinguishable from an oversight to the next reader, and the Scope check's "Over-scope: none" plus a single hedged under-scope note does not record it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the Scope check: the `Evidence`-field gap is closed and recorded as closed; a new "STILL DELIBERATELY NOT EDITED" clause names `report-template.md`, the four findings-table rows, `intent-audit.md` and `review-rubric.md` with the reason for each (output format versus gathering instruction; documented inheritance; unrelated `symbol` hit), and points at the review record's D-2. |
| PR-806 | MEDIUM | IN-SCOPE | A. Correctness / D. Anti-regression (a gate the plan fails today) | `check_engine.evaluate_durable_carrier` on this plan at review: one `error`-severity drift, "OQ-01 records an outstanding obligation with NO durable carrier; once this plan reaches `executed` it classes `done` in `aw attention` and this vanishes with no record"; `aw check plans --agent` 12 findings including this plan | OQ-01 IS `open` AND OWES A TYPED CARRIER, so `aw check plans` reports an `error` on this plan today and `aw ipd lint --phase pre-transition` would refuse it later rather than now. The question is a legitimate maintainer wording choice and correctly left open, but an open question with no carrier means the decision vanishes from `aw attention` the moment the plan classes `done`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Carrier: yos8rq` (the source item, `graduated` and therefore non-terminal, which resolves) as the durable home for the wording decision, with a note that a maintainer changing the clause after execution should record it there. Re-measured: zero carrier drifts on this plan, `aw check plans` 12 -> 11 with this plan absent. The question itself is deliberately NOT resolved by review; see D-1. |
| PR-807 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) + E. Testing (a false validation claim) | Plan gate as authored: two metadata lines plus one sentence. V-01 as authored: a case-insensitive grep for `by symbol` or `drift`, annotated "(it returns none before)", against a measured pre-edit result of two lines matching `symbol`, both `prerequisite whose symbols are absent`. Compare `0i4fkt`/`8apjpp`/`184tn9`/`qfpnrm` gates | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS AND V-01 ASSERTED A FALSE BASELINE. No statement of what a human is approving - which matters here because the framing question (PR-802) is exactly what a maintainer should weigh and it appeared nowhere near the approval point; no scope fence despite the Scope field carrying an OUT list; no honesty rule; no stop conditions. Separately, V-01's "it returns none before" is measurably wrong, and an executor checking it literally would read an already-contaminated baseline as a defect or would grep for a narrower pattern to make the claim true. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: an approval paragraph stating this is prose-only with no code/spec/test changes and naming the two things a human should weigh (the Section 10.2 framing question, and OQ-01's genuinely open wording choice); a per-file scope fence stated as a DECLARATION with an explicit not-in-scope list (the manifest, `intent-audit.md`, `report-template.md`, `review-rubric.md`, every table row and placeholder, the format itself, any lint via `hesb87`, the authoring rule, retrofits); the hard-MUST honesty rule naming V-01's grep and V-04's test run as the two mis-certifiable checks with the bare-suite flag prohibitions; two genuine stop conditions; and the lifecycle transition with conditional runner/executor ownership. Added E-06/V-06 recording the true pre-edit grep baseline. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 asks whether a moved-but-resolvable citation yields NO finding or a batched LOW. Resolve it from evidence, or leave it to the maintainer? | Leave it OPEN and owned by the maintainer; add evidence FAVOURING the plan's batched-LOW default rather than deciding. | (a) Resolve it to batched LOW on my own authority - rejected: it is a wording choice about how much noise a review may impose on an author, which is a risk-appetite judgement the maintainer owns, and the plan's own default is already reasonable. (b) Resolve it to "no finding" - rejected for the same reason plus the evidence below, which argues the opposite way. (c) Leave it open with no added evidence - rejected: the repository has a measured case bearing directly on it, and a reviewer who read that case and did not record it has wasted the finding. | Backlog `88manw`: a review rejected a CORRECT citation and the wrong correction propagated, so silence about decaying anchors loses information a batched note would preserve, while nothing in that case argues for a severity above LOW; the question is about reviewer-imposed cost, which AGENTS.md reserves to the human | yes |
| D-2 | The source backlog names about twenty citation sites; the plan edits four. Which omissions are legitimate? | Close the three `Evidence`-field sites (E-02); keep the report-table rows, `report-template.md`, `review-rubric.md` and `intent-audit.md` out, and RECORD why for each. | (a) Edit every site the backlog names - rejected: a `<path:line>` placeholder in a findings-table row is a column label, and appending a recommendation to a table cell changes the report SHAPE, which the plan's own Scope OUT excludes; `intent-audit.md` states its own inheritance. (b) Keep the plan's original four and leave the mirror fields out - rejected: the parity contract makes a one-sided `Evidence` edit drift by construction (PR-801). (c) Edit them but say nothing about the rest - rejected: an unstated correct judgement reads as an oversight to the next reader. | `plan-review-long/README.md` and `plan-review.md` both assert deliberate parity; `intent-audit.md` "Core discipline (inherited from `verify-execution.md`)"; `review-rubric.md`'s only `symbol` hit is the unrelated scope-fence sentence; the plan's Scope OUT already excludes the findings-table column | yes |
| D-3 | E-03 makes a currently-MATCHING manifest hash stale. Is that acceptable, and should the plan do anything about it? | Accept it, state it explicitly in E-03, and forbid hand-editing `managed-sections.json`. | (a) Hand-edit the manifest to re-record the new hashes - rejected: it is an installer-owned artifact whose contract is "the content the installer LAST WROTE", so writing a hash no install produced forges that record. (b) Add a step to re-run the installer - rejected: far outside a prose-edit plan's surface, and it would rewrite unrelated entries. (c) Leave the plan's original blanket note ("do not treat a mismatch as caused by this plan") - rejected: measurably false for this one file, which is the direction that misleads. | `manifest.hash_content` normalization; the four re-measured states (two stale, one untracked, one matching); `engine.plan_uninstall` -> `drifted`; `uninstall_repo` preserves a drifted owned file by default; no test reads this repository's own manifest | yes |
| D-4 | Does spec Section 10.2's "REVIEW IS NOT THE REMEDY" close the question this plan reopens? | No - it rejects review as PREVENTION while itself stating a reader-side disposition. Reframe the plan accordingly rather than narrowing or abandoning it. | (a) Mark the plan REPLAN as contradicting an approved spec - rejected: Section 10.2's closing sentence states exactly the posture this plan installs ("treat it as a HINT and locate the construct by symbol"), so the content is endorsed; only the plan's silence about the distinction was the problem. (b) Amend Section 10.2 to authorize the reviewer instruction - rejected as unnecessary and over-reaching: the spec already contains the posture, the plan changes no contract, and amending an `implemented` spec to restate what it says would be pure churn. (c) Leave the framing implicit - rejected: a maintainer reading the cited paragraph would reasonably refuse the plan. | Spec Section 10.2 "REVIEW IS NOT THE REMEDY ... rather than a reviewer instruction" beside its own "the correct posture toward an older plan's offset is to treat it as a HINT and locate the construct by symbol"; the plan's F-4 that this posture lives only in the IPD spec | yes |
| D-5 | V-01 claims the pre-edit grep "returns none". It returns two lines. Fix the claim, or narrow the grep to make it true? | Fix the claim: add E-06/V-06 recording the actual pre-edit matches and compare the after-grep as a delta. | (a) Narrow the grep pattern until it returns nothing pre-edit - rejected: it tunes the evidence to the assertion, which is the shape of a vacuous validation, and the scope-fence sentence would still be there. (b) Delete the grep from V-01 and rely on the diff - rejected: the grep is the only check that the rule is findable by a future reader searching for it, which is the whole delivery mechanism for a prose rule. (c) Leave "returns none" - rejected: it is false, and an executor checking it literally misreads a clean baseline as contaminated. | Measured pre-edit: `grep -rn -i "symbol"` over the four workflow dirs returns two lines, both `prerequisite whose symbols are absent` (`plan-review.md`, `plan-review-long/review-rubric.md`) | yes |
