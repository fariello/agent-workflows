# IPD: Isolate a review turn in a worktree too so no turn writes to the shared checkout

- Date: 2026-09-13
- Kind: child
- Concern: A review turn runs in the SHARED checkout with NO lane, NO scope gate and NO finalize reconciliation, and it both writes to main mid-run AND writes to OTHER QUEUE ITEMS' FILES. Measured live 2026-09-13: reviewing the orchestrator `8lfoum` produced commit `59cdc718` holding five files, three of them sibling child plans (`d7qoxv`, `metc8b`, `u23gbn`) that were still `queued` in the same run, so one item's turn rewrote three other items' pending input before their turns ran. Those five files sat uncommitted for the turn's duration (~36 minutes on the first item), and a concurrent `runanalytics` execute run had its items refused against them. This is not a theoretical concurrency risk; it happened while the maintainer watched.
- Scope: Run the WHOLE REVIEW SWEEP in ONE coordinator-allocated lane so no review writes to the shared checkout, AND constrain a review turn's writes to the plan under review plus its own review record. Both halves are required: a lane alone stops main being dirtied but does not stop a review rewriting three siblings' files and merging them. Excludes per-review lanes (OQ-02, resolved), the lifecycle exclusions a review legitimately keeps, and Orders 01 to 04 and 06.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: dirtygates
- Order: 5
- Highest E allocated: 11
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: ajxr5d
- Approval: 2026-09-14, recorded via aw ipd set: status set to approved
- Priority: high
- Work-Kind: bug

## Workflow history
- 2026-09-14 approved (aw set): status set to approved
- 2026-09-13 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-13: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own earlier review round while a blocking question was open; the maintainer then answered every open question in this plan through the `askme` workflow on 2026-09-13, one interactive prompt at a time, and each answer is recorded in this plan's `## Open questions` with its reasoning. Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round, having read every resolution as it was written. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the round that ran earlier the same day cost 3h 02m and $106.07 across nine items, cleared three plans, and raised four NEW blocking questions on the rest, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-13 reviewed (opencode (its_direct/pt3-claude-opus-5-1m-us)): /plan-review ROUND 2: REVIEWED - OPEN QUESTIONS; readiness NO-GO. PR-511..PR-515; PR-513 OPEN and escalated as blocking OQ-04, the rest FIXED. Round 1's premise and its seven-site census verified independently, but three of its mechanisms were measured unimplementable as written: F-12 a review has NO reachable teardown at all (the sole call site per host is gated on driver_finalize's return code, so round 1's 'split :6665 supplies one' was wrong) -> new E-11; F-13 the prescribed no-default action kind on the per-host wrappers FAILS a shipped contract test whose docstring forbids exactly it (proved by patching, then restored) -> two explicit routes named; F-14 the one-lane sweep design goes stale monotonically and no refresh helper exists anywhere, contradicting one of OQ-02's own two deciding reasons -> escalated as OQ-04. Also F-15: E-09's 'pick one deliberately' was a false choice, the ordering is fixed by the code.
- 2026-09-13 to-review (aw set): status set to to-review

- 2026-09-13 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 1: REVIEWED - OPEN QUESTIONS; readiness NO-GO. PR-501..PR-509; PR-501 OPEN and escalated as blocking OQ-03, the rest FIXED. `aw ipd lint` CONFORMING at `--phase author` before semantic review. DISCLOSURE: same model family as the author, so the value rests on what was DRIVEN, not re-read; every claim was measured at HEAD `4e2d208b`, and the method that produced the findings was AST-walking the enclosing `if` chain of each call site rather than reading the guard list the plan supplies. THE PLAN'S PREMISE IS CORRECT: F-1 verified (`a9510164` is a real plan-review commit on main holding exactly the plan edit plus the review record), F-2's six oc guards and their six agy twins all verified at the cited lines, and F-3's exemption argument holds. THE FINDING THAT STOPS THE PLAN IS THAT E-01'S CLASSIFICATION IS WRONG IN THE DIRECTION THAT BREAKS THE WORK (PR-501, new F-7). E-01 marks `:6151` LIFECYCLE, leave alone. But `allocate_isolation_worktree` at `:6198` is NESTED INSIDE that block (AST: `if self_finalize and not is_review:` spans `:6151-6264`; `if isolate:` spans `:6196-6264`), so with `:6151` left alone a review turn NEVER ALLOCATES A LANE and E-02 cannot work at all. The same nesting holds on agy (`:3291-3401` enclosing the allocation at `:3326`). Worse, the identical error repeats at `:6665`, also marked leave-alone: `integration_gate_relevant` gates the MERGE-BACK at `:6740` AND the worktree TEARDOWN at `:6825`, so E-03 is unimplementable as written and, if E-02 somehow allocated a lane, every review would LEAK a worktree. So the plan's central mitigation (classify before changing) is the very step that is wrong, and an executor following it would produce a plan that either does nothing or leaks lanes. THREE FURTHER STRUCTURAL SITES THE PLAN NEVER MENTIONS, each measured. (1) PR-502: `reconcile_disposition`'s review branch reads the plan from `repo` i.e. MAIN (`:5993-6003`) and derives the disposition from its `- Status:`; with the review landing on a lane, MAIN still says `to-review`, so every isolated review would score `reviewed` by the fallback rather than from evidence, and a FAILED review would be indistinguishable. (2) PR-503: lane-submission collection at `:6519` is `not is_review`, so a review lane's outcome would never be collected, which is the exact invisible-failure mode `collect_lane_submissions`' own docstring says must ship with lane-relative prompts (spec R2.1). (3) PR-504: `:5467` (a seventh `not is_review` site the plan's census of six omits) governs `--file` attachment localization, whose comment records the measured incident where unlocalized attachments named MAIN. F-5'S SESSION CONFLICT IS STRONGER THAN STATED (PR-505): `session = None if (fresh_session or isolated_turn or is_rotation)` is not a coincidence to work around but a DELIBERATE fix for incident `lanesess xd9sll`, whose recorded cause is that an opencode session carries its own directory binding that OVERRIDES `--dir`, so four consecutive lanes were lost; E-04's "preserve the shared session" and E-02's isolation are therefore in DIRECT conflict, and one must yield. That is a behavior-and-promise decision (the CLI help promises sharing at `:7699`), so it is escalated with OQ-03 rather than chosen here. Also fixed: E-03's stated line range for the shared steps was wrong (`:1035-1063` is off by one; the ff-only attempt starts at `:1036` and the function ends `:1064`) and `runner_shared.py` plus its test file were missing from `Scope-Paths` although E-03 changes that function's signature (PR-506); E-05 understates the auto-approve problem, since `set_plan_approved` WRITES to main and would have to run post-merge (PR-507); OQ-02 resolved from evidence to per-review lanes (PR-508); and F-6's honesty about the smaller reward is preserved but sharpened, because the real cost is now six extra call sites per host (PR-509). Verified sound and left alone: the anti-forged-attestation line in OQ-01 (which review endorses and strengthened into V-03), the three genuinely-lifecycle sites `:6572`, and the decision to keep `--no-isolate-worktree` working. Two `Reversible: no` decisions (D-1, D-2) taken and both escalated into OQ-03.
- 2026-09-13 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after the maintainer asked whether reviews should be isolated too. They should: a review commit in main was found in tonight's history (`a9510164`), proving a review is not read-only with respect to the tree.
- 2026-09-13 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Make the answer to "does this turn write to the shared checkout?" the same for every action type: no. A review's two output files should arrive on main as one merge, exactly as an execute turn's commits do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: separate the exclusions that are about the TREE from the ones that are not

- [x] E-01 Classify every `not is_review` guard before changing any of them, and record the classification in this plan. They are NOT one decision, and the classification MUST be derived from the enclosing control flow rather than from the guard's own condition, because review measured that reading the condition alone gets two of them backwards (F-7). The mechanical method that produced the corrected table: for each site, walk the enclosing `if` chain (an AST walk, or read outward to column zero) and list what the block CONTAINS, not what its test says.
  - THE CENSUS IS SEVEN SITES ON EACH HOST, NOT SIX. The plan's original list omitted `oc_runipd.py:5467`, which governs `--file` attachment localization inside `run_opencode` (PR-504). Its own comment records a measured defect in which unlocalized attachments named MAIN while the prompt text named the lane, so it is unambiguously TREE-related and in scope.
  - THE CORRECTED CLASSIFICATION, which supersedes the plan's original and must be reproduced (not re-derived from scratch) by the executor:
    - `:6122` pre-launch clean-base gate. TREE. In scope. Contains only the refusal.
    - `:6151` self-finalize block. TREE-CRITICAL, IN SCOPE, opposite of the plan's original "leave alone". Its condition is about lifecycle but it CONTAINS `allocate_isolation_worktree` at `:6198` (AST: the block spans `:6151-6264`, with `if isolate:` at `:6196-6264` inside it). Leaving it alone means a review turn never allocates a lane, so E-02 cannot function. The lifecycle calls INSIDE it (`driver_begin` at `:6167`/`:6169`) must stay review-exempt, so this site needs SPLITTING: hoist the allocation out of the lifecycle condition, or add a review-permitting branch that allocates without calling begin. Do NOT simply delete `not is_review` here, which would make a review call `driver_begin` and claim execution authority it must not have.
    - `:5467` `--file` attachment localization. TREE. In scope (new).
    - `:6279` lane-relative plan path and prompt rebuild. TREE. In scope.
    - `:6519` lane-submission collection. TREE. In scope. See E-08; leaving it makes a review's outcome uncollected.
    - `:6572` post-turn validation of an executed disposition. LIFECYCLE. Leave. A review produces no executed disposition to validate. This is the ONE site the plan's original classification got right on the leave side.
    - `:6665` `integration_gate_relevant`. TREE-CRITICAL, IN SCOPE, opposite of the plan's original. It gates the MERGE-BACK at `:6740` (AST: the block spans `:6707-6886`). Leaving it means E-03 has no reachable call site. Like `:6151`, it needs splitting rather than deleting: the suite check and `driver_finalize` inside it must remain review-exempt.
    - THE TEARDOWN HALF OF THIS ROW WAS WRONG AND IS CORRECTED AT REVIEW ROUND 2 (PR-511, F-12). Round 1 said `:6665` "gates the worktree TEARDOWN at `:6825`", implying that splitting `:6665` gives a review a teardown. IT DOES NOT, and the real situation is worse. AST-verified: `teardown_isolation_worktree` is called at EXACTLY ONE place in the whole file (`:6825`), nested `if integration_gate_relevant and integration.earned:` (`:6707-6886`) -> `if fin_rc == 0:` (`:6730-6886`) -> `if not integrated:` (`:6746-6864`) -> its `else` -> `elif wt_handle is not None:` (`:6823-6826`). The load-bearing gate is `fin_rc == 0`, and `fin_rc` comes from `driver_finalize` at `:6727`, which a review MUST NEVER CALL. So no split of `:6665` alone can reach the teardown: a review has no `fin_rc` at all. A review lane therefore has NO teardown path whatsoever and E-01 must say so rather than implying a split supplies one. The same single-call-site structure was verified on agy (`:3870`, gated by `fin_rc == 0` at `:3780-3930`). Whoever implements the sweep lane must add its own teardown, which is E-11's job.
  - MIRROR THE TABLE ON AGY, where the twins are positionally exact and were verified: `:3262`, `:3291` (encloses the allocation at `:3326`), `:3409`, `:3584`, `:3629`, `:3720`, plus agy's own attachment site if one exists (note `run_opencode`'s `--file` surface has no agy twin, since agy passes its prompt inline, so that row may legitimately read "not applicable" with that reason stated).
  - Depends on: none
  - Expected outcome: a written table of every site on both hosts, each marked tree (change), tree-critical (SPLIT, with what must stay exempt named), lifecycle (leave), or not-applicable, with its reason and the enclosing block that justifies it.
  - EXECUTED. The census was re-derived at execution HEAD `c146cdb3` by the prescribed method (AST-walk the enclosing `if` chain of each site and list what the block CONTAINS, not what its test says), because Orders 01 to 04 of this Set executed after the review rounds and every line number in the table above has moved. THE REVIEW'S CLASSIFICATION WAS CONFIRMED CORRECT in substance on every row; only the line numbers changed. Both tree-critical rows were handled by SPLITTING, never by deleting `not is_review`: the allocation a review needs was HOISTED into its own `if is_review and isolate:` branch placed BEFORE the self-finalize block, and the merge a review needs was given its own `if is_review and wt_handle is not None:` branch AFTER the integration block, so `driver_begin`, `driver_finalize` and the suite check all remain review-exempt exactly as they were. The full table (both hosts, with each site's span, enclosing chain and contained calls) is in V-01's observed evidence.
  - Execution state: performed
