# Review findings: plan 9aprci

- Subject-Id: 9aprci
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a27dced2` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` with ZERO findings BEFORE semantic review, and `--phase
review-finalize --agent` reports `conforming` with ZERO findings after the revisions, so nothing
here was structural. No pre-review snapshot was owed: the plan was committed and unmodified, and the
lane-input copy under `.aw/state/lane-inputs/rev-5/` is byte-identical to `HEAD` (`diff -q` reports
IDENTICAL). Bare suite at review HEAD: `3291 passed, 2 skipped, 3 warnings in 65.53s`. NO production
file, test, or workflow body was modified by this review; the only file changed is the plan itself,
plus this record.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
on RE-MEASURING the claims against the tree and on reading the plans it neighbours, not on re-reading
its own prose. That is what produced the blocker below, which the author had the evidence to find and
did not look for.

ALL NINE AUTHORED FINDINGS REPRODUCE AT THIS HEAD, and two are stronger than stated. F-01: AST-walking
both hosts, `oc_runipd.run_queue` spans `3460-4093` with its dispatch `While` at `3609-3954`,
`requeue_interrupted` called at `3494` and `if retry_incomplete:` at `3496`, both OUTSIDE the loop;
`agy_runipd.run_queue` spans `2949-3479` with its `While` at `3079-3393` and the same two constructs
at `2976`/`2978`. A walk for any `requeue`-named call inside either dispatch loop returns the EMPTY
LIST on both hosts, so the impossibility the plan is about still holds, now across three widely
separated commits (`6466cd33`, `377e8fb2`, `a27dced2`) and roughly 3300 lines of drift. F-02:
`agent_workflows/ipd_lint.py` contains ZERO occurrences of `Required evidence` and 3 of `Observed
evidence`, so the linter genuinely never reads the field the plan is about. F-03: searching the five
stems over `plan-review.md` and every `plan-review-long/*.md` returns 4 matches across 3 files, and
none is a reachability rule (the Step 2.4 sweep paragraph and the two copies of the HOW-questions
rule), so the gap is a real absence. F-04: the three-part bar, the `u23gbn` example, the rejection of
an unmeasured impossibility claim, and the plan-defect closing rule are all present in
`intent-audit.md` as described. F-05: spec Section 5.4 ends with the quoted sentence verbatim, and
rubric G's `Live-artifact` bullet carries the quoted `Review is the only enforcement surface`
parenthetical. F-08 and F-09 reproduce from `akzy45`'s own text: its V-03 `Observed evidence:` opens
with the quoted sentence and records `Result: pass`, and its review history records `SECOND (PR-902):
E-03's PREMISE WAS INVERTED` beside the scope-fence clause `Do NOT add a resurrection or un-blocking
mechanism`, so the contradiction did survive a review that corrected that very item.

THE BLOCKER THIS REVIEW EXISTS TO HAVE FOUND (F-10) is a sequencing defect the plan's own Deferred
section walked up to and then looked away from. The plan declared `- Item-Dependencies: none` while
THREE of its four scope paths are also declared by `vtup6x`, and TWO by `k6t24p`, both of which are
already `reviewed` with `- Readiness: go-pending-approval`. The overlap is not incidental file
contention, which worktree isolation handles: all three plans edit ONE bullet's neighbourhood in
rubric G. `vtup6x` E-01 REWRITES the `Live-artifact` bullet's exempt clause; `k6t24p` E-01 inserts its
own bullet DIRECTLY AFTER that same bullet; and this plan's E-01 as authored anchored `immediately
after the existing Live-artifact bullet` too. Separately, `vtup6x` E-03 extends the SAME
`intent-audit.md` unsatisfiable-demand paragraph, identified by the same opening string, as this
plan's E-03. The plan KNEW `vtup6x` existed, cited its `- Status:` and `- Readiness:` accurately, and
reasoned about the collision for the SPEC path alone, concluding correctly that it should not amend
Section 5.4. It never asked the same question about the three prose paths sitting in its own
`- Scope-Paths:`. Fixed: dependency edges declared so the runner's dependency-depth sort dispatches
this plan last; E-01 re-anchored to re-read rubric G as it stands and to report which neighbours were
present; E-03 told to extend what it finds and preserve the sibling's `i4c0c3` example; V-01, V-03 and
V-05 now demand the pre-edit text and the dependency state as evidence.

F-11 IS THE MORE INTERESTING FINDING, because both plans are wrong about the same thing in opposite
directions. F-06's verbatim-copy measurement is CORRECT for the two bullets it measured: `- **Right-
sizing and conceptual density` and `- **Maintainer sizing signals` are byte-identical across
`plan-review.md` and `review-rubric.md`. It then generalized to "a rubric bullet is copied", and the
counter-example is the very bullet E-01 sits beside: `- **Live-artifact success criteria` is ABSENT
from `review-rubric.md` entirely. So this pair of files has no settled shape for a bullet of this
kind, and `vtup6x` F-03 is right to call that a parity HOLE. `vtup6x` E-02 then resolves it the other
way, with a bolded instruction not to duplicate and the claim that the shipped test enforces a pointer
for this pair. That claim is measurably wrong about WHICH FILES the test compares:
`tests/test_plan_review_feasibility_rule.py`'s `PLAN_REVIEW_LONG_FILE` is
`plan-review-long/03-resolve-and-finalize.md`, and no test under `tests/` names `review-rubric.md` at
all, which `k6t24p` E-03 measured independently and states. Neither plan is therefore following an
existing convention for `review-rubric.md`; both are establishing one. This plan still copies, for a
reason that survives the single-source objection: every bullet in `## A. Plan completeness` is a full
copy today, so a lone pointer reads as an omission, and E-04's parity test converts the copy from a
drift risk into an enforced invariant, which is exactly the guard `vtup6x` says is missing. E-02 now
records the competing argument and instructs the executor to follow the shape actually present and
report a divergence rather than resolve it silently.

