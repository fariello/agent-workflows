# IPD: Cut the statusline swept-input sweep to a pairwise covering array and give the exhaustive arm its own budget

- Date: 2026-10-02
- Kind: child
- Concern: `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs` renders a 7,776-row full cartesian product (31,104 renders) inside one test function and measures 68.16s against the 90s per-test hang guard in `conftest.py`, leaving 1.3x headroom. Under CPU contention it crosses the budget and the guard fails it, which is how it was observed red in two separate suite runs.
- Scope: Replace the full cartesian product with a deterministic in-repo pairwise (2-way) covering array that preserves every single-value and every value-pair, and move the exhaustive product into a separate `slow`-marked test carrying its own explicit `@pytest.mark.timeout`. No production module is touched.
- Scope-Paths: tests/test_statusline_behavior.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: 8sr0or
- Blocks-Release: next
- Set: 8sr0or
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: mat9bt

## Workflow history

- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `8sr0or`; premises measured at HEAD `1a96623c0` rather than assumed (full-suite duration profile, contention reproduction, pairwise detection-power mutation study, and a rejected renderer-optimization alternative all run and recorded in Findings).

## Goal

Make the statusline box-renderer invariant test finish in well under its hang-guard budget without weakening what it detects, by sweeping a pairwise covering array (18 rows, measured 0.078s) in the fast suite and relegating the exhaustive 7,776-row product to a `slow`-marked companion with an explicit timeout. The defect is a user-perceptible one in the sense this repository defines: a maintainer waiting on `python3 -m pytest` gets a RED suite from a test that asserts nothing wrong.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-establish the defect at the execution head

- [ ] E-01 Re-measure the test's in-suite duration and reproduce the guard firing, before changing any test code, so the plan's premises are demonstrated at the execution head rather than inherited from this document.
  - Depends on: none
  - Expected outcome: a `--durations` figure for the target nodeid from a bare suite run, and a run in which `conftest.TestHangTimeout` names that exact nodeid. Both pasted. If the duration has drifted far below the F-01 figure, STOP AND REPORT rather than proceeding: the remedy is sized to a measurement, and a measurement that no longer holds invalidates the sizing.
  - Execution state: pending

### Task group 2: Introduce the covering-array helper

- [ ] E-02 Add a module-level pairwise covering-array generator to `tests/test_statusline_behavior.py` that takes a list of value domains and returns rows covering every value of every dimension and every value-pair across every dimension pair.
  - Depends on: E-01
  - Expected outcome: a deterministic generator (same input, same rows, no RNG and no `random` seeding) that converges on this plan's nine domains. It must be seeded from a still-uncovered pair on each row rather than greedily filling every dimension from scratch, because the naive greedy form does NOT converge here (F-06 records the failure and the fix).
  - Execution state: pending

- [ ] E-03 Add a test that asserts the generator's own contract directly: every value of every dimension appears, every cross-dimension value-pair appears, and regenerating yields identical rows.
  - Depends on: E-02
  - Expected outcome: a test that would FAIL if the generator silently dropped a pair, so the reduction's central claim is itself guarded rather than trusted. This is the item that makes the whole reduction safe to review: without it, a future edit to the generator could quietly shrink coverage with no test objecting.
  - Execution state: pending

### Task group 3: Split the sweep into a fast pairwise arm and a slow exhaustive arm

- [ ] E-04 Rewrite `test_box_renderer_invariants_across_swept_inputs` to iterate the covering-array rows instead of `itertools.product`, keeping all four invariants and both styling and both unicode modes per row, and keeping the existing zero-width/newline fence on the swept `setid`/`id6` values.
  - Depends on: E-02, E-03
  - Expected outcome: the fast-suite test asserts the same four properties per row and no longer asserts the two absolute literals `7776` and `31104`, which are properties of the discarded enumeration strategy and not of the renderer. Assert the row count and the render count as a DERIVED relationship (renders equal rows times modes) rather than as new hand-written literals, so the next legitimate change to the domains does not require editing a magic number.
  - Execution state: pending

