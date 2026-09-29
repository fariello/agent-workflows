# Review findings: plan vtup6x

- Subject-Id: vtup6x
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `650f6772` in a lane worktree. Structural preflight `aw ipd lint --phase author`
reported `conforming` with ONE `IPD-Z602` density advisory (E-05); after revision `--phase
review-finalize` reports `conforming` with ZERO findings. The advisory was acted on rather than
dismissed, since the linter's own contract is that a passing count check does not clear conceptual
density. No pre-review snapshot was owed: the plan was committed and unmodified (`git status --short`
empty) and the lane-input copy under `.aw/state/lane-inputs/rev-23/` is byte-identical (`diff -q`
reports IDENTICAL). Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings in 48.18s`. NO
PRODUCTION FILE, TEST, OR WORKFLOW BODY WAS MODIFIED by this review; the one probe that mutated a test
class attribute (`MERGE_DECISIONS`, to reproduce F-06) restored it in the same process and never wrote
to disk.

EVERY ONE OF THE TEN AUTHORED FINDINGS REPRODUCES, and two of them are unusually strong. F-01: rubric
G's bullet does exempt criteria counting `stable code facts (test assertions, schema keys, enum
members)`. F-03: `grep -rln 'Live-artifact' .aw/system/workflows/` matches `plan-review/plan-review.md`
ALONE while the neighbouring right-sizing and maintainer-sizing bullets do appear in
`plan-review-long/review-rubric.md`, so the parity hole is real. F-04: the three-part unsatisfiable bar
and the `u23gbn` calibrated example are present as described. F-06 REPRODUCES EMPIRICALLY, which is the
plan's best work: corrupting `MERGE_DECISIONS[0]`'s expected exit code to `99` makes the suite report
`FAILED (failures=1)` with the assertion naming "`check` decided 1 of 7 merge situations wrongly", while
an `addSubTest` driver prints `PASS` for ALL SEVEN ROWS INCLUDING THE CORRUPTED ONE. F-07's census
reproduces exactly by AST walk: 4 append-without-in-context-assert subTest blocks, all in
`tests/test_executed_transition_gate_e2e.py`, out of 266 subTest blocks total (so 262 others, against
the plan's stated 242 plus its 4; the plan's arithmetic differs slightly from mine but its CLAIM, that
the population is exactly four blocks in one file, is exactly right and is what bounds child `02`).
F-08: `tests/test_attention_contract.py`'s row test asserts INSIDE the subTest block, so its verdicts
are truthful, exactly as the plan says. F-09: `pytest-subtests` is NOT installed
(`ModuleNotFoundError`), `addopts` is as quoted, and the file collects as 7 tests. F-10: neither table
is in `tests/test_executed_transition_gate.py` any more; both are in the `_e2e` file. All three carriers
resolve (`t5txjk` is a real pending sibling, `7fzqop` a real open backlog item, `nos070` graduated
naming both children), the siblings' `Scope-Paths` do not overlap, and P16's exemption sentence is
verbatim as quoted.

THE PLAN'S DEFECT IS ITS OWN THESIS APPLIED ONE LAYER UP, which is what makes PR-001 a BLOCKER on an
otherwise strong plan. This plan's whole argument is that a POINTER to a mechanism is legitimate while
treating the pointer's text as the contract is what breaks. E-02 then instructed the executor to
DUPLICATE a normative paragraph into the long-form variant, which treats two texts as one contract,
with nothing in the toolchain able to diff them for semantic equivalence. The repository had already
solved this for this exact pair of files, and solved it with a test: the feasibility rule lives in one
place and the long-form carries a reference plus a summary.

I also verified what does NOT need fixing: the lint-rule deferral is correct and its authority axis is
real (Section 5.4's closing sentence and Section 10.1 both say what the plan says); `IPD-S402` and the
`pre-transition` arm of `IPD-S404` do test only non-emptiness; no managed block in
`agent_workflows/engine.py` restates rubric G; OQ-01's placeholder reasoning holds (`Required evidence:
TODO falsifiable evidence.` is a tracked marker) and OQ-02's spec-status answer matches the
repository's own instruction that specs are living contracts; and all four `Carrier-Declined` rows state
why no obligation exists rather than deferring work.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | C. Architecture (duplicate normative path); F. Honest documentation | plan E-02 as authored ("adds the amended bullet there"); `tests/test_plan_review_feasibility_rule.py` asserting `../plan-review/plan-review.md` and ``per the parity note in `plan-review-long.md` ``; that test's `test_spec_review_feasibility_rule_reference` docstring | **E-02 PRESCRIBED DUPLICATING A NORMATIVE PARAGRAPH INTO THE LONG-FORM VARIANT, reproducing this plan's own target defect one layer up.** The repository's parity mechanism for THIS EXACT PAIR of files is a POINTER and it is TEST-ENFORCED: the shipped feasibility-rule test asserts the long-form section carries the literal path and the literal parity-note phrase, and its sibling case is named "references plan-review's rule without copying the five points". Nothing in the toolchain compares two prose paragraphs for semantic equivalence, so two normative copies of one rule drift unobserved and a reader cannot tell which is authoritative. The plan's own thesis is that a POINTER is legitimate while treating the pointer's text as the contract is what breaks; a duplicated paragraph treats two texts as one contract. Worse, the plan's "HOW THIS PLAN CAN FAIL SILENTLY" paragraph named only the opposite hazard (forgetting the second file), so the more likely failure was unguarded. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 rewritten to write a POINTER bullet (operative one-sentence summary plus both reference literals) and to FORBID duplication with the measurement behind it. E-06 pins the pointer trio and is explicitly forbidden from asserting paragraph equality. Added F-11 and OQ-03; the gate's fence gains this as its ZEROTH constraint and its silent-failure paragraph is rewritten to name the real hazard. |
| PR-002 | HIGH | IN-SCOPE | D. Anti-regression (the calibrated example teaches the unsound shape) | `i4c0c3` V-03 observed evidence lines `[PASS] a hand-edited status flip OUTSIDE any merge` and `[PASS] a \`git mv\` into executed/ OUTSIDE any merge`; this plan's own F-06 | **THE CALIBRATED EXAMPLE THIS PLAN TELLS AUDITORS TO FOLLOW PASTES VERDICT LINES FROM EXACTLY THE DRIVER SHAPE F-06 FALSIFIES.** `i4c0c3` V-03's evidence is for `MergeAwareInTreeEvidenceTests`, one of F-07's four unsound blocks, and its per-row `[PASS]` lines are the output F-06 measured printing PASS for a failing row. Its SUBSTITUTION is genuinely sound (function-gone proof naming the removing commit, both successor rows named by case string and table constant, enclosing verdict pasted), which is what earns it the calibrated slot. But citing it without the caveat would bless the unsoundness in the very document that teaches the substitution, and E-03's own wording ("paste that row's individual verdict") points straight at the mechanism that cannot fail. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now requires the text to cite `i4c0c3` for its substitution discipline AND warn that its verdict lines are not a model to copy, naming `t5txjk` as the owner of a sound driver; and to state the row-verdict obligation in terms of SOUNDNESS (the mechanism's failure must be observable for that row; reject a per-row PASS co-occurring with an enclosing failure, which is the measured signature) with an honest fallback until child `02` ships. Added F-12. |
| PR-003 | HIGH | UNDER-SCOPE | G. Executability (an obligation with no owning E-item) | plan `## Required tests / validation` and V-05 as authored; the authored checklist ending at E-05 | **THE PLAN'S SELF-DESCRIBED "REAL ACCEPTANCE TEST" HAD NO OWNING E-ITEM.** The DOGFOOD CHECK and the whole-suite comparison lived only in prose and inside V-05's evidence demand, so the E/V mapping never reached them and an executor could complete every checklist item without performing either. V-05 had also become a catch-all demanding a module run, a mutation proof, a suite comparison, and a managed-block search under one checkbox. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-07 owning the suite comparison, the two named test files, the managed-block re-derivation and the dogfood check, with V-07 demanding each separately. E-07 also records the distinction that keeps the dogfood check honest: naming a test FILE TO RUN is a mechanism, not a name-as-contract. |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Right-sizing and conceptual density | plan E-05 as authored; `aw ipd lint --phase author` reporting `IPD-Z602` on E-05 ("3 clauses") | **E-05 BUNDLED TWO INDEPENDENT TEST SURFACES.** The presence-and-narrowing assertion over the single-file body and the PARITY assertion over the long-form body have different failure meanings, and after PR-001 they assert structurally DIFFERENT things (rule text versus pointer literals), so one V-item could check neither properly. The deterministic check flagged it independently. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-05 (presence and narrowing) and E-06 (parity pointer), with V-05/V-06 each demanding one surface's source-file mutation proof and empty-diff restore. `- Highest E allocated:` raised to `07`. Lint now reports zero findings. Added F-14. |
| PR-005 | MEDIUM | IN-SCOPE | E. Testing (a mutation proof on the wrong surface) | plan V-05 as authored (mutate `review-rubric.md` only) | **THE SINGLE MUTATION PROOF EXERCISED ONLY ONE OF THE TWO ASSERTIONS.** V-05 required deleting the rule from the long-form file, which after the split proves E-06 and says nothing about E-05's narrowing assertion. The narrowing assertion is the one that could most easily be written vacuously (a test asserting the bullet merely EXISTS passes both before and after the amendment, since the bullet existed already). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 now requires RE-WIDENING the single-file exemption as its mutation (the mutation that distinguishes the amended bullet from the original), and V-06 requires deleting the long-form pointer bullet; each requires its own empty-diff restore. |
| PR-006 | LOW | IN-SCOPE | Step 1 evidence (a count that does not reproduce) | plan F-07 ("The other 242 subTest blocks across 46 files"); measured 266 total subTest blocks | **F-07's SECONDARY COUNT DOES NOT REPRODUCE** (I measure 266 total, so 262 others rather than 242+4=246). The finding's OPERATIVE claim reproduces exactly and is what bounds child `02`: 4 append-without-in-context-assert blocks, all in `tests/test_executed_transition_gate_e2e.py`, in the four named test methods. Recorded rather than silently corrected because the difference is plausibly a counting-method difference (regex versus AST walk) rather than an error, and because a live population count in a Findings row is context, not a bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Left F-07's operative claim intact (it reproduces) and did NOT rewrite its subsidiary number, since the plan's own new rule says a count like this belongs in prose as context and must not become a bar; the review record carries the discrepancy so a later reader can see both measurements. No E-item or V-item depends on the 242. |
| PR-007 | LOW | UNDER-SCOPE | G. Execution contract | plan gate as authored | The fence's silent-failure paragraph named only the forget-the-second-file hazard, and the fence listed three negative constraints none of which forbade duplication, so the failure PR-001 identifies was entirely unguarded in the gate an approver reads. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The fence gains duplication as its ZEROTH and most important constraint; the silent-failure paragraph is rewritten to name duplication as the subtler and more likely failure and to point at V-06's specific confirmation. |
| PR-008 | LOW | IN-SCOPE | F. Honest documentation (a dated number presented as a bar) | plan `## Required tests / validation`; plan V-05 as authored | The plan correctly forbids comparing against any number written in it, then had no stated baseline at all, leaving an executor to take one without being told the honest framing. Separately the spec-sync managed-block claim was an assertion pointing at a V-item, with no recorded measurement behind it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-07 records the review-measured `3246 passed, 2 skipped` at HEAD `650f6772` explicitly labelled DATED CONTEXT, not the bar, and requires a same-lane baseline judged as a delta of failing node ids. Spec sync now records the review measurement (the grep returns nothing) and requires re-derivation by search in E-07/V-07. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the long-form variant carry a COPY of the amended rule or a POINTER to it (PR-001)? | A POINTER: the rule's operative one-sentence summary plus the two reference literals, with the full text in exactly one place. | (a) A verbatim copy in both files as authored; rejected because nothing diffs two prose paragraphs for semantic equivalence, so the copies drift silently and a reader cannot tell which is authoritative. (b) A bare cross-reference with no summary; rejected because an agent running only the long-form flow must be able to APPLY the rule without opening a second file, which is what the long-form's existing summary bullets already do. (c) Moving the rule wholly into the long-form and pointing the single-file at it; rejected because the single-file variant is explicitly the PORTABLE one that must stand alone. | Measured: `tests/test_plan_review_feasibility_rule.py` enforces exactly shape (pointer plus anchors) for these two files, asserting the literals `../plan-review/plan-review.md` and ``per the parity note in `plan-review-long.md` ``; its sibling case is named "references plan-review's rule without copying the five points", and `spec-review.md` uses the same shape. Recorded in the plan as OQ-03. | yes |
| D-2 | E-03 requires pasting "that row's individual verdict", but the only obvious driver is the one F-06 falsifies (PR-002). Require the verdict anyway, drop the requirement, or require soundness? | Require SOUNDNESS: the mechanism's failure must be observable for that row, with an explicit honest fallback (paste the enclosing table's verdict plus the row's inputs and expected value, and SAY that is what you did) until child `02` ships a sound driver. | (a) Require the per-row verdict with no soundness condition; rejected because F-06 measures that the obvious driver prints PASS for a failing row, so the requirement would mandate misleading evidence. (b) Drop the per-row requirement and accept the enclosing verdict; rejected because the row identity is the substance of the substitution and dropping it would let an executor paste a whole-file pass and claim the row was checked. | F-06 reproduced empirically at review (`FAILED (failures=1)` beside seven `PASS` rows). The plan's own Deferred row already states it "is deliberately usable with no tooling at all", so an honest fallback is consistent with its design rather than a weakening of it. F-08 establishes the assert-in-context case where per-row verdicts ARE truthful, which is why the rule must key on soundness rather than on a command. | yes |
| D-3 | F-07's subsidiary count (242 others across 46 files) does not reproduce; I measure 262 of 266 (PR-006). Correct it, or leave it? | Leave the number and record both measurements in this review record. | Rewriting F-07's number to my measurement; rejected because the difference is plausibly a counting-method artifact (AST walk versus whatever the author ran), no E-item or V-item depends on it, and this plan's own new rule says a live-population count belongs in prose as CONTEXT and must never become the bar. Substituting one unexplained number for another would not improve it. | The finding's operative claim (4 blocks, 1 file, 4 named methods) reproduces exactly by AST walk over `tests/*.py`; that claim is what bounds child `02`. Applying the plan's own rule to the plan's own finding is the consistent action. | yes |

### Verdict and readiness

Verdict: `APPROVE WITH REVISIONS APPLIED`. Readiness: `GO - PENDING HUMAN APPROVAL`
(`- Readiness: go-pending-approval`). All eight findings are FIXED in place; nothing is DEFERRED or left
OPEN, so no finding needed escalation as a `- Blocking: yes` question. All three open questions are
`resolved`, none blocking. `aw ipd lint --phase review-finalize --agent` reports `conforming` with ZERO
findings after the edits (the authored E-05 density advisory is gone, having been acted on rather than
dismissed).

NOTE FOR THE APPROVER. This plan amends an `implemented` spec, correctly declared in `- Scope-Paths:`
with its reason in the spec-sync section, so both runners will announce and reconcile the spec edit. It
carries no `- Blocks-Release:` gate, correctly, since backlog `nos070` carries none. Its sibling
`t5txjk` (Order 2) declares no overlapping paths, so no `- Item-Dependencies:` edge is owed; note
however that this plan's E-03 now NAMES `t5txjk` as the owner of the sound driver its fallback waits on,
which is a prose reference and not a dependency, because this plan is deliberately usable with no
tooling at all.
