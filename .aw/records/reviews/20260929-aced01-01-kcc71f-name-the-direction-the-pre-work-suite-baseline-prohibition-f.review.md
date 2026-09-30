# Review findings: plan kcc71f

- Subject-Id: kcc71f
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (HIGH, fixed), PR-602 (HIGH, fixed), PR-603 (LOW, fixed)

## Round 1

Reviewed at HEAD `c053dd2f` in an isolated review lane. The plan file was already committed and unchanged,
so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`conforming`, exit 0, ZERO findings BEFORE semantic review; `--phase review-finalize --agent` reports
`conforming` with zero findings after revision. The plan is `- Kind: child`, so the `IPD-S407`
orchestrator row check does not apply.

EVERY ONE OF THE PLAN'S NINE FINDINGS REPRODUCES, AND I DROVE THE CODE RATHER THAN READING IT, because
the plan's central claim is that a comment is FALSE against shipped behavior and that is not a claim prose
can settle. The direction matrix reproduces cell for cell: with one red measurement, `passed=True` when the
baseline names the failing id and `passed=False` for a baseline naming another id, an empty completed
baseline, or no baseline at all; a green measurement passes under all four baseline variants; an unmeasured
one refuses under all four. So F-2 holds (shipped code does change an outcome on the strength of the
baseline, making the undirected headline false as written) and F-3 holds (NO baseline value turns a pass
into a refusal, so "a baseline may only make an outcome more permissive" is an observed property, not an
aspiration). Worth recording: my first attempt reproduced NOTHING because I passed `failing_tests` where
`_relative_revalidation_verdict` reads `failures` and requires `suite_passed`, and the plan's E-01 already
warns about the adjacent trap (bare node ids normalizing to `<unparseable>` on both sides and fabricating a
match). The plan's warning is well placed; it is the reason I found my own error rather than reporting a
false refutation.

THE REST OF THE FINDINGS ARE EQUALLY SOUND. F-1: the headline is present verbatim, wrapped across two
comment lines. F-4: `revalidation_baseline_for` does read `candidate.get("suite_baseline")`, the same
record the prompt renders, so "THE BASELINE'S ONLY CONSUMER IS THE ADJUDICATION PROMPT" is false. F-5 is
the subtle one and the plan is right to protect it: `gate_answer_record`'s "Nothing in this package compares
`suite_baseline['failures']` to `failing_tests`" is still TRUE, because the relative verdict compares the
baseline against the merged tree's `failures`, not against `failing_tests`; a careless sweep would
"correct" a true sentence into a false one. F-6: `tests/test_suite_baseline.py` is absent and none of the
cited classes exists anywhere under `tests/`. F-7: spec 5.1 carries "but nothing refuses on it" verbatim.
F-8: the neighbouring section already says "That is a gate that makes an outcome WORSE ... What happens
HERE is the opposite direction ... The sign of the effect is the whole difference", so E-04 relocates a
reviewed distinction rather than inventing one. F-9: four sites in this module cite the absent file. I also
confirmed E-02 is executable as specified by DRIVING `perform_gate_answer` twice with a real outcome file:
a `not-mine` answer releases (`release=True`, no violation) identically with and without a baseline naming
the failing id, and `baseline` appears inside that function only in the `gate_answer_question(...)` and
`gate_answer_record(...)` calls. And the plan's claim that nothing currently tests this surface is exact:
`grep -rn "_relative_revalidation_verdict\|new_failures_since_baseline" tests/` returns nothing.

I ALSO CHECKED THAT V-03 DOES NOT DEMAND UNPRODUCIBLE EVIDENCE, since its assertion (b) is a NEGATIVE
property and a `V-*` requiring evidence that cannot exist is its own defect class. It is producible: I
patched `_relative_revalidation_verdict` so a present baseline turns a passing measurement into a refusal,
re-ran the matrix, and watched all three green rows flip to `False` with the detector reporting them, then
reverted to a clean tree. So the mutation V-03 mandates exists and would genuinely fail a correct
assertion (b).

