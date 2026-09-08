# IPD: Decide what a frozen begin base means once main has moved and stop reporting a stale baseline as scope drift

- Date: 2026-09-08
- Kind: child
- Concern: A STALE FROZEN BASE STILL MULTIPLIES INTO ONE FINDING PER FILE OF INTERVENING HISTORY, AND THAT IS STILL THE DOMINANT `aw check` SIGNAL, but the specific numbers the backlog item was filed on are GONE and must not be re-cited. MEASURED at HEAD: `check.scope-drift` produces 110 findings, of which SEVENTY-TWO come from ONE plan, `xdr83v`, whose receipt froze at `3d55a2d6` on 2026-09-06T06:19:17Z with 155 non-merge commits landing since. The remaining 38 are spread across seven plans at 5 to 7 each. So the mechanism the item describes is intact and is still the largest rule by volume, but the item's headline (1013 findings across 16 plans at 116 to 158 each) has resolved itself, exactly as the item predicted it would when the deferred lanes landed.
  THE ITEM'S OWN "INTERIM DISPOSITION" WAS CORRECT AND IS NOW SPENT, which is the finding that makes this graduable rather than obsolete. It said the count "resolves itself as the deferred lanes land" and forbade deleting receipts to quiet the rule. Verified: all six of the specifically named plans (`qcqhj7`, `58ha43`, `2c122z`, `rchpms`, `j4v6ga`, `2ouj70`) now sit in `superseded/` or `executed/`, and NONE of them is enumerated by the scope-drift scan any more (checked directly against `_iter_type_files(repo, "plans")`, which iterates 60 plan files and includes none of the six). Their receipts still exist on disk and were correctly left alone. So the ADVISORY volume problem self-healed and the QUESTION the item was actually filed to answer did not.
  THE QUESTION THAT SURVIVES IS THE ONE THE ITEM PUT FIRST, and it is unanswered in the tree: what is the frozen base FOR, given that ONE field serves at least three consumers with different needs. Measured consumers of `base_head`: `check.scope-drift` compares changed-since-base against declared Scope-Paths (`check_engine.py:1346`); `_paths_changed_by_this_execution` computes the finalize delta as a GIT REVISION RANGE (`base..HEAD`); and `_intervening_commits_touching` re-diffs the same range for the collision signal (`ipd_lifecycle.py:1441`). `run_begin`'s own docstring already records that these uses CONSTRAIN the field: `isolated_baseline` "deliberately does NOT influence `base_head`" because finalize consumes it as a git revision and "sourcing both from one execution tree would silently corrupt the finalize delta" (`:944-948`). That is the overload the item asks about, stated in the code, with no decision recorded about whether the advisory should share the field at all.
  ONE OF THE ITEM'S SIX QUESTIONS IS ALREADY ANSWERED IN THE TREE, and a plan transcribing the item would have commissioned work that exists. Its question 4 asks whether a stale receipt deserves its own state and rule. Its question 1's premise about liveness is partly satisfied by `_receipt_is_live` (`check_engine.py:1237`, landed in `45f8156c` on 2026-08-30, roughly nine hours BEFORE this item was written at `06b6c72e`), which already rejects a receipt whose plan is TERMINAL or whose `base_head` is not an ancestor of HEAD. That is why the six named plans stopped contributing. But it does NOT cover the case that still fires: `xdr83v`'s plan is in `pending/` and its base IS an ancestor, so the receipt is live by both tests while being 155 commits stale.
