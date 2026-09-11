# Review: widen the pre-merge dirty check to every path the merge would write, child fujm0y (Set mergedirty)

- Subject-Id: fujm0y
- Subject-Type: ipd
- Reviewed-At: 2026-09-10
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `751904e3`. Structural preflight `aw ipd lint --phase author` CONFORMED with zero findings
before semantic review. At `--phase review-finalize` the linter reports ONE finding, `IPD-Q501`, because this
review ESCALATED a new OQ-02 to `Blocking: yes`; that refusal is the intended gate firing, not an unrepaired
structural defect. No product code was modified by this review.

READINESS IS `no-go` FOR A REASON THAT IS NOT A CRITICISM OF THE PLAN. The plan's own E-01 stop condition is
MET: prerequisite `51vw4y` has not executed, so the correct state is not-yet-runnable. Its declared
`executed:51vw4y` edge already makes the runner mark it `dependency-blocked` and continue, so an unattended
run is safe. What needs a human is the sequencing decision, which OQ-02 now carries.

DISCLOSURE: the plan was authored by the same model family, so this is close to a self-review and is worth
less than an independent one. Its value therefore rests on what was EXECUTED. Things run: the reported defect
REPRODUCED from scratch in a throwaway git repository (base/lane/main-rename, `dirty_tree_overlap` called
against the real function, then a real `git merge --no-ff`); a SECOND fixture built to test the plan's
prescribed algorithm against a main-advanced-and-dirty case, with the real merge run to completion and the
resulting file content inspected; `git merge-tree --write-tree` run on both fixtures and its result tree
diffed against HEAD; `dirty_tree_overlap` and `integrate_lane_branch` located by symbol across the package
and all definitions read; both drivers' `integration-blocked` classification read; both prerequisite plans'
statuses read; `runner_shared.py` grepped for destructive git recovery verbs; `2c122z`'s directory checked;
backlog `h1ksy6`'s front matter read; the release record resolved; `git --version` taken; the package grepped
for existing `merge-tree` use; and the bare suite plus the failing module in isolation.

THE DEFECT IS REAL AND I REPRODUCED IT RATHER THAN TRUSTING THE PLAN. With base `a.txt`, a lane changing
`a.txt`, and main having renamed `a.txt` to `renamed.txt` and left it dirty, `dirty_tree_overlap(repo,
['a.txt'])` returned `[]`, so the guard reports clear; `git merge --no-ff` then failed with "Your local
changes to the following files would be overwritten by merge: renamed.txt", exit 2. The call site is
confirmed at `runner_shared.py:1003` passing `lane.changed_files`. F-1 holds exactly as written.

THE FINDING THAT RESHAPES THE PLAN IS THAT ITS PRESCRIBED ALGORITHM CAUSES THE REGRESSION ITS OWN V-03
FORBIDS. E-02 specified "the union of paths differing between the merge base and BOTH tips". I built the case
that distinguishes it: base has `a.txt` and `b.txt`; the lane changes only `a.txt`; main ADVANCES `b.txt` with
a commit and is left DIRTY on `b.txt`. The union is `['a.txt','b.txt']`, so the widened guard returns
`['b.txt']` and REFUSES. But the real `git merge --no-ff` exits 0 ("Merge made by the 'ort' strategy",
changing only `a.txt`) and the co-worker's dirty `b.txt` survives byte-intact. So the union refuses a
previously-integrating case, which V-03 defines as a FAILED validation. The plan would have failed its own
acceptance bar at execution time, and the executor would have faced an unresolvable conflict between E-02's
instruction and E-03's prohibition.

THE CORRECTED ALGORITHM IS MEASURED, NOT PROPOSED. `git merge-tree --write-tree HEAD <lane>` produces the
merge result tree; diffing that tree against HEAD gives exactly the paths the merge would write. Measured:
`['renamed.txt']` on the rename fixture, where the real merge does fail, and `[]` on the union-disproof
fixture, where the real merge does succeed. That is precisely the discrimination this plan needs and the union
cannot make. E-02 now prescribes it, and V-02/V-03 require the disproving fixture as evidence that the
corrected algorithm was implemented rather than the original one. Two consequences are handled explicitly: a
conflicting `merge-tree` exits non-zero and must not be turned into a fabricated empty path set, and
`--write-tree` requires git >= 2.38 (2.43.0 here), which is a reportable constraint rather than a licence to
fall back to the disproved union.

