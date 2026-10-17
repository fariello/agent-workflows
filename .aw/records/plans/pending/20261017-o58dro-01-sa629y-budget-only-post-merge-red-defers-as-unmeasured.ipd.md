# IPD: Post-merge revalidation defers a budget-only red as unmeasured instead of refusing it as combined-red

- Date: 2026-10-17
- Kind: child
- Concern: When the post-merge revalidation suite exits 1 with every test passing because the core-tier wall-time budget in the root `conftest.py` was overrun, `runner_shared.make_integration_validation_runner` records it as a MEASURED red (`measured: True`, empty `failures`), so the item is labelled combined-red, a paid agent fix turn is spent with the send-back text "no test ids recorded", and the refusal is terminal, although nothing in the merged code is wrong and the condition (host load) can clear on its own.
- Scope: (1) Carry a `budget_only` fact from `suite_cache.run_full_suite` through `runner_shared.run_suite_check` onto `SuiteCheckResult`, computed with the `suite_cache.is_budget_only_failure` predicate that plan `44nfmd` adds; (2) in `make_integration_validation_runner`, classify a budget-only result as NOT a measurement of the code (`measured=False`) with a reason naming the budget and the passing summary, so it routes through the existing `merge-unchecked` deferral (re-attempted, never sent back to the agent, never labelled combined-red) instead of the terminal combined-red path; (3) do NOT cache a budget-only measurement in the per-run revalidation cache, so a deferred re-attempt on the same merged tree re-runs the suite instead of being served the stale refusal; (4) behavioral tests; (5) one CHANGELOG `Fixed` line; (6) one dated `## Workflow history` note on spec `25kzda` recording that a budget-only red is a harness-side `merge-unchecked` refusal and not the "non-passing combined revalidation" Section 2.1 makes terminal. It does NOT turn a budget-only red into a pass, does NOT change the conftest guard, the 30s budget, the `ytz6z4` default demotion in `suite_cache.build_suite_child_env`, the send-back wording (plan `44nfmd`), or the seam regression tests (plan `t54fet`).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_budget_only_revalidation.py, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:44nfmd
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: o58dro
- Blocks-Release: next
- Set: o58dro
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sa629y
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved

- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record `.aw/records/reviews/20261017-o58dro-01-sa629y-budget-only-post-merge-red-defers-as-unmeasured.review.md`)
- 2026-10-17 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog o58dro with Step 0 evidence; review-ready.
- 2026-10-17 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): re-authored on lane attempt 2 under the same id6 (the attempt-1 lane commit `abca17e7d` never reached main, while plan `xc1xh9` already names `sa629y` as this backlog item's carrier); Step 0 claims re-verified against current `runner_shared` (`SuiteCheckResult` still has no `budget_only`, exit-5 branch, `record_integration_refusal` `l2mzxn` reclassification and the `not revalidation_was_unmeasured(item)` send-back guard all present) and F-2 updated for `vtcqpf`.

## Goal

A merged tree whose tests all pass must never be refused as combined-red, nor cost an agent fix turn, merely because the host was loaded while the post-merge suite ran; when the budget is the only cause, the runner must say so and treat the refusal as a re-attemptable harness condition rather than a verdict about the code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: carry the budget-only fact to the gate

- [ ] E-01 In `agent_workflows/runner_shared.py`, add a defaulted field `budget_only: bool = False` at the END of `SuiteCheckResult` (after `slot`, so every positional construction and test double keeps working, the same discipline the class docstring records for `failures`). In `run_suite_check`, set it on the success-path return to `suite_cache.is_budget_only_failure(res.exit_code, res.stdout, res.stderr, res.failures)` (the predicate added by plan `44nfmd` E-03), wrapped so any exception from the predicate yields `False`. The fail-closed exception return keeps the default `False`.
  - Depends on: none
  - Expected outcome: `run_suite_check` on a tree that exits 1 only on the enforced budget returns `passing=False, exit_code=1, failures=(), budget_only=True`; any other result has `budget_only=False`.
  - Execution state: pending

### Task group 2: classify a budget-only red as not a code measurement

- [ ] E-02 In `make_integration_validation_runner`'s inner `_runner`, in the `try` block right after the existing exit-5 branch (the one whose comment begins "`pytest` EXIT 5 IS \"no tests collected\""), add a branch taken when `not passed`, `bool(getattr(result, "budget_only", False))` and `failures` is empty: set `measured = False` and `reason` to a sentence stating that every collected test passed, that the run failed ONLY on the core-tier wall-time budget (a property of host load, not of the merged code), that this is therefore not a combined-red verdict, and ending with the suite's own `reason` (which after `44nfmd` names the budget and carries the summary). `passed` stays False. ALSO, in the same branch, set a local `budget_only_red = True` (initialised `False` beside `collected_nothing`), and guard the existing `if isinstance(cache, dict) and tree_id: cache[tree_id] = measurement` with `and not budget_only_red`, so the measurement is recorded on the item but NOT stored in the per-run tree cache. WHY: the cache at `state[REVALIDATION_CACHE_KEY]` is keyed on the merged tree id and the cache-hit branch returns the stored reading without calling `suite_check`. A deferred re-attempt (`retry_deferred_integrations`) on an unchanged main rebuilds the SAME tree, so a cached budget-only reading would be served on every re-attempt until the retry limit ran out and the item went terminal, and the deferral this plan exists to provide could never succeed (F-6 demonstrates the cache serving an unmeasured reading without re-running the suite). A budget-only reading says nothing about the tree, so it must not stand in for a later measurement of it.
  - Depends on: E-01
  - Expected outcome: the recorded `post_merge_revalidation` for a budget-only merged tree has `passed: false`, `measured: false`, no `baseline_comparison` block, and a reason naming the budget; `state[REVALIDATION_CACHE_KEY]` holds no entry for that tree, so the next call on the same tree invokes `suite_check` again; `revalidation_was_unmeasured(item)` is True, so `record_integration_refusal` reclassifies the refusal to `merge-unchecked` and the combined-red send-back loop (guarded by `not revalidation_was_unmeasured(item)`) does not fire.
  - Execution state: pending

- [ ] E-03 Confirm (read-only, no edit expected) that both hosts reach E-02 through the one shared runner: `oc_runipd` and `agy_runipd` pass `suite_check=run_suite_check` to the shared integration path, and the only `make_integration_validation_runner` definition is in `runner_shared`. Record the grep output in V-03. Review found none (one definition, at `runner_shared.make_integration_validation_runner`). If a host-local copy has appeared since, apply the same E-02 change to it and justify that out-of-scope path with `--scope-reason` at finalize.
  - Depends on: E-02
  - Expected outcome: one definition, both hosts covered.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Create `tests/test_budget_only_revalidation.py` (NOT `core`-marked; it builds git fixtures and one test launches a pytest subprocess). Fixture: a throwaway git repo with one committed file, `base_commit == lane_head ==` its HEAD, `state = {"repo": str(repo), "run_id": "run-o58dro01", "options": {"validate": False}}`, `item = {"id6": "o58dro", "base_commit": head, "lane_head": head, "attempts": []}`, exactly the shape `tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun` uses. Tests, each calling `runner_shared.make_integration_validation_runner(state, run_dir, item, suite_check=<stub>)("", ["x"])` with a stub returning a `SuiteCheckResult`: (a) `budget_only=True, passing=False, exit_code=1, failures=()` -> runner returns False, record `measured is False`, `"budget" in reason`, no `baseline_comparison` key, and `runner_shared.revalidation_was_unmeasured(item) is True`; (b) a real red (`budget_only=False`, `failures=("FAILED tests/t.py::t - x",)`) -> record `measured is True` and `revalidation_was_unmeasured(item) is False` (the code-fault path is unchanged); (c) `budget_only=True` but `failures` non-empty -> still measured (a real failure is never hidden behind the budget); (d) RE-MEASURED, NOT CACHED: with a stub that returns the budget-only result on its first call and a green result (`passing=True, exit_code=0`) on its second, call a fresh runner twice on the same `state` and tree; assert the stub was called twice, the first call returned False with `measured is False`, the second returned True with the record's `passed is True` and `cached is False`, and that after the first call `state.get(runner_shared.REVALIDATION_CACHE_KEY, {})` has no entry for the tree. This is the property the deferral depends on.
  - Depends on: E-02
  - Expected outcome: cases (a) to (d) pass, asserting only on returned values, stub call counts and recorded item and state.
  - Execution state: pending

- [ ] E-05 In the same module add the routing and end-to-end tests: (e) after case (a), call `runner_shared.record_integration_refusal` with `run_dir`, the same `state` and `item`, `attempt={}`, `branch="b"`, `integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT`, a reason tagged with the combined-red cause token via `runner_shared.tag_integration_cause(runner_shared.INTEGRATION_CAUSE_GATE_COMBINED_RED, "...")`, and recording `save_state`/`append_jsonl` stubs, asserting `item["integration_ladder"]["kind"] == runner_shared.INTEGRATION_REFUSAL_UNMEASURED`, `item["integration_ladder"]["deferrable"] is True`, and the returned decision's `deferred is True` (review F-7 ran this exact call: `merge-unchecked True merge-retry True`); (f) end-to-end `runner_shared.run_suite_check` on a fixture repo whose only test passes and whose `conftest.py` reproduces the enforced budget rule (banner `CORE TIER BUDGET EXCEEDED` on stderr, `session.exitstatus = 1` when `AW_CORE_BUDGET_ENFORCE=1`, `AW_TEST_CPU_COUNT>=12`, over `AW_CORE_BUDGET_SECONDS`), built with `tests.support.init_repo` and committed with `support.git(..., env=support.clean_git_env())`, run with `AW_CORE_BUDGET_ENFORCE=1`, `AW_CORE_BUDGET_SECONDS=0.01`, `AW_TEST_CPU_COUNT=12` patched into `os.environ` via `mock.patch.dict` AND, inside that patch, `PYTEST_XDIST_WORKER`, `PYTEST_XDIST_WORKER_COUNT`, `PYTEST_ADDOPTS`, `AW_SUITE_SLOT_HELD` and `AW_TEST_TIER` popped. The pops are required, not hygiene: CI runs this module under `-n auto`, the child pytest inherits the worker's `PYTEST_XDIST_WORKER`, and the fixture conftest's `if "PYTEST_XDIST_WORKER" in os.environ: return` then skips the budget check, so the child exits 0 and the test fails (F-8 measured exactly that under `-n 2`, and a pass under `-n 0` and `-n 2` once popped). Keep the fixture's own minimal conftest (do not import `tests.test_core_tier_selection.CONFTEST_HOOKS`, which after `44nfmd` is load-aware and would need `AW_TEST_LOADAVG` pinned). Assert `passing is False`, `exit_code == 1`, `failures == ()` and `budget_only is True`.
  - Depends on: E-01, E-04
  - Expected outcome: both tests pass, serially and under `-n 2`; (f) proves the fact is produced by the real seam, not only by a stub.
  - Execution state: pending

### Task group 4: documentation and suite

- [ ] E-06 Add one `- Fixed:` line under the pending 2.0.0 section of `CHANGELOG.md`, in plain user-facing language with no em or en dashes, saying that a merge whose tests all passed but which ran over the core-tier time budget is now retried later instead of being reported as a failing suite and sent back to the agent. Then run the new module serially and under `-n 2`, the neighbouring contracts (`tests/test_suite_cache.py`, `tests/test_hook_and_suite_fix_it.py`, `tests/test_core_tier_selection.py`), the bare core tier `python3 -m pytest`, `aw check`, and `aw sanitize --agent`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-07
  - Expected outcome: all pass; no new `aw check` or sanitizer finding.
  - Execution state: pending

- [ ] E-07 Record the spec reading on `25kzda` without changing its status or text: `aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "<note>"`, where the note says, in substance: plan `sa629y` (backlog `o58dro`) routes a post-merge revalidation whose every test passed and whose only failure is the enforced core-tier wall-time budget to the existing harness-side `merge-unchecked` refusal (`l2mzxn`), which defers and ends terminal at `merge-needs-human` when `--integration-retry-limit` is spent; this is not a "non-passing combined revalidation" in Section 2.1's sense, because Section 2.1 grounds that exclusion in repetition not fixing the condition, and host load is fixed by repetition; a budget-only red is never treated as a pass. WHY a note and not silence: Section 2.1's literal text ("a non-passing combined revalidation ... none reclassifies a failure as a deferral") reads as covering this case, so a reviewer checking a later plan against the spec would otherwise see a contradiction the contract never records.
  - Depends on: E-02
  - Expected outcome: the spec gains one dated `## Workflow history` line naming `sa629y` and `merge-unchecked`; its `- Status:` and body are unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `conftest.pytest_sessionfinish` (docstring "Enforce the wall-time budget on the core tier (IPD hguae9 E-05)") sets `session.exitstatus = 1` on overrun when `cpu_count >= 12` and `AW_CORE_BUDGET_ENFORCE != "0"`, writing a `CORE TIER BUDGET EXCEEDED` banner to stderr; tests can pass while the run exits 1.
- `suite_cache.build_suite_child_env` carries the `ytz6z4` default demotion (`base.setdefault(AW_CORE_BUDGET_ENFORCE_ENV, "0")`, commit `8b798b0b8`), so a runner-launched suite enforces the budget only when the caller explicitly sets `AW_CORE_BUDGET_ENFORCE`; `tests/test_core_tier_selection.py::test_gate_suite_honors_explicit_enforce` pins that an explicit request still fails `run_full_suite`.
- `runner_shared.run_suite_check` calls `suite_cache.run_full_suite(..., serve_failures=False, run_id=run_id)` and builds a `SuiteCheckResult` from the returned `SuiteRunResult`, which carries `stdout` and `stderr`; `SuiteCheckResult` does not, so the budget fact must be computed there and carried as a field.
- `make_integration_validation_runner`'s `_runner` already reinterprets one non-failure for the merge question: pytest exit 5 ("the merge cannot have broken anything; treating as passing for revalidation only"). E-02 is the same kind of narrow, exit-shape-keyed reinterpretation, but it keeps refusing.
- `_record_revalidation`'s docstring: `passed=False, measured=False` is "the harness could not ask the question", a statement about the RUNNER; `revalidation_was_unmeasured` is "THE ONE READER OF THE `measured` FLAG". `record_integration_refusal` reclassifies a refusal whose record is unmeasured to `INTEGRATION_REFUSAL_UNMEASURED` (`merge-unchecked`), and the combined-red send-back loop is guarded by `not revalidation_was_unmeasured(item)`, so no new routing code is needed.
- `classify_integration_refusal` docstring: `merge-unchecked` is deferrable because a re-attempt "CAN succeed", and "What it must never do is silently pass: it refuses, defers, and ends terminal when the budget runs out".
- `_relative_revalidation_verdict` returns early with no comparison when `measurement.get("measured") is False`, so a budget-only red is never fed to `new_failures_since_baseline` (whose empty-list-on-red branch is what produces today's `unknown` judgement).
- Tests must assert behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | o58dro was filed before the runner-side demotion landed | `git log`: `c83ed5c89` (file `o58dro`) 2026-10-16 20:28; `8b798b0b8` (ytz6z4 fix) 21:20; `8b798b0b8` is an ancestor of this lane's HEAD |
| F-2 | The same defect is filed four more times; its remaining surfaces are carried | `ytz6z4` done; `48hjbx` graduated to `44nfmd` (bare-pytest load awareness, budget-only `reason`, send-back wording); `m8d13e` graduated to `t54fet` (seam regression tests); `vtcqpf` graduated to `xc1xh9` (host-level end-to-end proof, gated on this item reaching `done`); `44nfmd` names `o58dro` as a duplicate carrier |
| F-3 | What no carrier fixes: the revalidation CLASSIFICATION. A budget-only red that reaches the gate (explicit enforce, or any future path that misses the demotion) is still recorded `measured: True`, labelled combined-red, sent back to the agent for a paid fix turn, and refused terminally, though repetition can clear host load | `make_integration_validation_runner` keeps `measured = True` for every suite result that did not raise; combined-red loop condition `and not revalidation_was_unmeasured(item)`; `44nfmd` OQ-02 keeps the verdict and only changes the explanation |
| F-4 | The routing for a harness-side refusal already exists and is shared by both hosts | `record_integration_refusal` `l2mzxn` reclassification; `classify_integration_refusal` |
| F-5 | The predicate needed to detect a budget-only failure is being authored by `44nfmd` (`suite_cache.is_budget_only_failure`, `CORE_BUDGET_BANNER`); writing a second detector would duplicate it | `44nfmd` E-03 |
| F-6 | (review, HEAD `3158217ae`) The per-run revalidation cache serves an UNMEASURED reading without re-running the suite. Driving `make_integration_validation_runner` twice on the same `state` and tree with a stub that raises on call 1 and passes on call 2: call 1 -> `False, measured False`; call 2 -> `False, cached True, measured False`, stub called once. So without E-02's cache guard a budget-only reading would be served on every deferred re-attempt over an unchanged main and the deferral could never succeed. | scratch script under gitignored `tmp/`; output `attempt 0 -> False ... suite calls: ['raise'] cached: False measured: False` / `attempt 1 -> False ... suite calls: ['raise'] cached: True measured: False`; cache-hit branch `if tree_id and isinstance(cache, dict) and tree_id in cache:` returns before `suite_check` |
| F-7 | (review) After an unmeasured record, `record_integration_refusal(integ_kind=INTEGRATION_REFUSAL_CONFLICT, integ_reason=tag_integration_cause(INTEGRATION_CAUSE_GATE_COMBINED_RED, ...))` yields ladder `kind merge-unchecked`, `deferrable True`, `status merge-retry`, decision `deferred True`; so E-05 (e) is satisfiable as written. | same scratch script |
| F-8 | (review) E-05 (f)'s fixture (minimal budget conftest, one passing test, `AW_CORE_BUDGET_ENFORCE=1`, `AW_CORE_BUDGET_SECONDS=0.01`, `AW_TEST_CPU_COUNT=12`) through `runner_shared.run_suite_check`: under `-n 0` returns `passing False, exit 1, failures ()`, banner on stderr; under `-n 2` returns `passing True, exit 0` because the child inherits `PYTEST_XDIST_WORKER` and the conftest skips; popping the xdist and suite env keys inside the patch makes it pass under both. | scratch pytest module under `tmp/`: `1 passed` (`-n 0`); `assert (True, 0, ()) == (False, 1, ())` (`-n 2`, no pops); `1 passed` both with pops |

## Proposed changes (ordered, validatable)

1. E-01: `SuiteCheckResult.budget_only`, set in `run_suite_check`.
2. E-02 and E-03: budget-only red recorded as unmeasured (and not cached) in the shared revalidation runner; confirm both hosts use it.
3. E-04 and E-05: behavioral tests for classification, cache reuse, routing, and the real seam.
4. E-06: CHANGELOG line and full validation.
5. E-07: dated note on spec `25kzda` recording the Section 2.1 reading.

## Deferred / out of scope (with reason)

- Load-aware demotion in the conftest guard, the budget-only `reason` text in `suite_cache`, and replacing "no test ids recorded" in the combined-red send-back: designed in `44nfmd`.
  - Carrier: 44nfmd
  - Carrier-Evidence: .aw/records/plans/executed/20261017-48hjbx-01-44nfmd-make-the-core-tier-wall-time-budget-load-aware-and-name-a-bu.ipd.md
- Regression tests proving each runner seam reports an all-green over-budget tree green under the default demotion: designed in `t54fet`. This plan does not alter that outcome (the default path never produces a budget-only red), and `t54fet`'s explicit-enforce controls assert `passed False` and empty `failures`, which still hold after E-02.
  - Carrier: t54fet
- Treating a budget-only red as a PASS at revalidation (as exit 5 is): refused, because an explicit `AW_CORE_BUDGET_ENFORCE` request is a request for enforcement (`test_gate_suite_honors_explicit_enforce`, `44nfmd` OQ-02); E-02 defers instead of passing.
  - Carrier-Declined: deliberate decision recorded in OQ-01; nothing is left unfixed.
- Classifying a budget-only red in the pre-work suite baseline (`start_suite_baseline`): the baseline is consumed only through `_relative_revalidation_verdict`, which E-02 short-circuits for this case, so a budget-only baseline cannot produce a fabricated verdict here.
  - Carrier-Declined: no defect remains once E-02 lands.
- Host-level end-to-end proof through `execute_item` and `retry_deferred_integrations` on both hosts: designed in `xc1xh9` (graduated from `vtcqpf`), which depends on this plan's `budget_only` field.
  - Carrier: xc1xh9

## Scope check

- Over-scope: none; one production file, one new test module, one CHANGELOG line, one spec history note.
- Under-scope: none; the classification, its exclusion from the tree cache so a re-attempt re-measures, its routing on both hosts (E-03) and the real seam that produces the fact (E-05 f) are all covered, and every other surface of the defect is carried by `44nfmd` or `t54fet`.

## Required tests / validation

- New `tests/test_budget_only_revalidation.py` (cases (a) to (f)), run serially and under `-n 2`; unchanged `tests/test_suite_cache.py`, `tests/test_hook_and_suite_fix_it.py`, `tests/test_core_tier_selection.py`; the bare core tier; `aw check`; `aw sanitize --agent`. Actual runner output must be pasted in each `V-*`.

## Spec / documentation sync

- Spec `25kzda` gains one `## Workflow history` note (E-07) and no body or status change, so it is listed in Scope-Paths. Spec `25kzda` Section 2.1 says the integration ladder "never applies to ... a non-passing combined revalidation" and that no rung "reclassifies a failure as a deferral", with the stated reason "none of which repetition fixes". A budget-only red is not a failing combined revalidation in that sense: every test of the merged tree passed, and the only failing condition (host load) IS fixed by repetition. The `merge-unchecked` class it routes to is the existing, already-shipped harness-side refusal (`l2mzxn`) and is not described by the spec text, so the spec's rule and its reason both stand unchanged. Review judged the literal text close enough to this case that the reading must be recorded where spec readers will find it, hence E-07's note rather than silence; the design is unchanged.
- `CHANGELOG.md` gains one `Fixed` line (E-06). `CONTRIBUTING.md` and `pyproject.toml` describe the conftest guard, which this plan does not change.

## Open questions

### OQ-01: Should a budget-only red at revalidation pass, defer, or stay terminal?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Defer (record as unmeasured, route to `merge-unchecked`). Resolved from repository evidence: passing would override an explicit enforcement request (`test_gate_suite_honors_explicit_enforce`; `44nfmd` OQ-02); staying terminal and sending back to the agent is the o58dro symptom itself, spending a paid turn on a condition the agent cannot fix; `classify_integration_refusal` defines the deferrable class as refusals a re-attempt "CAN succeed" on while never silently passing, which is exactly host load. The deferral is bounded by `--integration-retry-limit` and ends terminal, so a permanently overloaded host still reaches a human.

### OQ-02: Why depend on `44nfmd` instead of detecting the banner here?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `44nfmd` E-03 adds `suite_cache.is_budget_only_failure` and `CORE_BUDGET_BANNER` as the single detector; a second detector in `runner_shared` would drift from it. `- Item-Dependencies: executed:44nfmd` makes the runner dispatch this plan only after that predicate exists.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` hunk showing `budget_only: bool = False` as the last `SuiteCheckResult` field and the `run_suite_check` return setting it from `suite_cache.is_budget_only_failure`, with the fail-closed return unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff agent_workflows/runner_shared.py` hunk showing the budget-only branch after the exit-5 branch setting `measured = False`, `budget_only_red = True` and a budget-naming `reason` while leaving `passed` False, plus the `and not budget_only_red` guard on the `cache[tree_id] = measurement` store, and no other change inside `_runner`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted output of `rg -n "def make_integration_validation_runner|suite_check=run_suite_check" agent_workflows/` showing one definition in `runner_shared.py` and both hosts passing `run_suite_check`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_budget_only_revalidation.py` showing cases (a) to (d) PASSED, with case (d) asserting two stub calls and a second-call pass on the same tree (code path: `runner_shared.make_integration_validation_runner` `_runner`, changed by E-02).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the same pasted run showing cases (e) and (f) PASSED (code paths: `runner_shared.record_integration_refusal` reclassification; `runner_shared.run_suite_check` -> `suite_cache.run_full_suite` on the fixture repo), with a summary line showing 0 failed; plus a second pasted run of the module with `-n 2` showing 0 failed (proves (f) holds inside an xdist worker, as CI runs it).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff CHANGELOG.md` showing one `- Fixed:` line; pasted tails of `python3 -m pytest -o addopts="" -n 2 tests/test_budget_only_revalidation.py`, `python3 -m pytest -o addopts="" tests/test_suite_cache.py tests/test_hook_and_suite_fix_it.py tests/test_core_tier_selection.py` and of the bare `python3 -m pytest` (each `N passed`, zero failed); the `aw check` summary with no new error; and the `aw sanitize --agent` result record with status pass.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `git diff` of the `25kzda` spec showing exactly one added `## Workflow history` line naming `sa629y` and `merge-unchecked`, and pasted `grep -n "^- Status:" <spec>` still reading `approved`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`) and after `44nfmd` is executed. Execution contract:

- Open questions: OQ-01 and OQ-02 are resolved; nothing blocks execution.
- Prerequisite: if `suite_cache.is_budget_only_failure` is absent when this runs, `44nfmd` has not landed; STOP and report rather than writing a second detector (OQ-02).
- Scope fence: `- Scope-Paths:` declares the four files this plan edits. An edit outside them is made and then justified with `--scope-reason` at finalize.
- Honesty: paste ACTUAL runner output in each `V-*`; never claim a pass you did not run.
- Commits: path-scoped via `aw commit sa629y -- <paths>`; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize, so leave the plan in `pending/`. Executed by hand (`aw work begin sa629y`), finish with `aw ipd finalize sa629y --actor <agent/model> --message <summary> --apply` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan to `executed/`.