- Scope: Answer, with evidence, what a frozen `base_head` should mean once HEAD has moved far past it, and implement only what that answer authorizes. The one change this plan will make under EVERY outcome is to stop a single stale baseline from emitting one finding per intervening file, because that multiplication is what turns a real signal into noise and is independent of the base question. EXPLICITLY NOT receipt expiration: the item forbids it as the presumed answer and records four concrete reasons, all re-verified below.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_scope_drift.py, tests/test_receipt_stale_base.py
- Item-Dependencies: none
- Status: to-review
- Set: rcptstale
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wmnmei
- From-Backlog: v880xk
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `v880xk` as the EXPLORATION it demands, not as a fix, and with its headline evidence REPLACED rather than transcribed. THREE corrections. (1) The item's 1013-findings-across-16-plans measurement is DEAD: `check.scope-drift` now yields 110 findings, 72 from ONE plan (`xdr83v`, 155 commits past its base), and all six specifically named plans are now terminal and no longer enumerated by the scan. The item PREDICTED this ("resolves itself as the deferred lanes land"), so its interim disposition is vindicated and spent; a plan citing 1013 would have been arguing from a number a reader could not reproduce. (2) The rule that produced the item's harm was PARTLY fixed before the item was written: `_receipt_is_live` landed in `45f8156c` on 2026-08-30 at 01:57, about nine hours before the item's own commit `06b6c72e` at 11:09, and it is why the six named plans stopped contributing. The item's question 1 and question 4 must therefore be re-asked against that mechanism rather than against a tree without it. (3) The surviving case is NARROWER and more interesting: `xdr83v` passes BOTH liveness tests (plan in `pending/`, base IS an ancestor of HEAD) while being 155 commits stale, so liveness as currently defined does not capture staleness. The item's REJECTED FRAMING (receipt expiration) is carried forward intact with all four of its reasons re-verified, and OQ-01 is BLOCKING because the maintainer explicitly declined to have expiry chosen for them.

## Goal

Replace an overloaded frozen base and a noise-generating advisory with a recorded decision about what that base means once the tree has moved, so a large scope-drift count becomes information rather than something readers learn to ignore.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the current state, because the item's numbers are stale

- [ ] E-01 RE-MEASURE THE FINDING DISTRIBUTION AND WRITE IT DOWN, per plan, and do NOT cite this plan's numbers or the item's. This is the first E-item because every later decision is judged against it and because the figure has already moved by an order of magnitude once.
  MEASURE PER PLAN, NOT IN TOTAL. The shape of the problem is concentration: at authoring, 110 findings with 72 from ONE plan and the rest at 5 to 7 each. A total alone cannot distinguish "one stale baseline" from "widespread real drift", and that distinction decides whether E-05's per-plan collapse is sufficient.
  FOR EACH CONTRIBUTING PLAN, RECORD: its receipt's `base_head` and timestamp, its lifecycle directory, the count of non-merge commits from that base to HEAD, and whether `_receipt_is_live` returns True. `xdr83v` at authoring: base `3d55a2d6`, frozen 2026-09-06T06:19:17Z, 155 commits since, live=True, plan in `pending/`.
  ALSO CONFIRM THE SELF-HEAL. The item named six plans (`qcqhj7`, `58ha43`, `2c122z`, `rchpms`, `j4v6ga`, `2ouj70`). All six were measured terminal and NOT enumerated by the scan at authoring, while their receipts still exist on disk. Verify that is still so, and if any receipt has been DELETED, report it: the item explicitly forbade deleting these and a deletion would mean its warning was ignored.
  - Depends on: none
  - Expected outcome: a per-plan table of contributors with base, age in commits, directory and liveness; explicit confirmation of whether the item's six named plans are still terminal, unenumerated, and their receipts intact.
  - Execution state: pending

