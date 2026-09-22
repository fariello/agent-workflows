# IPD: Decide what a frozen begin base means once main has moved and stop reporting a stale baseline as scope drift

- Date: 2026-09-08
- Kind: child
- Concern: A STALE FROZEN BASE STILL MULTIPLIES INTO ONE FINDING PER FILE OF INTERVENING HISTORY, AND THAT IS STILL THE DOMINANT `aw check` SIGNAL, but every specific number is PERISHABLE and none may be re-cited. MEASURED at HEAD `3a3eaa79` on 2026-09-09: `check.scope-drift` produces 174 findings from exactly THREE plans: `xdr83v` 81 (base `5fe992aa`, frozen 2026-09-08T08:06:20Z, 138 non-merge commits since), `yvvf98` 75 (base `9b413533`, 139 commits since) and `hp9rot` 18 (base `8c06675c`, 41 commits since). All three are in `pending/` and all three are live by `_receipt_is_live`. DO NOT TRUST THOSE FIGURES EITHER: they replaced this plan's own authoring figures (110 findings, 72 from `xdr83v` at a base and timestamp that no longer exist because the receipt was re-begun, plus "38 across seven plans" that measured as one plan at 75 and one at 18), which in turn replaced the item's (1013 across 16 plans). The DISTRIBUTION SHAPE has now moved twice in two days and is the one thing E-01 must re-measure rather than inherit.
  THE OUT-OF-SCOPE PATHS ARE 100 PERCENT COMMITTED AND 0 PERCENT WORKING-TREE, measured per contributor by splitting `_changed_path_sources` (81/0, 75/0, 18/0). This is load-bearing and was not known at authoring: the rule's own docstring calls itself an advisory "about the current working tree", and today the working-tree half contributes NOTHING while the `base..HEAD` half contributes everything. So the noise is entirely intervening COMMITTED history, which is exactly the half `h9cn0y` already shipped an ownership predicate for.
  THE ITEM'S OWN "INTERIM DISPOSITION" WAS CORRECT AND IS NOW SPENT, which is the finding that makes this graduable rather than obsolete. It said the count "resolves itself as the deferred lanes land" and forbade deleting receipts to quiet the rule. Verified at HEAD `3a3eaa79`: all six of the specifically named plans (`qcqhj7`, `58ha43`, `2c122z`, `rchpms`, `j4v6ga`, `2ouj70`) now sit in `superseded/` or `executed/`; NONE of them is enumerated by the scope-drift scan any more (membership-tested against `_iter_type_files(repo, "plans")`, which iterates 104 plan files, NOT the 60 this plan first claimed, and includes none of the six); and all six receipt FILES are still on disk, 25 receipts in total. So the ADVISORY volume problem self-healed and the QUESTION the item was actually filed to answer did not.
  BUT SELF-HEALING IS NOT CONVERGENCE, and this is the argument for acting rather than waiting. The count went 1013 -> 110 -> 174 in nine days. It falls when a stale plan reaches a terminal directory and rises the moment a fresh `aw ipd begin` lands in a fast-moving tree, and the tree currently absorbs 57 to 134 non-merge commits per day (measured 2026-09-06 through 2026-09-09). So the mechanism REGENERATES the noise faster than the lifecycle drains it, and the volume problem is structural rather than a backlog to be waited out.
  THE QUESTION THAT SURVIVES IS THE ONE THE ITEM PUT FIRST, and it is unanswered in the tree: what is the frozen base FOR, given that ONE field serves at least three consumers with different needs. Measured consumers of `base_head`: `check.scope-drift` compares changed-since-base against declared Scope-Paths (`check_engine.py:1346`); `_paths_changed_by_this_execution` computes the finalize delta as a GIT REVISION RANGE (`base..HEAD`); and `_intervening_commits_touching` re-diffs the same range for the collision signal (`ipd_lifecycle.py:1441`). `run_begin`'s own docstring already records that these uses CONSTRAIN the field: `isolated_baseline` "deliberately does NOT influence `base_head`" because finalize consumes it as a git revision and "sourcing both from one execution tree would silently corrupt the finalize delta" (`:944-948`). That is the overload the item asks about, stated in the code, with no decision recorded about whether the advisory should share the field at all.
  ONE OF THE ITEM'S SIX QUESTIONS IS ALREADY ANSWERED IN THE TREE, and a plan transcribing the item would have commissioned work that exists. Its question 4 asks whether a stale receipt deserves its own state and rule. Its question 1's premise about liveness is partly satisfied by `_receipt_is_live` (`check_engine.py:1266`, landed in `45f8156c` at 2026-08-30 01:57:40, roughly nine hours BEFORE this item was written at `06b6c72e` 11:09:14), which already rejects a receipt whose plan is TERMINAL or whose `base_head` is not an ancestor of HEAD. That is why the six named plans stopped contributing. But it does NOT cover the case that still fires: all three current contributors sit in `pending/` with bases that ARE ancestors, so each is live by both tests while being 41 to 139 commits behind.
  AND "STALE" IS NOT EVEN THE RIGHT NAME FOR TWO OF THE THREE, which is the sharpest measurement in this plan and the one that reframes OQ-01. `hp9rot`'s receipt was written 2026-09-08T21:42 and its lane worktree is ACTIVELY DIRTY (8 modified files under `.aw/worktrees/hp9rot`, lane HEAD `8c06675c`), yet 41 commits have landed on main since it began. `xdr83v` and `yvvf98` are the same shape one day older. So these are not abandoned baselines: they are CORRECTLY FROZEN bases belonging to executions still in flight, which the advisory reports as drift purely because MAIN moved, not because the plan did anything. A rule that cannot tell "this plan wandered out of its fence" from "other agents committed while this plan was working" is mislabelling, and 174 of 174 current findings are the second case.
- Scope: Answer, with evidence, what a frozen `base_head` should mean once HEAD has moved far past it, and implement only what that answer authorizes. The one change this plan will make under EVERY outcome is to stop a single frozen baseline from emitting one finding per intervening file, because that multiplication is what turns a real signal into noise and is independent of the base question. EXPLICITLY NOT receipt expiration: the item forbids it as the presumed answer and records four concrete reasons, all re-verified below and joined by a fifth.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_scope_drift.py, tests/test_receipt_stale_base.py, tests/test_check_engine_receipt_liveness.py, tests/test_event_derived_lifecycle.py, tests/test_phase4_hooks.py, tests/test_finalize_scope_ownership.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: rcptstale
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: wmnmei
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: v880xk
- Blocks-Release: next

## Workflow history
- 2026-09-22 implementation performed (opencode its_direct/pt3-claude-opus-5-1m-us): NOT a status transition; the terminal `executed` transition is `aw ipd finalize`'s alone and is deliberately not claimed here. Implemented OQ-01's maintainer ruling as a TREE-SELECTION fix plus E-05's unconditional per-plan collapse, at HEAD `132e8333` in lane `.aw/worktrees/wmnmei`. MEASURED MY OWN DISTRIBUTION, which had moved a FOURTH time: 380 findings from SIX plans (219/100/28/18/13/2), not the review's 174-from-three, this plan's 110-from-eight, or the item's 1013-from-16. After: 4 findings from four plans, 17 offending paths, all lane-local. TWO OF THIS PLAN'S OWN CLAIMS WERE CORRECTED BY MEASUREMENT rather than inherited: F-3b's ABSOLUTE 100-percent-committed split is now 90 percent (343 committed-only, 32 worktree-only, 5 both), because this shared checkout carries dirty files it did not at review; and the cohesion cut is 57 percent (380 -> 162), not 76/79. Both corrections are recorded in V-01/V-03 rather than smoothed over. E-02 answered the overload question EXPLICITLY: six of seven `base_head` consumers want the identical git revision and the frozen value was NOT changed; the advisory is the one outlier and its need is a different TREE, not a different baseline, which is why all five of this plan's candidates were the wrong axis. E-04 re-verified all four anti-expiry reasons as still-true, stated reason (5), and listed FIVE live receipts an expiry would revoke today (replacing review's single `hp9rot` instance, which has since left the tree). E-06 added NO rule code and recorded why. SCOPE WAS WIDENED ADDITIVELY by two existing test files (`tests/test_phase4_hooks.py`, `tests/test_finalize_scope_ownership.py`) whose main-tree arrangements would otherwise have passed VACUOUSLY under the new rule; reasoned as decision D1, both literal-file eligible, no assertion deleted. Suite: `1 failed, 8208 passed, 3 skipped, 2 xfailed` against a baseline of `1 failed, 8189 passed, 3 skipped, 2 xfailed`, the one failure being the pre-existing environmental `tests/test_turn_bounds.py` case caused by this lane's ambient `OPENCODE_CONFIG_CONTENT` (proven by re-running it with the variable unset: 1 passed). Repo-wide rule-code SET identical before and after; `aw check plans` exits 1 both before and after on three unrelated codes.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, its one remaining open question is `Blocking: no` (OQ-02), which under the maintainer ruling of 2026-09-10 is not a not-ready condition; its blocking OQ-01 was answered on 2026-09-10. Performed at HEAD `84111de2` at the maintainer's explicit instruction of 2026-09-10, who was shown that 10 of 15 `no-go` plans were held by stale bookkeeping and chose to have them hand-fixed with evidence recorded rather than re-reviewed. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.

- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review at HEAD `3a3eaa79`; REVIEWED - OPEN QUESTIONS, readiness NO-GO on OQ-01 alone; PR-001..PR-014 all FIXED in place, none deferred, none REPLAN. Structural preflight returned EXIT 1 with one `IPD-Q501` (OQ-01 blocking and open) BEFORE and AFTER revisions, which is the gate working as designed on an exploration whose question is its deliverable, not a defect; that finding is why readiness is NO-GO and why the plan cannot be approved or begun until the maintainer answers. THREE MEASUREMENTS INVERTED THE PLAN'S OWN DIAGNOSIS. (1) All 174 findings (not 110) come from three plans, and splitting `_changed_path_sources` shows the offending paths are 100 percent COMMITTED history and 0 percent working tree, so the rule's stated subject (the current working tree) contributes nothing. (2) The contributors are not stale baselines but ACTIVE executions: `hp9rot`'s receipt is hours old and its lane worktree had 8 uncommitted files while 41 commits landed on main, so age is a proxy for "main moved", and every age-keyed remedy (including candidate (d) and any expiry) fires hardest on the healthiest execution. That became a fifth anti-expiry reason and restored reason (1)'s live instance, which the plan had reported as possibly lapsed. (3) The answer is partly already in the tree: `h9cn0y` is `executed`, and calling its shipped `_execution_cohesive_committed_paths` over the same three receipts yields 37 out-of-scope paths instead of 174, so E-03 gained a fifth measured candidate. FOUR CITATIONS WERE STALE (`_receipt_is_live` `:1237`->`:1266`, the per-path loop `:1357`->`:1386`, the frozen-base constraint attributed to `run_begin` when it lives on `begin` `:946-950`, the isolation default `:7661`->`:7888`), plus the plan-file count (60->104), the suite baseline (`5648`->`5919` passed with a different, environmental failing node), and one declared test file that does not exist. E-05 was re-pointed to depend on E-01 ALONE so the unconditionally-correct collapse is not stranded behind a maintainer decision, and gained a multi-plan fixture case, a `recovery`-field requirement and a `(rule, location)` set comparison after review measured that no existing test asserts a scope-drift count. A concurrency fence was added because two contributing plans have live lane worktrees other parties are working in now.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `v880xk` as the EXPLORATION it demands, not as a fix, and with its headline evidence REPLACED rather than transcribed. THREE corrections. (1) The item's 1013-findings-across-16-plans measurement is DEAD: `check.scope-drift` now yields 110 findings, 72 from ONE plan (`xdr83v`, 155 commits past its base), and all six specifically named plans are now terminal and no longer enumerated by the scan. The item PREDICTED this ("resolves itself as the deferred lanes land"), so its interim disposition is vindicated and spent; a plan citing 1013 would have been arguing from a number a reader could not reproduce. (2) The rule that produced the item's harm was PARTLY fixed before the item was written: `_receipt_is_live` landed in `45f8156c` on 2026-08-30 at 01:57, about nine hours before the item's own commit `06b6c72e` at 11:09, and it is why the six named plans stopped contributing. The item's question 1 and question 4 must therefore be re-asked against that mechanism rather than against a tree without it. (3) The surviving case is NARROWER and more interesting: `xdr83v` passes BOTH liveness tests (plan in `pending/`, base IS an ancestor of HEAD) while being 155 commits stale, so liveness as currently defined does not capture staleness. The item's REJECTED FRAMING (receipt expiration) is carried forward intact with all four of its reasons re-verified, and OQ-01 is BLOCKING because the maintainer explicitly declined to have expiry chosen for them.