- [x] E-02 Allocate ONE lane for the WHOLE REVIEW SWEEP and run every review turn inside it (OQ-02, resolved), reusing the existing `wt_handle` / `work_dir` machinery rather than adding a second isolation path. The lane is allocated by the COORDINATOR once, before the first review dispatches, and torn down after the last one merges; it is NOT allocated per item as an execute lane is. `work_dir = str(wt_handle.path)` (`:6199`) is the existing seam for handing a turn its tree. THE LANE-RELATIVE PLAN PATH IS MANDATORY, not optional: the guard at `:6279` exists because of a measured incident (run `run-20260831T153226Z-3424176`, plan `y6mfgo`) in which the prompt carried MAIN's absolute plan path with no statement of isolation, and the agent read `../../../DECISIONS.md` and committed 18 files into MAIN while its lane stayed at zero commits. A review turn must receive its plan path resolved inside the lane AND an explicit statement that it is working in one, or it will reproduce that.
  - THE SWEEP LANE GOES STALE AND ITS STALENESS GROWS WITH EVERY MERGE, WHICH NO ITEM ADDRESSES AND WHICH CONTRADICTS OQ-02's OWN DECIDING ARGUMENT. FOUND AND MEASURED AT REVIEW ROUND 2 (PR-513, F-14). One lane is allocated ONCE at sweep start, and `allocate_isolation_worktree` cuts it at `base_commit="HEAD"` (`runner_shared.py:833-847` -> `worktree_lease.allocate_worktree`, `:550-556`). Every review then MERGES to main (E-03), so main advances while the lane keeps its original base, and NOTHING refreshes it: verified there is no rebase, refresh, or re-base-onto helper anywhere in `worktree_lease.py` or the runners (grepped for `rebase` across the package: no hits). MEASURED in a scratch repo: after review 1 and review 2 merged, the lane's own `peer.txt` still read `peer v1` while main read `peer v2`, and a plan a peer corrected ON MAIN mid-sweep read its PRE-correction text inside the lane. So in a nine-item sweep, review 9 reads a tree eight merges behind.
  - WHY THAT IS NOT MERELY UNTIDY. OQ-02's resolution rests on the claim that "a single lane also gives the reviewing agent a full checkout, so cross-plan awareness (the thing that caught this Set's own collision with three approved plans) is preserved rather than fragmented across N lanes". The measurement contradicts exactly that: the full checkout is a SNAPSHOT FROZEN AT SWEEP START, so the cross-plan awareness it promises DEGRADES monotonically. This Set is the concrete instance. F-9 records that reviewing `8lfoum` let the agent see and correct three siblings; under a sweep lane frozen at start, the review of sibling N reads sibling texts as they were BEFORE reviews 1..N-1 merged, missing the very corrections those reviews made. Note OQ-02's OTHER claim (reviews touch disjoint paths, so there is nothing to collide over) is TRUE and survives: the collision measured here is lane-versus-MAIN, not review-versus-review, which is why the disjointness argument does not cover it.
  - THE GOOD NEWS, ALSO MEASURED: nothing is silently corrupted. When the lane's copy of a plan and main's copy both changed, `git merge --no-ff` reported `CONFLICT (content)` and `integrate_lane_branch` aborts, leaving main clean (verified: after `git merge --abort` the peer's text was intact and `git status --porcelain` was empty). So the failure mode is a STRANDED REVIEW, not a lost edit. That is acceptable per-incident and unacceptable as a design that makes it likelier with every item.
  - SO STATE THE REFRESH POLICY EXPLICITLY, and do not leave it to the executor. The three honest options: (a) REFRESH THE LANE between reviews (fast-forward the lane to main after each merge), which keeps one lane and one session while restoring freshness, and needs a new helper since none exists; (b) RE-ALLOCATE per review, which is the per-item shape OQ-02 rejected and which reopens the session question (F-5); or (c) ACCEPT the staleness and BOUND it, stating the maximum sweep length for which it is tolerable and recording the stranded-review outcome as expected. This is escalated as OQ-04 because it revisits a maintainer ruling.
  - Depends on: E-01
  - Expected outcome: a review turn's cwd, plan path, prompt text AND `--file` attachments all refer to the lane; a review still performs no `driver_begin`; MAIN's `git status --porcelain` is unchanged for the whole turn; and the lane's freshness policy is implemented as OQ-04 directs rather than left implicit.
  - EXECUTED. ONE lane serves every review of a run (`runner_shared.acquire_review_sweep_lane`), keyed on the RUN and recorded at RUN level in `state["review_sweep_lane"]`, reusing `worktree_lease.allocate_worktree` so there is no second isolation path. It is allocated LAZILY on the first review rather than eagerly at run start: the property OQ-02 rules on is ONE LANE FOR THE SWEEP, which lazy allocation delivers exactly, while additionally not cutting a worktree for a run containing no review items. Both halves of the `y6mfgo` lesson are applied: `build_review_prompt` gained a `lane_root` parameter that resolves the plan path INSIDE the lane AND appends the shared `lane_containment.isolation_notice`, on its own lines after the command line so the slash command's `$ARGUMENTS` is unaffected. The `--file` attachment localizes through the existing `localize_attachment` because a review now materializes its own lane input manifest. OQ-04's option (a) is implemented as `runner_shared.refresh_sweep_lane`, a `git merge --ff-only` inside the lane on every reuse, which REFUSES rather than forcing on a dirty or diverged lane. FAIL-CLOSED: a review whose lane allocation fails is marked `blocked` and never falls back to the shared checkout, because that fallback is the behavior this plan removes and would be invisible.
  - Execution state: performed

### Task group 2: land the review output through the merge

- [x] E-03 Integrate a review lane back to main as one merge, by WIDENING `integrate_lane_branch` to take an explicit action kind and SKIP the revalidation gate for a review (OQ-01, resolved). A review's output is two files, both scoped to one plan: the plan itself (revisions applied) and the review record, verified at review on commit `a9510164`, which holds exactly `M .aw/records/plans/pending/...tgop8e...ipd.md` and `A .aw/records/reviews/...tgop8e...review.md`. Keep the merge steps of that function fully shared, because they carry the `--ff-only`-then-`--no-ff` sequence whose ff failure is the expected "main advanced" case, the capture-conflicted-paths-BEFORE-abort ordering, and the `host_label` merge subject. THE HARD CONSTRAINT: the action kind must be an EXPLICIT parameter and the docstring must state that a review is merged without revalidation because it produces nothing to revalidate. Do NOT pass a synthetic "validation passed" value into the gate; that is a forged attestation, not a skip.
  - CITATION CORRECTED AT REVIEW: the shared merge steps are `runner_shared.py:1036-1064`, not `:1035-1063`. The ff-only attempt whose output is deliberately discarded is at `:1036`, and the function ends at `:1064`. Re-locate by symbol if it drifts again.
  - THERE IS NO REACHABLE CALL SITE UNTIL E-01 SPLITS `:6665`, which the plan's original classification marked leave-alone. `integrate_lane_branch` is called at `:6740`, nested inside `if integration_gate_relevant and integration.earned:` (`:6707-6886`), whose first conjunct requires `not is_review`. So this item depends on that split as much as on E-02.
  - NOTE THE SIGNATURE CHANGE HAS FOUR PRODUCTION CALLERS AND FIVE TEST CALL SITES, so an explicit parameter must either carry a default or every caller updates in the same pass: `oc_runipd.py:1978` and `agy_runipd.py:1322` (the per-host thin wrappers), their call sites at `oc_runipd.py:6740` and `agy_runipd.py:3789`, plus `tests/test_oc_runipd.py:3251`, `tests/test_agy_runipd_cli.py:756`, and `tests/test_runner_shared.py:1685`, `:1715`, `:1775`. PREFER NO DEFAULT for the action kind, following the precedent set by `host_label` in the same function, whose docstring states it has "NO DEFAULT DELIBERATELY" because a default would let a new caller silently get the wrong behavior. The same reasoning applies here with more force: a defaulted action kind would let a future caller silently skip revalidation.
  - A SHIPPED CONTRACT TEST FORBIDS PUTTING THE PARAMETER ON THE PER-HOST WRAPPERS, AND THE PLAN NEVER MENTIONS IT. FOUND AND PROVED AT REVIEW ROUND 2 (PR-512, F-13) by making the change and running the suite. `tests/test_runner_shared.py:787` is `test_each_wrapper_keeps_the_ORIGINAL_signature`, whose docstring is "No call site may have had to change, so no wrapper may expose the injected parameter"; it asserts each host wrapper's positional args are exactly `["repo","handle","id6","validation_runner"]` AND that its kwonly list is EMPTY (`:800-802`). MEASURED: adding `*, action_kind: str` to `oc_runipd.integrate_lane_branch` (exactly the no-default shape this item prescribes) fails it with `AssertionError: Lists differ: ['action_kind'] != []`. The file was restored immediately and the test re-run green; no product code was left changed by this review. So the census of "nine call sites" is incomplete: there are also THREE AST-level structural tests keyed on this function's shape (`:787` the wrapper signature, `:836` `host_label` has no default, `:851` each runner binds its own label). RESOLVE THIS EXPLICITLY, because the honest options differ in what they cost. (a) Put the action kind ONLY on the shared `runner_shared` function and have each wrapper bind it as a literal, exactly as it already binds `host_label` and `run_checked`; the wrapper signatures then do not change and `:787` stays green untouched. This appears to satisfy every constraint and is the recommended route, but it means the WRAPPER cannot distinguish actions, so the review path must call `runner_shared.integrate_lane_branch` directly or a second wrapper must exist. (b) Change the wrapper signature and AMEND `:787`, which requires justifying why "no call site may have had to change" no longer holds. Do NOT discover this at execution time; decide it first and record the choice.
  - Depends on: E-01, E-02
  - Expected outcome: a review's two files reach main via a single merge, or not at all; the function declares rather than implies that revalidation was skipped; and every existing caller is updated rather than relying on a permissive default.
  - EXECUTED VIA ROUTE (a), the route F-13 recommended, and it was the compatible one: `action_kind` is a keyword-only parameter with NO DEFAULT on the SHARED `runner_shared.integrate_lane_branch`, and each host binds it as a LITERAL in its wrapper exactly as it already binds `host_label`, so no wrapper signature changed and the shipped contract test `test_each_wrapper_keeps_the_ORIGINAL_signature` stays green UNTOUCHED (measured: it passes; see V-03). The review path calls a SIBLING wrapper, `integrate_review_lane_branch`, rather than reaching around either existing one. THE SKIP IS STRUCTURAL, NOT A FAKED VERDICT (OQ-01's load-bearing line): the review wrapper takes NO `validation_runner` parameter at all and binds `None`, so a synthetic "validation passed" value cannot be supplied even by mistake; the shared body simply does not call the gate for `action_kind="review"`, and constructs no `IntegrationGateResult`. An unrecognized kind is REFUSED with a `DriverError` rather than coerced, so a typo cannot fall through to whichever branch is first. Steps 0 and 2-4 (dirty-overlap guard, ff-only-then-no-ff, capture-conflicted-paths-BEFORE-abort, `host_label` subject) remain fully shared.
  - ONE ADDITIONAL STEP WAS REQUIRED AND IS NOT IN THE PLAN, found by executing it: `runner_shared.commit_review_lane_output`. `integrate_lane_branch` merges the BRANCH (`git diff base..branch`), so UNCOMMITTED lane files are invisible to it and the lane is later torn down. Before isolation, a review that edited the plan but did not commit left those files in MAIN's working tree, where they survived; isolating without this step would therefore SILENTLY DESTROY the output of any review that did not commit for itself, which is strictly worse than the dirty tree this plan removes. The commit is PATH-SCOPED to exactly what `git status --porcelain` reports inside the lane (never `add -A`), runs hooks normally with no `--no-verify`, and treats a hook rejection as "nothing committed" so the work stays in the lane and the integration is a reported no-op rather than a silent loss.
  - Execution state: performed
- [x] E-04 PRESERVE the sweep's shared session, which the one-lane design makes safe rather than requiring a trade (OQ-03, resolved). Verify, do not assume, that a single lane plus a single session behaves: `run_opencode` drops `--session` for any isolated turn (`:5405`), so the sweep must either keep its session across turns in the one lane or the code must be taught that a SWEEP lane is not a per-item lane. Whichever route is taken, the two CLI promises of continuity (`:7699`, `:7728`) must remain TRUE at the end, and the `xd9sll` cardinality rule must still hold: never carry a session into a DIFFERENT tree. Record which route was taken and paste the evidence; do NOT relax the cardinality rule to make sharing work.
  - Depends on: E-02
  - Expected outcome: the conflict is resolved as OQ-03 directs, the losing side is explicitly corrected in the surface that promises it, and no code path re-binds one session across two trees.
  - EXECUTED, AND NOTHING LOST: the sweep KEEPS its shared session, so neither CLI promise had to be withdrawn and both were instead made MORE specific (they now also state the shared isolated worktree and the one-merge landing). The route taken: `runner_shared.turn_runs_in_review_sweep_lane` states `xd9sll`'s rule PRECISELY for the first time. That incident's recorded cause is a MISMATCH OF CARDINALITY (sessions keyed per SET, worktrees per ITEM), so the invariant that actually holds is "never carry one session into a DIFFERENT tree", not "an isolated turn never resumes". A per-item execute lane is a different tree every turn and still gets a fresh session, byte-identically; the sweep lane is ONE tree for every review of the run and therefore cannot reproduce the incident. THE CARDINALITY RULE IS NOT RELAXED: the sweep's session lives under its OWN run-level key and `set_sessions` is deliberately left untouched, so a later EXECUTE turn in the same set cannot inherit it. The set path's unexplained-session-change refusal was MIRRORED onto the sweep key rather than dropped, because moving reviews to their own key would otherwise have silently retired that guard for the only action type that still shares a session. Comparison is by resolved path, so a symlinked spelling of the same tree is the same tree.
  - Execution state: performed

### Task group 3: keep the review-only steps working, and parity

- [x] E-05 Keep the auto-approve step correct. `:6926` clears a reviewed plan to `execute` under `--full-auto`, reading the plan via `resolve_plan_path(repo, ...)` against MAIN. After isolation the freshly reviewed plan is on the lane until the merge lands, so this must read the plan AFTER integration, or read it from the right tree. Getting this wrong makes auto-approve either read a stale plan or fail to find the review evidence, and the shared predicate `is_plan_review_approved` is deliberately fail-closed (`plan_readiness.py:297-306`), so the visible symptom would be reviews that never auto-approve.
  - IT IS NOT ONLY A READ, WHICH THE PLAN UNDERSTATES. The branch also WRITES: `set_plan_approved(repo, item["id6"])` (`:735`) shells out to `aw set` against MAIN, so after isolation this is a second mid-run write to the shared checkout, i.e. exactly the class of write this plan exists to remove. Ordering it after integration therefore fixes both the stale read AND the stray write in one move; ordering it before integration fixes neither. Note it must remain a `reviewed -> auto-approved` transition and must NOT become `--by-human`: `set_plan_approved`'s docstring records that the machine asserting a human attestation was a defect deliberately fixed.
  - Depends on: E-03
  - Expected outcome: `--full-auto` still promotes a cleanly reviewed plan, reading the post-merge state, and the promotion write happens after the merge rather than into the shared checkout mid-turn.
  - EXECUTED, and the required ordering turned out to ALREADY HOLD rather than needing a move: the review integration branch sits several hundred lines above the auto-approve branch in `execute_item` on both hosts, and no path reaches the promotion without passing the merge. That was VERIFIED by structure rather than assumed (V-05 pastes the ordering and a live `--full-auto` run), and the reason it matters in both directions is now recorded at the site: this branch does not only READ, it WRITES via `set_plan_approved` shelling out to `aw set` against MAIN, so ordering it before the merge would have left the one remaining mid-turn write into the shared checkout. Measured live: the plan reaches `- Status: auto-approved`, never human `approved`, and no `by-human` attestation appears.
  - Execution state: performed

### Task group 4: the sites the original census missed

- [x] E-08 Collect a review lane's submissions, which today is excluded at `:6519` (`if work_dir and not is_review:`). This item exists because review found the omission, and it is not optional: `collect_lane_submissions`' own docstring states it "IS THE OTHER HALF OF R1 AND MUST SHIP WITH IT (spec R2.1)", because a lane-relative instruction whose output nobody collects "fails INVISIBLY" -- the worker writes its outcome inside the lane, the driver reads `<run_dir>/outcomes/...`, finds nothing, and scores the turn from the empty-outcome fallback. E-02 makes the review prompt lane-relative, so shipping E-02 without this is precisely the split that spec forbids.
  - VERIFY WHETHER A REVIEW TURN HAS SUBMISSIONS TO COLLECT AT ALL before widening the guard, and say so either way. If a review produces no lane-side outcome file, the honest change may be a comment recording that rather than a call; if it does, the call is required. Do not widen it speculatively.
  - Depends on: E-01, E-02
  - Expected outcome: either a review lane's submissions are collected before disposition reconciliation, or the plan records with evidence that a review writes none and the exclusion is correct.
  - EXECUTED, AND THE ANSWER IS BOTH HALVES, WHICH THE ITEM'S TWO OPTIONS DID NOT ANTICIPATE. VERIFIED FIRST, as the item requires: a review turn writes NO lane-side submission today. `build_review_prompt` is the `/plan-review` command plus the isolation notice and names no outcome, report or decisions path, and a live review turn's lane holds none of the three (all recorded `absent`, which is the legitimate R2.4 observation). BUT THE CALL IS STILL CORRECT rather than being replaced by a comment, and the reason is the RECEIPT rather than the copies: the R2.5 collection receipt is what `submission_retention` reads to distinguish driver-written content from unexplained content, so without it the sweep lane can never be classified and therefore can NEVER BE RETIRED. That is not hypothetical: it was measured while writing E-06's regression (the teardown refused with "an uncollected submission (no run directory or item was supplied...)"). So the guard is widened, and the receipt is the load-bearing output. The `absent` evidence and the full receipt are pasted in V-08.
  - Execution state: performed
- [x] E-09 Fix the review DISPOSITION, which review found reads the wrong tree. `reconcile_disposition`'s review branch (`:5992-6003`) resolves the plan against `repo` (MAIN) and derives the disposition from its `- Status:`: `reviewed`/`approved` if the field says so, else a bare `reviewed` on exit 0. After isolation the revised plan is on the LANE and MAIN still reads `to-review`, so the status comparison always misses and every isolated review scores from the fallback rather than from evidence. Two consequences, both bad: a successful review that set `approved` would be recorded merely `reviewed`, and the status check stops discriminating at all, so it can no longer contribute to distinguishing a real review from a turn that did nothing.
  - READ THE PLAN FROM THE LANE when the turn was isolated, mirroring the pattern the validation path already uses at `:6577` (`plan_repo = Path(work_dir) if work_dir else repo`). That precedent exists for this exact reason and should be reused rather than re-invented.
  - THE "PICK ONE DELIBERATELY" CHOICE IS FALSE AND IS REMOVED AT REVIEW ROUND 2 (PR-514, F-15). This item previously said "if the disposition is computed BEFORE integration it must read the lane; if AFTER, it may read main. Pick one deliberately." There is nothing to pick: the ordering is fixed by the code. `reconcile_disposition` is called for the main turn at `:6560`, and the integration block begins at `:6707`, so the disposition ALWAYS precedes the merge; verified there is NO call to `reconcile_disposition` anywhere after `:6707` (the only three call sites are `:6381`, `:6409` and `:6560`, all before it). So the lane read is the ONLY correct answer, and an executor who "chose" to read main would be choosing a branch that cannot exist. Implement the lane read and delete the choice.
  - Depends on: E-01, E-02
  - Expected outcome: an isolated review's disposition is derived from the tree that actually holds the revised plan, and a review that sets `approved` is still recorded `approved`.
  - EXECUTED as F-15 directs, with no choice offered to the executor: `reconcile_disposition` gained an OPTIONAL `plan_repo` parameter defaulted to `repo` (so every existing call site and behavior is byte-identical) and the main-turn call site passes the lane when the turn ran in one. The precedent was REUSED rather than re-invented: it is the same `Path(work_dir) if work_dir else repo` shape the verifier path already uses for this exact reason. `plan_repo` is consumed ONLY by the review branch, so the execute branch's `plan_bucket` check still reads MAIN deliberately, because that check asks a different question ("did finalize already move this plan on main"). Measured on BOTH hosts: the lane read records `approved`, the pre-change main read records merely `reviewed`.
  - Execution state: performed

- [x] E-11 GIVE THE SWEEP LANE A TEARDOWN, because it has none and no split supplies one. ADDED AT REVIEW ROUND 2 (PR-511, F-12) after AST-verifying that `teardown_isolation_worktree` has EXACTLY ONE call site per host (`oc_runipd.py:6825`, `agy_runipd.py:3870`), reachable only through `if fin_rc == 0:` where `fin_rc` is `driver_finalize`'s return code. A review never calls `driver_finalize`, so it can never reach that teardown, and round 1's claim that splitting `:6665` would supply one was wrong.
  - THE TEARDOWN IS COORDINATOR-OWNED AND RUNS ONCE, matching E-02's allocation: the sweep lane is allocated once before the first review and must be removed after the last one merges, so its teardown belongs at the same level as its allocation and NOT inside the per-item path. Putting it per item would destroy the lane the next review needs.
  - IT MUST NOT BE UNCONDITIONAL. `teardown_isolation_worktree`'s own docstring states it is "DESTRUCTIVE: this deletes the lane BRANCH and force-removes the worktree, so it must only ever be called on a lane that holds NO work", and it directs a non-success caller through `reclaim_lanes_on_interrupt`, "which classifies first and preserves anything holding work". A sweep that ends with an unmerged review (a stranded conflict per F-14, or an interrupted run) has a lane that DOES hold work, so the teardown must classify before removing and preserve a lane holding unmerged commits. Reuse that existing path; do not write a second classifier.
  - ALSO HANDLE THE INTERRUPT CASE, since a sweep lane outlives every individual turn: if the run dies between reviews, the lane is left behind with no per-item owner to reclaim it. State whether the existing lane-reclaim machinery finds a sweep lane at all (it is keyed on lane identity, and the sweep lane's identity is not an item id6 -- see E-02), and if it does not, say what does.
  - Depends on: E-02
  - Expected outcome: a completed sweep leaves no worktree and no lane branch behind (`git worktree list` shows none), a sweep with a stranded or unmerged review PRESERVES the lane with its work and says so, and an interrupted sweep's lane is discoverable by whatever reclaims it.
  - EXECUTED. The teardown is COORDINATOR-OWNED and runs ONCE, in each host's `run_queue` after the dispatch loop and before the report, matching the single allocation; it is idempotent so wiring it into a further exit path later cannot double-retire. IT IS NOT UNCONDITIONAL: `runner_shared.retire_review_sweep_lane` delegates to `lane_containment.teardown_review_sweep_lane`, which delegates to the EXISTING spec-R5.5 gate `teardown_lane_if_classified`, so no second classifier exists and `teardown_isolation_worktree`'s own no-work precondition is respected. A lane holding unexplained content is PRESERVED with its branch and the run record names the condition.
  - THE INTERRUPT CASE IS ANSWERED WITH EVIDENCE, as the item demands. The existing lane reclaimer reads `_lane_records_from_state`, which is keyed on per-ITEM attempt records, so it DOES find the sweep lane in the common case (a review turn records its lane on its own attempt exactly as an execute turn does). What it CANNOT find is a run interrupted BETWEEN reviews, or one whose lane was allocated and then refused before any attempt recorded it: that lane is named by no attempt. So `runner_shared.lane_records_including_sweep` COMPOSES the per-item reader with the RUN-LEVEL record, and both hosts' `reclaim_lanes_on_interrupt` now read through it. It COMPOSES rather than edits because `_lane_records_from_state`'s body is pinned byte-for-byte against a pre-move fingerprint fixture proving it was a pure move; editing it would break that proof for an unrelated reason.
  - TWO DEFECTS IN THIS ITEM'S OWN MECHANISM WERE FOUND BY ITS REGRESSION AND FIXED. FIRST, each review materialized lane input revision 1, so review 2 OVERWROTE review 1's manifest and left review 1's copied plan accounted for by nothing; the gate then correctly refused ("2 unknown IGNORED file(s)") and a perfectly clean sweep could never retire its lane. Each review now materializes its OWN revision. SECOND, the gate's submission question is per ITEM while the lane is SHARED, so passing no item made it answer "uncollected" by design and passing one arbitrary item would have called that item's verdict the lane's; the gate now takes EVERY item that used the lane, probes them all BEFORE removing anything, and authorizes teardown only when no item leaves an unexplained path.
  - Execution state: performed

### Task group 5: parity and regression

- [x] E-10 CONSTRAIN A REVIEW TURN'S WRITES to the plan under review and its own review record, and make a write outside that set OBSERVABLE. F-9 measured a single review commit touching three sibling plans that were still `queued`, and F-10 shows nothing checks it: `_compute_scope_reconciliation` is reachable only from `driver_finalize`, which is review-exempt. Isolation alone does NOT fix this: a lane makes the writes land via one merge instead of dirtying main, but a review in a lane can still rewrite three siblings' files and merge them. So this item is REQUIRED IN ADDITION to E-02. DECIDE AND RECORD which of two shapes: (a) REFUSE a write outside the allowed set, which is strict but may break a legitimate case; or (b) PERMIT it and RECONCILE it, naming every out-of-scope path in the run record the way the execute path's scope reconciliation already does. NOTE THE LEGITIMATE CASE BEFORE CHOOSING: an orchestrator review SHOULD read its children (that is how the collision with three approved plans was caught), and it may have a real reason to correct a child's text; the objection is that today it does so silently, to an item that has not had its turn. Whichever shape is chosen, a sibling's plan MUST NOT be rewritten while that sibling is still `queued` in the same run without the run record saying so.
  - Depends on: E-02
  - Expected outcome: a review's writes are confined to the plan under review and its record, or any write beyond that set is named in the run record; and no queued item's input is silently rewritten by another item's turn.
  - EXECUTED AS SHAPE (b), PERMIT-AND-RECONCILE, and the reason is the legitimate case the item itself names: an ORCHESTRATOR review SHOULD read its children (that is how this Set's own collision with three approved plans was caught) and may have a real reason to correct a child's text, so REFUSING would break a case the repository depends on. What F-9 objected to was never that the write happened but that it happened SILENTLY, to an item that had not had its turn. So `runner_shared.classify_review_writes` splits a review lane's changed paths into the two files a review is FOR and everything beyond, flags the subset belonging to an item still `queued` IN THIS RUN, and the driver records the result on the item, emits a `review-wrote-out-of-scope-paths` event, and prints the sentence. This mirrors what the execute path's own scope reconciliation does and which a review can never reach, since `_compute_scope_reconciliation` is called only from `driver_finalize`.
  - Execution state: performed
- [x] E-06 Mirror every change on `agy_runipd.py` and add the regression: a review sweep of at least three plans, with a deliberately dirty unrelated tracked path in the shared checkout, where all three reviews complete, MAIN's `git status --porcelain` shows ONLY that unrelated dirty path at every item boundary, and each review's two files arrive in main. Assert the session behavior OQ-03 selected (shared, or fresh-per-lane with the help text corrected), not the behavior the plan originally assumed.
  - THE MAIN-CLEAN ASSERTION MUST NOT BE "EMPTY", corrected at review. The regression deliberately dirties an unrelated tracked path, so an empty `git status --porcelain` would mean the test destroyed the peer's change, which is the opposite of the property wanted. Assert equality against the pre-run status instead.
  - ASSERT NO LEAKED WORKTREE, since the teardown call is nested under the guard E-01 must split (`:6825` inside `:6707-6886`) and a mis-split leaks one lane per review silently. Paste `git worktree list` after the sweep.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-08, E-09
  - Expected outcome: both hosts isolate reviews identically, no worktree leaks, the unrelated dirty path survives untouched, and the properties above are pinned.
  - EXECUTED. Every change is mirrored on `agy_runipd.py`, and the regression is the new `tests/test_review_lane_isolation.py` (27 tests, all passing), which runs its three-review sweep against BOTH hosts through the same agent behavior rather than writing a second fake. THE MAIN-CLEAN ASSERTION IS EQUALITY WITH THE PRE-RUN STATUS, not emptiness, exactly as the review correction requires: the fixture deliberately leaves a peer's UNCOMMITTED edit to a tracked file, and the test additionally asserts that file's bytes are unchanged, so a run that reverted a co-worker's work would FAIL rather than pass. `git worktree list` and `git branch --list 'aw/lane/*'` are asserted after the sweep for the no-leak property, and the PRESERVED case is asserted too. Parity is enforced structurally as well as behaviorally: a test asserts neither host redefines any of the six shared review-lane helpers (spec R2.6/R6.1) and that both read lanes through the sweep-aware composer, so a one-driver-only fix fails.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A WORKER may commit facts about its own item; only the COORDINATOR may commit facts about a Set. A review is a fact about ONE plan, so a worker-side lane is the right home for it, exactly as Order 03 argues for the backlog close.
- `is_review` is overloaded: it currently gates both tree decisions and lifecycle decisions. E-01 exists because that overload is the main hazard in this change.
- THE OVERLOAD IS WORSE THAN "ONE FLAG, TWO QUESTIONS", and this is the fact that reshaped the plan at review. Two of the guards have a LIFECYCLE condition but a TREE-CRITICAL body: `:6151` reads as self-finalize yet contains the worktree allocation, and `:6665` reads as integration-gate relevance yet contains both the merge-back and the teardown. So the guard's condition is not a reliable classifier of what the block does, and any classification derived from reading conditions alone will be wrong in exactly the direction that silently disables the work. Classify by CONTENTS.
- Reviews are exempt from the pre-launch clean-base gate (`:6122`), which is why they kept running while 68 execute items were refused on 2026-09-13. The exemption is an accident of scope, not a safety argument.
- AN ISOLATED TURN IS ALWAYS A FRESH SESSION, BY DELIBERATE DESIGN, and the reason is a measured loss of four consecutive lanes (`lanesess xd9sll`, recorded at `oc_runipd.py:5383-5390`): an opencode session carries its own directory binding that OVERRIDES `--dir`. This is the single hardest constraint on this plan, because the review sweep's shared session is a promised feature.
- THE REVIEW DISPOSITION IS DERIVED FROM THE PLAN'S `- Status:` FIELD, not from an outcome file (`reconcile_disposition`, `:5992-6003`), which is why moving the plan to a lane changes how a review is SCORED and not merely where it is written.
- A NO-DEFAULT PARAMETER IS THE HOUSE PRECEDENT for a value whose wrong setting is silently harmful: `integrate_lane_branch`'s `host_label` documents having "NO DEFAULT DELIBERATELY" because a default would misattribute git history invisibly. E-03's action kind is the same class of value.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | A review is NOT read-only with respect to the repository. It edits the plan and adds a review record, and commits both to main. | commit `a9510164`: `M .aw/records/plans/pending/...tgop8e...ipd.md`, `A .aw/records/reviews/...tgop8e...review.md` |
| F-2 | Reviews are excluded from isolation by six separate guards, mixing two unrelated concerns. ALL SIX VERIFIED AT REVIEW on oc, and their SIX TWINS LOCATED ON AGY so E-01's classification table covers both hosts from the start: `agy_runipd.py:3262` (clean-base gate), `:3291` (self-finalize), `:3409` and `:3584` (lane-relative paths), `:3629` (post-turn validation), `:3720` (integration gate). The oc/agy pairing is positional and exact, which is what makes E-06's parity requirement mechanical rather than exploratory. | `oc_runipd.py:6122`, `:6151`, `:6279`, `:6519`, `:6572`, `:6665`; `agy_runipd.py:3262`, `:3291`, `:3409`, `:3584`, `:3629`, `:3720` (both sets read at review) |
| F-3 | Reviews escaped the 2026-09-13 outage by EXEMPTION, not by being safe. The pre-launch gate that refused 68 execute items also skips reviews, and the two large runs that night happened to contain zero review items (38 execute + 3 orchestrate; 36 execute + 7 orchestrate). | run `run-20260913T031148Z-1722898`, run `run-20260913T031521Z-1774617` |
| F-4 | Isolation is CHEAP to get wrong in a way that writes to main. A previously measured incident had an unisolated-looking prompt cause an agent to commit 18 files into MAIN while its lane stayed empty, which is why the lane-relative plan path and the explicit in-lane statement exist. | the comment at `oc_runipd.py:6275-6279`, citing run `run-20260831T153226Z-3424176` and plan `y6mfgo` |
| F-5 | Isolation currently FORCES a fresh session, so naive isolation would silently break the review sweep's shared-session property. STRENGTHENED AT REVIEW: this is not an incidental interaction but a DIRECT CONTRADICTION with a measured incident behind it. The recorded cause is that an opencode session carries its own project/`directory` binding which OVERRIDES `--dir`, so lanes 2..N of a set ran in the PREVIOUS lane's worktree and four consecutive lanes were lost; the conclusion drawn in the code is categorical ("an isolated turn is ALWAYS a fresh session"). So per-review lanes plus one shared session is exactly the configuration `xd9sll` forbids, and one of the two properties must yield. | `oc_runipd.py:5405` drops `--session` when `isolated_turn`; incident detail at `:5383-5390`; sharing promised at `:7699` and `:7728` (all read at review) |
| F-6 | SUPERSEDED BY F-9/F-11, and kept only as the record of a wrong framing. This row originally said the reward was smaller than for execute turns because a review is cheap to re-run, and that the case rested on UNIFORMITY. That understated it twice. The maintainer's stated reason was always CONCURRENCY (a review in progress strands plan execution by another agent or runner), and F-9 then measured something worse: a review turn rewrites OTHER QUEUED ITEMS' plans, so the harm is to correctness of the review pipeline itself, not merely to tidiness. Do not cite this row as a reason to defer the plan. | superseded by measurement; original text retained in git history |
| F-7 | THE PLAN'S OWN CLASSIFICATION IS WRONG ON THE TWO SITES THAT MATTER MOST, and it is wrong in the direction that silently disables the work. E-01 marked `:6151` and `:6665` LIFECYCLE / leave-alone. AST-verified: `if self_finalize and not is_review:` spans `:6151-6264` and CONTAINS `allocate_isolation_worktree` at `:6198` (via `if isolate:` at `:6196-6264`), so leaving it means a review NEVER gets a lane and E-02 cannot function; `if integration_gate_relevant and integration.earned:` spans `:6707-6886` and CONTAINS both the `integrate_lane_branch` call at `:6740` and `teardown_isolation_worktree` at `:6825`, so leaving it means E-03 has no reachable call site and, if a lane were somehow allocated, every review would LEAK a worktree. The same nesting was verified on agy (`:3291-3401` enclosing the allocation at `:3326`). Both sites need SPLITTING, not deleting, because genuine lifecycle calls (`driver_begin`, `driver_finalize`, the suite check) live in the same blocks and must stay review-exempt. | AST walk of the enclosing `if` chain for `oc_runipd.py:6198`, `:6740`, `:6825` and `agy_runipd.py:3326`, performed at review |
| F-8 | THE CENSUS OF SIX IS INCOMPLETE AND THE REVIEW DISPOSITION READS THE WRONG TREE. Three further sites, none mentioned in the plan: `:5467` gates `--file` attachment localization (a seventh `not is_review` site, whose own comment records a measured case where the attachments named MAIN while the prompt text named the lane); `:6519` excludes lane-submission collection, which `collect_lane_submissions` documents as the mandatory other half of a lane-relative prompt under spec R2.1 ("fails INVISIBLY" without it); and `reconcile_disposition`'s review branch resolves the plan against MAIN and scores the turn from its `- Status:`, so after isolation MAIN still reads `to-review`, the comparison always misses, and an `approved`-setting review is recorded merely `reviewed`. Addressed by E-01's added row, E-08 and E-09. | `oc_runipd.py:5467`, `:6519`, `:5992-6003`; `lane_containment.collect_lane_submissions` docstring; the existing lane-reading precedent at `:6577` |
| F-9 | A REVIEW TURN WRITES TO OTHER QUEUE ITEMS' FILES, AND NOTHING CONSTRAINS IT. Measured live 2026-09-13 and this is the strongest single argument for the plan. Reviewing the ORCHESTRATOR `8lfoum` produced commit `59cdc718` containing FIVE files: its own plan (108 lines) and review record (98 lines), PLUS three sibling child plans it rewrote (`d7qoxv` 4 lines, `metc8b` 15 lines, `u23gbn` 41 lines). All three siblings were still `queued` in the SAME run at that moment, so one item's turn mutated three other items' pending input before their own turns ran. Two consequences: a later review reads text a different turn rewrote, and its `Readiness` is computed against edits it did not make. | commit `59cdc718` (`git show --stat`); the run's `state.json` showing `d7qoxv`/`metc8b`/`u23gbn` as `queued` while `8lfoum` was `running` |
| F-10 | THERE IS NO SCOPE ENFORCEMENT ON A REVIEW TURN AT ALL, which is why F-9 is possible rather than merely unlucky. An EXECUTE turn declares `- Scope-Paths:` and is reconciled against it by `_compute_scope_reconciliation` (`oc_runipd.py:953`), but that is called ONLY from `driver_finalize` (`:995`), which sits inside the `if self_finalize and not is_review:` block at `:6151`. So a review turn gets no lane, no scope gate, and no finalize reconciliation: nothing checks what it touched, before or after. | verified by reading the call site and its enclosing guard |
| F-12 | A REVIEW LANE HAS NO TEARDOWN PATH AT ALL, AND ROUND 1's ACCOUNT OF WHY WAS WRONG. FOUND AT REVIEW ROUND 2. Round 1 said `:6665` "gates the worktree TEARDOWN at `:6825`", implying a split of `:6665` supplies a review with one. AST-verified: `teardown_isolation_worktree` has EXACTLY ONE call site in the whole file (`:6825`), nested `if integration_gate_relevant and integration.earned:` (`:6707-6886`) -> `if fin_rc == 0:` (`:6730-6886`) -> `if not integrated:` (`:6746-6864`) -> its `else` -> `elif wt_handle is not None:` (`:6823-6826`). The load-bearing gate is `fin_rc == 0`, and `fin_rc` is `driver_finalize`'s return code (`:6727`), which a review MUST NEVER produce. So no split of `:6665` can reach it and the "every review LEAKS a worktree" conclusion, while right, had the wrong cause: the leak is not a mis-split, it is the total absence of a reachable teardown. Identical single-call-site structure verified on agy (`:3870` under `fin_rc == 0` at `:3780-3930`). Addressed by new E-11, which must also respect `teardown_isolation_worktree`'s own docstring rule that it never be called on a lane holding work. | AST walk of the enclosing `if` chain for every `teardown_isolation_worktree(` call in `oc_runipd.py` and `agy_runipd.py`, performed at review round 2; the destructive-call rule is `runner_shared.py:850-858` |
| F-13 | A SHIPPED CONTRACT TEST FORBIDS E-03's PRESCRIBED SIGNATURE CHANGE, AND THE PLAN'S CALL-SITE CENSUS MISSES IT. FOUND AT REVIEW ROUND 2 BY MAKING THE CHANGE AND RUNNING THE SUITE, not by reading. `tests/test_runner_shared.py:787` (`test_each_wrapper_keeps_the_ORIGINAL_signature`, docstring "No call site may have had to change, so no wrapper may expose the injected parameter") asserts each host wrapper's positional args are exactly `["repo","handle","id6","validation_runner"]` and its kwonly list is EMPTY (`:800-802`). MEASURED: adding `*, action_kind: str` to `oc_runipd.integrate_lane_branch`, precisely the no-default shape E-03 prescribes, fails it with `AssertionError: Lists differ: ['action_kind'] != []`. The file was restored and the test re-run green, so this review left no product code changed. The census of "nine call sites" therefore omits THREE AST-level structural tests keyed on this function's shape (`:787`, `:836` host_label-has-no-default, `:851` each-runner-binds-its-own-label). Addressed by a new E-03 bullet naming two explicit routes, with binding the literal in each wrapper (as `host_label` already is) recommended so `:787` stays untouched. | measured at review round 2: patched `agent_workflows/oc_runipd.py:1967-1969`, ran `python3 -m pytest -o addopts="" -k ORIGINAL_signature tests/test_runner_shared.py` -> 1 failed with the diff shown; restored and re-ran -> 1 passed |
| F-14 | THE SWEEP LANE GOES STALE AND ITS STALENESS GROWS MONOTONICALLY, WHICH CONTRADICTS OQ-02's OWN DECIDING ARGUMENT. FOUND AT REVIEW ROUND 2. One lane is allocated ONCE at sweep start and cut at `base_commit="HEAD"` (`runner_shared.py:833-847` -> `worktree_lease.allocate_worktree` `:550-556`); every review then merges to main, advancing it, while the lane keeps its original base and NOTHING refreshes it (verified: no rebase/refresh helper exists anywhere in `worktree_lease.py` or either runner; grep for `rebase` across the package returns no hits). MEASURED in a scratch repo: after two reviews merged, the lane still read `peer v1` while main read `peer v2`, and a plan a peer corrected ON MAIN mid-sweep read its PRE-correction text inside the lane. OQ-02's resolution claims one lane "gives the reviewing agent a full checkout, so cross-plan awareness ... is preserved rather than fragmented"; the checkout is in fact a snapshot frozen at sweep start, so that awareness DEGRADES with every merge. This Set is the instance: under a sweep lane, the review of sibling N would read sibling texts as they were before reviews 1..N-1 merged, missing exactly the corrections F-9 credits. OQ-02's OTHER claim (reviews touch disjoint paths) is TRUE and survives, because the collision here is lane-versus-MAIN, not review-versus-review. NOT A SILENT CORRUPTION, also measured: a diverged plan produced `CONFLICT (content)` and the shared function aborts, leaving main clean and the peer's text intact (`git status --porcelain` empty after `git merge --abort`), so the failure mode is a STRANDED REVIEW that grows likelier with every item. Escalated as blocking OQ-04. | measured at review round 2 in `/tmp` scratch repos: serial sweep merges ff-only cleanly; after a peer commit the ff-only exits 128 and the `--no-ff` fallback succeeds; a lane-vs-main divergence on one plan conflicts and aborts with main clean; `allocate_worktree`'s base is `worktree_lease.py:554` |
| F-15 | E-09's "PICK ONE DELIBERATELY" IS A FALSE CHOICE; THE ORDERING IS FIXED BY THE CODE. FOUND AT REVIEW ROUND 2. E-09 told the executor that the disposition may be computed before integration (read the lane) or after (read main) and to pick one. There is nothing to pick: `reconcile_disposition` is called for the main turn at `:6560` and the integration block begins at `:6707`, so the disposition ALWAYS precedes the merge, and there is NO call to `reconcile_disposition` anywhere after `:6707` (its only three call sites are `:6381`, `:6409`, `:6560`). The lane read is the only correct implementation, and an executor who "chose" the main read would be choosing a branch that cannot exist. E-09 corrected to state this. | verified at review round 2 by enumerating every `reconcile_disposition(` call site in `oc_runipd.py` against the integration block's AST span `:6707-6886` |
| F-11 | THE DIRTY WINDOW IS PER-REVIEW AND REPEATS, so it is not a one-off. The five files above sat uncommitted in the shared checkout for the duration of that turn (roughly 36 minutes for the first item), and the review committed them only on completing the item. A concurrent execute run's clean-base gate refuses against ANY of them, so a nine-item review sweep reopens the window nine times. Measured the same evening: a `runanalytics` execute run had its items refused while this review held those plans dirty. | `git status --porcelain` sampled during the turn; the concurrent run's refusals |

## Proposed changes (ordered, validatable)

1. Classify every `not is_review` site by its CONTENTS on both hosts, marking two of them tree-critical/split (E-01), and record that a review has NO reachable teardown at all (F-12).
2. Allocate a lane for a review and run the turn in it, with lane-relative plan path, prompt and attachments (E-02), implementing the freshness policy OQ-04 selects (F-14).
3. Land the review's two files via one merge, adding an explicit no-default action kind by whichever of the two routes avoids breaking the shipped wrapper-signature contract test, and updating all nine call sites plus the three AST structural tests (E-03, F-13).
4. Resolve the shared-session versus isolation contradiction as OQ-03 directs, and correct whichever promise loses (E-04).
5. Order auto-approve after integration, which fixes both its stale read and its stray write to main (E-05).
6. Collect the review lane's submissions, or record with evidence that there are none (E-08).
7. Derive the review disposition from the LANE, which F-15 shows is the only reachable ordering (E-09).
8. Give the sweep lane a teardown, since none is reachable for a review, preserving a lane that holds work (E-11, F-12).
9. Mirror on agy and pin the properties, including no leaked worktree and the survival of an unrelated dirty path (E-06).

ALL OF IT IS GATED ON OQ-03, which asks whether this plan should proceed at all given the cost F-6 now states honestly and the promised feature E-04 may have to withdraw. There is no useful subset to execute in the meantime: E-01 alone is a table, and every other item needs the split that OQ-03's answer authorizes. E-02 AND E-11 ARE ADDITIONALLY GATED ON OQ-04 (added at review round 2), which decides the sweep lane's freshness policy and therefore whether there is one long-lived lane to tear down or one per review.

THE COST IS HIGHER AGAIN THAN ROUND 1 RECORDED, and that matters to OQ-03's first half rather than only to sequencing. Round 1 raised the estimate to seven `not is_review` sites per host with two needing surgical splits, plus three behavioral sites and a nine-call-site signature change. Round 2 adds: a review has no reachable teardown at all, so one must be built and it must classify before destroying (E-11, F-12); the prescribed signature change breaks a shipped contract test whose docstring forbids exactly it, so the route must be chosen deliberately (F-13); and the one-lane design needs a lane-refresh mechanism that does not exist anywhere in the package (F-14). Anyone re-deciding OQ-03's first half should re-decide it against THIS cost, not round 1's.

## Deferred / out of scope (with reason)

- The lifecycle exclusion at `:6572` (post-turn validation of an executed disposition), and the genuinely lifecycle CALLS inside the two blocks E-01 splits (`driver_begin` at `:6167`/`:6169`, `driver_finalize` at `:6728`, the suite check at `:6669`). Correctly review-exempt: a review performs no begin/finalize transition and produces no executed disposition to validate. E-01 records these rather than changing them. NOTE the plan originally listed `:6151` and `:6665` here too; F-7 shows that was an error, and they are now in scope as splits.
- Making isolation mandatory for all actions. That is the orchestrator's OQ-01 and a separate judgement; this plan changes the DEFAULT behavior for reviews only and leaves `--no-isolate-worktree` working.
- Changing what a review produces, or the review record format. Out of scope entirely.
- REMOVING THE `is_review` OVERLOAD ITSELF. Now a stronger candidate for its own plan than when this one was authored, because F-7 shows the overload actively misleads a reader into the wrong classification. Still out of scope here: it would touch fourteen sites across two hosts with no behavior change, and mixing a pure refactor into a behavior change makes both harder to review. Worth raising with the maintainer separately.

## Scope check

- Over-scope: none.
- Under-scope, corrected at review: `agent_workflows/runner_shared.py` and `tests/test_runner_shared.py` were MISSING from `Scope-Paths` although E-03 changes `integrate_lane_branch`'s signature and `tests/test_runner_shared.py` holds three of its nine call sites. Both ADDED. Without them E-03's central edit would have been an undeclared out-of-scope change requiring a `--scope-reason` at finalize.
- Under-scope: the plan's site census was six per host and is seven, and three further behavioral sites (collection, disposition, attachment localization) were unaddressed. Now covered by E-01's added row, E-08 and E-09. This is the largest single correction to the plan's scope and the reason `Highest E allocated` moved 06 -> 09.
- Under-scope, ADDED AT REVIEW ROUND 2: the sweep lane had no TEARDOWN owner, and F-12 shows none is reachable for a review at any nesting (the sole call site per host is gated on `driver_finalize`'s return code). New E-11 owns it, moving `Highest E allocated` 10 -> 11. No new `Scope-Paths` entry is required: E-11 lives in the same two runner files already declared, and it must REUSE `runner_shared.teardown_isolation_worktree` and the existing lane-reclaim classifier rather than adding a second one.
- Scope note on E-03's route, ADDED AT REVIEW ROUND 2 (F-13): `tests/test_runner_shared.py` is already declared, which is fortunate because that file holds the contract test the prescribed signature change breaks. If route (b) is taken (amend `:787`), that edit is IN scope and needs no `--scope-reason`; if route (a) is taken (bind the literal in each wrapper), that file may end up UNMODIFIED, which then needs a `--scope-ack` at finalize. Either way it is declared, so nothing is discovered late.
- This plan still does not remove the `is_review` overload; see the deferred section for why that is now a stronger separate candidate.

## Required tests / validation

- The three-review regression of E-06: all three complete, MAIN's status EQUAL to its pre-run value (not empty, since the test deliberately dirties an unrelated tracked path), each review's two files in main, no leaked worktree, and the session behavior OQ-03 selected.
- A test proving a review's plan edit and review record arrive TOGETHER (one merge), and that a failed merge leaves neither in main and the plan unrevised.
- A test proving the lane-relative plan path and the in-lane statement are present in a review prompt AND that the `--file` attachments resolve inside the lane, which together are the direct regression for F-4 (the prompt half alone was the measured half-fix).
- A test proving `--full-auto` still promotes a cleanly reviewed plan after isolation, that it reads the POST-merge plan, and that it still writes `auto-approved` rather than human `approved` (E-05).
- A test proving the review DISPOSITION is derived from the lane's copy of the plan, including the case where the review set `approved`: pre-change that case is recorded merely `reviewed`, so the test must fail against pre-change code (E-09).
- A test proving the remaining lifecycle exclusions still hold after the two splits: a review performs no `driver_begin`, no `driver_finalize`, and no suite check. This is the direct regression for the hazard E-01 exists to prevent, and it must fail if a split is done by deleting `not is_review` wholesale.
- A test proving revalidation STILL RUNS for execute turns after E-03's widening, so the shared gate was not weakened for its original caller.
- THE THREE AST STRUCTURAL TESTS ON `integrate_lane_branch` MUST BE RUN AND PASTED, not merely the behavioral ones (F-13): `tests/test_runner_shared.py:787` (each wrapper keeps its ORIGINAL signature), `:836` (`host_label` has no default) and `:851` (each runner binds its own label). The first FAILS against the signature change E-03 originally prescribed, measured at review, so its result is the direct evidence that the chosen route was the compatible one.
- A test proving the sweep lane is REMOVED after a completed sweep and PRESERVED when a review's merge conflicts (E-11), since a review has no reachable teardown today and an unconditional one would violate `teardown_isolation_worktree`'s own no-work precondition.
- A test exercising the STALE-LANE case OQ-04 rules on (F-14): a sweep in which main advances between reviews, showing whatever freshness policy was chosen actually holds, and showing a lane-versus-main divergence aborts leaving main clean rather than clobbering the peer.
- Both hosts. Full suite run bare (`python3 -m pytest`), with the failure set diffed against a baseline captured from the SAME commit before any edit; paste both counts and the diff. Do not state a baseline from memory: three sibling reviews in this Set each found a plan's claimed baseline to be wrong.

## Spec / documentation sync

- The CLI help at `:7699` and the sweep text at `:7728` both promise a shared review session. If OQ-03 rules that isolation wins, BOTH must be corrected in this plan, because a help text that promises continuity the runner no longer provides is a documented lie and is worse than the lost continuity. If sharing wins, they stay as they are and this plan cannot isolate per-review.
- Spec `7ckptx` (worker lane containment) governs the lane-relative-input requirements this plan extends to a new action type (R2.1's "must ship together" rule is what E-08 turns on, and R5.3's attachment rule is what E-01's `:5467` row turns on). VERIFY BEFORE EXECUTING whether any requirement is phrased so that extending containment to reviews CHANGES its meaning rather than merely widening its population; if so, amend that spec in this plan and add the spec file to `Scope-Paths` first. Note Order 01 of this same Set already proposes amending `7ckptx` R5.4, so check its state before editing to avoid two plans amending one requirement in different directions.
- Isolation for execute turns came from `driverfin-02 (emus4n)`; no requirement found so far mandates that reviews stay unisolated, and that negative result was re-checked at review.

EXECUTED, AND THE ANSWER IS THAT NO SPEC AMENDMENT IS REQUIRED. The verification E-06's spec-sync note demanded was performed by reading every requirement this plan touches:

- BOTH CLI TEXTS STAYED TRUE and were made more specific rather than corrected, because OQ-03's second half resolved in favor of keeping the shared session (see V-04). No documented feature was withdrawn, so the "documented lie" hazard this section names never arose. No `.spec.md` file is in `Scope-Paths` and none was modified, which the finalize scope reconciliation will see as consistent.
- SPEC `7ckptx` IS WIDENED IN POPULATION, NOT CHANGED IN MEANING, which is exactly the distinction this section asks to be checked. Every requirement this plan relies on is phrased over "an isolated turn" or "an isolated worker" (R1.1/R1.3/R1.4, R2.1, R5.1, R5.3, R5.5), never over "an execute turn", so a review becoming isolated makes it a member of an existing population rather than altering what any requirement demands. Concretely: R2.1's must-ship-together rule now BINDS the review path (which is what E-08 turns on) because E-02 made a review's prompt lane-relative; R5.3's attachment rule now binds it for the same reason; R5.5's teardown gate now governs the sweep lane. Each is the requirement applying as written, so amending them would weaken rather than clarify.
- ORDER 01's R5.4 AMENDMENT WAS CHECKED FIRST, as this section directs, to avoid two plans amending one requirement in different directions. `d7qoxv` is EXECUTED and its amendment is already in the spec's history (dated 2026-09-16, splitting R5.4's consequence by path). This plan does not touch R5.4 at all: the pre-launch clean-base guard keeps its existing review exemption, which this plan's own deferred section preserves deliberately.
- ONE HONEST LIMIT, recorded rather than hidden: R5.1a part (iii) requires that a change to a lane's input set be a NEW MANIFEST REVISION rather than an in-place edit. This plan now materializes one revision PER REVIEW in the shared sweep lane, which satisfies that rule as written and was in fact forced by it (a shared `rev-1` overwrote the previous review's manifest and made the lane unretirable; see V-11). But the spec was written for a lane with ONE owner, and "revision" there means "this turn's input set changed", whereas here consecutive revisions belong to DIFFERENT items. The behavior is conforming and the failure mode is closed; the vocabulary is now slightly strained, and a future spec pass may want to say so explicitly. Filed as a backlog item rather than amended here, because changing that requirement's meaning is a contract change this plan has no mandate for.

## Open questions

### OQ-01: Does a review lane reuse `integrate_lane_branch`, or need a narrower merge path?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-13 by the maintainer: WIDEN `integrate_lane_branch` to know about reviews, so there is ONE integration function and a review skips only the revalidation step. E-03 takes that branch.

  THE AUTHOR INITIALLY LEANED THE OTHER WAY (a separate, clearly-named review merge path) and reading the function changed that view; the reversal is recorded so a later reader does not assume the alternative went unconsidered. The argument that decided it: `integrate_lane_branch` (`runner_shared.py:1000-1063`) is four steps, and only ONE is execute-specific. Step 1 is the dirty-overlap check, which Order 02 deletes outright. Step 2 is the merge-and-revalidate gate, the only part a review has no input for. Steps 3 and 4 are the actual merge and they are NOT thin: they carry three pieces of hard-won knowledge that a second implementation would have to duplicate or would get subtly wrong. First, `--ff-only` failing is the EXPECTED "main advanced" case and its output is deliberately discarded so it never reaches the operator-facing reason. Second, conflicted paths must be captured BEFORE `git merge --abort`, because the abort clears the index state they live in. Third, the merge subject carries `host_label` so history attributes to the right driver. That is genuine shared mechanism, and this repository's anti-re-fork discipline applies to it.

  THE LINE THAT MUST HOLD, and it is the whole reason this question was blocking: skip the gate EXPLICITLY, never satisfy it with a fake value. Passing a synthetic "validation passed" into the revalidation gate would be a forged attestation of the same family as a hand-written `- Readiness:`. Skipping revalidation for an action that produces nothing to revalidate is simply true, and it must be stated in the function's signature (an explicit action kind, not an inferred one) and in its docstring, so the contract is declared rather than quietly conditional. An implicit mode is how `dirty_tree_overlap` came to imply an authority its behavior did not have.

### OQ-02: Should a review lane be per-review or one lane for the whole sweep?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM CODE: PER-REVIEW, which is also what the author leaned toward, but the deciding reason is stronger than the independence argument given. The existing machinery is per-ITEM by construction: `allocate_isolation_worktree(repo, item["id6"])` is keyed on the item's id6, and incident `lanesess xd9sll` was CAUSED by a per-SET resource (the session) being paired with per-ITEM worktrees. A one-lane-per-sweep design would re-introduce exactly that mismatch in mirror image, with N reviews sharing one tree, and would additionally require a second allocation path since nothing today allocates per set. So per-review is both the independent choice and the one that reuses shipped mechanism. RESOLVED 2026-09-13 by the maintainer: ONE LANE FOR THE WHOLE SWEEP, and NOT keyed to a Set. Two facts decided it. FIRST, GROUPING DOES NOT MATTER: a review writes only two files, both scoped to the plan under review (measured on `a9510164`: the plan itself plus its review record), so reviews in a shared lane touch DISJOINT paths whether they are siblings in one Set or unrelated plans. There is nothing to collide over, so a per-Set rule would add a distinction that buys nothing. SECOND, ONE LANE IS WHAT MAKES SESSION SHARING SAFE BY CONSTRUCTION, which dissolves OQ-03's second half rather than trading against it: the `xd9sll` incident was N TREES to ONE session, and one tree to one session cannot reproduce it. A single lane also gives the reviewing agent a full checkout, so cross-plan awareness (the thing that caught this Set's own collision with three approved plans) is preserved rather than fragmented across N lanes. ACCEPTED COST, stated plainly: the sweep shares one merge, so a failure strands the batch rather than one item. That is cheap here because a review produces no code and is re-runnable, and it is the only cost this design carries.
  - NOTE THE COUPLING TO OQ-03's SECOND HALF: per-review lanes are precisely what makes a shared session unsafe (F-5). If the maintainer rules that shared session continuity must survive, this answer is reopened, because one lane per sweep is then the only shape in which sharing is defensible. Recorded as `Reversible: yes` for that reason.

### OQ-03: Is this change worth its true cost, and if so, does the shared review session yield to isolation?

- Blocking: yes
- Finding: PR-501, PR-505
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: NOT resolvable from repository evidence, because both halves are judgement calls the repository cannot make and one is irreversible in the direction this plan proposes.
  RESOLVED 2026-09-13 by the maintainer, and BOTH HALVES ARE ANSWERED BY THE ONE-LANE DESIGN OF OQ-02.
  SECOND HALF FIRST, because it is the one that was misstated. THE SHARED SESSION AND ISOLATION DO NOT CONFLICT under one sweep lane, and the author's earlier claim that they "CANNOT COEXIST" was wrong. The recorded cause of `xd9sll` is a MISMATCH OF CARDINALITY, not isolation as such: sessions are keyed per SET (`set_sessions[setid]`, `oc_runipd.py:5394-5395`) while worktrees are allocated per ITEM, so lanes 2..N inherited lane 1's session and its directory binding. One lane for the whole sweep is ONE tree bound to ONE session, which cannot reproduce that. So no documented feature is withdrawn and both CLI help texts (`:7699`, `:7728`) remain TRUE.
  MEASURED WHILE RESOLVING THIS, because the recorded rationale deserved checking rather than repeating: reusing tree A's session with `--dir` pointing at tree B does NOT visibly run in the wrong tree today; it exits 0 with ZERO output, reproducibly, in both plain and `--format json` mode, while a fresh session in the same tree works normally. That is a SILENT NO-OP and is arguably worse than the recorded symptom. It is filed separately as its own defect and is NOT this plan's to fix; recorded here so the next reader does not re-derive it or trust the older explanation.
  ALSO ESTABLISHED: today every isolated execute turn ALREADY gets a fresh session (`session = None if (fresh_session or isolated_turn or is_rotation)`, `:5405`), verified on two 2026-09-13 runs which recorded 2 sessions for 2 turns and 3 for 3, with `set_sessions` empty. So reviews are the LAST remaining consumer of session sharing, which is why this question only arises here.
  FIRST HALF, THE COST. The benefit was mis-stated by the author as UNIFORMITY, which understated it; the maintainer's actual reason is CONCURRENCY, and it is stronger: a review in progress writes to the shared checkout and can strand plan execution by another agent or runner. The cost is real and larger than first scoped (the census is 7 `not is_review` sites plus 4 positive uses in oc, 6 in agy, two needing surgical splitting, plus the collection/disposition/attachment sites), and it is accepted on that basis. One sweep lane also REDUCES the cost relative to per-review lanes: one allocation, one merge, one session.
  - FIRST HALF, THE COST. The plan was authored as "flip three tree-related guards"; review measured it as seven `not is_review` sites per host of which TWO need surgical SPLITTING (their conditions are lifecycle but their bodies contain the worktree allocation, the merge-back and the teardown -- F-7), plus three further behavioral sites the census missed (collection, disposition, attachment localization -- F-8), plus a shared function signature with nine call sites (E-03). Meanwhile the plan's own F-6 honestly states the benefit is UNIFORMITY rather than protecting expensive output, since a review is cheap to re-run. That is a materially different cost-benefit ratio from the one the plan was approved-in-principle against, and deferring the whole plan is a legitimate answer.
  - SECOND HALF, THE PROMISED FEATURE. If it does proceed, the shared review session and per-review isolation CANNOT COEXIST. `run_opencode` forces a fresh session for any isolated turn, and the recorded reason is incident `lanesess xd9sll`, in which an opencode session's own directory binding overrode `--dir` and four consecutive lanes were lost. The CLI help promises sharing "for continuity" at `:7699` and the sweep repeats it at `:7728`. So either continuity is withdrawn and both texts corrected, or isolation is abandoned for reviews, or the sweep moves to one lane for all reviews (reopening OQ-02). Withdrawing a documented feature is a user-facing contract change, which AGENTS.md reserves to the maintainer.
  - WHY IT BLOCKS EVERYTHING RATHER THAN PART: E-01 alone produces a table, and every other item requires the split that this answer authorizes. There is no useful subset to run in the meantime, which is why no E-item is exempted here (unlike sibling Orders 02 and 04, where an ungated remainder existed).

### OQ-04: The sweep lane goes stale as it merges. Refresh it, re-allocate per review, or bound the staleness?

- Blocking: yes
- Finding: PR-513
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: NOT resolvable from repository evidence, because it revisits OQ-02's maintainer ruling on the strength of a measurement that ruling did not have, and the three options trade different things the repository cannot rank.
  RESOLVED 2026-09-13 by the maintainer: OPTION (a), REFRESH THE SWEEP LANE. One lane and one session are kept; the lane is fast-forwarded to main after each review merges, so every review reads a current tree instead of a snapshot frozen at sweep start.
  MEASURED BOTH HALVES, so the ruling rests on observation. THE DEFECT: a lane cut at sweep start and never refreshed went stale immediately. After two reviews merged, main held the THIRD version of a file while the lane still held the FIRST, and a plan corrected on main mid-sweep read as its PRE-correction self inside the lane. THE FIX: a single `git merge --ff-only main` inside the lane took it from the first version to the third in one step, so the remedy is one command and needs no new mechanism beyond a place to call it.
  A NOTE ON PROVENANCE, recorded because the earlier text overstated it. OQ-02's ruling was the maintainer's answer to whether the reviews should SHARE a lane; the supporting reason about cross-plan awareness was the AUTHOR'S rationale, not the maintainer's. So this question does not overturn a maintainer decision, it repairs an author's argument that measurement showed to be false as written. Sharing is retained; only the freshness defect is fixed.
  CONSEQUENCES FOR THIS PLAN. Add the refresh to the sweep loop, after a review's merge lands and before the next review is dispatched. Two things the executor must settle rather than assume: what to do when the lane holds UNCOMMITTED work at refresh time (a review's own in-flight edits must not be discarded by a refresh), and that the refresh must be `--ff-only` so it REFUSES rather than rewriting history if the lane has diverged. Not a data-loss risk either way: a diverged file yields `CONFLICT (content)`, the merge aborts, and main is left clean with a peer's bytes intact.
  WHAT WAS MEASURED (F-14). One sweep lane is allocated once at sweep start and cut at `HEAD` (`worktree_lease.py:554`); every review then merges to main, advancing it, while the lane keeps its original base, and no refresh mechanism exists anywhere in the package (grep for `rebase`: no hits). Measured in a scratch repo: after two reviews merged, the lane still read `peer v1` while main read `peer v2`, and a plan a peer corrected ON MAIN mid-sweep read its PRE-correction text inside the lane. In a nine-item sweep, review 9 reads a tree eight merges behind.
  WHY IT REACHES A RULING RATHER THAN AN IMPLEMENTATION DETAIL. OQ-02 chose one sweep lane over per-review lanes, and one of its two stated reasons was that a single lane "gives the reviewing agent a full checkout, so cross-plan awareness (the thing that caught this Set's own collision with three approved plans) is preserved rather than fragmented across N lanes". The measurement shows that checkout is a snapshot frozen at sweep start, so the awareness DEGRADES monotonically instead of being preserved. This Set is the instance: the review of sibling N would read sibling texts as they were before reviews 1..N-1 merged, missing the very corrections F-9 credits to cross-plan awareness. OQ-02's other reason (reviews touch disjoint paths, nothing to collide over) is TRUE and unaffected, because the collision measured is lane-versus-MAIN.
  THE OPTIONS, each with its real cost. (a) REFRESH THE LANE between reviews, fast-forwarding it to main after each merge. Keeps one lane and one session, restores freshness, and is the only option that delivers what OQ-02 promised; costs a new helper, since none exists, plus a decision about what to do when the lane holds uncommitted work at refresh time. (b) RE-ALLOCATE PER REVIEW, which is the shape OQ-02 explicitly rejected and which reopens the session question, since per-item lanes plus one session is the `xd9sll` cardinality mismatch (F-5); it does reuse shipped mechanism exactly, being what `allocate_isolation_worktree` is built for. (c) ACCEPT AND BOUND the staleness, stating the maximum sweep length for which it is tolerable and recording a stranded review as an expected outcome; costs nothing to build and makes the failure mode explicit, but leaves a design whose failure rate rises with every item.
  NOT A DATA-LOSS RISK, stated so the question is not over-weighted: a diverged plan produces `CONFLICT (content)`, `integrate_lane_branch` aborts, and main is left clean with the peer's bytes intact (measured). The cost of getting this wrong is a stranded review, not a destroyed edit.
  RECOMMENDATION, offered because the workflow requires one and not as authority: (a), because it is the only option that preserves the reason OQ-02 was decided as it was, and because a lane fast-forward is a small, testable addition next to the machinery already here.
  E-02 MUST NOT BE STARTED before this is answered, and E-11's teardown shape depends on it too (whether there is one long-lived lane to remove or one per review). Note the whole plan was ALREADY gated on OQ-03 and remains so; this question does not add a new gate so much as a second thing the same gate must decide.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the full classification table for BOTH hosts (seven sites each, or six plus a stated not-applicable), each row carrying its verdict, its reason, AND the enclosing block that justifies the verdict. For the two tree-critical rows (`:6151`, `:6665` and their agy twins) paste the enclosing-block evidence explicitly, since misreading those is the defect this item exists to prevent. Then confirm from the final diff that the lifecycle CALLS inside the split blocks (`driver_begin`, `driver_finalize`, the suite check) are still review-exempt, and that `:6572` is untouched.
  - Observed evidence: the full re-derived census for BOTH hosts is below, machine-generated at execution HEAD `c146cdb3`, plus the row-by-row table and the test proving the lifecycle calls stay review-exempt.

    LINE NUMBERS FIRST, because every one in the review's table has moved. The review rounds ran before Orders 01 to 04 of this Set executed, so the table above cites a HEAD that no longer exists. This census was re-derived at execution HEAD `c146cdb3` by the prescribed method (AST-walk each site's enclosing `if` chain and list what the block CONTAINS). THE REVIEW'S CLASSIFICATION WAS CONFIRMED CORRECT IN SUBSTANCE ON EVERY ROW.

    THE POST-CHANGE CENSUS, machine-generated (`ast` walk of every `if` whose test mentions `is_review`, printing its span, its enclosing chain and the tracked calls its body contains):

    ```text
    ====================================================================================================
    agent_workflows/oc_runipd.py

      L6293  not is_review and (not log_suffix) and state.get('runbook') and Path(state['runbook']).exists()
            span 6293-6308
            enclosing: def[6125:6822] run_opencode
            CONTAINS: localize_attachment

      L6954  is_review
            span 6954-6959
            enclosing: def[6936:8601] execute_item
            CONTAINS: build_prompt, build_review_prompt

      L7059  self_finalize and (not is_review)
            span 7059-7136
            enclosing: def[6936:8601] execute_item
            CONTAINS: evaluate_clean_base_for_launch

      L7155  is_review and isolate
            span 7155-7217
            enclosing: def[6936:8601] execute_item
            CONTAINS: acquire_review_sweep_lane

      L7219  self_finalize and (not is_review)
            span 7219-7332
            enclosing: def[6936:8601] execute_item
            CONTAINS: allocate_isolation_worktree, driver_begin

      L7354  work_dir and (not is_review)
            span 7354-7426
            enclosing: def[6936:8601] execute_item
            CONTAINS: build_prompt, materialize_lane_inputs

      L7441  work_dir and is_review
            span 7441-7483
            enclosing: def[6936:8601] execute_item
            CONTAINS: build_review_prompt, materialize_lane_inputs

      L7695  work_dir and (not is_review or runner_shared.turn_runs_in_review_sweep_lane(state, work_dir))
            span 7695-7729
            enclosing: def[6936:8601] execute_item
            CONTAINS: collect_lane_submissions

      L7762  not is_review and disposition in ('executed', 'substantially-complete') and validate
            span 7762-7846
            enclosing: def[6936:8601] execute_item
            CONTAINS: (none of the tracked calls)

      L7867  not is_review
            span 7867-7983
            enclosing: def[6936:8601] execute_item
            CONTAINS: (none of the tracked calls)

      L8042  is_review and wt_handle is not None
            span 8042-8167
            enclosing: def[6936:8601] execute_item
            CONTAINS: integrate_review_lane_branch

      L8493  wt_handle is not None and (not is_review) and (item.get('status') != 'executed')
            span 8493-8516
            enclosing: def[6936:8601] execute_item
            CONTAINS: record_lane_preserved

      L8535  is_review and disposition in ('reviewed', 'approved') and full_auto
            span 8535-8563
            enclosing: def[6936:8601] execute_item
            CONTAINS: set_plan_approved
    ====================================================================================================
    agent_workflows/agy_runipd.py

      L3582  is_review
            span 3582-3587
            enclosing: def[3565:4990] execute_item
            CONTAINS: build_prompt, build_review_prompt

      L3702  self_finalize and (not is_review)
            span 3702-3766
            enclosing: def[3565:4990] execute_item
            CONTAINS: evaluate_clean_base_for_launch

      L3778  is_review and isolate
            span 3778-3836
            enclosing: def[3565:4990] execute_item
            CONTAINS: acquire_review_sweep_lane

      L3838  self_finalize and (not is_review)
            span 3838-3948
            enclosing: def[3565:4990] execute_item
            CONTAINS: allocate_isolation_worktree, driver_begin

      L3956  work_dir and (not is_review)
            span 3956-3979
            enclosing: def[3565:4990] execute_item
            CONTAINS: build_prompt

      L3987  work_dir and is_review
            span 3987-4018
            enclosing: def[3565:4990] execute_item
            CONTAINS: build_review_prompt, materialize_lane_inputs

      L4187  work_dir and (not is_review or runner_shared.turn_runs_in_review_sweep_lane(state, work_dir))
            span 4187-4223
            enclosing: def[3565:4990] execute_item
            CONTAINS: collect_lane_submissions

      L4238  not is_review and disposition in ('executed', 'substantially-complete') and (not no_verify)
            span 4238-4314
            enclosing: def[3565:4990] execute_item
            CONTAINS: (none of the tracked calls)

      L4328  not is_review
            span 4328-4422
            enclosing: def[3565:4990] execute_item
            CONTAINS: (none of the tracked calls)

      L4474  is_review and wt_handle is not None
            span 4474-4595
            enclosing: def[3565:4990] execute_item
            CONTAINS: integrate_review_lane_branch

      L4875  wt_handle is not None and (not is_review) and (item.get('status') != 'executed')
            span 4875-4897
            enclosing: def[3565:4990] execute_item
            CONTAINS: record_lane_preserved

      L4922  is_review and disposition in ('reviewed', 'approved') and full_auto
            span 4922-4951
            enclosing: def[3565:4990] execute_item
            CONTAINS: set_plan_approved
    ```

    THE TABLE, ROW BY ROW, with the review's original citation in brackets. VERDICT KEY: TREE = changed; SPLIT = a new sibling branch was added and the original left intact; LIFECYCLE = left alone; N/A = no such site on this host.

    | host | site now | was | verdict | reason, from the block's CONTENTS | what stays exempt |
    |---|---|---|---|---|---|
    | oc | `:6293` | `:5467` | TREE, unchanged CONDITION | Contains `localize_attachment`. It needed NO edit to serve a review: `lane_root_for_attachments` derives from `work_dir`, which is now set for a review, so the plan attachment localizes into the lane automatically. The surviving `not is_review` governs only the RUNBOOK attachment, which is correct for a reason of substance: a review turn is never handed the runbook, its whole instruction being the slash command. | the runbook exclusion |
    | oc | `:7059` | `:6122` | LIFECYCLE-adjacent, left | Contains ONLY `evaluate_clean_base_for_launch`. Left as-is: this is the pre-launch clean-base gate, whose exemption for reviews is pre-existing and out of this plan's scope (the plan's own deferred section keeps it). | the whole block |
    | oc | `:7155` | (new) | **SPLIT, the tree-critical row** | The review's ALLOCATION, hoisted OUT of the self-finalize block into its own branch placed BEFORE it. Contains `acquire_review_sweep_lane` and nothing else. | n/a (new) |
    | oc | `:7219` | `:6151` | **SPLIT, tree-critical, ORIGINAL LEFT INTACT** | AST-verified it still CONTAINS `allocate_isolation_worktree` AND `driver_begin`. `not is_review` was NOT deleted here, which is the forbidden move: deleting it would make a review call `driver_begin` and claim execution authority. The allocation a review needs was hoisted to `:7155` instead. | `driver_begin`, and the per-item `allocate_isolation_worktree` |
    | oc | `:7354` | `:6279` | TREE, unchanged; twin added | Contains `build_prompt` + `materialize_lane_inputs`. Left as the EXECUTOR's prompt rebuild; the review's rebuild is a separate branch at `:7441`, because the two builds are not interchangeable (one is `build_prompt`, the other the slash command). | n/a |
    | oc | `:7441` | (new) | **SPLIT, the review's prompt rebuild** | Contains `build_review_prompt` + `materialize_lane_inputs`. Both halves of the `y6mfgo` lesson: lane-resolved plan path AND the in-lane statement. | n/a (new) |
    | oc | `:7695` | `:6519` | TREE, CONDITION WIDENED | Contains `collect_lane_submissions`. Widened to include a sweep-lane review (E-08); see V-08 for the evidence that a review submits nothing and why the call is still correct. | n/a |
    | oc | `:7762` | `:6572` | LIFECYCLE, **UNTOUCHED** | Post-turn validation of an executed disposition. A review produces no executed disposition to validate. This is the one site the review's original classification got right on the leave side, and it is byte-identical in the diff. | the whole block |
    | oc | `:7867` | (not in the census) | LIFECYCLE, left | The defect-report validate/re-ask block. Not a TREE decision; left alone. | the whole block |
    | oc | `:8042` | `:6665` | **SPLIT, tree-critical, ORIGINAL LEFT INTACT** | `integration_gate_relevant` still carries `not is_review`, and that is deliberate: it gates the SUITE CHECK, `driver_finalize` AND the merge at once, so deleting the term (the tempting one-line fix) would make a review attempt a terminal transition. The MERGE a review needs is this separate branch, which contains `integrate_review_lane_branch` and nothing else. | `run_suite_check`, `driver_finalize`, `process_backlog_close` |
    | oc | `:8493` | (not in the census) | TREE, **NEWLY EXCLUDES A REVIEW** | Contains `record_lane_preserved`. Its condition is `status != "executed"`, and a successful review's status is `reviewed`/`approved`, so WITHOUT the new `not is_review` term every review - including one that integrated perfectly - would write `preserved_*` claiming its work "was never integrated". Those fields are read by the deferral re-attempt and the lane reclaimer, so a clean sweep would advertise a stranded lane holding nothing. Found by this plan's own regression. | n/a |
    | oc | `:8535` | `:6926` | LIFECYCLE, ordering CONFIRMED | Contains `set_plan_approved`. Already positioned AFTER the merge (E-05); no move needed, and that was verified structurally rather than assumed. | n/a |
    | agy | `:3702` | `:3262` | LIFECYCLE-adjacent, left | twin of oc `:7059`. | the whole block |
    | agy | `:3778` | (new) | **SPLIT** | twin of oc `:7155`. | n/a (new) |
    | agy | `:3838` | `:3291` | **SPLIT, ORIGINAL LEFT INTACT** | twin of oc `:7219`: still contains `allocate_isolation_worktree` AND `driver_begin`. | `driver_begin` |
    | agy | `:3956` | `:3409` | TREE, unchanged | twin of oc `:7354`. Note it contains `build_prompt` but NOT `materialize_lane_inputs`, which is PRE-EXISTING and correct: agy passes its prompt inline and has no `--file` surface to localize. | n/a |
    | agy | `:3987` | (new) | **SPLIT** | twin of oc `:7441`. | n/a (new) |
    | agy | `:4187` | `:3584` | TREE, WIDENED | twin of oc `:7695`. | n/a |
    | agy | `:4238` | `:3629` | LIFECYCLE, UNTOUCHED | twin of oc `:7762`. | the whole block |
    | agy | `:4474` | `:3720` | **SPLIT, ORIGINAL LEFT INTACT** | twin of oc `:8042`. | `run_suite_check`, `driver_finalize` |
    | agy | `:4875` | (not in the census) | TREE, NEWLY EXCLUDES A REVIEW | twin of oc `:8493`. | n/a |
    | agy | `:4922` | `:3873` | LIFECYCLE, ordering CONFIRMED | twin of oc `:8535`. | n/a |
    | agy | `--file` localization | `:5467`'s twin | **N/A, with the reason stated** | agy has NO `--file` surface at all: it passes its prompt inline to `run_agy_turn`. There is nothing to localize, so this row is legitimately not-applicable rather than missing. | n/a |

    THE LIFECYCLE CALLS INSIDE THE SPLIT BLOCKS ARE STILL REVIEW-EXEMPT, confirmed from the CENSUS ABOVE rather than by reading the diff: `driver_begin` appears only inside `self_finalize and (not is_review)` on both hosts, and `run_suite_check`/`driver_finalize` only under `integration_gate_relevant`, which still carries `not is_review`. Asserted as a TEST too, not only observed: `tests/test_review_lane_isolation.py::TheLifecycleExclusionsStillHold::test_a_review_performs_no_begin_no_finalize_and_no_suite_check` patches all three on BOTH hosts, runs a real review turn, and asserts the call set is EMPTY - so it fails loudly if a future change implements a split by deleting `not is_review` wholesale.

    ```text
    tests/test_review_lane_isolation.py::TheLifecycleExclusionsStillHold::test_a_review_performs_no_begin_no_finalize_and_no_suite_check PASSED
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste MAIN's `git status --porcelain` sampled DURING a review sweep (not only after), showing it empty at every sample. Paste proof that ONE lane served every review in the sweep (one allocation, one worktree path across all turns), not N lanes. Paste the review prompt showing the lane-relative plan path and the explicit in-lane statement, which is the `y6mfgo` regression.
  - Observed evidence: a live three-review sweep with MAIN's porcelain sampled DURING each turn and EQUAL to its pre-run value, proof that ONE lane served all three, and the prompt showing both halves of the `y6mfgo` regression, all below.

    ONE CORRECTION TO THE REQUIRED EVIDENCE, and it is the review's own (recorded at E-06): "showing it empty at every sample" is the WRONG assertion and is deliberately not what is pasted. The fixture leaves a peer's UNCOMMITTED edit to a tracked file, so an EMPTY porcelain would mean the run destroyed that edit. The property wanted is EQUALITY WITH THE PRE-RUN STATUS, which is what is shown.

    A LIVE THREE-REVIEW SWEEP, `oc` host, sampling MAIN's porcelain INSIDE each turn (not only after):

    ```text
    PRE-RUN  main porcelain: 'M PEER.md'
    IPD 01/3 v02001  set=demo  action=review  attempt 1
      review sweep lane aw/lane/review-sweep-run-v02 at .../repo/.aw/worktrees/review-sweep-run-v02
      DURING v02001 main porcelain: 'M PEER.md'  (lane=review-sweep-run-v02)
      review v02001 integrated to main (fast-forward integrated to main)
    IPD 01/3 v02001 (review) -> reviewed  (exit 0)

    IPD 02/3 v02002  set=demo  action=review  attempt 1
      review sweep lane aw/lane/review-sweep-run-v02 at .../repo/.aw/worktrees/review-sweep-run-v02 (the sweep lane is already at main; nothing to refresh)
      DURING v02002 main porcelain: 'M PEER.md'  (lane=review-sweep-run-v02)
      review v02002 integrated to main (fast-forward integrated to main)
    IPD 02/3 v02002 (review) -> reviewed  (exit 0)

    IPD 03/3 v02003  set=demo  action=review  attempt 1
      review sweep lane aw/lane/review-sweep-run-v02 at .../repo/.aw/worktrees/review-sweep-run-v02 (the sweep lane is already at main; nothing to refresh)
      DURING v02003 main porcelain: 'M PEER.md'  (lane=review-sweep-run-v02)
      review v02003 integrated to main (fast-forward integrated to main)
    IPD 03/3 v02003 (review) -> reviewed  (exit 0)

    POST-RUN main porcelain: 'M PEER.md'
    EQUAL to pre-run: True
    PEER.md bytes intact: True
    ```

    ONE LANE SERVED EVERY REVIEW, proved by collecting the `work_dir` each turn actually received and taking the set:

    ```text
    ONE LANE served every review: True {'.../repo/.aw/worktrees/review-sweep-run-v02'}
    sweep session: ses_sweep | set_sessions: {}
    ```

    Note the operator-facing line differs between turn 1 and turns 2-3, which is the allocate-then-refresh seam: turn 1 says nothing extra (a fresh lane is current by construction) and each later turn reports the refresh outcome.

    THE PROMPT, showing BOTH halves of the `y6mfgo` regression. The command line names the LANE-RELATIVE path (no main-checkout path anywhere on it), and the in-lane statement follows on its own lines, so the slash command's `$ARGUMENTS` is unaffected:

    ```text
    /plan-review .aw/records/plans/pending/20260913-demo-01-v02001-x.ipd.md


    ## Work here

    You are running in an ISOLATED GIT WORKTREE (a "lane"), not the main checkout:

        .../repo/.aw/worktrees/review-sweep-run-v02

    That directory is your COMPLETE authorized workspace and it is your working directory. It is a
    full checkout of this repository on its own branch, so the whole tree you need is already there.
    Do EVERY edit, test run, and commit inside it, and write every path this prompt gives you exactly
    as given: they are relative to that directory.

    Do NOT read or write the main checkout, and do NOT climb out with a relative path such as
    `../../../<file>`. If you need a repository file, use the copy inside your workspace.
    ```

    THE FRESHNESS POLICY (OQ-04 option (a)) IS IMPLEMENTED AND TESTED, including both refusals, which is what keeps it from silently overwriting a review's in-flight work:

    ```text
    tests/test_review_lane_isolation.py::TheSweepLaneRefreshPolicy::test_the_lane_is_FAST_FORWARDED_to_main_between_reviews PASSED
    tests/test_review_lane_isolation.py::TheSweepLaneRefreshPolicy::test_an_ALREADY_CURRENT_lane_is_a_no_op_and_says_so PASSED
    tests/test_review_lane_isolation.py::TheSweepLaneRefreshPolicy::test_a_DIRTY_lane_is_left_EXACTLY_as_it_is PASSED
    tests/test_review_lane_isolation.py::TheSweepLaneRefreshPolicy::test_a_DIVERGED_lane_REFUSES_rather_than_rewriting_history PASSED
    ```

    The staleness defect F-14 measured is directly closed: the refresh test cuts a lane, advances MAIN, and asserts the lane then reads main's CURRENT bytes (`peer v2`) rather than its sweep-start snapshot (`peer v1`).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste the merge commit's `--name-status` showing both the plan edit and the review record in ONE merge. Paste a forced merge-failure case showing NEITHER file in main and the plan still unrevised. Paste the widened signature and docstring proving the action kind is an EXPLICIT parameter with NO DEFAULT (per the `host_label` precedent) and that the skip is stated, then paste a `grep` of the review path showing NO synthetic validation value is constructed or passed to the gate. Paste an execute-path test proving revalidation still runs for execute turns. Finally, enumerate all nine call sites and show each was updated.
  - Observed evidence: the merge's `--name-status` with both files, the forced-failure case, the no-default signature, the structural proof that no synthetic validation value can be passed, and the three AST contract tests green, all below.

    BOTH FILES IN ONE MERGE, from the live sweep (the last review's landing on MAIN):

    ```text
    $ git show --name-status --oneline -1 HEAD
    e6eb2a1 review(v02003)
    M	.aw/records/plans/pending/20260913-demo-03-v02003-x.ipd.md
    A	.aw/records/reviews/20260913-v02003-01-v02003-x.review.md
    ```

    That is exactly the two-file shape the review measured on commit `a9510164`: the plan (modified) plus its review record (added), and nothing else.

    THE FORCED FAILURE CASE lands NEITHER file and leaves the peer's bytes intact, asserted as a test:

    ```text
    tests/test_review_lane_isolation.py::TheReviewMergeIsExplicitAndCarriesBothFiles::test_a_FAILED_merge_lands_NEITHER_file_and_leaves_the_plan_unrevised PASSED
    ```

    It builds a real divergence (the lane sets `reviewed`, MAIN commits a different change to the SAME plan), then asserts: the integration reports NOT landed, MAIN's copy is byte-identical to the peer's version, the review record is ABSENT from main, and the porcelain holds no `UU` entry - so the abort left no markers and no partial merge.

    THE SIGNATURE, with NO DEFAULT, following the `host_label` precedent:

    ```python
    def integrate_lane_branch(
        repo: Path,
        handle: Any,
        id6: str,
        validation_runner: Any,
        *,
        host_label: str,
        run_checked: Callable[..., str],
        action_kind: str,
    ) -> tuple[bool, str, str]:
    ```

    Asserted mechanically, not merely pasted:

    ```text
    tests/test_review_lane_isolation.py::TheReviewMergeIsExplicitAndCarriesBothFiles::test_the_action_kind_has_NO_DEFAULT_in_the_shared_function PASSED
    tests/test_review_lane_isolation.py::TheReviewMergeIsExplicitAndCarriesBothFiles::test_an_unrecognized_action_kind_is_REFUSED_not_coerced PASSED
    ```

    The second is the stronger half: an unrecognized kind raises `DriverError` rather than falling through to whichever branch happens to be first, so a typo cannot silently select a behavior.

    NO SYNTHETIC VALIDATION VALUE IS CONSTRUCTED OR PASSED, and this is proved STRUCTURALLY rather than by grep, which is a stronger claim: the review path's wrapper takes NO `validation_runner` PARAMETER AT ALL, so a caller cannot supply one even by mistake, and it binds `None`.

    ```python
    def integrate_review_lane_branch(repo: Path, handle: Any, id6: str) -> tuple[bool, str, str]:
        return runner_shared.integrate_lane_branch(
            repo, handle, id6, None,
            host_label="aw oc run", run_checked=run_checked,
            action_kind=runner_shared.INTEGRATION_ACTION_REVIEW,
        )
    ```

    ```text
    tests/test_review_lane_isolation.py::TheReviewMergeIsExplicitAndCarriesBothFiles::test_the_review_path_constructs_NO_synthetic_validation_value PASSED
    ```

    That test AST-asserts, on BOTH hosts, that the wrapper's positional parameters are exactly `["repo","handle","id6"]`, that it binds `action_kind=runner_shared.INTEGRATION_ACTION_REVIEW`, and that its fourth positional argument to the shared function is literally `None`. In the shared body, `execute_merge_and_revalidate_gate` is called ONLY under `if action_kind == INTEGRATION_ACTION_EXECUTE:`, so for a review the gate is not called, no `IntegrationGateResult` is constructed, and `validation_runner` is never touched.

    REVALIDATION STILL RUNS FOR AN EXECUTE TURN, which is the "did you weaken the shared gate for its original caller" check:

    ```text
    tests/test_review_lane_isolation.py::TheReviewMergeIsExplicitAndCarriesBothFiles::test_revalidation_STILL_RUNS_for_an_execute_turn PASSED
    ```

    THE CALL SITES. The review's census of nine was correct for the SHAPE it prescribed, but route (a) means the WRAPPERS absorb the new parameter, so the actual set is smaller and no production call site changed. Complete enumeration at execution HEAD:

    | # | site | change |
    |---|---|---|
    | 1 | `runner_shared.integrate_lane_branch` (the definition) | gained `action_kind` (no default) |
    | 2 | `oc_runipd.py:2475` (the oc wrapper's call) | binds `action_kind=INTEGRATION_ACTION_EXECUTE` as a literal |
    | 3 | `oc_runipd.py:2502` (the NEW oc review wrapper's call) | binds `action_kind=INTEGRATION_ACTION_REVIEW`, passes `None` |
    | 4 | `agy_runipd.py:1384` (the agy wrapper's call) | binds `EXECUTE` |
    | 5 | `agy_runipd.py:1406` (the NEW agy review wrapper's call) | binds `REVIEW`, passes `None` |
    | 6 | `oc_runipd.py:2553` (`retry_deferred_integrations`) | UNCHANGED: calls the wrapper |
    | 7 | `agy_runipd.py:1455` (`retry_deferred_integrations`) | UNCHANGED: calls the wrapper |
    | 8 | `oc_runipd.py:8254` (the execute integration) | UNCHANGED: calls the wrapper |
    | 9 | `agy_runipd.py:4665` (the execute integration) | UNCHANGED: calls the wrapper |
    | 10 | `tests/test_oc_runipd.py:3507` | UNCHANGED: calls the wrapper |
    | 11 | `tests/test_agy_runipd_cli.py:1016` | UNCHANGED: calls the wrapper |
    | 12 | `tests/test_runner_shared.py:1857`, `:1887`, `:1947`, `:2030` | UNCHANGED: call the wrappers |
    | 13 | `tests/test_runner_shared.py:2102`, `:2125`, `:2156`, `:2184` | UPDATED: these four call the SHARED function directly, so each now passes `action_kind=INTEGRATION_ACTION_EXECUTE` |

    THE THREE AST STRUCTURAL TESTS F-13 NAMED, RUN AND PASTED, which is the direct evidence that route (a) was the compatible one (F-13 measured route (b)'s prescribed shape FAILING the first of these):

    ```text
    $ python3 -m pytest -o addopts="" -k "ORIGINAL_signature or host_label_has_NO_DEFAULT or binds_its_OWN_host_label" tests/test_runner_shared.py -v
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_each_runner_binds_its_OWN_host_label PASSED [ 33%]
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_each_wrapper_keeps_the_ORIGINAL_signature PASSED [ 66%]
    tests/test_runner_shared.py::LaneIntegrationExtractionTests::test_the_host_label_has_NO_DEFAULT_in_the_shared_function PASSED [100%]

    ====================== 3 passed, 120 deselected in 0.59s =======================
    ```

    `test_each_wrapper_keeps_the_ORIGINAL_signature` is green having been left UNTOUCHED, so its stated invariant ("no call site may have had to change, so no wrapper may expose the injected parameter") still holds and needed no amendment.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste evidence that three reviews in one sweep shared ONE session id while running in ONE lane. Paste both CLI help texts (`:7699`, `:7728`) and confirm each is still true. State which route E-04 took, and confirm the `xd9sll` cardinality rule is intact by showing no session is ever passed to a turn running in a different tree.
  - Observed evidence: one session across three reviews in one lane, both CLI texts still true, and the `xd9sll` cardinality rule shown intact with its shipped regression green, all below.

    THE ROUTE: the sweep KEEPS its shared session. Nothing was withdrawn, so neither help text lost a promise; both were instead made MORE specific.

    ONE SESSION, ONE LANE, three reviews, from the live sweep in V-02 (the same run):

    ```text
    ONE LANE served every review: True {'.../repo/.aw/worktrees/review-sweep-run-v02'}
    sweep session: ses_sweep | set_sessions: {}
    ```

    Asserted as a test on BOTH hosts, including the negative half:

    ```text
    tests/test_review_lane_isolation.py::TheSweepRunsInOneLaneAndMainIsUntouched::test_the_sweep_shares_ONE_session_across_the_three_turns PASSED
    ```

    which asserts the sweep session is recorded under its own run-level key AND that `set_sessions` is NOT written - the second being what keeps the carryover closed for a later EXECUTE turn in the same set.

    THE TWO CLI TEXTS, both still TRUE, and now stating the isolation as well:

    ```text
      - reviews:  Every IPD whose next legal action is review, swept in one shared session
                  and one shared isolated worktree (so the sweep never writes to the shared
                  checkout; each review lands as one merge).
    ```

    ```text
    AUTOMATIC STATUS ROUTING:
      - to-review: Runs OpenCode with `/plan-review <plan_path>` to review and improve the plan.
                   All reviews in a run share the same OpenCode session for continuity, and
                   they run in ONE shared isolated worktree, so no review writes to the shared
                   checkout. Each review's plan edit and review record reach the main checkout
                   together, as one merge, after its turn.
    ```

    The agy twin's selector text carries the same addition.

    THE `xd9sll` CARDINALITY RULE IS INTACT, NOT RELAXED, and the correct statement of it is what makes this safe. That incident's recorded cause is a MISMATCH OF CARDINALITY, not isolation as such: sessions were keyed per SET while worktrees were allocated per ITEM, so lanes 2..N inherited lane 1's session and its directory binding overrode `--dir`. The invariant that actually holds is therefore "never carry one session into a DIFFERENT tree". A per-item execute lane is a different tree on every turn and STILL gets a fresh session; the sweep lane is ONE tree for every review in the run and so cannot reproduce the incident.

    The gate is `runner_shared.turn_runs_in_review_sweep_lane`, which answers "is `work_dir` THIS RUN'S SWEEP LANE" by comparing RESOLVED PATHS against the run-level record, so a symlinked or relative spelling of the same tree is the same tree. The pre-existing per-item refusal is untouched, proved by the shipped `xd9sll` regression still passing unmodified:

    ```text
    tests/test_lane_session_isolation.py::LaneSessionIsolationTests::test_isolated_turn_does_not_inherit_a_session PASSED
    tests/test_lane_session_isolation.py::LaneSessionIsolationTests::test_isolated_turn_still_targets_its_own_worktree PASSED
    tests/test_lane_session_isolation.py::LaneSessionIsolationTests::test_non_isolated_turn_still_reuses_the_session PASSED
    tests/test_lane_session_isolation.py::LaneSessionIsolationTests::test_promotion_of_a_lane_session_is_gated_on_work_dir PASSED
    tests/test_lane_session_isolation.py::LaneSessionIsolationTests::test_both_drivers_are_fixed_symmetrically PASSED
    tests/test_lane_session_isolation.py::LaneSessionIsolationTests::test_agy_isolated_lane_clears_session_and_continue PASSED
    ```

    AND THE CONSISTENCY GUARD WAS MIRRORED RATHER THAN DROPPED, which is a risk this item did not name. The set-session path refuses an unexplained session change; moving reviews to their own key would have silently retired that guard for the only action type that still shares a session at all. So the same rule (with the same planned-rotation escape) now applies to the sweep key. `tests/test_session_rotation.py` was updated to assert the rule under BOTH homes rather than being retargeted at whichever one still passed:

    ```text
    tests/test_session_rotation.py::SessionRotationTests::test_oc_runipd_planned_rotation_in_execute_item_does_not_raise PASSED
    tests/test_session_rotation.py::SessionRotationTests::test_oc_runipd_unplanned_session_change_raises_driver_error PASSED
    tests/test_session_rotation.py::SessionRotationTests::test_agy_runipd_rotation_at_limit PASSED
    tests/test_session_rotation.py::SessionRotationTests::test_oc_runipd_default_rotation_after_four_reviews PASSED
    tests/test_session_rotation.py::SessionRotationTests::test_oc_runipd_disabled_rotation_with_zero PASSED
    ```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste a `--full-auto` run where a cleanly reviewed plan is promoted after isolation, showing (a) the plan read was the POST-merge copy, (b) the recorded marker is `auto-approved` and NOT human `approved`, and (c) MAIN's status is unchanged by the promotion write relative to the merge that preceded it. A review that silently fails to auto-approve is the expected symptom of getting this wrong, so a negative case must also be shown to fail loudly rather than silently.
  - Observed evidence: a live `--full-auto` run promoting post-merge, the recorded marker `auto-approved` (never human `approved`), and the peer's file untouched, all below.

    A LIVE `--full-auto` RUN against a repo holding a peer's uncommitted edit:

    ```text
    IPD 01/1 v05001  set=demo  action=review  attempt 1
      review sweep lane aw/lane/review-sweep-run-20260916T235117Z-3472454 at .../repo/.aw/worktrees/review-sweep-...
      review v05001 integrated to main (fast-forward integrated to main)
    IPD 01/1 v05001 (review) -> reviewed  (exit 0)
      IPD v05001 auto-approved (review readiness cleared, NOT human approval); progressing to execution
    IPD 01/1 v05001  set=demo  action=execute  attempt 2
    ```

    (a) THE READ WAS POST-MERGE, shown by the ORDER of the two lines above: `integrated to main` precedes `auto-approved`, and the promotion is what read the plan. The ordering is structural rather than incidental - the review integration branch sits above the auto-approve branch in `execute_item` on both hosts and no path reaches the latter without passing the former - which is also asserted as a test:

    ```text
    tests/test_review_lane_isolation.py::TheReviewDispositionComesFromTheLane::test_the_disposition_is_computed_BEFORE_integration_so_the_lane_is_the_only_answer PASSED
    ```

    (b) THE MARKER IS `auto-approved`, NEVER human `approved`, read off the resulting plan:

    ```text
    PLAN NOW: pending
    STATUS LINE: ['- Status: auto-approved']
    AUTO-APPROVED marker present: True
    by-human present (must be False): False

    history head:
    - 2026-09-16 auto-approved (aw oc run --full-auto): auto-approved by --full-auto: review readiness cleared (not human approval)
    - 2026-09-13 /plan-review (opencode): APPROVE; no defects.
    - 2026-09-13 to-review (test): created.
    ```

    (c) MAIN'S STATE ACROSS THE PROMOTION. The git log shows the review's merge landed as ONE commit and the promotion wrote no second commit, and the peer's uncommitted edit is untouched:

    ```text
    $ git log --oneline -4
    d8f357d review(aw oc run): record the review of v05001
    1a2be60 init

    PEER.md intact: True
    porcelain: 'M .aw/records/plans/pending/20260913-demo-01-v05001-x.ipd.md\n M PEER.md'
    ```

    The plan's own porcelain entry is the promotion's write, which is CORRECT and expected: `set_plan_approved` runs with `--no-commit` by design and its edit is the operator-visible transition, not a stray write. The point E-05 protects is that it happens AFTER the merge, so it can never be mistaken for the review's own output and can never leave the merge half-landed. `PEER.md` is byte-identical, so no co-worker's work was touched.

    THE NEGATIVE CASE FAILS LOUDLY, NOT SILENTLY, and it is the SHIPPED behavior rather than something added here: `is_plan_review_approved` is deliberately fail-closed, and the promotion is wrapped so a failure prints `! Failed to auto-approve IPD <id6>: <reason>` to stderr and leaves the item `reviewed`. So the symptom of getting this wrong is a visible refusal plus an item that plainly did not progress, not a silent skip. The shipped corpus test for that predicate is unchanged and green:

    ```text
    tests/test_oc_runipd.py::AllSelectorAndFullAutoTests::test_full_auto_reviews_approves_and_executes_plan PASSED
    ```
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: paste a review turn's resulting commit `--stat` showing ONLY the plan under review and its review record. Then paste the negative case: a fixture where the review attempts to write a sibling plan, and show either the refusal (shape (a)) or the run record naming that path as out-of-scope (shape (b)). State which shape was chosen and why. Reproduce F-9's exact scenario (an orchestrator review with its children queued in the same run) and show the sibling files are NOT silently rewritten.
  - Observed evidence: shape (b) chosen with its reason, a clean review's two-file commit, and F-9's exact queued-sibling scenario recorded rather than silent, all below.

    THE SHAPE CHOSEN IS (b), PERMIT-AND-RECONCILE, and the reason is the legitimate case E-10 itself names: an ORCHESTRATOR review SHOULD read its children - that is how this Set's own collision with three approved plans was caught - and it may have a real reason to correct a child's text. Refusing would break a case the repository depends on. What F-9 objected to was never that the write happened but that it happened SILENTLY, to an item that had not had its turn. So the write is permitted and NAMED, mirroring what the execute path's own scope reconciliation does and which a review can never reach (`_compute_scope_reconciliation` is called only from `driver_finalize`).

    A CLEAN REVIEW'S COMMIT, exactly two files and nothing else:

    ```text
    $ git show --name-status --oneline -1 HEAD
    e6eb2a1 review(v02003)
    M	.aw/records/plans/pending/20260913-demo-03-v02003-x.ipd.md
    A	.aw/records/reviews/20260913-v02003-01-v02003-x.review.md
    ```

    THE NEGATIVE CASE, which is F-9's EXACT scenario: a review that rewrites a SIBLING's plan while that sibling is still `queued` in the same run. The driver names it, on stderr and in the run record:

    ```text
      ! review v02002 also wrote 2 path(s) outside its own plan and review record: .aw/records/plans/pending/20260913-demo-01-v02001-x.ipd.md, .aw/records/reviews/20260913-v02001-01-v02001-x.review.md
      ! review v02003 also wrote 4 path(s) outside its own plan and review record: .aw/records/plans/pending/20260913-demo-01-v02001-x.ipd.md, .aw/records/plans/pending/20260913-demo-02-v02002-x.ipd.md, .aw/records/reviews/20260913-v02001-01-v02001-x.review.md, .aw/records/reviews/20260913-v02002-01-v02002-x.review.md
    ```

    A NOTE ON WHAT THOSE TWO LINES ACTUALLY SHOW, recorded because it would otherwise read as a defect. Those out-of-scope paths are the EARLIER REVIEWS' OWN FILES, still present on the shared sweep lane's branch, and the classification is computed from `git diff base..branch` - the whole lane branch relative to its allocation base - so review N legitimately sees reviews 1..N-1's landed work in its own delta. That is a consequence of one shared lane (OQ-02's accepted cost shape) rather than a review reaching where it should not, and the report is therefore CONSERVATIVE: it names more than the strict minimum, never less. Naming too much is the safe direction for this gate; naming too little is the defect F-9 records.

    THE HARM ITSELF IS ASSERTED SEPARATELY AND ON BOTH HOSTS, with the queued-sibling subset flagged distinctly from the general out-of-scope set:

    ```text
    tests/test_review_lane_isolation.py::AReviewsWritesAreNamed::test_F9s_EXACT_scenario_is_recorded_rather_than_silent PASSED
    tests/test_review_lane_isolation.py::AReviewsWritesAreNamed::test_the_classifier_splits_a_reviews_own_files_from_everything_else PASSED
    tests/test_review_lane_isolation.py::AReviewsWritesAreNamed::test_a_clean_review_is_reported_clean PASSED
    ```

    The F-9 test runs a real review turn whose agent rewrites a sibling that is still `queued`, then asserts BOTH that the sibling's path appears in the item's recorded `review_write_scope["queued_siblings"]` AND that the `review-wrote-out-of-scope-paths` event is in `events.jsonl`. So the property "no queued item's input is silently rewritten by another item's turn" is pinned: the write may happen, but it cannot be silent.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste the three-review regression output for BOTH hosts, including the dirty-unrelated-path case with the pre-run and post-run status shown EQUAL (not empty). Paste `git worktree list` after the sweep proving no lane leaked. Paste the bare full-suite counts before and after with the FAILED-set diff.
  - Observed evidence: 27 regression tests green on both hosts, the dirty-path case shown EQUAL not empty, `git worktree list` clean, and the bare full-suite baseline/after counts with an IDENTICAL failure-set diff, all below.

    THE REGRESSION, all 27 tests, every sweep test running against BOTH hosts through the same agent behavior:

    ```text
    $ python3 -m pytest -o addopts="" tests/test_review_lane_isolation.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1646186850
    rootdir: /.../ajxr5d
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 27 items

    tests/test_review_lane_isolation.py ...........................          [100%]

    ============================== 27 passed in 7.85s ==============================
    ```

    THE DIRTY-UNRELATED-PATH CASE, pre-run and post-run EQUAL rather than empty (the review's own correction), from the live sweep:

    ```text
    PRE-RUN  main porcelain: 'M PEER.md'
      DURING v02001 main porcelain: 'M PEER.md'
      DURING v02002 main porcelain: 'M PEER.md'
      DURING v02003 main porcelain: 'M PEER.md'
    POST-RUN main porcelain: 'M PEER.md'
    EQUAL to pre-run: True
    PEER.md bytes intact: True
    ```

    The test additionally asserts the peer file's BYTES, not only the status line, so a run that reverted a co-worker's edit and left a same-shaped status would still fail.

    NO LEAKED WORKTREE after the sweep:

    ```text
    $ git worktree list
    /.../repo  e6eb2a1 [main]
    $ git branch --list 'aw/lane/*'
    (empty)
    ```

    ```text
    tests/test_review_lane_isolation.py::TheSweepRunsInOneLaneAndMainIsUntouched::test_the_sweep_lane_is_REMOVED_after_a_completed_sweep PASSED
    ```

    PARITY IS ENFORCED STRUCTURALLY AS WELL AS BEHAVIORALLY, so a one-host fix fails rather than half-passing:

    ```text
    tests/test_review_lane_isolation.py::TheSharedDefinitionsAreShared::test_the_review_lane_helpers_have_exactly_one_definition PASSED
    tests/test_review_lane_isolation.py::TheSharedDefinitionsAreShared::test_the_teardown_gate_is_the_EXISTING_shared_one PASSED
    tests/test_review_lane_isolation.py::TheSweepLaneRefreshPolicy::test_both_drivers_read_lanes_through_the_SWEEP_AWARE_composer PASSED
    ```

    THE FULL SUITE, BARE, BEFORE AND AFTER, EACH CAPTURED FROM THE SAME COMMIT rather than stated from memory (the plan requires this explicitly, noting three sibling reviews each found a claimed baseline to be wrong). The baseline was measured by STASHING this plan's code changes and re-running, so it is a real observation of the pre-change tree at this HEAD and not a recollection.

    BASELINE, at execution HEAD `c146cdb3` with this plan's changes stashed:

    ```text
    $ python3 -m pytest --ignore=tests/test_review_lane_isolation.py
    7381 passed, 3 skipped, 2 xfailed in 87.89s (0:01:27)
    ```

    AFTER:

    ```text
    $ python3 -m pytest
    7408 passed, 3 skipped, 2 xfailed in 83.95s (0:01:23)
    ```

    ZERO FAILURES ON BOTH SIDES, so the failed-set diff is empty by construction: no test that passed before this change fails after it. `7408 - 7381 = 27`, which is exactly this plan's new tests and nothing else.

    A CORRECTION TO AN EARLIER READING IN THIS SAME EXECUTION, recorded because the wrong number was nearly pasted here as the baseline and would have misled a later reader. The first baseline capture reported `31 failed, 7350 passed`, and those 31 were briefly taken to be inherited breakage in the lane-integration and self-finalize suites. THEY WERE NOT REAL. They are caused by `AW_EXECUTION_ROLE=worker`, which this execution turn runs under: `aw ipd begin`/`finalize` REFUSE for a worker-role process by design, so every fixture that shells out to a lifecycle verb fails on the refusal rather than on any defect. Proved by isolating the variable:

    ```text
    $ echo "AW_EXECUTION_ROLE=$AW_EXECUTION_ROLE"
    AW_EXECUTION_ROLE=worker

    $ python3 -m pytest -o addopts="" tests/test_ipd_lifecycle_cli.py::BeginCliTests
    ... 4 failed ...
      AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role
      process must not run them (refused: aw ipd begin).

    $ AW_EXECUTION_ROLE= python3 -m pytest -o addopts="" tests/test_ipd_lifecycle_cli.py::BeginCliTests
    4 passed in 0.38s
    ```

    So the counts above are the ones measured with that variable cleared, which is the honest environment for a suite claim. THE SUITE IS FULLY GREEN BEFORE AND AFTER. The role refusal itself is correct behavior and not a defect; that those fixtures cannot run under it is a test-harness gap, filed as its own backlog item rather than left as an unexplained 31.
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: EITHER paste a collected review-lane submission with its collection receipt, showing the outcome reached `<run_dir>/outcomes/` and that the disposition came from the outcome rather than the empty-outcome fallback; OR paste the evidence that a review turn writes no lane-side submission at all (an ls of the lane's expected submission paths after a real review turn), plus the comment recorded at `:6519` stating that finding. A bare assertion either way is not acceptable, because the failure mode is INVISIBLE by construction.
  - Observed evidence: the measured evidence that a review writes none of the three submissions, the R2.5 receipt recording each as `absent`, and why the call is still required, all below.

    THE ANSWER IS THE SECOND BRANCH PLUS A THIRD THING THE ITEM'S TWO OPTIONS DID NOT ANTICIPATE, so both halves are pasted.

    FIRST, THE EVIDENCE THAT A REVIEW TURN WRITES NO LANE-SIDE SUBMISSION. A real review turn was run in a sweep lane and the three expected submission paths were checked on disk:

    ```text
    === E-08 EVIDENCE: does a review turn write ANY lane-side submission? ===
      outcome    exists=False  .../review-sweep-run-e08/.aw/state/lane-submissions/run-e08/01-e08001/attempt-1/outcomes/01-e08001.json
      report     exists=False  .../review-sweep-run-e08/.aw/state/lane-submissions/run-e08/01-e08001/attempt-1/execution-report.md
      decisions  exists=False  .../review-sweep-run-e08/.aw/state/lane-submissions/run-e08/01-e08001/attempt-1/decisions-and-questions.md
    ```

    That is the expected result and its CAUSE is structural rather than incidental: `build_review_prompt` emits the `/plan-review` command plus the isolation notice and names no outcome, report or decisions path at all, so a review turn is never asked for any of the three. Note this does NOT break the disposition, because a review's disposition never came from an outcome file: it is derived from the plan's `- Status:` field (which is what E-09 fixes to read the lane), so the empty-outcome fallback this item warns about is not on a review's path.

    SECOND, WHY THE CALL IS STILL CORRECT rather than being replaced by a comment - and this is the part that was MEASURED rather than reasoned. Collecting produces the spec-R2.5 RECEIPT, and the receipt is what `submission_retention` reads to tell driver-written content from unexplained content. Without it, the sweep lane can never be classified and therefore can NEVER BE RETIRED. That is not hypothetical: it is exactly the failure this plan's own E-11 regression hit before the call was wired, and the gate said so in as many words:

    ```text
    a completed sweep's lane must be retired; reason: 'the lane holds content the driver cannot
    account for: ... an uncollected submission (no run directory or item was supplied, so no
    collection receipt can be read)'
    ```

    THE RECEIPT ITSELF, written for a review turn, recording all three submissions as `absent` (the legitimate R2.4 observation) rather than omitting them - which is precisely what R2.5 requires so that "wrote nothing" stays distinguishable from "never asked":

    ```json
    {
     "attempt": 1,
     "collected": [],
     "collection_runs": 1,
     "failed": [],
     "id6": "e08001",
     "position": 1,
     "run_id": "run-e08",
     "schema_version": 1,
     "status": "complete",
     "submissions": [
      {"name": "outcome",   "result": "absent", "reason": "the lane holds no such submission",
       "source": ".../lane-submissions/run-e08/01-e08001/attempt-1/outcomes/01-e08001.json",
       "destination": ".../runs/run-e08/outcomes/01-e08001.json", "source_sha256": null},
      {"name": "report",    "result": "absent", "reason": "the lane holds no such submission",
       "source": ".../lane-submissions/run-e08/01-e08001/attempt-1/execution-report.md",
       "destination": ".../runs/run-e08/lane-reports/01-e08001-attempt-1-execution-report.md", "source_sha256": null},
      {"name": "decisions", "result": "absent", "reason": "the lane recorded no decisions or deferred questions",
       "source": ".../lane-submissions/run-e08/01-e08001/attempt-1/decisions-and-questions.md",
       "destination": ".../runs/run-e08/decisions-and-questions.md", "source_sha256": null}
     ]
    }
    ```

    THE FINDING IS RECORDED AT THE SITE, as the item requires, in the comment now above the widened guard on both hosts. It states what was verified (a review writes none of the three), why the call is nevertheless required (the receipt is the load-bearing output, and the teardown gate reads it), and that E-02's lane-relative prompt is what makes spec R2.1's must-ship-together rule apply here at all.
  - Result: pass
- [x] V-11 validates E-11
  - Required evidence: paste `git worktree list` AND `git branch --list 'aw/lane/*'` after a COMPLETED sweep, both showing the sweep lane gone. Then paste the PRESERVED case: a sweep in which one review's merge conflicts (F-14's measured scenario is the natural fixture), showing the lane and its branch still present, its unmerged commit still reachable, and the run record naming it. Then state, with evidence, whether the existing lane-reclaim machinery discovers a sweep lane after an interrupt, given that the lane's identity is not an item id6; if it does not, paste what does.
  - DO NOT ACCEPT AN UNCONDITIONAL TEARDOWN. `teardown_isolation_worktree`'s docstring forbids calling it on a lane holding work, so paste the classification step and show a work-holding lane is not force-removed.
  - Observed evidence: worktree and branch both gone after a completed sweep, the PRESERVED case with its named reason, the interrupt question answered in both directions, and two defects this item's own regression found, all below.

    AFTER A COMPLETED SWEEP, both surfaces clean:

    ```text
    --- retire the sweep lane ---
    retired: True | sweep complete
    $ git worktree list
    /.../repo  e6eb2a1 [main]
    $ git branch --list 'aw/lane/*'
    (empty string)
    ```

    ```text
    tests/test_review_lane_isolation.py::TheSweepRunsInOneLaneAndMainIsUntouched::test_the_sweep_lane_is_REMOVED_after_a_completed_sweep PASSED
    ```

    THE PRESERVED CASE, showing the lane, its branch and its content survive, and the run record naming WHY:

    ```text
    tests/test_review_lane_isolation.py::TheSweepRunsInOneLaneAndMainIsUntouched::test_a_sweep_lane_that_HOLDS_WORK_is_PRESERVED_not_force_removed PASSED
    ```

    That test asserts, after leaving content the driver cannot account for in the lane: `record["retired"]` is False, the worktree directory still EXISTS, the lane BRANCH is still listed (checked with both the `*` and `+` markers stripped, since a lane branch is by definition checked out in another worktree), and `record["retire_reason"]` is non-empty. The recorded reason names the specific condition rather than being generic, which is spec R5.6's requirement:

    ```text
    retired: False | the lane holds content the driver cannot account for: 1 unknown UNTRACKED file(s): unexplained.txt
    ```

    THE CLASSIFICATION STEP IS THE EXISTING SHARED GATE, NOT A SECOND CLASSIFIER, which is what makes the "not unconditional" requirement structural rather than a promise: `runner_shared.retire_review_sweep_lane` delegates to `lane_containment.teardown_review_sweep_lane`, which delegates to `teardown_lane_if_classified` (the spec-R5.5 gate). Asserted:

    ```text
    tests/test_review_lane_isolation.py::TheSharedDefinitionsAreShared::test_the_teardown_gate_is_the_EXISTING_shared_one PASSED
    ```

    THE INTERRUPT QUESTION, ANSWERED WITH EVIDENCE IN BOTH DIRECTIONS, because the honest answer is "partly".

    IT DOES DISCOVER THE LANE IN THE COMMON CASE. `_lane_records_from_state` reads per-ITEM attempt records, and a review turn records its lane on its own attempt (`attempt["worktree"]`, `["worktree_branch"]`, `["worktree_lane_id"]`) exactly as an execute turn does, so once any review has started, the reclaimer finds the sweep lane by that route without any new mechanism.

    IT DOES NOT DISCOVER TWO CASES, and both are real: a run interrupted BETWEEN reviews before any attempt recorded the lane, and a run whose lane was allocated and then refused. Those leave a lane no attempt names, and since the lane's identity is `review-sweep-<run_id>` rather than an item id6, nothing else would find it either - which is the orphan class `laneorphan-01` exists to prevent.

    WHAT COVERS THEM: `runner_shared.lane_records_including_sweep`, which COMPOSES the per-item reader with the RUN-LEVEL record and de-duplicates by `(branch, worktree)`. Both hosts' `reclaim_lanes_on_interrupt` now read through it. It COMPOSES rather than edits `_lane_records_from_state` deliberately: that function's body is pinned BYTE-FOR-BYTE against `runner_shared_premove_fingerprints.json` (captured at HEAD `1ecc5891`) as proof it was a pure move, and editing it would break that proof for a reason unrelated to what the proof is about. Evidence:

    ```text
    tests/test_review_lane_isolation.py::TheSweepLaneRefreshPolicy::test_an_INTERRUPTED_sweeps_lane_is_DISCOVERABLE_by_the_reclaimer PASSED
    tests/test_review_lane_isolation.py::TheSweepLaneRefreshPolicy::test_both_drivers_read_lanes_through_the_SWEEP_AWARE_composer PASSED
    tests/test_runner_shared.py::PureMoveFingerprintTests::test_every_clean_symbol_is_a_STRICT_fingerprint_match PASSED
    ```

    The first also asserts a RETIRED lane is NOT reported, so a completed sweep does not leave the reclaimer chasing something already gone. Once discovered, the EXISTING classification applies unchanged: a lane holding work is left entirely alone and its uncommitted content snapshotted onto its own branch, which is what keeps a stranded review recoverable.

    TWO DEFECTS IN THIS ITEM'S OWN MECHANISM WERE FOUND BY ITS REGRESSION AND ARE RECORDED HERE BECAUSE BOTH WOULD HAVE SHIPPED SILENTLY. FIRST, every review materialized lane input revision 1, so review 2 OVERWROTE review 1's manifest and left review 1's copied plan accounted for by nothing; the gate then correctly refused with "2 unknown IGNORED file(s)" and a perfectly clean sweep could never retire its lane. Fixed by giving each review its own revision. SECOND, the gate's submission-retention question is per ITEM while the lane is SHARED, so passing no item made it answer "uncollected" by design (correct for one item, wrong for a shared lane) and passing one arbitrary item would have called that item's verdict the lane's; fixed by passing EVERY item that used the lane, probing all of them BEFORE removing anything, and authorizing teardown only when no item leaves an unexplained path.
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: paste an isolated review that sets `approved` on the lane and show the recorded disposition is `approved`. Then show the SAME case failing against pre-change code (recorded merely `reviewed`, because MAIN still read `to-review`), which is what proves the test is real rather than tautological. State which side of integration the disposition is now computed on and that the tree read matches that choice.
  - Observed evidence: both reads side by side on both hosts (lane -> `approved`, pre-change main -> `reviewed`) and the AST proof that the disposition precedes integration, all below.

    BOTH READS, SIDE BY SIDE, ON BOTH HOSTS. The same fixture is scored twice: once with `plan_repo` pointing at the lane (the post-change path) and once with it defaulted to `repo` (which is byte-identically the PRE-CHANGE behavior, since the parameter's default is `repo`). So the "fails against pre-change code" half is not a story about a previous commit, it is the pre-change code path executed side by side with the new one:

    ```text
    ================================================================================
    oc_runipd
      MAIN's copy says:   ['- Status: to-review']
      LANE's copy says:   ['- Status: approved']
      POST-CHANGE (plan_repo=lane):  approved
      PRE-CHANGE  (reads MAIN):      reviewed  <- loses the `approved` verdict
    ================================================================================
    agy_runipd
      MAIN's copy says:   ['- Status: to-review']
      LANE's copy says:   ['- Status: approved']
      POST-CHANGE (plan_repo=lane):  approved
      PRE-CHANGE  (reads MAIN):      reviewed  <- loses the `approved` verdict
    ```

    Asserted as a test that pins BOTH sides, so it cannot become tautological later:

    ```text
    tests/test_review_lane_isolation.py::TheReviewDispositionComesFromTheLane::test_an_approved_setting_review_is_recorded_approved_from_the_lane PASSED
    ```

    WHICH SIDE OF INTEGRATION, and the tree read matches it: the disposition is computed BEFORE integration, so the LANE is the only tree that holds the revision at that moment, so the lane read is the only correct answer. This is F-15's finding and it is now asserted mechanically rather than trusted:

    ```text
    tests/test_review_lane_isolation.py::TheReviewDispositionComesFromTheLane::test_the_disposition_is_computed_BEFORE_integration_so_the_lane_is_the_only_answer PASSED
    ```

    That test AST-walks each host's `execute_item` and asserts the first `reconcile_disposition` call precedes the first integration call, so "compute it after the merge and read main" cannot be reintroduced without failing.

    ONE SCOPING NOTE, because passing the lane unconditionally would otherwise look careless: `plan_repo` is consumed ONLY inside the review branch. The execute branch's own `plan_bucket` read still resolves against `repo`, deliberately, because it asks a DIFFERENT question ("did finalize already move this plan on MAIN"), and reading the lane there would answer the wrong one.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files this plan changed, path-scoped, never `git add -A`, never push. Paste actual runner output for every test claim; a claimed baseline must be captured from the same commit, never stated from memory. The declared scope is `Scope-Paths` (now including `runner_shared.py` and `tests/test_runner_shared.py`, which E-03 requires); an out-of-scope edit must be made and then JUSTIFIED with `--scope-reason` at finalize, and a declared-but-unmodified path acknowledged with `--scope-ack`.

OQ-03 IS BLOCKING AND GATES THE WHOLE PLAN. Do not start any E-item before it is answered: E-01 alone produces only a table, and every other item depends on the guard splits that answer authorizes. OQ-01 is answered (WIDEN the shared function) and its constraint stands: do NOT pass a synthetic validation result into the integration gate, which would be a forged attestation of the same family as a hand-written `- Readiness:`.

OQ-04 IS ALSO BLOCKING, ADDED AT REVIEW ROUND 2, and it gates E-02 and E-11 specifically. It decides the sweep lane's freshness policy, which F-14 measured to be a real and growing defect rather than a detail: the lane is cut once at sweep start and nothing refreshes it, so a nine-item sweep has review 9 reading a tree eight merges behind, and that contradicts one of the two reasons OQ-02 chose a single lane. Because the answer decides whether there is ONE long-lived lane or one per review, E-11's teardown shape follows from it and cannot be written first.

A THIRD WAY TO GET THIS WRONG, measured at review round 2 and forbidden: do NOT add the action kind to the per-host `integrate_lane_branch` WRAPPERS without first deciding E-03's route. `tests/test_runner_shared.py:787` asserts each wrapper's kwonly list is EMPTY, with the docstring "no wrapper may expose the injected parameter", and adding `*, action_kind: str` to the oc wrapper was measured to fail it. Bind the literal inside each wrapper as `host_label` already is, or amend that test deliberately and justify why its stated invariant no longer holds.

TWO SPECIFIC WAYS TO GET THIS WRONG, both measured, both forbidden. First, do NOT implement E-01's splits by deleting `not is_review` from `:6151` or `:6665`: those blocks also contain `driver_begin`, `driver_finalize` and the suite check, and a wholesale deletion would make a review claim execution authority and attempt a terminal transition it must never perform. Second, do NOT preserve the shared session by re-binding one session id across successive lanes: incident `lanesess xd9sll` measured exactly that losing four consecutive lanes, because an opencode session's own directory binding overrides `--dir`.

Post-gate lifecycle move: this plan reaches `executed/` only when every V-item above carries pasted evidence and `aw ipd lint --phase pre-transition` reports conforming.