THE FIRST SERIOUS FINDING IS THAT E-05 FALSIFIES AN EXISTING SPEC HISTORY NOTE AND THE PLAN DOES NOT
NOTICE. That is PR-601. The plan cites the 2026-09-23 `n9na1c` amendment as PRECEDENT for the shape of its
own spec edit, which is apt, but that note's own words are "WHAT IS UNCHANGED, deliberately and verbatim:
the conjunctive conditions, the closed vocabulary, the two answers that may release, ... and the HONEST
LIMIT paragraph including the maintainer's 2026-09-08/2026-09-20 ruling that no gate may refuse on the
strength of a pre-work baseline." E-05 edits exactly that paragraph. So the moment this plan lands, the
spec carries one history note asserting the paragraph was deliberately preserved verbatim and another
amending it, with nothing connecting them, in the file a graduating plan is reviewed against. The plan
cannot fix this by editing the earlier note (that would rewrite a record, and the note was true when
written), so the remedy is that the NEW note must name the paragraph and distinguish the RULING, which
genuinely is preserved verbatim, from the undirected WORDING, which is what changes. That distinction is
this plan's entire content, so stating it in the history costs nothing and is where a future reader will
look.

THE SECOND IS A ONE-EDIT COLLISION WITH ANOTHER ITEM'S DECLARED WORK. That is PR-602. The sentence E-04
rewrites ENDS with a citation to the absent `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`,
one of four such citations in this module that backlog `gia5i7` owns and that this plan correctly defers.
E-04 must add a live citation to its new test into that same sentence. The plan says "must not add a new
one" (meaning a new dangling citation) but never says what to do about the dangling one already there, and
the two natural instincts are both wrong: striking it absorbs `gia5i7`'s declared work into a plan that
does not declare it and stales that item's own four-site measurement, while re-pointing it at the new E-03
file is wrong on the MERITS, because E-03 pins the DIRECTION rule and not the `not-mine`
byte-identical-outcome property that citation describes, so the two are not substitutes. I verified
`gia5i7` genuinely covers these citations and not only its headline symbol: its body names both
`NothingRefusesOnTheBaseline` and `TheTwoMeasurementsAreComparable` explicitly. The honest outcome is one
live citation beside one dangling one, with the carrier named, and E-04/V-04 now require exactly that and
make either instinct a failed validation.

PR-603 is the two open questions. Both carried `- Status: open` with `- Owner: reviewer`, which is a
direct request for this review to decide them, and leaving them open would have made the plan `NO-GO` for
no reason since neither blocks. I resolved both in the direction the plan drafted, but on evidence I
measured rather than by deferring to its preference, and recorded each as a decision below. For OQ-01 the
deciding point the plan does not make is that the pointer names a SECTION HEADING IN THE SAME FILE, so a
rename shows up in the diff that causes it, whereas the four rotted citations in this same module all point
OUT of the file at a deleted test; the rot argument is real but does not apply to this pointer's shape. For
OQ-02 the deciding point is that the reader's entry path is the banner, which E-04 makes cite the new file,
so "a future reader may not find it" is answered by the rule itself.

ONE JUDGEMENT I AGREE WITH AND RECORD RATHER THAN PASS OVER. The plan classifies itself `chore` and
declines a `Blocks-Release` gate, on the ground that no user-perceptible behavior is wrong (the relative
verdict already behaves correctly) and the cost falls on the next author to read the rule. That is the
correct application of the repository's perceptibility test, and the plan states the judgement openly with
its measurement rather than burying it. I note the counter-argument honestly: a FALSE safety rule in a
comment is the kind of thing that could mislead an author into weakening a gate, which is a real risk. It
is still not a user-perceptible defect today, and the plan's own E-02 exists to prove the protected
property is intact before a word changes.

