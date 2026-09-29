# Review findings: plan k6t24p

- Subject-Id: k6t24p
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0cfc41a9` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` conforms
after. No pre-review snapshot was owed: the plan was committed and unmodified. NEITHER RUBRIC FILE,
NO TEST, AND NO `agent_workflows/` FILE WAS MODIFIED by this review; every measurement came from
read-only probes and in-memory drives of the shipped functions.

EVERY LOAD-BEARING CLAIM IN THIS PLAN REPRODUCED, which is worth stating plainly because the plan is
unusually well evidenced for its size. `artifact_core.drift_exit_code` reads exactly as quoted and
returns `error -> 1`, `warning -> 1`, `info -> 0`, `empty -> 0` when driven with a synthetic `Drift`
(and `1` for a legacy 3-field `Drift`, whose empty severity is not `info`). `check_engine.RULE_REGISTRY`
holds exactly 52 rules at 33 `error` / 12 `warning` / 7 `info`, and `check_engine.rule_spec`
resolves `check.identity-absent-from-name` to `RuleSpec(severity='warning', assurance='repository',
determinism='deterministic', invariant='I-09')`, so F-06's "45 of 52 could not satisfy the demand" is
exact. Executed plan `3i6rso`'s V-04 does demand "a synthetic-tree run whose only finding is the new
code exiting 0", and its `Observed evidence` does record the executor refusing it, proving the
impossibility and raising DECISION 04-3i6rso-D1. `test_the_rule_gates_no_lifecycle_step` was deleted
by `80db6750` (confirmed with `git log -S`). GUIDING_PRINCIPLES section 16 prohibits `read_text()`
and substring searches against `agent_workflows/*.py` and carries the narrow exception the plan's
E-03 relies on, in the words the plan quotes. Pending plan `0ykozn` carries the same exit-0 wording
legitimately, because its rule is registered `info` and its own text pins that. The `ipd-spec` doc
does delegate outward to "Rubric G" rather than restating the convention, so the spec-sync reasoning
holds. And both rubric files are genuine installed body members (`engine.collect_source_members`
lists both), so the parity obligation is real rather than cosmetic.

WHAT REVIEW FOUND IS THAT TWO OF THE THREE E-ITEMS WOULD HAVE MISPLACED OR BROKEN THEIR TARGET, and
one demanded weaker evidence than the very refusal it sets out to canonize.

**THE TWO RUBRICS' SECTION LETTERS DO NOT CORRESPOND (PR-101, HIGH).** The plan's Goal, E-01 and its
proposed-changes list all frame the destination as "section G", which is right for the single-file
rubric (`### G. Plan executability`) and WRONG for the long-form one, whose `## G.` is
`UX and accessibility`. The long-form file's plan-executability material is `## A. Plan completeness`,
and that is where the `Right-sizing and conceptual density` bullet E-02 names as its anchor actually
sits. E-02 as authored said only "beside its existing sibling" and never named a section, so an
executor carrying "section G" across from E-01 would have filed an evidence-shape rule under
accessibility in one of the two routes. Measured: the single-file sections run A Correctness /
B Security / C Architecture / D Anti-regression / E Testing / F KISS / G Plan executability; the
long-form run A Plan completeness / B Data / C Security / D Architecture / E Invariants / F Testing /
G UX / H Operations. E-02 now names `## A. Plan completeness`, requires anchoring by quoted text
rather than by letter, and V-02 fails the item on a bullet landing under `## G.`.

**THE TEST MODULE E-03 REUSES DOES NOT READ THE SECOND SCOPE PATH, AND ITS SHARED ANCHOR LIST IS
LOAD-BEARING (PR-102, HIGH).** E-03 instructs the executor to reuse
`tests/test_plan_review_feasibility_rule.py` and "follow the parity-pointer test already in that
file", which reads as though the module already covers both rubric surfaces. It does not: its
`PLAN_REVIEW_LONG_FILE` constant resolves to `plan-review-long/03-resolve-and-finalize.md`, not the
rubric, and no test under `tests/` names `review-rubric.md` at all. Repointing that constant would
break the existing `test_long_form_plan_review_feasibility_rule`. Separately, the module-level
`ANCHOR_PHRASES` list is consumed by all three of its tests including
`test_spec_review_feasibility_rule_reference`, which asserts that AT MOST ONE of those phrases
appears in `spec-review.md`; appending this plan's anchors to the shared list would change what that
test asserts and could fail it for an unrelated reason. Its section-slicing pattern also keys on
`### 3.1 ` and `## 1. Resolve open questions`, neither of which exists in either rubric, so copying
that pattern yields a confusing "missing heading" failure rather than a useful one. E-03 now
mandates a new constant, a separate anchor list, and re-derived slice boundaries; V-03 fails the item
on a repointed constant or an extended shared list, and requires the run to show 4 or more passing
tests against the measured pre-existing `3 passed`.

