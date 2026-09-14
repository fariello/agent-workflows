# Review: delete the pre-launch dirty-tree refusal and report it as a warning instead, child d7qoxv (Set dirtygates)

- Subject-Id: d7qoxv
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `bffedb96`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review; at `--phase review-finalize` it reports one `IPD-Q501`, which is the
escalation gate working as designed on the blocking question this review added.

DISCLOSURE: same repository, same model family as the author, so this is a near-self-review worth less
than an independent one. Its value rests on what was DRIVEN rather than re-read. Measured here: every
code anchor the plan cites, opened individually (`oc_runipd.py:6122-6148`, `:6123`, `:1955`,
`agy_runipd.py:3258-3267`, `:1299`, `lane_containment.py:2537`, `:2543-2551`, `:2554-2582`,
`run_evidence.py:223-241`, `oc_runipd.py:1988`); the full grep for every consumer of the four
`clean_base_*` keys and the `clean-base-refused` event across `agent_workflows/` and `tests/`; the
target test module RUN to get a real baseline (`15 passed`); spec `7ckptx` R4, R2.6, A5c, R5.4 and A14
read at their lines; `CID-3` grepped across the whole specs tree; and approved plan `3i0aaz`'s E-02/E-03
read in full.

THE PLAN'S CORE ARGUMENT IS SOUND AND REVIEW DID NOT WEAKEN IT. F-1 is accurate (this really is the only
one of three dirty-tree gates that is not path-scoped, and `dirty_within`'s docstring says in terms that
disjoint dirty work is ignored BY DESIGN to preserve concurrent multi-agent work). F-3's disproof is a
real measurement and its logic holds for a lane cut from a commit. F-4's downstream replacement exists
(`make_integration_validation_runner:1988`). F-5 is correct and the untracked exclusion should survive.
The E-01/E-02/E-03 sequencing is right, and both host call sites were verified byte-parallel, so E-02 is
a genuine mirror rather than a reconciliation.

WHAT REVIEW FOUND, in order of consequence. FIRST, a HIGH left open: `3i0aaz` is approved,
`Blocks-Release: next`, and its E-03 EXTENDS the very refusal this plan deletes to the
`--no-isolate-worktree` path, while E-04 here rewrites the R5.4 obligation that plan builds on. The two
have a coherent combined shape (remove for isolated, keep and extend for shared-tree, `--allow-dirty-base`
as consent) but choosing it amends an APPROVED spec, so it is escalated as blocking OQ-02 rather than
decided. SECOND, FOUR SHIPPED TESTS BREAK AND THE PLAN NAMED NONE OF THEM. `tests/test_lane_clean_base.py:192`
asserts the literal source strings `attempt["clean_base_dirty_paths"]` and `"event": "clean-base-refused"`
by inspecting `execute_item`'s SOURCE, so E-01's rename to a non-refusal key breaks it TEXTUALLY, not
behaviorally, which is the kind of failure an executor misreads as a flaky test. `:105` and `:114` pin
the refusal classification; `:123` pins the untracked exclusion and must stay green. All four are now
enumerated in E-05 with the required disposition for each, plus the design question they expose: does the
pure RULE still classify not-clean while only the CALLER stops refusing? THIRD, E-02's host-parity
citation was simply wrong: it invoked spec R4, which governs PERMISSION POSTURE, where the live authority
is R2.6 plus A5c. Worse, the `CID-3` identifier that both the plan and the shipped agy code comment lean
on appears NOWHERE in the specs tree, so an executor chasing it finds nothing.

FOURTH, MY OWN PRIOR EDIT TO THIS FILE HAD DAMAGED E-04 and is repaired. Reviewing the orchestrator
earlier today, I inserted a scope caveat mid-item and left the original `(a)/(b)/(c)` justification list
orphaned after an unrelated sentence, and that stranded fragment still carried the "100% batch failure"
figure the same review had disproved. E-04 is now one coherent instruction carrying the measured figures.
Recorded plainly because a reviewer's own edit is exactly the kind of defect a later reader would
attribute to the author.