## Goal

Replace an overloaded frozen base and a misattributing advisory with a recorded decision about what that base means once the tree has moved, so a large scope-drift count becomes information about the plan under audit rather than a report of other agents' commits that readers learn to ignore.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the current state, because the item's numbers are stale

- [x] E-01 RE-MEASURE THE FINDING DISTRIBUTION AND WRITE IT DOWN, per plan, and do NOT cite this plan's numbers or the item's. This is the first E-item because every later decision is judged against it and because the figure has now moved TWICE, by an order of magnitude and then back up.
  MEASURE PER PLAN, NOT IN TOTAL. The shape of the problem is concentration: at review, 174 findings from exactly THREE plans (`xdr83v` 81, `yvvf98` 75, `hp9rot` 18) at HEAD `3a3eaa79`; at authoring one day earlier, 110 from eight. A total alone cannot distinguish "a few frozen bases" from "widespread real drift", and that distinction decides whether E-05's per-plan collapse is sufficient.
  FOR EACH CONTRIBUTING PLAN, RECORD: its receipt's `base_head` and `timestamp` (the field is `timestamp`, not `frozen_at`), its lifecycle directory and `- Status:`, the count of non-merge commits from that base to HEAD, whether `_receipt_is_live` returns True, and WHETHER ITS LANE WORKTREE EXISTS AND IS DIRTY (`git -C .aw/worktrees/<id> status --porcelain`). That last column is the one review added and it is the point: `hp9rot` had 8 modified lane files while contributing 18 findings, which makes it an ACTIVE execution, not an abandoned baseline.
  SPLIT THE OUT-OF-SCOPE PATHS BY SOURCE, per contributor, using `_changed_path_sources(repo, base)` and applying the SAME fence `check_scope_drift` applies (the `.aw/state/`+`.aw/worktrees/` prefix skip, `_is_implicitly_allowed`, `_scope_match`). Report committed-only, worktree-only and both. Measured at review: 81/0/0, 75/0/0, 18/0/0. If your split is still ~100 percent committed, say so explicitly, because that single fact is what makes E-03's ownership candidate the leading one rather than a curiosity.
  ALSO CONFIRM THE SELF-HEAL. The item named six plans (`qcqhj7`, `58ha43`, `2c122z`, `rchpms`, `j4v6ga`, `2ouj70`). All six were measured terminal and NOT enumerated by the scan (104 plan files iterated), while all six receipts remain on disk. Verify that is still so, and if any receipt has been DELETED, report it: the item explicitly forbade deleting these and a deletion would mean its warning was ignored.
  - Depends on: none
  - Expected outcome: a per-plan table of contributors with base, timestamp, age in commits, directory, status, liveness AND lane-dirtiness; the committed/worktree split of out-of-scope paths per contributor; explicit confirmation of whether the item's six named plans are still terminal, unenumerated, and their receipts intact.
  - Execution state: performed

