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

## Round 2

Reviewed at HEAD `9272e7ee`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review; it conforms again after this round's E-11/V-11 additions, and at
`--phase review-finalize` reports exactly one finding, `IPD-Q501` for the blocking OQ-04 raised here,
which is the escalation gate working as designed.

DISCLOSURE: same repository and same model family as the author, so this is close to a self-review and
worth less than an independent one. Its value rests on what was DRIVEN. Measured this round: every
enclosing `if` chain re-derived by AST at current HEAD rather than trusted from round 1; every
`teardown_isolation_worktree` call site in both runners enumerated with its full nesting; E-03's
prescribed signature change ACTUALLY MADE against `oc_runipd.py` and the suite run to see what breaks
(then restored, and re-run green); the one-lane sweep design built by hand in scratch repos through
three merges plus a peer commit plus a lane-versus-main divergence; `reconcile_disposition`'s call sites
enumerated against the integration block's AST span; the package grepped for any lane-refresh mechanism;
and `state['runbook']` traced to confirm the seventh guard is reachable for a review at all.

ROUND 1's PREMISE AND ITS CENSUS HOLD, AND I RE-VERIFIED THEM RATHER THAN INHERITING THEM. F-1 is real
(`a9510164` holds exactly the plan edit plus the review record). F-9 is real and is the strongest fact in
the plan (`59cdc718` holds five files: `8lfoum`'s plan and record plus three sibling child plans, and I
confirmed one of those siblings is `u23gbn`, which I reviewed separately in this same session, so the
collision is not hypothetical). F-7's allocation nesting is exact at current HEAD (`if self_finalize and
not is_review:` spans `:6151-6264` and contains `allocate_isolation_worktree` at `:6198` via `if
isolate:` at `:6196-6264`), and the agy twin holds. The seven-site census is right, including `:5467`,
which I confirmed is genuinely reachable for a review because `state["runbook"]` is ALWAYS set
(`:2993`, synthesized at `:2904-2906` when not supplied). F-4's incident comment is verbatim at
`:6275-6279`. Round 1's corrected `runner_shared.py:1036-1064` citation is right.

THE FINDING THAT MOST CHANGES THE WORK IS F-12, AND IT CORRECTS ROUND 1 RATHER THAN THE AUTHOR. Round 1
said `:6665` "gates the worktree TEARDOWN at `:6825`", which implies that splitting `:6665` hands a
review a teardown. It does not. `teardown_isolation_worktree` has EXACTLY ONE call site in each runner
(`oc:6825`, `agy:3870`), and its enclosing chain is `integration_gate_relevant and integration.earned`
-> `fin_rc == 0` -> `not integrated` -> else -> `elif wt_handle is not None`. The load-bearing gate is
`fin_rc == 0`, and `fin_rc` is `driver_finalize`'s return code, which a review MUST NEVER produce. So no
split of `:6665` at any depth reaches it: a review lane has NO teardown path whatsoever. Round 1's
conclusion ("every review lane LEAKS a worktree") was right for the wrong reason, and the wrong reason
matters, because an executor who split `:6665` expecting a teardown would ship the leak believing it
fixed. New E-11 owns building one, and it must respect that function's own docstring rule that it is
DESTRUCTIVE and "must only ever be called on a lane that holds NO work".

THE FINDING I FOUND BY DOING RATHER THAN READING IS F-13. E-03 prescribes an explicit no-default action
kind, "PREFER NO DEFAULT ... following the precedent set by `host_label`". I added `*, action_kind: str`
to `oc_runipd.integrate_lane_branch` and ran the suite:
`tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_each_wrapper_keeps_the_ORIGINAL_signature`
FAILED with `AssertionError: Lists differ: ['action_kind'] != []`. Its docstring is "No call site may
have had to change, so no wrapper may expose the injected parameter", and it asserts the kwonly list is
EMPTY (`:800-802`). So the plan's own recommended shape breaks a shipped contract, and the plan's census
of nine call sites omits three AST-level structural tests keyed on this function (`:787`, `:836`,
`:851`). I restored the file and re-ran the test green; NO product code was left changed by this review.
E-03 now names two explicit routes and recommends the one that leaves `:787` untouched (bind the literal
inside each wrapper, exactly as `host_label` already is).

THE FINDING THAT REVISITS A MAINTAINER RULING IS F-14, WHICH IS WHY IT IS ESCALATED AND NOT DECIDED.
OQ-02 was resolved to ONE lane for the whole sweep. That lane is allocated once and cut at `HEAD`
(`worktree_lease.py:554`), every review merges to main and advances it, and NOTHING refreshes the lane;
I grepped the whole package for any rebase or refresh helper and found none. Built by hand: after two
reviews merged, the lane still read `peer v1` while main read `peer v2`; a plan a peer corrected ON MAIN
mid-sweep read its PRE-correction text inside the lane. So the "full checkout" OQ-02 credits for
preserving cross-plan awareness is a snapshot frozen at sweep start, and that awareness degrades
monotonically. This Set is the instance: under a sweep lane, the review of sibling N reads sibling texts
as they were before reviews 1..N-1 merged, missing exactly the corrections F-9 credits. I want to be
precise about severity: nothing is silently corrupted. A lane-versus-main divergence produced
`CONFLICT (content)` and the shared function aborts, and I verified main was left clean with the peer's
bytes intact. The cost is a STRANDED REVIEW whose likelihood grows with every item, not a lost edit.
OQ-02's other reason (reviews touch disjoint paths) is TRUE and survives untouched, because the collision
is lane-versus-MAIN rather than review-versus-review.

ONE FALSE CHOICE REMOVED (F-15). E-09 told the executor the disposition could be computed before
integration (read the lane) or after (read main), and to "pick one deliberately". There is nothing to
pick: `reconcile_disposition`'s only three call sites are `:6381`, `:6409` and `:6560`, all before the
integration block at `:6707-6886`, and there is no call after it. The lane read is the only reachable
implementation. A plan that offers a choice between a real branch and an impossible one costs the
executor real time discovering which is which.

WHAT I DELIBERATELY DID NOT CHANGE. E-04's handling of the session question is correct as written: it
says "verify, do not assume", and I confirmed why that caution is warranted rather than resolving it,
because `isolated_turn = bool(work_dir)` (`:5395`) keys the fresh-session decision on WHETHER a work_dir
exists and not on whether the tree changed, so one sweep lane does NOT by itself restore sharing;
OQ-03's claim that both CLI promises "remain TRUE" depends on code that must still be taught the
difference. That is E-04's stated job and I left it as the plan's work rather than pre-empting it. I also
left E-10 alone: it is the right response to F-9/F-10 and its two shapes are honestly costed. And I did
not touch the `:6572` leave-alone row, which remains correct.

No product code was modified by this review. The one patch made to measure F-13 was reverted and the
affected test re-run green.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-511 | BLOCKER | UNDER-SCOPE | A (correctness), C (operability), G | AST: sole `teardown_isolation_worktree(` call at `oc_runipd.py:6825` / `agy_runipd.py:3870`, chain `:6707-6886` -> `fin_rc == 0` `:6730-6886` -> `not integrated` `:6746-6864` -> else -> `:6823-6826`; `fin_rc` from `driver_finalize` `:6727`; destructive-call rule `runner_shared.py:850-858` | A REVIEW LANE HAS NO REACHABLE TEARDOWN, AND ROUND 1's ACCOUNT OF WHY WAS WRONG. Round 1 said splitting `:6665` supplies one; the sole call site is gated on `fin_rc == 0`, i.e. `driver_finalize`'s return code, which a review must never produce. So the leak is not a mis-split but the total absence of a path, and an executor who split `:6665` expecting a teardown would ship the leak believing it fixed. No item owned building one. | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | E-01's `:6665` row corrected to claim only the merge-back, with the teardown situation stated. New E-11 (coordinator-owned, once per sweep, classify-before-destroy per the docstring, plus the interrupt case) and new V-11 (worktree list AND branch list after a completed sweep; the PRESERVED case for a stranded review). Required tests and Scope check updated. New F-12. |
| PR-512 | HIGH | IN-SCOPE | E (testing), G (executability) | measured: patched `oc_runipd.py:1967-1969` with `*, action_kind: str`, ran `-k ORIGINAL_signature` -> FAILED `Lists differ: ['action_kind'] != []`; restored -> passed. Test at `tests/test_runner_shared.py:787`, assertions `:800-802`; siblings `:836`, `:851` | E-03's RECOMMENDED SIGNATURE SHAPE BREAKS A SHIPPED CONTRACT TEST THE PLAN NEVER MENTIONS. `test_each_wrapper_keeps_the_ORIGINAL_signature` asserts each host wrapper's positional args are exactly the original four and its kwonly list is EMPTY, with the docstring "no wrapper may expose the injected parameter". The plan's nine-call-site census also omits three AST structural tests keyed on this function's shape. An executor following E-03 literally hits a red suite and must then decide, under time pressure, whether to amend a contract test. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New E-03 bullet with the measurement, naming two explicit routes: (a) put the parameter only on the shared function and bind a literal in each wrapper, as `host_label` already is, leaving `:787` untouched (RECOMMENDED); or (b) change the wrapper and amend `:787` with justification. Required tests now demands those three AST tests be run and pasted. Scope check records which route leaves `tests/test_runner_shared.py` unmodified and therefore needing a `--scope-ack`. New F-13. |
| PR-513 | BLOCKER | IN-SCOPE | A (correctness), C (architecture), D | `worktree_lease.py:554` (`base_commit="HEAD"`); `runner_shared.py:833-847`; no `rebase`/refresh helper anywhere in the package (grepped); measured in scratch repos: lane `peer v1` vs main `peer v2` after two merges; peer's mid-sweep correction invisible in lane; divergence -> `CONFLICT (content)`, abort, main clean | THE ONE-LANE SWEEP GOES STALE MONOTONICALLY, CONTRADICTING ONE OF OQ-02's TWO DECIDING REASONS. The lane is cut once at sweep start; every review merges and advances main; nothing refreshes the lane and no mechanism exists to. OQ-02 chose one lane partly because it "gives the reviewing agent a full checkout, so cross-plan awareness ... is preserved rather than fragmented", but that checkout is frozen at sweep start, so the awareness degrades with every merge. In a nine-item sweep review 9 reads a tree eight merges behind. This Set is the instance: sibling N's review would miss the corrections reviews 1..N-1 made. NOT data loss (divergence conflicts and aborts leaving main clean, verified); the cost is a stranded review whose likelihood grows per item. | C:Medium; U:Low; S:Low; F:High; Overall:Medium-High | OPEN | Escalated as blocking OQ-04 with three costed options (refresh the lane between reviews; re-allocate per review, reopening the session question; or accept and BOUND the staleness), a recommendation, and the explicit note that it revisits a maintainer ruling. E-02 gains the measurement and the requirement to implement whichever policy is chosen; E-02 and E-11 are gated on it. Proposed-changes and gate paragraphs updated. New F-14. |
| PR-514 | MEDIUM | IN-SCOPE | G (executability) | `reconcile_disposition(` call sites `oc_runipd.py:6381`, `:6409`, `:6560`; integration block AST span `:6707-6886`; no call after `:6707` | E-09 OFFERED A CHOICE BETWEEN A REAL BRANCH AND AN IMPOSSIBLE ONE. It said the disposition may be computed before integration (read the lane) or after (read main), and told the executor to "pick one deliberately". The ordering is fixed: all three call sites precede the integration block and none follows it, so the lane read is the only reachable implementation. The choice costs the executor time discovering it is not a choice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09's ordering bullet replaced with the measurement and an instruction to implement the lane read and delete the choice. New F-15. |
| PR-515 | MEDIUM | IN-SCOPE | G (honest documentation) | round 1's cost statement vs this round's F-12/F-13/F-14 | THE COST OQ-03's FIRST HALF IS BEING DECIDED AGAINST IS NOW UNDERSTATED. OQ-03 asks whether the change is worth its true cost, and round 1 raised the estimate to seven sites per host with two surgical splits plus three behavioral sites plus a nine-call-site signature change. Round 2 adds a teardown that must be built and must classify before destroying, a prescribed signature change that breaks a shipped contract, and a lane-refresh mechanism that does not exist. A maintainer re-reading OQ-03 would otherwise weigh the old number. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | A paragraph added under Proposed changes stating the round-2 additions explicitly and directing that OQ-03's first half be re-decided against this cost rather than round 1's. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-3 | The sweep lane goes stale as it merges (F-14). Should review pick the freshness policy? | No. Escalate as blocking OQ-04 with three costed options and a recommendation. | Pick option (a), refresh the lane, since it is the only option preserving OQ-02's stated reason; or treat the staleness as an implementation detail for the executor. | The question revisits OQ-02, a decision the maintainer already made, on the strength of a measurement that ruling did not have; and the three options trade build cost against a failure rate the repository cannot rank. AGENTS.md reserves scope and risk-appetite calls to the maintainer, and re-deciding a ruling on the reviewer's own authority is exactly the case it names. | no |
| D-4 | Round 1 stated `:6665` gates the teardown; AST shows the sole teardown is gated on `driver_finalize`'s return code. Correct round 1 in place, or note the discrepancy? | Correct it in place, in both the E-01 row and a new finding, and add the missing E-item. | Leave round 1's text and add only a caveat, since its CONCLUSION (leaked worktree) was right. | A right conclusion reached by a wrong mechanism is worse than a wrong conclusion here: an executor who splits `:6665` expecting a teardown ships the leak believing it fixed. The mechanism is what the executor acts on, so it is the part that must be true. | yes |
| D-5 | E-03's prescribed no-default parameter breaks `tests/test_runner_shared.py:787`. Choose the route, or present both? | Present both with the measurement, and RECOMMEND route (a) without mandating it. | Choose (a) outright, since it satisfies every constraint; or choose (b) and amend the test. | Route (a) appears strictly better but has a consequence I could not fully verify without writing the code: the wrapper can no longer distinguish actions, so the review path must call the shared function directly or gain a second wrapper, which is a structural choice the implementer is better placed to make. Recommending rather than mandating leaves that judgement where the evidence is. | yes |
| D-6 | E-04's session question: resolve it, or leave it as the plan's work? | Leave it, adding only the confirmation that the caution is warranted. | Resolve it by declaring that OQ-03's "both promises remain TRUE" claim is wrong, since `isolated_turn = bool(work_dir)` disables sharing regardless of tree identity. | E-04 already says "verify, do not assume" and names both routes, so the plan handles it correctly; the code fact I measured (`:5395`, `:5405`) is exactly what E-04 tells the executor to confront. Pre-empting it would replace a correct instruction with my own guess about which route the implementer should take. | yes |

D-3 is `Reversible: no` and is ESCALATED as the workflow requires: raised in the reviewed plan as OQ-04
carrying `- Blocking: yes` and `- Finding: PR-513`, so `aw ipd lint` refuses the plan at every checkpoint
until the maintainer answers (verified: `IPD-Q501` at both `--phase author` and `--phase
review-finalize`). It is deliberately a SECOND blocking question rather than folded into OQ-03, because
OQ-03 asks whether to proceed at all while OQ-04 asks which shape to proceed in, and the maintainer may
well answer the first yes and the second differently from the plan's current design.

## Round 3

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round exists to record that round 2's gating finding
was resolved by the maintainer's own decision, taken on 2026-09-13 through the `askme` workflow, one
interactive prompt at a time. Nothing in the plan was re-reviewed here and no new finding was sought;
appending a round is the mechanism `plan-review.md:187` prescribes for this, since the gate reads only
the current round. The earlier rounds are left exactly as written.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-513 | BLOCKER | IN-SCOPE | G (executability) | the resolved `OQ-04` in this plan's `## Open questions` | The single sweep lane went stale as each review merged, so late reviews read an out-of-date tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The maintainer ruled REFRESH: fast-forward the sweep lane to main after each review lands. Measured both halves, an unrefreshed lane read the first version of a file while main held the third, and one `git merge --ff-only` inside the lane fixed it. Sharing is retained; only the freshness defect is fixed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's answer to OQ-04 discharge PR-513, or does the finding need a fresh review pass? | It discharges it; record the discharge and leave the earlier rounds untouched. | Run a further full review round on this plan. | The finding's own recorded remedy was a human decision, and that decision is now recorded in the owning plan with its reasoning. A further round was priced on evidence and rejected: the round earlier the same day cost 3h 02m and $106.07 across nine items and raised four NEW blocking questions, so it was not expected to yield a clean sheet. | yes |

HONEST LIMIT: the discharge rests on the maintainer's decision, not on an independent reviewer's
re-examination. If a later reader needs assurance that this plan's content was checked afresh, that
assurance is in rounds 1 and 2 and not here.