- [ ] E-05 Add the exhaustive full-cartesian sweep as a separate `@pytest.mark.slow` test carrying an explicit `@pytest.mark.timeout` sized from the E-01 measurement with headroom, asserting the identical four invariants over the complete 7,776-row product.
  - Depends on: E-04
  - Expected outcome: the exhaustive coverage still EXISTS and is still runnable (`make test-all`, `-m slow`, or the CI advisory slow step), so this plan reduces the fast suite's cost without deleting the coverage. The timeout must be explicit on this test and not left to the 90s default, because the default is exactly what it exceeds. Record in a comment WHY the budget is what it is, citing the measured serial duration, in the manner `tests/test_exit_contract_conformance.py` already does for its own 500s budget.
  - Execution state: pending

### Task group 4: Prove the reduction did not weaken detection

- [ ] E-06 Demonstrate by mutation that the pairwise arm still catches the defect classes the full product catches, and record honestly the class it does NOT catch.
  - Depends on: E-04
  - Expected outcome: a table of mutations, each applied to RENDERED OUTPUT (not to the shared `term.visible_width` measurement, which both the renderer and the assertion call, so patching it masks the defect; F-07 records this trap and the wasted first attempt), reporting for each whether the full product and the pairwise rows detect it. The deliberate inclusion of at least one 3-way-only mutation that pairwise MISSES is required, not optional: it is the honest statement of the tradeoff this plan makes, and it is the reason E-05 keeps the exhaustive arm alive.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Do not add `-n0` (several times slower here), a second `-q` (compounds to `-qq` and suppresses the `N passed` summary this plan requires pasted), or `-p no:randomly` (disables the order randomization). To see per-test counts from a narrowed run, clear the defaults with `-o addopts=""`.