F-12 is a trap the author avoided in E-02 and re-opened in E-04. The two rubric surfaces do NOT share
section letters: `plan-review.md` `### G.` is `Plan executability`, while `review-rubric.md` `## G.` is
`UX and accessibility` and its plan-executability content is `## A. Plan completeness`. E-02 named the
right section, but E-04 described the parity test without warning that a G-slice would assert against
accessibility text and SILENTLY PASS. `k6t24p`'s own review recorded the identical trap as its PR-101.
Also folded into E-04: do not extend `tests/test_plan_review_feasibility_rule.py`'s module-level
`ANCHOR_PHRASES`, which `test_spec_review_feasibility_rule_reference` bounds at one occurrence, so
adding to it would change what three passing tests assert.

WHAT I DELIBERATELY DID NOT CHANGE. The plan's refusal to add a lint rule is CORRECT and its axis is
correctly stated as authority rather than effort: spec Section 5.4's closing sentence forbids the
linter from judging evidence sufficiency, reachability is a sufficiency judgement, and F-02 measures
that the field is not parsed at all, so a rule would cross a spec boundary and invent a parsing
surface. Rubric G already refuses the mechanical route for its neighbouring case in the same words.
I also left the `CHANGELOG.md` question where the plan put it, flagged for a reviewer rather than
settled, and I am the reviewer, so D-3 records my answer. The plan's decision not to touch the
`assess` template is right and its reason is measurable: `Required evidence: TODO falsifiable
evidence.` appears in `ipd_authoring.py` at three sites as a placeholder marker.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | G. Plan executability (dependencies, sequencing) | `.aw/records/plans/pending/20260929-nos070-01-vtup6x-*.ipd.md:7` `- Scope-Paths:` and E-01/E-02/E-03; `.aw/records/plans/pending/20260929-findtier-03-k6t24p-*.ipd.md:7` `- Scope-Paths:` and E-01/E-02; plan `:8` `- Item-Dependencies: none` | Declared `- Item-Dependencies: none` while all THREE prose scope paths are also declared by `vtup6x` (`reviewed`, `go-pending-approval`) and two by `k6t24p` (same state). All three edit one bullet's neighbourhood in rubric G, and `vtup6x` E-03 extends the identical `intent-audit.md` paragraph as this plan's E-03. Not file contention (isolation handles that) but three designs for one section. The plan's Deferred section reasoned about the SPEC collision with the same plan and never asked the same question of its own prose paths. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Declared `- Item-Dependencies: executed:vtup6x, executed:k6t24p` (both parse as canonical typed edges). E-01 re-anchored off the contested position to re-read rubric G as it stands; E-03 told to extend what it finds and preserve the sibling's `i4c0c3` example; F-10 records the measurement; Scope check gained a sequencing paragraph; gate and approval summary disclose it. |
| PR-002 | HIGH | IN-SCOPE | F. KISS / single source of truth | measured at review: `- **Live-artifact success criteria` present in `.aw/system/workflows/plan-review/plan-review.md`, ABSENT from `.aw/system/workflows/plan-review-long/review-rubric.md`; `tests/test_plan_review_feasibility_rule.py:36-38` `PLAN_REVIEW_LONG_FILE`; `vtup6x` E-02 and F-11 | F-06's verbatim-copy conclusion holds for the two bullets it measured and over-generalizes: the bullet E-01 sits beside is absent from the long-form, so the pair has NO settled shape for this kind of bullet. A reviewed sibling resolves the same hole the opposite way (pointer, not copy) on a claim about the shipped test that is wrong about which files it compares. OQ-02 therefore rested on an incomplete measurement. | C:Low; U:Medium; S:Low; F:Low; Overall:Medium | FIXED | E-02 now records the competing argument, states why this plan still copies (every bullet in that section is a copy; E-04's test supplies the missing guard), and requires following the shape actually present with any divergence reported as a finding. F-11 added. OQ-02's resolution amended to record the counter-example and the sibling's position. V-02 now demands the pre-existing shape be recorded, not only the written one. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing and verification | `.aw/system/workflows/plan-review-long/review-rubric.md` headings (`## A. Plan completeness`, `## G. UX and accessibility`) vs `.aw/system/workflows/plan-review/plan-review.md` `### G. Plan executability`; `tests/test_plan_review_feasibility_rule.py:140-146`; `k6t24p` history PR-101 | E-04 specified a rubric-G presence test and a `## A.` parity test without warning that the two surfaces do not share section letters, so a G-slice on the long-form would assert against accessibility text and pass silently. Separately, reusing the existing module's shared `ANCHOR_PHRASES` would change what its at-most-one spec-review assertion means. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-04 now names both headings explicitly, requires confirming a heading exists before slicing, and forbids extending the shared `ANCHOR_PHRASES` or repointing `PLAN_REVIEW_LONG_FILE`. V-04 must quote the two headings sliced. F-12 added. |
| PR-004 | LOW | IN-SCOPE | G. Plan executability (evidence) | plan V-01 `Required evidence:` as authored (`after the Live-artifact bullet`); V-03, V-05 | Three validation items demanded evidence of a position and a paragraph text that two reviewed siblings are concurrently changing, so a truthful executor could have been forced to report a mismatch as a failure rather than as the expected state. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now demands the full rubric-G bullet list with the neighbours named; V-03 permits (and requires recording) either the two-example or three-example paragraph depending on dependency state; V-05 demands the dependency state and pre-edit text explicitly. |