FIFTH, OQ-01 was RESOLVED FROM EVIDENCE rather than asked, because an approved plan already settled the
identical question: `3i0aaz`'s own review (PR-005) rejected a per-item report as firing "once per queue
entry and says the same thing N times" and named `initialize_run` on both hosts as the run-start seam.
The answer is both, split by purpose (stderr line once per run, per-attempt record per item), and it
carries a coordination obligation because `3i0aaz` E-02 is approved to add an untracked-dirt report at
that same seam.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | B (security), D (invariants), G | `.aw/records/plans/pending/20260907-dirtybase-01-3i0aaz-...ipd.md:12` (`approved`, `Blocks-Release: next`), its E-03/E-04/E-05; this plan's E-04 | `3i0aaz` is approved to EXTEND this clean-base refusal to the `--no-isolate-worktree` path and to add `--allow-dirty-base` as its consent surface. This plan deletes the refusal and rewrites spec `7ckptx` R5.4, the obligation that plan builds on. A wholesale amendment silently negates an approved release blocker, and a weakened approved spec cannot be un-shipped once other plans are reviewed against it. | C:Medium; U:Low; S:Medium-High; F:Medium; Overall:Medium-High | OPEN | Escalated as blocking OQ-02 naming PR-101, stating the coherent combined end state (remove for isolated, keep for shared-tree) so the maintainer answers a concrete question. E-04 revised to scope the amendment to the isolated case pending that answer. |
| PR-102 | HIGH | UNDER-SCOPE | E (testing), D | `tests/test_lane_clean_base.py:105`, `:114`, `:123`, `:192`; `python3 -m pytest tests/test_lane_clean_base.py -o addopts=""` -> `15 passed` | Four shipped tests break and the plan named none. `:192` asserts the literal source strings `attempt["clean_base_dirty_paths"]` and `"event": "clean-base-refused"` by SOURCE INSPECTION, so E-01's rename breaks it textually; `:105`/`:114` pin the refusal classification; `:123` must stay green or the tracked/untracked scope has widened. E-05 said only "update the file". | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now enumerates all four with the required disposition for each (retarget, do not delete), records the `15 passed` baseline, forbids widening the untracked scope, and surfaces the rule-versus-caller design question. New F-7 records the measurement. |
| PR-103 | MEDIUM | IN-SCOPE | G (honest documentation) | `.aw/records/specs/20260901-7ckptx-...spec.md:248-298` (R4 = permission posture), `:165-172` (R2.6), `:477-480` (A5c); `grep -rn CID-3 .aw/records/specs/` returns nothing | E-02's host-parity authority was cited as spec "R4", which governs permission posture and says nothing about guard parity; the live authority is R2.6 + A5c + R6.1. The `CID-3` identifier both the plan and the shipped agy comment rely on exists nowhere in the specs tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 recites R2.6/A5c, flags `CID-3` as a dead reference, and records that both call sites were verified byte-parallel at review. New F-8 carries the evidence. |
| PR-104 | MEDIUM | IN-SCOPE | G (executability) | this plan's E-04 as it stood at HEAD `bffedb96` | E-04 was internally incoherent: an orphaned `(a)/(b)/(c)` justification list stranded after the `aw specs note` instruction, still carrying the "100% batch failure" figure that F-6 disproves. Cause: this reviewer's own earlier edit during the orchestrator review. An executor would have written a disproved figure into an approved spec. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 rewritten as one coherent instruction carrying F-6's measured figures (68 refusals, 27/42, 23/41, 18/43, 36 cascades) and explicitly forbidding the disproved rate. Authorship of the defect recorded above. |
| PR-105 | MEDIUM | IN-SCOPE | C (architecture), F (KISS) | `3i0aaz` E-02 and its review PR-005; `oc_runipd.py:2732`, `agy_runipd.py:1800` | OQ-01 (warning once per run or per item) was left open although an approved plan already answered it, and E-01 as written emits per item, which that plan's review explicitly rejected as N-times noise. The two plans would also place two adjacent dirty-tree reports at the same run-start seam. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 resolved from evidence (stderr once per run, record per item) with the coordination obligation stated: extend `3i0aaz`'s report, do not add a parallel one. E-01's conflict called out inside the resolution. |
| PR-106 | LOW | IN-SCOPE | G | this plan's Concern; F-6 | The Concern block carried the disproved "100% batch failure rate" and "$106" figures. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Corrected during the orchestrator review pass and re-verified here against each run's `state.json`. |
| PR-107 | LOW | IN-SCOPE | E | `tests/test_lane_clean_base.py:172` | The plan never said what happens to `test_guard_precedes_spawn_and_allocation`, which asserts the guard call precedes spawn and lane allocation. It should stay green (the call remains, now warning), and that ordering IS what R5.4's "before any worker is spawned" clause becomes under a reporting obligation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires it kept green and meaningful rather than deleted. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should OQ-01 (warning per run or per item) be asked, or resolved from evidence? | Resolved from evidence: stderr line ONCE PER RUN, per-attempt record PER ITEM. | Ask the maintainer as the plan intended; or pick per-item silently as E-01 implies. | `3i0aaz` E-02 and its review's PR-005 settled the identical question, naming `initialize_run` (`oc_runipd.py:2732`, `agy_runipd.py:1800`) as the run-start seam and rejecting per-item as N-times noise. `plan-review.md:242-244` forbids asking what the repository already answers. | yes |
| D-2 | Is PR-101 (collision with approved `3i0aaz`) resolvable by narrowing this plan unilaterally? | No. Escalate as blocking OQ-02, while narrowing E-04 to the isolated case as an interim guard. | Narrow E-04 silently and close the question; or let E-04 amend R5.4 wholesale on this plan's technical merits. | `3i0aaz:12` carries a human approval and `Blocks-Release: next`; AGENTS.md reserves public-contract and release-scope calls to the human, and an approved-spec weakening cannot be cleanly undone. | no |
| D-3 | E-01 renames `clean_base_refused` to a non-refusal key. Keep or drop the durable record? | Keep it, retargeting the source-inspection test rather than deleting it. | Delete `test_refusal_records_the_dirty_paths_on_the_attempt` as obsolete along with the refusal. | That test is the only thing pinning that the dirty paths reach durable state rather than only stderr (`tests/test_lane_clean_base.py:192`); dropping it would let the operator's audit trail vanish silently while the suite stayed green. | yes |
| D-4 | Was it in scope to repair E-04's incoherence, given it was this reviewer's own earlier edit? | Yes, repair it and record the authorship. | Leave it and report it as a finding for the author to fix. | `plan-review.md:214-222` requires revising the plan in place and replacing ambiguity rather than appending; leaving a known-incoherent item that would write a disproved figure into an approved spec fails the Fix Bar at Low remediation risk. | yes |