Bare suite at review HEAD: `3361 passed, 2 skipped, 3 warnings in 137.59s`. Working tree clean after every
probe and after the assertion-(b) mutation was reverted (`git status --short` empty).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | IN-SCOPE | Rubric A (public record compatibility), F (honest documentation) | The spec's `- 2026-09-23 note (aw specs)` line: "WHAT IS UNCHANGED, deliberately and verbatim: ... and the HONEST LIMIT paragraph including the maintainer's 2026-09-08/2026-09-20 ruling"; E-05's target is that paragraph | E-05 FALSIFIES AN EXISTING SPEC HISTORY NOTE AND THE PLAN CITES THAT NOTE ONLY AS PRECEDENT. After this plan the spec carries one note claiming the HONEST LIMIT paragraph was deliberately preserved verbatim and another amending it, unconnected, in the file a graduating plan is reviewed against. The earlier note cannot be edited (it was true when written; the plan contract forbids rewriting a record), so the new note must reconcile it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-10. E-05 now requires the new history line to name the paragraph the 2026-09-23 note recorded as verbatim-unchanged and to distinguish the preserved RULING from the changed WORDING; V-05 requires that clause quoted and the earlier note shown UNMODIFIED, and fails the item if the earlier note is edited. Spec-sync section records the conflict rather than only the precedent. |
| PR-602 | HIGH | IN-SCOPE | Rubric C (avoid duplicate paths), G (dependencies and ownership) | `grep -c "tests/test_suite_baseline.py" agent_workflows/runner_shared.py` = 4; the sentence E-04 rewrites ends with `::NothingRefusesOnTheBaseline`; `gia5i7`'s body names that class and `::TheTwoMeasurementsAreComparable` explicitly | E-04 MUST ADD A LIVE CITATION INTO A SENTENCE THAT ALREADY ENDS IN A DANGLING ONE OWNED BY ANOTHER ITEM, and the plan never says what to do with it. Striking it absorbs `gia5i7`'s declared work undeclared and stales that item's four-site measurement; re-pointing it at the E-03 file is wrong on the merits, since E-03 pins the DIRECTION and not the `not-mine` byte-identical-outcome property. Both instincts are available to an executor and both are wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-11. E-04 now requires ADDING the live citation and LEAVING the dangling one, stating which act it performed and why re-pointing would be wrong; V-04 requires the dangling citation shown byte-unchanged and makes striking or re-pointing a FAILED validation. The Deferred row now confirms `gia5i7` covers these specific citations. |
| PR-603 | LOW | IN-SCOPE | Workflow Step 3 (resolve open questions) | OQ-01 and OQ-02 both `- Status: open` with `- Owner: reviewer` | TWO OPEN QUESTIONS WERE ADDRESSED TO THIS REVIEW AND WOULD OTHERWISE HAVE STAYED OPEN. Both are non-blocking and both were drafted with the author's preferred answer, so leaving them open would have withheld a decision the plan explicitly asked for. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both resolved in the drafted direction but on independently measured grounds (D-1, D-2 below), `- Owner:` updated to record the reviewer as the decider per the workflow's ownership rule. Neither E-item changed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01: should the corrected banner state the direction as a bare rule, or keep a pointer to the relative-verdict section as the worked example? | KEEP THE POINTER, as E-04 drafts. | Drop it and let the rule stand alone: rejected. The rot objection is real and this module proves it (four already-rotted citations), but it does not apply to THIS pointer's shape: it names a section heading in the SAME file, so a rename appears in the diff that causes it, whereas all four rotted citations point OUT of the file at a deleted test file. A reader given only the abstract rule must re-derive the permitted case, which `tgyfs2` did at the cost of a full pass over three artifacts. | Verified the pointer's target is a live reachable case by driving `_relative_revalidation_verdict` across the matrix (red+baseline-names-it is the only `True`); `runner_shared`'s "THE RELATIVE REVALIDATION VERDICT" section text; `tgyfs2`'s own record of paying that cost | yes |
| D-2 | OQ-02: should E-03's pin live in a new file or beside an existing revalidation test? | NEW FILE `tests/test_suite_baseline_direction.py`, as E-03 drafts. | Join an existing revalidation test: rejected, there is none to join. Add it to a broadly-named module: rejected, because the two absent files this banner cites are exactly what happens when a guard's home does not say what it guards. | `grep -rn "_relative_revalidation_verdict\|new_failures_since_baseline" tests/` returns nothing (re-run at review); `tests/test_suite_baseline.py` and its classes measured absent; sibling plans `cvs2b7` and `jw6cm3` both add property-named modules | yes |
| D-3 | Should an `- Item-Dependencies:` edge be declared, given sixteen pending plans declare the same spec file? | NO EDGE. Record the concurrency and rely on the merge gate. | Declare `executed:` on the overlapping plans: rejected, the grammar offers no "prefer after" edge, and gating this work on unrelated review cycles for mere file adjacency would overstate a preference as a constraint. | Read all three pending plans that both declare the spec and contain "HONEST LIMIT" (`pi3bk8`, `wzhe4n`, `yu47nf`): all three use the phrase for the unrelated host-capability preflight docstring, none names section 5.1 or proposes editing it, so the edit surfaces are disjoint | yes |
| D-4 | Accept the plan's `chore` classification and its refusal to invent a `Blocks-Release` gate? | ACCEPT. | Escalate to `bug` with a release gate: rejected. A false safety rule in a comment is a genuine hazard to a future author, but no user-perceptible behavior is wrong today and the shipped verdict is correct, which is the repository's stated test. | `AGENTS.md`'s perceptibility test; backlog `aced01` carries no `- Blocks-Release:` and is `- Work-Kind: chore`; F-2/F-3 reproduced showing shipped behavior correct | yes |
