# Review: isolate a review turn in a worktree too so no turn writes to the shared checkout, child ajxr5d (Set dirtygates)

- Subject-Id: ajxr5d
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

Reviewed at HEAD `4e2d208b`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review. At `--phase review-finalize` the linter reports exactly one finding,
`IPD-Q501` for the blocking OQ-03 this review raised, which is the gate working as designed and matches
the disposition Orders 01, 02 and 04 carry.

DISCLOSURE: same repository and same model family as the author, so this is close to a self-review and
worth less than an independent one. Its value therefore rests on METHOD rather than on re-reading. The
method that produced every material finding here was to AST-walk the enclosing `if` chain of each call
site the plan depends on, instead of reading the guard conditions the plan lists. That distinction is
the whole review: the plan's guard list is accurate, and its INTERPRETATION of two entries is backwards,
which reading conditions alone cannot reveal.

THE PLAN'S PREMISE IS CORRECT AND WAS CONFIRMED INDEPENDENTLY. F-1 verified: `a9510164` is a real
`plan-review: harden stalecrit-01 tgop8e` commit on main carrying exactly the plan edit plus the review
record, so a review demonstrably writes to the shared checkout. F-2's six oc guards all verified at their
cited lines, and their six agy twins verified as positionally exact. F-3's argument that reviews escaped
the outage by exemption rather than by safety holds. So the plan is aimed at a real defect.

THE FINDING THAT STOPS IT IS THAT THE PLAN'S OWN MITIGATION IS THE PART THAT IS WRONG. E-01 exists to
classify the guards before touching them, and its classification gets the two most important entries
backwards, in the direction that silently disables the work. `:6151` is marked LIFECYCLE / leave-alone,
but AST-verified it spans `:6151-6264` and CONTAINS `allocate_isolation_worktree` at `:6198`, so leaving
it means a review turn never gets a lane and E-02 is inert. `:6665` is marked leave-alone too, but its
block spans `:6707-6886` and contains BOTH the `integrate_lane_branch` call at `:6740` and
`teardown_isolation_worktree` at `:6825`, so E-03 has no reachable call site and, if a lane were
allocated anyway, every review would leak a worktree. The same nesting was verified on agy. An executor
following the plan literally would therefore produce either nothing or a lane leak, while believing the
classification step had protected them. Both sites need surgical SPLITTING, because genuine lifecycle
calls live in the same blocks and must stay review-exempt: deleting `not is_review` wholesale would make
a review call `driver_begin` and claim execution authority it must never have.

THREE FURTHER SITES THE CENSUS MISSED, each measured. `:5467` is a seventh `not is_review` guard,
governing `--file` attachment localization, whose own comment records a measured case where the
attachments named MAIN while the prompt text named the lane, i.e. exactly half of the F-4 incident the
plan cites; fixing only the prompt reproduces the other half. `:6519` excludes lane-submission
collection, which `collect_lane_submissions`' docstring calls the mandatory other half of a
lane-relative prompt under spec R2.1 and warns "fails INVISIBLY" without it. And
`reconcile_disposition`'s review branch resolves the plan against MAIN and scores the turn from its
`- Status:`, so once the review lands on a lane MAIN still reads `to-review`, the comparison always
misses, and a review that set `approved` is recorded merely `reviewed`. That last one is the subtlest of
the three because it changes how a review is SCORED, not merely where it is written, and nothing in the
plan mentions it.

F-5'S SESSION PROBLEM IS A CONTRADICTION, NOT AN INTERACTION. The plan asks E-04 to "preserve the shared
session" and to "record the reason isolation does not break it", which presumes a reconciliation exists.
The code's own recorded reasoning says otherwise and is categorical: an opencode session carries its own
directory binding that OVERRIDES `--dir`, per-set sessions paired with per-item worktrees lost four
consecutive lanes (`lanesess xd9sll`), and therefore "an isolated turn is ALWAYS a fresh session". Since
OQ-02 resolves to per-review lanes, sharing and isolation cannot both survive. One must yield, and
because the CLI help promises continuity in two places, withdrawing it is a user-facing contract change.
Escalated rather than chosen.