- [ ] E-02 ENUMERATE EVERY CONSUMER OF THE FROZEN BASE AND WHAT EACH NEEDS FROM IT. This is the item's question 1 and it is the question the whole exploration turns on: whether one field has been overloaded for three purposes.
  THE THREE KNOWN CONSUMERS, to be verified and extended by search rather than trusted from this list: `check.scope-drift` (`check_engine.py:1346`) uses it as the baseline for an ADVISORY about the current working tree; `_paths_changed_by_this_execution` uses it as a GIT REVISION for the finalize delta; `_intervening_commits_touching` (`ipd_lifecycle.py:1441`) re-diffs the same range for the collision signal. Search for every read of `base_head` across the package and the hooks, and say whether each wants the same thing.
  THE CODE ALREADY DOCUMENTS THE CONSTRAINT, AND IT MUST NOT BE BROKEN. `run_begin`'s docstring (`ipd_lifecycle.py:944-948`) records that `isolated_baseline` deliberately does not influence `base_head` because finalize consumes it as a git revision and a lane's HEAD "is not even its ancestor", so mixing sources "would silently corrupt the finalize delta". Any answer that changes what is FROZEN, rather than what the ADVISORY compares against, collides with that. Quote it in your finding.
  ANSWER THE OVERLOAD QUESTION EXPLICITLY, in one sentence per consumer: does the advisory need the same base as the finalize delta? The plausible answer is no (an advisory about the CURRENT tree could legitimately use a merge-base, or the plan's own commits, while the finalize delta must keep the exact frozen revision), but this E-item must establish it rather than assume it.
  - Depends on: E-01
  - Expected outcome: a consumer table naming every read of `base_head`, what each needs, and a stated verdict on whether the advisory and the finalize delta genuinely require the same field.
  - Execution state: pending

### Task group 2: answer the question the item was filed to answer

- [ ] E-03 SET OUT THE CANDIDATE ANSWERS FOR WHAT THE ADVISORY SHOULD COMPARE AGAINST, with the cost of each, and do NOT choose. This is the item's question 2.
  THE CANDIDATES: the frozen base as today; the MERGE-BASE of the frozen base and HEAD; the plan's OWN commits; or the advisory does not run at all once the base is stale by some measure. For each, say what it reports correctly and what it misses.
  READ `lbgzxg` FIRST, as the item instructs, and say what transferred. That executed plan made the closely related change at the FINALIZE end, attributing by OWNERSHIP rather than by mere dirtiness, and its reasoning ("demanding a reason for an unowned path would force this plan to either write a false claim into its permanent record or block on a condition it does not control") is recorded in `_working_tree_path_is_owned`'s docstring. State whether ownership-based attribution is available to the ADVISORY too, and note that approved plan `h9cn0y` is extending that same predicate to the committed half, so the advisory may be able to inherit the result rather than inventing anything.
  MIND THE COMPATIBILITY CONSTRAINT, because it is documented and load-bearing. `_paths_changed_by_this_execution` is "kept as the UNION-returning surface so every existing caller (notably `check_engine.check_scope_drift`) is unaffected", and `h9cn0y` E-02 is required to work at the split rather than the union for exactly that reason. So the advisory's input is a deliberately stabilized surface: changing what IT consumes is this plan's business, but it must not change that surface's shape for the finalize path.
  DO NOT PICK THE WINNER. Two of the four candidates change what a fail-closed-adjacent gate reports, and the maintainer declined to have the analogous decision made for them.
  - Depends on: E-02
  - Expected outcome: a candidate table with, per option, what it reports and what it misses; a written statement of what transferred from `lbgzxg` and what `h9cn0y` may supply; no option selected.
  - Execution state: pending

- [ ] E-04 RE-VERIFY THE REJECTED FRAMING RATHER THAN QUIETLY DROPPING IT, so nobody re-proposes expiry as the obvious fix. The item rejected "expire a receipt when its base drifts too far from HEAD" and gave four reasons; each must be re-checked at your HEAD and recorded as still-true or changed.
  THE FOUR REASONS, TO RE-VERIFY: (1) a receipt IS execution authority and `aw ipd finalize` refuses without a valid one, so expiring receipts silently revokes permission for in-flight work; (2) "too far" has no principled definition, since commit distance, wall-clock age and semantic distance disagree; (3) expiry treats the symptom rather than the question; (4) it interacts with worktree isolation, where a lane's base is deliberately NOT main's HEAD, so "far from HEAD" is the NORMAL and correct state for an isolated turn. Reason (4) has grown STRONGER since the item was written, because isolation is now the DEFAULT (`isolate_worktree` defaults True), so the case where distance-from-HEAD is normal is now the common case rather than an exception.
  CHECK WHETHER REASON (1)'s CONCRETE HARM STILL APPLIES. The item said 13 of the 16 affected plans belonged to deferred lane branches plus the `wtiso` stack that `6knsrx` needed in order to resume. `6knsrx` is now in `superseded/`, so THAT specific stranding risk may be gone; establish whether ANY currently-live receipt would be revoked by an expiry rule, and if none would, say so plainly rather than repeating a hazard that no longer has an instance. The ARGUMENT against expiry survives on reasons (2) to (4) regardless.
  - Depends on: E-03
  - Expected outcome: each of the four rejection reasons recorded as still-true or changed WITH evidence; an explicit statement of whether any live receipt would be revoked by an expiry rule today; no expiry implemented.
  - Execution state: pending

### Task group 3: fix the multiplication, which is true under every answer

- [ ] E-05 COLLAPSE THE PER-FILE MULTIPLICATION INTO A PER-PLAN FINDING THAT NAMES A COUNT. This is the item's question 3 and it is the ONE change that is correct regardless of how OQ-01 resolves, because the volume problem is independent of the base question.
  THE MECHANISM IS EXPLICIT AND LOCAL: `check_scope_drift` loops `for c in sorted(set(out_of_scope))` and appends one Drift per path (`check_engine.py:1357`). One stale baseline therefore yields one finding per file in the intervening history; measured, 72 for `xdr83v`.
  DO NOT LOSE THE PATHS. A count alone is less useful than the list when the drift is REAL: a plan genuinely touching three undeclared files should still say WHICH three. So the finding must carry the paths (in its detail, or bounded with an explicit "and N more"), not merely a number. Losing them would trade one usability failure for another.
  CONSIDER WHETHER THE COLLAPSE SHOULD BE CONDITIONAL, and decide deliberately rather than by omission: always one finding per plan, or per-path below a threshold and collapsed above it. A threshold is a heuristic of the kind the item warns against for expiry, so prefer the unconditional rule unless you can state why not.
  THIS CHANGES A CI-CONSUMED COUNT. `aw check` runs fail-closed in CI, and several plans' validation sections compare `aw check` findings and are explicitly told to compare CLASSES rather than counts for this reason. Collapsing changes the count but not the class, so it should not flip any gate; VERIFY that rather than assuming, and state the before/after totals.
  - Depends on: E-04
  - Expected outcome: one finding per plan carrying the count AND the paths; the collapse rule stated and justified; before/after totals measured and no rule CLASS added or removed.
  - Execution state: pending

- [ ] E-06 MAKE A STALE BASELINE VISIBLE AS WHAT IT IS, rather than as scope drift, if and only if OQ-01's answer calls for it. This is the item's question 4, re-asked against the mechanism that already exists.
  WHAT ALREADY EXISTS, so nothing is rebuilt: `_receipt_is_live` (`check_engine.py:1237`) already rejects a receipt whose plan is TERMINAL or whose base is not an ancestor of HEAD, and it FAILS SAFE (undeterminable means skip) for reasons its docstring records at length. It landed in `45f8156c`, about nine hours before the backlog item was written, and it is why the item's six named plans stopped contributing.
  WHAT IT DOES NOT COVER, which is the whole remaining case: a plan in `pending/` whose base IS an ancestor but is 155 commits behind. That receipt is live by both tests and stale by any reasonable reading. So if a distinct advisory state is wanted, it is a THIRD condition alongside the two that exist, not a replacement for them.
  DO NOT ADD A NEW RULE CODE UNLESS OQ-01 ASKS FOR ONE. A new `check.*` code is a new contract that CI and every plan's validation section then compares against, so it must be a decision rather than a convenience. If OQ-01 resolves to "no new state", this E-item is satisfied by RECORDING that in the docstring, and that is a legitimate completed outcome rather than a skipped item.
  DO NOT SURFACE IT IN `aw doctor` OR `aw attention` HERE. That is the item's question 6 and it is deferred with a reason below.
  - Depends on: E-05
  - Expected outcome: either a distinct, decision-authorized advisory state for a stale-but-live baseline, or a recorded decision that none is added with the reason; no new rule code introduced without OQ-01 authorizing it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- LIVENESS ALREADY EXISTS AND ALREADY FIXED HALF OF THIS. `_receipt_is_live` (`check_engine.py:1237`) rejects a terminal plan's receipt and an unreachable base, FAILS SAFE when undeterminable, and landed in `45f8156c` (2026-08-30 01:57), about NINE HOURS before the backlog item was written (`06b6c72e`, 11:09). The item's questions must be re-asked against it.
- IGNORING A RECEIPT IS NOT DELETING IT. `_receipt_is_live`'s docstring is explicit that a terminal plan's receipt "is NOT necessarily garbage" because a `committed-incomplete` journal re-runs finalize against a plan already in `executed/`, so "terminal licenses IGNORING the receipt here; it never licenses deleting one". The item independently reached the same conclusion.
- THE ADVISORY IS DELIBERATELY BEST-EFFORT, NOT AN AUTHORITY BOUNDARY: `hooks/precommit_scope_gate.py:17-19` records that hooks are local and skippable and that "the authoritative boundary is phase-5 CI running the same engine". That is why the liveness test fails safe rather than loud.
- THE FROZEN BASE IS CONSTRAINED BY THE FINALIZE DELTA. `run_begin`'s docstring (`ipd_lifecycle.py:944-948`) records that `isolated_baseline` must not influence `base_head` because finalize consumes it as a GIT REVISION and a lane's HEAD is not even this tree's ancestor. Change what the advisory COMPARES, never what is frozen.
- THE UNION SURFACE IS A DOCUMENTED COMPATIBILITY CONSTRAINT, kept unchanged specifically so `check_scope_drift` is unaffected; approved plan `h9cn0y` is required to work at the split for that reason. Do not change its shape.
- `lbgzxg` SOLVED THE ANALOGOUS PROBLEM AT THE OTHER END by attributing on OWNERSHIP rather than dirtiness, and its reasoning is in `_working_tree_path_is_owned`'s docstring. `h9cn0y` extends that predicate to the committed half.
- ISOLATION IS NOW THE DEFAULT (`isolate_worktree` default True), which strengthens the item's fourth reason against expiry: distance from HEAD is the normal state for an isolated turn.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the item's headline number is DEAD | `check.scope-drift` yields 110 findings, not 1013: 72 from ONE plan (`xdr83v`) and 38 across seven others at 5 to 7 each. The item's 16 named plans at 116 to 158 each no longer exist as contributors. | `check_scope_drift` run at HEAD, counted per location |
| F-2 | HIGH | the item PREDICTED the self-heal, and was right | Its interim disposition said the count "resolves itself as the deferred lanes land" and forbade deleting receipts. All six specifically named plans are now terminal and NOT enumerated by the scan (60 plan files iterated, none of the six), while their receipts remain on disk. | `_iter_type_files(repo,'plans')` membership test per id; receipt files present |
| F-3 | HIGH | the mechanism itself is intact | `xdr83v`'s receipt froze at `3d55a2d6` (2026-09-06T06:19:17Z) with 155 non-merge commits since, and `check_scope_drift` appends one Drift PER PATH, so one stale baseline still multiplies. | receipt contents; `git log --oneline --no-merges <base>..HEAD \| wc -l`; `check_engine.py:1357` |
| F-4 | HIGH | liveness landed BEFORE the item was written | `_receipt_is_live` shipped in `45f8156c` at 2026-08-30 01:57; the item was written in `06b6c72e` at 11:09 the same day. So the item's questions 1 and 4 were partly answered nine hours before it was filed, and it is why F-2's self-heal happened. | `git log -1` timestamps on both shas |
| F-5 | HIGH | but liveness does NOT capture staleness | `xdr83v` passes BOTH liveness tests (plan in `pending/`, base IS an ancestor of HEAD) while being 155 commits behind. So the surviving case is live-and-stale, a third condition neither existing test covers. | `_receipt_is_live` returns True for it; `git merge-base --is-ancestor` succeeds |
| F-6 | HIGH | ONE field serves three consumers with different needs | `check.scope-drift` uses `base_head` as an advisory baseline; `_paths_changed_by_this_execution` uses it as a git revision for the finalize delta; `_intervening_commits_touching` re-diffs the same range. The overload the item asks about is real. | `check_engine.py:1346`; `ipd_lifecycle.py:1441`, `:946` |
| F-7 | HIGH | and the code already documents the constraint | `run_begin`: `isolated_baseline` "deliberately does NOT influence `base_head`" because finalize consumes it as a git revision and mixing sources "would silently corrupt the finalize delta". So the FROZEN value must not change; only what the advisory compares may. | `ipd_lifecycle.py:944-948` |
| F-8 | MEDIUM | the fourth anti-expiry reason has STRENGTHENED | The item argued expiry misfires under isolation because a lane's base is deliberately not main's HEAD. Isolation is now the DEFAULT, so that is the common case rather than an exception. | `oc_runipd.py:7661-7665` (`isolate_worktree` default True) |
| F-9 | MEDIUM | one concrete stranding risk may be gone | The item warned expiry could strand the `wtiso` stack that `6knsrx` needed to resume. `6knsrx` is now in `superseded/`. E-04 must establish whether ANY live receipt would still be revoked, rather than repeating a hazard with no instance. | `aw find 6knsrx` |
| F-10 | MEDIUM | the advisory's input is a stabilized surface | `_paths_changed_by_this_execution` is documented as kept union-returning so `check_scope_drift` is unaffected, and `h9cn0y` is required to work at the split for that reason. Do not change its shape. | that docstring; `h9cn0y` E-02 and F-7 |
| F-11 | MEDIUM | the analogous problem was solved by OWNERSHIP | `lbgzxg` attributed the finalize working-tree half on positive ownership evidence rather than dirtiness, and `h9cn0y` extends it to the committed half, so the advisory may be able to inherit rather than invent. | `_working_tree_path_is_owned` docstring; `h9cn0y` E-02 |
| F-12 | LOW | the rule is explicitly best-effort | The precommit gate records that hooks are local and skippable and that CI is the authoritative boundary, which is why liveness fails safe. Relevant to how loud a stale-base state may be. | `hooks/precommit_scope_gate.py:17-19` |
| F-13 | LOW | a receipt for a terminal plan is not garbage | A `committed-incomplete` finalize journal re-runs finalize against a plan already in `executed/`, so ignoring a receipt is licensed while deleting one is not. | `_receipt_is_live` docstring |

## Proposed changes (ordered, validatable)

1. Re-measure the finding distribution per plan, with base, age, directory and liveness, and confirm the item's six named plans self-healed with receipts intact (E-01).
2. Enumerate every `base_head` consumer and state whether the advisory genuinely needs the same field as the finalize delta (E-02).
3. Set out the candidate baselines for the advisory with each one's cost, reporting what transferred from `lbgzxg` and what `h9cn0y` may supply, choosing none (E-03).
4. Re-verify all four anti-expiry reasons and whether any live receipt would be revoked today (E-04).
5. Collapse the per-file multiplication into one finding per plan carrying the count AND the paths (E-05).
6. Add a distinct stale-but-live advisory state only if OQ-01 authorizes it, else record the decision (E-06).

## Deferred / out of scope (with reason)

- RECEIPT EXPIRATION. Explicitly forbidden by the item as the presumed answer, with four recorded reasons that E-04 re-verifies rather than drops. Reason (4) has strengthened since isolation became the default. This plan will not implement expiry under any outcome of OQ-01.
- DELETING ANY RECEIPT. The item forbids it and `_receipt_is_live`'s docstring independently explains why (a `committed-incomplete` journal re-runs finalize against a terminal plan). The 20-odd receipts on disk stay exactly where they are; E-01 REPORTS on them and touches none.
- CHANGING WHAT `aw ipd begin` FREEZES, OR THE RECEIPT SCHEMA. `run_begin`'s docstring records that the frozen value is constrained by finalize's use of it as a git revision. This plan may change what the ADVISORY compares against; it must not change what is frozen.
- FINALIZE'S ATTRIBUTION. Owned by approved plan `h9cn0y` for the committed half and by executed `lbgzxg` for the working-tree half. This plan touches the ADVISORY only, and must not change the union surface both depend on.
- SURFACING A STALE BASE IN `aw doctor` OR `aw attention` (the item's question 6). Deferred: both are aggregate views with their own contracts, and adding a state to them before the state itself is decided (E-06, gated on OQ-01) would be backwards. Worth doing once there is a decided state to surface.
- WHAT SHOULD HAPPEN WHEN A PLAN HOLDING A RECEIPT IS RESUMED AFTER MAIN MOVED (the item's question 5). That is a LIFECYCLE decision about re-issuing, refusing, or re-basing execution authority, not an advisory one, and it belongs with whoever owns `begin`/`finalize` semantics. E-02's consumer analysis is the input such a plan would need; answering it here would mean changing execution authority from a plan scoped to a check rule.
- `xmqv5l` (begin freezes a whole-file digest so recording V evidence invalidates the receipt). Related defect in the same machinery, already `done`, and a different mechanism.
- THE `aw check` FINDING COUNT AS A TARGET. This plan is not a count-reduction exercise: E-05 reduces the count as a side effect of making one finding per cause, and E-05 must verify no rule CLASS changes, because several plans' validation sections compare classes rather than counts for exactly this reason.

## Scope check

- Over-scope: none. One check rule, two test modules.
- Scope-Paths justification: `agent_workflows/check_engine.py` holds `check_scope_drift`, its per-path Drift loop, `_receipt_is_live` and `_plan_disposition`, i.e. E-05 and E-06 in full and the measurement surface E-01 and E-02 read; `tests/test_check_engine_scope_drift.py` is where the collapse and the no-class-change property belong; `tests/test_receipt_stale_base.py` is new and covers the live-but-stale condition and whatever E-06 authorizes. `ipd_lifecycle.py` is deliberately NOT in scope even though E-02 must READ it: this plan analyzes the consumers and changes only the advisory, and an edit there would collide with approved `h9cn0y` in the highest-contention lifecycle module. If E-02 or E-03 concludes the advisory cannot be fixed without a lifecycle change, that is a FINDING and a follow-up plan, not a silent scope widening.
- Under-scope, stated rather than left as `none`: this plan does not implement expiry, deletes no receipt, changes nothing about what `begin` freezes or the receipt schema, does not touch finalize attribution or the union surface, does not surface a stale base in `aw doctor` or `aw attention`, does not answer the resume-semantics question, and does not treat the raw finding count as a target. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed` (the pre-existing `test_orchestrator_retirement` case). Roughly 32 further failures inside a lane are environmental. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- THE PER-PLAN DISTRIBUTION measured before and after, from `check_scope_drift` directly, with the per-location counts pasted. Authoring baseline: 110 findings, 72 from `xdr83v`, 38 across seven plans. Your numbers WILL differ; measure your own.
- A COLLAPSE TEST from a FIXTURE (a throwaway repo with a plan, a receipt, and several out-of-scope intervening files) asserting ONE finding per plan carrying the count AND the paths. Do not assert against live repository state, which drifts by the hour.
- A NO-CLASS-CHANGE ASSERTION: the set of `check.*` rule codes emitted repo-wide before and after must be identical unless OQ-01 authorized a new code, in which case name it. Paste both sets.
- A REAL-DRIFT PRESERVATION TEST: a plan genuinely touching three undeclared paths must still name all three; the collapse must not hide a small real drift.
- LIVENESS REGRESSION: the existing behavior that a TERMINAL plan's receipt and an UNREACHABLE base are both ignored must be unchanged, and the fail-safe direction (undeterminable means skip) preserved. Paste the tests covering `_receipt_is_live`.
- A CI-GATE CHECK: confirm `aw check` still exits as before for a repository whose only findings are collapsed scope-drift, since the rule runs fail-closed in CI.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`check_scope_drift`'s DOCSTRING is the authoritative prose on what the rule asks and must be updated to say what the finding now REPRESENTS (one per plan, carrying a count and the paths) rather than one per offending file. It already documents the liveness narrowing and the grandfathered-sentinel behavior; extend it rather than replacing it, since both record reasoning that must survive.

`_receipt_is_live`'s DOCSTRING must gain the case it does NOT cover, because that absence is exactly what this graduation had to discover by measurement: a plan in `pending/` whose base IS an ancestor of HEAD can still be arbitrarily stale (155 commits, measured), so liveness as defined is not staleness. State it even if E-06 adds no new state, so the next reader does not conclude the two tests are exhaustive.

No spec change is expected. `check.scope-drift` is an engine rule rather than a spec-defined contract. If the executor finds spec text asserting that scope drift reports one finding per offending path, declare that spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and record the reason here.

Write no em or en dashes in any user-facing finding message this plan produces.

## Open questions

### OQ-01: What should the frozen base MEAN for the advisory once HEAD has moved far past it?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT AGENT-RESOLVABLE, AND THE ITEM SAYS SO EXPLICITLY. The maintainer declined to accept receipt expiry "as the answer without more thought", and the four candidate baselines (frozen base, merge-base, the plan's own commits, or not evaluating at all) each change what a CI-consumed, fail-closed-adjacent rule reports. Two of them would make the advisory silent in circumstances where it is currently the only signal that a plan is touching territory it did not declare, and one of them (the plan's own commits) needs an ownership channel this repository has only partly built. The evidence needed is gathered by E-01 to E-04; the choice is a judgement about how much a stale baseline is still worth asking about, which is the maintainer's. NOTE this does not block E-05: the multiplication fix is correct under every candidate, which is why it sits in its own task group and why this plan delivers something real even if OQ-01 stays open.

### OQ-02: Should a stale-but-live baseline get its own rule code?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEPENDS ON OQ-01 AND IS DELIBERATELY SUBORDINATE TO IT. The item's question 4 asks whether reporting a stale baseline AS scope drift is a mislabelling rather than only a volume problem, and F-5 shows the condition is real and uncovered (live by both existing tests, 155 commits stale). But a new `check.*` code is a new contract that CI and every plan's validation section then compares against, so it should not be minted as a convenience. E-06 is written so that RECORDING the decision not to add one is a legitimate completed outcome, which is why this is non-blocking: the plan finishes either way, and the answer only decides whether E-06 writes code or prose.

### OQ-03: Is the advisory worth keeping at all for a plan whose base is very old?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, KEEP IT, and this is settled by the item's own analysis rather than needing a new decision. The item states the rule "is not simply wrong: it is answering the question it was asked, and that question is genuinely useful for a plan mid-execution in a tree that is moving under it". The defect is that the question stops being MEANINGFUL once the base is no longer a plausible baseline, and that nothing notices the transition. So the answer is never to delete the rule; it is to make it report proportionately (E-05) and, if OQ-01 so decides, to distinguish the stale case (E-06). Removing the advisory would lose the only signal that a plan is editing territory it never declared, which is the failure D141 built this machinery to surface.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL per-plan distribution you measured, with counts per location, plus for each contributor its `base_head`, freeze timestamp, lifecycle directory, commits-since-base, and `_receipt_is_live` verdict. THEN paste the membership check showing whether the item's six named plans (`qcqhj7`, `58ha43`, `2c122z`, `rchpms`, `j4v6ga`, `2ouj70`) are still unenumerated, and confirm each of their receipt FILES still exists. A missing receipt is a finding to report, not a tidy-up.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the consumer table with the ACTUAL search output enumerating every read of `base_head` across the package and hooks. Quote `run_begin`'s constraint sentence verbatim. State in one sentence per consumer whether it needs the same field as the others, and give an explicit verdict on the overload question; "unclear" is an acceptable verdict if the evidence genuinely does not settle it, but silence is not.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the candidate table naming, per option, what it reports correctly and what it misses. Paste what you read from `lbgzxg` and state explicitly whether ownership-based attribution is available to the advisory, and whether `h9cn0y` can supply it. Confirm in one sentence that NO option was selected and that the union surface's shape was not changed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for each of the four anti-expiry reasons, paste the evidence showing it still holds or has changed, including the isolation default for reason (4). THEN state explicitly whether any CURRENTLY LIVE receipt would be revoked by an expiry rule today, with the list (or an explicit none). Paste proof that no expiry mechanism was implemented and that no receipt file was deleted (`git status` plus a receipt-directory listing).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of the fixture-based collapse test, and quote the assertion showing the finding carries BOTH the count and the paths. Paste the real-drift preservation test showing a three-path drift still names all three. Paste the per-plan distribution before and after, and the two repo-wide rule-code SETS, confirming they are identical (or naming the one code OQ-01 authorized). Paste `aw check`'s unpiped exit code before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: state which way OQ-01 resolved and what E-06 therefore did. If a state was added, paste its rule code, a fixture test producing it for a live-but-stale receipt, and confirmation that the existing terminal-plan and unreachable-base behaviors are unchanged with their tests' output. If NO state was added, paste the docstring text recording the decision and its reason, and paste the sentence added to `_receipt_is_live`'s docstring naming the case it does not cover. Either way, paste the liveness regression tests' actual output showing the fail-safe direction preserved.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS AN EXPLORATION AND ITS BLOCKING QUESTION IS THE POINT, not an oversight. The backlog item states in its first line that it is "AN EXPLORATION, NOT A FIX" and forbids graduating it into a plan that implements receipt expiration. OQ-01 is therefore `Blocking: yes`, and the pre-execution gate that refuses a plan carrying an unresolved blocking question is the correct mechanism to hold task group 2's outcome for the maintainer. Task group 1 (E-01, E-02) is pure measurement and safe to perform first; E-05 is deliberately independent of OQ-01 so the plan delivers the proportionate-reporting fix regardless.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. DELETE NO RECEIPT and edit nothing under `.aw/state/`: the item forbids it, `_receipt_is_live`'s docstring explains why, and E-01 only reports. Do NOT edit `ipd_lifecycle.py`: approved plan `h9cn0y` is changing that module and this plan's scope is the advisory. Re-locate every symbol by NAME rather than by the line numbers cited here. Paste ACTUAL command and test output; measure your OWN finding distribution rather than citing this plan's, which has already moved by an order of magnitude once. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the two repo-wide rule-code sets and the explicit statement of whether any live receipt would have been revoked. If OQ-01 remains unanswered, this plan does not finalize on E-05 alone: report the measurement and the collapse as delivered work and leave the plan pending for the decision, rather than closing an exploration whose question is still open.
