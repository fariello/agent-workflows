# IPD: Add a worktree-isolated mutation probe that reports whether a test selection kills a named mutant

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `e486tz` asks to MUTATION-PROVE surviving coverage, and `GUIDING_PRINCIPLES.md` Section 16 names mutation as the validity test for a test ("A test is only valid if breaking the underlying behavior makes the test fail"). The repo has no mutation tool: `mutmut` is not installed (`python3 -c "import mutmut"` -> `ModuleNotFoundError` at authoring) and no `tools/` script mutates code. Plan `oyh28b` mutated in memory with a `pytest -p` plugin; that cannot reach behavior exercised through a SUBPROCESS (`aw ...` CLI invocations a large share of the suite uses), where an in-memory patch is invisible, so a CLI-only guard would be scored `survived` falsely. It also cannot be shared with a co-worker's checkout safely if done on disk (`oyh28b` approval gate: "mutation proofs are staged IN MEMORY, never by editing a tracked file in this shared checkout"). A DISPOSABLE git worktree outside the repo satisfies both: the mutation is a real on-disk edit visible to subprocesses, and no tracked file of the shared checkout is touched. Measured cost basis: one bare suite run is `201.44s` at authoring (`38 failed, 7181 passed, 2 skipped` at `fca848304`), so a full-suite mutant costs about 3.5 minutes and baseline failures must be subtracted, not ignored.
- Scope: IN: a new `tools/mutation_probe.py` that, given a production target `agent_workflows/<module>.py::<qualname>`, a mutation operator, and a test selection (pytest args; default the bare suite's own selection, `-m 'not slow and not livecorpus'`), creates a detached worktree of `HEAD` under a temp dir, runs the selection UNMUTATED to record the baseline failing node set, applies the mutant, reruns, confirms each newly failing node against the unmutated tree (flaky nodes excluded), and reports `killed` (a non-collection node that passed at baseline now fails or errors), `killed-by-import` (only collection errors are new: the mutant broke import, not counted as a guard), `survived` (no such node), `invalid` (mutant did not apply), `timeout`, or `error` (baseline unusable, or the worktree copy is not what the interpreter imports); optional `--extra-test <commit>:<path>` writes the blob at `<commit>^` into the worktree so a replayed deleted test can serve as the POSITIVE CONTROL; always removes the worktree (`git worktree remove --force` plus `git worktree prune`). Operators: `return-none`, `return-true`, `return-false`, `negate-return` (wrap each `return <expr>` of the function itself as `return not (<expr>)`), `raise` (body becomes `raise RuntimeError("mutant")`). Behavioral tests over a synthesized repo. `tools/README.md` section. OUT: choosing which targets to mutate (Order 07); a general mutation framework; any change to production code.
- Scope-Paths: tools/mutation_probe.py, tests/test_mutation_probe.py, tools/README.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: e486tz
- Set: uncitedaudit
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g55j1e

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: g55j1e verified (set uncitedaudit, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009. Reviewed at HEAD 131f01291. Added --continue-on-collection-errors (import-break no longer aborts the session) and flaky-kill confirmation; new E-04 pure apply_operator splice; isolation preflight; status-change warns not refuses; V-01 gains a demonstrated positive control; noop dropped; gate itemized. Record: .aw/records/reviews/20261011-uncitedaudit-03-g55j1e-add-a-worktree-isolated-mutation-probe-that-reports-whether.review.md.
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog e486tz.

## Goal

Provide a reproducible yes/no answer to "does this test selection fail when this production function is broken this way?", baseline-corrected and isolated from the shared checkout, so Order 07 can mutation-prove properties without hand-patching files.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Probe

- [x] E-04 (do FIRST; E-01 depends on it) In `tools/mutation_probe.py`, add the pure splice function `apply_operator(source: str, qualname: str, operator: str) -> str | None` plus the `OPERATORS` tuple. It returns the mutated module source, or `None` when the mutant does not apply, and it touches no file. This is the TOOL editing a disposable copy, not a test reading production source.
  - Resolution: parse with `ast`. `qualname` is dotted through `ClassDef`/`FunctionDef`/`AsyncFunctionDef` nodes (`Cls.meth`, `outer.inner`). If it is absent, return `None`.
  - Operators, applied to that function node only:
    - `return-none`, `return-true`, `return-false`: the whole body becomes the single statement `return None|True|False`.
    - `raise`: the whole body becomes `raise RuntimeError("mutant")`.
    - `negate-return`: every `return <expr>` that belongs to this function becomes `return not (<expr>)`. Returns inside nested `def`/`lambda`/`class` are left alone. If the function has no `return <expr>`, return `None`.
  - Splice: replace the source lines from the first decorator's `lineno` (or the def's own `lineno`) through `end_lineno` with `ast.unparse(<mutated function node>)` indented by the node's `col_offset`. A one-line `def f(): return 1` works, because the unit replaced is the whole node and not its body lines. Before returning, check that the result `compile()`s; if it does not, return `None`.
  - Scope note: `noop` is DROPPED from the operator list. "Body becomes `pass`/`return None`" means the same as `return-none`, so the tool would be carrying an alias with no use of its own.
  - Depends on: none
  - Expected outcome: `apply_operator` returns compilable, mutated source for each operator on functions, methods and one-line defs, and returns `None` for a missing qualname and for `negate-return` on a function that has no `return <expr>`.
  - Execution state: performed

- [x] E-01 In `tools/mutation_probe.py`, add `probe(repo_root, target, operator, pytest_args=None, extra_tests=(), timeout_s=1800) -> ProbeResult` and `main(argv)` with the signature `<path.py>::<qualname> --op <operator> [--extra-test COMMIT:PATH ...] [--timeout N] [--format text|json] [-- <pytest args>]`.
  - Worktree: `tmp = tempfile.mkdtemp()`, then `git -C <repo_root> worktree add --detach <tmp>/wt HEAD`. The probe tests COMMITTED `HEAD`; uncommitted edits in the invoking checkout are not seen, and `ProbeResult.head` records the sha.
  - Extra tests: each `--extra-test COMMIT:PATH` writes the blob `git show COMMIT^:PATH` to `<wt>/PATH`. The blob is the PARENT's, so a trim commit can be named directly. Overwriting a path that exists at `HEAD` is recorded in `extra_tests_overwrote`. Extra tests are written BEFORE the baseline, so an extra test that already fails at baseline can never count as a kill.
  - Applicability first: read the target file in `<wt>` and call `apply_operator`. If it returns `None`, return `invalid` before any pytest run, with `baseline_failing` and `mutant_failing` set to `null`.
  - Isolation preflight: run `sys.executable -c 'import <pkg>; print(<pkg>.__file__)'` with `cwd=<wt>` and `PYTHONPATH=<wt>`, where `<pkg>` is the target path's first component. If it raises, or the path printed is not under `<wt>`, return verdict `error` with reason `isolation`. This guards against a false `survived` from mutating a copy that nothing imports. The package is in this machine's editable install, so the check is load-bearing; at review, `PYTHONPATH=<wt>` did resolve to the worktree copy.
  - Run command: `sys.executable -m pytest -o addopts="" -q -p no:randomly -p no:cacheprovider --continue-on-collection-errors --junitxml <xml> <selection>`, with `cwd=<wt>`, `PYTHONPATH=<wt>` prepended to the inherited value, and `timeout=timeout_s`.
    - `<selection>` is `pytest_args` when given, which REPLACES the default. The default is `-n auto -m 'not slow and not livecorpus'`, the bare suite's own selection (`pyproject.toml` `addopts`).
    - `--continue-on-collection-errors` is REQUIRED: without it, one module that fails to import interrupts the whole session ("Interrupted: 1 error during collection", exit 2) and no other test runs. This was demonstrated at review.
  - Node ids: parse the junit XML into the SET of failing or erroring ids. A testcase becomes `<classname>::<name>`. A collection error has an empty `classname` and `name` = the dotted module. It becomes `<module path>` and is flagged as a collection error. Under xdist the same collection error appears once per worker, which is why the result is a set.
  - Mutate: after the baseline run, write the mutant source computed in the applicability step and run the selection again.
  - Then: `newly_failing = mut_fail - base_fail`. Restore the original source and re-run ONLY the `newly_failing` ids. Ids that fail again unmutated are FLAKY, moved to `flaky` and dropped from `newly_failing`. A single bare run shows tens of failing nodes, so a baseline-versus-mutant comparison without this confirmation would credit flakiness as a kill.
  - Verdicts:
    - `killed`: `newly_failing` contains at least one non-collection id.
    - `killed-by-import`: `newly_failing` is non-empty and every id in it is a collection error, meaning the mutant broke import (a module-level call into the mutated function). Order 07 maps this to `import-only`, not to a guard.
    - `survived`: `newly_failing` is empty.
    - `invalid`: the mutant does not apply.
    - `timeout`: either run exceeds `timeout_s`.
    - `error`: the baseline run could not produce junit XML, or the isolation preflight failed.
    - Consumers: `timeout` and `error` are NOT guard evidence. Order 07 (`rq3q7v`) maps `killed`, `survived`, `invalid` and `killed-by-import`, but not these two, so its executor must treat them as `unprovable` with the reason recorded. This is cross-referenced here because this plan owns the verdict set.
  - Result fields: `head`, `target`, `operator`, `selection`, `verdict`, `reason`, `baseline_failing` (count), `mutant_failing` (count), `newly_failing` (sorted, first 20, plus a total count), `flaky`, `extra_tests_overwrote`, `wall_s`, `checkout_status_changed`. `--format json` writes only `json.dumps(result, sort_keys=True)`.
  - Exit codes: 0 for any verdict, 2 for usage errors.
  - Cleanup: a `finally` always runs `git worktree remove --force <tmp>/wt`, then `git worktree prune` and `shutil.rmtree(tmp)`.
  - Shared-checkout check: snapshot `git status --porcelain` of `repo_root` before and after. If it changed, set `checkout_status_changed` to the differing lines and print a stderr warning. Do not refuse: in a shared checkout a co-worker's concurrent edit legitimately changes it, and the probe writes nothing there except git's own worktree metadata.
  - Depends on: E-04
  - Expected outcome: on the real tree, the live run V-01 names reports a verdict with `head`, baseline and mutant counts. The positive control (`--extra-test 19313eed:tests/test_run_freeze.py -- tests/test_run_freeze.py`) reports `killed`: at review, the hand-applied `raise` mutant of `freeze_requirements` failed all 12 of that file's tests (`12 failed in 0.20s`), and the unmutated file passes (`12 passed`). Afterwards, `git worktree list` of the invoking checkout is identical to before.
  - Execution state: performed

### Task group 2: Tests and docs

- [x] E-02 Create `tests/test_mutation_probe.py`, two test classes.
  - (a) `apply_operator` unit tests, on fixture SOURCE STRINGS authored inside the test (not repo source). For each operator, assert the result compiles. `exec` the result and call the mutated function to check its observable return or raise: `return-true` gives `True`, `raise` raises `RuntimeError("mutant")`, and `negate-return` on `is_even` gives `is_even(2) is False`. Cover a method (`C.m`), a decorated function, a one-line def, a nested function whose inner `return` must be left alone by `negate-return`, a missing qualname (`None`), and `negate-return` on a body with no `return <expr>` (`None`).
  - (b) `probe` tests on a throwaway git repo. The suite's existing tests use `tempfile.TemporaryDirectory()` in `setUp`, which is equivalent to `tmp_path`.
    - Fixture: `agent_workflows/__init__.py` (empty), `agent_workflows/m.py` with `def is_even(n): return n % 2 == 0`, `def unused(): return 1`, `def boot(): return 1` and module-level `BOOT = boot()`. Tests: `tests/test_m.py` asserting `is_even(2)` and `not is_even(3)`, one test that always fails, and `tests/test_other.py` with one trivial passing test that imports nothing from `m`. A second commit deletes `tests/test_unused.py`, a file that asserted `unused() == 1` in the first commit, so `--extra-test <second sha>:tests/test_unused.py` restores it from the parent.
    - Every `probe` call passes an explicit `pytest_args` selection without `-n`. This keeps each fixture run serial and fast, and a sub-run needs no xdist.
    - Assert `is_even` + `negate-return` gives `killed`, with exactly the two assertion nodes in `newly_failing` and the always-failing node in neither `newly_failing` nor `flaky`.
    - Assert `unused` + `return-none` gives `survived`.
    - Assert the same plus the `--extra-test` gives `killed`.
    - Assert `boot` + `raise` gives `killed-by-import`, with `test_other`'s node not in `newly_failing`. This shows the session was not interrupted.
    - Assert `nope` gives `invalid` with no pytest run, shown by `baseline_failing is None`, as E-01's applicability step defines.
    - Assert an always-failing extra test is not credited as a kill.
    - After every call, assert the fixture's `git worktree list --porcelain` names only the fixture root, `git status --porcelain` is empty, and the temp parent is gone.
  - Drive the CLI once as a subprocess, `[sys.executable, <tools/mutation_probe.py>, "agent_workflows/m.py::is_even", "--op", "negate-return", "--format", "json", "--", "tests/test_m.py"]` with `cwd=<fixture>`. Assert exit 0, that `json.loads(stdout)` has every E-01 result key, and `verdict == "killed"`. Also assert that a bad `--op` exits 2.
  - No `livecorpus` marker; no real trim sha; nothing under `.aw/records/` is read.
  - Depends on: E-01, E-04
  - Expected outcome: the new file passes in the default bare run and asserts every verdict class except `timeout` and `error`. Those two are covered by one test each: `timeout_s=1` against a fixture test that sleeps 5 s, and a forced isolation failure via a fixture whose committed `agent_workflows/__init__.py` raises `ImportError`.
  - Execution state: performed

- [x] E-03 Add a `mutation_probe.py` section to `tools/README.md`: purpose, the disposable-worktree isolation rule and why in-memory patching is insufficient for subprocess-driven tests, the operator list, the verdict classes including baseline subtraction, the positive-control use of `--extra-test` (blob read from `<COMMIT>^`), that the probe tests committed `HEAD` only, and the measured cost (one default-selection run is about 200 s here, and a probe does at least two). `tools/README.md` is user-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: README section with those points.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Mutation is P16's own validity test (`GUIDING_PRINCIPLES.md` Section 16, bullet "Verify test sensitivity with mutation").
- Never edit a tracked file of the shared checkout for an experiment (`AGENTS.md` "Shared checkout"; `oyh28b` approval gate). A detached worktree outside the repo is a separate working tree and is torn down afterwards.
- Narrowed pytest runs use `-o addopts=""` (repo-local development contract in `AGENTS.md`); this tool passes the default marker selection explicitly so its default equals what a bare run selects.
- Bare suite at authoring HEAD `fca848304`: `38 failed, 7181 passed, 2 skipped, 3 warnings in 201.44s`, so baseline subtraction is mandatory: a mutant cannot be credited for a node that already fails.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | No mutation tooling exists in the repo or environment. | `python3 -c "import mutmut"` -> `ModuleNotFoundError: No module named 'mutmut'`; no `tools/*.py` mutates code (`ls tools`). |
| F-02 | In-memory mutation cannot see subprocess-driven behavior. | Plan `oyh28b` E-05 prescribes a `-p` plugin patching in `pytest_configure`; a subprocess `aw ...` imports a fresh interpreter that never loads that plugin. |
| F-03 | The bare suite currently has 38 failing nodes, so raw "any failure" is not a kill signal. | Bare `python3 -m pytest` at `fca848304`: `38 failed, 7181 passed, 2 skipped, 3 warnings in 201.44s (0:03:21)`. |
| F-04 | A disposable worktree is the repo's established isolation unit. | `git worktree list` shows the runner's own lanes under `.aw/worktrees/`; the runner isolates each item in one (`AGENTS.md` "each execute item gets its own ISOLATED WORKTREE"). This probe uses a temp dir outside the repo instead, so it never collides with lane leases. |
| F-05 | Without `--continue-on-collection-errors`, one unimportable module aborts the whole pytest session, so a mutant that breaks import would hide every other node and the plan's "every collected node errors" rule could never be checked. | Review demo (2026-10-12) in a detached worktree under `/tmp/opencode/`: a module whose import-time call raises -> `ERROR tests/test_zz.py - RuntimeError: mutant`, `Interrupted: 1 error during collection`, exit 2, sibling test not run; with the flag and `-n 2` -> `1 passed, 2 errors`, the junit XML carrying the collection error twice as `classname=""`, `name="tests.test_zz"`. |
| F-06 | The worktree copy IS what both the in-process tests and subprocess `aw` import, so on-disk mutation reaches CLI-driven tests. | Review demo: `PYTHONPATH=<wt> python3 -c 'import agent_workflows; print(agent_workflows.__file__)'` -> `<wt>/agent_workflows/__init__.py`; a marker appended to `<wt>/agent_workflows/__init__.py` printed from `aw --version` run with `cwd=<wt>` (via `checkout_pin.check_and_reexec`, which re-executes with the checkout's package), with and without `PYTHONPATH`. The repo is an editable install of another checkout, so an isolation preflight is still worth its one subprocess. |
| F-07 | The plan's live target is real and has a working positive control, but its V-01 selection did not. | `agent_workflows/run_freeze.py` `freeze_requirements`; `tests/test_run_freeze.py` was deleted by `19313eed` (12 tests), passes unmutated in a worktree (`12 passed in 0.15s`) and fails under a hand-applied `raise` mutant (`12 failed in 0.20s`); the only surviving test naming `run_freeze` is `tests/test_agy_runipd_cli.py`. The original V-01 ran `-- tests/` (the whole suite, about 200 s per run, twice) without the control. |
| F-08 | `noop` duplicated `return-none`. | Scope text: `noop` "body becomes `pass`/`return None`", identical in effect to `return-none`. |

## Proposed changes (ordered, validatable)

1. Pure `apply_operator` splice (E-04, first).
2. Probe with baseline subtraction, flaky confirmation and worktree isolation (E-01).
3. Synthesized-repo tests for every verdict and every operator (E-02).
4. README section (E-03).

## Deferred / out of scope (with reason)

- Selecting targets and operators per property, and running the probes: Order 07 (`rq3q7v`).
  - Carrier: rq3q7v
- Automatic operator enumeration (mutating every statement): not needed; the audit mutates named properties, and per-statement enumeration multiplies the 200 s cost by orders of magnitude.
  - Carrier-Declined: Won't-fix for this Set by measured cost (F-03 suite time); a property-level operator answers the item's question.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- Before any edit, run bare `python3 -m pytest` and keep its summary line and sorted failing node ids as the execution-start baseline.
- `python3 -m pytest -o addopts="" tests/test_mutation_probe.py` passes.
- Two live probes on the real tree (V-01: positive control and survivor), `git worktree list` identical before and after.
- Bare `python3 -m pytest`, actual summary pasted; failing node ids after minus baseline is empty.

## Spec / documentation sync

N/A for specs: no `.spec.md` governs `tools/` audit scripts. `tools/README.md` gains a section (E-03).

## Open questions

### OQ-01: Where should the disposable worktree live?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Under `tempfile.mkdtemp()`, outside the repo, so it is never mistaken for a runner lane under `.aw/worktrees/` and never leased. `git worktree prune` after removal keeps `.git/worktrees` clean. Demonstrated at review: a detached worktree under `/tmp/opencode/` was added, used, and removed with `git worktree remove --force`, leaving `git worktree list` unchanged.

### OQ-02: Should the probe refuse when the invoking checkout's `git status` changes during a run?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No; it records `checkout_status_changed` and warns. The probe writes nothing in the invoking checkout (only git's worktree metadata under `.git/worktrees/`, which `git status` does not report), so a change there is a co-worker's concurrent edit (`AGENTS.md` "Shared checkout: you are not alone in this repo"); refusing would discard a valid, possibly 7-minute result for something the probe did not cause, and exit 2 is reserved for usage errors. The invariant that the probe itself never writes there is tested in E-02 on the fixture repo, where no co-worker exists.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git worktree list` and `git status --short` of the invoking checkout before and after two live runs, both produced by E-01's `main`. Paste each run's JSON.
    - (a) Positive control: `python3 tools/mutation_probe.py agent_workflows/run_freeze.py::freeze_requirements --op raise --extra-test 19313eed:tests/test_run_freeze.py --format json -- tests/test_run_freeze.py`. Its JSON must show `verdict: killed`, `baseline_failing: 0` and a non-empty `newly_failing`.
    - (b) Survivor: the same target and operator with `--format json -- -n auto tests/test_agy_runipd_cli.py`. This is the one surviving test file that names `run_freeze` (`git grep -ln run_freeze -- tests`, re-derived at execution). Its JSON must show a `killed` or `survived` verdict with `head` and both counts.
    - Required outcome: `git worktree list` is identical after both runs, and no `/tmp` probe directory is left. Any `checkout_status_changed` lines must be explained.
  - Observed evidence: Live runs executed cleanly and left git worktree list and git status --short identical before and after with no /tmp probe directories remaining. (a) Positive control JSON: {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "7b23e627b0970e082dd4797b8e12dde48c004c40", "mutant_failing": 12, "newly_failing": ["tests.test_run_freeze.FreezeDeterminismTest::test_binds_every_category_id", "tests.test_run_freeze.FreezeDeterminismTest::test_dict_order_does_not_change_set_digest", "tests.test_run_freeze.FreezeDeterminismTest::test_same_input_same_ids_and_digests", "tests.test_run_freeze.MalformedInputTest::test_empty_item_refused_before_set_emitted", "tests.test_run_freeze.MalformedInputTest::test_non_mapping_refused", "tests.test_run_freeze.MalformedInputTest::test_non_string_item_refused", "tests.test_run_freeze.RequirementSetRecordTest::test_record_is_schema_valid_and_binds_scope", "tests.test_run_freeze.RevisionTest::test_addition_after_approval_allowed", "tests.test_run_freeze.RevisionTest::test_cosmetic_edit_is_a_digest_noop", "tests.test_run_freeze.RevisionTest::test_drop_after_approval_refused", "tests.test_run_freeze.RevisionTest::test_redefine_after_approval_refused", "tests.test_run_freeze.RevisionTest::test_semantic_edit_yields_revision_and_invalidates_evidence"], "newly_failing_total": 12, "operator": "raise", "reason": null, "selection": ["tests/test_run_freeze.py"], "target": "agent_workflows/run_freeze.py::freeze_requirements", "verdict": "killed", "wall_s": 8.13}. (b) Survivor JSON: {"baseline_failing": 0, "checkout_status_changed": [], "extra_tests_overwrote": [], "flaky": [], "head": "7b23e627b0970e082dd4797b8e12dde48c004c40", "mutant_failing": 10, "newly_failing": ["tests.test_agy_runipd_cli.AgyFailClosedIntegrationGuardTests::test_a_real_git_local_changes_refusal_is_DEFERRED_not_recorded_merge_conflict", "tests.test_agy_runipd_cli.AgyFailClosedIntegrationGuardTests::test_deferred_reattempt_backlog_close_reaches_coordinator_worktree_performer", "tests.test_agy_runipd_cli.AgyFailClosedIntegrationGuardTests::test_dirty_overlapping_base_refuses_integration", "tests.test_agy_runipd_cli.AgyFailClosedIntegrationGuardTests::test_non_passing_gate_records_merge_conflict_main_pristine", "tests.test_agy_runipd_cli.AgyFailClosedIntegrationGuardTests::test_the_MEASURED_INCIDENT_is_now_SURVIVED_defer_then_integrate", "tests.test_agy_runipd_cli.AgySelfFinalizeTests::test_begin_writes_receipt_then_finalize_moves_to_executed", "tests.test_agy_runipd_cli.AgySelfFinalizeTests::test_execute_item_spec_edits_report_parity_with_oc", "tests.test_agy_runipd_cli.AgyWorktreeIsolationTests::test_main_tree_clean_during_turn_and_receipt_under_main", "tests.test_agy_runipd_cli.AgyWorktreeIsolationTests::test_non_passing_gate_defers_not_faked_executed", "tests.test_agy_runipd_cli.AgyWorktreeIsolationTests::test_verified_child_integrates_to_main_and_worktree_removed"], "newly_failing_total": 10, "operator": "raise", "reason": null, "selection": ["-n", "auto", "tests/test_agy_runipd_cli.py"], "target": "agent_workflows/run_freeze.py::freeze_requirements", "verdict": "killed", "wall_s": 105.0}. Worktree list before and after: <repo-root> b63617180 [main], <repo-root>/.aw/worktrees/g55j1e 7b23e627b [aw/lane/g55j1e], and concurrent lane checkouts; identical before and after. Status before and after: ?? tests/test_mutation_probe.py, ?? tools/mutation_probe.py; identical.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence:
    - The pasted `python3 -m pytest -o addopts="" tests/test_mutation_probe.py` summary line.
    - A table mapping each verdict class (`killed`, `survived`, `invalid`, `killed-by-import`, `timeout`, `error`, the positive control, the not-credited baseline-failing extra test, and flaky exclusion if tested) to the test node that asserts it, re-derived from the file as written.
    - One pasted sensitivity run in a scratch copy under `/tmp/opencode/`, never the tracked file: change the copy of `tools/mutation_probe.py` so that `newly_failing` is `mut_fail` (no baseline subtraction). Run `PYTHONPATH=<scratch> python3 -m pytest -o addopts="" -p no:cacheprovider --rootdir <scratch> <scratch>/tests/test_mutation_probe.py` from `<scratch>` and show that at least one test fails.
  - Observed evidence: Pytest summary line: "22 passed in 30.55s". Test nodes mapping: killed -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_killed_is_even_negate_return; survived -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_survived_unused_return_none; invalid -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_invalid_qualname_no_pytest_run; killed-by-import -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_killed_by_import_boot_raise; timeout -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_timeout; error -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_error_isolation_preflight; positive control -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_positive_control_extra_test_kills_unused; not-credited baseline-failing extra test -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_always_failing_extra_test_not_credited_as_kill; flaky exclusion -> tests/test_mutation_probe.py::ProbeGitFixtureTests::test_flaky_test_excluded_from_kill. Sensitivity run under /tmp/opencode/scratch_sensitivity with candidate_newly_failing = mut_fail: FAILED tests/test_mutation_probe.py::ProbeGitFixtureTests::test_verdict_killed_is_even_negate_return - AssertionError: True is not false (1 failed, 21 passed in 29.94s).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff tools/README.md` showing every point E-03 lists, with zero em or en dashes in the added lines (`git diff tools/README.md | grep '^+' | grep -c $'\u2014\|\u2013'` prints 0). Also the pasted bare `python3 -m pytest` summary line, and the failing node ids after the change minus the execution-start baseline failing node ids, which must be empty.
  - Observed evidence: Dash check: git diff tools/README.md | grep '^+' | grep -c $'\u2014\|\u2013' returned 0 (zero em or en dashes in added lines). git diff tools/README.md adds the mutation_probe.py section covering purpose, worktree isolation, 5 operators, verdict classes with baseline subtraction and flaky confirmation, --extra-test positive controls, committed HEAD only, and measured cost (~200s per pass). Bare post-change pytest suite summary: "7762 passed, 4 skipped, 3 warnings in 611.84s (0:10:11)". Execution-start baseline failing node ids (tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository) minus post-change failures (0) is empty.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted `apply_operator` test node ids and their pass lines from the V-02 run, one per operator plus each `None` case. Also a pasted one-shot demonstration, `python3 -c 'from tools.mutation_probe import apply_operator; s = apply_operator(open("agent_workflows/run_freeze.py").read(), "freeze_requirements", "raise"); i = s.index("def freeze_requirements"); print(s[i:i+300])'`, printing the mutated `def freeze_requirements` block. The demonstration only reads the file and writes nothing.
  - Observed evidence: All 12 apply_operator unit tests passed in V-02: ApplyOperatorUnitTests::test_return_none PASSED, test_return_true PASSED, test_return_false PASSED, test_raise PASSED, test_negate_return PASSED, test_method_c_m PASSED, test_decorated_function PASSED, test_one_line_def PASSED, test_nested_function_negate_return_inner_preserved PASSED, test_missing_qualname_returns_none PASSED, test_negate_return_no_return_expr_returns_none PASSED, test_unknown_operator_returns_none PASSED. Demonstration command: python3 -c 'from tools.mutation_probe import apply_operator; s = apply_operator(open("agent_workflows/run_freeze.py").read(), "freeze_requirements", "raise"); i = s.index("def freeze_requirements"); print(s[i:i+300])' prints: 'def freeze_requirements(requirements: Mapping[str, Sequence[str]]) -> RequirementSet:\n    raise RuntimeError(\x27mutant\x27)\n\n\ndef requirement_set_record(\n    run_id: str,\n    seq: int,\n    actor: str,\n    timestamp: str,\n    parent: str,\n    frozen: RequirementSet,\n) -> Dict[str, Any]:\n    \"\"\"Build a `re'.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. EXECUTION CONTRACT:
- Open questions: OQ-01 and OQ-02 are resolved, and none remain.
- Order: E-04, then E-01, then E-02 and E-03.
- Scope fence (a declaration, not a stop rule): the change is expected to touch only the paths in `- Scope-Paths:`. If an out-of-scope edit proves necessary, make it and justify it at finalize: `--scope-reason` for each out-of-scope path, `--scope-ack` for each declared path left unmodified.
- Invariants:
  - The probe never edits a tracked file of the invoking checkout. Every mutation is written only inside its own temp worktree.
  - Every worktree it creates is removed and pruned, even on exception or timeout.
  - A node already failing at baseline, or flaky on confirmation, is never credited as a kill.
  - If a run leaves a worktree or a dirty path behind, fix the tool. Do not hand-clean.
- Honesty: paste the ACTUAL runner output for every claim. Never claim a result you did not run.
- Commit: only the declared paths, through `aw commit <plan> -- <paths>`. Verify that `git diff --cached --name-only` lists only your paths. Never `git add -A`, never `--no-verify`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs finalize and the lifecycle move. When executing by hand, finalize with `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms. Never move the plan with a hand `git mv`.