### Decisions

ID | Question | Chosen | Alternatives considered | Basis | Reversible
D-1 | The plan collides with two reviewed siblings on all three prose paths. Split the section's ownership into one plan, or order the three? | Order them, with `- Item-Dependencies: executed:vtup6x, executed:k6t24p`, and disclose the choice to the approving human. | (a) REPLAN into a single plan owning rubric G, rejected because two of the three are already `reviewed`/`go-pending-approval` and re-planning them is not this review's authority; (b) leave `none` and rely on worktree isolation, rejected because isolation resolves textual conflict and not three designs for one section; (c) drop this plan's prose paths, rejected because the reachability rule is the whole deliverable. | `.aw/records/plans/pending/20260929-nos070-01-vtup6x-*.ipd.md:7,9,10` and E-01/E-02/E-03; `.aw/records/plans/pending/20260929-findtier-03-k6t24p-*.ipd.md:7,9,10` and E-01/E-02; `agent_workflows/runner_shared.py` `queue_sort_key`/`dependency_depth` (dependency depth is the first sort key); `ipd_schema.parse_item_dependencies` accepted both edges | yes
D-2 | Copy the bullet verbatim into `review-rubric.md`, or write a pointer as `vtup6x` E-02 instructs for its own bullet? | Copy, but instruct the executor to follow whichever shape is actually present and report a divergence as a finding. | (a) Pointer-only, rejected because every bullet in `## A. Plan completeness` is a full copy today and a lone pointer reads as an omission, and because the claim that a shipped test enforces a pointer for this pair is wrong about the files; (b) convert the sibling bullets to pointers for consistency, rejected as an unrequested change out of scope; (c) leave the question open and blocking, rejected because the repository answers it for the section as it currently stands. | measured: `- **Right-sizing and conceptual density` and `- **Maintainer sizing signals` byte-identical across the two files; `- **Live-artifact success criteria` absent from `review-rubric.md`; `tests/test_plan_review_feasibility_rule.py:36-38` points at `03-resolve-and-finalize.md`, not the rubric | yes
D-3 | The plan flagged the `CHANGELOG.md` entry for the reviewer to overrule. Add one? | No entry, and the path stays out of `- Scope-Paths:`. | Adding a one-line `Changed:` entry as `7b4945c6` did for a comparable plan-review rule change, rejected because the audience for this rule is an agent running `/plan-review`, and because `e6566341`, whose exact three-surface shape this plan copies, added none. | `git show --stat 7b4945c6` (touches `CHANGELOG.md`) versus `git show --stat e6566341` (three workflow bodies, no CHANGELOG); plan `## Scope check` under-scope FIRST already records both precedents | yes
D-4 | Should the reachability obligation be a lint rule after all, since a reviewer may skip it? | No. Keep it a review obligation and keep the deferral on the authority axis. | Adding an `ipd_lint` rule that parses `Required evidence:` and refuses an unreachable demand, rejected because it would contradict an implemented spec. | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md:291` `The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.`; measured: 0 occurrences of `Required evidence` in `agent_workflows/ipd_lint.py`; `plan-review.md:553` refuses the mechanical route for the neighbouring rule for the same reason | yes