- THE REPOSITORY ALREADY HAS A SANCTIONED REMEDY FOR A LEGITIMATELY SLOW TEST, and this plan uses it rather than inventing one. The guard's own rationale comment in `conftest.py` says "Raise the budget for a legitimately slow test with `@pytest.mark.timeout(<seconds>)`", and `tests/test_exit_contract_conformance.py` pairs `@pytest.mark.slow` with `@pytest.mark.timeout(500)`, documenting in its docstring that the marker is needed because "the hang guard ignores `@pytest.mark.slow`". `tests/test_json_surface_leak_posture.py` carries two `@pytest.mark.timeout(300)` tests. So both halves of E-05's remedy are established practice.
- THE `slow` MARKER IS A REAL ARM AND NOT A DELETION. `pyproject.toml` describes `slow` as "Deselected by default for a fast per-run suite; run them with `make test-all` / `-m ''`", the `Makefile` documents a full-suite target that clears the filter with `-m ""`, and `.github/workflows/tests.yml` runs a second "Run slow-marked tests (ADVISORY...)" step. Moving work to `slow` therefore moves it to a less-frequently-run arm, which is a real reduction in protection and is why E-04 keeps a fast-suite arm at all rather than simply marking the existing test `slow`.
- P16 (GUIDING_PRINCIPLES) bans code-pinning tests: no `inspect`/`ast`/regex reads of production source, no symbol censuses, no asserting that comment banners survive. Every test this plan touches or adds must assert rendered OUTPUT. E-03 is the one place a reader might suspect a structural pin, and it is not one: it asserts the generator's output rows, which are test data this plan authors, not production code structure.
- THE SWEEP'S ZERO-WIDTH FENCE IS LOAD-BEARING AND MUST SURVIVE. The executed plan `6tjq2j` that authored this test records at F-10 that a zero-width code point in `setid` makes the box NON-rectangular today (measured widths `127, 126, 127, 127`), because the column uses bare `len()` while `term.visible_width("\u200b")` is 0, and that approved plan `it6tpj` owns the fix. The sweep's value lists are deliberately free of zero-width and newline code points. Admitting one while reshaping the sweep would make the module red for someone else's defect.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE DEFECT IS REAL, IS THE SECOND-SLOWEST TEST IN THE SUITE, AND ITS HEADROOM IS 1.3x.** A bare suite run with `--durations=12` puts the target nodeid second at 68.16s against the 90s guard. That is the measurement that sizes this whole plan: a test at 76 percent of its budget is not a test that is occasionally unlucky, it is a test that fails whenever the machine is busy. | `python3 -m pytest --durations=12` at HEAD `1a96623c0`: `68.16s call tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`, listed under `82.98s` for `test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference` and above `47.82s` for `test_fields_flag_reach.py`. Run summary: `3 failed, 4624 passed, 2 skipped, 3 warnings in 284.07s`. |
| F-02 | **THE GUARD DOES NOT CONSULT THE `slow` MARKER, so `slow` ALONE WOULD NOT FIX THIS**, which is why E-05 requires an explicit `@pytest.mark.timeout` and not merely a marker. `conftest._test_timeout_seconds` resolves a `timeout` marker argument, then the `AW_TEST_TIMEOUT` environment variable, then falls back to `_DEFAULT_TEST_TIMEOUT`; `slow` appears nowhere in it. `tests/test_exit_contract_conformance.py` states this in its own docstring as the reason for its `timeout(500)`. | `conftest._test_timeout_seconds` reads `item.get_closest_marker("timeout")`, then `os.environ.get("AW_TEST_TIMEOUT", "")`, then returns `_DEFAULT_TEST_TIMEOUT = 90.0`. `tests/test_exit_contract_conformance.py` docstring: "ignores @pytest.mark.slow, an explicit @pytest.mark.timeout(500) is set, providing". |
| F-03 | **THE GUARD FIRES CORRECTLY, INCLUDING UNDER XDIST, so the remedy's mechanism is verified and not assumed.** A three-case probe confirms the default budget fires, a `timeout(n)` marker lowers it, and `timeout(0)` disables it, with identical behavior serially and under `-n 2`. This matters because the suite always runs under xdist, and a guard that only worked in the main process would make E-05's remedy inert. | Probe under `AW_TEST_TIMEOUT=3`, serial: `2 failed, 1 passed in 6.08s`, with `conftest.TestHangTimeout: TEST HANG GUARD: ...::test_default_budget_fires exceeded its 3s per-test budget` and `...::test_marker_lowers_budget exceeded its 2s per-test budget`, while `timeout(0)` passed. Under `-n 2`: `2 failed, 1 passed in 4.73s`, same two nodeids named. Probe file removed afterwards; `git status --short` empty. |
| F-04 | **A PAIRWISE COVERING ARRAY OVER THE NINE DOMAINS IS 18 ROWS, A 432x REDUCTION, AND RUNS IN 0.078s**, giving roughly 1,150x headroom under the 90s budget where the current test has 1.3x. The nine domains are `3*2*3*3*3*2*3*4*2 = 7776`; the array is generated deterministically in about 2.4ms. | Covering-array probe: `rows=18 generated in 2.4ms`, `pairwise coverage verified: True`, `full cartesian = 7776; renders full = 31104, renders pairwise = 72`, `reduction factor = 432.0x`, `deterministic on regeneration: True`. Full four-invariant check over the 18 rows: `pairwise rows=18 renders/calls=216 wall=0.078s`, `headroom under 90s budget: 1157x`. |
| F-05 | **PAIRWISE CATCHES EVERY 1-WAY AND 2-WAY DEFECT TESTED, SEVEN FOR SEVEN, INCLUDING A NON-DETERMINISTIC ONE.** This is the evidence that the reduction is not a coverage giveaway for the defect classes that actually occur in a column-padding renderer, where a cell is wrong because of what is IN it, not because of a nine-way conjunction. | Mutation study over rendered output, each row reporting full and pairwise: drop the 4th line `full=CAUGHT pairwise=CAUGHT`; widen line 0 when setid set `CAUGHT/CAUGHT`; widen line 1 when progress is N/N `CAUGHT/CAUGHT`; widen line 2 when activity is free text `CAUGHT/CAUGHT`; widen line 3 when tracker populated AND ascii `CAUGHT/CAUGHT`; widen line 0 when setid long AND stall large `CAUGHT/CAUGHT`; non-deterministic 3-way counter widening line 0 `CAUGHT/CAUGHT`. Unmutated baseline passes both arms. |
| F-06 | **PAIRWISE PROVABLY MISSES A 3-WAY-ONLY DEFECT, AND THIS PLAN STATES THAT RATHER THAN HIDING IT.** A mutation firing only on (long setid AND `customact` action AND free-text activity) fails 288 of the 7,776 full combinations and ZERO of the 18 pairwise rows. A 4-way-only mutation likewise fails 144 full combinations and no pairwise row. This is the exact and complete cost of the reduction, and it is why E-05 preserves the exhaustive arm instead of deleting it. | `3-way (setid-long AND customact AND free-text) full=CAUGHT pairwise=MISSED (full combos failing: 288)`; `4-way (statuscov AND id6 AND customart AND stall0) full=CAUGHT pairwise=MISSED (full combos failing: 144)`. |
| F-07 | **THE OBVIOUS WAY TO RUN THIS MUTATION STUDY IS WRONG, AND E-06 FENCES AGAINST IT** because authoring hit it first. Monkeypatching `term.visible_width` to inject a width error reports `missed` for BOTH arms on four of five mutations, because the renderer pads WITH that same function: inflate it and the padding inflates too, so the box stays rectangular and nothing is detectable by any arm. The sound method mutates the rendered tuple returned by `render_stream.format_statusline_lines`. | First attempt, patching `_T.visible_width`: `M1 width+1 when setid present full=missed pairwise=MISSED`, same for M3, M4, M5; only `M2 drop 4th line` was `CAUGHT/CAUGHT`. Second attempt, mutating rendered output: seven of seven caught by both arms (F-05). |
| F-08 | **THE CHEAPER-LOOKING ALTERNATIVE, OPTIMIZING THE RENDERER, WAS PROTOTYPED AND IS REJECTED ON MEASUREMENT.** `term.visible_width` is the hot path (about 80 percent of render cost: 0.398s of 0.483s cumulative, via 389,600 generator-expression calls and 377,200 `unicodedata.category` calls per 400 renders). Replacing it with a `str.translate` delete-map is 4.5x faster and bit-identical, BUT the map costs about 320ms to build over `sys.maxunicode`, which lands on every `aw` invocation: `agent_workflows.term` import goes from about 115ms to 571ms eagerly, and a lazy build still pays 324ms on the first `visible_width` call. Trading a 440ms regression in every interactive command for a test-only win is the wrong trade, and `aw` startup latency is itself user-perceptible. The prototype was reverted; the tree is unmodified. | `cProfile`: `16400 calls 0.398s cumulative term.py:90(visible_width)` of `0.483s` total. Microbenchmark: `current 14.692s / translate 3.381s / ascii+translate 3.227s` over 320,000 calls, correctness `mismatches = 0` on all probes including `\u26a0\ufe0e`, `a\u200bb`, `e\u0301clair`. Import cost: baseline `115595 | agent_workflows.term`; eager map `448092 | 571054`; lazy `first call 324ms, second call 12.0us`. `git checkout -- agent_workflows/term.py` then `visible_width('\u26a0\ufe0e') == 1`. |
| F-09 | **REDUCING THE SWEEP'S PER-COMBINATION WORK IS NOT SUFFICIENT ON ITS OWN**, so the row count is the right lever. Dropping the in-loop repeat render buys 1.34x and dropping the `format_statusline` wrapper call buys 1.90x, against a shortfall that needs far more. The test performs 8 `format_statusline_lines` calls and 4 `format_statusline` calls per combination (two unicode modes x two styling modes x [render, repeat] plus the wrapper). | Decomposition probe: `as-shipped 4018us/combo -> projected full 7776 = 31.2s single-process`; `no in-loop repeat 2992us/combo -> 23.3s (1.34x cheaper)`; `lines-only 2117us/combo -> 16.5s (1.90x cheaper)`. `calls per combo: {'format_statusline_lines': 8, 'format_statusline': 4}`. |
| F-10 | **CONTENTION IS THE TRIGGER, AND THE 68.16s IN-SUITE FIGURE IS ALREADY THE CONTENDED ONE.** Alone the test is 14-15s; under a bare suite (`-n auto` on 12 cores) it is 68.16s, a 4.5x inflation from competing for the same cores. A synthetic load of 11 and then 36 spinning processes drove the isolated test to 27.1s and 27.5s, confirming the mechanism without reaching 90s on this particular 12-core machine. The honest reading is that the suite's own parallelism is the dominant contention source and a busier or smaller machine closes the remaining 1.3x. | Isolated: `1 passed in 15.24s`, and `1 passed in 14.20s` on a second run. Under 11 hogs: `1 passed in 27.12s`, `WALL 27.70 s`. Under 36 hogs: `1 passed in 27.48s`, `WALL 28.18 s`. In-suite: `68.16s` (F-01). `nproc` = 12. |
| F-11 | **THREE BACKLOG ITEMS DESCRIBE THIS ONE DEFECT AND A FOURTH DESCRIBES ITS NEIGHBOUR.** `8sr0or` (this plan's item), `cqgr7f` ("under xdist CPU contention") and `mu4k1g` ("exceeds 90s hang guard under parallel xdist load") are the same nodeid and the same failure; all three are `open`, `Work-Kind: bug`, `Blocks-Release: next`. Separately `tf6x3a` proposes marking the `fields`/`verbose` end-to-end tests `livecorpus`, which is the F-01 neighbour at 82.98s. This plan closes the defect for all three statusline items, but it must NOT silently close records it does not own. | `grep -rln "90s\|hang guard\|hang timeout" .aw/records/backlog/` returns the four open items named. `8sr0or` and `cqgr7f` and `mu4k1g` each carry `- Status: open`, `- Work-Kind: bug`, `- Blocks-Release: next`. Both `8sr0or` and `cqgr7f` were created as incidental side effects of unrelated plan executions (`fqcax0` and `x19law` respectively, each auto-reconciled as an out-of-scope path). |
| F-12 | **THE BASELINE AT THIS HEAD IS `3 failed, 4624 passed, 2 skipped`, AND ALL THREE FAILURES ARE PRE-FILED AND UNRELATED.** This is recorded so the post-change run reconciles against a known number instead of being read as clean or as newly broken. Notably the statusline test PASSED in both of these runs, consistent with F-10: it is load-dependent, not deterministic, which is itself the argument for fixing the cost rather than waiting for a reliable reproduction. | Two independent bare runs: `3 failed, 4624 passed, 2 skipped, 3 warnings in 242.87s` and `... in 284.07s`. Failures both times: `test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` (filed `6bolin`), `test_selector_type_containment.py::test_must_not_refuse_matrix` (filed `bxnhdj`), `test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation` (filed `8jeh4x`). |
| F-13 | **THE TWO LITERALS THE CURRENT TEST ASSERTS ARE ARTIFACTS OF THE ENUMERATION, NOT PROPERTIES OF THE RENDERER**, which is why E-04 replaces them with a derived relationship rather than new literals. `assert len(combos) == 7776` and `assert render_count == 31104` only restate that nine domains of sizes 3,2,3,3,3,2,3,4,2 were multiplied and that each combination was rendered four times. Neither can fail for any renderer defect. | `tests/test_statusline_behavior.py` contains `assert len(combos) == 7776` and the trailing `assert render_count == 31104` with the comment "7,776 combinations * 2 styling * 2 unicode = 31,104 renders". `3*2*3*3*3*2*3*4*2 = 7776` and `7776*4 = 31104`. |
| F-14 | **THE EXHAUSTIVE ARM IS CHEAP TO KEEP, so preserving it costs the project almost nothing.** Serially the full product projects to about 31.2s single-process (F-09), comfortably inside a generous explicit timeout, and it runs only in the `slow` arm. So this plan does not face a keep-or-delete choice on the 3-way coverage F-06 identifies; it can and does keep it. | F-09 projection `31.2s single-process` for the as-shipped per-combination work over 7,776 rows. `pyproject.toml` marker description: `slow: heavy subprocess/integration tests ... Deselected by default for a fast per-run suite`. |

## Proposed changes (ordered, validatable)

1. Re-measure the duration and reproduce the guard firing at the execution head before editing anything (E-01).
2. Add a deterministic pairwise covering-array generator to the test module, seeded from an uncovered pair per row (E-02).
3. Add a test asserting the generator's own coverage and determinism contract, so the reduction's premise is guarded (E-03).
4. Rewrite the fast-suite sweep to iterate covering-array rows, keeping all four invariants, both styling modes, both unicode modes, and the zero-width fence, and replacing the two enumeration literals with a derived relationship (E-04).
5. Add the exhaustive full-product sweep as a `slow`-marked companion with an explicit, comment-justified timeout (E-05).
6. Run the mutation study over rendered output and record both what pairwise catches and the 3-way class it misses (E-06).

## Deferred / out of scope (with reason)

- Optimizing `term.visible_width` is NOT done here. F-08 measured a 4.5x speedup that is bit-identical, but it costs about 440ms on `agent_workflows.term` import (or 324ms on first call if built lazily), which every `aw` invocation pays. That is a user-perceptible regression traded for a test-only gain.
  - Carrier-Declined: There is no deferred work to carry, because the prototype's conclusion is REJECT rather than LATER. Filing a carrier would schedule a change this plan measured and found net-negative, and a future reader needs the measurement, not a ticket. The numbers are recorded in F-08 so nobody repeats the experiment. If renderer throughput later becomes a real constraint (for example a live statusline redrawing far more often than it does today), the right move is a fresh measurement of the then-current hot path, not resurrection of this prototype.
- The 82.98s `tests/test_verbose_flag_reach.py::VerboseFlagReachTests::test_verbose_flag_end_to_end_observable_difference` is the slowest test in the suite and has less headroom than the one this plan fixes, but it is a different test, a different root cause (subprocess-heavy CLI reach checking, 25.92s even in isolation), and a different remedy.
  - Carrier: tf6x3a
- The three pre-existing suite failures recorded in F-12 are not fixed here; they are recorded only so the post-change run reconciles. Each has its own filed item: `6bolin`, `bxnhdj`, `8jeh4x`.
  - Carrier-Declined: No carrier is filed because all three are ALREADY FILED as open backlog items, named in F-12 with their nodeids. Filing a fourth would create a duplicate owner for work that already has one, which is the specific failure mode F-11 documents has happened three times over on this very defect.
- The duplicate backlog items `cqgr7f` and `mu4k1g` (F-11) describe the same nodeid and the same failure as this plan's item. This plan does not close or retire them.
  - Carrier-Declined: Deliberately NOT carried, because deduplicating another record's lifecycle is a maintainer's call and not an executing agent's. RECOMMENDED ACTION FOR THE REVIEWER: once this plan executes, close `cqgr7f` and `mu4k1g` as duplicates of `8sr0or` with this plan as the evidence, or re-point them at it. An executing agent must not quietly set two records it was not handed to `done`, and filing a carrier for "someone should tidy the backlog" would itself add a fourth record to a pile of three.
- No production module is touched. `- Scope-Paths:` names exactly one test file. If execution discovers a real renderer DEFECT while reshaping the sweep, it must stop and report rather than fixing production code under a test-cost plan.
  - Carrier-Declined: This is a SCOPE CONSTRAINT, not parked work: no renderer defect is known or suspected. F-05's unmutated baseline passes every invariant on today's tree, so there is nothing to carry. The one KNOWN open renderer defect in this area, the zero-width non-rectangularity, is already owned by approved plan `it6tpj` and is fenced out of the sweep rather than deferred by this plan.

## Scope check

- Over-scope: none. The single scope path is `tests/test_statusline_behavior.py`. The renderer optimization that would have touched `agent_workflows/term.py` was prototyped, measured, rejected, and reverted (F-08), and the tree is unmodified.
- Under-scope: this plan fixes ONE test's cost. It does not lower the suite's overall runtime (about 242-284s, F-12), does not address the slower `test_verbose_flag_reach.py` neighbour (carried by `tf6x3a`), and does not change the 90s default or the guard itself. Leaving the default alone is deliberate: the guard caught a real cost problem, and raising the global budget would blind it to the next one.

## Required tests / validation

Every validation item demands PASTED runner output, never a claim. Run the focused module with `python3 -m pytest tests/test_statusline_behavior.py` and, where per-test timings or counts are needed, `-o addopts="" --durations=N` rather than fighting the configured flags. Run the exhaustive arm explicitly with `-m slow` (or `-m ""`), since the default `addopts` deselects it; an E-05 arm that was never actually run is not validated. Run the whole suite bare (`python3 -m pytest`) and reconcile against the F-12 baseline of `3 failed, 4624 passed, 2 skipped` with the three nodeids named. The mutation study (E-06/V-06) mutates rendered output in the working tree or in a scratch harness, captures the result, and leaves `git status` clean for `agent_workflows/`.

## Spec / documentation sync

N/A with reason: this plan changes one test file's enumeration strategy and its marker/timeout posture. It changes no CLI surface, no production module, no public contract, and no `.spec.md`, so `- Scope-Paths:` declares no spec and the runners' spec-edit announcement will correctly report nothing. The hang guard's own rationale comment in `conftest.py` already documents `@pytest.mark.timeout` as the sanctioned remedy for a legitimately slow test, so E-05 follows existing documented practice rather than establishing new policy needing a doc change. The durable record of WHY the fast arm is pairwise, and of the 3-way class that choice gives up, is F-05 and F-06 of this plan plus the comment E-05 requires on the slow arm.

## Open questions

### OQ-01: Should the exhaustive arm be `slow`-marked, or deleted in favour of pairwise alone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT, keep it, `slow`-marked. F-06 proves pairwise misses a 3-way-only defect (288 of 7,776 full combinations fail, zero pairwise rows do), so deleting the exhaustive arm would be a real and provable loss of coverage. F-14 shows keeping it is nearly free: about 31.2s serial in an arm that is deselected by default and run by `make test-all`, `-m ''`, and the CI advisory slow step. A choice between a measured loss and a near-zero cost is not a question for a human.

### OQ-02: Should the 18 covering-array rows be frozen as a literal table instead of generated?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, generate them. A frozen table would be marginally faster to read but would rot silently the moment a domain gained a value: the table would still pass while no longer covering the new value's pairs. Generating them, with E-03 asserting the coverage contract, makes a domain change automatically re-cover. The generator is deterministic (F-04: `deterministic on regeneration: True`) and costs about 2.4ms, so generation buys the rot-resistance for nothing. Reviewers wanting the rows visible can get them from the E-03 test's failure output.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the `--durations` line for `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs` from a bare suite run at the execution head, and separately paste a run in which `conftest.TestHangTimeout` names that exact nodeid (forcing it with `AW_TEST_TIMEOUT` below the measured duration is acceptable and should be stated plainly as forced, since F-10 shows the natural trigger is load-dependent and may not reproduce on a given machine). State the measured duration against the 90s default and compute the headroom ratio. If the duration has fallen far below F-01's 68.16s, STOP AND REPORT: the remedy is sized to that measurement.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the generator and the row count it produces for the nine domains, and state that it uses no RNG (quote the absence: no `random` import, no seed). Confirm it converges, and state the guard it carries against non-convergence. Paste a demonstration that the NAIVE greedy form does NOT converge on these domains (F-06 of authoring hit `RuntimeError: covering array did not converge`), so a reviewer can see the seeded-from-uncovered-pair design is load-bearing rather than stylistic.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the generator-contract test and its green run. Then PROVE IT IS MUTATION-SENSITIVE: break the generator (for example drop the last row, or return early once single-value coverage is met) and paste the resulting failure, showing the test names a specific uncovered pair rather than failing vaguely. Revert and re-paste green. A contract test that cannot fail is the one thing that would make this entire plan's reduction unverifiable, so this item is not satisfied by a passing run alone.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the rewritten fast-suite test in full and confirm by reading it that all four invariants survive (exactly four lines; `format_statusline` equals the newline join; a single distinct `term.visible_width` across the lines; `_strip_ansi(styled)` equals plain line for line; byte-identical repeat renders), that BOTH styling modes and BOTH unicode modes are still covered, that no rendered TIME STRING and no absolute column-width number is asserted, and that no ASCII-purity assertion was introduced (that fails today and belongs to `mzrr7x`). Confirm EXPLICITLY, quoting the value lists, that no swept `setid`/`id6` value contains a zero-width code point or a newline. Confirm the literals `7776` and `31104` are gone and state what derived relationship replaced them. Paste the focused module run green, with `--durations` showing the new duration, and state the new headroom ratio against 90s.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the slow arm's decorators and the comment justifying its budget. Prove the arm is DESELECTED by default and SELECTED explicitly: paste a default `python3 -m pytest tests/test_statusline_behavior.py` collection showing it absent, and a `-m slow` run showing it collected, RUN TO COMPLETION, and green, with its duration pasted. State the duration against the chosen timeout and give the headroom ratio. A slow arm that was marked but never executed is NOT validated, because the whole point of keeping it is that it still runs somewhere.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the mutation table with one row per mutation and an explicit full-versus-pairwise verdict in each. It must include at least five 1-way or 2-way mutations (all expected CAUGHT by both arms) AND at least one 3-way-only mutation expected CAUGHT by full and MISSED by pairwise, with the count of failing full combinations stated. Confirm in writing that mutations were applied to RENDERED OUTPUT and NOT to `term.visible_width`, and say why (F-07: the renderer pads with that same function, so patching it masks the defect from every arm). Paste the unmutated baseline passing both arms. Confirm `git status` is clean for `agent_workflows/` afterwards. A table in which pairwise catches everything is a RED FLAG to be investigated, not a result to celebrate: F-06 establishes that a correct study finds the 3-way gap.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. The second-slowest test in the suite spends 68.16s of a 90s hang-guard budget rendering a 7,776-row cartesian product of statusline inputs, and when the machine is busy it crosses the line and turns the suite red while asserting nothing actually wrong. This plan changes ONE TEST FILE and NO production code. It sweeps a pairwise covering array (18 rows, 0.078s, about 1,150x headroom) in the fast suite and keeps the exhaustive product as a `slow`-marked companion with its own explicit timeout, so the coverage is relocated rather than deleted. The tradeoff is stated and measured rather than glossed: pairwise caught seven of seven 1-way and 2-way defects in a mutation study, and provably MISSES a 3-way-only defect that fails 288 of the 7,776 full combinations, which is exactly why the exhaustive arm survives. WHAT IS DELIBERATELY NOT HERE: the tempting renderer optimization, which is genuinely 4.5x faster and bit-identical but costs about 440ms on `agent_workflows.term` import that every single `aw` invocation would pay, so it was prototyped, measured, rejected, and reverted; the slower 82.98s `test_verbose_flag_reach.py` neighbour, carried by `tf6x3a`; any change to the 90s default or the guard itself, left alone because the guard did its job; and any closure of the two duplicate backlog records this defect accumulated, which is a maintainer's call.

EXECUTION CONTRACT. Commit only `tests/test_statusline_behavior.py` through `aw commit <plan> -- tests/test_statusline_behavior.py`; never `git add -A` and never push. Paste ACTUAL runner output for every `V-*` item; a claimed pass with no pasted output fails the gate. Do not raise `_DEFAULT_TEST_TIMEOUT` in `conftest.py` to make the existing test fit, which would blind the guard repository-wide to the next cost regression and is the opposite of this plan's intent. Do not delete the exhaustive sweep (F-06 prices that loss at a real 3-way defect class). Do not weaken any of the four invariants, the two-styling-mode or two-unicode-mode coverage, or the zero-width fence. Do not touch `agent_workflows/term.py` or `agent_workflows/render_stream.py`; if the mutation study appears to reveal a genuine renderer defect rather than an injected one, STOP AND REPORT rather than widening scope.

POST-GATE LIFECYCLE. Run `aw ipd begin` before implementing and `aw ipd finalize` after every `V-*` reads `pass`, which performs the path-scoped commit and the move to `.aw/records/plans/executed/`. Do not hand-edit terminal state or move the file manually. Before finalizing, confirm `aw ipd lint --phase pre-transition` conforms and reconcile the bare-suite result against the F-12 baseline (`3 failed, 4624 passed, 2 skipped`, the three nodeids named there): the target nodeid must be absent from the failure list, and any NEW failure is a stop-and-report condition rather than something to explain away. Backlog item `8sr0or` carries `- Blocks-Release: next` and this plan inherits it, so the gate travels with this plan and is discharged when it reaches `executed`.
