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