**LIMB (b) DEMANDED LESS THAN THE REFUSAL IT CANONIZES (PR-103, MEDIUM).** As authored, limb (b) is a
single `drift_exit_code` call with the return value pasted. That is satisfied by any nonempty
non-`info` list and so does not localize the exit code to the severity under test. The evidence
`3i6rso`'s executor actually produced is a CONTRASTIVE pair (`drift_exit_code(drift) == 1` beside
`drift_exit_code([d._replace(severity="info") ...]) == 0`) plus a per-rule count delta table
(`before total=324 / after total=329`, with `check.identity-absent-from-name 0 -> 2` as the only
moved id). Canonizing the weaker form would let a future author demand less than the calibrated
example already achieved, which inverts the plan's own purpose. E-01 now requires the pair and
permits the count delta as an optional third limb, marked optional because a rule reporting nothing
on this tree cannot produce a nonzero delta.

**TWO EVIDENCE CORRECTIONS (PR-104 MEDIUM, PR-105 LOW).** F-03 attributes the deletion of
`tests/test_review_findings.py` to `80db6750`; `git log --diff-filter=D` names `19313eed` for BOTH
stale files, and `80db6750` only shrank the first by 51 lines. The conclusion is unaffected. And
F-04 quotes an in-code comment reading `error -> 1, warning -> 1, info -> 0, empty -> 1`; the
`empty` figure is wrong at two separate `check_engine.py` sites, because `any([])` is `False` so the
`else 0` branch is taken. The plan's own Concern and F-01 state it correctly as `-> 0`, so this is an
inconsistency inside the plan rather than a wrong premise, but it matters because E-01 writes a
bullet describing this exact gate. New F-08 records the measurement, the gate is told not to trust
the comment, and correcting the comments is explicitly deferred (it would breach the plan's own
`agent_workflows/` fence) with a carrier.

**A PRE-EXISTING STRUCTURAL FINDING WAS CLEARED AS PART OF REVISION.** Before this review touched
anything, `aw check` reported `check.ipd-uncarried-obligation` at `error` severity against this plan:
five deferral rows recorded outstanding obligations with no durable carrier. Verified pre-existing by
stashing the review's edits and re-running (finding present, repository total 21 both ways). Each row
already stated its reasoning in prose; what was missing was the typed `- Carrier:` /
`- Carrier-Declined:` line the gate reads. Added one per row (four declines and a `Carrier: y43g6q`
for the coverage-restoration row), clearing the finding and dropping the repository total from 21 to
20. This is a revision the workflow's Step 4 requires rather than an out-of-scope fix: an unfixable
`error`-severity check finding on the reviewed plan would have blocked it.

