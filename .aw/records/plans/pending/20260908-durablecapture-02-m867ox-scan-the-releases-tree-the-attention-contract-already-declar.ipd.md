# IPD: Scan the releases tree the attention contract already declares tracked and guard the two lists against drifting again

- Date: 2026-09-08
- Kind: child
- Concern: `releases` is a DECLARED tracked tree with a full status map and a `TreePolicy`, and it is never scanned, so every release record is invisible to `aw attention` while the view reports `valid: true`. Two lists encode one fact and they have drifted. MEASURED AT HEAD `a2e0438a` by importing both modules: `attention_contract.TRACKED_TREES` is `('specs', 'plans', 'research', 'backlog', 'releases')`, and `artifact_core.SCAN_ROOTS` contains no releases path at all (it holds four root docs, three `.agents/` roots, and seven `.aw/records/` roots, none of them releases). Resolving each tracked tree against the scan roots: `specs`, `plans`, `research` and `backlog` each match at least one root; `releases` matches NONE.
  CONFIRMED EMPIRICALLY, and the numbers are worse than the item recorded because the corpus grew. `aw attention --format json` returns 848 items: plans 557, backlog 158, research 105, specs 28, and ZERO releases, with `valid: true` and zero violations, while `.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md` exists on disk. The item measured 749 items and the same zero.
  THE POLICY IS NOT THE GAP, WHICH NARROWS THE FIX. `releases` DOES have a `TreePolicy` (`.agents/releases`, `tracked=True`, `owner='aw releases'`, reason "release records (ship-gate anchors); tracked lifecycle planned/blocked/shipped"), and `attention._classify_tree('.aw/records/releases/x.release.md')` correctly returns that policy, and `attention_contract` carries the status map (`planned`->ready, `blocked`->blocked, `shipped`->done). So classification and mapping both work; the file is simply never handed to them, because `core.iter_scan_files` never yields it. The fix is one scan root plus a guard, not a new policy.
  WHY IT MATTERS MORE THAN A MISSING COUNT. Releases anchor the whole `Blocks-Release` mechanism, and `AGENTS.md` instructs agents to consume `aw attention` for the cross-tree view and states it "surfaces the outstanding release-blocker set for the active release". If the release records are invisible to that view, any conclusion an agent draws about release readiness from `aw attention` alone was drawn without them. Note `aw check releases` IS wired fail-closed in CI (`.github/workflows/tests.yml:157-159`), so release records are VALIDATED but not SURFACED, and that split is exactly what makes this easy to miss.
- Scope: Add the releases scan root(s) so the declared tracked tree is actually scanned, decide the `reviews` tree deliberately (a `TreePolicy` either tracked or explicitly excluded WITH a reason, matching how the other five exclusions are recorded), and add a consistency check asserting every `TRACKED_TREES` entry has at least one `SCAN_ROOTS` entry so this class of drift cannot recur silently. EXCLUDES retiring `TODO.md` (sibling backlog `ld08f1`, whose plan is authored alongside this one); excludes per-requirement spec tracking (`f1sw71`); excludes the durable-carrier predicate (pending plan `rnkqrc`, from `jys5dp`); excludes changing any release record or the `Blocks-Release` resolution logic.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/attention_contract.py, tests/test_artifact_core.py, tests/test_attention_contract.py, tests/test_backlog.py, tests/test_next_ordering.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: durablecapture
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m867ox
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: v7u6vm