- [x] E-02 ENUMERATE EVERY CONSUMER OF THE FROZEN BASE AND WHAT EACH NEEDS FROM IT. This is the item's question 1 and it is the question the whole exploration turns on: whether one field has been overloaded for three purposes.
  THE KNOWN CONSUMERS, to be verified and extended by search rather than trusted from this list: `check.scope-drift` (`check_engine.py:1363`) uses it as the baseline for an ADVISORY; `_paths_changed_by_this_execution` (`ipd_lifecycle.py:1200`) uses it as a GIT REVISION for the finalize delta; `_intervening_commits_touching` (`:1225`) re-diffs the same range for the collision signal; `finalize_precheck` reads it off the receipt and refuses without a usable one (`:1485`); and `run_begin` re-emits it in its success payload (`:3025`). Search for every read across the package AND `agent_workflows/hooks/`, and say whether each wants the same thing. Note `ipd_set_plan`'s `ExecutionManifest.base_head` is a DIFFERENT field with the same name (a Set-level manifest, not the receipt) and must not be conflated.
  THE CODE ALREADY DOCUMENTS THE CONSTRAINT, AND IT MUST NOT BE BROKEN. The docstring of `begin` (`ipd_lifecycle.py:946-950`; the constraint is on `begin`, NOT on `run_begin`, which is the thin CLI entry point at `:2933`) records that `isolated_baseline` deliberately does not influence `base_head` because finalize consumes it as a git revision and a lane's HEAD "is not even its ancestor", so mixing sources "would silently corrupt the finalize delta". Any answer that changes what is FROZEN, rather than what the ADVISORY compares against, collides with that. Quote it in your finding.
  ANSWER THE OVERLOAD QUESTION EXPLICITLY, in one sentence per consumer: does the advisory need the same base as the finalize delta? The plausible answer is no (an advisory about the CURRENT tree could legitimately use a merge-base, or the plan's own commits, while the finalize delta must keep the exact frozen revision), but this E-item must establish it rather than assume it.
  - Depends on: E-01
  - Expected outcome: a consumer table naming every read of `base_head`, what each needs, and a stated verdict on whether the advisory and the finalize delta genuinely require the same field.
  - Execution state: performed

### Task group 2: answer the question the item was filed to answer

- [x] E-03 SET OUT THE CANDIDATE ANSWERS FOR WHAT THE ADVISORY SHOULD COMPARE AGAINST, with the cost of each, and do NOT choose. This is the item's question 2.
  THE CANDIDATES, now FIVE rather than four: (a) the frozen base as today; (b) the MERGE-BASE of the frozen base and HEAD; (c) the plan's OWN commits; (d) the advisory does not run once the base is stale by some measure; and (e) THE FROZEN BASE AS TODAY, BUT ATTRIBUTED, i.e. keep the range and filter it through the ownership predicate that already ships. For each, say what it reports correctly and what it misses.
  CANDIDATE (e) IS NOT HYPOTHETICAL AND MUST BE MEASURED, NOT DESCRIBED. `h9cn0y` is `executed`, and `_execution_cohesive_committed_paths(repo, base, scope_paths)` (`ipd_lifecycle.py:1258`) is callable today. Measured at review over the three contributors, with the SAME fence applied, it yields 21, 7 and 9 out-of-scope paths instead of 81, 75 and 18: a 76 percent reduction that comes from CORRECTING ATTRIBUTION rather than from compressing output. Re-run that measurement yourself and put the numbers in the table. Also state its documented COST honestly: cohesion is a heuristic that errs in both directions (see its own docstring), so option (e) trades a systematic over-report for a smaller two-sided error, and that trade is part of what OQ-01 decides.
  NOTE THAT (b) AND (d) ARE ANSWERS TO A QUESTION THE MEASUREMENT DID NOT ASK. Both key on the base being OLD. But E-01's lane-dirtiness column and F-5b show the contributors are ACTIVE executions whose bases are correctly frozen, so age is a proxy for "main moved", not for "this plan is stale". Say plainly, per option, whether it addresses misattribution or only volume.
  READ `lbgzxg` FIRST, as the item instructs, and say what transferred. That executed plan made the closely related change at the FINALIZE end, attributing by OWNERSHIP rather than by mere dirtiness, and its reasoning ("demanding a reason for an unowned path would force this plan to either write a false claim into its permanent record or block on a condition it does not control") is recorded in `_working_tree_path_is_owned`'s docstring (`:1392`, whose name is a documented misnomer: it now judges BOTH halves). State whether ownership-based attribution is available to the ADVISORY too.
  MIND THE COMPATIBILITY CONSTRAINT, because it is documented and load-bearing. `_paths_changed_by_this_execution` is "kept as the UNION-returning surface so every existing caller (notably `check_engine.check_scope_drift`) is unaffected". So the advisory's input is a deliberately stabilized surface: changing what IT consumes is this plan's business (calling `_changed_path_sources` or the cohesion helper instead is a caller-side change), but it must not change that surface's shape or value for the finalize path.
  DO NOT PICK THE WINNER. Every candidate except (a) changes what a fail-closed-adjacent gate reports, and the maintainer declined to have the analogous decision made for them.
  - Depends on: E-02
  - Expected outcome: a five-row candidate table with, per option, what it reports, what it misses, and whether it addresses misattribution or only volume; the re-measured cohesion figures for option (e) with its stated heuristic cost; a written statement of what transferred from `lbgzxg` and what `h9cn0y` already supplies; no option selected.
  - Execution state: performed

- [x] E-04 RE-VERIFY THE REJECTED FRAMING RATHER THAN QUIETLY DROPPING IT, so nobody re-proposes expiry as the obvious fix. The item rejected "expire a receipt when its base drifts too far from HEAD" and gave four reasons; each must be re-checked at your HEAD and recorded as still-true or changed.
  THE FOUR REASONS, TO RE-VERIFY: (1) a receipt IS execution authority and `aw ipd finalize` refuses without a valid one (`finalize_precheck` at `ipd_lifecycle.py:1485` returns cannot-run for an unusable base), so expiring receipts silently revokes permission for in-flight work; (2) "too far" has no principled definition, since commit distance, wall-clock age and semantic distance disagree; (3) expiry treats the symptom rather than the question; (4) it interacts with worktree isolation, where a lane's base is deliberately NOT main's HEAD, so "far from HEAD" is the NORMAL and correct state for an isolated turn. Reason (4) has grown STRONGER since the item was written, because isolation is now the DEFAULT (`oc_runipd.py:7888-7891`, `--no-isolate-worktree` with `default=True`), so the case where distance-from-HEAD is normal is now the common case rather than an exception.
  REASON (1) HAS A LIVE INSTANCE AGAIN, so do NOT report it as lapsed. The item feared expiry stranding the `wtiso` stack that `6knsrx` needed; `6knsrx` is now `superseded/`, so THAT instance is gone. But measured at review, `hp9rot` holds a live receipt (written 2026-09-08T21:42) whose lane worktree has 8 uncommitted modified files while 41 commits have landed on main since it began. A distance-keyed expiry would revoke authority for that execution TODAY. Re-measure at YOUR head and report the list, or an explicit none if the lanes have since landed; the point is to check rather than to inherit either conclusion.
  ADD A FIFTH REASON IF YOUR MEASUREMENT SUPPORTS IT, and review's does: expiry (and every age-keyed variant, including candidate (d)) fires HARDEST on the most active execution, because a fast-moving main accrues distance fastest exactly while a plan is being worked. That inverts the intent. State it as reason (5) with your own evidence, or say why your measurement does not support it.
  - Depends on: E-03
  - Expected outcome: each of the four rejection reasons recorded as still-true or changed WITH evidence, plus reason (5) stated or explicitly declined; an explicit LIST of live receipts an expiry rule would revoke today (or an evidenced none); no expiry implemented.
  - Execution state: performed

### Task group 3: fix the multiplication, which is true under every answer

- [x] E-05 COLLAPSE THE PER-FILE MULTIPLICATION INTO A PER-PLAN FINDING THAT NAMES A COUNT. This is the item's question 3 and it is the ONE change that is correct regardless of how OQ-01 resolves, because the volume problem is independent of the base question.
  IT DEPENDS ON E-01 ONLY, DELIBERATELY. This item needs the measured distribution and nothing else; E-02 to E-04 are the analysis feeding OQ-01, and chaining the collapse behind them would strand the plan's one unconditionally-correct deliverable behind a maintainer decision. That independence is stated in the gate and is the reason this sits in its own task group.
  THE MECHANISM IS EXPLICIT AND LOCAL: `check_scope_drift` loops `for c in sorted(set(out_of_scope))` and appends one Drift per path (`check_engine.py:1386`). One frozen base therefore yields one finding per file in the intervening history; measured at review, 81 for `xdr83v`.
  DO NOT LOSE THE PATHS. A count alone is less useful than the list when the drift is REAL: a plan genuinely touching three undeclared files should still say WHICH three. So the finding must carry the paths (in its detail, or bounded with an explicit "and N more"), not merely a number. Losing them would trade one usability failure for another. Keep the existing `observed`/`required`/`recovery` enrichment (`enrich_drift`, `check_engine.py:351`) populated: the pre-commit hook prints `recovery` verbatim as its teaching message, so a collapsed finding with an empty recovery field would silently degrade the hook's output.
  KEEP THE LOCATION AND THE RULE ID EXACTLY AS THEY ARE. The CI parity test compares the SET of `(rule, location)` pairs (`tests/test_ci_check_parity.py:87`), and the location is already the plan file, so collapsing N findings for one plan into one preserves that set by construction. Verify it rather than assuming.
  THE COLLAPSE SHOULD BE UNCONDITIONAL, and the burden is on any threshold. A threshold is a heuristic of the kind the item warns against for expiry, and E-01's measured shape (three plans at 81/75/18, no long tail of small honest drifts) gives no evidence a threshold would preserve anything. Implement the unconditional rule unless your own measurement contradicts that, and if it does, state the contradiction.
  THIS DOES NOT MOVE ANY GATE, AND THAT IS MEASURED RATHER THAN HOPED. At review `aw check plans` exits 1 with 193 findings across FIVE rule codes, of which scope-drift is 174; the other four (`check.lifecycle-transition-invalid`, `check.ipd-dependency-findings-blocked`, `check.review-finding-unescalated`, `check.review-decision-unescalated`) keep the exit at 1 no matter what this rule emits. Re-measure and state the before/after totals, the exit codes, and the rule-code sets; the claim to prove is that no CLASS is added or removed.
  - Depends on: E-01
  - Expected outcome: one finding per plan carrying the count AND the paths, with `recovery` still populated; the unconditional collapse rule stated and justified; before/after totals, exit codes and rule-code sets measured with no CLASS added or removed.
  - Execution state: performed

- [x] E-06 MAKE THE MISATTRIBUTED CASE VISIBLE AS WHAT IT IS, rather than as scope drift, if and only if OQ-01's answer calls for it. This is the item's question 4, re-asked against the mechanism that already exists.
  WHAT ALREADY EXISTS, so nothing is rebuilt: `_receipt_is_live` (`check_engine.py:1266`) already rejects a receipt whose plan is TERMINAL or whose base is not an ancestor of HEAD, and it FAILS SAFE (undeterminable means skip) for reasons its docstring records at length. It landed in `45f8156c`, about nine hours before the backlog item was written, and it is why the item's six named plans stopped contributing.
  WHAT IT DOES NOT COVER, which is the whole remaining case: a plan in `pending/` whose base IS an ancestor but is 41 to 139 commits behind while its lane is actively being worked. That receipt is live by both tests, and the finding it produces names OTHER agents' commits. So if a distinct advisory state is wanted, it is a THIRD condition alongside the two that exist, not a replacement for them.
  NAME IT FOR THE DEFECT, NOT FOR THE AGE, if OQ-01 authorizes a state at all. The item floated `check.receipt-base-stale`, and review's measurement argues against that spelling: nothing about these bases is stale in the sense of wrong, and the honest description is that intervening history is being attributed to this plan. Put the naming choice to the maintainer with OQ-02 rather than settling it here, and record whichever is chosen with its reason.
  DO NOT ADD A NEW RULE CODE UNLESS OQ-01 ASKS FOR ONE. A new `check.*` code is a new contract that CI and every plan's validation section then compares against, and an UNREGISTERED id silently falls back to `_DEFAULT_RULESPEC` (`error`, empty invariant), so adding one without registering it in `RULE_REGISTRY` with a deliberate severity and invariant trace would be a contract change made by omission. If OQ-01 resolves to "no new state", this E-item is satisfied by RECORDING that in the docstring, and that is a legitimate completed outcome rather than a skipped item.
  DO NOT SURFACE IT IN `aw doctor` OR `aw attention` HERE. That is the item's question 6 and it is deferred with a reason below.
  - Depends on: E-04, E-05
  - Expected outcome: either a distinct, decision-authorized advisory state (registered in `RULE_REGISTRY` with an explicit severity and invariant) for the live-but-misattributed case, or a recorded decision that none is added with the reason; no new rule code introduced without OQ-01 authorizing it.
  - Execution state: performed

## Project conventions discovered (Step 0)

- LIVENESS ALREADY EXISTS AND ALREADY FIXED HALF OF THIS. `_receipt_is_live` (`check_engine.py:1266`) rejects a terminal plan's receipt and an unreachable base, FAILS SAFE when undeterminable, and landed in `45f8156c` (2026-08-30 01:57:40), about NINE HOURS before the backlog item was written (`06b6c72e`, 11:09:14). The item's questions must be re-asked against it.
- IGNORING A RECEIPT IS NOT DELETING IT. `_receipt_is_live`'s docstring is explicit that a terminal plan's receipt "is NOT necessarily garbage" because a `committed-incomplete` journal re-runs finalize against a plan already in `executed/`, so "terminal licenses IGNORING the receipt here; it never licenses deleting one". The item independently reached the same conclusion.
- THE ADVISORY IS BEST-EFFORT LOCALLY AND FAIL-CLOSED IN CI, and both halves matter. `hooks/precommit_scope_gate.py:16-19` records that hooks are local and skippable and that "the authoritative boundary is phase-5 CI running the same engine"; that CI step is `aw check plans` at `.github/workflows/tests.yml:153` and it does fail closed. So the liveness test fails safe locally while the rule still gates CI.
- THE FROZEN BASE IS CONSTRAINED BY THE FINALIZE DELTA. The docstring of `begin` (`ipd_lifecycle.py:946-950`) records that `isolated_baseline` must not influence `base_head` because finalize consumes it as a GIT REVISION and a lane's HEAD is not even this tree's ancestor. Change what the advisory COMPARES, never what is frozen. (`run_begin` at `:2933` is the CLI wrapper, not the site of this constraint.)
- THE UNION SURFACE IS A DOCUMENTED COMPATIBILITY CONSTRAINT, kept unchanged specifically so `check_scope_drift` is unaffected; `h9cn0y` worked at the split for that reason. Do not change its shape. `_changed_path_sources` (`:1176`) is the split-returning surface a caller uses instead.
- THE OWNERSHIP FIX FOR THE COMMITTED HALF IS ALREADY SHIPPED, NOT PENDING. `h9cn0y` is `executed`, and `_execution_cohesive_committed_paths` (`:1258`) is callable now; `lbgzxg` solved the working-tree half and its reasoning is in `_working_tree_path_is_owned`'s docstring (`:1392`, a documented misnomer that now judges both halves). The advisory can INHERIT rather than invent.
- THE NOISE IS ENTIRELY COMMITTED HISTORY. Measured per contributor, the out-of-scope split is committed-only 81/75/18 and worktree-only 0/0/0, so the half the rule's docstring foregrounds ("the current working tree") contributes nothing today.
- A CONTRIBUTING PLAN MAY BE ACTIVELY EXECUTING. `hp9rot` has a live lane worktree with 8 modified files. Do NOT touch `.aw/worktrees/*` or any lane branch, and do not read a contributor's findings as evidence that its plan misbehaved.
- ISOLATION IS NOW THE DEFAULT (`oc_runipd.py:7888-7891`), which strengthens the item's fourth reason against expiry: distance from HEAD is the normal state for an isolated turn.
- AN UNREGISTERED RULE ID DEFAULTS TO `error` WITH AN EMPTY INVARIANT (`_DEFAULT_RULESPEC`), so any new `check.*` code must be registered in `RULE_REGISTRY` deliberately. `check.scope-drift` is registered `error`/`I-01`.
- NO EXISTING TEST ASSERTS A SCOPE-DRIFT COUNT. All assertions are emptiness or truthiness, and the CI parity test compares `(rule, location)` SETS, so a per-plan collapse breaks nothing by construction. Verify, do not assume.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name: every line number in this plan was corrected once during review and several were wrong.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | EVERY headline number is perishable, including this plan's own | The item claimed 1013 findings across 16 plans; this plan's authoring round measured 110 from 8; re-measured at HEAD `3a3eaa79` it is 174 from exactly THREE (`xdr83v` 81, `yvvf98` 75, `hp9rot` 18). Cite NONE of these; measure your own. | `check_scope_drift(Path('.'))` counted per location at `3a3eaa79` |
| F-2 | HIGH | the item PREDICTED the self-heal, and was right | Its interim disposition said the count "resolves itself as the deferred lanes land" and forbade deleting receipts. All six specifically named plans are now terminal and NOT enumerated by the scan (104 plan files iterated, none of the six), while all six receipt files remain on disk (25 receipts total). | `_iter_type_files(repo,'plans')` membership test per id; `ls .aw/state/ipd-lifecycle/` |
| F-2b | HIGH | but self-healing is NOT convergence, so waiting is not a strategy | The count went 1013 -> 110 -> 174 in nine days: it drains as plans reach terminal directories and refills on every fresh `begin`, in a tree absorbing 57 to 134 non-merge commits per day. The mechanism regenerates noise faster than the lifecycle removes it. | per-day `git log --no-merges` counts for 2026-09-06..09; the three measurement rounds above |
| F-3 | HIGH | the mechanism itself is intact | `check_scope_drift` appends one Drift PER PATH inside `for c in sorted(set(out_of_scope))`, so one frozen base multiplies into one finding per intervening file: 81 for `xdr83v`, whose base `5fe992aa` is 138 non-merge commits behind. | `check_engine.py:1386`; receipt contents; `git log --oneline --no-merges <base>..HEAD \| wc -l` |
| F-3b | BLOCKER | the noise is 100 percent COMMITTED history and 0 percent working tree | Splitting `_changed_path_sources` per contributor gives committed-only/worktree-only of 81/0, 75/0 and 18/0. The rule's docstring calls itself an advisory about "the current working tree", yet that half contributes nothing today. So the defect is precisely the `base..HEAD` half that `h9cn0y` already built `_execution_cohesive_committed_paths` to attribute, and a collapse-only fix would compress a wrong answer instead of correcting it. | `_changed_path_sources(repo, base)` per receipt; `check_engine.py:1330` docstring |
| F-3c | BLOCKER | cohesion attribution already shrinks the finding set by 76 percent | Running the SHIPPED `_execution_cohesive_committed_paths` over the same three receipts and applying the same fence leaves 21, 7 and 9 out-of-scope paths (37) rather than 174. So the answer OQ-01 was asked to choose between is partly already IN the tree, unconsumed by the advisory, and E-03's candidate table must include it as a fifth option with this measurement attached. | `_execution_cohesive_committed_paths(repo, base, sp)` per receipt, fenced identically |
| F-4 | HIGH | liveness landed BEFORE the item was written | `_receipt_is_live` shipped in `45f8156c` at 2026-08-30 01:57:40; the item was written in `06b6c72e` at 11:09:14 the same day. So the item's questions 1 and 4 were partly answered nine hours before it was filed, and it is why F-2's self-heal happened. | `git log -1 --format='%H %ci'` on both shas |
| F-5 | HIGH | but liveness does NOT capture staleness | All three contributors pass BOTH liveness tests (plans in `pending/`, bases ARE ancestors of HEAD) while being 41 to 139 commits behind. So live-and-stale is a third condition neither existing test covers. | `_receipt_is_live` returns True for all three; `merge-base --is-ancestor` succeeds |
| F-5b | BLOCKER | "stale" MISNAMES the case: these are live executions whose base is correctly frozen | `hp9rot`'s receipt is dated 2026-09-08T21:42 and its lane worktree has 8 modified files right now; 41 commits landed on main since it began. Nothing about its base is wrong, and its plan has drifted nowhere. All 174 findings report OTHER agents' commits as this plan's drift. So the defect is MISATTRIBUTION, and an age-based framing (however phrased) would fire hardest on the healthiest, most active execution. | `git -C .aw/worktrees/hp9rot status --porcelain` (8 entries); receipt timestamp; F-3b |
| F-6 | HIGH | ONE field serves three consumers with different needs | `check.scope-drift` uses `base_head` as an advisory baseline (`check_engine.py:1363`); `_paths_changed_by_this_execution` uses it as a git revision for the finalize delta (`ipd_lifecycle.py:1200`); `_intervening_commits_touching` re-diffs the same range (`:1225`). Also read at `ipd_lifecycle.py:1485` (finalize precheck) and re-emitted at `:3025`. | the five call sites above, located by name |
| F-7 | HIGH | and the code already documents the constraint | `begin`'s docstring: `isolated_baseline` "deliberately does NOT influence `base_head`" because finalize consumes it as a git revision and mixing sources "would silently corrupt the finalize delta". So the FROZEN value must not change; only what the advisory compares may. | `ipd_lifecycle.py:946-950` (in `begin`, NOT `run_begin`) |
| F-8 | MEDIUM | the fourth anti-expiry reason has STRENGTHENED | The item argued expiry misfires under isolation because a lane's base is deliberately not main's HEAD. Isolation is now the DEFAULT, so that is the common case rather than an exception. | `oc_runipd.py:7888-7891` (`--no-isolate-worktree`, `default=True`) |
| F-9 | MEDIUM | the stranding hazard has an instance again, so it is NOT lapsed | The item feared expiry stranding `6knsrx`, now `superseded/`. But `hp9rot` is a live receipt with 8 uncommitted lane files and 41 commits of distance: an expiry rule keyed on distance would revoke authority for work in progress TODAY. E-04 must report this instance, not an absence. | `aw find 6knsrx`; `git -C .aw/worktrees/hp9rot status --porcelain` |
| F-10 | MEDIUM | the advisory's input is a stabilized surface | `_paths_changed_by_this_execution` is documented as kept union-returning so `check_scope_drift` is unaffected, and `h9cn0y` worked at the split for that reason. Do not change its shape; consume `_changed_path_sources` instead if the halves must be told apart. | `ipd_lifecycle.py:1218-1222` docstring; `_changed_path_sources` `:1176` |
| F-11 | MEDIUM | the analogous problem was solved by OWNERSHIP, and it is ALREADY SHIPPED | `lbgzxg` attributed the finalize working-tree half on positive evidence rather than dirtiness; `h9cn0y` is `executed` and shipped `_execution_cohesive_committed_paths` for the committed half. It is available to call TODAY (F-3c measures what it yields), so nothing needs inventing or waiting. | `_working_tree_path_is_owned` `:1392`; `_execution_cohesive_committed_paths` `:1258`; `h9cn0y` Status `executed` |
| F-12 | LOW | the rule is explicitly best-effort locally, but fail-closed in CI | The hook records that hooks are local and skippable and that CI is the authoritative boundary; CI runs `aw check plans` fail-closed. Both are true and neither excuses the other. | `hooks/precommit_scope_gate.py:16-19`; `.github/workflows/tests.yml:153` |
| F-13 | LOW | a receipt for a terminal plan is not garbage | A `committed-incomplete` finalize journal re-runs finalize against a plan already in `executed/`, so ignoring a receipt is licensed while deleting one is not. | `_receipt_is_live` docstring `:1266` |
| F-14 | MEDIUM | `aw check plans` ALREADY exits 1 for reasons other than scope drift | At `3a3eaa79` it reports 193 findings across five rule codes (`check.scope-drift` 174, plus `lifecycle-transition-invalid`, `ipd-dependency-findings-blocked`, `review-finding-unescalated`, `review-decision-unescalated`). So no achievable reduction in scope-drift volume flips the CI exit code, which makes E-05's gate check a confirmation rather than a risk, and means volume alone cannot be argued as a CI hazard. | `aw check plans --agent` rule tally; unpiped `aw check plans; echo $?` = 1 |
| F-15 | MEDIUM | the collapse has NO existing count assertion to break | Every scope-drift test asserts emptiness or truthiness (`assertEqual([d.detail ...], [])` / `assertTrue(hits)`), never a count; the CI parity test compares the SET of `(rule, location)` pairs, which a collapse preserves. So the collapse is unusually cheap, and the new tests E-05 needs are additions rather than migrations. | `tests/test_check_engine_receipt_liveness.py` 7 assertions; `tests/test_event_derived_lifecycle.py:250-280`; `tests/test_ci_check_parity.py:87` |
| F-16 | LOW | one named test file already exists under a different name | `Scope-Paths` declares `tests/test_check_engine_scope_drift.py`, which does not exist; the scope-drift liveness tests live in `tests/test_check_engine_receipt_liveness.py`, and the rule's behavior tests in `tests/test_event_derived_lifecycle.py`. Creating the declared file is legitimate, but the executor must not assume the existing coverage is missing. | `ls tests/` ; the two files above |

## Proposed changes (ordered, validatable)

1. Re-measure the finding distribution per plan, with base, timestamp, age, directory, status, liveness, lane dirtiness and the committed/worktree split, and confirm the item's six named plans self-healed with receipts intact (E-01).
2. Collapse the per-file multiplication into one finding per plan carrying the count AND the paths, depending on E-01 alone so it is deliverable while OQ-01 is open (E-05).
3. Enumerate every `base_head` consumer and state whether the advisory genuinely needs the same field as the finalize delta (E-02).
4. Set out the five candidate baselines with each one's cost, including the already-shipped ownership option measured against the live receipts, choosing none (E-03).
5. Re-verify all four anti-expiry reasons plus the inverted-incentive fifth, and list the live receipts an expiry rule would revoke today (E-04).
6. Add a distinct advisory state for the live-but-misattributed case only if OQ-01 authorizes it, registered deliberately, else record the decision (E-06).

## Deferred / out of scope (with reason)

- RECEIPT EXPIRATION. Explicitly forbidden by the item as the presumed answer, with four recorded reasons that E-04 re-verifies rather than drops. Reason (4) has strengthened since isolation became the default. This plan will not implement expiry under any outcome of OQ-01.
- DELETING ANY RECEIPT. The item forbids it and `_receipt_is_live`'s docstring independently explains why (a `committed-incomplete` journal re-runs finalize against a terminal plan). The 20-odd receipts on disk stay exactly where they are; E-01 REPORTS on them and touches none.
- CHANGING WHAT `aw ipd begin` FREEZES, OR THE RECEIPT SCHEMA. `run_begin`'s docstring records that the frozen value is constrained by finalize's use of it as a git revision. This plan may change what the ADVISORY compares against; it must not change what is frozen.
- FINALIZE'S ATTRIBUTION. Owned by `h9cn0y` (now `executed`) for the committed half and by `lbgzxg` for the working-tree half. This plan touches the ADVISORY only, and must not change the union surface both depend on. Note the distinction that matters for E-03: CONSUMING `_execution_cohesive_committed_paths` from the advisory is in scope if OQ-01 authorizes it, while CHANGING that predicate or finalize's use of it is not.
- SURFACING A STALE BASE IN `aw doctor` OR `aw attention` (the item's question 6). Deferred: both are aggregate views with their own contracts, and adding a state to them before the state itself is decided (E-06, gated on OQ-01) would be backwards. Worth doing once there is a decided state to surface.
- WHAT SHOULD HAPPEN WHEN A PLAN HOLDING A RECEIPT IS RESUMED AFTER MAIN MOVED (the item's question 5). That is a LIFECYCLE decision about re-issuing, refusing, or re-basing execution authority, not an advisory one, and it belongs with whoever owns `begin`/`finalize` semantics. E-02's consumer analysis is the input such a plan would need; answering it here would mean changing execution authority from a plan scoped to a check rule.
- `xmqv5l` (begin freezes a whole-file digest so recording V evidence invalidates the receipt). Related defect in the same machinery, already `done`, and a different mechanism.
- THE `aw check` FINDING COUNT AS A TARGET. This plan is not a count-reduction exercise: E-05 reduces the count as a side effect of making one finding per cause, and E-05 must verify no rule CLASS changes, because several plans' validation sections compare classes rather than counts for exactly this reason. Measured at review, `aw check plans` exits 1 on four OTHER rule codes regardless, so no achievable change here turns CI green and nobody should claim it did.
- THE FOUR OTHER `aw check plans` RULE CODES. `check.lifecycle-transition-invalid` (15 locations at review), `check.ipd-dependency-findings-blocked`, `check.review-finding-unescalated` and `check.review-decision-unescalated` are unrelated defects in other plans' records. They are measured here only to establish that the CI exit code does not move; fixing them belongs to whoever owns those plans.

## Scope check

- Over-scope: none. One check rule and its test modules.
- Scope-Paths justification: `agent_workflows/check_engine.py` holds `check_scope_drift`, its per-path Drift loop, `_receipt_is_live` and `_plan_disposition`, i.e. E-05 and E-06 in full and the measurement surface E-01 and E-02 read; `tests/test_check_engine_scope_drift.py` is NEW (review verified no such file exists) and is where the collapse, the multi-plan case and the no-class-change property belong; `tests/test_receipt_stale_base.py` is new and covers the live-but-misattributed condition and whatever E-06 authorizes. Review ADDED two existing files that E-05 and E-06 must be able to touch and that were missing from the declaration: `tests/test_check_engine_receipt_liveness.py` (the seven liveness cases whose docstrings describe what the rule emits, and where a new liveness condition belongs beside its siblings) and `tests/test_event_derived_lifecycle.py` (the rule's behavior tests, whose `test_flags_out_of_scope_change` asserts on finding DETAIL and so is the one existing assertion a detail-string change could legitimately require updating). Declaring them is not a licence to rewrite them; it is so a needed one-line adjustment does not become an undeclared out-of-scope edit. `ipd_lifecycle.py` is deliberately NOT in scope even though E-02 must READ it and E-03 may CALL into it: this plan analyzes the consumers and changes only the advisory. If E-02 or E-03 concludes the advisory cannot be fixed without a lifecycle change, that is a FINDING and a follow-up plan, not a silent scope widening.
- Under-scope, stated rather than left as `none`: this plan does not implement expiry, deletes no receipt, changes nothing about what `begin` freezes or the receipt schema, does not touch finalize attribution or the union surface, does not surface a stale base in `aw doctor` or `aw attention`, does not answer the resume-semantics question, and does not treat the raw finding count as a target. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline re-measured at HEAD `3a3eaa79` on 2026-09-09: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL: it is caused by 189 untracked `opencode-recovery/*.md` files belonging to another party in this shared checkout, NOT by any code defect. DO NOT TRUST THAT TOTAL EITHER: the plan first recorded `1 failed, 5648 passed` with a different failing node id one day earlier. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- THE PER-PLAN DISTRIBUTION measured before and after, from `check_scope_drift` directly, with the per-location counts pasted. Review baseline: 174 findings from three plans (81/75/18). Your numbers WILL differ; measure your own.
- THE COMMITTED/WORKTREE SPLIT per contributor, pasted, since it is what justifies the shape of the fix. Review measured 100 percent committed.
- A COLLAPSE TEST from a FIXTURE (a throwaway repo with a plan, a receipt, and several out-of-scope intervening files) asserting ONE finding per plan carrying the count AND the paths, and asserting the finding's `recovery` field is still populated so the pre-commit hook's teaching message survives. Do not assert against live repository state, which drifts by the hour.
- A MULTI-PLAN FIXTURE CASE: two plans each holding a live receipt with out-of-scope changes must yield exactly TWO findings, one per plan, not one merged finding. The collapse must be per plan, and nothing in the current single-plan fixtures would catch a global merge.
- A NO-CLASS-CHANGE ASSERTION: the set of `check.*` rule codes emitted repo-wide before and after must be identical unless OQ-01 authorized a new code, in which case name it. Paste both sets. Review baseline: five codes, `check.scope-drift` plus `check.lifecycle-transition-invalid`, `check.ipd-dependency-findings-blocked`, `check.review-finding-unescalated`, `check.review-decision-unescalated`.
- A `(rule, location)` SET COMPARISON before and after, because that is the pair `tests/test_ci_check_parity.py` compares; it must be IDENTICAL, which is the strongest available statement that the collapse changes volume and nothing else.
- A REAL-DRIFT PRESERVATION TEST: a plan genuinely touching three undeclared paths must still name all three; the collapse must not hide a small real drift.
- LIVENESS REGRESSION: the existing behavior that a TERMINAL plan's receipt and an UNREACHABLE base are both ignored must be unchanged, and the fail-safe direction (undeterminable means skip) preserved. Run and paste `tests/test_check_engine_receipt_liveness.py` (all seven cases a-g) and `tests/test_event_derived_lifecycle.py`.
- THE HOOK SURFACE, not only the engine: run `hooks/precommit_scope_gate.check` on a fixture and paste its messages, since `tests/test_phase4_hooks.py` asserts the hook names the rule, prints `fix:`, and mentions `Scope-Paths`. A collapsed detail string must keep all three true.
- A CI-GATE CHECK: `aw check plans` unpiped exit code before and after. Review measured 1 both before and (necessarily) after, since four other rule codes hold it there; state that rather than implying the collapse cleared CI.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`check_scope_drift`'s DOCSTRING is the authoritative prose on what the rule asks and must be updated to say what the finding now REPRESENTS (one per plan, carrying a count and the paths) rather than one per offending file. It already documents the liveness narrowing and the grandfathered-sentinel behavior; extend it rather than replacing it, since both record reasoning that must survive.

`_receipt_is_live`'s DOCSTRING must gain the case it does NOT cover, because that absence is exactly what this graduation had to discover by measurement: a plan in `pending/` whose base IS an ancestor of HEAD can still be arbitrarily far behind (41 to 139 commits, measured across three live receipts) while its lane is actively being worked, so liveness as defined is not distance and distance is not staleness. State it even if E-06 adds no new state, so the next reader does not conclude the two tests are exhaustive.

No spec change is expected. `check.scope-drift` is an engine rule rather than a spec-defined contract. If the executor finds spec text asserting that scope drift reports one finding per offending path, declare that spec file in `Scope-Paths` before editing it, per the spec-amendment rule, and record the reason here.

Write no em or en dashes in any user-facing finding message this plan produces.

EXECUTED 2026-09-22, recorded here because the section above is the plan's prediction and this is the outcome. `check_scope_drift`'s docstring was EXTENDED (not replaced): it now records WHICH TREE is measured and why, the accepted cost of silence in a shared main checkout, and that a finding is now one-per-plan carrying a count and the paths. `_receipt_is_live`'s docstring gained the case its two tests do NOT cover (live-and-far-behind), stated even though E-06 added no new state, so the next reader does not conclude the two tests are exhaustive. A new `_plan_execution_tree` carries OQ-01's ruling, the withdrawal of candidate (e) with its measured figures, and the accepted-cost paragraph nobody may later reverse as an oversight. `check_commit_invariants`' rule list was updated in the same file, since it describes `check.scope-drift` to every reader of the aggregator.

NO SPEC CHANGE WAS NEEDED, as predicted. Searched for spec text asserting the rule's shape (`grep -rn "scope-drift" .aw/records/specs/ docs/`): no spec mentions `check.scope-drift` at all, and the only non-engine mentions are two one-line CLI/installer help strings naming the rule in a list (`cli.py:5547`, `engine.py:5616`), neither of which asserts one-finding-per-path or which tree is measured, so neither needed editing. No `.spec.md` file was touched and none is declared in `Scope-Paths`.

SCOPE-PATHS WAS WIDENED ADDITIVELY, and it must be said here rather than left to the diff: `tests/test_phase4_hooks.py` and `tests/test_finalize_scope_ownership.py` were added. Both are EXISTING tests whose arrangements place an out-of-scope change in the MAIN tree and assert the advisory fires; under tree selection that arrangement is silent by design, so each had to move its change into the plan's lane or become a vacuous pass. The plan could not have named them when authored, because all five of its candidate BASELINES would have left both untouched; only the TREE answer moves them. Both entries are literal file paths (`scope_entry_is_literal_file` -> True for each), so the widening is eligible under `rcptwiden 63425h`; no entry was removed; no assertion in either file was deleted or weakened. Reasoned in full as decision D1 of this turn's register.

## Open questions

### OQ-01: What should the frozen base MEAN for the advisory once HEAD has moved far past it?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): MEASURE THE ISOLATED LANE WHEN THERE IS ONE, AND REPORT NOTHING WHEN THERE IS NOT. The advisory's subject is a lane-isolated execution's own tree, not the shared main checkout, and it must stay SILENT for work performed directly in a shared main rather than attributing co-workers' commits to the plan under audit.
  THE MAINTAINER OVERTURNED THIS PLAN'S FRAMING AND THE REVIEW'S, AND THE MEASUREMENT CONFIRMED THEM, so the record must not be read as the plan's own recommendation having been accepted. Asked which of the five baselines to adopt, with candidate (e) (commit-cohesion attribution) recommended, they answered with a question instead: "This was intended to work on things like IPDs worked on in isolated worktrees not in items worked on in main. Did we change the scope? Was it not made clear? Do we need to change the scope? I don't see a way to do this in main if more than one entity (human or agent) is working on main." That is correct, and it makes every one of the five candidates the wrong axis: they all argue about WHICH BASELINE to compare against while the defect is WHICH TREE is being measured.
  THE DECIDING MEASUREMENT, taken at HEAD `0cfe9bb6` on 2026-09-10 and reproducible with `_paths_changed_by_this_execution` called against each tree with the SAME fence (`.aw/state/`+`.aw/worktrees/` prefix skip, `_is_implicitly_allowed`, `_scope_match`). For `hp9rot`, the one contributor with a live lane (`git worktree list` shows `.aw/worktrees/hp9rot` at `8c06675c`): measured IN THE LANE, 8 changed paths and ZERO out of scope; measured IN MAIN, 121 changed paths and 23 out of scope. The plan is CLEAN and the advisory reports 23 violations, all of them other agents' commits. The rule reads whichever tree the command happens to run in and is never told the execution lives elsewhere.
  THE SCOPE WAS NEVER NARROWED; IT WAS NEVER EXPRESSED. `_baseline_ambiguity` (`ipd_lifecycle.py:863-899`) already takes an `isolated_baseline` switch and its docstring states the isolated case must be measured differently because "uncommitted work in THIS tree cannot reach that lane"; that distinction was never carried into `check_scope_drift`, which calls the union-returning `_paths_changed_by_this_execution` against `repo_root` (`check_engine.py:1375`). `_paths_changed_by_this_execution`'s own docstring concedes it "is a TIME WINDOW, NOT AN ATTRIBUTION" and that `check_scope_drift` is "deliberately NOT ownership-filtered" (`ipd_lifecycle.py:1199-1221`), so the over-report was documented at the call site and never fixed at it.
  CANDIDATE (e) IS WITHDRAWN, NOT DEFERRED, and the reviewer's own recommendation with it. Its 79 percent cut (174 -> 37, re-measured this session: 81->21, 75->7, 18->9) is real but it is compression of a misdirected measurement: none of the surviving 37 is verified to be the author's own work, and adopting a two-sided heuristic to soften numbers produced by reading the wrong tree would have bought quiet at the cost of a documented false-excuse path. Measuring the lane yields 0 findings on evidence rather than 37 on a guess.
  ACCEPTED COST, STATED BECAUSE IT IS A REAL LOSS OF COVERAGE. Work performed by hand directly in the shared main checkout gets NO scope advisory at all under this answer. The maintainer accepted that explicitly, on the ground that no honest attribution exists there when several parties share the tree; the offered variant that additionally prints a "scope not checked, not lane-isolated" line was declined in favor of the plain silent form. Nobody may later reintroduce a main-checkout comparison on the argument that coverage was lost by oversight.
  CONSEQUENCE FOR THIS PLAN, which E-01 to E-06 must be re-read against: the deliverable is now a TREE-SELECTION fix, not a baseline choice. E-05's per-plan collapse remains correct and still depends on E-01 alone, but note it now collapses a set measured at 0 for lane-isolated work, so its value is in the shared-checkout-silence path and in future lane findings rather than in compressing today's 174.

### OQ-02: Should the live-but-misattributed case get its own rule code, and under what name?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEPENDS ON OQ-01 AND IS DELIBERATELY SUBORDINATE TO IT. The item's question 4 asks whether reporting this AS scope drift is a mislabelling rather than only a volume problem, and F-5/F-5b show the condition is real and uncovered: live by both existing tests, 41 to 139 commits behind, with the plan itself having drifted nowhere. But a new `check.*` code is a new contract that CI and every plan's validation section then compares against, and an unregistered id silently defaults to `error` with an empty invariant, so it must not be minted as a convenience.
  THE NAME IS PART OF THE QUESTION, which review added. The item proposed `check.receipt-base-stale`; the measurement argues that spelling is wrong, because nothing about these bases is stale in the sense of incorrect and the observable defect is that intervening commits are attributed to this plan. A name keyed on staleness would teach every future reader the diagnosis review just disproved. Whether to name it for the age or for the misattribution is the maintainer's call, and E-06 must record whichever is chosen with its reason.
  E-06 is written so that RECORDING the decision not to add a code is a legitimate completed outcome, which is why this is non-blocking: the plan finishes either way, and the answer only decides whether E-06 writes code or prose.
  ANSWERED IN THE NEGATIVE BY EXECUTION, 2026-09-22, and left `open` for the maintainer because the NAME is theirs to choose if they ever want one. E-06 added NO rule code and recorded the decision in prose, for a reason OQ-01's resolution created rather than one this plan foresaw: tree selection REMOVES the condition a new state would have reported. Measured this turn, 380 findings from six plans became 4 findings from four, and every survivor is lane-local work genuinely outside that plan's fence, so there is no longer a population of live-but-misattributed findings needing a distinct label. Minting a CI-visible contract for an eliminated condition would be cost with no signal, and the item's proposed spelling (`check.receipt-base-stale`) is the one the measurement disproves, since nothing about these bases is stale in the sense of incorrect. If a maintainer later wants the shared-main-checkout SILENCE made visible, that is a new question (OQ-01 explicitly declined a "scope not checked, not lane-isolated" line), not this one.

### OQ-03: Is the advisory worth keeping at all for a plan whose base is very old?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, KEEP IT, and this is settled by the item's own analysis rather than needing a new decision. The item states the rule "is not simply wrong: it is answering the question it was asked, and that question is genuinely useful for a plan mid-execution in a tree that is moving under it". The defect is that the question stops being MEANINGFUL once the base is no longer a plausible baseline, and that nothing notices the transition. So the answer is never to delete the rule; it is to make it report proportionately (E-05) and, if OQ-01 so decides, to attribute it correctly (E-06). Removing the advisory would lose the only signal that a plan is editing territory it never declared, which is the failure D141 built this machinery to surface.
  REVIEW STRENGTHENED THIS RESOLUTION and it now rests on measurement rather than only on the item's prose. The rule is not merely useful in principle: it is the only in-tree check on a plan's declared fence between `begin` and `finalize`, it is what the opt-in pre-commit gate teaches from, and it runs fail-closed in CI (`.github/workflows/tests.yml:153`). Note also that its volume is NOT what holds CI red today: four other rule codes do that independently, so nobody may argue for removing the rule on the grounds that it is what fails the build.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL per-plan distribution you measured, with counts per location, plus for each contributor its `base_head`, receipt `timestamp`, lifecycle directory, plan `- Status:`, commits-since-base, `_receipt_is_live` verdict, and the lane-worktree dirtiness output (`git -C .aw/worktrees/<id> status --porcelain`, or an explicit "no lane"). THEN paste the per-contributor committed-only / worktree-only / both split from `_changed_path_sources` with the same fence applied, and say in one sentence whether the noise is committed history. THEN paste the membership check showing whether the item's six named plans (`qcqhj7`, `58ha43`, `2c122z`, `rchpms`, `j4v6ga`, `2ouj70`) are still unenumerated, and confirm each of their receipt FILES still exists. A missing receipt is a finding to report, not a tidy-up.
  - Observed evidence: MEASURED AT HEAD `132e8333` on 2026-09-22, in lane `.aw/worktrees/wmnmei`. Every figure below is my own; none is inherited. The pre-change rule (main tree, one finding per path) yielded **380 findings from exactly SIX plans**, not the 174-from-three the review measured nor the 110-from-eight this plan authored nor the item's 1013-from-16: the distribution has now moved a FOURTH time, which is the plan's own F-1 holding.

```
plan files iterated: 68 | plans with a LIVE receipt + fence: 6

id6     base      timestamp             dir      status      age  live  lane         lane tree
m7gvuz  b5208b0e  2026-09-19T04:37:15Z  pending  approved    344  True  ABSENT       no lane
qdd5jq  54c7f5fb  2026-09-20T21:39:24Z  pending  approved    151  True  HOLDS-WORK   0 dirty
li44r9  ee20e831  2026-09-22T04:28:42Z  pending  approved     31  True  HOLDS-WORK   0 dirty
lc4unl  c49c9027  2026-09-22T07:10:05Z  pending  approved     12  True  HOLDS-WORK   0 dirty
xipfy1  d1d6b6eb  2026-09-22T07:44:46Z  pending  approved      7  True  HOLDS-WORK   0 dirty
wmnmei  132e8333  2026-09-22T08:26:01Z  pending  approved      0  True  HOLDS-WORK   7 dirty
```

All six sit in `pending/`, all six are `approved`, and `_receipt_is_live` returns **True for all six** while they are 0 to 344 non-merge commits behind, so live-and-far-behind is confirmed as a condition neither existing liveness test captures (F-5 holds). Five of the six hold a lane worktree; `m7gvuz` has NONE (`inspect_lane` -> `ABSENT`).

COMMITTED / WORKING-TREE SPLIT of the out-of-scope set, per contributor, from `_changed_path_sources` with the SAME fence (`.aw/state/`+`.aw/worktrees/` prefix skip, `_is_implicitly_allowed`, `_scope_match`):

```
m7gvuz: committed-only=212 worktree-only=3 both=4 | old-rule findings=219
qdd5jq: committed-only=93  worktree-only=6 both=1 | old-rule findings=100
li44r9: committed-only=21  worktree-only=7 both=0 | old-rule findings=28
lc4unl: committed-only=11  worktree-only=7 both=0 | old-rule findings=18
xipfy1: committed-only=6   worktree-only=7 both=0 | old-rule findings=13
wmnmei: committed-only=0   worktree-only=2 both=0 | old-rule findings=2
TOTALS: committed-only=343 worktree-only=32 both=5
```

IN ONE SENTENCE: the noise is overwhelmingly COMMITTED intervening history (343 of 380, i.e. 90 percent, with 32 worktree-only and 5 in both), so F-3b's direction holds but its ABSOLUTE claim does NOT - review measured 0 percent working-tree and I measure 8 percent, because this shared checkout now carries dirty files (including my own edits) that it did not then. I am recording the correction rather than restating the 100/0 split.

THE SIX NAMED PLANS from item `v880xk`, re-verified: all six remain UNENUMERATED by the scan and all six receipt FILES are intact. None was deleted, so the item's prohibition was honored.

```
qcqhj7: enumerated_by_scan=False receipt_file_exists=True
58ha43: enumerated_by_scan=False receipt_file_exists=True
2c122z: enumerated_by_scan=False receipt_file_exists=True
rchpms: enumerated_by_scan=False receipt_file_exists=True
j4v6ga: enumerated_by_scan=False receipt_file_exists=True
2ouj70: enumerated_by_scan=False receipt_file_exists=True
receipt count on disk: 30
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the consumer table with the ACTUAL search output enumerating every read of `base_head` across the package and hooks. Quote `run_begin`'s constraint sentence verbatim. State in one sentence per consumer whether it needs the same field as the others, and give an explicit verdict on the overload question; "unclear" is an acceptable verdict if the evidence genuinely does not settle it, but silence is not.
  - Observed evidence: EVERY read of `base_head` across the package, located by search (`grep -rn "base_head" agent_workflows/ --include=*.py`), including `agent_workflows/hooks/` which has NONE:

```
ipd_lifecycle.py:1467   "base_head": head,                      <- the WRITER (begin builds the receipt)
ipd_lifecycle.py:1564   diff --name-only {base_head}..HEAD      <- _changed_path_sources (GIT REVISION)
ipd_lifecycle.py:1603   _changed_path_sources(...).union()      <- _paths_changed_by_this_execution
ipd_lifecycle.py:1617   diff --name-only {base_head}..HEAD      <- _intervening_commits_touching (GIT REVISION)
ipd_lifecycle.py:1748   merge-base --is-ancestor sha base_head  <- _run_record_committed_paths window filter
ipd_lifecycle.py:1815   log --no-merges ... {base_head}..HEAD   <- _execution_cohesive_committed_paths
ipd_lifecycle.py:2036   receipt.get("base_head")                <- finalize_precheck: REFUSES without a usable one
ipd_lifecycle.py:2044   evidence["base_head"]                   <- finalize evidence record
ipd_lifecycle.py:4253   "base_head": receipt["base_head"]       <- run_begin re-emits it in its payload
runner_shared.py:5340   receipt.get("base_head")                <- audit-target basis selection
check_engine.py:2127    receipt.get("base_head")                <- _receipt_is_live ancestry test
check_engine.py:2290    receipt.get("base_head")                <- check_scope_drift (THE ADVISORY)
agent_workflows/hooks/: (no reads under hooks/)
```

`ipd_set_plan.py`'s `ExecutionManifest.base_head` (:773, :792, :818, :899, :934, :1110) is a DIFFERENT field with the same name, a Set-level manifest rather than a receipt, and is NOT conflated here.

CONSUMER TABLE, one verdict sentence each:

| Consumer | What it needs from the field | Same field as the others? |
|---|---|---|
| `_changed_path_sources` / `_paths_changed_by_this_execution` | a GIT REVISION it can put on the left of `base..HEAD` | YES: it must be the exact frozen commit or the finalize delta is wrong |
| `_intervening_commits_touching` | the same revision RANGE, re-diffed for in-scope collisions | YES: it is the same range by construction |
| `_run_record_committed_paths` / `_execution_cohesive_committed_paths` | the same range, as a membership/anchoring window | YES |
| `finalize_precheck` | a USABLE base, refusing (`EXIT_CANNOT_RUN`) without one | YES: this is the authority read |
| `run_begin` payload / `runner_shared` audit basis | an opaque identifier to REPORT | INDIFFERENT: it only echoes the value |
| `_receipt_is_live` | a commit whose ANCESTRY of HEAD it can test | YES, and note it tests ancestry in THIS tree |
| `check.scope-drift` (the advisory) | a baseline to compare a changed set against | **NO** |

`begin`'s constraint sentence, quoted VERBATIM from `ipd_lifecycle.py` (the docstring of `begin`, NOT of `run_begin`, which is the thin CLI entry point):

> ``isolated_baseline`` deliberately does NOT influence ``base_head``. The receipt's ``base_head`` is
> always captured from ``repo_root`` because finalize consumes it as a GIT REVISION
> (``_paths_changed_by_this_execution`` diffs ``base..HEAD``, and ``_intervening_commits_touching``
> re-diffs the same range); a lane's HEAD is not this tree's HEAD and is not even its ancestor, so
> sourcing both from one "execution tree" would silently corrupt the finalize delta.

VERDICT ON THE OVERLOAD QUESTION, explicit: the field IS overloaded, but NOT in the way this plan assumed. Six of the seven consumers want the identical thing, an exact git revision, and the frozen value is therefore correctly constrained and was not changed. The ADVISORY is the one consumer with a different need, and its need is not a different BASELINE at all - it is a different TREE. That is what made all five of E-03's candidates the wrong axis, and it is why the fix changes only which tree the advisory measures while leaving the frozen value, the union surface's shape, and every other consumer untouched.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the FIVE-row candidate table naming, per option, what it reports correctly, what it misses, and whether it addresses misattribution or only volume. Paste the re-measured cohesion figures for candidate (e) (`_execution_cohesive_committed_paths` over each live receipt, same fence) alongside the unattributed counts, and quote its docstring's own statement that cohesion errs in both directions. Paste what you read from `lbgzxg` and state explicitly whether ownership-based attribution is available to the advisory. Confirm in one sentence that NO option was selected and that `_paths_changed_by_this_execution`'s shape and value were not changed.
  - Observed evidence: THE CANDIDATE TABLE, with candidate (f) added because OQ-01's answer is not among the five this plan enumerated:

| # | Candidate | What it reports correctly | What it misses | Misattribution or only volume? |
|---|---|---|---|---|
| (a) | the frozen base, main tree (status quo) | every path that changed in the window, so it never misses the plan's own drift | nothing changed by the plan is missed; everything ELSE is falsely included | neither: it IS the misattribution |
| (b) | merge-base of frozen base and HEAD | identical to (a) here | identical to (a): measured 380 findings, byte-identical totals, because the base IS an ancestor so merge-base == base | only volume, and it reduces none |
| (c) | the plan's OWN commits | would be exact if it existed | NOT MEASURABLE: no channel names this execution's commits (no `AW-Run`/`AW-Item` trailers in history, backlog `a8eufb`), so it is only approximable BY cohesion and collapses onto (e) | misattribution in principle, unavailable in fact |
| (d) | skip once the base is "stale" by some measure | nothing; it deletes the signal for the plans that need it most | fires HARDEST on the most active execution: `wmnmei` is 0 commits behind with 7 dirty lane files, `qdd5jq` is 151 behind and clean | only volume, and keyed on the wrong variable |
| (e) | frozen base, main tree, COHESION-attributed | narrows to commits that touched declared territory: 380 -> 162 (57 percent cut) | none of the surviving 162 is VERIFIED to be the author's work; two-sided heuristic error | misattribution, partially, by heuristic |
| (f) | **measure the plan's ISOLATED LANE; report nothing when there is none** | 380 -> 17 offending paths in 4 findings, each lane-local and attributable on EVIDENCE | hand work in a shared main checkout gets no advisory at all (the accepted cost) | misattribution, on evidence rather than heuristic |

CANDIDATE (e) RE-MEASURED myself, per live receipt, with the same fence, alongside the unattributed counts and the lane figures:

```
id6      unattributed  cohesion  lane
m7gvuz            219       102     0   (no lane -> silent)
qdd5jq            100        43     5
li44r9             28         8     9
lc4unl             18         5     0   (lane base not an ancestor of lane HEAD -> silent)
xipfy1             13         4     1
wmnmei              2         0     2
TOTAL             380       162    17
```

My cohesion cut is 57 percent (380 -> 162), NOT the 76/79 percent review measured; the ratio moved with the distribution, so it is recorded rather than inherited. Cohesion's own docstring states its cost verbatim:

> ACCEPTED COST, stated because it is real and is the reason the fail-closed tests matter. Cohesion
> is a HEURISTIC, not proof of authorship, and it errs in both directions. A co-worker who touches
> one of this plan's declared paths in the same commit as unrelated files makes those files look
> like this plan's (a false DEMAND, which is fail-closed and merely annoying). An executor who
> commits an out-of-scope path in a commit containing NO declared path escapes the reason
> requirement (a false EXCUSE, and the genuine weakening).

Note `9kmbr0` (a contributor in an earlier pass this session) measured `anchored=False`, the fail-closed switch firing exactly as documented: with no recognizable commit footprint, cohesion knows nothing and the caller must leave the committed half unfiltered.

WHAT TRANSFERRED FROM `lbgzxg`, read this turn: it attributed the finalize WORKING-TREE half on positive evidence rather than dirtiness, and its reasoning survives in `_working_tree_path_is_owned`'s docstring (a documented misnomer that now judges both halves) - that demanding a reason for an unowned path forces a plan either to write a false claim into its permanent record or to block on a condition it does not control. `h9cn0y` then shipped `_execution_cohesive_committed_paths` for the committed half and is `executed`, so ownership-based attribution IS available to the advisory today and needed no invention. Measured above as candidate (e).

AND IT WAS NOT ADOPTED, which is the finding. OQ-01's resolution WITHDRAWS (e) rather than deferring it: its cut is real but it compresses a misdirected measurement, so 17 paths measured in the right tree beats 162 guessed in the wrong one. NO OPTION WAS SELECTED BY ME: the selection is the maintainer's, recorded in OQ-01 on 2026-09-10, and I implemented that answer. `_paths_changed_by_this_execution` was NOT changed in shape or in value - it is still the union-returning surface, still consumed by finalize unchanged, and `tests/test_finalize_scope_ownership.py::ChangedPathSourcesSplitTests` (25 passed) pins that; what changed is the TREE the advisory passes to it.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: for each of the four anti-expiry reasons, paste the evidence showing it still holds or has changed, including the isolation default for reason (4) located by name. State reason (5) with your evidence or say why your measurement does not support it. THEN state explicitly whether any CURRENTLY LIVE receipt would be revoked by an expiry rule today, with the LIST and, for each, its lane dirtiness (or an evidenced none). Paste proof that no expiry mechanism was implemented and that no receipt file was deleted (`git status` plus a `.aw/state/ipd-lifecycle/` listing with its count).
  - Observed evidence: EACH of the four rejection reasons re-checked at HEAD `132e8333`, plus the fifth.

REASON (1), a receipt IS execution authority: HOLDS, and its mechanism is unchanged. `finalize_precheck` reads the base off the receipt and returns cannot-run without a usable one:

```
ipd_lifecycle.py:2036   base_head = str(receipt.get("base_head") or "").strip()
ipd_lifecycle.py:2037   if not base_head or base_head == "unversioned":
ipd_lifecycle.py:2038       return (EXIT_CANNOT_RUN, f"the begin receipt for {plan_id} has no usable base HEAD; ...")
```

AND IT HAS FIVE LIVE INSTANCES TODAY, so it is emphatically not lapsed. This is the explicit LIST an expiry rule keyed on distance would revoke right now:

```
  wmnmei:    0 commits behind | lane HOLDS-WORK | 7 dirty | receipt ts 2026-09-22T08:26:01Z
  lc4unl:   12 commits behind | lane HOLDS-WORK | 0 dirty | receipt ts 2026-09-22T07:10:05Z
  xipfy1:    7 commits behind | lane HOLDS-WORK | 0 dirty | receipt ts 2026-09-22T07:44:46Z
  li44r9:   31 commits behind | lane HOLDS-WORK | 0 dirty | receipt ts 2026-09-22T04:28:42Z
  qdd5jq:  151 commits behind | lane HOLDS-WORK | 0 dirty | receipt ts 2026-09-20T21:39:24Z
  m7gvuz:  344 commits behind | lane ABSENT     |   n/a   | receipt ts 2026-09-19T04:37:15Z
```

Five of the six hold a lane classified `HOLDS-WORK`, i.e. commits beyond its base or a dirty tree, which is work in flight. Any distance threshold above 0 revokes at least `qdd5jq` and `m7gvuz`; any threshold at or below 12 also revokes `lc4unl`; and my OWN receipt (`wmnmei`, 7 dirty lane files) would be revoked by any WALL-CLOCK rule tighter than hours. Review's single instance (`hp9rot`) is gone from the tree; five new ones replaced it, which is the regeneration F-2b describes.

REASON (2), "too far" has no principled definition: HOLDS, and this measurement sharpens it. The three plausible metrics DISAGREE on the ordering of the same six plans. By commit distance the worst offender is `m7gvuz` (344); by wall-clock age it is also `m7gvuz` (3 days); but by LANE ACTIVITY the healthiest is `wmnmei` (0 behind, 7 dirty) and the most abandoned is `m7gvuz` (no lane at all). So distance and abandonment are not the same variable, and no threshold on distance can express "abandoned".

REASON (3), expiry treats the symptom rather than the question: HOLDS, and it is now demonstrated rather than argued. The question ("what should the advisory compare against") turned out to be the wrong question entirely (which TREE), and no expiry rule would have discovered that; it would have silenced the symptom and left the misattribution in place for every plan under the threshold.

REASON (4), it interacts with worktree isolation: HOLDS and has STRENGTHENED, exactly as the plan predicted. Isolation is the DEFAULT, located by name in `oc_runipd.py`:

```
        dest="isolate_worktree",
        action="store_false",
        default=True,
        help="Do not isolate each execute turn in its own git worktree; run in the main tree "
        "instead. Default: each IPD executes in an isolated worktree and its verified branch is "
        "integrated back to main.",
```

So distance-from-HEAD is the NORMAL state of a correct isolated turn, and under OQ-01's answer the lane is now the rule's SUBJECT rather than an exception to it, which strengthens reason (4) further still.

REASON (5), STATED and supported by my own measurement: expiry and every age-keyed variant (including candidate (d)) fire HARDEST on the most active execution, because a fast-moving main accrues distance fastest precisely while a plan is being worked. Evidence: `qdd5jq` is 151 commits behind with a `HOLDS-WORK` lane, while `m7gvuz`, the one plan with NO lane at all and therefore the best abandonment candidate, is distinguished from it by distance only as 344-versus-151, a difference of degree that no threshold can turn into a difference of kind. Inverting the intent is exactly what the item warned of.

NO EXPIRY WAS IMPLEMENTED AND NO RECEIPT WAS DELETED. Proof, both directions:

```
$ git status --porcelain            # (nothing under .aw/state/; receipts are gitignored anyway)
 M agent_workflows/check_engine.py
 M tests/test_check_engine_receipt_liveness.py
 M tests/test_event_derived_lifecycle.py
 M tests/test_finalize_scope_ownership.py
 M tests/test_phase4_hooks.py
?? tests/test_check_engine_scope_drift.py
?? tests/test_receipt_stale_base.py

$ ls .aw/state/ipd-lifecycle/*.receipt.json | wc -l
30
```

30 receipts before, 30 after; the count is unchanged and includes all six of the item's named plans. `tests/test_receipt_stale_base.py::NoExpiryTests::test_the_rule_never_removes_a_receipt` pins the read-only property in a fixture (30 commits of distance, receipt still present with its original `base_head`), and `test_no_distance_or_age_field_gates_the_advisory` pins that the verdict does not change with distance alone.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the ACTUAL passing output of the fixture-based collapse test, and quote the assertion showing the finding carries BOTH the count and the paths AND a non-empty `recovery`. Paste the MULTI-PLAN fixture case proving two contributing plans yield exactly two findings. Paste the real-drift preservation test showing a three-path drift still names all three. Paste the hook-surface output from `precommit_scope_gate.check` on a fixture, showing it still names the rule, prints `fix:` and mentions `Scope-Paths`. Paste the per-plan distribution before and after; the two repo-wide rule-code SETS, confirming they are identical (or naming the one code OQ-01 authorized); and the before/after `(rule, location)` SET comparison. Paste `aw check plans`' unpiped exit code before and after, and state plainly which other rule codes hold it where it is.
  - Observed evidence: THE FIXTURE-BASED COLLAPSE TESTS, actual passing output (`tests/test_check_engine_scope_drift.py`, the file this plan declared and which did not previously exist):

```
$ python3 -m pytest tests/test_check_engine_scope_drift.py
.........                                                                [100%]
9 passed in 4.95s
```

THE COUNT AND THE PATHS TOGETHER, quoted from the passing assertion (`test_many_offending_paths_yield_exactly_one_finding_naming_the_count`), which asserts BOTH halves deliberately because a count-only finding would be as unusable as the volume it replaced:

```python
        self.assertEqual(len(hits), 1, ...)
        detail = hits[0].detail
        self.assertIn("5 changed paths are outside", detail)
        for rel in rels:
            self.assertIn(rel, detail,
                f"the collapsed finding dropped {rel!r}; a count without the paths is unactionable: ...")
```

AND A NON-EMPTY `recovery` (`test_the_finding_still_carries_a_populated_recovery_for_the_hook`):

```python
        self.assertTrue(hit.recovery, "recovery must stay populated")
        self.assertIn("Scope-Paths", hit.recovery)
        self.assertTrue(hit.observed, "observed must stay populated")
        self.assertIn("other/f.py", hit.observed)
```

THE MULTI-PLAN CASE, proving the collapse is per PLAN and not global (`MultiPlanTests::test_two_contributing_plans_yield_two_findings_one_each`): two plans, each with its own lane, yield exactly TWO findings; the first names `other/one.py` and `other/two.py` and `assertNotIn("other/three.py", first)` proves one plan's finding does not absorb another's paths.

THE REAL-DRIFT PRESERVATION TEST (`test_a_real_three_path_drift_still_names_all_three`): a three-path drift still names all three AND states `"3 changed paths"`. A small genuine drift is not hidden.

THE HOOK SURFACE, run on a fixture through `precommit_scope_gate.check` (not merely the engine), with its ACTUAL message:

```
HOOK exit: 1
  - /tmp/.../20260828-t-01-aaa111-x.ipd.md: check.scope-drift: 3 changed paths are outside the plan's declared Scope-Paths: 'other/a.py', 'other/b.py', 'other/c.py'
      fix: restrict the change to Scope-Paths, or declare the path in the plan's Scope-Paths (then re-`aw ipd begin`), or reconcile it at `aw ipd finalize`

names rule: True
prints fix: True
mentions Scope-Paths: True
```

All three promises `tests/test_phase4_hooks.py` asserts survive the collapsed detail string, and that suite passes (10 passed).

THE PER-PLAN DISTRIBUTION BEFORE AND AFTER (both computed at the same HEAD `132e8333` from the same tree state, the BEFORE column being the old rule's main-tree/one-per-path shape):

```
id6       OLD findings  NEW findings  NEW paths  reason
m7gvuz             219             0          0  no usable lane (ABSENT) -> silent
qdd5jq             100             1          5
li44r9              28             1          9
lc4unl              18             0          0  no usable lane (HOLDS-WORK, base not ancestor) -> silent
xipfy1              13             1          1
wmnmei               2             1          2
TOTAL              380             4         17
```

380 findings -> 4 findings. Two effects compose and are separable: the COLLAPSE alone would have given 6 findings (one per contributing plan), and TREE SELECTION silences the two plans with no usable lane.

THE ACTUAL COLLAPSED FINDINGS now emitted repo-wide:

```
2 changed paths are outside the plan's declared Scope-Paths: 'tests/test_finalize_scope_ownership.py', 'tests/test_phase4_hooks.py'
5 changed paths are outside the plan's declared Scope-Paths: 'agent_workflows/ipd_lint.py', 'agent_workflows/status_set.py', 'tests/test_lifecycle_palette_singleness.py', 'tests/test_refusal_surfacing.py', 'tests/test_runner_refork_guard.py'
9 changed paths are outside the plan's declared Scope-Paths: 'tests/test_dirty_base_gate.py', 'tests/test_lane_allocation_idempotent.py', 'tests/test_lane_clean_base.py', 'tests/test_lane_tool_identity.py', 'tests/test_nested_tty_noninteractive.py', 'tests/test_runner_shared.py', 'tests/test_runner_stop.py', 'tests/test_rununify_main.py', 'tools/runner_fork_scan.py'
1 changed path is outside the plan's declared Scope-Paths: 'tests/test_runner_refork_guard.py'
```

The first is MY OWN plan's lane, correctly reporting the two existing test files this change had to touch; it is declared as an additive widening rather than suppressed (see decision D1). Every finding names other-plan lane work that is genuinely out of those plans' declared fences, so each remaining finding is now a REAL signal.

THE `(rule, location)` SET, the pair `tests/test_ci_check_parity.py:87` compares, verified rather than assumed:

```
('check.scope-drift', '20260908-rcptstale-01-wmnmei-...ipd.md')
('check.scope-drift', '20260908-retrywire-01-xipfy1-...ipd.md')
('check.scope-drift', '20260917-hostdedup-01-li44r9-...ipd.md')
('check.scope-drift', '20260919-lifeglyph-07-qdd5jq-...ipd.md')
```

The RULE is unchanged and each LOCATION is a plan file, exactly as before, so collapsing N findings for one plan preserves the pair by construction. The set SHRANK (the two silenced plans dropped out), which is the tree selection and not the collapse; `tests/test_ci_check_parity.py` passes (its parity claim is that two runs on the SAME tree agree, which they do).

THE REPO-WIDE RULE-CODE SETS, before and after, and no CLASS added or removed by this change:

```
BEFORE: ['check.collisions-not-checked', 'check.ipd-uncarried-obligation', 'check.lifecycle-transition-invalid', 'check.scope-drift']
AFTER:  ['check.collisions-not-checked', 'check.ipd-uncarried-obligation', 'check.lifecycle-transition-invalid', 'check.scope-drift']
```

IDENTICAL. No new code was minted (OQ-02 is answered in the negative; see V-06).

THE CI GATE, measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`):

```
$ python3 -m agent_workflows check plans >/dev/null 2>&1; echo $?
1        # BEFORE
1        # AFTER
```

Exit 1 both times, and the collapse did NOT clear CI. The codes holding it there are `check.ipd-uncarried-obligation` (53 findings), `check.lifecycle-transition-invalid` (8) and `check.collisions-not-checked` (1), all unrelated defects in other plans' records. F-14's structural claim holds although its specific code list has rotated since review.

THE COLLAPSE IS UNCONDITIONAL, with no threshold, as the plan directed. My measured distribution supports that and does not contradict it: the per-plan offender counts are 9, 5, 2 and 1, so any threshold above 1 would have suppressed a genuine single-path drift (`xipfy1`'s `tests/test_runner_refork_guard.py`), which is precisely the real-drift case the collapse must preserve.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: state which way OQ-01 resolved and what E-06 therefore did. If a state was added, paste its rule code, its `RULE_REGISTRY` entry showing the deliberate severity and invariant trace, a fixture test producing it for a live-but-misattributed receipt, and confirmation that the existing terminal-plan and unreachable-base behaviors are unchanged with their tests' output. If NO state was added, paste the docstring text recording the decision and its reason, and paste the sentence added to `_receipt_is_live`'s docstring naming the case it does not cover. Either way, paste the actual output of `tests/test_check_engine_receipt_liveness.py` and `tests/test_event_derived_lifecycle.py` showing the fail-safe direction preserved.
  - Observed evidence: HOW OQ-01 RESOLVED, and what E-06 therefore did. OQ-01 was resolved by the maintainer on 2026-09-10 as a TREE-SELECTION answer, NOT a new advisory state: "MEASURE THE ISOLATED LANE WHEN THERE IS ONE, AND REPORT NOTHING WHEN THERE IS NOT." It explicitly withdrew candidate (e) and overturned both this plan's framing and the review's. E-06 therefore added **NO new rule code** and instead (i) implemented the tree selection and (ii) RECORDED the decision and its reason in the docstrings, which the plan's own E-06 declares a legitimate completed outcome.

WHY NO CODE, beyond deference: OQ-01 removed the CONDITION a new state would have reported. Under tree selection the live-but-misattributed findings do not exist to be relabelled (380 -> 4, every survivor lane-local), so minting a CI-visible contract for an eliminated condition would be cost with no signal. OQ-02 (the NAME) remains `Status: open` and `Blocking: no`, and is now largely moot; the item's proposed spelling `check.receipt-base-stale` is the one the measurement disproves, since nothing about these bases is stale in the sense of incorrect.

`RULE_REGISTRY` IS UNCHANGED, so no unregistered id can fall back to `_DEFAULT_RULESPEC` (`error`, empty invariant). Pinned behaviorally by `tests/test_check_engine_scope_drift.py::RuleLocationSetTests::test_the_severity_and_invariant_come_from_the_shared_registry`, which asserts the collapsed finding's `severity`/`assurance`/`determinism` all come from `rule_spec("check.scope-drift")` rather than being hand-set.

THE SENTENCE ADDED TO `_receipt_is_live`'s DOCSTRING naming the case its two tests do NOT cover, quoted from the shipped code:

> WHAT THESE TWO TESTS DO **NOT** COVER, stated because their absence was mistaken for exhaustive
> and cost a graduation to discover (rcptstale ``wmnmei``, backlog ``v880xk``). LIVENESS IS NOT
> DISTANCE, and distance is not staleness. A plan sitting in ``pending/`` whose ``base_head`` IS an
> ancestor of HEAD passes BOTH tests here while being arbitrarily far behind: measured 2026-09-22
> across six live receipts, 4 to 344 non-merge commits, five of the six holding a lane worktree that
> was being actively worked. [...] The defect those receipts produced was MISATTRIBUTION rather than
> spent authority: all 350 findings named OTHER agents' commits [...] That is fixed in
> :func:`check_scope_drift` by selecting the EXECUTION TREE (see :func:`_plan_execution_tree`), not by
> widening liveness, and deliberately so: this predicate answers "is this authority spent", which is a
> different question from "which tree does this authority describe".

(The docstring's "350" is the figure measured at the moment it was written this session, before my own lane's two files entered the working tree; V-01's 380 is the final measurement. Both are recorded rather than reconciled into one number, since the point of F-1 is that the figure is perishable.)

THE EXISTING TERMINAL-PLAN AND UNREACHABLE-BASE BEHAVIORS ARE UNCHANGED, with the fail-safe direction preserved. Actual output of both declared regression suites:

```
$ python3 -m pytest tests/test_check_engine_receipt_liveness.py
..................                                                       [100%]
18 passed in 5.56s

$ python3 -m pytest tests/test_event_derived_lifecycle.py
.......                                                                  [100%]
7 passed in 3.91s
```

All seven liveness cases (a) through (g) pass, INCLUDING (e), the fail-safe direction: an undeterminable liveness is still treated as NOT live and produces a skip rather than a finding or a traceback. Note those fixtures now allocate a REAL lane worktree and dirty the out-of-scope path INSIDE it, because otherwise every flagging assertion in the file would pass VACUOUSLY under the new tree selection - the silence would come from having no lane rather than from liveness. No liveness assertion was deleted or weakened; only the tree carrying the arrangement moved. The new fail-safe direction of the tree selection itself is pinned by `tests/test_receipt_stale_base.py::TreeSelectionTests::test_tree_resolution_fails_SILENT_when_git_cannot_answer`, which induces the error and asserts the exercised path.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN IS AN EXPLORATION AND ITS BLOCKING QUESTION IS THE POINT, not an oversight. The backlog item states in its first line that it is "AN EXPLORATION, NOT A FIX" and forbids graduating it into a plan that implements receipt expiration. OQ-01 is therefore `Blocking: yes`, and the lint gate that refuses a plan carrying an unresolved blocking question at EVERY checkpoint is the correct mechanism to hold task group 2's outcome for the maintainer. Expect `aw ipd lint` to report `IPD-Q501` on this plan until the maintainer answers: that finding is the gate working, not a defect to repair, and it is why this plan cannot be approved or begun until OQ-01 is resolved. Task group 1 (E-01, E-02) is pure measurement and safe to perform first; E-05 depends on E-01 alone so the plan delivers the proportionate-reporting fix regardless of OQ-01.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. DELETE NO RECEIPT and edit nothing under `.aw/state/`: the item forbids it, `_receipt_is_live`'s docstring explains why, and E-01 only reports. Do NOT edit `ipd_lifecycle.py`; this plan's scope is the advisory, and `h9cn0y`'s ownership work in that module is already `executed`, so there is nothing to add there and an edit would only collide with whoever holds it next. Re-locate every symbol by NAME rather than by the line numbers cited here: review corrected several of this plan's own citations (`_receipt_is_live` is at `:1266` not `:1237`, the per-path loop at `:1386` not `:1357`, and the frozen-base constraint lives on `begin` at `:946-950`, not on `run_begin`). Paste ACTUAL command and test output; measure your OWN finding distribution rather than citing this plan's, which has now moved twice in two days.

CONCURRENCY FENCE, because two contributing plans are being executed by other parties RIGHT NOW. `.aw/worktrees/hp9rot` and `.aw/worktrees/yvvf98` are live lane worktrees, and `hp9rot`'s had 8 uncommitted modified files at review. Do NOT touch anything under `.aw/worktrees/`, do not check out or modify any `aw/lane/*` branch, and do not "clean up" a lane or a receipt that looks abandoned. A plan appearing in your measured distribution is EVIDENCE ABOUT THE RULE, never a licence to act on that plan or its lane. Also note ~189 untracked `opencode-recovery/*.md` files belong to another party and cause the one pre-existing suite failure; leave them alone and do not stage them.

Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the two repo-wide rule-code sets and the explicit statement of whether any live receipt would have been revoked. If OQ-01 remains unanswered, this plan does not finalize on E-05 alone: report the measurement and the collapse as delivered work and leave the plan pending for the decision, rather than closing an exploration whose question is still open.