Every finding is FIXED. None was deferred, so no escalation to a `- Blocking: yes` question is owed.
OQ-01 survives review unchanged and its reasoning was independently confirmed: `spec-review.md`
reviews specs, which carry no `E-*`/`V-*` checklists, so a plan-only evidence-shape rule has no home
there. The plan's non-goals are well drawn (no lint rule, no code change, no edit to the executed
plan or to the legitimately-worded pending one), and its decision to fix an authoring contract rather
than the correct code is the right diagnosis.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | high | IN-SCOPE | G. Plan executability | `.aw/system/workflows/plan-review/plan-review.md` `### G. Plan executability` against `.aw/system/workflows/plan-review-long/review-rubric.md` `## G. UX and accessibility` and `## A. Plan completeness` | The two rubrics' section letters do not correspond. The plan frames the target as "section G" throughout while E-02's anchor actually lives in the long-form file's section A, so an executor would file an evidence-shape rule under accessibility in the long-form route. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-02 names `## A. Plan completeness`, mandates anchoring by quoted text not by letter, and pastes both files' measured section lists; V-02 fails the item on a `## G.` placement; new F-09; a conventions bullet records the non-correspondence. |
| PR-102 | high | IN-SCOPE | E. Testing and verification | `tests/test_plan_review_feasibility_rule.py` constants `PLAN_REVIEW_LONG_FILE` (= `03-resolve-and-finalize.md`) and module-level `ANCHOR_PHRASES`; `rg -ln 'review-rubric' tests/` -> no match; `3 passed` baseline | E-03 reads as though the module already covers `review-rubric.md`. It does not, so the executor must add a constant rather than repoint one three tests depend on; and the shared `ANCHOR_PHRASES` list is asserted against with an at-most-one bound by `test_spec_review_feasibility_rule_reference`, so extending it changes what that test asserts. Its slice headings also do not exist in either rubric. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-03 mandates a new constant, a separate anchor list, and re-derived slice boundaries; V-03 fails the item on a repointed constant or extended shared list and requires 4+ passing tests; new F-10; a conventions bullet records the constants. |
| PR-103 | medium | UNDER-SCOPE | D. Anti-regression and domain invariants | `3i6rso` V-04 `Observed evidence` (the paired `drift_exit_code(drift) == 1` / `_replace(severity="info") == 0` assertion and the `before total=324 / after total=329` per-rule table) | Limb (b) as authored is a single exits-1 call, satisfied by any nonempty non-`info` list, so it does not localize the exit code to the severity under test. The plan would canonize weaker evidence than the refusal it exists to bless. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | fixed | E-01 requires limb (b) as the contrastive pair and permits the per-rule count delta as an optional third limb; V-01 fails a single-call limb (b); new F-11. |
| PR-104 | medium | IN-SCOPE | Evidence accuracy | `drift_exit_code([]) == 0`; `any([]) is False`; the two `check_engine.py` comment sites reading `empty -> 1` | F-04 repeats an in-code comment whose `empty -> 1` figure is wrong, while the plan's own Concern and F-01 state `-> 0`. E-01 writes a bullet describing this exact gate, so an inherited wrong figure would ship into both rubrics. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-04 corrected and new F-08 records the measurement; the gate tells the executor not to trust the comment; V-01 requires the bullet's empty-list claim to match the executor's own measurement; correcting the comments deferred with carrier `hwhbc8` (an `agent_workflows/` edit the plan forbids itself). |
| PR-105 | low | IN-SCOPE | Evidence accuracy | `git log --oneline --diff-filter=D -- tests/test_review_findings.py` -> `19313eed`; `git show --stat 80db6750 -- tests/test_review_findings.py` -> 51 deletions, file retained | F-03 attributes the file's deletion to `80db6750`, which only shrank it; `19313eed` deleted both stale files. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | F-03 carries the corrected attribution and states the conclusion is unaffected. |
| PR-106 | high | IN-SCOPE | G. Plan executability | `aw check` reporting `check.ipd-uncarried-obligation` (severity `error`) against this plan, verified pre-existing by stashing the review's edits (finding present, total 21 both ways) | Five deferral rows recorded outstanding obligations with no typed durable carrier, so the plan carried an `error`-severity check finding that would have blocked it. Each row stated its reason in prose but lacked the `- Carrier:`/`- Carrier-Declined:` line the gate reads. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Added one typed annotation per row (four `Carrier-Declined` and `Carrier: y43g6q` for the coverage row); finding cleared, repository total 21 -> 20. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The long-form rubric has no section corresponding to the single-file rubric's "section G". Place the mirrored bullet by letter, by its sibling bullet, or ask the maintainer which section owns evidence-shape rules? | Anchor on the sibling `Right-sizing and conceptual density` bullet and name its actual enclosing section (`## A. Plan completeness`) explicitly, instructing the executor to locate it by quoted text. | (a) By letter: rejected outright, since the long-form `## G.` is `UX and accessibility` and that is the misplacement being prevented. (b) Ask the maintainer: rejected because the repository already answers it. The two files agree on exactly two shared bullets (`Right-sizing` and `Maintainer sizing signals`) and both sit in the long-form file's section A, so the repository's own demarcation of where a plan-authoring rubric bullet belongs is observable rather than a judgement call. | `rg '^### [A-H]\.'` and `rg '^## [A-H]\.'` on the two files; both shared bullets present verbatim inside `## A. Plan completeness`. | yes |
| D-2 | Limb (b) as written is weaker than the evidence the canonized refusal produced. Strengthen it on review authority, or leave the plan's wording and note the gap? | Strengthen it in place: require the contrastive exits-1/swapped-to-info-exits-0 pair, and permit the per-rule count delta as an optional third limb. | (a) Leave as written and note the gap: rejected because the plan's entire purpose is to stop authors demanding the wrong evidence shape, so shipping a weak canonical shape defeats it. (b) Require the per-rule delta as a mandatory third limb: rejected because a rule that legitimately reports nothing on this repository's tree cannot produce a nonzero delta, which would recreate the unsatisfiable-demand defect in a new form. | `3i6rso`'s V-04 evidence block showing both the paired assertion and the count table; `drift_exit_code` measurements showing a single exits-1 call is satisfied by any nonempty non-`info` list. | yes |
| D-3 | This plan carried a pre-existing `error`-severity `check.ipd-uncarried-obligation` finding. Fix it as part of review revision, or report it and leave the plan blocked? | Fix it: add the typed `- Carrier:`/`- Carrier-Declined:` annotation each of the five rows was missing. | (a) Report and leave: rejected because Step 4 requires the reviewed plan to be left conforming, and an `error` check finding on the plan would block it while every row already stated its reasoning, making this a transcription rather than a new judgement. (b) Attach a backlog carrier to all five: rejected because four of the rows genuinely decline (no outstanding work exists), and minting carriers for non-obligations would pollute the attention view with items nobody can close. | `aw check` detail naming all five rows; stash-and-rerun proving the finding pre-existing; the rule's own `required` text accepting `Carrier-Declined` as a valid disposition; `y43g6q` existing and non-terminal for the one row with real outstanding work. | yes |