WHAT REVIEW DID NOT WEAKEN. OQ-01's answer and its anti-forged-attestation line are exactly right and
were strengthened into V-03 rather than diluted: skipping revalidation for an action with nothing to
revalidate is simply true, and passing a synthetic pass value would be a forgery of the same family as a
hand-written `- Readiness:`. The one genuinely lifecycle site the plan identified correctly (`:6572`)
stays leave-alone. F-6's honesty about the smaller reward was preserved and sharpened rather than
removed, because it is now the strongest input to the deferral question.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-501 | BLOCKER | IN-SCOPE | G (executability), C | AST: `oc_runipd.py` `if self_finalize and not is_review:` spans `:6151-6264` containing `allocate_isolation_worktree` at `:6198`; `if integration_gate_relevant and integration.earned:` spans `:6707-6886` containing `integrate_lane_branch` at `:6740` and `teardown_isolation_worktree` at `:6825`; agy twin `:3291-3401` containing `:3326` | E-01'S CLASSIFICATION IS BACKWARDS ON THE TWO DECISIVE SITES. Both are marked lifecycle/leave-alone, but one contains the worktree allocation (so E-02 cannot function) and the other contains both the merge-back and the teardown (so E-03 has no call site and reviews leak worktrees). The plan's own protective step is thus the source of the error, and an executor trusting it ships something inert or leaky. | C:High; U:Low; S:Medium; F:High; Overall:High | OPEN | E-01 rewritten with a corrected, contents-derived table naming both as tree-critical SPLITS and stating what must stay exempt; classification method changed to an enclosing-block walk; E-02/E-03 annotated with their dependency on the splits; new F-7. Escalated into blocking OQ-03 together with PR-505, since the combined cost is what the maintainer must weigh. |
| PR-502 | HIGH | UNDER-SCOPE | A (correctness), E | `oc_runipd.py:5992-6003`; the existing lane-reading precedent at `:6577` | THE REVIEW DISPOSITION READS THE WRONG TREE AFTER ISOLATION. `reconcile_disposition`'s review branch resolves the plan against `repo` (MAIN) and derives the disposition from its `- Status:`. With the revision on a lane, MAIN still reads `to-review`, so the status comparison always misses: an `approved`-setting review is recorded merely `reviewed`, and the check stops discriminating. Unmentioned in the plan. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | New E-09 reads the plan from the lane when isolated, reusing the `:6577` precedent, and requires the executor to state which side of integration the disposition is computed on. New V-09 demands the pre-change failure be exhibited. New F-8. |
| PR-503 | HIGH | UNDER-SCOPE | A, E | `oc_runipd.py:6519`; `lane_containment.collect_lane_submissions` docstring (spec R2.1, "fails INVISIBLY") | LANE-SUBMISSION COLLECTION IS EXCLUDED FOR REVIEWS AND THE PLAN NEVER ADDRESSES IT. The collector's own contract says it must ship with any lane-relative prompt, because otherwise the driver reads an empty outcome path and scores from the fallback. E-02 makes the review prompt lane-relative, so shipping without this is the split that spec forbids. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | New E-08, deliberately two-sided: either collect, or prove with evidence that a review writes no lane-side submission and record that. V-08 forbids a bare assertion either way because the failure is invisible by construction. |
| PR-504 | MEDIUM | UNDER-SCOPE | A, E | `oc_runipd.py:5467` and the measured correction recorded in its own comment | THE CENSUS OF SIX IS SEVEN. `:5467` gates `--file` attachment localization and is unambiguously tree-related; its comment records a measured defect in which the prompt text named the lane while the attachments still named MAIN. Fixing only the prompt reproduces half of the very F-4 incident the plan cites as its motivation. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added as a row to E-01's corrected table and as an explicit sub-bullet of E-02; V-02 now requires the constructed argv be pasted, not only the prompt. |
| PR-505 | HIGH | IN-SCOPE | C (architecture), F (UX) | `oc_runipd.py:5405` with incident detail at `:5383-5390`; promises at `:7699` and `:7728` | E-04 PRESUMES A RECONCILIATION THAT THE CODE SAYS DOES NOT EXIST. It asks to preserve the shared session and record why isolation does not break it, but the recorded reasoning is categorical: a session carries its own directory binding that overrides `--dir`, per-set sessions with per-item worktrees lost four consecutive lanes, so an isolated turn is ALWAYS fresh. With OQ-02 resolving to per-review lanes, sharing and isolation are mutually exclusive and a documented promise must be withdrawn or the plan narrowed. | C:Medium; U:Medium-High; S:Low; F:Medium; Overall:Medium-High | OPEN | E-04 rewritten as a resolve-the-contradiction item with both branches spelled out and a prohibition on re-binding a session across trees; V-04 forbids pasting a shared id across separate lanes as success. Escalated as the second half of blocking OQ-03, since withdrawing a documented feature is the maintainer's call. New F-5 strengthened. |
| PR-506 | HIGH | UNDER-SCOPE | G (plan executability) | `Scope-Paths` as authored vs E-03; callers at `oc_runipd.py:1978`, `:6740`, `agy_runipd.py:1322`, `:3789`, `tests/test_runner_shared.py:1685`, `:1715`, `:1775`, `tests/test_oc_runipd.py:3251`, `tests/test_agy_runipd_cli.py:756`; range cited as `:1035-1063` vs actual `:1036-1064` | E-03 CHANGES A SHARED FUNCTION NOT IN SCOPE. `runner_shared.py` and `tests/test_runner_shared.py` were absent from `Scope-Paths` although E-03 widens `integrate_lane_branch`'s signature and that test file holds three of its nine call sites, so the central edit would have been an undeclared out-of-scope change. The cited line range for the shared merge steps was also off by one. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Both paths added to `Scope-Paths`; citation corrected; E-03 now enumerates all nine call sites and requires NO DEFAULT for the action kind, following the `host_label` precedent in the same function; V-03 requires each call site be shown updated. |
| PR-507 | MEDIUM | IN-SCOPE | A, G | `oc_runipd.py:6926` and `set_plan_approved` at `:735` | E-05 UNDERSTATES ITS OWN PROBLEM AS A STALE READ. The auto-approve branch also WRITES to main via `set_plan_approved`, so after isolation it is a second mid-run write to the shared checkout, i.e. the very class of write this plan exists to remove. Ordering it after integration fixes both; ordering it before fixes neither. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names the write, requires post-integration ordering for both reasons, and preserves the `auto-approved` (never `--by-human`) transition per `set_plan_approved`'s recorded rationale. V-05 requires all three properties. |
| PR-508 | MEDIUM | IN-SCOPE | C, G | `allocate_isolation_worktree(repo, item["id6"])` is per-item; incident `lanesess xd9sll` at `:5383-5390` | OQ-02 WAS LEFT OPEN WHERE THE CODE ANSWERS IT. The existing machinery is per-ITEM by construction, and `xd9sll` was caused precisely by pairing a per-SET resource with per-ITEM worktrees; a one-lane-per-sweep design would re-create that mismatch in mirror image and need a second allocation path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-02 resolved from code to PER-REVIEW, with the reuse-shipped-mechanism reason recorded as stronger than the independence argument, and its coupling to OQ-03's session half stated so the answer can be reopened if sharing wins. |
| PR-509 | LOW | IN-SCOPE | G (honest documentation) | the corrected site census (7 per host, 2 needing splits, 3 further behavioral sites, 9 call sites) against the plan's own F-6 | THE COST-BENEFIT STATEMENT IS NOW MISLEADING THROUGH NO FAULT OF ITS AUTHOR. F-6 honestly says the benefit is uniformity rather than protecting expensive output, but it was written against a three-guard change. The real cost is materially larger, and a maintainer weighing scope against benefit needs the corrected figure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 sharpened with the measured cost and an explicit statement that deferring the plan entirely is a legitimate answer; that statement feeds OQ-03's first half. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-01's classification is wrong on two sites. Should review simply correct the table and let the plan proceed? | No. Correct the table AND escalate, because the correction changes the plan's size and shape enough that the original cost-benefit judgement no longer applies. | Correct the table silently and treat it as an ordinary FIXED finding; or reject the plan outright as REPLAN. | The corrected scope is 7 sites per host with 2 surgical splits, plus 3 unaddressed behavioral sites and a 9-call-site signature change, against a benefit the plan's own F-6 describes as uniformity rather than protecting expensive output. Whether that trade is worth making is a scope and risk-appetite call AGENTS.md reserves to the maintainer, and the splits touch execution-authority code (`driver_begin`) where a wrong cut grants authority that must never be granted. | no |
| D-2 | Shared review session versus per-review isolation: can both be kept? | No. They are mutually exclusive; escalate which one yields rather than choosing. | Keep sharing and abandon isolation for reviews; keep isolation and silently drop sharing; or re-bind one session across successive lanes to have both. | `oc_runipd.py:5405` forces a fresh session for any isolated turn, and `:5383-5390` records why: a session's own directory binding OVERRIDES `--dir`, and per-set sessions with per-item worktrees lost four consecutive lanes (`xd9sll`). The third option is exactly that measured failure. Withdrawing the continuity promised at `:7699` and `:7728` is a user-facing contract change. | no |
| D-3 | Should the disposition and collection gaps (PR-502, PR-503) be folded into this plan or filed separately? | Fold in, as E-09 and E-08. | File as follow-up items and let this plan ship the isolation alone. | Both are DEFECTS THIS PLAN'S OWN CHANGE CREATES rather than pre-existing ones: the disposition only reads the wrong tree once the plan moves to a lane, and the collector's contract (spec R2.1) explicitly forbids shipping a lane-relative prompt without collection. Shipping isolation without them yields a silently mis-scored review, which is worse than today. | yes |
| D-4 | E-03's action kind: give it a default so existing callers need no change, or require it explicitly? | Require it explicitly, no default. | Default it to the execute behavior, which would leave all nine call sites untouched. | `integrate_lane_branch`'s own `host_label` documents having "NO DEFAULT DELIBERATELY" because a default would let a new caller silently get the wrong behavior in a way invisible until audited. An action kind whose wrong value SKIPS REVALIDATION is the same class of value with higher stakes. | yes |
| D-5 | OQ-02 (per-review versus one lane per sweep) was left open as non-blocking. Resolve it? | Yes, from code: per-review. | Leave it open for the maintainer as authored. | `allocate_isolation_worktree` is keyed per item, so per-review reuses shipped mechanism while one-lane-per-sweep needs a new allocation path and re-creates the per-set-resource-with-per-item-tree mismatch that caused `xd9sll`. Recorded reversible because OQ-03's session ruling can reopen it. | yes |
| D-6 | E-06's regression asserts MAIN's status is EMPTY at every boundary while deliberately dirtying an unrelated path. Keep as authored? | No. Assert EQUALITY with the pre-run status. | Keep the emptiness assertion; or drop the dirty-path element of the test. | An empty status in a test that deliberately dirties a tracked path would mean the run DESTROYED the peer's change, which is the opposite of the property this Set exists to protect; the assertion as written would have passed on the harmful behavior. | yes |

D-1 and D-2 are both `Reversible: no` and are ESCALATED as the workflow requires: raised in the reviewed
plan as OQ-03 carrying `- Blocking: yes` and `- Finding: PR-501`, so `aw ipd lint` refuses the plan at
every checkpoint until the maintainer answers (verified: `IPD-Q501` at `--phase review-finalize`). They
are deliberately carried by ONE question because they are one decision in practice: the true cost of the
change and the feature it would cost are what the maintainer must weigh together.
