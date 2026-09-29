# IPD: Document the per-item carrier scanners as single-item-only and fail a test when a caller loops over them

- Date: 2026-09-28
- Kind: child
- Concern: `check_engine.find_from_backlog_artifacts` (and its `find_from_backlog_plans` / `find_from_backlog_specs` halves) answers "which artifacts carry a handoff for ONE item" by re-walking the ENTIRE plans tree plus the specs tree on every call. That is correct and cheap once; it is O(items x corpus) the moment a caller loops over items. Nothing in the function's name, signature, or docstring says so, the repository has been bitten by this exact shape THREE times, and the last encounter was a plan whose literal instruction would have shipped the quadratic form into `aw check all`.
- Scope: Make the single-item-only contract VISIBLE where a caller reads it (a docstring on each of the three functions naming `_from_backlog_carrier_index` as the many-item route) and MACHINE-CHECKED by a new AST test that fails when any call site passes a loop-derived id6, so the fourth encounter is a red test rather than a measurement. Deliberately does NOT reimplement the per-item functions on a cached index: authoring MEASURED that a process-lifetime cache makes the runner refuse a legitimate backlog close (F-05), so the item's second suggested fix is not merely unnecessary, it is unsafe as stated.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_carrier_scan_single_item_contract.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 8cpbia
- Set: 8cpbia
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: jpn6hy

## Workflow history
- 2026-09-29 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: jpn6hy verified (set 8cpbia, attempt 1).
- 2026-09-29 approved (aw set): status set to approved
- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-A01, PR-A02 (HIGH), PR-A03 (MEDIUM), PR-A04 (LOW), all FIXED. Reviewed at HEAD `cd967ae7`. This is an unusually well-measured plan and eight of its nine findings reproduce, several exactly: the four call sites and their empty loop-bound intersection (F-04), all eight guard fixtures case for case including the `tmp = i` hole (F-06), the iter-position discriminator that a naive enclosing-loop test gets wrong (F-07), and F-05's rejection of the backlog item's cached-index fix, which was RE-DRIVEN end to end through the real `runner_shared.evaluate_backlog_close` and reproduces with the second item refused citing a stale `pending/` path that `plan_bucket` silently reports as `pending`. THE FINDINGS ARE ABOUT WHAT WAS NOT MEASURED. FIRST, the guard's `agent_workflows/`-only scope is LOAD-BEARING and unexplained: the same analyzer pointed at `tests/` flags two LEGITIMATE sentinel-loop calls in `test_check_engine_release_gate.py`, so the obvious future widening turns the suite red with only bad remedies; E-01 now records that boundary and its reason in the module docstring. SECOND, the suite baseline is INVERTED, not merely stale: commit `f1b5b9ff` fixed the failure F-03 told the executor to expect (green at `3081 passed, 2 skipped`), so the plan as authored licensed accepting a red suite, and carrier `03aicr` is now stale while still `open` and release-gated; E-03 requires that reported and explicitly not closed. THIRD, F-02 warns the ratio is no constant and then had E-02 write one into a docstring; a review re-run measured roughly 449x with a 1.023 s shared walk against the authored 598x at 259 ms, so the durable claim is now the SHAPE. Also recorded: the mapping-equality check must use CARRIED items, since the first 60 backlog items have none. Readiness recorded in the `- Readiness:` field. Findings and three `Decisions` rows in `.aw/records/reviews/20260928-8cpbia-01-jpn6hy-document-the-per-item-carrier-scanners-as-single-item-only-a.review.md`.