D-2 is `Reversible: no` and is ESCALATED as required: raised in this plan as OQ-02 with `- Blocking: yes`
and `- Finding: PR-101`, so the lint gate refuses the plan at every checkpoint until the maintainer
answers. It is the same decision as the orchestrator's OQ-03, carried here because this plan performs the
spec amendment.

## Round 2

Reviewed at HEAD `59cdc718`, as an INDIVIDUAL review of this child. It exists because the orchestrator's
round-2 review raised OQ-04: Orders 01, 02 and 04 carried a stale `Readiness: no-go` from their round-1
reviews although their blocking questions had been resolved, and that field could not honestly be rewritten
by a review whose ledger was the parent. This is the review that earns the field for `d7qoxv`.

Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0 findings) before semantic review;
`--phase review-finalize` re-run after revisions and it now reports exactly one finding, the deliberate
`IPD-Q501` for the new blocking OQ-03.

DISCLOSURE: same model family as the author and as the round-1 reviewer, so treat this as a near-self-review
worth less than an independent one. Its value rests on what was MEASURED at this HEAD.

ROUND 1'S BLOCKER IS GENUINELY DISCHARGED. PR-101 escalated the collision with approved `3i0aaz` over the
spec obligation; OQ-02 resolved to the path split and E-04 now reads "SO THE OBLIGATION IS SPLIT BY PATH,
NOT REMOVED", with V-04 failing the item if `3i0aaz` E-03 is left nothing to build on. Re-verified
independently rather than trusted: R5.4 at `:416-420` and A14 at `:570-572` are exactly where the plan cites
them; both call sites open with the identical `if isolate and self_finalize and not is_review:` (oc `:6122`,
agy `:3262`); `CleanBaseResult.reason` at `:2545-2551` still begins "refusing to launch an unattended
isolated turn"; the baseline is `15 passed`; and all four `initialize_run`/`refuse_unimplemented_run_flags`
anchors behind OQ-01 are correct. Every anchor in this plan resolved.

