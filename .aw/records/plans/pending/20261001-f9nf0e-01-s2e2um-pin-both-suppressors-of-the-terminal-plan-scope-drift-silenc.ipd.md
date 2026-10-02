# IPD: Pin both suppressors of the terminal-plan scope-drift silence and record which one is load-bearing

- Date: 2026-10-01
- Kind: child
- Concern: `check_engine._receipt_is_live`'s TERMINAL PLAN branch cannot be reached from its only caller, and the repository DOCUMENTS it in four places as the mechanism that produces the terminal-plan silence. Re-measured in this lane at HEAD `bdcabdc97`: deleting the branch outright left the full bare suite at `4542 passed` with the three terminal-plan test rows still GREEN, and the rule's finding count UNCHANGED (0) for `executed/`, `executed/202609/`, `superseded/` and `not-executed/`. The real suppressor is `_iter_type_files`' retired-path filter, which is pinned by no test at all. So BOTH mechanisms are unguarded today: one is documented but inert, the other is load-bearing but invisible.
- Scope: IN: one behavioral test module that pins BOTH suppressors independently (the outer retired-path filter as the ACTUAL one, the inner liveness branch as DEFENSE-IN-DEPTH proven effective under a narrowed outer filter), plus a corrected docstring on `_receipt_is_live` naming the outer filter as today's suppressor. OUT, each with a reason recorded under "Deferred": changing `check_scope_drift` to `include_retired=True` (candidate direction 2, REFUSED on measured cost, see F-06/OQ-01); deleting the branch (direction 3, REFUSED, see F-05); any change to the rule's observable contract; the general trim audit `xvp5vx`.
- Scope-Paths: tests/test_receipt_liveness_suppressors.py, agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: f9nf0e
- Set: f9nf0e
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: s2e2um

## Workflow history

- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `f9nf0e`. Every claim in the item was re-measured in this lane rather than trusted, and ONE OF THEM IS FALSE: the item asserts "direction (2) is the only one that makes the branch testable", which was the sole stated reason the choice needed a maintainer. Measured here, `_receipt_is_live` is a module-level function that a test can call DIRECTLY with a terminal plan path, and such a test is mutation-sensitive (it returns False stock, True with the branch deleted, for all three terminal dispositions). That removes the blocking decision and is why this plan proceeds on repository evidence instead of referring OQ-01 upward.
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the terminal-plan silence GUARDED and HONESTLY DOCUMENTED, by pinning the mechanism that
actually produces it today and separately proving that the documented mechanism still works when the
first one stops covering for it.

This plan deliberately does NOT choose between the three candidate directions as an either/or. The
measurement shows the question was mis-framed: the risk the item describes is not "an unreachable
branch exists", it is "nothing tells a future reader WHICH mechanism is load-bearing, and no test
fails if either one breaks". Both are fixed without changing one bit of observable behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pin the suppressor that actually fires

- [ ] E-01 In a new `tests/test_receipt_liveness_suppressors.py`, pin the OUTER suppressor: that `check_engine._iter_type_files(root, "plans")` yields NOTHING for a plan in each of the three `plans.TERMINAL` dispositions, and that this holds for a `<disposition>/YYYYMM/` sharded placement too. This is first because it is the mechanism that actually produces the silence in production and it is pinned by ZERO tests today, which is the more serious of the two gaps the backlog item describes.

    ASSERT THE FILTER'S OUTCOME, NOT ITS IMPLEMENTATION. Drive `_iter_type_files` and assert on the
    yielded SET, rather than asserting that `is_retired` consults a particular container or that
    `_RETIRED_PATH_SEGMENTS` holds particular members. A membership assertion on that frozenset would
    be a code-structure pin of exactly the kind `AGENTS.md` and GUIDING_PRINCIPLES P16 forbid, and it
    would also be WEAKER: it would still pass if `_iter_type_files` stopped calling the filter.

    PROVE NON-VACUITY WITH A LIVE TWIN IN THE SAME TABLE. A test asserting "nothing was yielded" passes
    just as well when the fixture built no plan at all, which is the single most likely way this guard
    rots into a false green. Include a `pending/` row in the same parameterized table asserting the plan
    IS yielded, so the empty rows are anchored by a positive control built the same way.

    USE THE SHARED FIXTURE, DO NOT HAND-BUILD A REPO. `tests/support.scope_drift_repo` already
    arranges the git repo, the gitignore, the plan under an arbitrary `plan_dir`, the frozen base, the
    begin receipt and the lane worktree, and its docstring records WHY changes must go in the lane. Its
    `plan_dir` parameter already accepts `"executed/202609"`, which is how the sharded row is built.
  - Depends on: none
  - Expected outcome: a table-driven case asserting `_iter_type_files` yields the plan for `pending/` and yields NOTHING for `executed/`, `executed/YYYYMM/`, `superseded/` and `not-executed/`; the file passes; no production file touched by this item.
  - Execution state: pending