## Workflow history
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all FIXED, zero deferred, zero open; OQ-01 and OQ-02 resolved from evidence; review record written
- 2026-09-09 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all FIXED, zero deferred, zero open. Both open questions RESOLVED from repository evidence.
  THE PLAN'S CENTRAL DIAGNOSIS IS CORRECT AND WAS RE-MEASURED WHOLE at HEAD `8dffd7a0`: `releases` is declared tracked, matches no scan root, and contributes zero items to a view that reports `valid: true`; the `TreePolicy` and the status map both already exist, so the fix really is one scan root. Its F-3 self-correction was right and its sibling-boundary check against `rnkqrc` holds.
  WHAT REVIEW FOUND WAS NOT WRONG DIAGNOSIS BUT UNMEASURED CONSEQUENCE, and the fix was applied by EXECUTING it rather than reading. Applying E-01 in an isolated worktree BREAKS TWO TESTS (`tests/test_backlog.py:248` -> `2 != 1`, `tests/test_next_ordering.py:1327` -> `3 != 2`), both because a fixture creates a release record and then pins an exact count; neither test file was in `- Scope-Paths:`. The plan declared no fallout and also carried a STALE known-failure baseline (`1 failed, 5648 passed`) that would have excused exactly this regression; the real baseline is `5930 passed, 3 skipped, 2 xfailed` with zero failures. Added E-06 and the two paths.
  THE MOST CONSEQUENTIAL FINDING IS THAT THE PLAN'S OWN GUARD COULD PASS WITHOUT FIXING THE BUG. With only `.agents/releases` added, the E-04 cross-list guard is GREEN while `attention.scan` still returns zero releases, because `releases.py::_releases_dir` hardcodes `.aw/records/releases`. That turned OQ-02 from a symmetry preference into a correctness question, resolved to ADD BOTH with the load-bearing entry named, and added E-05 mutation 3 to prove the gap rather than assert it.
  E-05's MUTATION 1 WAS IMPOSSIBLE AS WRITTEN: `TRACKED_TREES` is DERIVED from `TREE_POLICY`, so appending to it is a no-op. Rewritten to mutate the policy, and E-04's message now also names the `tracked=False` bypass that derivation creates. E-04's predicate was likewise under-specified: a classify-only form FAILS IMMEDIATELY because `.agents/docs` is the scanned ancestor of specs and research; the three rejected forms are now recorded with the measurement that rejected each.
  OQ-01 RESOLVED WITHOUT ESCALATION because the repository answered it: a review record has NO `- Status:` field (zero of 132 files), so there is no native enum for a pure total mapping and spec Section 6 forbids inferring one from `Verdict`. Excluded, with the reason stated to the standard of the five existing exclusions, and enforcement unaffected since `aw check` already gates review findings.
  SPEC SYNC RESOLVED BY READING rather than left as an instruction: Section 8.6 states the tracked-or-excluded RULE, not a closed roster, so an exclusion SATISFIES the spec; Section 8.1 already requires a tracked tree be scanned, so E-01 brings code into compliance. No amendment, and the spec is deliberately absent from `- Scope-Paths:`.
  ALSO ADDED: E-02 now adds the MISSING map-totality test (releases is the only tracked tree without one; its four siblings all have one), and E-07 records the measured `aw check` delta (171 -> 173, all `check.scope-drift`, attributed to other agents' in-flight plans) so an executor does not "fix" it destructively. Stale counts corrected throughout (848 -> 921 items, 82 -> 132 review records) with an explicit instruction never to pin a total.

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `v7u6vm`. The item carries no `- Blocks-Release:` so none is inherited or invented, though the defect is ABOUT the release-gating surface, which is worth noting rather than confusing with a gate.
  EVERY CLAIM RE-MEASURED at HEAD `a2e0438a` by importing the modules rather than reading them, and all three held: the two lists disagree exactly as described, `releases` matches no scan root, and `aw attention` returns zero releases with `valid: true`. Two numbers moved and one claim needed CORRECTING.
  THE CORRECTION MATTERS BECAUSE IT SHRINKS THE WORK. The item says releases "has a status->class map ... and is never scanned", which is right, but it does not say that `releases` ALREADY HAS a `TreePolicy` and that `_classify_tree` already resolves a `.aw/records/releases/` path to it. Measured both. So an executor must NOT add a policy (that would be a second, conflicting entry); the single missing piece is the scan root. Stated in E-01 so the cheap fix is not mistaken for an incomplete one.
  NUMBERS UPDATED: 848 attention items (plans 557, backlog 158, research 105, specs 28), not the item's 749; and the reviews tree now holds 82 records, which strengthens its point that an absent policy for a consequential tree should be a DECISION rather than an omission.
  THE `reviews` HALF IS A DECISION, NOT AN IMPLEMENTATION, and E-03 is written to force that honestly. The item observes that the five EXCLUDED trees each carry a recorded reason (measured: walkthroughs "narrative records; no lifecycle status in v1 (OQ8)", roadmaps "intent, not commitment", prompts and comms "deferred to Phase 3 (OQ3)", docs-prompts "the evergreen copy-paste prompt LIBRARY"), while `reviews` is simply absent. Given that `check.review-finding-unescalated` treats an unescalated review finding as an ERROR, that absence is consequential enough to deserve a reason either way. E-03 therefore requires a recorded decision and forbids silently tracking 82 records into the view without measuring what that does to it.
  SIBLING BOUNDARY, checked rather than assumed: pending plan `rnkqrc` (from `jys5dp`) names BOTH this item and `ld08f1` in its deferred section ("THE `releases` TREE having no scan root, and the `reviews` tree having no TreePolicy: both found while investigating, both their own items"), so there is no overlap and this work is unowned.

## Goal

Make the attention view actually cover the five trees it claims to cover, and make a sixth divergence fail a test instead of hiding behind `valid: true`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: scan the tree that is already declared and already classified

- [x] E-01 ADD THE RELEASES SCAN ROOT(S) TO `SCAN_ROOTS`, and add nothing else. Locate `SCAN_ROOTS` by SYMBOL in `artifact_core.py`; the item cites `:158` for the `TODO.md` entry and line numbers move.
  DO NOT ADD A `TreePolicy` FOR RELEASES. One already exists and `_classify_tree` already resolves a `.aw/records/releases/` path to it (measured: returns the `.agents/releases` policy, `tracked=True`, `owner='aw releases'`). A second entry would be two policies for one tree, which is the duplication this repository's shared-authority discipline exists to prevent.
  ADD BOTH PATH GENERATIONS, matching how every other records-class tree is listed. `SCAN_ROOTS` carries `.agents/plans` AND `.aw/records/plans`, and `.agents/backlog` AND `.aw/records/backlog`, because the layout migrated. OQ-02 is now RESOLVED to add both (see its rationale); the `TreePolicy` root is the `.agents/` spelling, and `_classify_tree` rewrites `.aw/records/<type>` to `.agents/<type>` before matching, so both spellings resolve to the same policy.
  `.aw/records/releases` IS THE LOAD-BEARING ENTRY AND `.agents/releases` FIXES NOTHING ON ITS OWN. MEASURED in an isolated worktree at HEAD `8dffd7a0`: with ONLY `.agents/releases` added, `aw attention` still reports ZERO releases items, because `releases.py::_releases_dir` hardcodes `.aw/records/releases` and no `.agents/releases` directory exists here. Adding `.agents/releases` is a symmetry and pre-migration-repo choice, NOT the fix. Do not treat a green cross-list guard (E-04) as evidence the defect is fixed: that guard is satisfied by `.agents/releases` alone (measured), so the guard and the fix must be verified SEPARATELY.
  VERIFY THE RECORD ACTUALLY APPEARS, which is the item's own acceptance condition. Adding a root that `iter_scan_files` skips for an unrelated reason (an ignore rule, a name filter, a `is_nonartifact_name` match) would look like a fix and change nothing. Measured: with both roots added the tree contributes exactly TWO files to `iter_scan_files`, of which `README.md` is correctly dropped by `is_nonartifact_name`, so exactly one record reaches the view.
  - Depends on: none
  - Expected outcome: `releases` resolves to at least one scan root; the existing release record appears in `aw attention` output as `tree: releases`; no second `TreePolicy` was added; both path generations added, with `.aw/records/releases` identified as the one that actually fixes the defect.
  - Execution state: performed

- [x] E-06 REPAIR THE TWO TESTS THIS CHANGE BREAKS, which are a CORRECT consequence of the fix and not a regression to avoid. THE PLAN AS AUTHORED CLAIMED A KNOWN-FAILING BASELINE AND DECLARED NO TEST FALLOUT; BOTH WERE WRONG. Re-measured in an isolated worktree at HEAD `8dffd7a0`: the bare baseline is `5930 passed, 3 skipped, 2 xfailed` with ZERO failures (`tests/test_orchestrator_retirement.py` passes; the plan's claimed `1 failed` baseline is stale), and applying E-01 alone yields `2 failed, 5928 passed`.
  THE TWO FAILURES, both measured, both because a release record NOW enters the view where the test's fixture assumed it could not:
  1. `tests/test_backlog.py::BacklogVerbTests::test_new_blocks_release_valid_and_appears_in_release_blockers` -> `AssertionError: 2 != 1` at `tests/test_backlog.py:248`. The test calls `releases.create_release(...)` and then asserts `len(ATT.scan(repo)) == 1`, counting only the backlog item. The release record it created is now correctly a second item.
  2. `tests/test_next_ordering.py::NonColoredBoardOrderingTests::test_release_blocker_in_order_under_explicit_sort` -> `AssertionError: 3 != 2` at `tests/test_next_ordering.py:1327`. It writes a release record to `.aw/records/releases/planned/...` and asserts the `-o priority` board has exactly 2 lines; the release record is now a correct third line.
  FIX THEM BY UPDATING THE EXPECTATION, NOT BY NARROWING THE SCAN. Each assertion encodes "a release record is invisible", which is precisely the defect. Assert the release record IS present with `tree: releases` rather than merely bumping `1` to `2` and `2` to `3`, so the test would fail again if the record vanished for a different reason. Do NOT add a filter, a skip, or an `is_nonartifact_name` entry to keep the old counts.
  NOTE THE SECOND TEST PROVES A SUBDIRECTORY LAYOUT IS ALREADY IN USE (`releases/planned/<file>.release.md`) while the live record sits FLAT at `.aw/records/releases/<file>.release.md`. `iter_scan_files` uses `rglob`, so both are scanned and no extra root is needed; do not add one.
  BOTH TEST FILES ARE OUTSIDE `- Scope-Paths:` AS AUTHORED and have been ADDED to it. That is a declaration, not a permission question.
  - Depends on: E-01
  - Expected outcome: both named tests updated to assert the release record is VISIBLE (not merely to expect a larger count); a bare `python3 -m pytest` matching the measured `5930 passed, 3 skipped, 2 xfailed` baseline by failing NODE IDS (zero failures), with the actual output pasted.
  - Execution state: performed

- [x] E-07 RECONCILE THE `check.scope-drift` DELTA THIS CHANGE PRODUCES, so an executor is not surprised by `aw check` growing findings and does not "fix" it destructively. MEASURED: `aw check --agent` goes from 171 findings to 173, entirely `check.scope-drift`, +1 each on pending plans `xdr83v` and `hp9rot`.
  THIS IS AN ARTIFACT OF THE EXECUTOR'S OWN EDIT, NOT A DEFECT THE FIX INTRODUCES. Those two plans hold LIVE begin receipts, and `check_scope_drift` compares every path changed since their frozen base against their declared Scope-Paths; `agent_workflows/artifact_core.py` is in neither plan's scope, so the executor's own edit to it is attributed to both. The count returns to 171 once the edit is committed and those receipts are reconciled or the plans finalize.
  DO NOT ATTEMPT TO REDUCE THIS COUNT. Do not edit `xdr83v` or `hp9rot`, do not touch their receipts, and do not widen their Scope-Paths: both are other agents' in-flight work under the shared-checkout rule. Record the delta and its cause; that is the whole deliverable.
  ALSO CONFIRM WHAT DOES **NOT** CHANGE, because `SCAN_ROOTS` is documented as "the single enumeration shared by the reference tools and the dangling detector across areas" and widening it widens every consumer (`plans_index`, `research_index`, `artifact_refs`, `artifact_rename`, `research_archive`). Measured: research dangling citations stay at 6 before and after, and no new `check.*-dangling` rule fires. Re-measure and paste rather than assuming.
  - Depends on: E-01
  - Expected outcome: the before/after `aw check --agent` finding counts and the per-rule delta pasted, with the two attributed plans named and their cause stated; a re-measured confirmation that no dangling-citation or index consumer gained a finding; no edit to either attributed plan or its receipt.
  - Execution state: performed

- [x] E-02 CONFIRM THE STATUS MAPPING PRODUCES THE RIGHT CLASS for a real release record, rather than assuming the map is correct because it exists. `attention_contract` maps `planned`->ready, `blocked`->blocked, `shipped`->done. The one record on disk exercises exactly one of those three.
  CHECK ALL THREE VALUES, not just the one on disk. A map that has never run is not a map that works, and a release record is cheap to synthesize in a temporary repo. If a status value in the release-record contract has NO entry in the map, that is a finding to report, not a gap to paper over.
  THE VOCABULARY IS ALREADY CLOSED AND ALREADY TOTAL, MEASURED, so this item is a demonstration and not a search. `releases.RELEASE_STATUSES` is exactly `("planned", "blocked", "shipped")` and `attention_contract.CLASS_MAPS["releases"]` has exactly those three keys, so no value is unmapped today. WHAT IS MISSING IS THE GUARD: every other tracked tree has a totality test comparing its map keys to its owning enum (`tests/test_attention_contract.py:62-71` for specs/plans/research, `tests/test_backlog.py:52` for backlog), and `RELEASE_STATUSES` greps to ZERO hits in `tests/`. ADD THE MISSING TOTALITY TEST asserting `set(CLASS_MAPS["releases"]) == set(releases.RELEASE_STATUSES)`, in the same shape as its four siblings. That, not a one-off print, is what makes a future enum addition fail closed.
  ASSERT THROUGH THE SCANNER, NOT ONLY THROUGH `class_of`. A synthesized record must be shown to reach `attention.scan` and emerge with the right `attention_class`, because the defect this plan fixes was precisely a correct map that nothing ever called. Also cover the two shapes both in live use: FLAT (`.aw/records/releases/<x>.release.md`, the live record) and SUBDIRECTORY (`.aw/records/releases/planned/<x>.release.md`, used by `tests/test_next_ordering.py:1284`).
  DO NOT CHANGE THE MAP to make an output look tidier. If a mapping is wrong, report it: the map is a contract other surfaces read, and `aw check releases` is fail-closed in CI on the record shape.
  - Depends on: E-01
  - Expected outcome: a totality test asserting the releases map keys equal `releases.RELEASE_STATUSES` (mirroring the four sibling tests); each of the three statuses shown reaching its declared class THROUGH `attention.scan` on synthesized records, in both the flat and subdirectory layouts; any unmapped status value reported rather than silently added.
  - Execution state: performed

### Task group 2: decide reviews deliberately

- [x] E-03 GIVE THE `reviews` TREE A RECORDED DECISION as an EXCLUSION: add `TreePolicy(name='reviews', root='.agents/reviews', tracked=False, owner='', reason=...)` in the same shape the five existing exclusions use. Measured at HEAD `8dffd7a0`, the tree holds 132 `.review.md` records (NOT the 82 the plan's own history line recorded; that number is stale) and has NEITHER a policy nor a scan root, so it is the only consequential tree that is absent rather than decided.
  EXCLUDED, NOT TRACKED, AND THE REASON IS DECISIVE RATHER THAN A PREFERENCE. A review record HAS NO `- Status:` FIELD AT ALL: measured, `grep -l '^- Status:' .aw/records/reviews/*.review.md` returns ZERO of 132 files. Its front matter is `Subject-Id`, `Subject-Type`, `Reviewed-At`, `Reviewer`, `Verdict` (and sometimes `Readiness`). The attention contract maps `(tree, native_status) -> class` and spec `20260808-1945-01` Section 6 requires that mapping be PURE and TOTAL over the tree's native enum while forbidding the scanner to INFER state from prose. A tree with no status field has no enum to be total over, so tracking it would require either inventing a lifecycle the owner does not have or inferring class from `Verdict`, and Section 6 forbids the second. This is the same rationale the walkthroughs and roadmaps exclusions already record ("no lifecycle status in v1"), applied to a tree that fits it exactly.
  THE FIVE EXISTING EXCLUSIONS ARE THE TEMPLATE, and each carries a real reason: walkthroughs "narrative records; no lifecycle status in v1 (OQ8)", roadmaps "intent, not commitment; no lifecycle status in v1 (OQ8)", prompts and comms "deferred to Phase 3 (OQ3)", docs-prompts "the evergreen copy-paste prompt LIBRARY, not a lifecycle-tracked artifact tree". Match that standard: a reason that says only "not tracked" is not a reason. The reason MUST state both halves: that a review record carries no `- Status:` (so there is no native enum to map), and that its findings are already policed as ERRORs by `check.review-finding-unescalated` and `check.review-decision-unescalated`, so exclusion loses no enforcement.
  DO NOT TRACK IT, and this is now a fence rather than an option. Tracking would be a contract change to a spec whose `- Status:` is `implemented`, would need a native status vocabulary the `reviews` owner has not defined, and is a maintainer-scope decision on both counts. If an executor believes tracking is right, that is a NEW backlog item, not an in-flight substitution.
  ADD NO SCAN ROOT FOR REVIEWS. An excluded tree is filtered by `if not pol.tracked: continue` in `attention.scan` AFTER being scanned, so a scan root would cost 132 file reads per invocation for records that are then discarded. The `TreePolicy` alone discharges the decision.
  - Depends on: none
  - Expected outcome: a `TreePolicy` for reviews with `tracked=False` and a reason naming both the absent `- Status:` field and the existing `aw check` enforcement; the five existing exclusion reasons pasted beside it; no scan root added; no status map invented; no spec amendment needed (an exclusion adds no mapping).
  - Execution state: performed

### Task group 3: make the drift impossible to repeat silently

- [x] E-04 ADD THE CONSISTENCY CHECK the item asks for: assert that every tree in `TRACKED_TREES` has at least one corresponding entry in `SCAN_ROOTS`. This is the item's requirement 3 and it is what stops a sixth tree being declared and never scanned.
  ASSERT THE RELATIONSHIP, NOT A HARDCODED LIST. A test that pins the current five names passes forever and catches nothing; the point is that ADDING a tracked tree without a scan root must fail. Derive both sides from the modules at test time.
  THE COVERAGE PREDICATE IS THE HARD PART AND THREE NAIVE FORMS ARE ALREADY MEASURED WRONG. Do not write one before reading these results, all taken at HEAD `8dffd7a0`.
  (a) SUBSTRING (`any(tree in root for root in SCAN_ROOTS)`) is the obvious form and it does work today, returning False for `releases` at HEAD. But it is coincidental: it matches any root whose text happens to contain the tree name, so it would call a tree covered by an unrelated path. Do not ship it without saying why it is safe, or prefer a stricter form.
  (b) `_classify_tree(root)` alone is WRONG and would FAIL IMMEDIATELY. Measured: `_classify_tree('.agents/docs')` returns None, so `specs` and `research` would both be reported uncovered even though `.agents/docs` is their scanned ANCESTOR. A predicate must accept a root that CONTAINS the tree, not only one that IS or is INSIDE it.
  (c) TREE-NAME-ONLY lookups CRASH on the very case the guard exists for. `TRACKED_TREES` is DERIVED (`tuple(p.name for p in TREE_POLICY if p.tracked)`), so a `next(p for p in TREE_POLICY if p.name == t)` lookup raises `StopIteration` for a tracked tree with no policy. That cannot happen through the derived tuple, but it is exactly what a mutation test will do, so write the lookup defensively.
  THE MEASURED-CORRECT PREDICATE accepts a root that is the policy root, is INSIDE it (`root == pol.root or root.startswith(pol.root + "/")`), CONTAINS it (`pol.root.startswith(root + "/")`), or classifies to it (`_classify_tree(root).name == tree`, which is what resolves the `.aw/records/<type>` twin spelling). Verified: all five tracked trees are covered with the E-01 change, and `releases` alone is uncovered without it.
  STATE THE GUARD'S LIMIT PLAINLY IN ITS OWN DOCSTRING, because this is where a reader will over-trust it. The guard proves a tracked tree has SOME scan root; it does NOT prove the tree's records are REACHED. Measured: `.agents/releases` alone satisfies the guard while `aw attention` still reports zero releases, because `releases.py::_releases_dir` hardcodes `.aw/records/releases`. A guard that can be satisfied without fixing the bug must say so, or the next agent will read green and stop.
  CONSIDER THE REVERSE DIRECTION AND DECIDE IT EXPLICITLY. Several `SCAN_ROOTS` entries are deliberately NOT tracked trees (`DECISIONS.md`, `README.md`, `ARCHITECTURE.md`, `TODO.md`, `.aw/records/walkthroughs`, `.aw/records/roadmaps`, `.aw/records/prompt-library`, `.agents/docs`), so a symmetric assertion would fail immediately and wrongly. State that the check is deliberately one-directional and why, or the next reader will "fix" it into a false failure. NOTE `TODO.md`'s presence in `SCAN_ROOTS` is itself the subject of sibling backlog `ld08f1`; do not resolve that here.
  MAKE THE FAILURE MESSAGE CONSTRUCTIVE. This repository records that a gate stating only a prohibition gets complied with by DELETION, and here the destructive fix is obvious and wrong: a failing check could be silenced by removing a tree from `TRACKED_TREES`, or (since that tuple is derived) by flipping its `TreePolicy` to `tracked=False`. The message must name the tree and say the constructive action is to add its scan root, and must name that second bypass so it is not mistaken for a fix.
  - Depends on: E-01, E-03
  - Expected outcome: a test deriving both lists from the modules and asserting every tracked tree has a scan root, using a predicate that handles the ancestor and twin-spelling cases (with the three rejected forms recorded); a docstring stating the guard proves declaration and NOT reachability, citing the `.agents/releases`-alone measurement; the one-directional design stated with its reason; a failure message naming the tree, the constructive fix, and the `tracked=False` bypass.
  - Execution state: performed

- [x] E-05 MUTATION-CHECK THE GUARD, because a consistency check that cannot fail is decoration. Perform BOTH mutations below and paste each failing and each passing run.
  MUTATION 1 CANNOT BE DONE AS THE PLAN ORIGINALLY WROTE IT, and the correction matters. "Add a fake tree to `TRACKED_TREES`" is impossible: measured, `TRACKED_TREES` is DERIVED (`tuple(p.name for p in TREE_POLICY if p.tracked)`), so appending to it in a test is a no-op against the real value. Mutate at the SOURCE instead: monkeypatch `TREE_POLICY` with an extra `TreePolicy(name='frobnicated', ..., tracked=True)` and re-derive, or monkeypatch `TRACKED_TREES` and `SCAN_ROOTS` together as the values the guard reads. Be aware a tracked tree also needs a `CLASS_MAPS` entry or the sibling totality test at `tests/test_attention_contract.py:74` fails for an unrelated reason, which would make the mutation prove nothing; keep the mutation scoped to the guard under test.
  MUTATION 2 IS THE LOAD-BEARING ONE: remove the releases scan root added in E-01, show the guard FAILS naming `releases`, restore, show it passes. It demonstrates the guard would have caught the ACTUAL bug that motivated this plan, rather than only a synthetic one.
  MUTATION 3, ADDED BECAUSE THE GUARD'S KNOWN BLIND SPOT MUST BE PROVEN RATHER THAN ASSERTED: leave ONLY `.agents/releases` in `SCAN_ROOTS` (drop `.aw/records/releases`) and show the guard PASSES while `attention.scan` still yields ZERO releases items. Measured to behave exactly this way. This is not a defect in the guard; it is the limit E-04's docstring must state, and a passing E-05 that omits it has not shown that the guard and the fix are independent.
  - Depends on: E-04
  - Expected outcome: three mutations pasted in full; mutations 1 and 2 each FAIL naming the offending tree and pass after revert; mutation 3 PASSES the guard while the scan still returns zero releases, demonstrating the declaration-vs-reachability gap.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE POLICY AND THE MAP ALREADY EXIST FOR RELEASES. `TreePolicy(name='releases', root='.agents/releases', tracked=True, owner='aw releases', reason='release records (ship-gate anchors); tracked lifecycle planned/blocked/shipped (awrelease)')`, and `attention._classify_tree` rewrites `.aw/records/<type>` to `.agents/<type>` before matching, so a `.aw/records/releases/` path already resolves. Only the scan root is missing.
- EVERY RECORDS-CLASS TREE IS LISTED IN BOTH GENERATIONS. `SCAN_ROOTS` carries `.agents/plans` and `.aw/records/plans`, `.agents/backlog` and `.aw/records/backlog`, because the layout migrated. Follow that shape.
- THE FIVE EXCLUSIONS EACH CARRY A REAL REASON, which is the standard E-03 must meet.
- `TRACKED_TREES` IS DERIVED, NOT WRITTEN: `tuple(p.name for p in TREE_POLICY if p.tracked)`. So `TREE_POLICY` is the single source and there is no second list to edit; a "sixth tracked tree" is added by writing a `tracked=True` policy, and a guard failure can be silenced by flipping that flag. Both E-04's message and E-05's mutation depend on this.
- EVERY OTHER TRACKED TREE HAS A MAP-TOTALITY TEST AND RELEASES HAS NONE. `tests/test_attention_contract.py:62-71` covers specs/plans/research and `tests/test_backlog.py:52` covers backlog; `RELEASE_STATUSES` greps to ZERO hits under `tests/`. E-02 closes that asymmetry.
- A REVIEW RECORD CARRIES NO `- Status:` FIELD. Measured across all 132 `.review.md` files: zero contain one. Its front matter is `Subject-Id`/`Subject-Type`/`Reviewed-At`/`Reviewer`/`Verdict`. This is what decides E-03.
- `SCAN_ROOTS` IS A SHARED ENUMERATION, documented in place as "the single enumeration shared by the reference tools and the dangling detector across areas". Widening it widens `plans_index`, `research_index`, `artifact_refs`, `artifact_rename` and `research_archive` simultaneously. E-07 measures that blast radius rather than assuming it is nil.
- THE RELEASES TREE IS SCANNED WITH `rglob`, so both the live FLAT layout and the `releases/planned/<x>.release.md` subdirectory layout used by `tests/test_next_ordering.py:1284` are covered by one root. Do not add a second root per subdirectory.
- AN UNCLASSIFIED FILE IS ONLY FLAGGED UNDER `.agents/`. `attention.scan` appends `attention.unclassified-tree` drift only when the path starts with `.agents/`, so a root-level or `.aw/records/`-level file with no policy is dropped SILENTLY. That is why the releases gap produced `valid: true` rather than a violation, and it is the same mechanism sibling `ld08f1` reports for `TODO.md`.
- VALIDATION AND SURFACING ARE SEPARATE, AND BOTH EXIST. `aw check releases` is wired fail-closed in CI (`.github/workflows/tests.yml:157-159`) while `aw attention` never sees the tree. Do not read the passing CI check as evidence the view is complete.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals. THE BASELINE IS CLEAN, corrected from this plan's own earlier text: re-measured in an isolated worktree at HEAD `8dffd7a0`, a bare run is `5930 passed, 3 skipped, 2 xfailed` with ZERO failures, and `tests/test_orchestrator_retirement.py` passes on its own (112 passed). The plan previously asserted `1 failed, 5648 passed` with a known `test_orchestrator_retirement.py` failure; that is STALE and must not be used to excuse a failure. Any failure after this plan's edits is this plan's to explain.

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`; F-10..F-16 re-measured at HEAD `8dffd7a0`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `attention_contract.TRACKED_TREES`, `artifact_core.SCAN_ROOTS` | `releases` is declared tracked and matches NO scan root, while the other four tracked trees each match at least one. | resolved every tracked tree against `SCAN_ROOTS` by import; releases -> none |
| F-2 | MED | measured | `aw attention --format json` returns ZERO releases with `valid: true` and zero violations, while a release record exists on disk. The item measured 749 items and this plan measured 848; at HEAD `8dffd7a0` it is 921 (plans 607, backlog 175, research 110, specs 29). The corpus keeps growing; the zero has not changed. Do not treat any of these totals as a fixed expectation. | ran the command and counted by `tree` |
| F-3 | CORRECTION | `attention_contract.TREE_POLICY`; `attention._classify_tree` | THE ITEM UNDERSTATES WHAT EXISTS: `releases` ALREADY has a `TreePolicy` (tracked, owned by `aw releases`) and `_classify_tree('.aw/records/releases/x.release.md')` already resolves to it. So the fix is ONE scan root, and adding a policy would create a duplicate. | printed `TREE_POLICY`; called `_classify_tree` on a releases path |
| F-4 | MED | `attention.scan` | An unclassified file is flagged as drift ONLY when its path starts with `.agents/`; anything else is dropped silently. That is why this defect reports `valid: true` instead of a violation. | source read of the `pol is None` branch |
| F-5 | MED | `attention_contract.TREE_POLICY` | `reviews` has NEITHER a policy nor a scan root, unlike the five trees deliberately excluded WITH reasons. The tree holds 132 `.review.md` records at HEAD `8dffd7a0`, not the 82 this plan recorded. | printed `TREE_POLICY`; counted `.aw/records/reviews/*.review.md` -> 132 |
| F-6 | MED | `check_engine` | `check.review-finding-unescalated` treats an unescalated review finding as an ERROR, which is why the reviews exclusion deserves a recorded reason. It does NOT by itself require the tree be tracked, since the finding is already policed. | rule read |
| F-7 | LOW | `.github/workflows/tests.yml:157-159` | `aw check releases` is fail-closed in CI, so release records are validated but not surfaced. That split is what made this easy to miss. | file read |
| F-8 | LOW | `artifact_core.SCAN_ROOTS` | `SCAN_ROOTS` legitimately contains entries that are NOT tracked trees (four root docs plus walkthroughs, roadmaps, prompt-library), so the E-04 guard must be ONE-directional or it fails wrongly. `TODO.md` is among them and is sibling `ld08f1`'s subject. | list read |
| F-9 | CONFIRMED-NOT-OVERLAPPING | pending plan `rnkqrc` | That plan (from `jys5dp`) names BOTH the releases scan root and the reviews policy in its deferred section as "both their own items", so this work is unowned. | read its deferred section |
| F-10 | HIGH | `tests/test_backlog.py:248`, `tests/test_next_ordering.py:1327` | THE FIX BREAKS TWO TESTS AND THE PLAN DECLARED NO FALLOUT. Both assert an exact item/line COUNT on a fixture that creates a release record, so both fail the moment a release record becomes visible (`2 != 1` and `3 != 2`). Neither test file was in `- Scope-Paths:`. Now E-06, with both paths declared. | applied E-01 in an isolated worktree; bare `python3 -m pytest` -> `2 failed, 5928 passed` |
| F-11 | MED | this plan's `## Project conventions` | THE STATED BASELINE IS STALE AND EXCUSES A FAILURE THAT DOES NOT EXIST. The plan recorded `1 failed, 5648 passed` with a known `test_orchestrator_retirement.py` failure; at HEAD `8dffd7a0` a bare run is `5930 passed, 3 skipped, 2 xfailed` with ZERO failures and that module passes standalone (112 passed). A stale known-failure baseline is how a real regression gets waved through. | ran the bare suite and the module alone on a clean worktree |
| F-12 | HIGH | `agent_workflows/releases.py::_releases_dir` | THE GUARD E-04 ADDS CAN BE SATISFIED WITHOUT FIXING THE BUG. With ONLY `.agents/releases` in `SCAN_ROOTS`, the cross-list guard PASSES while `attention.scan` still yields ZERO releases, because `_releases_dir` hardcodes `.aw/records/releases` and no `.agents/releases` exists. So OQ-02 is not cosmetic: `.aw/records/releases` is the load-bearing entry. Now stated in E-01 and proven by E-05 mutation 3. | dropped the `.aw/` root, re-ran the scan -> 0 releases with the guard green |
| F-13 | HIGH | `attention_contract.TRACKED_TREES` | E-05's MUTATION 1 IS IMPOSSIBLE AS WRITTEN. `TRACKED_TREES` is DERIVED (`tuple(p.name for p in TREE_POLICY if p.tracked)`), so "add a fake tree to `TRACKED_TREES`" is a no-op; the mutation must go through `TREE_POLICY`. The same derivation gives the guard a second silencing bypass (flip `tracked=False`) that its message must name. | compared `TRACKED_TREES` to the derivation; got `StopIteration` from a name-only policy lookup |
| F-14 | MED | `agent_workflows/attention.py::_classify_tree` | THE OBVIOUS COVERAGE PREDICATE FAILS IMMEDIATELY. `_classify_tree('.agents/docs')` returns None, so a classify-only predicate reports `specs` and `research` uncovered even though `.agents/docs` is their scanned ancestor. The predicate must accept an ANCESTOR root. Recorded in E-04 with the two other rejected forms. | called `_classify_tree` on every `SCAN_ROOTS` entry |
| F-15 | MED | `releases.RELEASE_STATUSES` | RELEASES IS THE ONLY TRACKED TREE WITH NO MAP-TOTALITY TEST. specs/plans/research are covered at `tests/test_attention_contract.py:62-71` and backlog at `tests/test_backlog.py:52`; `RELEASE_STATUSES` greps to zero hits under `tests/`. The map is total today (`planned`/`blocked`/`shipped`), but nothing keeps it so. E-02 now adds the guard rather than only printing three values. | grepped `tests/`; compared `CLASS_MAPS['releases']` keys to `RELEASE_STATUSES` |
| F-16 | LOW | `agent_workflows/artifact_core.py:154-155`, `check_engine.check_scope_drift` | WIDENING A DOCUMENTED SHARED ENUMERATION HAS MEASURABLE SIDE EFFECTS AND THE PLAN NAMED NONE. `aw check --agent` goes 171 -> 173 findings, all `check.scope-drift`, attributed to in-flight plans `xdr83v` and `hp9rot` whose live receipts see the executor's own edit to an out-of-scope file. Benign and self-clearing, but an executor told nothing will try to "fix" another agent's plan. Research dangling stays at 6, so the citation consumers are unaffected. Now E-07. | ran `aw check --agent` and the research dangling detector before and after |

## Proposed changes (ordered, validatable)

1. E-01 adds BOTH releases scan roots, adding no policy, and verifies a record actually appears (`.aw/records/releases` being the entry that fixes the defect).
2. E-06 repairs the two count-pinned tests the fix correctly breaks, asserting VISIBILITY rather than a larger number.
3. E-07 records the `check.scope-drift` delta and its cause, and confirms no citation or index consumer gained a finding.
4. E-02 adds the missing releases map-totality test and exercises all three statuses through `attention.scan` in both layouts.
5. E-03 decides `reviews` as an explicit EXCLUSION, to the standard the five existing exclusions set.
6. E-04 adds the one-directional consistency guard, with a predicate that survives the ancestor and twin-spelling cases and a docstring stating it proves declaration and not reachability.
7. E-05 mutation-checks it three ways, including the mutation that reproduces the original defect and the one that proves the guard's blind spot.

## Deferred / out of scope (with reason)

- RETIRING `TODO.md`, and its presence in `SCAN_ROOTS`. Sibling backlog `ld08f1`, whose plan is authored alongside this one. The two touch the same list, so they must not both edit it: this plan ADDS a releases entry and does not remove or repolicy the `TODO.md` entry.
- PER-REQUIREMENT SPEC TRACKING. Backlog `f1sw71`.
- THE DURABLE-CARRIER PREDICATE. Pending plan `rnkqrc` (from `jys5dp`), which explicitly defers both halves of this item to their own items.
- CHANGING ANY RELEASE RECORD, the `Blocks-Release` resolution logic, or `aw check releases`. This plan makes existing records VISIBLE; it does not change what they mean or how they validate.
- MAKING THE UNCLASSIFIED-FILE DRIFT FIRE OUTSIDE `.agents/` (F-4). That would surface this class of gap generally, and is a genuinely attractive change, but it would immediately flag the four root docs and three untracked `.aw/records/` trees that are in `SCAN_ROOTS` by design, so it needs its own decision about what to exempt. The E-04 guard closes the specific hazard without that blast radius.
- ADDING A SIXTH TRACKED TREE. Out of scope; the guard exists so that whoever does must add its scan root. TRACKING `reviews` specifically is now settled as OUT (resolved OQ-01): it would need a native status vocabulary the tree does not have and an amendment to an `implemented` spec, both maintainer scope. If it should be tracked, that is a new backlog item.
- MAKING THE E-04 GUARD PROVE REACHABILITY rather than declaration (F-12). A guard that asserted each tracked tree's records actually ARRIVE in the view would be strictly stronger, but it would need a fixture record per tree and would couple the contract test to five trees' record shapes. E-05 mutation 3 instead PROVES the gap exists and E-04's docstring names it, so a reader cannot over-trust the green. Closing it properly is its own item.
- RECONCILING THE `check.scope-drift` FINDINGS ON PLANS `xdr83v` AND `hp9rot` (F-16). They are other agents' in-flight work; the delta is caused by this executor's own uncommitted edit and self-clears. E-07 records it and explicitly forbids touching either plan.

## Scope check

- Over-scope: `attention_contract.py` is in scope ONLY for the reviews policy decision (E-03). Do NOT add a releases policy, do NOT edit the existing five exclusions, and do NOT change any status map to make output tidier. `tests/test_backlog.py` and `tests/test_next_ordering.py` are in scope ONLY for the two assertions named in E-06 (`test_backlog.py:248` and `test_next_ordering.py:1327`); do not refactor either module.
- Under-scope: stated rather than left as `none`. After this plan a file under a `.aw/records/` tree with no policy is STILL dropped silently rather than flagged as drift (F-4), and `TODO.md` is still scanned and discarded (sibling `ld08f1`). Both are named above with their owners. Two more, added by review and both deliberate: the E-04 guard proves DECLARATION and not REACHABILITY, so a tracked tree could still be declared, scan-rooted, and unreached (F-12, and E-05 mutation 3 proves the gap exists rather than closing it); and `reviews` is left EXCLUDED, so a review record's gating findings remain visible only through `aw check`, never through `aw attention` (E-03, by decision).

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. THE BASELINE IS CLEAN (`5930 passed, 3 skipped, 2 xfailed` at HEAD `8dffd7a0`), so the only acceptable end state is zero failures; see F-11 before citing any known-failure allowance.

THE GUARD'S HOME, verified rather than assumed: `tests/test_attention_registry.py` DOES NOT EXIST. The two modules that already assert on these lists are `tests/test_artifact_core.py` (which pins three `SCAN_ROOTS` members) and `tests/test_attention_contract.py`. Put the E-04 cross-list guard where it can see BOTH, and say which you chose and why; extend those modules rather than creating a third that asserts on the same two lists.

SYNTHESIZE release records in a temporary repo for E-02 rather than depending on the single record in this checkout, since a test pinned to one live record breaks when that record ships. Cover both the FLAT and the `planned/` subdirectory layouts (both are in live use).

DO NOT ASSERT A TOTAL ITEM COUNT anywhere, in a new test or a repaired one. Every count in this plan's history has already gone stale (749 -> 848 -> 921 items; 82 -> 132 review records), and F-10 exists precisely because two tests pinned counts. Assert the RELATIONSHIP: that the releases record is present with `tree: releases`, that its class is the mapped one, that `valid` is true. `tests/test_artifact_core.py:59-61` is the pattern to follow (membership, not length).

RE-RUN `aw check --agent` after the change and reconcile the delta per E-07. A finding count that moves is expected here; an unexplained one is not.

## Spec / documentation sync

The controlling spec is `.aw/records/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` (`- Status: implemented`), which owns `TRACKED_TREES`, the `TreePolicy` set, and the cross-tree class mapping.

NO SPEC AMENDMENT IS REQUIRED, and this is now RESOLVED BY READING rather than left as an instruction. Both checks the plan asked for were performed:

1. THE SPEC DOES NOT ENUMERATE THE TREES AS A CLOSED LIST. Section 8.6 states the RULE, not the roster: "Maintain an explicit inventory: every known tree is `tracked` (owner + contract + mapping) or `excluded` (rationale). A newly discovered tree that is neither is a violation ... preventing silent blind spots while letting walkthroughs/roadmaps/support dirs be deliberately excluded." Adding an EXCLUDED policy for `reviews` therefore SATISFIES the spec instead of changing it, and no roster cell needs editing. (OQ8 records walkthroughs/roadmaps as the human-resolved instances of that same rule.)
2. THE SPEC DOES REQUIRE THAT A TRACKED TREE BE SCANNED. Section 8.1: "Full scan on EVERY invocation ... via `artifact_core.iter_scan_files` over the tracked trees". A tracked tree with no scan root is not scanned, so E-01 brings the CODE INTO COMPLIANCE with a spec that already says the right thing. That is the justification for amending nothing.

The spec file is therefore deliberately ABSENT from `- Scope-Paths:`. Do NOT add it, and do NOT edit it: an `implemented` spec whose text already governs this fix needs no change, and touching it would put a declared spec edit in front of the runners for no contract change. Note that Section 8.6's own violation mechanism did NOT fire here, because `attention.scan` only raises `attention.unclassified-tree` under `.agents/` (F-4); closing that is explicitly out of scope and owned elsewhere.

E-03's EXCLUSION is what keeps this true. If a future change TRACKS the reviews tree, its native status vocabulary becomes part of the cross-tree mapping and that IS a contract change requiring an amendment plus maintainer approval; that is a reason to keep the exclusion inside this plan, not a task for it. Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

The sibling spec `.aw/records/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md` PREDICTED the `TODO.md` half of this class of bug in its own text. It is sibling `ld08f1`'s concern, not this plan's, and is not edited here.

## Open questions

### OQ-01: Should the reviews tree be tracked or explicitly excluded?

- Blocking: no
- Status: resolved
- Owner: resolved at review from repository evidence; no maintainer decision needed
- Resolution or deferral rationale: RESOLVED (2026-09-09, `/plan-review`): EXCLUDED, with `tracked=False` and a reason. The question was resolvable from evidence rather than preference, so it needed no escalation. MEASURED: a review record has NO `- Status:` field at all (zero of 132 `.review.md` files contain one; the front matter is `Subject-Id`/`Subject-Type`/`Reviewed-At`/`Reviewer`/`Verdict`). The attention contract maps `(tree, native_status) -> class`, and spec `20260808-1945-01` Section 6 requires that mapping be PURE and TOTAL over the tree's native enum while FORBIDDING the scanner to infer state from prose. A tree with no status field has no enum to be total over, so tracking it would demand either inventing a lifecycle the `reviews` owner does not have or inferring a class from `Verdict`, and Section 6 forbids the second. That is the same rationale walkthroughs and roadmaps already carry ("no lifecycle status in v1"). Exclusion also loses no ENFORCEMENT: `check.review-finding-unescalated` and `check.review-decision-unescalated` already police review findings as errors, so `aw attention` would add surfacing only. Tracking remains defensible as a FUTURE change but is then a contract change to an `implemented` spec plus a new status vocabulary, which is maintainer scope and a separate backlog item, not a substitution inside this plan. E-03 is now written as the exclusion rather than as a choice.

### OQ-02: Should `.agents/releases` be added beside `.aw/records/releases`?

- Blocking: no
- Status: resolved
- Owner: resolved at review from repository evidence
- Resolution or deferral rationale: RESOLVED (2026-09-09, `/plan-review`): ADD BOTH, with `.aw/records/releases` identified as the entry that actually fixes the defect. The question turned out NOT to be merely cosmetic, which is why it was resolved rather than left open. MEASURED: with ONLY `.agents/releases` added, `aw attention` still reports ZERO releases items, because `releases.py::_releases_dir` hardcodes `.aw/records/releases` and this repository materializes no `.agents/releases` directory. So an executor who added only the `.agents/` spelling would satisfy the E-04 cross-list guard, see it green, and ship nothing (F-12). `.aw/records/releases` is mandatory; `.agents/releases` is added for symmetry with the plans and backlog entries, which list both generations, and for pre-migration repositories, at the cost of one directory probe per scan when absent. Both are now required by E-01 and the distinction between them is stated there, with E-05 mutation 3 proving the failure mode rather than asserting it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `SCAN_ROOTS` before and after. Paste the resolution of every `TRACKED_TREES` entry against it, showing releases now matches. Paste `aw attention --format json` counted by `tree` BEFORE and AFTER, showing releases going from 0 to at least 1 and the other four counts unchanged. Paste proof no second `TreePolicy` for releases was added (print `TREE_POLICY` and show one releases entry). Confirm BOTH generations were added, and state explicitly that `.aw/records/releases` is the one that makes the record appear (per the resolved OQ-02 and F-12), not merely that both are present.
  - Observed evidence: |
      MEASURED IN THIS LANE WORKTREE at base HEAD `cdace6a5`, branch `aw/lane/m867ox`. Every number below
      comes from ONE harness (`.aw/state/m867ox-evidence/measure.py`, gitignored) run twice: once with all six
      scoped files reverted to their COMMITTED content, once with the change applied.

      ONE METHOD NOTE THAT DECIDES WHICH NUMBERS ARE TRUSTWORTHY, and it is a real trap here. The `aw` console
      script on PATH hardcodes an interpreter that imports the MAIN checkout's `agent_workflows`, NOT this
      worktree's:
        $ python3 -c "import agent_workflows; print(agent_workflows.__file__)"        # in-lane
        .../.aw/worktrees/m867ox/agent_workflows/__init__.py
        $ (cd /tmp && python3 -c "import agent_workflows; print(agent_workflows.__file__)")
        .../agent-workflows/agent_workflows/__init__.py                              # what bare `aw` gets
      So every measurement below runs `python3 -m agent_workflows ...` with cwd AND PYTHONPATH pinned to the
      lane, and the harness records the resolved module path in its own output to prove which code answered:
        "agent_workflows_module": ".../.aw/worktrees/m867ox/agent_workflows/__init__.py"   (identical, both runs)

      SCAN_ROOTS BEFORE (14 entries):
        ["DECISIONS.md", "TODO.md", "README.md", "ARCHITECTURE.md", ".agents/plans", ".agents/docs",
         ".agents/backlog", ".aw/records/plans", ".aw/records/specs", ".aw/records/research",
         ".aw/records/walkthroughs", ".aw/records/roadmaps", ".aw/records/prompt-library",
         ".aw/records/backlog"]
      SCAN_ROOTS AFTER (16 entries; the diff is COMPUTED, not eyeballed):
        added   -> ['.agents/releases', '.aw/records/releases']
        removed -> []
      So the `TODO.md` entry is untouched, as the scope fence requires (sibling `ld08f1` / plan `diof9n` owns it).

      EVERY `TRACKED_TREES` ENTRY RESOLVED AGAINST `SCAN_ROOTS` (the F-1 measurement, re-run both ways):
        BEFORE  specs    -> ['.agents/docs', '.aw/records/specs']
                plans    -> ['.agents/plans', '.aw/records/plans']
                research -> ['.agents/docs', '.aw/records/research']
                backlog  -> ['.agents/backlog', '.aw/records/backlog']
                releases -> []                                          <-- THE DEFECT, reproduced
        AFTER   specs    -> ['.agents/docs', '.aw/records/specs']        (unchanged)
                plans    -> ['.agents/plans', '.aw/records/plans']       (unchanged)
                research -> ['.agents/docs', '.aw/records/research']     (unchanged)
                backlog  -> ['.agents/backlog', '.aw/records/backlog']   (unchanged)
                releases -> ['.agents/releases', '.aw/records/releases']
      Only the `releases` row changed; the other four are identical before and after.

      `attention --format json` COUNTED BY TREE, BEFORE -> AFTER:
        BEFORE  total 1108  {'backlog': 293, 'plans': 671, 'research': 110, 'specs': 34}     releases ABSENT
        AFTER   total 1109  {'backlog': 293, 'plans': 671, 'releases': 1, 'research': 110, 'specs': 34}
      The other four counts are UNCHANGED and the delta is exactly +1, the single release record. (Per this
      plan's own instruction, no total is asserted anywhere in a test; these totals are evidence, not a fixture.)
      THE RECORD AS IT NOW APPEARS IN THE VIEW:
        {"path": ".aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md",
         "tree": "releases", "native_status": "planned", "attention_class": "ready"}

      NO SECOND `TreePolicy` FOR RELEASES WAS ADDED (F-3's warning). Counted by name in `TREE_POLICY`:
        releases policy count BEFORE = 1, AFTER = 1, and the entry is byte-unmodified:
        TreePolicy(name='releases', root='.agents/releases', tracked=True, owner='aw releases',
                   reason='release records (ship-gate anchors); tracked lifecycle planned/blocked/shipped (awrelease)')
        TREE_POLICY names diff BEFORE -> AFTER: added ['reviews'] (that is E-03, deliberate), removed [].
        TRACKED_TREES is IDENTICAL before and after: ('specs','plans','research','backlog','releases').

      THE RECORD IS ACTUALLY REACHED, not merely rooted, which is the acceptance condition E-01 insists on.
      `iter_scan_files` now yields exactly TWO files under the tree, of which the README is dropped from the
      VIEW by `is_nonartifact_name`, leaving exactly one record:
        BEFORE: []
        AFTER : ['.aw/records/releases/20260820-f33nrj-01-f33nrj-2-0-0.release.md',
                 '.aw/records/releases/README.md']

      BOTH GENERATIONS WERE ADDED AND `.aw/records/releases` IS THE ONE THAT FIXES THE DEFECT. Stated as
      required, and MEASURED rather than restated: E-05 mutation 3 (see V-05) leaves only `.agents/releases`
      and `attention.scan` still returns ZERO releases items, because `releases._releases_dir` resolves
      `.aw/records/releases` and this repository materializes no `.agents/releases` directory at all.
      `.agents/releases` is therefore symmetry with the plans/backlog pairs plus pre-migration-repo support,
      NOT the fix. A green E-04 guard is consequently NOT evidence the defect is fixed, and the two were
      verified separately.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` output for THREE runs in the executing worktree: the pre-change baseline, the run after E-01 alone (which must reproduce the two failures at `tests/test_backlog.py:248` and `tests/test_next_ordering.py:1327`), and the final run after the repairs. Compare failing NODE IDS, not totals. Paste the before/after text of each repaired assertion and show it asserts the release record is PRESENT (`tree: releases`), not merely a larger number. Confirm no filter, skip, or `is_nonartifact_name` entry was added to preserve the old counts, and that neither test module was otherwise refactored.
  - Observed evidence: |
      THREE BARE RUNS IN THIS LANE WORKTREE, compared by FAILING NODE IDS as required, never by totals.

      A CORRECTION THE PLAN COULD NOT HAVE KNOWN, AND IT CHANGES HOW EVERY RUN BELOW MUST BE READ. A bare
      `python3 -m pytest` in this lane reports 31 failures BEFORE any edit, and they are caused by the LANE
      ENVIRONMENT, not by any code. The runner exports `AW_EXECUTION_ROLE=worker` into this turn, and the
      suite asserts on that variable directly:
        $ python3 -m pytest "tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role" -o addopts=""
            def test_driver_own_process_is_not_worker_role(self):
                """The DRIVER's own environment must never be worker-marked, or `driver_begin` would refuse."""
        >       self.assertNotEqual(os.environ.get("AW_EXECUTION_ROLE"), "worker")
        E       AssertionError: 'worker' == 'worker'
        tests/test_worker_role_refusal.py:225: AssertionError
      So each run is reported BOTH ways: as-invoked (worker marker set) and with the two runner variables
      unset (`env -u AW_EXECUTION_ROLE -u AW_PIN_KEEP_ROOT`), which is the environment the plan's clean
      baseline describes. The as-invoked runs are what make the NODE-ID comparison valid; the clean runs are
      what show the honest zero.

      RUN 1, PRE-CHANGE BASELINE (all six scoped files reverted to committed content):
        as-invoked : 31 failed, 8065 passed, 3 skipped, 2 xfailed in 118.52s (0:01:58)
        clean env  : 8096 passed, 3 skipped, 2 xfailed in 113.84s (0:01:53)      <- ZERO failures
        The 31 as-invoked failures are exactly the lane-environment set (test_worker_role_refusal,
        test_oc_runipd, test_agy_runipd_cli, test_ipd_lifecycle_cli, test_runner_backlog_close_in_lane,
        test_novalnomerge_integration), captured in full at
        `.aw/state/m867ox-evidence/00-baseline-failing-nodeids.txt`.
        NOTE the plan's own recorded baseline (`5930 passed`) is itself now stale: the suite has grown to 8096.
        This is why the contract compares NODE IDS.

      RUN 2, E-01 APPLIED ALONE (the two test repairs reverted to committed content). It reproduces the two
      predicted failures, at the two predicted lines, with the two predicted messages:
        $ python3 -m pytest tests/test_backlog.py tests/test_next_ordering.py -o addopts=""
        E       AssertionError: 2 != 1
        tests/test_backlog.py:248: AssertionError
        E           AssertionError: 3 != 2
        tests/test_next_ordering.py:1327: AssertionError
        FAILED tests/test_backlog.py::BacklogVerbTests::test_new_blocks_release_valid_and_appears_in_release_blockers
        FAILED tests/test_next_ordering.py::NonColoredBoardOrderingTests::test_release_blocker_in_order_under_explicit_sort
        ========================= 2 failed, 88 passed in 9.87s =========================
        (F-10 confirmed exactly, including both node ids and both line numbers.)

      RUN 3, FINAL (E-01 + the repairs + E-02/E-03/E-04 tests):
        as-invoked : 31 failed, 8076 passed, 3 skipped, 2 xfailed in 113.78s (0:01:53)
        clean env  : 8107 passed, 3 skipped, 2 xfailed in 114.76s (0:01:54)      <- ZERO failures
        NODE-ID COMPARISON, which is the load-bearing check:
          $ diff 00-baseline-failing-nodeids.txt 08-final-failing-nodeids.txt && echo "IDENTICAL failing node-id sets"
          IDENTICAL failing node-id sets
        So this change introduces ZERO new failures and fixes the two it caused. Passed count rises
        8096 -> 8107 (+11), which is the 11 new tests added by E-02/E-03/E-04/E-05.
        The four directly-affected modules together:
          $ python3 -m pytest tests/test_backlog.py tests/test_next_ordering.py tests/test_artifact_core.py tests/test_attention_contract.py -o addopts=""
          ============================= 142 passed in 10.46s =============================

      THE REPAIRED ASSERTIONS, BEFORE AND AFTER, both asserting PRESENCE rather than a larger number.

      (1) tests/test_backlog.py (was `:248`). BEFORE:
            items_att, drift = ATT.scan(self.repo)
            self.assertEqual(len(items_att), 1)
            self.assertEqual(items_att[0].blocks_release, "next")
            blockers = ATT.release_blockers(items_att, self.repo)
            self.assertEqual(len(blockers), 1)
            self.assertEqual(blockers[0].path, items_att[0].path)
          AFTER (bucketed by tree, so which TREES contributed is asserted, not how many items):
            by_tree = {}
            for it in items_att:
                by_tree.setdefault(it.tree, []).append(it)
            self.assertEqual(sorted(by_tree), ["backlog", "releases"])
            self.assertEqual(len(by_tree["releases"]), 1)
            self.assertEqual(by_tree["releases"][0].native_status, "planned")
            self.assertEqual(by_tree["releases"][0].attention_class, A.READY)
            backlog_items = by_tree["backlog"]
            self.assertEqual(len(backlog_items), 1)
            self.assertEqual(backlog_items[0].blocks_release, "next")
          The old `1` did not become `2`. The release record must be PRESENT, with `tree: releases`, status
          `planned` and class `ready`; if it vanished for any other reason the `sorted(by_tree)` assertion
          fails. The final line also changed from `items_att[0].path` to `backlog_items[0].path`, because the
          original indexed position 0 of an unordered mixed-tree list and would now silently compare against
          whichever tree sorted first: that was a latent fragility the fix exposed, not a new one.

      (2) tests/test_next_ordering.py (was `:1327`). BEFORE:
            self.assertEqual(len(lines_exp), 2)
            self.assertIn("eee555", lines_exp[0])
            self.assertIn("aaa111", lines_exp[1])
          AFTER (the RELATIONSHIP the test exists to prove, plus the record's presence with its tree tag):
            backlog_lines = [line for line in lines_exp if "[backlog]" in line]
            release_lines = [line for line in lines_exp if "[releases]" in line]
            self.assertEqual(len(backlog_lines), 2)
            self.assertIn("eee555", backlog_lines[0])
            self.assertIn("aaa111", backlog_lines[1])
            self.assertEqual(len(release_lines), 1)
            self.assertIn("rel001", release_lines[0])
            self.assertIn("(planned)", release_lines[0])
            self.assertEqual(len(lines_exp), len(backlog_lines) + len(release_lines))
          The blocking item still must sort AHEAD of the non-blocking one (the test's actual subject), and the
          release record must appear tagged `[releases]` and `(planned)`. The last line asserts no OTHER
          unexpected row appeared, which the removed count assertion used to do. The board output that drove
          this, captured live:
            - [backlog] .aw/records/backlog/open/20260101-s-01-eee555-e.backlog.md (open)
            - [backlog] .aw/records/backlog/open/20260101-s-02-aaa111-a.backlog.md (open)
            - [releases] .aw/records/releases/planned/20260101-rel-01-rel001-r.release.md (planned)

      NO FILTER, SKIP, OR `is_nonartifact_name` ENTRY WAS ADDED to preserve the old counts, which the scope
      fence forbids. `is_nonartifact_name` is UNMODIFIED (verified: it is absent from the diff of
      `attention_contract.py`, whose only change is the E-03 `reviews` policy), no `@skip` or `skipTest` was
      added to either module, and neither module was otherwise refactored: the complete diff is 18 changed
      lines in `test_backlog.py` and 17 in `test_next_ordering.py`, confined to the two named assertions.
      CONFIRMED ALSO that the subdirectory layout needed no extra scan root (F-6's note): `iter_scan_files`
      uses `rglob`, and the `releases/planned/<file>.release.md` record in this very test is found by the one
      `.aw/records/releases` root.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `aw check --agent` finding counts and the per-rule breakdown BEFORE and AFTER, and name every plan any new finding is attributed to. State the cause (live begin receipts seeing an out-of-scope edit by the executor) and confirm neither attributed plan, nor its receipt, nor its Scope-Paths was touched. Separately paste the research dangling-citation count before and after, and confirm no `check.*-dangling` rule and no per-type `index --check` gained a finding. An unexplained delta is a FAIL, not a note.
  - Observed evidence: |
      BEFORE AND AFTER, both measured in this lane against THIS worktree's package (never the `aw` script,
      which imports the main checkout; see V-01's method note):

        findings BEFORE = 496
        findings AFTER  = 514      (delta +18)

      PER-RULE BREAKDOWN, BEFORE -> AFTER. Exactly ONE rule moved:
        check.scope-drift                345 -> 363    (+18)
        check.ipd-uncarried-obligation   105 -> 105
        check.setid-collision             33 ->  33
        check.lifecycle-transition-invalid 5 ->   5
        check.name-nonconformant           3 ->   3
        check.from-backlog-gate-mismatch    2 ->   2
        check.id6-collision                 1 ->   1
        check.from-backlog-dangling         1 ->   1
        check.system-layout-missing         1 ->   1

      THE PLAN'S PREDICTION WAS DIRECTIONALLY RIGHT AND NUMERICALLY STALE, which is worth stating plainly
      rather than quietly matching. E-07 predicted 171 -> 173 (+2) on plans `xdr83v` and `hp9rot`. The
      mechanism is exactly as described, but the corpus moved on: the delta is +18 across FOUR plans, and
      NEITHER originally-named plan is among them (both have since left the pending tree). Per-plan:
        .aw/records/plans/pending/20260908-runanalytics-09-ixis0c-...ipd.md   130 -> 133   (+3)
        .aw/records/plans/pending/20260908-runanalytics-10-9xycbh-...ipd.md   137 -> 140   (+3)
        .aw/records/plans/pending/20260908-runnoop-01-zz5yxq-...ipd.md         42 ->  48   (+6)
        .aw/records/plans/pending/20260911-nobugship-01-zqs0px-...ipd.md       36 ->  42   (+6)
        total                                                                            +18

      THE CAUSE IS THIS EXECUTOR'S OWN UNCOMMITTED EDIT, ATTRIBUTED BY OTHER PLANS' LIVE RECEIPTS, exactly the
      mechanism E-07 names. Verified by asking the evaluator which changed path each new finding cites, rather
      than inferring it: every one of the 18 names one of MY six scoped files.
        $ python3 -c "... check_engine.check_scope_drift(repo) ... group by plan, filter to my six paths"
          PLAN: 20260908-runanalytics-09-ixis0c-...      PLAN: 20260908-runnoop-01-zz5yxq-...
               agent_workflows/artifact_core.py               agent_workflows/artifact_core.py
               agent_workflows/attention_contract.py         agent_workflows/attention_contract.py
               tests/test_artifact_core.py                   tests/test_artifact_core.py
               tests/test_attention_contract.py              tests/test_attention_contract.py
               tests/test_backlog.py                         tests/test_backlog.py
               tests/test_next_ordering.py                   tests/test_next_ordering.py
          PLAN: 20260908-runanalytics-10-9xycbh-...      PLAN: 20260911-nobugship-01-zqs0px-...
               (the same six)                                (the same six)
      `check_scope_drift` compares every path changed since each live receipt's frozen `base_head` against
      that plan's declared Scope-Paths; my six files are in none of those four plans' scope, so my working-tree
      edit is attributed to all four. 4 plans x 6 files = 24 potential findings; 18 are new because some of
      those paths were already counted against some of those plans before my edit. The count returns to its
      prior level once those receipts are reconciled or those plans finalize.

      NEITHER ATTRIBUTED PLAN, NOR ITS RECEIPT, NOR ITS SCOPE-PATHS WAS TOUCHED, as the fence requires: all
      four are other agents' in-flight work under the shared-checkout rule. My complete diff is the six
      declared paths and nothing else:
        $ git diff --stat
         agent_workflows/artifact_core.py      |  10 ++
         agent_workflows/attention_contract.py |  28 ++++
         tests/test_artifact_core.py           |  31 ++++
         tests/test_attention_contract.py      | 270 ++++++++++++++++++++++++++++++++++
         tests/test_backlog.py                 |  18 ++-
         tests/test_next_ordering.py           |  17 ++-
         6 files changed, 368 insertions(+), 6 deletions(-)
      No plan file, no `.aw/state/ipd-lifecycle/` receipt, and no `Scope-Paths:` line of any other plan appears
      in it.

      WHAT DOES **NOT** CHANGE, re-measured rather than assumed, because `SCAN_ROOTS` is documented in place as
      "the single enumeration shared by the reference tools and the dangling detector across areas" and
      widening it widens `plans_index`, `research_index`, `artifact_refs`, `artifact_rename` and
      `research_archive` at once:
        research dangling citations BEFORE = 15, AFTER = 15   (unchanged)
        no `check.*-dangling` rule gained a finding: `check.from-backlog-dangling` is 1 both before and after,
        and no other `*-dangling` rule appears in either run's breakdown.
        no per-type index rule moved: every rule except `check.scope-drift` is identical above.
      (The plan recorded 6 research danglers; the live number is 15 both before and after. The INVARIANT the
      V-item asks for is that the number does not MOVE, and it does not.)

      WHY THE TREE ADDS NO CITATION SURFACE, which explains the flat dangling count rather than leaving it
      lucky: the two files the new roots contribute are one release record and one README, and neither carries
      an id6 citation handle that the dangling detector would try to resolve.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new totality test asserting `set(CLASS_MAPS["releases"]) == set(releases.RELEASE_STATUSES)`, and paste it beside one of its four sibling tests (`tests/test_attention_contract.py:62-71` or `tests/test_backlog.py:52`) to show the shape matches. Paste, for EACH of `planned`, `blocked` and `shipped`, a synthesized release record and the class it received THROUGH `attention.scan` (not only through `class_of`), matching the declared map. Cover BOTH the flat and the `planned/` subdirectory layouts. Paste the vocabulary you compared against, and if any value has no map entry, name it. Confirm the tests synthesize records rather than reading the single live one, and that no test asserts a total item count.
  - Observed evidence: |
      THE NEW TOTALITY TEST, as written in `tests/test_attention_contract.py`:

          def test_releases_total_over_RELEASE_STATUSES(self):
              """durablecapture-02 (`m867ox`) E-02: the missing sibling of the three tests above.

              `releases` was the only TRACKED tree with no map-totality guard (`RELEASE_STATUSES` grepped to
              zero hits under `tests/`), so the map happened to be total while nothing kept it so. This is
              what makes a status added to `releases.RELEASE_STATUSES` fail CLOSED here instead of reaching
              `class_of` unmapped at runtime.
              """
              from agent_workflows import releases

              self.assertEqual(
                  set(A.CLASS_MAPS["releases"].keys()), set(releases.RELEASE_STATUSES)
              )

      BESIDE ITS FOUR SIBLINGS, to show the shape matches. Three live in the same class, immediately above it:

          def test_specs_total(self):
              self.assertEqual(set(A.CLASS_MAPS["specs"].keys()), set(A.SPEC_STATUSES))

          def test_plans_total_over_RECOGNIZED(self):
              self.assertEqual(set(A.CLASS_MAPS["plans"].keys()), set(plans.RECOGNIZED))

          def test_research_total_over_STATUSES(self):
              self.assertEqual(
                  set(A.CLASS_MAPS["research"].keys()), set(research_contract.STATUSES)
              )

      and the fourth is `tests/test_backlog.py:52`:

          def test_map_covers_every_status(self):
              self.assertEqual(set(A.CLASS_MAPS["backlog"].keys()), set(B.STATUSES))

      Same single-assertion shape, same direction (map keys == the owning module's enum), placed in the same
      `MappingTotalityTests` class as three of the four. The asymmetry F-15 recorded is closed: `releases` was
      the only tracked tree whose enum had zero references under `tests/`.

      THE VOCABULARY COMPARED AGAINST, printed from the source of truth rather than transcribed:
        releases.RELEASE_STATUSES        = ("planned", "blocked", "shipped")
        A.CLASS_MAPS["releases"].keys()  = ("planned", "blocked", "shipped")
      NO STATUS VALUE IS UNMAPPED, so there is nothing to report under E-02's "report it, do not paper over it"
      clause, and the map was NOT edited (the only change to `attention_contract.py` is E-03's `reviews`
      policy; `_RELEASES_MAP` is untouched).

      EACH OF THE THREE STATUSES REACHING ITS DECLARED CLASS **THROUGH `attention.scan`**, not through
      `class_of`, which is the point: the defect this plan fixes was a correct map that nothing ever called, so
      a `class_of` assertion would not have caught it. Measured on synthesized records:
        releases  rplann  planned  -> ready    .aw/records/releases/20260101-rel-01-rplann-x.release.md
        releases  rblock  blocked  -> blocked  .aw/records/releases/planned/20260101-rel-01-rblock-x.release.md
        releases  rshipp  shipped  -> done     .aw/records/releases/shipped/20260101-rel-01-rshipp-x.release.md
        drift: []
      Each observed class equals the declared map value (`planned`->ready, `blocked`->blocked, `shipped`->done).

      BOTH LAYOUTS IN LIVE USE ARE COVERED, and the test iterates them rather than asserting one:
        FLAT           `.aw/records/releases/<x>.release.md`          (the live record in this checkout)
        SUBDIRECTORY   `.aw/records/releases/planned/<x>.release.md`  (used by tests/test_next_ordering.py)
      The test body:
          for subdir in ("", "planned/"):
              for status in releases.RELEASE_STATUSES:
                  got, drift, rel = self._scan_synth(status, subdir)
                  self.assertEqual([i.path for i in got], [rel], f"{status} @ {subdir!r} not scanned")
                  self.assertEqual(got[0].native_status, status)
                  self.assertEqual(got[0].attention_class, A.CLASS_MAPS["releases"][status],
                                   f"{status} @ {subdir!r} got the wrong class")
                  self.assertEqual(drift, [])
      Note the expected class is read FROM the map rather than hardcoded, so this test asserts the map is
      HONORED end to end while the totality test above asserts the map is COMPLETE; neither can mask the other.
      The status list is iterated from `releases.RELEASE_STATUSES`, so a newly added status is exercised here
      automatically instead of being silently skipped.

      THE RECORDS ARE SYNTHESIZED IN A TEMPORARY REPO, never read from this checkout: `_scan_synth` builds each
      one inside `tempfile.TemporaryDirectory()` and writes its own front matter, so nothing breaks the day the
      live `2.0.0` record ships to `shipped`. And NO TEST ASSERTS A TOTAL ITEM COUNT: the assertions are
      membership/identity (`[i.path for i in got] == [rel]`) in the `tests/test_artifact_core.py:59-61`
      membership style the plan names, per this plan's explicit instruction never to pin a total.

      RUN, as invoked:
        $ python3 -m pytest tests/test_attention_contract.py tests/test_artifact_core.py -o addopts=""
        collected 52 items
        tests/test_attention_contract.py .................................       [ 63%]
        tests/test_artifact_core.py ...................                          [100%]
        ============================== 52 passed in 0.26s ==============================
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new `TreePolicy` for reviews as written, showing `tracked=False` and its reason. Paste the five existing exclusion reasons beside it so a reader can see the standard was met. Confirm the reason names BOTH halves: that a review record carries no `- Status:` (paste the measurement over the live corpus), and that its findings are already policed by `check.review-finding-unescalated`/`check.review-decision-unescalated`. Confirm NO scan root was added for reviews, NO status map was invented, and NO spec was edited. If an executor instead chose to TRACK the tree, this V-item FAILS: that is a maintainer decision and a contract change, per the resolved OQ-01.
  - Observed evidence: |
      THE NEW `TreePolicy` AS WRITTEN, in `attention_contract.TREE_POLICY`:

          TreePolicy(
              "reviews",
              ".agents/reviews",
              False,
              "",
              "review records carry NO `- Status:` field (Subject-Id/Subject-Type/Reviewed-At/Reviewer/Verdict only), so there is no native enum for the pure+total mapping Section 6 requires and inferring one from Verdict is forbidden; their findings are already policed as errors/warnings by check.review-finding-unescalated + check.review-decision-unescalated, so exclusion loses no enforcement",
          ),

      `tracked=False`, `owner=''`, and a reason. Printed back from the loaded module to prove what shipped:
        {'name': 'reviews', 'root': '.agents/reviews', 'tracked': False, 'owner': '',
         'reason': 'review records carry NO `- Status:` field (...) so exclusion loses no enforcement'}

      THE FIVE EXISTING EXCLUSION REASONS, BESIDE IT, so a reader can see the standard was met:
        walkthroughs   "narrative records; no lifecycle status in v1 (OQ8)"
        roadmaps       "intent, not commitment; no lifecycle status in v1 (OQ8)"
        prompts        "deferred to Phase 3 (OQ3); own lifecycle not yet contracted here"
        comms          "deferred to Phase 3 (OQ3); own ack lifecycle not contracted here"
        docs-prompts   "the evergreen copy-paste prompt LIBRARY, not a lifecycle-tracked artifact tree"
      The new reason is the walkthroughs/roadmaps rationale ("no lifecycle status") stated for a tree that fits
      it literally rather than approximately, plus the enforcement half those two do not need.

      BOTH HALVES ARE NAMED, and a test asserts they stay named (so the reason cannot decay into "not tracked"):

        HALF 1, NO `- Status:` FIELD. Measured over the LIVE corpus, which has grown well past the plan's
        recorded 132:
          $ ls .aw/records/reviews/*.review.md | wc -l          -> 231
          $ grep -l '^- Status:' .aw/records/reviews/*.review.md | wc -l   -> 0
        Zero of 231. A real record's front matter, for the shape:
          # Review: Extend the shipped sandbox capability contract with the runner-safety guarantees ...
          - Subject-Id: mjx7ne
          - Subject-Type: ipd
          - Reviewed-At: 2026-08-30
          - Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
          - Verdict: REVIEWED - OPEN QUESTIONS
        So there is no native enum for the PURE and TOTAL mapping spec Section 6 requires, and the only
        candidate field (`Verdict`) would have to be INFERRED from, which Section 6 forbids outright.

        HALF 2, ENFORCEMENT IS UNAFFECTED. Both rules exist and are registered with real severities, read from
        `check_engine`'s registry rather than assumed:
          "check.review-finding-unescalated":  RuleSpec("error",   ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")
          "check.review-decision-unescalated": RuleSpec("warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")
        So an unescalated review finding is already an ERROR today; excluding the tree from `aw attention`
        removes SURFACING only, never a gate.

        The test that pins both halves:
          def test_reviews_is_excluded_with_a_rationale(self):
              pol = next((p for p in A.TREE_POLICY if p.name == "reviews"), None)
              self.assertIsNotNone(pol, "the reviews tree must be inventoried, not absent")
              self.assertFalse(pol.tracked)
              self.assertEqual(pol.owner, "")
              self.assertIn("Status:", pol.reason)                        # no native enum to be total over
              self.assertIn("check.review-finding-unescalated", pol.reason)  # enforcement kept

      NO SCAN ROOT WAS ADDED FOR REVIEWS, asserted rather than promised:
          self.assertFalse(any(_scan_root_covers_tree(r, "reviews") for r in core.SCAN_ROOTS))
      `attention.scan` filters an excluded tree AFTER reading it (`if not pol.tracked: continue`), so a root
      would have cost 231 file reads per invocation for records immediately discarded.

      NO STATUS MAP WAS INVENTED, also asserted:
          self.assertNotIn("reviews", A.CLASS_MAPS)
          with self.assertRaises(A.UnknownNativeStatus):
              A.class_of("reviews", "anything")

      THE TREE WAS **NOT** TRACKED, which this V-item makes a FAIL condition. `TRACKED_TREES` is identical
      before and after the change: ('specs','plans','research','backlog','releases'), measured in V-01. Tracking
      would need a native status vocabulary the `reviews` owner has not defined plus an amendment to an
      `implemented` spec, both maintainer scope (resolved OQ-01).

      NO SPEC WAS EDITED. No `.spec.md` path appears in `git diff --name-only`; the six changed files are the
      six declared ones. This is correct rather than an omission: spec Section 8.6 states the tracked-or-excluded
      RULE and not a closed roster, so adding an EXCLUDED policy SATISFIES the spec, and spec `25kzda`'s §4.2
      finding-code table was likewise not approached.

      RUN:
        $ python3 -m pytest tests/test_attention_contract.py -o addopts=""
        collected 33 items
        tests/test_attention_contract.py .................................       [100%]
        ============================== 33 passed in 0.19s ==============================
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the guard as written, showing it DERIVES both lists from the modules rather than hardcoding names, and showing the coverage predicate handles the ANCESTOR case (`.agents/docs` covering specs and research) and the twin-spelling case. Paste it passing. Paste the failure message text and confirm it names the offending tree, states the constructive fix (add a scan root), AND names the `tracked=False` bypass that the derived `TRACKED_TREES` makes available. Paste the docstring text stating the guard proves DECLARATION and not REACHABILITY. Paste the recorded reason the check is one-directional, and the list of `SCAN_ROOTS` entries that are legitimately not tracked trees. Paste the three rejected predicate forms with the measurement that rejected each.
  - Observed evidence: |
      THE GUARD AS WRITTEN, in `tests/test_attention_contract.py`. It DERIVES both lists from the modules at
      test time and hardcodes no tree name:

          def test_every_tracked_tree_has_a_scan_root(self):
              from agent_workflows import artifact_core as core

              uncovered = [
                  t
                  for t in A.TRACKED_TREES
                  if not any(_scan_root_covers_tree(r, t) for r in core.SCAN_ROOTS)
              ]
              self.assertEqual(uncovered, [], "TRACKED but never SCANNED: " + ", ".join(uncovered) + ...)

      THE COVERAGE PREDICATE, which is the hard part, handling the ancestor and twin-spelling cases:

          pol = next((p for p in A.TREE_POLICY if p.name == tree), None)
          if pol is None:
              return False                                   # defensive: see rejected form (c)
          r = root.replace("\\", "/")
          proot = pol.root.replace("\\", "/")
          if r == proot or r.startswith(proot + "/"):
              return True   # the root IS, or is INSIDE, the tree
          if proot.startswith(r + "/"):
              return True   # the root is an ANCESTOR of the tree (.agents/docs -> specs, research)
          classified = ATT._classify_tree(r)
          return classified is not None and classified.name == tree   # the .aw/records/<type> twin spelling

      THE THREE REJECTED FORMS, each with the measurement that rejected it, recorded in the predicate's own
      docstring so the next reader cannot "simplify" back into one (all measured at HEAD `cdace6a5`):
        (a) SUBSTRING, `any(tree in root for root in SCAN_ROOTS)`. Measured: it returns the right answer for all
            five trees today (specs/plans/research/backlog True, releases False pre-fix), so it is not broken
            NOW; it is rejected because it matches any root whose TEXT contains the tree name, so an unrelated
            path would be reported as covering a tree it never walks. It tests spelling, not containment.
        (b) CLASSIFY-ONLY, `_classify_tree(root).name == tree`. Measured: `_classify_tree('.agents/docs')`
            returns `None`, while `.agents/docs` is exactly the scanned ANCESTOR of the `specs`
            (`.agents/docs/specs`) and `research` (`.agents/docs/research`) policy roots. Evaluated over the
            legacy `.agents/`-only root set this form reports:
              specs UNCOVERED (wrongly) [] | research UNCOVERED (wrongly) [] | plans covered | backlog covered
            A CORRECTION TO F-14, stated because accuracy outranks agreeing with the plan: on the CURRENT root
            list this form does not fail, because `.aw/records/specs` and `.aw/records/research` are also
            present and do classify. F-14's "would FAIL IMMEDIATELY" is therefore true of the legacy layout, not
            of HEAD. That makes the form MORE dangerous, not less: it would pass here and break on a
            pre-migration repository, which is why the ancestor branch is asserted directly by its own test.
        (c) TREE-NAME-ONLY policy lookup, `next(p for p in TREE_POLICY if p.name == t)`. Measured: raises
            `StopIteration()` for a tracked tree with no policy. Unreachable through the derived
            `TRACKED_TREES`, but it is precisely what the mutation test constructs, hence `next(..., None)`.

      THE PREDICATE'S TWO HARD CASES ASSERTED DIRECTLY, so a future simplification breaks a test rather than a
      downstream repository:
          self.assertIsNone(ATT._classify_tree(".agents/docs"))
          self.assertTrue(_scan_root_covers_tree(".agents/docs", "specs"))
          self.assertTrue(_scan_root_covers_tree(".agents/docs", "research"))
          self.assertTrue(_scan_root_covers_tree(".aw/records/specs", "specs"))
          self.assertTrue(_scan_root_covers_tree(".aw/records/releases", "releases"))
          self.assertFalse(_scan_root_covers_tree("DECISIONS.md", "releases"))
          self.assertFalse(_scan_root_covers_tree(".aw/records/releases", "frobnicated"))

      THE FAILURE MESSAGE TEXT, verbatim from a real failing run (E-05 mutation 2):
        AssertionError: Lists differ: ['releases'] != []
        - ['releases']
        + [] : TRACKED but never SCANNED: releases. Every tree in TRACKED_TREES must have at least one
        artifact_core.SCAN_ROOTS entry, or its records are invisible to `aw attention` while the view still
        reports valid: true (an unclassified file is only flagged as drift under .agents/). THE CONSTRUCTIVE FIX
        IS TO ADD THE TREE'S SCAN ROOT to artifact_core.SCAN_ROOTS (add BOTH the .agents/<tree> and
        .aw/records/<tree> spellings, as plans and backlog do; the .aw/records/ one is normally the load-bearing
        entry). DO NOT silence this by removing the tree from the attention view: TRACKED_TREES is DERIVED from
        TREE_POLICY, so flipping that policy's tracked=True to tracked=False would make this pass while HIDING
        the tree from the view entirely, which is the opposite of the fix.
      It NAMES the offending tree (`releases`), states the CONSTRUCTIVE fix (add the scan root, both spellings),
      AND names the `tracked=False` bypass the derived `TRACKED_TREES` makes available (F-13).

      THE DOCSTRING STATING DECLARATION-NOT-REACHABILITY, verbatim:
        "WHAT THIS GUARD PROVES, AND WHAT IT DOES NOT. It proves DECLARATION: a tracked tree has SOME scan
         root. It does NOT prove REACHABILITY: that the tree's records actually ARRIVE in the view. Measured,
         so this limit is a fact and not a caveat: with only `.agents/releases` in `SCAN_ROOTS` this guard is
         GREEN while `attention.scan` still yields ZERO releases items, because `releases._releases_dir` writes
         and reads `.aw/records/releases` and no `.agents/releases` directory exists in this repository. So a
         reader must not treat this passing as evidence that a tree is surfaced; `ReleaseRecordsReachTheViewTests`
         below asserts reachability for releases specifically, and E-05 mutation 3 proves the gap is real."

      THE ONE-DIRECTIONAL DESIGN AND ITS REASON, also in the docstring, with the full list of legitimately
      untracked `SCAN_ROOTS` entries so nobody "fixes" it into a false failure:
        "THE CHECK IS DELIBERATELY ONE-DIRECTIONAL (tracked tree -> scan root, never the reverse). SCAN_ROOTS
         legitimately contains entries that are NOT tracked trees, because it is the shared tracked-TEXT
         enumeration for the citation/dangling tools, not a list of lifecycle trees: four root docs
         (DECISIONS.md, TODO.md, README.md, ARCHITECTURE.md), the .agents/docs ancestor, and three deliberately
         EXCLUDED trees (.aw/records/walkthroughs, .aw/records/roadmaps, .aw/records/prompt-library). A
         symmetric assertion would fail immediately and WRONGLY on all eight, so do not 'fix' this into one."
      Measured, the eight entries that classify to None or to an untracked policy:
        DECISIONS.md -> None            .aw/records/walkthroughs -> walkthroughs (tracked=False)
        TODO.md -> None                 .aw/records/roadmaps     -> roadmaps     (tracked=False)
        README.md -> None               .aw/records/prompt-library-> docs-prompts (tracked=False)
        ARCHITECTURE.md -> None         .agents/docs             -> None
      `TODO.md`'s presence is sibling `ld08f1`'s subject and is deliberately NOT resolved here.

      THE GUARD PASSING:
        $ python3 -m pytest "tests/test_attention_contract.py::TrackedTreeScanCoverageTests::test_every_tracked_tree_has_a_scan_root" -o addopts=""
        collected 1 item
        tests/test_attention_contract.py .                                       [100%]
        ============================== 1 passed in 0.11s ==============================

      WHERE IT LIVES AND WHY. `tests/test_attention_registry.py` DOES NOT EXIST (verified: the attention
      modules present are test_attention.py, test_attention_compact.py, test_attention_contract.py,
      test_attention_notices.py, test_attention_priority_blocker.py, test_attention_stem.py). The guard is in
      `tests/test_attention_contract.py`, chosen over `tests/test_artifact_core.py` because it must see BOTH
      lists and this module already imports `attention_contract` (the owner of `TRACKED_TREES`/`TREE_POLICY`)
      while `test_artifact_core.py` deliberately imports only `artifact_core`; putting the cross-list guard here
      adds one import to the module that already owns the more complex half. A membership assertion for the two
      new roots was added to `tests/test_artifact_core.py` alongside its existing `test_scan_roots_include_*`
      pattern, so neither module was newly created and both existing modules keep their own concern.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste ALL THREE mutations in full. Mutation 1: introduce a fake tracked tree with no scan root THROUGH `TREE_POLICY` (not by appending to the derived `TRACKED_TREES`, which is a no-op per F-13), paste the FAILING output naming it, revert, paste passing. Mutation 2: remove the releases scan root added in E-01, paste the FAILING output naming `releases`, restore, paste passing. Mutation 3: leave only `.agents/releases`, paste the guard PASSING alongside a scan yielding ZERO releases items. Mutation 2 proves the guard would have caught the real defect and mutation 3 proves its blind spot; a V-05 missing either has not validated E-05.
  - Observed evidence: |
      ALL THREE MUTATIONS PERFORMED IN THIS LANE, each with the failing run, the revert, and the passing run.

      METHOD, WHICH MATTERS FOR SAFETY IN A SHARED CHECKOUT. Each mutation copies the target file
      byte-for-byte into `.aw/state/m867ox-evidence/backups/` (gitignored), mutates in place, runs the guard,
      then restores from that copy and asserts the bytes match. NO git command is used to revert. This is a
      correction of my own first attempt, which used `git checkout -- <file>` and destroyed my own uncommitted
      E-03 edit; on a shared checkout that same command could have destroyed a CO-WORKER's edit, so the
      harness (`.aw/state/m867ox-evidence/mutate.py`) removes the possibility rather than relying on care. Each
      run also reports how many releases items `attention.scan` yields UNDER the mutation, which is what makes
      mutation 3 legible.

      ################ MUTATION 1: a tracked tree with NO scan root ################
      INJECTED THROUGH `TREE_POLICY`, NOT the derived `TRACKED_TREES` (F-13: appending to the derived tuple is a
      no-op and would prove nothing). The injected line:
        TREE_POLICY = TREE_POLICY + (TreePolicy("frobnicated", ".agents/frobnicated", True, "aw frob", "MUTATION 1"),)
      FAILING RUN:
        E       AssertionError: Lists differ: ['frobnicated'] != []
        E       First list contains 1 additional elements.
        E       First extra element 0:
        E       'frobnicated'
        E       - ['frobnicated']
        E       + [] : TRACKED but never SCANNED: frobnicated. Every tree in TRACKED_TREES must have at least
        one artifact_core.SCAN_ROOTS entry, or its records are invisible to `aw attention` while the view still
        reports valid: true ... THE CONSTRUCTIVE FIX IS TO ADD THE TREE'S SCAN ROOT to artifact_core.SCAN_ROOTS
        ... DO NOT silence this by removing the tree from the attention view: TRACKED_TREES is DERIVED from
        TREE_POLICY, so flipping that policy's tracked=True to tracked=False would make this pass while HIDING
        the tree from the view entirely, which is the opposite of the fix.
        tests/test_attention_contract.py:370: AssertionError
        FAILED tests/test_attention_contract.py::TrackedTreeScanCoverageTests::test_every_tracked_tree_has_a_scan_root
        ============================== 1 failed in 0.15s ===============================
        --- releases items reaching attention.scan under this mutation: 1 ---
      It FAILS and NAMES the offending tree. AFTER REVERT:
        --- REVERTED; guard re-run exit=0 ---
        tests/test_attention_contract.py .                                       [100%]
        ============================== 1 passed in 0.11s ==============================
        --- releases items after revert: 1 ---

      ################ MUTATION 2 (LOAD-BEARING): remove the releases scan roots ################
      Removes BOTH entries added by E-01, reconstructing the exact pre-fix state that motivated this plan.
      FAILING RUN:
        E       AssertionError: Lists differ: ['releases'] != []
        E       First extra element 0:
        E       'releases'
        E       - ['releases']
        E       + [] : TRACKED but never SCANNED: releases. Every tree in TRACKED_TREES must have at least one
        artifact_core.SCAN_ROOTS entry, or its records are invisible to `aw attention` while the view still
        reports valid: true (an unclassified file is only flagged as drift under .agents/). THE CONSTRUCTIVE FIX
        IS TO ADD THE TREE'S SCAN ROOT to artifact_core.SCAN_ROOTS ... DO NOT silence this by removing the tree
        from the attention view ...
        tests/test_attention_contract.py:370: AssertionError
        FAILED tests/test_attention_contract.py::TrackedTreeScanCoverageTests::test_every_tracked_tree_has_a_scan_root
        ============================== 1 failed in 0.15s ===============================
        --- releases items reaching attention.scan under this mutation: 0 ---
      THIS IS THE PROOF THE GUARD WOULD HAVE CAUGHT THE REAL BUG: the guard fails naming `releases` in exactly
      the state where `attention.scan` returns ZERO releases items. AFTER RESTORE:
        --- REVERTED; guard re-run exit=0 ---
        tests/test_attention_contract.py .                                       [100%]
        ============================== 1 passed in 0.14s ==============================
        --- releases items after revert: 1 ---

      ################ MUTATION 3 (THE BLIND SPOT): leave ONLY `.agents/releases` ################
      Drops `.aw/records/releases` and keeps `.agents/releases`, which is the state an executor would reach by
      adding only the `TreePolicy` root spelling.
      RUN UNDER THE MUTATION:
        collected 1 item
        tests/test_attention_contract.py .                                       [100%]
        ============================== 1 passed in 0.13s ==============================
        --- releases items reaching attention.scan under this mutation: 0 ---
      THE GUARD PASSES (exit 0) WHILE THE SCAN STILL RETURNS ZERO RELEASES. That is the declaration-vs-reachability
      gap, PROVEN rather than asserted: an executor who added only `.agents/releases` would have seen a green
      guard and shipped nothing, because `releases._releases_dir` resolves `.aw/records/releases` and this
      repository materializes no `.agents/releases` directory. This is F-12 confirmed and it is exactly why
      E-01 requires BOTH entries and names which one is load-bearing, and why V-01 verified the fix and the
      guard SEPARATELY. AFTER RESTORE:
        --- REVERTED; guard re-run exit=0 ---
        ============================== 1 passed in 0.13s ==============================
        --- releases items after revert: 1 ---

      MUTATIONS 1 AND 2 ARE ALSO PERMANENT TESTS, not only one-off runs, so the guard's ability to fail is
      itself defended after this turn ends:
        TrackedTreeScanCoverageTests::test_the_guard_fails_for_a_tracked_tree_with_no_scan_root   (mutation 1)
        TrackedTreeScanCoverageTests::test_removing_the_releases_scan_root_fails_the_guard        (mutation 2)
      The first monkeypatches `TREE_POLICY`, re-derives `TRACKED_TREES`, asserts `uncovered == ['frobnicated']`,
      restores in a `finally:`, and then re-asserts the real lists are clean. The second rebuilds the pre-fix
      root tuple and asserts `uncovered == ['releases']`. Mutation 3 is NOT made a permanent test, deliberately:
      asserting that a wrong configuration passes would encode the blind spot as desired behavior. It is recorded
      here and in E-04's docstring instead, which is what the plan asks for.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the six paths in `- Scope-Paths:` (the two test modules `tests/test_backlog.py` and `tests/test_next_ordering.py` were ADDED at review for E-06, and only for the two assertions it names). Do NOT add a `TreePolicy` for releases (one exists). Do NOT edit the five existing exclusions or any status map. Do NOT remove or repolicy the `TODO.md` entry in `SCAN_ROOTS` (sibling `ld08f1`). Do NOT change any release record, the `Blocks-Release` resolution, or `aw check releases`. Do NOT make the unclassified-file drift fire outside `.agents/`. Do NOT track the `reviews` tree (resolved OQ-01). Do NOT edit any spec: the spec-sync reading is DONE and concluded no amendment is required, and never touch spec `25kzda`'s §4.2 finding-code table. Do NOT edit pending plans `xdr83v` or `hp9rot`, their begin receipts, or their Scope-Paths in order to reduce the `check.scope-drift` count (F-16): they are other agents' in-flight work. Do NOT silence the two E-06 test failures with a filter, a skip, or an `is_nonartifact_name` entry. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `SCAN_ROOTS`, `TRACKED_TREES`, `TREE_POLICY`, `TreePolicy`, `iter_scan_files`, `attention.scan`, `_classify_tree`, `RELEASE_STATUSES`, `CLASS_MAPS` and `_releases_dir` by name. The two E-06 test line numbers (`tests/test_backlog.py:248`, `tests/test_next_ordering.py:1327`) are given so the failures are recognizable, but locate the ASSERTIONS by their failing node ids, which the suite prints.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. This plan and sibling `ld08f1`'s plan both edit `artifact_core.py`, so that re-verification is not boilerplate here. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved m867ox --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `v7u6vm`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited.