THE TWO PREREQUISITES WERE VERIFIED AND THEY DIVERGE. `6sb3yu` HAS landed, so F-2's concern is resolved:
`dirty_tree_overlap` has exactly one definition at `runner_shared.py:888` and E-01's two-copy stop will not
fire. `51vw4y` has NOT: it is `reviewed` and still in `pending/`, and `integration-blocked` is terminal in both
drivers, the only `integration_deferred` occurrences being an attempt-record field holding a reason string
rather than a non-terminal status. So the plan's F-3 sequencing argument is not merely prudent, it is live.

A TRIPWIRE IN E-01 WOULD HAVE STOPPED A LEGITIMATE RUN. `grep "def integrate_lane_branch"` returns THREE
hits. Read in full, the two driver hits are thin wrappers that delegate to the shared implementation, binding
only `host_label` and `run_checked`, and both docstrings cite `6sb3yu`. An executor applying E-01's
"more than one means stop and report" to that symbol would have refused to proceed on a correctly extracted
tree. The stop rule now keys on `dirty_tree_overlap` definitions only, and the wrapper shape is described.

WHAT I VERIFIED SOUND AND LEFT ALONE, because the plan's honesty here is better than most. F-4's severity
claim holds: `runner_shared.py` contains no `reset`, `checkout -f`, `stash`, or `clean` on the integration
path, so today's cost really is a worse message rather than lost work, and the plan is right to refuse to call
it a data-safety bug. F-5 holds (`2c122z` is in `superseded/`). F-6's rename endpoint handling is present and
was load-bearing in the reproduction. OQ-01's refusal to reclassify conflict-resolution paths is correct and
now rests on a more precise premise. And the insistence that tests drive REAL git rather than a hand-built
path list is vindicated by this review's own method: a mocked path set would have hidden both the defect and
the union's flaw.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A. Correctness and data integrity / D. Anti-regression | `runner_shared.py:1003`; both fixtures built and merged at review | E-02's PRESCRIBED ALGORITHM CAUSES THE REGRESSION V-03 FORBIDS. The merge-base-to-both-tips union returns `['b.txt']` and refuses when base has `a.txt`+`b.txt`, the lane changes `a.txt`, and main advances AND dirties `b.txt`; the real merge exits 0 and preserves the dirt. The plan would fail its own acceptance bar, leaving the executor with contradictory instructions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 rewritten to use `git merge-tree --write-tree` diffed against HEAD, with the measured counterexample and the reason the union is wrong; conflict-exit handling and the git floor added; E-03/V-02/V-03 now require the disproving fixture as mandatory evidence; Scope and Proposed changes updated; new F-7. |
| PR-002 | HIGH | IN-SCOPE | C. Architecture and operability / G. Plan executability | `51vw4y` front matter; `oc_runipd.py:6754-6767`; `agy_runipd.py:3813` | THE PLAN'S OWN STOP CONDITION IS MET AND NOTHING SURFACED IT AS A DECISION. `51vw4y` is `reviewed` in `pending/`, and `integration-blocked` is still terminal, so E-01 must stop today. The runner handles this safely via the declared edge, but whether to approve the prerequisite (also a `Blocks-Release: next` gate) so this high-priority release blocker can ever run is a maintainer choice that was nowhere raised. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | OPEN | New OQ-02 escalated to `Blocking: yes` carrying `- Finding: PR-002`, with three named choices and a recommendation against dropping the edge; E-01, conventions, findings (F-8) and the gate all state the observed prerequisite states. |
| PR-003 | MEDIUM | IN-SCOPE | G. Plan executability | all three `integrate_lane_branch` definitions read | E-01's STOP RULE WOULD MISFIRE ON A CORRECTLY EXTRACTED TREE. `integrate_lane_branch` has three definitions, two of which are thin delegating wrappers; an executor applying "more than one means stop" to that symbol would refuse to proceed after `6sb3yu` succeeded. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 now states the post-extraction shape explicitly, describes the wrappers, and scopes the stop rule to `dirty_tree_overlap` DEFINITIONS; V-01 requires pasting the wrapper bodies; new F-9. |
| PR-004 | MEDIUM | UNDER-SCOPE | G. Plan executability | `h1ksy6` front matter; `releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` | THE PLAN INHERITED THE RELEASE GATE BUT NOT THE PRIORITY. Source item `h1ksy6` is `Priority: high`, `Work-Kind: bug`; the plan carried `Blocks-Release: next` (resolving to the single `planned` release `f33nrj` / 2.0.0) while omitting both other fields, understating a high-priority release-blocking bug. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Priority: high` and `- Work-Kind: bug` added to front matter; the completion note records their provenance; new F-10. |
| PR-005 | MEDIUM | OVER-SCOPE | G. Plan executability | `Scope-Paths`; `runner_shared.py:888`,`:1003`; `lane_containment.evaluate_clean_base` | A DECLARED SCOPE PATH HAS NO IDENTIFIED CHANGE. `lane_containment.py` is declared, but the guard and its call site both live in `runner_shared.py`, and `lane_containment.evaluate_clean_base` is a different base-cleanliness check this plan does not touch. `aw ipd finalize` refuses to complete without a `--scope-ack` per declared-but-unmodified path, so this would surface as a finalize obstacle. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | A Scope-Paths justification was added naming what each path is for, stating that no change to `lane_containment.py` was identified, and requiring the executor to justify the edit or drop the path; the not-declared drivers are explained too. |
| PR-006 | LOW | UNDER-SCOPE | F. KISS, principles, and UX | `runner_shared.py:888` docstring | A DOCSTRING BECOMES FALSE WHEN THIS PLAN LANDS. `dirty_tree_overlap`'s docstring says it reports paths overlapping "an incoming lane's `changed_files`", which is exactly the defect being fixed; unchanged, it would strand a description of the bug on the fixed function. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync now requires updating that docstring in the same change AND recording why the input is the merge-result diff rather than a union, so a later reader does not "simplify" it back. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | E-02's union algorithm is wrong. Rewrite it in place, or mark the plan REPLAN? | Rewrite E-02 in place with the measured correct algorithm. | REPLAN (rejected: the plan's problem statement, sequencing, anti-regression discipline and test strategy are all sound and independently verified; only the path-set computation was wrong, which is a bounded edit); leave E-02 and let the executor discover the contradiction (rejected: E-02 and E-03 would be mutually unsatisfiable, and the executor would have no authority to choose). | Both fixtures measured at review, including the real merge outcomes and surviving file content; `git merge-tree --write-tree` measured to give the exact write set on both. | yes |
| D-2 | The ladder prerequisite is unmet. Resolve it myself or escalate to the maintainer? | Escalate as a new `Blocking: yes` OQ-02 with three named choices. | Resolve as "wait for `51vw4y`" on my own authority (rejected: both plans are `Blocks-Release: next` gates on the same release and this one is `Priority: high`, so the sequencing affects what ships and is the maintainer's call); resolve as "drop the edge and run alone" (rejected outright: it would make transient dirt permanently fatal more often, the exact harm `5wdoze:113` warns of); leave it unraised (rejected: it is the reason the plan cannot run, and silence would leave a high-priority release blocker permanently `dependency-blocked`). | `51vw4y` `Status: reviewed` in `pending/`; `integration-blocked` terminal at `oc_runipd.py:6754-6767` and `agy_runipd.py:3813`; `h1ksy6` `Priority: high`; release `f33nrj` is the sole `planned` release. | yes |
| D-3 | Does the `integrate_lane_branch` three-definition grep mean `6sb3yu` did not fully land? | No: two are delegating wrappers, so the tree is in the correct post-extraction shape. | Treat it as surviving duplication and flag the dependency as unhonored (rejected: I read all three bodies; the driver ones call `runner_shared.integrate_lane_branch` and bind only `host_label`/`run_checked`, and both docstrings cite `6sb3yu`); ignore the ambiguity (rejected: E-01's stop rule would misfire on it, which is PR-003). | All three definitions read at review; `6sb3yu` `Status: executed`; `dirty_tree_overlap` single definition at `runner_shared.py:888`. | yes |