### Task group 2: make the documented branch earn its place

- [ ] E-02 In the same module, pin the INNER branch two ways: (a) call `check_engine._receipt_is_live` DIRECTLY with a terminal plan path and assert it returns False for each `plans.TERMINAL` disposition (plus True for `pending/`, the non-vacuity control); and (b) assert the DEFENSE-IN-DEPTH property end to end, that `check_scope_drift` still reports NOTHING for a terminal plan when the outer filter no longer excludes it.

    PART (a) IS WHAT THE BACKLOG ITEM BELIEVED IMPOSSIBLE, and it is the reason this plan needs no
    maintainer ruling. The item states direction (2) "is the only one that makes the branch testable".
    Measured in this lane, that is false: the function is module-level, takes `(repo_root, plan_path,
    receipt)` explicitly, and reads disposition from the PATH, so a direct call needs no production
    change and no `include_retired` flip. F-05 records the mutation evidence.

    PART (b) IS THE CLAIM THE DOCSTRING WILL MAKE, so it must be measured rather than asserted.
    "Defense in depth" is only true if the inner branch actually holds when the outer one stops
    covering. Establish that by narrowing `check_engine._RETIRED_PATH_SEGMENTS` for the duration of
    one case (restoring it in `finally`) and asserting the rule stays silent. Narrowing the module
    attribute SIMULATES the future change the backlog item fears; it does not endorse making that
    change.

    THIS PERTURBATION IS NOT A CODE PIN, and the distinction matters because the two look similar.
    It does not READ production source, parse it, or assert on its text; it substitutes a value and
    asserts on the RESULTING BEHAVIOR of a real call. `tests/test_run_finding_reachability.py`
    (`test_unreachable_binding_refusal_fires_under_perturbation`) is the in-repo precedent for exactly
    this shape, including the `try/finally` restore and the post-restore re-assertion.

    RESTORE THE PATCHED ATTRIBUTE IN A `finally`, AND RE-ASSERT AFTERWARDS. `_RETIRED_PATH_SEGMENTS`
    is module-global and the suite runs under `pytest-randomly` with `-n auto`, so a leak would corrupt
    unrelated tests by ORDER and nondeterministically. Follow the precedent's final step too: after
    restoring, assert the stock behavior once more, which proves the restore actually happened rather
    than trusting it.
  - Depends on: E-01
  - Expected outcome: `_receipt_is_live` returns False for all three terminal dispositions (and the sharded form) and True for `pending/`; with `_RETIRED_PATH_SEGMENTS` narrowed, `check_scope_drift` still returns zero `check.scope-drift` findings for a terminal plan holding an out-of-scope lane change; the attribute is provably restored.
  - Execution state: pending

### Task group 3: stop the docstrings asserting the wrong mechanism