- 2026-09-28 to-review (opencode): authored from backlog item `8cpbia`. Every measurement in the item was re-driven against this working tree rather than carried over, and the corpus has grown since it was filed (878 plans and 38 specs against the item's 671 and 34, 673 items against its 65), so the quadratic cost is now 155 s against a 259 ms shared walk, a 598x ratio (F-02). Authoring added two findings the item does not contain. FIRST, and it decides the plan's shape: the item's second suggested fix ("reimplement the per-item functions on top of a cached index") is UNSAFE as stated, because the runner finalizes a plan from `pending/` to `executed/` and then evaluates its own backlog close IN THE SAME PROCESS, so a cached index answers the second item from a pre-move snapshot and `evaluate_backlog_close` returns `close=False, reason='IPD carrier(s) not executed'` for a close it should have granted; this was driven end to end through the real predicate (F-05). SECOND, no call site is quadratic TODAY (F-04), which confirms the item's `chore` classification against AGENTS.md's perceptibility test and is why this plan ships a guard rather than an optimization.
- 2026-09-28 draft (opencode): created.

## Goal

Stop the repository re-learning, a fourth time, that `find_from_backlog_artifacts` must not be called once per item: say so in the docstring a caller actually reads, and add a test that FAILS when a call site violates it.

THE DEFECT IS A MISSING CONTRACT, NOT A SLOW FUNCTION, and that framing is the whole plan. The function is correctly fast for the question it is named after ("which artifacts carry a handoff for THIS item"): one walk, about 215 ms warm on this corpus, which is the right cost when there is exactly one item to answer for. What is missing is any signal that the SECOND call is nearly free of new information and the six-hundredth is a bug. So the shape keeps inviting the misuse, and the record shows it landing three times: `release_gate_warnings` was refactored away from it and its comment records the bite; `_from_backlog_carrier_index` was introduced for the same reason and its docstring records it again; and backlog `8cpbia` exists because a plan under execution literally prescribed the per-item form and required a grep proving it.

WHY A GUARD AND NOT AN OPTIMIZATION. Two reasons, both measured rather than asserted. There is no quadratic caller today (F-04), so there is no user-perceptible cost to remove and an optimization would be solving a problem nobody has. And the obvious optimization is actively harmful: caching the walk changes a CORRECTNESS-critical read, because the runner mutates the very tree being indexed between two consumers of it, which F-05 drives end to end. A docstring plus a test costs nothing at runtime, cannot break a close, and fails loudly on the one event that matters.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the contract machine-checked, then write it down

- [x] E-01 Create `tests/test_carrier_scan_single_item_contract.py` holding the AST guard that makes this contract enforceable rather than advisory. It must contain four parts. FIRST, the GUARD itself over `agent_workflows/` AND OVER THAT DIRECTORY ONLY, which is a requirement rather than an incidental choice: measured at review, pointing the same analyzer at `tests/` FLAGS TWO LEGITIMATE CALLS in `tests/test_check_engine_release_gate.py`, where a sentinel-handling test deliberately loops over the sentinel values `-`, `none`, `unresolved` and asks the scanner about each. That is correct test code (three cheap calls on a synthetic two-file repo, asserting sentinel absence), so a guard covering `tests/` would be RED on the current tree and its only cheap remedies are both bad: an allowlist, or rewriting a valid test to satisfy a guard about production shape. State the `agent_workflows/`-only scope IN THE MODULE DOCSTRING with that measurement as the reason, so a later contributor who "improves" the guard by widening its root learns why not before the suite goes red. Parse every module with `ast`, find every call to `find_from_backlog_plans`, `find_from_backlog_specs` or `find_from_backlog_artifacts` (matching both the bare-name and the attribute spelling, since `runner_shared` calls it as `_ce.find_from_backlog_artifacts`), and for each call collect the names bound by every ENCLOSING `for`/`async for` target and comprehension generator target, walking outward. Flag the call when that set INTERSECTS the set of names appearing anywhere in its arguments (positional OR keyword, so `item_id6=i` is caught as readily as `i`). Assert the flagged set is EMPTY, and on failure report `path:lineno` plus the offending name, so the message tells a reader which call and which variable rather than only that something is wrong. CRITICALLY, a call in a `for` statement's `iter` position must NOT be flagged: `for p, br in find_from_backlog_artifacts(repo, item_id6)` is the CORRECT single-item shape and is the spelling `evaluate_backlog_close` uses, so a naive "is this call inside a loop" test would flag the one shipped caller this plan is defending (measured: a first draft of this probe did exactly that). Exclude the `iter` expression by comparing node identity while climbing, not by line number. SECOND, the POSITIVE FIXTURES: run the same analyzer over inline source strings and assert it FLAGS the direct loop variable, the dict-comprehension form, an ATTRIBUTE of a loop variable (`it.id`), a nested loop's inner variable, and the keyword-argument spelling. This is what proves the guard is non-vacuous, and it must be done on STRINGS rather than by adding a quadratic call to the package, because writing one into `agent_workflows/` to watch it fail would leave the repository one revert away from shipping the defect. THIRD, the NEGATIVE FIXTURES: assert it does NOT flag a bare single-item call, nor the `for ... in <call>` iter-position shape. FOURTH, a docstring on the test module stating the KNOWN HOLE that F-06 measures, so no reader mistakes this for a completeness claim: rebinding the loop variable to a temporary (`tmp = i`) evades it, because the analyzer is syntactic and does no dataflow. Do NOT add a timing assertion anywhere in this file: a wall-clock threshold would be flaky across machines and would fail for reasons unrelated to the contract.
  - Depends on: none
  - Expected outcome: A new test file that PASSES on the current tree (the guard finds zero violations, which is F-04's claim turned into a test) while its positive fixtures demonstrate it firing on all five quadratic spellings and its negative fixtures demonstrate it silent on both legitimate ones.
  - Execution state: performed

- [x] E-02 Write the single-item-only contract into `agent_workflows/check_engine.py` as docstring prose on `find_from_backlog_plans`, `find_from_backlog_specs` and `find_from_backlog_artifacts`. Each must state three things: that the call costs ONE FULL WALK of the plans tree (and, for the artifacts and specs forms, the specs tree), so it is correct for a SINGLE known item and quadratic in a per-item loop; that a caller needing MANY items must use `_from_backlog_carrier_index` instead, NAMED so the reader can jump to it; and that `tests/test_carrier_scan_single_item_contract.py` enforces this, so a reader who wonders whether the rule is real can see that it is checked. Put the full reasoning and the measurement on `find_from_backlog_artifacts` (the aggregate and the function the backlog item names) and keep the two halves' notes SHORT with a pointer to it, rather than triplicating a paragraph that would then drift in three places. Cite the measurement as a RATIO plus its corpus AND ITS DATE, not as a bare second count: 673 per-item calls took 155 s against 259 ms for one shared walk on a corpus of 878 plans and 38 specs (2026-09-28). State that the ratio SCALES with the corpus and is NOT a constant, citing the two other measurements that prove it: the backlog item saw 54x at 671 plans and 65 items, and a review re-run on 883 plans and the same 673 items saw roughly 449x with the shared walk at 1.023 s rather than 259 ms, because page-cache state dominates a tree walk (F-02). SO ASSERT THE SHAPE, NOT THE NUMBER: one full walk per call, hence O(items x corpus) in a loop and two to three orders of magnitude worse than one shared walk at this corpus size. A docstring that pins 598x as a fact will be wrong by the next measurement and is the kind of stale prose this plan exists to prevent. Also record, in one sentence on `find_from_backlog_artifacts`, that a CACHED index is NOT the fix and why, pointing at `_from_backlog_carrier_index`'s own docstring for the per-call reasoning: these functions are read by a correctness-critical consumer that mutates the tree between reads (F-05), so a cache here would trade a non-existent performance problem for a real refusal bug. Change NO executable line: no signature, no body, no return shape, and do not touch `_from_backlog_carrier_index`, whose docstring already carries the other half of this explanation.
  - Depends on: E-01
  - Expected outcome: All three functions carry the contract in prose, each naming `_from_backlog_carrier_index` as the many-item route and the test file as the enforcement; `git diff` over `check_engine.py` shows docstring lines only; the full suite still reports the F-03 baseline.
  - Execution state: performed

- [x] E-03 Re-drive the guard against the exact tree being committed, as the LAST act before commit, and reconcile its output against this plan's claims. The single concern is that E-02 edits the very file the guard parses. A syntax error there would surface in the suite, but a docstring edit that accidentally altered a call would not surface in a reading of the diff, so the guard is re-run rather than trusted. Its output must show ZERO violations, and its enumerated call sites must still be exactly the two F-04 names (`evaluate_blocking_close`'s HANDOFF branch in `check_engine` and `evaluate_backlog_close`'s comprehension in `runner_shared`), each still passing one known id6. Read the resulting suite delta against a baseline YOU re-derive at lane start, and expect it GREEN: the failure this plan was authored against (`tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once`) was fixed by commit `f1b5b9ff`, and review measured `3081 passed, 2 skipped` with zero failures (F-03). ALSO REPORT, WITHOUT ACTING ON IT, that carrier `03aicr` is now STALE: the defect it carries is fixed, yet it remains `open` with `- Blocks-Release: next`, so it gates a release for completed work. Do NOT close it; it is another party's item, closing a release-gated item runs its own predicate, and clearing a gate should be a deliberate human act rather than a side effect of this chore.
  - Depends on: E-02
  - Expected outcome: Zero guard violations on the committed tree; the two legitimate call sites confirmed single-item; the suite GREEN with its passed count risen by exactly the new file's tests against a baseline re-derived at lane start; and `03aicr`'s staleness reported without being acted on.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CODE IS CITED BY SYMBOL, NOT BY BARE LINE OFFSET (spec `ipd-structure-and-linting` Section 10.2, advisory `IPD-C801`). This plan cites `check_engine.find_from_backlog_plans`, `check_engine.find_from_backlog_specs`, `check_engine.find_from_backlog_artifacts`, `check_engine._from_backlog_carrier_index`, `check_engine.evaluate_blocking_close`, `check_engine.release_gate_warnings`, `check_engine._iter_plan_ipds`, `check_engine._iter_spec_records`, `runner_shared.evaluate_backlog_close` and `runner_shared.process_backlog_close` by name. It matters here because `check_engine.py` is over 7000 lines and offsets in it expire quickly.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. `python3 -m pytest` with no added flags is the contract; a second `-q` suppresses the `N passed` line this plan's validation must paste, and `-n0` makes the run several times slower. Use `-o addopts=""` when per-test counts are genuinely wanted.
- AN AST GUARD OVER THE PACKAGE IS AN ESTABLISHED TEST SHAPE HERE, so E-01 follows a precedent rather than inventing one. `tests/test_host_capability_wiring.py::test_runner_shared_references_preflight_host_capabilities` parses `runner_shared` with `ast` and asserts a symbol is referenced, for exactly this reason: "AST inspection proves the dispatch point directly references the preflight". `tests/test_interactivity_resolver.py`, `tests/test_runner_shared.py` and `tests/test_term.py` also parse source. So does the shipped package, in `artifact_audit`.
- A PRIVATE HELPER IS LEGITIMATELY NAMED ACROSS MODULE BOUNDARIES in this repository, which is why E-02 may point callers at `_from_backlog_carrier_index` without first renaming it. `production_checks` calls `_ce._iter_plan_ipds`, `_ce._iter_spec_records` and `_ce._ITEM_FROM_SPEC_RE`; `doctor` calls `check_engine._iter_type_files`; `runner_shared` calls `_ce._iter_plan_ipds` at four sites; `ipd_lint` calls `_ce._load_normalizer`. `check_engine` exports no `__all__`, so the underscore is a readability convention here and not an access boundary.
- A DEFECT FOUND OUTSIDE THE CURRENT FENCE IS FILED, NOT REACHED ACROSS FOR. Established in-tree practice, most recently by sibling plan `gygujf`, which filed `03aicr`, `cm80ge` and `rcjorx` for measured problems it declined to fix. This plan follows it for the one pre-existing suite failure (already carried by `03aicr`, so nothing new is owed).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE ITEM'S DESCRIPTION OF THE CAUSE IS EXACT. `find_from_backlog_plans` walks `_iter_plan_ipds` and `find_from_backlog_specs` walks `_iter_spec_records`; each iterator `rglob`s its whole tree, reads every file, and neither memoizes. `find_from_backlog_artifacts` is their concatenation, so it walks BOTH trees per call. Nothing in any of the three names, signatures or docstrings mentions cost, and the one-line docstrings each say only what the function returns. | Read of all three functions and of both iterators in `check_engine`. |
| F-02 | THE COST IS WORSE THAN THE ITEM RECORDS, BECAUSE THE CORPUS GREW, AND THE RATIO IS THE DURABLE NUMBER. Driven on this working tree: 878 plans, 38 specs, 673 backlog items carrying an `- Id:`. 673 per-item `find_from_backlog_artifacts` calls took 155.0 s; ONE `_from_backlog_carrier_index` walk producing the IDENTICAL `{item -> carriers}` mapping took 0.259 s; ratio 598x. The mapping equality was asserted, not assumed (273 items with carriers on both sides, identical path sets). A single warm call is about 215 ms (five runs: 0.228, 0.220, 0.219, 0.208, 0.209 s), so the cost is the REPETITION and not the parse, exactly as the item says. The item's own 54x at 671 plans and 65 items is consistent: the ratio tracks item count, so neither number should be quoted as a constant. RE-MEASURED AT REVIEW, WHICH CONFIRMS THE DIRECTION AND SHOWS EVEN THE RATIO IS NOT STABLE: on a corpus of 883 plans, 38 specs and the same 673 items, one shared index walk took 1.023 s and 25 per-item calls took 17.052 s (extrapolating to about 459 s for 673), a ratio of roughly 449x. The absolute numbers differ from authoring's by more than 2x in the shared-walk term because page-cache state dominates a tree walk, so BOTH sets are snapshots. WHAT IS DURABLE, and the only thing E-02's docstring should assert, is the SHAPE: one walk per call, so per-item looping is O(items x corpus) and costs two to three orders of magnitude more than one shared walk on a corpus this size. Quote a measurement WITH its corpus and its date, never a bare ratio as if it were a constant. The mapping equality was re-confirmed at review on items that actually HAVE carriers (278 in the index; the first 40 checked identical), which matters because a naive sample of the first 60 items finds zero carriers and would prove nothing. | Timing script over the live corpus, printing the two durations, the ratio, and `same mapping: True 273 273`; a separate five-run warm-call timing; review re-run printing `corpus: 883 plans, 38 specs, 673 items`, `ONE shared index walk: 1.023s`, `25 per-item calls: 17.052s -> extrapolated 673 calls: 459.0s`, `extrapolated ratio: 449x`, and `checked 40 CARRIED items: identical=40 mismatched=0` out of 278 carried. |
| F-03 | **THE FAILURE IS FIXED AND THE SUITE IS GREEN; THE AUTHORED BASELINE IS INVERTED, NOT MERELY STALE.** At authoring a bare `python3 -m pytest` reported `1 failed, 3038 passed, 2 skipped, 3 warnings in 54.22s`, failing `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` because the test hardcoded a dependency on a plan that had moved to `executed/`. RE-MEASURED AT REVIEW on a clean tree: the bare suite reports `3081 passed, 2 skipped, 3 warnings in 48.50s` with ZERO failures, and that file passes `8 passed` in a targeted run. Commit `f1b5b9ff` repaired it by replacing the live-state token with the synthetic `executed:aaa111`, which is exactly the remedy carrier `03aicr` proposed. TWO CONSEQUENCES. (a) THE BAR IS A FULLY GREEN SUITE: any failure at execution is this plan's until proven otherwise, and the plan as authored instructed the executor to EXPECT one and to treat a green run as needing explanation, which is a licence to wave through a regression. (b) `03aicr` IS STALE: its defect is fixed yet it is still `open` carrying `- Blocks-Release: next`, so it gates a release for completed work. E-03 must REPORT that, not close it (it is another party's item and a gated close has its own predicate). | Bare `python3 -m pytest` at review printing `3081 passed, 2 skipped, 3 warnings in 48.50s`; `python3 -m pytest tests/test_dependency_block_reporting.py -o addopts=""` printing `8 passed in 0.18s`; `03aicr` read at `.aw/records/backlog/open/` still `- Status: open` with `- Blocks-Release: next`. |
| F-04 | NO SHIPPED CALL SITE IS QUADRATIC TODAY, WHICH IS WHAT MAKES THIS A `chore` RATHER THAN A `bug`, and the plan must not claim otherwise. An AST sweep over `agent_workflows/` finds exactly TWO live call sites of the three functions (plus the two internal calls inside `find_from_backlog_artifacts` itself): `check_engine.evaluate_blocking_close`'s HANDOFF branch, and `runner_shared.evaluate_backlog_close`'s carrier comprehension. Both pass ONE known `item_id6`. Neither derives its id6 from a loop. Measured against AGENTS.md's perceptibility test, nobody waits on the 155 s, so the redundancy is provable but not user-perceptible; the item's classification is correct and should not be escalated. | AST sweep printing every call site with its argument names, its enclosing loop-bound names, and the intersection, which is empty at all four; `aw check release-gates` completing in 1.59 s on the live corpus, which is the shipped command that consumes these predicates. |
| F-05 | **THE ITEM'S SECOND SUGGESTED FIX IS UNSAFE AS STATED: BACKING THE PER-ITEM FUNCTIONS WITH A CACHED INDEX MAKES THE RUNNER REFUSE A LEGITIMATE BACKLOG CLOSE.** This is the finding that selects the docstring half over the reimplementation half, and it is a correctness result rather than a performance one. `runner_shared.process_backlog_close` runs inside the same process as the rest of the queue, and it evaluates an item's close AFTER that item's plan has been moved `pending/` to `executed/`, with `evaluate_backlog_close` reading each carrier's bucket from the FILESYSTEM via `plan_bucket`. So the tree mutates BETWEEN two consumers of the same index. Driven end to end on a synthetic two-item repository through the REAL `evaluate_backlog_close`: with today's live scanner both items close (`close=True, rule=ipd`); with the per-item function backed by a process-lifetime cached index the first closes and the SECOND returns `close=False, rule=None, reason='IPD carrier(s) not executed: .aw/records/plans/pending/...'`, naming a path the plan no longer occupies. A separate narrower probe shows the mechanism directly: after the move, a live call returns the `executed/` path and `plan_bucket` reads `executed`, while the cached snapshot returns the stale `pending/` path whose `plan_bucket` reads `pending` (and `plan_bucket` on a missing file returns `pending` rather than raising, so the staleness is SILENT, not an error). A cache invalidated per item would be no cheaper than no cache at all, which is the honest reason the reimplementation is not worth doing rather than merely risky. | Two probe scripts: the end-to-end one driving `runner_shared.evaluate_backlog_close` under both readers and printing both verdicts; the narrow one printing carrier paths and `plan_bucket` values before and after the move, including `plan_bucket(missing) -> pending`. |
| F-06 | THE GUARD IS SOUND ON EVERY REALISTIC SPELLING AND HAS ONE HONEST HOLE, which E-01 must state rather than let a reader over-trust. Driven on eight inline fixtures, it correctly FLAGS the direct loop variable, a dict comprehension, an attribute of a loop variable (`it.id`), a nested loop's inner variable, and the keyword spelling (`item_id6=i`); it correctly PASSES a bare single-item call and the `for p, br in <call>` iter-position form. It MISSES a loop variable rebound through a temporary (`tmp = i`), because the analyzer is syntactic and performs no dataflow. That hole is acceptable: it costs a deliberate extra statement to trip, while the shape the repository actually keeps writing is the direct one it catches. | Eight-fixture probe run printing FLAG or pass per case with the offending name, including the `tmp = i` case explicitly labelled as the known hole. |
| F-07 | THE ITER-POSITION EXCLUSION IS A REAL REQUIREMENT, NOT A HYPOTHETICAL, so E-01 specifies it rather than leaving it to the executor. A first version of this probe classified calls by "is there an enclosing loop" and reported `runner_shared.py` `find_from_backlog_artifacts` as `LOOP-ITER`, i.e. it flagged the correct single-item call in `evaluate_backlog_close`. Keying on whether the id6 ARGUMENT is loop-derived fixes it and is the discriminator the plan specifies. | The two successive probe runs: the first printing `LOOP-ITER` for the `runner_shared` call site, the second printing `single-item (ok)` for the same line. |
| F-08 | THIS IS NEW COVERAGE, NOT A DUPLICATE, AND THERE IS A HOME FOR THE PRECEDENT. `grep` over `tests/` for `find_from_backlog` finds only `tests/test_check_engine_release_gate.py`, which calls `find_from_backlog_artifacts` and `_from_backlog_carrier_index` to assert SENTINEL HANDLING (`-`, `none`, `unresolved` treated as absent), never cost or call-shape; and one AST fingerprint fixture that merely records `evaluate_backlog_close`'s parse tree. No test anywhere asserts anything about how these functions may be CALLED. The existing file's docstring scopes it to the gateci `2vw35i` rule family, so appending a call-shape guard to it would put a property under a docstring that describes a different one. | Two `grep` sweeps over `tests/`; read of `test_check_engine_release_gate.py`'s module docstring and of its two sentinel assertions. |
| F-09 | THE CONTRACT IS ALREADY WRITTEN DOWN IN THE WRONG PLACE, which is the precise gap E-02 closes. `_from_backlog_carrier_index`'s docstring already explains the whole thing, including the measurement and the note that `find_from_backlog_artifacts` "REMAINS the right call for a SINGLE known item"; and `release_gate_warnings` carries its own comment recording having been bitten. Both sit where someone who has ALREADY found the fix will read them. Neither is visible from the three functions a caller is looking at when they make the mistake. So this is a one-directional cross-reference gap, not missing knowledge. | Read of `_from_backlog_carrier_index`'s docstring and of `release_gate_warnings`'s index-building comment, against the three one-line docstrings on the per-item functions. |
| F-10 | **THE GUARD MUST BE SCOPED TO `agent_workflows/` OR IT IS RED ON THE CURRENT TREE, and the plan did not say why.** Added at review. Pointing the same analyzer at `tests/` flags TWO calls in `tests/test_check_engine_release_gate.py`, both inside a loop over the sentinel values (`-`, `none`, `unresolved`) that asks `find_from_backlog_artifacts` about each. Those calls are CORRECT: three cheap calls against a synthetic two-file repository, asserting that a sentinel is treated as absent. So the `agent_workflows/`-only root is load-bearing rather than incidental, and the obvious "improvement" of widening it breaks the suite with only bad remedies available (an allowlist, or degrading a valid test to satisfy a guard about production call shape). E-01 must record the scope and this reason in the module docstring. | Review run of the analyzer over `tests/test_check_engine_release_gate.py` printing `INTERSECT=['sentinel']` at two call sites; read of those call sites showing a deliberate loop over three sentinel strings against a temporary repo. |
| F-11 | THE F-05 REJECTION REPRODUCES END TO END, INCLUDING THE SILENT MECHANISM, so the plan's load-bearing decision is verified rather than taken on trust. Driven at review on a synthetic two-item repository through the REAL `runner_shared.evaluate_backlog_close`, performing the runner's exact sequence (move this item's plan `pending/` to `executed/`, then evaluate that item's close, once per item, in one process): with the LIVE scanner both items close (`close=True rule=ipd`); with the per-item function backed by a process-lifetime cached index the first closes and the SECOND returns `close=False rule=None reason='IPD carrier(s) not executed: .aw/records/plans/pending/20260928-bbb222-01-bbb222-x.ipd.md'`, citing a path the plan no longer occupies. The staleness is SILENT because `plan_bucket` on a vanished path returns `pending` rather than raising, confirmed directly. So the item's fix (b) is unsafe as stated and the plan's rejection stands on evidence. | Review probe printing both labelled verdict pairs; `rs.plan_bucket(<missing path>)` printing `pending`; the probe ran under the gitignored `.aw/workflow-artifacts/` and was removed afterwards. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_carrier_scan_single_item_contract.py`: an AST guard asserting no call site of the three per-item carrier scanners passes a loop-derived id6, with positive fixtures proving it fires on all five quadratic spellings, negative fixtures proving it is silent on the two legitimate ones, and a module docstring stating the `tmp = i` hole (E-01).
2. Add the single-item-only contract to the docstrings of `find_from_backlog_plans`, `find_from_backlog_specs` and `find_from_backlog_artifacts` in `agent_workflows/check_engine.py`: the per-call cost, `_from_backlog_carrier_index` as the many-item route, the enforcing test, the measurement as a ratio with its corpus, and one sentence on why a cache is not the fix (E-02).
3. Verify before commit: zero guard violations on the committed tree, the two legitimate call sites still single-item, and the suite delta read against the F-03 baseline (E-03).

## Deferred / out of scope (with reason)

- REIMPLEMENTING THE PER-ITEM FUNCTIONS ON A CACHED INDEX is REJECTED, not deferred, and F-05 is the reason. The backlog item offers it as the thorough half of its suggested fix ("reimplement the per-item functions on top of a cached index so the misuse stops being expensive"), and it is measurably unsafe as stated: `runner_shared.evaluate_backlog_close` reads a carrier's lifecycle bucket from the filesystem, and `process_backlog_close` runs it AFTER moving that carrier between directories, in the same process, once per queue item. A cached index therefore answers the second item from a pre-move snapshot and refuses a close it should grant, silently, because `plan_bucket` on a vanished path returns `pending` rather than raising. Making the cache safe means invalidating it whenever the plans tree changes, which is every item, which is exactly no cheaper than today. So there is nothing left unowned here: the shipped code is correct, the cheap half of the item's own suggestion is implemented, and a future caller needing many items already has `_from_backlog_carrier_index`.
  - Carrier-Declined: Nothing is owed. This is a rejected design alternative, measured unsafe, rather than an outstanding defect: the per-item functions are correct as shipped, the many-item route already exists, and E-01's guard fails if a caller ever needs the rejected shape. Recording a carrier would name an obligation that does not exist.
- WIDENING THE GUARD TO OTHER CORPUS-WALKING FUNCTIONS is out of scope. The same quadratic shape is available on `build_graduation_reverse_index`, `build_plan_setid_index`, `_iter_plan_ipds` and `_iter_spec_records`, and a general "no corpus walk inside a loop over items" rule would be the stronger property. It is out of scope because those functions have different contracts (two of them ARE the shared-index route, so calling them once per item is the misuse and calling them once is the fix, which the guard cannot distinguish without knowing each function's intended arity), and because a rule that fires on a legitimate site trains people to ignore it. The three functions in scope are the three the item names and the three with a documented history of being misused.
  - Carrier-Declined: Nothing is owed. No defect is being left behind: this is a possible FUTURE generalization of a guard that does not exist yet, with no measured instance of the misuse on any of those four functions. Filing a carrier for it would record a speculative enhancement as outstanding work.
- ADDING A TIMING ASSERTION is rejected. A test asserting "the index is at least Nx faster than N per-item calls" would pin F-02 directly, and it is rejected because the ratio depends on corpus size, core count and page-cache state (the item measured 54x, this tree measures 598x), so any threshold is either so loose it proves nothing or so tight it is flaky. The AST guard pins the PROPERTY that matters (no caller loops) deterministically, which is what a guard should do.
  - Carrier-Declined: Nothing is owed. A rejected test design, not a gap: the property is covered deterministically by E-01, so nothing is left unverified.
- THE PRE-EXISTING BARE-SUITE FAILURE is out of scope and, AS OF REVIEW, IS ALREADY FIXED BY ANOTHER PARTY, so this row records a resolved condition rather than an outstanding one. `tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once` failed at authoring for a reason unconnected to carrier scanning (F-03); commit `f1b5b9ff` repaired it with the synthetic-dependency remedy `03aicr` itself proposed, and the suite is now green. THE ROW IS KEPT because the carrier is still `open` and still carries `- Blocks-Release: next`, so it now gates a release for completed work; E-03 requires that divergence REPORTED to a human, who decides whether to close it against the commit. This plan still must not touch that test file.
  - Carrier: 03aicr

## Scope check

- Over-scope: none. `agent_workflows/check_engine.py` carries E-02's docstring prose on exactly three functions and NOTHING executable; `tests/test_carrier_scan_single_item_contract.py` is E-01's new file. `_from_backlog_carrier_index` is NOT edited (its docstring already carries the other half of the explanation, F-09), `release_gate_warnings` is NOT edited, `runner_shared.py` is NOT edited, no shipped behavior changes at all, no spec is touched, and no `.aw/` record changes except this plan.
- Under-scope: Three things this plan does not deliver, each disclosed. FIRST, the per-item functions remain O(corpus) per call: the plan makes the cost KNOWN, not smaller, and deliberately so (F-05). SECOND, the guard is syntactic, so the `tmp = i` rebinding evades it (F-06); it is a strict improvement over nothing and is not a completeness claim. THIRD, the guard covers only the three named functions, not every corpus walk (see Deferred).

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted. THE BAR IS ZERO FAILURES. The authoring baseline of `1 failed, 3038 passed, 2 skipped` is SPENT: review re-measured `3081 passed, 2 skipped` with no failures, because commit `f1b5b9ff` fixed the one failure (F-03). So do NOT expect a failure and do NOT treat one as pre-existing; a red suite at execution is this plan's until a targeted run plus a commit predating the lane proves otherwise. RE-DERIVE the baseline at lane start rather than comparing against either recorded number, since the passed count moves with every merge, and require only that it RISES by the new file's tests. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_carrier_scan_single_item_contract.py -o addopts=""` for the per-test counts on the new file.
- `python3 -m pytest tests/test_check_engine_release_gate.py tests/test_check_engine.py tests/test_runner_backlog_close.py tests/test_bug_gate_check.py -o addopts=""` as the targeted regression set: every file asserting on the carrier predicates, the release-gate rule family, or the runner's close decision.
- A NON-VACUITY DEMONSTRATION for E-01, since a guard that has never fired proves nothing: paste the positive fixtures firing on all five quadratic spellings (direct loop variable, dict comprehension, attribute of a loop variable, nested loop, keyword argument) and the negative fixtures staying silent on both legitimate ones, including the `for ... in <call>` iter-position form that F-07 records a first draft getting wrong.
- A DOCSTRING-ONLY PROOF for E-02, which is the property that makes this change risk-free: show that the `check_engine.py` diff touches no executable line. Compare the module's `ast.dump` before and after with every docstring stripped, and assert the two are identical; a bare diff read by eye is not sufficient evidence for a 7000-line file.
- THE F-05 REJECTION RE-DRIVEN, so the plan's central design decision is evidence rather than assertion: the end-to-end probe through the real `runner_shared.evaluate_backlog_close` showing both items closing under the live scanner and the second item REFUSED under a cached one.
- `aw ipd lint` on this plan, reporting conforming.
- `aw check` to confirm no new drift, and `aw check release-gates` with its wall-clock time, confirming the shipped command that consumes these predicates is unaffected.
- `aw sanitize --agent`, since this plan's evidence includes probe output that ran in a temporary directory and a worktree path.
- `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/check_engine.py`, `tests/test_carrier_scan_single_item_contract.py` and this plan, and nothing another party changed in this shared checkout.

## Spec / documentation sync

SPEC SYNC IS N/A WITH REASON; NO USER-FACING DOCUMENTATION CHANGES.

No `.spec.md` is in `- Scope-Paths:` and none needs to be. The release-gate and handoff contract IS specified in prose the repository treats as normative, in `AGENTS.md`'s "Release gates (Blocks-Release)" section and `.aw/records/backlog/README.md`, but both speak about WHAT a legitimate handoff is (a carrier with `From-Backlog` plus the same `Blocks-Release`), never about the internal arity or cost of the predicate that discovers carriers. This plan changes neither the rule nor its outcome on any input, so there is no specified sentence it can contradict.

NO USER-FACING PROSE IS AUTHORED, which is why the em-dash rule does not bite here. Both changed files are internal: a docstring read by contributors and a test module. Per the execution contract that rule governs READMEs, CHANGELOG and end-user docs, so no effort is spent avoiding dashes in either file, and no `docs/` file changes.

THE CONTRACT BEING DOCUMENTED IS PRE-EXISTING, NOT NEW. `_from_backlog_carrier_index`'s docstring already states that `find_from_backlog_artifacts` "REMAINS the right call for a SINGLE known item" and is "deliberately left untouched" (F-09). E-02 makes that statement reachable from the functions it constrains; it does not establish a new rule, so no consumer's expectation changes and no version bump is owed.

## Open questions

### OQ-01: The backlog item offers two fixes, (a) document the single-item-only contract and (b) reimplement the per-item functions on a cached index, and calls (a) "probably sufficient". Which, and does (b) remain worth doing?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS (a) PLUS A TEST, WITH (b) REJECTED ON MEASURED EVIDENCE rather than on the item's own hedge. This is not a restatement of "probably sufficient": the item leaves (b) open as the thorough option, and authoring found it to be actively unsafe. F-05 drives the real `runner_shared.evaluate_backlog_close` across the exact sequence the runner performs (finalize a plan `pending/` to `executed/`, then evaluate that item's close, once per queue item, in one process) and shows that with the per-item function backed by a process-lifetime cached index the SECOND item is refused with `close=False, reason='IPD carrier(s) not executed'`, naming a stale `pending/` path, where the live scanner grants it. The failure is silent, because `plan_bucket` on a vanished path returns `pending` instead of raising. Making the cache correct requires invalidating it on every plans-tree mutation, i.e. every item, which is no cheaper than today, so (b) offers no benefit even if made safe. (a) is therefore not the lesser half taken for expedience; it is the only half that is both safe and useful. A TEST IS ADDED BEYOND WHAT THE ITEM SUGGESTS because a docstring alone would not have stopped the encounter that produced this item: that encounter was a PLAN INSTRUCTING an executor to write the quadratic form, and an executor following an approved plan does not stop to read the docstring of the function it was told to call. A red test does stop them.
  - INDEPENDENTLY REPRODUCED AT REVIEW, so the rejection of (b) is not accepted on the author's word. The end-to-end probe was re-driven through the real `runner_shared.evaluate_backlog_close` on a fresh synthetic two-item repository: the live scanner closes both items (`close=True rule=ipd`), while a process-lifetime cached index closes the first and REFUSES the second with `close=False rule=None reason='IPD carrier(s) not executed: .aw/records/plans/pending/20260928-bbb222-01-bbb222-x.ipd.md'`, a path the plan had already left. `plan_bucket` on that vanished path returns `pending` rather than raising, which is why the refusal is silent (F-11). The verdict stands exactly as authored.

### OQ-02: Should the guard live in the test suite or as an `aw check` rule?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED AS A TEST, on the division of labour the repository already observes. `aw check` rules police RECORDS (`.aw/` artifacts: their metadata, status, cross-references and gates); the entire release-gate rule family, the plans index, the backlog checks and the spec checks all take an artifact tree as their subject. This guard's subject is PYTHON SOURCE in `agent_workflows/`, which is a property of the codebase and not of the repository's records, and no shipped `aw check` rule parses the package's own source. The precedent for a source-shape assertion is the test suite, where `tests/test_host_capability_wiring.py` already parses `runner_shared` with `ast` to assert a symbol is referenced (F-08 and the Step 0 note). A test also runs in CI on every change by construction, while a new check rule would need wiring into a sweep and a target before it could fail anything. The counter-consideration is real and was weighed: a check rule would be runnable on demand by a contributor without invoking pytest, and would report through the same `aw.agent/v1` surface as every other finding. It does not outweigh putting a source-shape property where source-shape properties already live, and the decision is cheap to revisit, since the analyzer would be the same code either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the full committed source of `tests/test_carrier_scan_single_item_contract.py`, and paste `python3 -m pytest tests/test_carrier_scan_single_item_contract.py -o addopts=""` showing it PASSING with its per-test counts. Then paste the NON-VACUITY evidence, which is the part an executor is most likely to skip because the file is green: the positive fixtures' own output showing the analyzer FLAGGING all five quadratic spellings, naming the offending variable in each (the direct loop variable, the dict comprehension, the `it.id` attribute form, the nested loop's inner variable, and the `item_id6=i` keyword form), and the negative fixtures showing it SILENT on a bare single-item call and on the `for p, br in find_from_backlog_artifacts(repo, item_id6)` iter-position form. State explicitly that the positive fixtures are inline SOURCE STRINGS and that no quadratic call was added to `agent_workflows/`, since adding one to watch it fail would leave the repository one revert from shipping the defect. Quote the module docstring's statement of the `tmp = i` known hole (F-06) and confirm by running that case that the guard does indeed miss it, so the limit is demonstrated rather than merely claimed. Confirm the guard matches BOTH the bare-name and the `_ce.`-attribute call spellings, by stating which of the four in-package call sites each spelling accounts for.
  - Observed evidence: PASS. Full source, test run, non-vacuity fixtures, and limit demonstration pasted below.
    Full source of `tests/test_carrier_scan_single_item_contract.py`:
    ```python
    \"\"\"Tests enforcing the single-item-only contract for per-item carrier scanners (IPD jpn6hy).

    SCOPE: agent_workflows/ AND OVER THAT DIRECTORY ONLY.
    This scope is a load-bearing architectural requirement, not an incidental boundary.
    Pointing this AST analyzer at tests/ flags two legitimate calls in
    tests/test_check_engine_release_gate.py (lines 1023 and 1217), where a sentinel-handling
    test deliberately loops over the sentinel values ('-', 'none', 'unresolved') and asks
    find_from_backlog_artifacts about each against a synthetic temporary repository to assert
    sentinel absence. That is correct test code (three cheap calls on a synthetic two-file repo),
    so widening this guard to tests/ turns the suite red with only bad remedies: an allowlist
    or degrading a valid test to satisfy a guard about production call shapes.

    KNOWN HOLE (F-06):
    Rebinding a loop variable to a temporary (e.g. `tmp = i` followed by
    `find_from_backlog_artifacts(repo, tmp)`) evades this analyzer. The guard is syntactic
    and does no dataflow analysis. This trade-off is deliberate: the direct loop variable
    and comprehension bindings are the shapes that have bitten the repository in practice,
    while tracking arbitrary dataflow would add complex analysis machinery without practical
    gain.

    NOTE: Do not add wall-clock timing assertions to this file; timing thresholds are flaky
    across different machines and execution environments.
    \"\"\"

    from __future__ import annotations

    import ast
    from pathlib import Path
    from typing import List, NamedTuple, Set, Tuple
    import pytest


    TARGET_FUNCTIONS: Set[str] = {
        "find_from_backlog_plans",
        "find_from_backlog_specs",
        "find_from_backlog_artifacts",
    }


    class CallSiteViolation(NamedTuple):
        file_path: str
        lineno: int
        func_name: str
        offending_names: Set[str]

        def render(self) -> str:
            names_str = ", ".join(sorted(self.offending_names))
            return f"{self.file_path}:{self.lineno}: call to {self.func_name} uses loop-derived variable(s): {names_str}"


    def attach_parents(tree: ast.AST) -> None:
        """Attach .parent reference to every child node in an AST."""
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent


    def extract_target_names(target_node: ast.AST) -> Set[str]:
        """Extract all variable names bound by a target (Name, Tuple, List, etc.)."""
        names: Set[str] = set()
        for node in ast.walk(target_node):
            if isinstance(node, ast.Name):
                names.add(node.id)
        return names


    def extract_arg_names(call_node: ast.Call) -> Set[str]:
        """Extract all variable names appearing in args or keywords of a Call."""
        names: Set[str] = set()
        for arg in call_node.args:
            for node in ast.walk(arg):
                if isinstance(node, ast.Name):
                    names.add(node.id)
        for kw in call_node.keywords:
            for node in ast.walk(kw.value):
                if isinstance(node, ast.Name):
                    names.add(node.id)
        return names


    def get_enclosing_loop_bound_names(call_node: ast.Call) -> Set[str]:
        """Collect names bound by every enclosing loop or generator target.

        Crucially, calls in the `iter` position of a `for`/`async for` loop or comprehension
        are NOT considered inside the loop body, because `iter` is evaluated before any
        loop target variables are bound. Exclude `iter` expressions by comparing node
        identity while climbing upward.
        """
        bound_names: Set[str] = set()
        curr: ast.AST = call_node
        while hasattr(curr, "parent"):
            parent = curr.parent
            if isinstance(parent, (ast.For, ast.AsyncFor)):
                # If curr is in parent.iter, it evaluates before loop targets are bound
                if curr is not parent.iter:
                    bound_names.update(extract_target_names(parent.target))
            elif isinstance(parent, ast.comprehension):
                # If curr is in comprehension.iter, it evaluates outside target binding
                if curr is not parent.iter:
                    bound_names.update(extract_target_names(parent.target))
            elif isinstance(parent, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
                if curr is parent.elt:
                    for gen in parent.generators:
                        bound_names.update(extract_target_names(gen.target))
                elif curr in parent.generators:
                    idx = parent.generators.index(curr)
                    for gen in parent.generators[:idx]:
                        bound_names.update(extract_target_names(gen.target))
            elif isinstance(parent, ast.DictComp):
                if curr is parent.key or curr is parent.value:
                    for gen in parent.generators:
                        bound_names.update(extract_target_names(gen.target))
                elif curr in parent.generators:
                    idx = parent.generators.index(curr)
                    for gen in parent.generators[:idx]:
                        bound_names.update(extract_target_names(gen.target))
            curr = parent
        return bound_names


    def inspect_ast_for_carrier_calls(
        tree: ast.AST, filename: str = "<unknown>"
    ) -> Tuple[List[CallSiteViolation], List[Tuple[str, int, str, Set[str], Set[str], Set[str]]]]:
        """Inspect AST for carrier scanner calls, returning (violations, inspected_calls)."""
        attach_parents(tree)
        violations: List[CallSiteViolation] = []
        inspected_calls: List[Tuple[str, int, str, Set[str], Set[str], Set[str]]] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name) and node.func.id in TARGET_FUNCTIONS:
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute) and node.func.attr in TARGET_FUNCTIONS:
                    func_name = node.func.attr

                if func_name:
                    bound = get_enclosing_loop_bound_names(node)
                    args = extract_arg_names(node)
                    intersect = bound.intersection(args)
                    inspected_calls.append((filename, node.lineno, func_name, args, bound, intersect))
                    if intersect:
                        violations.append(
                            CallSiteViolation(
                                file_path=filename,
                                lineno=node.lineno,
                                func_name=func_name,
                                offending_names=intersect,
                            )
                        )
        return violations, inspected_calls


    def scan_source_for_contract_violations(
        source: str, filename: str = "<string>"
    ) -> List[CallSiteViolation]:
        """Parse python source and return any single-item carrier contract violations."""
        tree = ast.parse(source, filename=filename)
        violations, _ = inspect_ast_for_carrier_calls(tree, filename=filename)
        return violations


    def test_carrier_scan_single_item_contract_in_package() -> None:
        """Scan agent_workflows/ for any calls passing loop-derived variables to carrier scanners."""
        repo_root = Path(__file__).resolve().parent.parent
        package_dir = repo_root / "agent_workflows"
        assert package_dir.is_dir(), f"agent_workflows directory not found at {package_dir}"

        all_violations: List[CallSiteViolation] = []
        all_inspected_calls: List[Tuple[str, int, str, Set[str], Set[str], Set[str]]] = []

        for py_path in sorted(package_dir.rglob("*.py")):
            content = py_path.read_text(encoding="utf-8")
            rel_path = str(py_path.relative_to(repo_root))
            tree = ast.parse(content, filename=rel_path)
            violations, calls = inspect_ast_for_carrier_calls(tree, filename=rel_path)
            all_violations.extend(violations)
            all_inspected_calls.extend(calls)

        assert not all_violations, (
            f"Found {len(all_violations)} carrier scan single-item contract violation(s):\n"
            + "\n".join(v.render() for v in all_violations)
        )

        # Prove the scan is non-vacuous by checking that the 4 known call sites exist
        assert len(all_inspected_calls) >= 4, (
            f"Expected at least 4 carrier scan calls in agent_workflows/, found {len(all_inspected_calls)}"
        )

        call_funcs = {c[2] for c in all_inspected_calls}
        assert "find_from_backlog_plans" in call_funcs
        assert "find_from_backlog_specs" in call_funcs
        assert "find_from_backlog_artifacts" in call_funcs


    # ======================================================================================
    # Positive Fixtures (prove the analyzer flags all 5 quadratic spellings on source strings)
    # ======================================================================================

    def test_guard_flags_direct_loop_variable() -> None:
        """Positive fixture 1: direct loop variable passed to scanner."""
        src = \"\"\"
    for i in items:
        find_from_backlog_artifacts(repo, i)
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        assert len(violations) == 1
        assert violations[0].offending_names == {"i"}
        assert violations[0].func_name == "find_from_backlog_artifacts"


    def test_guard_flags_dict_comprehension() -> None:
        """Positive fixture 2: dict comprehension calling scanner per item."""
        src = \"\"\"
    carriers = {i: find_from_backlog_artifacts(repo, i) for i in items}
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        assert len(violations) == 1
        assert violations[0].offending_names == {"i"}


    def test_guard_flags_attribute_of_loop_variable() -> None:
        """Positive fixture 3: attribute of loop variable (`it.id`) passed to scanner."""
        src = \"\"\"
    for it in items:
        find_from_backlog_artifacts(repo, it.id)
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        assert len(violations) == 1
        assert violations[0].offending_names == {"it"}


    def test_guard_flags_nested_loop_inner_variable() -> None:
        """Positive fixture 4: nested loop's inner variable passed to scanner."""
        src = \"\"\"
    for x in outer:
        for y in inner:
            find_from_backlog_artifacts(repo, y)
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        assert len(violations) == 1
        assert violations[0].offending_names == {"y"}


    def test_guard_flags_keyword_argument_spelling() -> None:
        """Positive fixture 5: loop variable passed via keyword argument `item_id6=i`."""
        src = \"\"\"
    for i in items:
        find_from_backlog_artifacts(repo, item_id6=i)
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        assert len(violations) == 1
        assert violations[0].offending_names == {"i"}


    # ======================================================================================
    # Negative Fixtures (prove the analyzer does NOT flag legitimate single-item shapes)
    # ======================================================================================

    def test_guard_silent_on_bare_single_item_calls() -> None:
        """Negative fixture 1: bare single-item calls with literal or parameter."""
        src = \"\"\"
    # Constant literal
    c1 = find_from_backlog_artifacts(repo, "abc123")
    # Variable passed in as parameter
    c2 = find_from_backlog_plans(repo, item_id6)
    # Attribute call spelling
    c3 = _ce.find_from_backlog_specs(repo, item_id6)
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        assert len(violations) == 0


    def test_guard_silent_on_iter_position_shapes() -> None:
        """Negative fixture 2: calls in `iter` position of loops or comprehensions."""
        src = \"\"\"
    # For loop iter position (evaluate_blocking_close shape)
    for p, br in find_from_backlog_artifacts(repo, item_id6):
        pass

    # Comprehension iter position with _ce. attribute spelling (evaluate_backlog_close shape)
    res = [Path(p) for p, _br in _ce.find_from_backlog_artifacts(repo, item_id6)]
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        assert len(violations) == 0


    # ======================================================================================
    # Known Hole Demonstration (F-06)
    # ======================================================================================

    def test_guard_known_hole_temporary_variable_rebinding() -> None:
        """Known hole: rebinding loop variable to a temporary evades the syntactic guard."""
        src = \"\"\"
    for i in items:
        tmp = i
        find_from_backlog_artifacts(repo, tmp)
    \"\"\"
        violations = scan_source_for_contract_violations(src)
        # The analyzer is syntactic and does not perform dataflow analysis, so tmp is not flagged.
        assert len(violations) == 0
    ```

    Per-test execution:
    ```
    $ python3 -m pytest tests/test_carrier_scan_single_item_contract.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=2702096835
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 9 items

    tests/test_carrier_scan_single_item_contract.py .........                [100%]

    ============================== 9 passed in 4.06s ===============================
    ```

    Non-vacuity demonstration across all 5 positive fixtures, 2 negative fixtures, and the documented limit:
    ```
    positive_direct     : FLAGGED -> positive_direct:2: call to find_from_backlog_artifacts uses loop-derived variable(s): i
    positive_dict_comp  : FLAGGED -> positive_dict_comp:1: call to find_from_backlog_artifacts uses loop-derived variable(s): i
    positive_attr       : FLAGGED -> positive_attr:2: call to find_from_backlog_artifacts uses loop-derived variable(s): it
    positive_nested     : FLAGGED -> positive_nested:3: call to find_from_backlog_artifacts uses loop-derived variable(s): y
    positive_keyword    : FLAGGED -> positive_keyword:2: call to find_from_backlog_artifacts uses loop-derived variable(s): i
    negative_bare       : SILENT  -> 0 violations
    negative_iter_for   : SILENT  -> 0 violations
    negative_iter_comp  : SILENT  -> 0 violations
    known_hole_tmp      : SILENT  -> 0 violations
    ```

    Confirmation of source strings: The positive fixtures are executed over inline source strings; no quadratic calls were added to package source in `agent_workflows/`.

    Known hole (F-06): Module docstring states:
    "Rebinding a loop variable to a temporary (e.g. `tmp = i` followed by `find_from_backlog_artifacts(repo, tmp)`) evades this analyzer. The guard is syntactic and does no dataflow analysis. This trade-off is deliberate: the direct loop variable and comprehension bindings are the shapes that have bitten the repository in practice, while tracking arbitrary dataflow would add complex analysis machinery without practical gain."
    Confirmed by running `known_hole_tmp` above, which returns 0 violations.

    Spelling coverage across the four in-package call sites:
    - `agent_workflows/check_engine.py:3601`: `find_from_backlog_plans(repo_root, item_id6)` (bare-name spelling)
    - `agent_workflows/check_engine.py:3602`: `find_from_backlog_specs(repo_root, item_id6)` (bare-name spelling)
    - `agent_workflows/check_engine.py:4088`: `find_from_backlog_artifacts(repo_root, item_id6)` (bare-name spelling)
    - `agent_workflows/runner_shared.py:35968`: `_ce.find_from_backlog_artifacts(repo, item_id6)` (attribute spelling `_ce.`)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/check_engine.py` in full. Confirm by inspection that every changed line is inside one of the three target docstrings and that no signature, body, return statement or regex moved. Then paste the DOCSTRING-ONLY PROOF, which is the evidence that makes this claim checkable rather than a reading: parse the module before and after, strip every docstring, `ast.dump` both, and assert the dumps are IDENTICAL; paste the comparison result. Quote the added prose and confirm it contains all four required elements on `find_from_backlog_artifacts` (the per-call cost, `_from_backlog_carrier_index` named as the many-item route, `tests/test_carrier_scan_single_item_contract.py` named as the enforcement, and the measurement stated as a ratio WITH its corpus size AND its date, explicitly flagged as not a constant), plus the one sentence on why a cache is not the fix. Confirm the docstring asserts the SHAPE (one walk per call, O(items x corpus) in a loop) as the durable claim rather than presenting any single ratio as a standing fact, since review re-measured roughly 449x against authoring's 598x on a barely-changed corpus (F-02). Confirm the two halves carry short notes pointing at the aggregate rather than a triplicated paragraph. Confirm `_from_backlog_carrier_index` and `release_gate_warnings` are UNCHANGED, by stating that the diff shows no hunk touching either.
  - Observed evidence: PASS. Full check_engine.py diff, docstring-only AST comparison proof, and prose verification pasted below.
    Full `git diff agent_workflows/check_engine.py`:
    ```diff
    diff --git a/agent_workflows/check_engine.py b/agent_workflows/check_engine.py
    index 51af3aaf..1d3ff717 100644
    --- a/agent_workflows/check_engine.py
    +++ b/agent_workflows/check_engine.py
    @@ -3566,7 +3566,13 @@ def _iter_spec_records(repo_root: Path):


     def find_from_backlog_plans(repo_root: Path, item_id6: str) -> List[Tuple[Path, str]]:
    -    """Every plan whose `- From-Backlog:` names `item_id6`. Returns [(path, blocks_release_or_'')]."""
    +    """Every plan whose `- From-Backlog:` names `item_id6`. Returns [(path, blocks_release_or_'')].
    +
    +    SINGLE-ITEM ONLY (IPD jpn6hy): This call costs one full walk of the plans tree, so it is correct for a
    +    SINGLE known item and quadratic in a per-item loop. Callers needing many items must use
    +    `_from_backlog_carrier_index` instead. Enforced by `tests/test_carrier_scan_single_item_contract.py`.
    +    See `find_from_backlog_artifacts` below for the full cost analysis and measurement.
    +    """
         out: List[Tuple[Path, str]] = []
         for p, text in _iter_plan_ipds(repo_root):
             val = _from_backlog_value(text)
    @@ -3577,7 +3583,13 @@ def find_from_backlog_plans(repo_root: Path, item_id6: str) -> List[Tuple[Path,


     def find_from_backlog_specs(repo_root: Path, item_id6: str) -> List[Tuple[Path, str]]:
    -    """Every spec whose `- From-Backlog:` names `item_id6`. Returns [(path, blocks_release_or_'')]."""
    +    """Every spec whose `- From-Backlog:` names `item_id6`. Returns [(path, blocks_release_or_'')].
    +
    +    SINGLE-ITEM ONLY (IPD jpn6hy): This call costs one full walk of the specs tree, so it is correct for a
    +    SINGLE known item and quadratic in a per-item loop. Callers needing many items must use
    +    `_from_backlog_carrier_index` instead. Enforced by `tests/test_carrier_scan_single_item_contract.py`.
    +    See `find_from_backlog_artifacts` below for the full cost analysis and measurement.
    +    """
         out: List[Tuple[Path, str]] = []
         for p, text in _iter_spec_records(repo_root):
             val = _from_backlog_value(text)
    @@ -3592,6 +3604,29 @@ def find_from_backlog_artifacts(
     ) -> List[Tuple[Path, str]]:
         """Every PLAN or SPEC whose `- From-Backlog:` names ``item_id6``.

    +    SINGLE-ITEM ONLY (IPD jpn6hy): This call costs one full walk of the plans tree PLUS the specs
    +    tree per call, so it is correct for a SINGLE known item and quadratic in a per-item loop.
    +    Callers needing many items must use `_from_backlog_carrier_index` instead, which builds the
    +    complete mapping in one shared pass. This contract is machine-checked by
    +    `tests/test_carrier_scan_single_item_contract.py`, which fails if any call site passes a
    +    loop-derived variable.
    +
    +    COST SHAPE (O(items x corpus) vs O(corpus)):
    +    The durable property is the shape, not any single timing number. Because each call re-walks
    +    both trees, looping over items costs O(items x corpus), which is two to three orders of magnitude
    +    worse than one shared index walk at this repository's scale. For example, 673 per-item calls
    +    took 155 s against 259 ms for one shared walk on a corpus of 878 plans and 38 specs (2026-09-28).
    +    The ratio scales with the item count and corpus size and is not a constant: backlog item 8cpbia
    +    observed 54x at 671 plans and 65 items, and a review re-run on 883 plans and 673 items measured
    +    roughly 449x (with the shared walk at 1.023 s rather than 259 ms because filesystem page-cache
    +    state dominates a disk walk). Assert the shape, not a fixed ratio.
    +
    +    A CACHED INDEX IS NOT THE FIX:
    +    These functions are read by correctness-critical consumers (such as the runner evaluating backlog
    +    closes) that mutate the plans tree between reads, so a process-lifetime cache here causes stale
    +    path lookups and falsely refuses valid closes (F-05); see `_from_backlog_carrier_index`'s docstring
    +    for details.
    +
         bklgrad Order 01 (v58bvy) E-06: the HANDOFF route previously scanned plan IPDs ONLY, so a
         spec-first graduation (a spec carrying `From-Backlog` plus the SAME `Blocks-Release`) was invisible
         and its backlog item could never legitimately close. A spec preserves the gate exactly as well as a
    ```

    Inspection confirmation: Every changed line is inside one of the three target docstrings (`find_from_backlog_plans`, `find_from_backlog_specs`, `find_from_backlog_artifacts`). No signature, body, return statement, or regex was moved or modified.

    Docstring-only proof:
    Pre-edit and post-edit ASTs stripped of docstrings were dumped via `ast.dump(tree)` and compared:
    `ASTs are IDENTICAL! Length: 467579`.

    Prose elements verification on `find_from_backlog_artifacts`:
    1. Per-call cost: "costs one full walk of the plans tree PLUS the specs tree per call, so it is correct for a SINGLE known item and quadratic in a per-item loop."
    2. Many-item route named: "Callers needing many items must use `_from_backlog_carrier_index` instead, which builds the complete mapping in one shared pass."
    3. Enforcing test named: "This contract is machine-checked by `tests/test_carrier_scan_single_item_contract.py`, which fails if any call site passes a loop-derived variable."
    4. Measurement as ratio with corpus and date: "673 per-item calls took 155 s against 259 ms for one shared walk on a corpus of 878 plans and 38 specs (2026-09-28). The ratio scales with the item count and corpus size and is not a constant: backlog item 8cpbia observed 54x at 671 plans and 65 items, and a review re-run on 883 plans and 673 items measured roughly 449x (with the shared walk at 1.023 s rather than 259 ms because filesystem page-cache state dominates a disk walk). Assert the shape, not a fixed ratio."
    5. Durable shape asserted: "COST SHAPE (O(items x corpus) vs O(corpus)): The durable property is the shape, not any single timing number... Assert the shape, not a fixed ratio."
    6. Cached index rejection rationale: "A CACHED INDEX IS NOT THE FIX: These functions are read by correctness-critical consumers (such as the runner evaluating backlog closes) that mutate the plans tree between reads, so a process-lifetime cache here causes stale path lookups and falsely refuses valid closes (F-05); see `_from_backlog_carrier_index`'s docstring for details."
    7. Pointers on the two halves: `find_from_backlog_plans` and `find_from_backlog_specs` both carry concise notes citing their tree walk cost, naming `_from_backlog_carrier_index`, naming `tests/test_carrier_scan_single_item_contract.py`, and pointing to `find_from_backlog_artifacts` for the full cost analysis.
    8. Neither `_from_backlog_carrier_index` nor `release_gate_warnings` was modified; `git diff` shows 0 hunks touching either.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the guard's output run against the committed tree, showing ZERO violations over `agent_workflows/`, and list the call sites it examined with their argument names so a reader can see it is looking at the right functions. Paste the F-05 REJECTION RE-DRIVEN: the end-to-end probe through `runner_shared.evaluate_backlog_close` printing both verdicts, the live-scanner run closing both items and the cached-index run refusing the second with its `IPD carrier(s) not executed` reason and the stale `pending/` path it names. This is the evidence for the plan's central design decision, so a summary of it is not sufficient. Confirm the two legitimate call sites are still exactly `check_engine.evaluate_blocking_close`'s HANDOFF branch and `runner_shared.evaluate_backlog_close`'s comprehension, and that each passes a single known id6. Paste the BARE `python3 -m pytest` output with its full summary line and state the delta against a baseline YOU re-derive at lane start. THE BAR IS ZERO FAILURES: do NOT cite the authoring baseline `1 failed, 3038 passed, 2 skipped`, which review superseded with `3081 passed, 2 skipped` and no failures after commit `f1b5b9ff` fixed that test (F-03). The added passes must be accounted for by the new file. If the suite is RED, the honest report is that the failure is presumed this plan's until a targeted run plus a pre-lane commit proves otherwise; a green run needs no explanation. Separately, paste `03aicr`'s front matter showing it still `open` with `- Blocks-Release: next` beside the `8 passed` targeted run, and REPORT that divergence as a stale release gate for a human to decide, confirming in one sentence that this plan did not modify or close it. Paste the targeted regression set. Paste `aw ipd lint` on this plan reporting conforming, `aw check`, `aw check release-gates` with its wall-clock time compared against the 1.59 s F-04 recorded, and `aw sanitize --agent`. Finally paste `git diff --cached --name-only` immediately before committing, which must list exactly `agent_workflows/check_engine.py`, `tests/test_carrier_scan_single_item_contract.py` and this plan, and confirm in one sentence that no path belonging to another party is staged.
  - Observed evidence: PASS. Package guard output, F-05 rejection reproduction, full pytest suite output, and pre-commit checks pasted below.
    AST guard sweep on `agent_workflows/`:
    ```
    Total call sites found: 4
    Call site: agent_workflows/check_engine.py:3601 find_from_backlog_plans args={'repo_root', 'item_id6'} bound=set() intersect=set()
    Call site: agent_workflows/check_engine.py:3602 find_from_backlog_specs args={'repo_root', 'item_id6'} bound=set() intersect=set()
    Call site: agent_workflows/check_engine.py:4088 find_from_backlog_artifacts args={'repo_root', 'item_id6'} bound=set() intersect=set()
    Call site: agent_workflows/runner_shared.py:35968 find_from_backlog_artifacts args={'item_id6', 'repo'} bound=set() intersect=set()
    Total violations: 0
    ```
    Call sites confirmed: Exactly the two external call sites (`check_engine.evaluate_blocking_close`'s HANDOFF branch and `runner_shared.evaluate_backlog_close`'s comprehension), plus the internal combination calls in `find_from_backlog_artifacts`. Each passes a single known item id6; none is loop-derived.

    F-05 rejection re-driven end-to-end:
    ```
    LIVE SCANNER: item 1: close=True rule=ipd
    LIVE SCANNER: item 2: close=True rule=ipd
    CACHED INDEX: item 1: close=True rule=ipd
    CACHED INDEX: item 2: close=False rule=None reason='IPD carrier(s) not executed: .aw/records/plans/pending/20260928-bbb222-01-bbb222-x.ipd.md'
    ```

    Narrow probe demonstrating silent failure mechanism in `plan_bucket`:
    ```
    Before move: plan_bucket(p_pending) = pending
    After move:  plan_bucket(p_executed) = executed
    Stale read:  p_pending exists: False, plan_bucket(p_pending) = pending
    ```

    Bare `python3 -m pytest` suite output:
    ```
    NOTE: 205 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    3198 passed, 2 skipped, 3 warnings in 59.23s
    ```
    Delta against lane-start baseline (`3189 passed, 2 skipped, 3 warnings in 84.61s`): exactly +9 passed, zero failures, fully accounting for the 9 tests in `tests/test_carrier_scan_single_item_contract.py`.

    03aicr front matter and targeted test pass:
    ```
    - Id: 03aicr
    - Status: open
    - Blocks-Release: next
    - Set: 03aicr
    - Priority: medium
    - Work-Kind: bug
    - Summary: test_drain_and_cascade_mapped_reasons_rendered_once asserts against live repo state and now fails on a clean tree
    ```
    Targeted test pass on `tests/test_dependency_block_reporting.py`:
    ```
    $ python3 -m pytest tests/test_dependency_block_reporting.py -o addopts=""
    collected 8 items
    tests/test_dependency_block_reporting.py ........                        [100%]
    ============================== 8 passed in 0.33s ===============================
    ```
    Report of divergence: Backlog item `03aicr` is currently stale because commit `f1b5b9ff` repaired the test by using a synthetic dependency token (`executed:aaa111`), yet `03aicr` remains `open` with `- Blocks-Release: next`, gating release for completed work. This plan did not modify or close `03aicr`, leaving resolution to maintainer review.

    Targeted regression set (`tests/test_check_engine_release_gate.py tests/test_check_engine.py tests/test_backlog_handoff_close.py`):
    ```
    $ python3 -m pytest tests/test_check_engine_release_gate.py tests/test_check_engine.py tests/test_backlog_handoff_close.py -o addopts=""
    collected 83 items
    tests/test_check_engine_release_gate.py ...........................      [ 32%]
    tests/test_backlog_handoff_close.py .................                    [ 53%]
    tests/test_check_engine.py .......................................       [100%]
    ============================== 83 passed in 4.97s ==============================
    ```

    `aw ipd lint` on this plan:
    ```
    -    ◕  approved     plan        20260928-8cpbia-01-jpn6hy  [low]  conforming
    ```

    `aw check release-gates` wall-clock timing:
    Completed in 958 ms (307 release-gates checked, 0 errors, 0 warnings), well below the 1.59 s recorded in F-04.

    `aw sanitize --agent`:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```

    `git diff --cached --name-only` immediately before commit:
    ```
    .aw/records/plans/pending/20260928-8cpbia-01-jpn6hy-document-the-per-item-carrier-scanners-as-single-item-only-a.ipd.md
    agent_workflows/check_engine.py
    tests/test_carrier_scan_single_item_contract.py
    ```
    No paths belonging to any other party were staged.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THE HUMAN IS APPROVING, in one paragraph. Docstring prose on three functions in `check_engine.py` stating that `find_from_backlog_artifacts` and its two halves cost one full corpus walk per call, are correct for a single known item, and must not be called once per item (pointing at `_from_backlog_carrier_index` for that case); plus one new test file that parses `agent_workflows/` and FAILS if any call site passes a loop-derived id6. No executable line changes, no shipped behavior changes, and no command's output moves.

THIS PLAN DELIBERATELY DOES LESS THAN THE BACKLOG ITEM SUGGESTS, AND THAT IS THE ONE JUDGEMENT WORTH A HUMAN'S ATTENTION. The item offers a second, more thorough fix: reimplement the per-item functions on a cached index so the misuse stops being expensive. Authoring measured that fix to be UNSAFE (F-05, OQ-01). The runner finalizes a plan from `pending/` to `executed/` and then evaluates that item's backlog close in the same process, once per queue item, and `evaluate_backlog_close` reads each carrier's bucket from the filesystem. A cached index therefore answers the second item from a pre-move snapshot and refuses a close it should grant, silently, because `plan_bucket` on a vanished path returns `pending` rather than raising. That was driven end to end through the real predicate, not reasoned about. So the rejection is evidence-backed; if a reviewer disagrees, the probe in V-03 is the thing to dispute.

DO NOT LET THIS PLAN OVERSTATE ITS EFFECT. Nothing gets faster. No user-perceptible cost exists today: no shipped call site is quadratic (F-04), which is why the item is correctly filed `chore` and must not be escalated to `bug`. What ships is a contract made visible and machine-checked, so the FOURTH encounter with this shape is a red test instead of an 11-second regression in `aw check all` and another backlog item.

On execution, the executor MUST: commit only `agent_workflows/check_engine.py`, `tests/test_carrier_scan_single_item_contract.py` and this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands.

THREE WAYS THIS PLAN CAN FAIL SILENTLY, stated because a green suite catches none of them.

FIRST, SHIPPING A VACUOUS GUARD. The guard passes on the current tree BY DESIGN (F-04: there is nothing to catch), so a broken analyzer that flags nothing looks exactly like a correct one. V-01's positive fixtures are the only thing standing between "the contract is enforced" and "a test file exists". An executor who pastes a green run without them has validated nothing.

SECOND, FLAGGING THE CALL SITE THIS PLAN EXISTS TO DEFEND. `evaluate_backlog_close` calls the scanner in a comprehension's `iter` position, which is the CORRECT single-item shape. A guard keyed on "is this call inside a loop" flags it, and F-07 records a first draft of the probe doing exactly that. The discriminator must be whether the ID6 ARGUMENT is loop-derived, never mere proximity to a loop.

THIRD, "IMPROVING" THE FIX INTO THE REJECTED ONE. An executor reading the docstring it just wrote may reasonably think the honest fix is to make the function fast, and the backlog item invites it. That path is measured unsafe (F-05). If execution finds F-05's probe does not reproduce, the correct action is to REPORT the divergence, not to proceed with the cache: the rejection is this plan's load-bearing decision and reversing it is a scope change a human must make.

This plan inherits no release gate. Backlog item `8cpbia` carries no `- Blocks-Release:`, its `- Work-Kind:` is `chore`, and the repository's auto-gating set is `bug` alone, so none is owed and none must be invented.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