WHAT ROUND 2 FOUND IS A SECOND, DIFFERENT COLLISION WITH THE SAME APPROVED PLAN, AND ROUND 1 MISSED IT.
OQ-02 split the SPEC and the BEHAVIOR by path, which was the right answer and dissolved that conflict. It
said nothing about the TEST FILE. There, the two plans issue contradictory instructions about one file, with
a human approval behind one of them. `3i0aaz` requires `tests/test_lane_clean_base.py` to stay green WITH AN
EMPTY DIFF, three times over: E-06 says leave it "UNEDITED so the two guards are provably independent"; V-06
demands "`git diff --stat` EMPTY for that file. That empty diff is what proves E-03 relaxed a CONDITION
rather than rewriting a rule"; and its scope fence DELIBERATELY omits the file so any edit is a declared
violation. This plan's E-05 rewrites four of that file's tests and declares it in `Scope-Paths`. Whichever
runs second either fails its own validation or reverts the other. `3i0aaz` E-03's expected outcome also
asserts "the isolated path's message and behavior are unchanged", which is exactly what this plan changes.
Neither plan is wrong on its own terms, which is why this is escalated (OQ-03) rather than decided:
recommended answer is deliberate sequencing (`3i0aaz` first), because the empty-diff proof is meaningful
only at that plan's execution and is spent once consumed.

THE TEST CENSUS WAS ALSO INCOMPLETE, AND THE MISSING ONE IS THE SUBTLE KIND. E-05 enumerated four tests;
reading the file in full found a fifth, `test_the_two_checks_answer_different_questions:274`, whose docstring
states "clean-base REFUSES, overlap does not ... asserted as behaviour so the two checks cannot quietly
collapse into one". Its assertions are on the RULE, which E-03 keeps, so it will probably stay GREEN while
its docstring becomes false. A test that passes while documenting behavior the code no longer has is worse
than one that fails, because nothing surfaces it. Its disposition is now a docstring correction with
assertions untouched.

TWO SMALLER CORRECTIONS AND ONE POSITIVE RESULT. E-01 still instructed the executor to emit the stderr
warning at the per-item call site, contradicting this plan's own resolved OQ-01 in the same document, so the
per-run/per-item split is now written into E-01 itself rather than only into the question. The title
("Delete the pre-launch dirty-tree refusal") overstates what ships now that the refusal is retained for the
shared-tree path, recorded in Scope rather than fixed by a rename. And the attempt-key rename was VERIFIED
SAFE, which the plan asserted without establishing: `grep -rn "clean_base"` finds consumers in exactly three
modules plus the one test file, and nothing in `render_stream.py`, `attention.py` or any viewer surface reads
the key or the event name.