- [ ] E-03 Correct `check_engine._receipt_is_live`'s docstring so it states which mechanism suppresses a terminal plan TODAY, and cite the new tests. Keep the branch and keep its rationale; the defect is a documentation claim that reads as a description of live behavior when it describes a path nothing reaches.

    SAY THREE THINGS, NO MORE. (1) The TERMINAL PLAN branch is defense in depth, not the active
    suppressor; (2) the active suppressor is `_iter_type_files`' retired-path filter via
    `check_engine.is_retired`, whose retired path segments are a strict superset of `plans.TERMINAL`,
    so a terminal plan is never yielded to `check_scope_drift`'s loop and its receipt is never read;
    (3) both facts are pinned by `tests/test_receipt_liveness_suppressors.py`. Do NOT restate the
    existing rationale about why terminal licenses ignoring rather than deleting a receipt: that part
    is correct and load-bearing.

    DO NOT REWRITE THE OTHER THREE SITES. `check_scope_drift`'s docstring, the `check.scope-drift`
    RuleSpec comment, and `check_commit_invariants`' docstring each describe the rule's OBSERVABLE
    contract ("a receipt is IGNORED when its plan sits in a terminal lifecycle directory"), which is
    TRUE regardless of which mechanism achieves it. Only `_receipt_is_live`'s own docstring makes a
    claim about its own reachability, so only it is wrong. Editing all four would enlarge the diff and
    push mechanism detail into three places that correctly speak only about outcomes.

    THE 1183-vs-116 ASYMMETRY IS THE REASON THE OUTER FILTER MUST STAY THE SUPPRESSOR, and it belongs
    in the docstring as a measured number because it is what makes direction (2) unattractive. Record
    it as a measurement with its date, not as a timeless fact.
  - Depends on: E-02
  - Expected outcome: `_receipt_is_live`'s docstring names the outer filter as the active suppressor, labels its own terminal branch defense-in-depth, cites the new test module, and retains the existing receipt-not-garbage rationale verbatim; no behavior changes and no other docstring is touched.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- OUTCOME TESTS ONLY (`AGENTS.md`, GUIDING_PRINCIPLES P16). P16 specifically forbids `inspect.getsource`, `ast.parse`, `read_text()` and substring/regex searches against `agent_workflows/*.py`, and forbids census pins on caller or definition counts. This plan's guards call functions and assert on returned values; none reads production source. The E-03 docstring edit is therefore NOT accompanied by any test asserting the docstring's text, which would be precisely the forbidden shape.
- MUTATION IS THE TEST OF A TEST (GUIDING_PRINCIPLES P16's "Verify test sensitivity with mutation", and line 186's "Never weaken an assertion so it passes everywhere"). This is the whole reason the plan exists: the terminal rows in `tests/test_check_scope_drift.py` pass with the branch deleted, so they are not evidence about the branch. Every new case here must be shown failing under a stated mutation.
- MONKEYPATCHING A MODULE GLOBAL FOR ONE CASE IS ESTABLISHED PRACTICE HERE, with a `try/finally` restore and a post-restore re-assertion: `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` patches `run_evidence.RUN_FINDING_CODES`, restores it in `finally`, then re-validates the restored table.
- `tests/support.scope_drift_repo` IS THE FIXTURE, and its docstring records a precondition this plan must respect: `check_scope_drift` measures the plan's ISOLATED LANE, so a change placed in the main checkout is INVISIBLE to the rule and any assertion built there passes VACUOUSLY. Put dirt in the returned lane path.
- Run the suite BARE: `python3 -m pytest`. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and deselects `slow`/`livecorpus`; `-n0` is forbidden, a second `-q` suppresses the `N passed` line this plan requires pasted, and `-p no:randomly` would disable the order randomization that makes the restore discipline in E-02 load-bearing. Use `-o addopts=""` only for a narrowed run needing per-test counts.
- `aw` re-execs into the checkout's own package unless `AW_NO_REEXEC=1` is set; inside a lane it prints a notice naming both paths. Set `AW_NO_REEXEC=1` on every `aw` call so the lane's code runs and the notice does not pollute pasted evidence.
- TWO SUITE FAILURES ARE PRE-EXISTING AT THE AUTHORING HEAD and are NOT this plan's to fix: `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` and `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`. Both reproduce in isolation on an unmodified tree. Compare failure SETS BY NAME, never counts.

## Findings

Established in this lane at HEAD `bdcabdc97` by driving the code, not by reading it. Every mutation was reverted and the tree verified clean (`git diff --stat` empty) before the next measurement.

| # | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | MEDIUM (THE ITEM'S CORE CLAIM IS TRUE) | Replaced `_receipt_is_live` with a variant lacking only the terminal branch and compared `check.scope-drift` finding counts per `plan_dir`: `pending` 1 -> 1, `executed` 0 -> 0, `executed/202609` 0 -> 0, `superseded` 0 -> 0, `not-executed` 0 -> 0, `reusable` 1 -> 1. Not one disposition differs. | **THE BRANCH IS INERT AT THE RULE LEVEL**, confirming the filing. The `reusable` row is additional evidence the item did not record: a non-terminal, non-pending disposition is correctly still measured, so the inertness is specific to the terminal set and not a general collapse of the rule. |
| F-02 | HIGH (THE SUITE CANNOT SEE THE DELETION) | Deleted the three-line terminal branch from `agent_workflows/check_engine.py` and ran the FULL BARE suite: `5 failed, 4542 passed, 2 skipped` versus the unmodified baseline `2 failed, 4545 passed, 2 skipped`. All three extra failures (`test_typecheck_gate`, `test_statusline_behavior`, `test_verbose_flag_reach`) PASS when re-run in isolation against the same mutated tree (`3 passed`, then `44 passed`), so they are load/ordering flakes, not detections. `tests/test_check_scope_drift.py` measured `6 passed` WITH the branch deleted. | **NO TEST GUARDS THE BRANCH**, which is what makes this a latent trap rather than a style complaint. Note the specific trap: the three terminal rows in `tests/test_check_scope_drift.py` are green under the mutation, so a reader who greps for "terminal" and finds them concludes the branch is covered. |
| F-03 | HIGH (THE REAL SUPPRESSOR IS UNGUARDED) | `_iter_type_files(root, "plans")` yields `[]` for a plan placed in `executed/`, `executed/202609/`, `superseded/` and `not-executed/`, and yields it for `pending/`. Narrowing `_RETIRED_PATH_SEGMENTS` to `{archive, parked, done, shipped}` flips all three terminal dispositions from excluded to YIELDED. A repo-wide search for a test driving `_iter_type_files` over a terminal plan found none. | **THE MECHANISM THAT ACTUALLY PRODUCES THE SILENCE HAS ZERO COVERAGE.** This reframes the item: the inert branch is the lesser gap. The documented-but-dead path at least has a docstring; the live path has neither test nor comment saying it is load-bearing. |
| F-04 | MEDIUM (DEFENSE IN DEPTH IS REAL, MEASURED) | With `_RETIRED_PATH_SEGMENTS` narrowed so the outer filter no longer excludes terminal plans, `check_scope_drift` still reported 0 findings for `executed`, `superseded` and `not-executed`. Narrowing the outer filter AND deleting the inner branch reported 1 finding for each. | **THE INNER BRANCH IS A WORKING SECOND LINE, not dead weight**, so direction (1) rests on a measured property rather than on a plausible-sounding label. This is also the exact arrangement that makes the branch testable end to end. |
| F-05 | HIGH (THE ITEM'S BLOCKING PREMISE IS FALSE) | Called `check_engine._receipt_is_live(root, plan_file, receipt)` directly, with no production change and no `include_retired` flip: returns False for `executed`, `executed/202609`, `superseded`, `not-executed`; True for `pending`. Under the branch-deleted mutation the same four calls return True. | **THE BRANCH IS DIRECTLY TESTABLE TODAY AND SUCH A TEST IS MUTATION-SENSITIVE.** The item asserts direction (2) "is the only one that makes the branch testable", and that was its ONLY stated reason for needing a maintainer decision. With the premise falsified, the decision is no longer a judgement call about authority; it is answerable from measurement (OQ-01). |
| F-06 | MEDIUM (DIRECTION 2 HAS A MEASURED COST) | `_iter_type_files` yields 116 plans with `include_retired=False` and 1183 with `include_retired=True` (10.2x). Driving `check_scope_drift` with the flag flipped: `_receipt_is_live` call count rises 12 -> 37, terminal rejections 0 -> 25, findings UNCHANGED at 3, median warm wall time 1.99s -> 3.08s (+55%) over three runs. | **DIRECTION (2) BUYS NOTHING OBSERVABLE AND COSTS 55% ON A RULE THAT RUNS IN A PRE-COMMIT HOOK.** `check_commit_invariants` calls `check_scope_drift` and `agent_workflows/hooks/precommit_scope_gate.py` delegates to that aggregator, whose docstring promises "on an ordinary clean commit this is a fast no-op". Reading 1067 extra terminal plans to reach a branch a direct unit call already reaches would break that promise for zero contract change. |
| F-07 | MEDIUM (THE DOC CLAIM IS LOCALIZED) | Four sites describe the terminal case: `_receipt_is_live`'s own docstring ("TERMINAL PLAN - the plan file sits in a terminal lifecycle directory"), `check_scope_drift`'s docstring ("a receipt is IGNORED when (1) its plan sits in a TERMINAL lifecycle directory"), the `check.scope-drift` RuleSpec comment ("LIVE excludes a receipt whose plan is in a terminal lifecycle dir"), and `check_commit_invariants`' docstring. | **ONLY ONE SITE IS ACTUALLY WRONG.** The other three describe the rule's OBSERVABLE contract, which is true however it is achieved. This bounds E-03 to a single docstring and is why this plan does not open a four-site documentation sweep. |
| F-08 | LOW (THE LIVE CORPUS WOULD EXERCISE IT) | Of 37 begin receipts in `.aw/state/ipd-lifecycle/`, 25 belong to plans now in a terminal directory (`executed` 18, `superseded` 7) and 12 to non-terminal plans; every receipt resolved to exactly one plan. | **THE BRANCH WOULD FIRE 25 TIMES ON THE REAL TREE IF IT WERE REACHED**, so it is not guarding a hypothetical. It also quantifies F-06's waste concretely: 25 receipt reads whose answer the outer filter already determined. |
| F-09 | LOW (STATUS TEXT IS NOT THE PATH) | Across all 1183 plans: 24 sit in a terminal directory while carrying no parseable `- Status:` (all pre-`Status` legacy plans), and ZERO sit in a non-terminal directory carrying a retired status. | **THE TWO SUPPRESSORS AGREE ON TODAY'S CORPUS VIA THE PATH ARM ALONE**, which is why `is_retired`'s status arm is not part of this plan's subject and why `_plan_disposition`'s path-not-status choice is correct as documented. Recorded so review need not re-derive it. |

## Proposed changes (ordered, validatable)

1. `tests/test_receipt_liveness_suppressors.py` (new): the outer-filter table with its `pending/` positive control (E-01).
2. Same file: the direct `_receipt_is_live` verdict table including the sharded form and the `pending/` control (E-02a).
3. Same file: the narrowed-`_RETIRED_PATH_SEGMENTS` defense-in-depth case, with `try/finally` restore and post-restore re-assertion (E-02b).
4. `agent_workflows/check_engine.py`: `_receipt_is_live`'s docstring corrected to name the active suppressor, label its own branch defense-in-depth, carry F-06's measured asymmetry, and cite the new module (E-03). No executable line changes.

The observable behavior of `aw check`, `aw doctor` and the pre-commit gate is UNCHANGED by every item above. That is the plan's central property, and V-03 verifies it rather than assuming it.

## Deferred / out of scope (with reason)

- CANDIDATE DIRECTION (2), `include_retired=True` IN `check_scope_drift`, IS REFUSED, not deferred. Measured: zero change in findings, +55% median wall time, 1067 extra plans read, on a rule the pre-commit aggregator's docstring promises is "a fast no-op" (F-06). It also makes a terminal plan's receipt readable by the rule again, re-creating the condition that produced 350 misattributed findings and discarding the fail-safe redundancy F-04 proves works.
  - Carrier-Declined: not a defect; the current arrangement is correct and the direction would make a measured performance regression in exchange for no contract change.
- CANDIDATE DIRECTION (3), DELETING THE TERMINAL BRANCH, IS REFUSED. F-04 measures it as a working second line of defense, and F-08 shows it would answer for 25 of 37 live receipts if reached. Deleting a cheap fail-safe inside an advisory that fails safe by design is the wrong direction, and the stated motive (removing a docstring nothing exercises) is addressed by E-03 at no behavioral cost.
  - Carrier-Declined: not a defect; the branch is effective under the perturbation that matters.
- THE RULE'S OBSERVABLE CONTRACT IS NOT CHANGED. A terminal plan gets no drift advisory before and after. This plan adds tests and corrects one docstring.
  - Carrier-Declined: not a defect; the contract is correct as-is, which the backlog item itself states.
- THE THREE SIBLING DOCSTRINGS ARE NOT EDITED. `check_scope_drift`, the `check.scope-drift` RuleSpec comment and `check_commit_invariants` describe the OUTCOME, which is true however achieved (F-07). Rewriting them would push mechanism detail into three sites that correctly speak only of contract.
  - Carrier-Declined: not a defect; those three statements are accurate.
- `tests/test_check_scope_drift.py` IS NOT EDITED. Its terminal rows already state, in the module docstring and in each row, that they assert the observable contract and do NOT claim to exercise `_receipt_is_live`, naming this backlog item. That attribution is honest and becomes MORE accurate once this plan's module exists beside it. Editing it would also put two plans' tests in one file for no gain.
  - Carrier-Declined: not a defect; the existing attribution note is correct.
- THE GENERAL TRIM AUDIT IS NOT ADVANCED. Backlog `xvp5vx` owns the systematic question of what lost its only guard in commit `19313eed`. This plan closes one specific gap found by a different route (a `/plan-review` finding), and its maintainer directive to test outcomes rather than code structure is honored here.
  - Carrier: xvp5vx
- `is_retired`'s STATUS ARM IS NOT PINNED. This plan's subject is the terminal-plan suppression of a scope advisory, which F-09 measures as reached through the PATH arm alone on today's corpus. A guard on the status arm belongs with whatever rule actually depends on it.
  - Carrier-Declined: not a defect; out of this plan's subject, not a gap in it.
- NO `aw check` RULE IS ADDED to detect unreachable branches generally. That is a static-reachability problem with no deterministic answer in a language with dynamic dispatch, and the repository has an existing surface for the specific case of a declared-but-unreachable binding (`run_evidence.validate_finding_table`). A general rule would be mostly false positives.
  - Carrier-Declined: not a defect; outside this item's subject and not deterministically checkable.

## Scope check

- Over-scope: none. Both declared paths are edited by numbered items: `tests/test_receipt_liveness_suppressors.py` (E-01, E-02) and `agent_workflows/check_engine.py` (E-03, docstring only). The production path is declared because E-03 edits that file, even though no executable line changes; declaring it is what lets the finalize scope gate reconcile honestly.
- Under-scope: if E-02's perturbation shows the inner branch does NOT hold under a narrowed outer filter (contradicting F-04), do not weaken the case to make it pass. Stop and report: that would mean the defense-in-depth claim E-03 is about to write is false, and the plan's conclusion would need revisiting rather than its assertion relaxing. Equally, if the executing HEAD has changed `_iter_type_files`' filtering such that terminal plans are already yielded, E-01's expected outcome inverts; record the measurement and report rather than editing the expectation to match.

## Required tests / validation

- The BARE suite: `python3 -m pytest`, `N passed` line pasted. Re-establish the baseline at the executing HEAD rather than trusting this document's numbers. The two PRE-EXISTING failures named in Step 0 must be shown unchanged; compare failure SETS BY NAME, never counts.
- `tests/test_receipt_liveness_suppressors.py` run alone with `-o addopts=""`, every case named, pasted.
- MUTATION PROOF FOR E-01, pasted: narrow `check_engine._RETIRED_PATH_SEGMENTS` to exclude the `plans.TERMINAL` members, confirm the E-01 case FAILS, revert, confirm it passes. A guard never seen failing proves nothing, and F-02 shows this exact area already holds tests that are green under the mutation they appear to cover.
- MUTATION PROOF FOR E-02a, pasted: delete the three-line terminal branch from `_receipt_is_live`, confirm the direct-verdict case FAILS for all three terminal dispositions, restore, confirm it passes, and show `git diff --stat` empty after restoring.
- MUTATION PROOF FOR E-02b, pasted: with the outer filter narrowed AND the inner branch deleted, confirm the defense-in-depth case FAILS (the rule now reports a finding for a terminal plan); restore both and confirm it passes. This is the only arrangement that proves the case is measuring the inner branch rather than the outer filter.
- NON-VACUITY, pasted: the `pending/` positive-control rows must FAIL when `check_scope_drift` is stubbed to `return []` and when `_iter_type_files` is stubbed to yield nothing, proving the empty-set assertions are anchored.
- TZ-FREE GLOBAL-RESTORE PROOF, pasted: run the new module together with `tests/test_check_scope_drift.py` and `tests/test_scope_drift_lane_resolution.py` in ONE process (`-o addopts=""`, no xdist), proving `_RETIRED_PATH_SEGMENTS` was restored and no neighbor that depends on the retired filter was corrupted. Then run the new module alone twice with `-p randomly` seeds differing, pasted.
- BEHAVIOR-UNCHANGED PROOF for E-03, pasted: `AW_NO_REEXEC=1 aw check` finding set and `AW_NO_REEXEC=1 aw doctor` finding set captured BEFORE and AFTER the docstring edit and shown IDENTICAL. Both exit nonzero on pre-existing conditions, so the bar is an unchanged SET, not exit 0. Do not fix another plan's finding or another lane's state.
- `tests/test_check_scope_drift.py`, `tests/test_scope_drift_lane_resolution.py`, `tests/test_check_engine.py` and `tests/test_ci_check_parity.py` each run individually with results pasted, since all four touch this rule or its finding shape.
- `AW_NO_REEXEC=1 aw sanitize --agent`, pasted.
- `AW_NO_REEXEC=1 aw ipd lint --phase pre-transition` on this plan, conforming.
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`, never push. Verify the staged set against `Scope-Paths` before committing.

## Spec / documentation sync

No spec is amended and no `.spec.md` appears in `Scope-Paths`. This plan changes no contract: it adds
test coverage for behavior that already exists and corrects one docstring's account of its own
reachability.

No `CHANGELOG.md` entry. Nothing user-visible changes, by construction (V-03 proves the `aw check` and
`aw doctor` finding sets are identical before and after), and announcing a docstring correction as a
release note would misreport a behavior change.

No `DECISIONS.md` entry. The two refusals recorded under "Deferred" are measurements about a private
helper's performance and redundancy, not rulings that bind future work; the authority for them is
F-04/F-06 plus the corrected docstring, which is where a future reader will be standing when the
question recurs.

## Open questions

### OQ-01: Of the backlog item's three candidate directions, which should be taken, and does the choice require a maintainer ruling?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS DIRECTION (1) PLUS COVERAGE, AND THE REFERRAL IS WITHDRAWN ON MEASUREMENT. The item asks for a maintainer decision on one stated ground: "Direction (2) is the only one that makes the branch testable, and it changes which mechanism is authoritative, so it needs a maintainer decision rather than an agent's." THE PREMISE IS FALSE. `_receipt_is_live` is module-level and takes `(repo_root, plan_path, receipt)` explicitly, so a test calls it directly on a terminal plan path with no production change; that test is mutation-sensitive, returning False stock and True with the branch deleted, for all three terminal dispositions and the sharded form (F-05). Once the branch is testable without touching production, direction (2) retains no advantage and carries a measured cost: zero change in findings, +55% median wall time, 1067 extra plans read, inside a rule the pre-commit aggregator documents as "a fast no-op" (F-06). Direction (3) is refused because the branch is measurably effective under the one perturbation that matters (F-04) and would answer for 25 of 37 live receipts if reached (F-08). Direction (1) is therefore correct, and this plan adds what the item's framing omitted: the ACTUAL suppressor has no test either (F-03), which is the larger gap. What remains is a documentation correction and two guards, none of which changes an authority or a public contract, so nothing here is a maintainer's call. The maintainer retains the option this plan does not take: if they WANT liveness to be the authoritative gate on principle, direction (2) becomes a deliberate trade of 55% of this rule's runtime for mechanism simplicity, and F-06 is the number to decide on.

### OQ-02: Should the new guards live in `tests/test_check_scope_drift.py` beside the existing terminal rows instead of a new module?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS A NEW MODULE, on subject rather than on size. `tests/test_check_scope_drift.py` declares an EXPLICIT BOUND in its docstring, covering "the drift advisory's own OBSERVABLE decisions", and states that the `_receipt_is_live` unit surface is outside it and belongs to backlog `xvp5vx`. This plan's subject is precisely that excluded surface plus the `_iter_type_files` filter, which is not the drift rule at all and is used by many other `check_engine` rules. Adding these cases there would contradict a bound that file deliberately records, and would mix two plans' provenance in one module. The new module cites the existing one so a reader finds both. The existing file's attribution note, which names this backlog item as holding the uncovered branch, stays TRUE and is simply answered elsewhere.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: the new case's source quoted, showing it drives `_iter_type_files` and asserts on the YIELDED SET with no membership assertion against `_RETIRED_PATH_SEGMENTS` and no read of production source. The run pasted with every row named, including the `pending/` positive control. THE MUTATION PASTED BOTH WAYS: with `_RETIRED_PATH_SEGMENTS` narrowed to exclude the `plans.TERMINAL` members the case FAILS, naming which dispositions were wrongly yielded; restored, it passes. Plus the stubbed-`_iter_type_files` run showing the `pending/` control FAILS, proving the empty-set rows are not vacuous. Plus `git diff --stat` empty after each mutation is reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for (a), the direct-call case pasted showing False for `executed`, `executed/YYYYMM`, `superseded`, `not-executed` and True for `pending`; then the branch-deleted mutation pasted showing the case FAILS on all four terminal rows, then restored and passing, with `git diff --stat` empty. For (b), the narrowed-filter case pasted GREEN (inner branch holding) and then pasted RED under narrowed-filter-PLUS-branch-deleted, which is the only arrangement proving it measures the inner branch; state the finding counts observed in each. Plus the `try/finally` restore quoted, the post-restore re-assertion quoted, and the single-process co-run with `tests/test_check_scope_drift.py` and `tests/test_scope_drift_lane_resolution.py` pasted, proving no global leaked. Plus two differing-seed runs of the new module pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `git diff` of `agent_workflows/check_engine.py` showing ONLY docstring lines changed and ONLY inside `_receipt_is_live` (no executable line, no other function), with the retained receipt-not-garbage rationale quoted to prove it was not dropped. The new docstring text quoted, showing it names `_iter_type_files`/`is_retired` as the active suppressor, labels its own branch defense-in-depth, carries the measured plan-count asymmetry WITH its measurement date, and cites `tests/test_receipt_liveness_suppressors.py`. An explicit statement that the three sibling sites named in F-07 were NOT edited, with `git diff` as evidence. The `aw check` and `aw doctor` finding sets pasted before and after and shown IDENTICAL. The bare suite's `N passed` line pasted with the two pre-existing failures shown unchanged BY NAME. `tests/test_check_scope_drift.py`, `tests/test_scope_drift_lane_resolution.py`, `tests/test_check_engine.py` and `tests/test_ci_check_parity.py` each pasted individually. `aw sanitize --agent` pasted. `aw ipd lint --phase pre-transition` conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries no `- Readiness:` field: that field is an OUTPUT of `/plan-review`
and writing one here would forge a review that has not happened. It requires explicit human approval
before execution.

DO NOT "SIMPLIFY" THIS PLAN INTO DIRECTION (2) OR (3) DURING EXECUTION. Both were measured and refused
with numbers recorded under "Deferred" and in OQ-01. An executor who flips `include_retired=True`
because it looks tidier would impose a measured +55% on a pre-commit-path rule for no contract change;
one who deletes the branch would remove a fail-safe that F-04 proves works. If either looks right at
execution time, the honest route is to say so and stop, not to re-decide a refusal this plan recorded.

DO NOT WEAKEN A GUARD TO MAKE IT PASS. Each new case must be demonstrated FAILING under the stated
mutation. This area already contains tests that look like they cover the branch and are green when it
is deleted (F-02), so an unmutated green here is worth nothing, and a case that cannot be shown red is
a defect in the case.

Execution contract: commit ONLY the files this plan changed, limited to its `Scope-Paths`, through
`aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push.
Verify the staged set with `git diff --cached --name-only` before each commit and unstage anything not
this plan's with `git restore --staged <path>`; this is a shared checkout and another agent's
uncommitted work must never enter a commit here. REVERT EVERY MUTATION BEFORE COMMITTING and prove it
with an empty `git diff --stat` for the mutated file: this plan's validation deliberately requires
temporarily breaking production code, and a committed mutation would be a silent regression.

Validation is not optional and not inferable: every `V-*` item demands pasted output from a command
actually run, including the mutation runs in both directions.

Post-gate lifecycle: on completion, run `aw ipd lint --phase pre-transition` to conforming, then move
this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition. Do not hand-edit
the terminal state. Backlog item `f9nf0e` is handed off via `- From-Backlog:` and should reach
`graduated`, not `done`. The item carries no `- Blocks-Release:` gate and this plan must not invent one.