I DID NOT WEAKEN THE PLAN'S GOAL, and the evidence for it is stronger than the plan claimed in one respect:
the three other `item["status"] = "blocked"` producers per host were located and are now explicitly excluded
from the change, so the removal is narrower and safer than "stop writing blocked" would have been.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | IN-SCOPE | B, D | `3i0aaz:12`; this plan's E-04; spec `:416-420`, `:570-572` | CARRIED FROM ROUND 1 AND NOW DISCHARGED. The spec-obligation collision with approved `3i0aaz` is resolved by the path split; verified E-04 performs a split rather than a replacement and V-04 enforces it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 resolved by the maintainer; E-04 and V-04 carry it. Stale "pending OQ-03" gating language removed in five places. |
| PR-108 | BLOCKER | IN-SCOPE | D (invariants), E (testing), G | `3i0aaz` E-06 `:91`, V-06 `:212-214`, fence `:252`, Scope-Paths `:10`, E-03 outcome `:67`; this plan's `Scope-Paths:8` and E-05 | A SECOND collision with the same approved release-blocking plan, over `tests/test_lane_clean_base.py`. `3i0aaz` requires it byte-identical as its load-bearing proof and leaves it undeclared so any edit is a violation; E-05 rewrites four of its tests and declares it. Whichever runs second breaks: this plan first makes `3i0aaz`'s V-06 unobtainable; `3i0aaz` first makes E-05 a fence violation. Not solvable by worktree isolation, which makes concurrent edits safe but cannot arbitrate contradictory instructions. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | Escalated as blocking OQ-03 with three costed answers and a recommendation (sequence `3i0aaz` first, which costs neither plan its proof). New F-9 records the evidence. E-05 and the gate now forbid starting it before the answer; E-01 to E-04 explicitly remain ungated so the plan is not stalled wholesale. |
| PR-109 | HIGH | UNDER-SCOPE | E (testing), G | `tests/test_lane_clean_base.py:274-299` read in full at review | THE CENSUS IS FIVE, NOT FOUR. `test_the_two_checks_answer_different_questions:274` asserts the clean-base/overlap contrast and documents "clean-base REFUSES" as deliberate behavior. Its assertions target the RULE (kept by E-03) so it likely stays GREEN while its docstring turns false, which no assertion would catch. E-05 dispositioned only four tests. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | New F-10. E-05 now names all five with a disposition each; `:274` gets a docstring correction with assertions untouched, and going red there is defined as evidence the RULE was changed (which E-03 forbids). V-05 requires the corrected docstring pasted. |
| PR-110 | HIGH | IN-SCOPE | C (architecture), G | this plan's E-01 versus its own OQ-01 resolution | E-01 still instructed "emit the dirty-path list as a WARNING to stderr" at the PER-ITEM call site, while OQ-01 in the same document had resolved that the stderr line goes ONCE PER RUN. Round 1 recorded the conflict inside the question but never fixed the item, so an executor reading the checklist ships the N-times noise `3i0aaz`'s review explicitly rejected. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 rewritten: record per item HERE, stderr line once per run from `initialize_run` (all four anchors verified), with the de-duplication alternative permitted but requiring a comment. The coordination obligation with `3i0aaz` E-02's report at the same seam is stated in the item. V-01 now requires a three-item run proving the line appears ONCE. |
| PR-111 | MEDIUM | UNDER-SCOPE | A (correctness), D | `oc_runipd.py:6129`, `:6174`, `:6244`; `agy_runipd.py:3269`, `:3302`, `:3381` | THREE SITES PER HOST WRITE `item["status"] = "blocked"` and only the first is this gate. The plan described its change as stopping the terminal disposition without bounding it to the clean-base site, so a literal-minded executor could generalize it and silently disable two unrelated refusals. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | All six anchors measured and recorded in E-01 with an explicit instruction not to generalize; V-01 requires the grep showing three sites per host still present. |
| PR-112 | MEDIUM | UNDER-SCOPE | E (testing) | this plan's Required tests; OQ-02's path split | NO TEST PROVED THE SPLIT WAS HONORED. The plan's validation covered the isolated path becoming a report, but nothing asserted the SHARED-TREE path still refuses, which is the entire substance of OQ-02's resolution and the property `3i0aaz` inherits. A correct-looking execution could have removed both and passed. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Low | FIXED | Required tests gain the shared-tree regression (refusal preserved under `--no-isolate-worktree`, or, pre-`3i0aaz`, the spec obligation proven still present) plus a rule-unchanged assertion. |
| PR-113 | MEDIUM | IN-SCOPE | G (honest documentation) | plan title versus Scope after OQ-02 | The title says "Delete the pre-launch dirty-tree refusal"; after OQ-02 the refusal is RETAINED for the shared-tree path and only the isolated path becomes a report. A title that overstates the change misleads every future reader and every index listing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in Scope that the title overstates and that the Scope line governs; NOT renamed, because renaming churns the slug and every cross-reference and AGENTS.md reserves plan naming to `aw rename plans` (D-7). |
| PR-114 | LOW | IN-SCOPE | G (executability) | five sites citing "the orchestrator's blocking OQ-03" | Five passages still told the executor to treat the spec split as "pending the orchestrator's blocking OQ-03". That question is resolved AND was renumbered to OQ-02 during the orchestrator's round 2, so the citation pointed at a question number that now means something else entirely. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | All five corrected to state the question is resolved, with the renumbering noted so a reader who remembers the old number is not confused. Note the number OQ-03 is now REUSED here for PR-108's new question, which is exactly why the stale citations had to go. |
| PR-115 | LOW | IN-SCOPE | G | `Item-Dependencies: none`; OQ-03 recommended answer | `Item-Dependencies:` is `none`, and OQ-03's recommended answer would make that false by requiring `executed:3i0aaz`. Left unstated, an executor would treat the ordering as free. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded in the scope check as an under-scope note, with an instruction not to add the dependency before the question is answered nor to assume the ordering is free. |
| PR-116 | LOW | IN-SCOPE | G, E | `grep -rn "clean_base" agent_workflows/ tests/ --include=*.py` at review | POSITIVE RESULT, recorded rather than left implicit. The plan asserted the attempt-key rename was safe but never established it. Verified: consumers exist in exactly three modules plus the one test file, and nothing in `render_stream.py`, `attention.py` or any viewer reads the key or the event name, so the rename cannot silently break a reporting surface. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-11 records the search and its result, so the executor does not re-derive it and a later reader knows it was done rather than assumed. |
| PR-117 | LOW | IN-SCOPE | G | Deferred section, Scope check (pre-edit) | The deferred section still described the work as "deleting the refusal" and did not list the shared-tree path as deliberately out of scope, so the single most important boundary of the revised plan appeared nowhere in the section whose job is to state boundaries. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred section rewritten with the shared-tree refusal as an explicit preserved exclusion, `dirty_tree_overlap`'s retention noted, and the co-worker-attribution problem correctly attributed to the shared-tree case. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-5 | PR-108 (the test-file ownership collision) is a BLOCKER. Resolve it by narrowing E-05, or escalate? | Escalate as blocking OQ-03, with E-01 to E-04 explicitly ungated so the plan is not stalled wholesale. | Narrow E-05 to a new test file now (presupposes answer (b) and would leave four tests asserting a refusal the code no longer performs); or declare this plan the owner and amend `3i0aaz`'s V-06 (edits an approved release-blocking plan's validation without authority). | The repository holds a HUMAN approval on `3i0aaz` (`:12`, `Blocks-Release: next`) whose V-06 names the empty diff as its proof. AGENTS.md reserves release-scope and public-contract calls to the human, and `plan-review.md:227-229` reserves unilateral narrowing for cases repairable with bounded edits that do not presuppose a maintainer decision. Answer (b) has a measurable cost (four tests left asserting removed behavior) that makes silent selection wrong. | no |
| D-6 | Should this review edit `3i0aaz` to resolve the collision, since it is the "owning plan" for the empty-diff requirement? | No. Leave `3i0aaz` untouched and escalate. | Edit `3i0aaz` E-06/V-06 to drop the empty-diff proof, per `plan-review.md:224-226` (fix in the owning plan). | `3i0aaz` is `Status: approved` and outside this review's Step 0 ledger. Editing an APPROVED plan's validation is not a bounded in-place revision, it retracts a proof a human signed off on; and AGENTS.md's shared-checkout rule forbids reworking another party's approved artifact. The fix-in-the-owning-plan rule governs findings that SPAN plans under review, not amendments to approved work. | yes |
| D-7 | The title now overstates the change. Rename the plan file, or record the discrepancy? | Record it in Scope. | `aw rename plans` to a title matching the reduced scope. | A rename changes the `<slug>` in the uniform artifact name and every cross-reference (the orchestrator's child table, this plan's review record, three sibling plans, the plans index). Cost of a stale-but-explained title is one paragraph; cost of a rename is a wide reference update for no behavioral gain. Same reasoning applied to the orchestrator in its round-2 D-3. | yes |
| D-8 | Which readiness does this plan carry? | `no-go`, verdict REVIEWED - OPEN QUESTIONS. | `go-pending-approval`, on the grounds that eleven of twelve findings are FIXED and OQ-02 is resolved. | `plan-review.md:543-545` makes NO-GO correct when ANY open question or ANY unfixed BLOCKER remains; OQ-03 is open and PR-108 is an unfixed BLOCKER. `aw ipd lint --phase review-finalize` independently reports `IPD-Q501` for the open blocking question, which is the gate agreeing. So OQ-04 on the orchestrator is answered for THIS child: its `no-go` is now EARNED rather than stale. | yes |

D-5 is `Reversible: no` and is ESCALATED as required: raised in this plan as OQ-03 with `- Blocking: yes`
and `- Finding: PR-108`, so the lint gate refuses the plan at every checkpoint until the maintainer answers.

NOTE ON THE ORCHESTRATOR'S OQ-04: it asked who would re-review the three children carrying a stale
`no-go`. For `d7qoxv` the answer is now on record: this round did it, and the `no-go` STANDS, but for a
NEW and different reason (PR-108) rather than the resolved one. That is a materially better position than
before, because the field is now honest. `metc8b` and `u23gbn` still carry unverified `no-go` values.

## Round 3

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round exists to record that round 2's gating finding
was resolved by the maintainer's own decision, taken on 2026-09-13 through the `askme` workflow, one
interactive prompt at a time. Nothing in the plan was re-reviewed here and no new finding was sought;
appending a round is the mechanism `plan-review.md:187` prescribes for this, since the gate reads only
the current round. The earlier rounds are left exactly as written.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-108 | BLOCKER | IN-SCOPE | G (executability) | the resolved `OQ-03` in this plan's `## Open questions` | This plan and approved plan `3i0aaz` gave contradictory instructions about `tests/test_lane_clean_base.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer chose deliberate sequencing: `3i0aaz` executes FIRST and collects its empty-diff proof, then this plan runs and may break that property, since the proof is spent once collected. Neither plan loses anything and no approved validation is edited. The executor must add `- Item-Dependencies: executed:3i0aaz`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's answer to OQ-03 discharge PR-108, or does the finding need a fresh review pass? | It discharges it; record the discharge and leave the earlier rounds untouched. | Run a further full review round on this plan. | The finding's own recorded remedy was a human decision, and that decision is now recorded in the owning plan with its reasoning. A further round was priced on evidence and rejected: the round earlier the same day cost 3h 02m and $106.07 across nine items and raised four NEW blocking questions, so it was not expected to yield a clean sheet. | yes |

HONEST LIMIT: the discharge rests on the maintainer's decision, not on an independent reviewer's
re-examination. If a later reader needs assurance that this plan's content was checked afresh, that
assurance is in rounds 1 and 2 and not here.
