# IPD: Add aw suite: one full-suite entry point with a tree-keyed result cache and a bounded worker count

- Date: 2026-10-12
- Kind: child
- Concern: Full suites run with no memory of identical prior runs and at `-n auto` regardless of how many other suites are running. Measured over October: 1,258 agent full-suite invocations (median 216s, p90 622s, 91.5h total); of the 322 runner baselines, 61 (19%) were at a code tree (`agent_workflows`, `tests`, `conftest.py`, `pyproject.toml`, `tools`) already seen; and three handoffs are exact repeats BY CONSTRUCTION: a fast-forward integration leaves `main`'s tree equal to the lane's last-tested tree, the next item's baseline is taken at the tip the integration gate just measured, and lanes dispatched from one base share it. The runner has three suite seams that each spawn their own pytest: `runner_shared.run_suite_check` (argv `SUITE_CHECK_ARGV`), `start_suite_baseline` (same argv in a detached checkout), and post-merge revalidation (`make_integration_validation_runner` -> injected `suite_check` in the materialized merge result). Agents are told only "e.g. `python3 -m pytest <test_file> -v`" (`runner_shared` execute/verify prompt templates, "Run the required tests and validation commands for this IPD").
- Scope: IN: a new `agent_workflows/suite_cache.py` (key computation, store, lookup) and a new `aw suite` command that runs the repository's bare full suite through it with a bounded worker count; route the three runner seams through the same library function; update the execute and verify prompt templates to direct full-suite runs to `aw suite`; docs and CHANGELOG. OUT: narrowed runs (`aw suite` refuses a test selection and points at plain pytest, so quick checks stay fast and uncached); the machine-wide lock (Order 03); test selection (Order 04); changing `pyproject.toml` `addopts` for humans.
- Scope-Paths: agent_workflows/suite_cache.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/runner_shared.py, tests/test_suite_cache.py, tests/conformance_matrix.py, docs/cli-human-guide.md, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:9ec94f
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 2
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0o0wt2

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-4-Argon-High): aw agy run self-finalize: 0o0wt2 verified (set suiteeff, attempt 1). [Scope reconciliation - in-scope-unmodified tests/conformance_matrix.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-13 approved (aw set): status set to approved

- 2026-10-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-011 (record `.aw/records/reviews/20261012-suiteeff-02-0o0wt2-add-aw-suite-one-full-suite-entry-point-with-a-tree-keyed-re.review.md`)
- 2026-10-13 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-011

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 02 of Set `suiteeff` from backlog `58x9mw`.

## Goal

Every full-suite run, by a runner or an agent, goes through one command that returns the stored result when the exact same code was already measured, and otherwise runs with a worker count sized to the machine instead of to all of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the cache key and store

- [x] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` before the first edit; record its summary line and failing node ids.
  - Depends on: none
  - Expected outcome: a recorded summary line and failing-node-id list.
  - Execution state: performed

- [x] E-02 Create `agent_workflows/suite_cache.py` with `suite_key(checkout: Path, argv: Sequence[str]) -> SuiteKey`. The key is a SHA-256 over: (1) the WORKING-TREE tree id, computed by `git add -A` then `git write-tree` against a TEMPORARY index (`GIT_INDEX_FILE=<tmp>`, seeded by COPYING the checkout's real index file, `git rev-parse --git-path index`, which makes the add incremental: measured at review on this 4,882-file checkout, 0.03s copied versus 0.65s seeded by `git read-tree HEAD`) AND a TEMPORARY object directory (`GIT_OBJECT_DIRECTORY=<tmpdir>` with `GIT_ALTERNATE_OBJECT_DIRECTORIES=<the repo's real objects dir>`), both deleted afterwards. The object-directory redirect is REQUIRED, not an optimization: a plain `git add -A` writes a loose blob for every modified or untracked file into the SHARED object store of the git common dir, which (a) the hardened sandbox profile keeps READ-ONLY for a worker (`host_sandbox_profile`, "the GIT COMMON DIRECTORY is READ-ONLY"), so the key would fail in exactly the lanes that need it, and (b) leaves unreferenced objects behind on every call. Measured at review in a scratch repo with one tracked edit and one untracked file: the redirected form produced the same tree id as the plain form and left the real object count at 3 (plain form: 3 -> 6); `git status --short` was unchanged. Tracked edits AND untracked non-ignored files are both covered; (2) the argv after the interpreter EXCLUDING the worker count `run_full_suite` adds (E-04), so a suite measured at `-n 4` and one at `-n 6` share a key: parallelism does not change what is measured (Project conventions). The repo's `addopts` is NOT a separate component, because `pyproject.toml` is already in the tree id; (3) `sys.version` and `sys.executable`; (4) a digest of the sorted `name==version` list of installed distributions (`importlib.metadata.distributions()`); (5) the sorted `name=value` pairs, absent recorded as absent, of environment variables that change what the suite does: `PYTEST_ADDOPTS` as the CALLER set it (before E-04's own addition), `PYTHONPATH`, `AW_NO_REEXEC`, `NO_COLOR`, `FORCE_COLOR`, `TERM`, and `AW_EXECUTION_ROLE` (an agent turn exports `worker`; `conftest.py` scrubs it today, but a stored PASS must not outlive that scrub silently). Values are hashed into the key and NOT stored in plain text in `components` beyond the variable NAMES and a per-variable short digest, so a cache record never persists an environment value. Return the components alongside the digest so a miss can say WHICH component changed. Fail open: any git or metadata error yields `SuiteKey(None, reason)`, meaning "uncacheable", never a guess.
  - Depends on: E-01
  - Expected outcome: two checkouts at the same commit with no edits produce the same digest; a one-byte edit to a tracked file, a new untracked `tests/test_x.py`, a changed `PYTEST_ADDOPTS` or a different interpreter each produce a different one; an ignored file (`.aw/state/x`) does not.
  - Execution state: performed

- [x] E-03 Add the store in `suite_cache.py`: records live under `<git-common-dir>/aw-suite-cache/<digest>.json` (shared by every linked worktree of the repo, never inside a lane, never tracked), written atomically, holding `{digest, components, passed, exit_code, summary, failures, duration_seconds, recorded_at, worker_count}`. Store a PASS directly. Store a FAILURE only after one confirming re-run reproduces it: re-run the SAME argv and environment restricted to the failing node ids taken from `extract_suite_failures` (the ids passed as positional arguments; the configured `addopts` stays in force, and the marker filter cannot drop an id that the full run just selected), and store with `confirmed: true` only when at least one of those ids fails again. An unconfirmed failure is returned but not stored, so a flake is never replayed. A suite that produced NO parseable failing ids (timeout 124, unrunnable 127, collection error) is NEVER stored. A served FAILURE is ADVISORY ONLY for `aw suite` itself: the runner's seams never serve a cached failure (E-06), because a failure answer re-litigated from cache would bypass spec `25kzda` Section 5.1's rule that a repair claim releases only on an OBSERVED PASSING RE-RUN. Prune records older than 14 days on write. Lookups never raise, and a store write that fails (for example the git common dir is READ-ONLY to a worker under the hardened sandbox profile) is skipped with one stderr note and never fails or alters the suite result. Trust model: a record is an attestation by a same-user process, which is the same trust the run's own per-run `REVALIDATION_CACHE_KEY` cache and the outcome files already carry (GUIDING_PRINCIPLES P15: guard against honest mistakes, not a malicious agent); a cross-machine cache stays out of scope for that reason.
  - Depends on: E-02
  - Expected outcome: a pass is stored and served; a failure that does not reproduce is not stored; a failure with no parseable ids is not stored; a corrupt record is ignored and overwritten; nothing is ever written under the checkout's working tree.
  - Execution state: performed

### Task group 2: the command and the worker bound

- [x] E-04 Add `run_full_suite(checkout, *, argv=SUITE_CHECK_ARGV, use_cache=True, timeout) -> SuiteRunResult` in `suite_cache.py`: compute the key; on a hit print `aw suite: cached result for tree <short> (recorded <when>, <duration>s): <summary>` and return it with `cached: true`; on a miss run the suite with `-n <workers>` where `workers = max(2, cpus // slots)`, `cpus = os.cpu_count() or 2`, and `slots` is read from `AW_SUITE_SLOTS` (a positive integer; anything else falls back to the default with one stderr warning; default `max(1, cpus // 6)`, the same default Order 03's lock uses). The bound is APPENDED to `PYTEST_ADDOPTS` in the child's environment, which overrides the repo's own `addopts` `-n auto` without editing `pyproject.toml` (measured at review with xdist 3.8.0: an `addopts = -n auto` ini plus `PYTEST_ADDOPTS="-n 3"` printed `created: 3/3 workers`; `PYTEST_XDIST_AUTO_NUM_WORKERS` was rejected as the mechanism because an explicit `-n 5` in `addopts` ignored it). Because the repo's `addopts` carries `-q`, pytest prints NO header line, so the bound is evidenced by xdist's `created: N/N workers` line and by the recorded `worker_count`, not by a header. `timeout` defaults to `runner_shared.SUITE_CHECK_TIMEOUT_SECONDS`; an expiry returns exit 124 and is a failure, never stored. Output: in the CLI (E-05) stream the suite's output live to the terminal AND keep a bounded copy (512,000 bytes per stream, the bound `run_suite_check` already uses) for `parse_suite_summary`/`extract_suite_failures`; the library entry point used by the seams captures without streaming, so the seams' existing records are unchanged. Store per E-03. Reuse `parse_suite_summary` and `extract_suite_failures` from `runner_shared` (move them into `suite_cache` and re-export from `runner_shared` under the same names if that avoids an import cycle).
  - Depends on: E-03
  - Expected outcome: a miss runs pytest with xdist reporting `created: N/N workers` for the bounded N; an immediate second call on the unchanged tree returns the cached result without spawning pytest.
  - Execution state: performed

- [x] E-05 Register `aw suite` in `cli.py` and `command_surface.py` as `command_class="mutation"` (it runs a suite and writes the cache; same declaration shape as `integration-lock`, `exit_contract=(0, 1, 2)`) with flags `--no-cache` (always run, still store), `--json`/`--agent` (an `aw.agent/v1` `result` record carrying the structured `SuiteRunResult`), and `--explain` (print the key component NAMES and digests and, on a miss, which component differs from the most recent record for the same HEAD). Exit code: 0 when the suite passed, 1 when it ran and did not pass (including timeout 124 and spawn failure 127, reported with the reason), 2 for a usage refusal (E-09) or a checkout that is not a git repository. The mutation conformance sweep in `tests/test_agent_surface_conformance.py` runs every `mutation` leaf with bare `--agent` in an isolated project, so `aw suite` must emit a valid record there too; ONLY if that cell cannot pass without running a real suite, add a `MUTATION_EXEMPTION_REGISTRY` entry in `tests/conformance_matrix.py` with a kind from that registry's contract and a concrete reason.
  - Depends on: E-04
  - Expected outcome: `aw suite` runs or serves the full suite; `aw suite --agent` emits one valid `aw.agent/v1` `result` record; `python3 -m pytest tests/test_command_surface_declarations.py tests/test_agent_surface_conformance.py tests/test_conformance_matrix_structure.py` passes.
  - Execution state: performed

### Task group 3: adoption by the runner and the agents

- [x] E-09 `aw suite` refuses a narrowed selection: any positional argument, `-k`, `-m`, or an argument containing `::` exits 2 with the message "aw suite runs the FULL suite only; run a narrowed selection with plain python3 -m pytest", runs nothing and writes no cache record, so it never becomes a slower path for quick checks.
  - Depends on: E-05
  - Expected outcome: `aw suite tests/x.py`, `aw suite -k x` and `aw suite t.py::test_a` each exit 2 with that text and the cache directory listing is unchanged.
  - Execution state: performed

- [x] E-06 Route the runner's three seams through `run_full_suite`: `run_suite_check` (primary checkout), `start_suite_baseline`'s spawned argv (the detached baseline checkout: run `python -m agent_workflows suite --agent` there instead of bare pytest, keeping the existing `extract_failures`/`parse_summary` consumption working on its JSON), and the post-merge revalidation `suite_check` call. Each keeps its existing fail-closed semantics: a cache hit on a PASS counts as the measured verdict; a FAILURE is never served from cache to a seam (each seam calls `run_full_suite` with `serve_failures=False`, which treats a cached failure as a miss and RUNS), so every failure a gate acts on, and every `rerun_suite` re-check in the gate-answer follow-up, is an observed run; an uncacheable key just runs. For the baseline, the detached checkout's child prints the `--agent` record on stdout; give `SuiteBaselineRun` a small adapter so `extract_failures`/`parse_summary` receive the record's `summary` and `failures` (or, if simpler, pass the suite's own captured stdout through in the record as `output_tail`) and say which in V-06. Post-merge revalidation keeps its per-run `REVALIDATION_CACHE_KEY` tree cache in front; `run_full_suite` is the measurement behind it. Do NOT change which tree each seam measures. Record `cached: true|false` and the digest on the existing records (`attempt["suite_check"]`, the baseline record, the revalidation record) so a reader can see the reuse.
  - Depends on: E-05
  - Expected outcome: after a fast-forward integration, the next item's baseline at the new tip is served from cache (same tree), visible as `cached: true` on its record.
  - Execution state: performed

- [x] E-07 Update the agent prompts in `runner_shared.py`: (a) the two "Run the required tests and validation commands for this IPD{test_tool}" lines, which live in `build_verifier_prompt` and `_build_audit_prompt` (each under "3. **Run and Verify Test Suite**"), and (b) the execute prompt `build_prompt`, which today carries NO test-command line (its only suite guidance is the "Run every command you need the RESULT of in the FOREGROUND" paragraph), by adding one sentence beside that paragraph. Each says: run narrowed checks with `python3 -m pytest <test_file>`; run the FULL suite with `aw suite` (cached when the tree has not changed, bounded worker count); paste its output. Keep the existing `{test_tool}` substitution.
  - Depends on: E-05
  - Expected outcome: a rendered execute prompt (`build_prompt`), verify prompt (`build_verifier_prompt`) and audit prompt (`_build_audit_prompt`) each contain `aw suite`.
  - Execution state: performed

- [x] E-08 Add `tests/test_suite_cache.py` (behavioral, P16; real `git init` fixture repos with a tiny pytest suite and their own `pytest.ini`, `AW_NO_REEXEC=1`, `PYTHONPATH` at this checkout, and the cache under the FIXTURE's git common dir, never this checkout's): key stability and sensitivity cells per E-02's expected outcome, including the real object count unchanged; pass stored and served (second `python -m agent_workflows suite --agent` reports `cached: true` and does not create the fixture's run-marker file the test writes from inside its test); flaky failure (a test that fails once then passes, via a marker file) is NOT stored; reproducible failure IS stored with `confirmed: true` and is NOT served to a seam call (`serve_failures=False` runs again, the marker proves it); refusal of `tests/x.py`, `-k x` and `t.py::test_a` each exit 2; worker bound (`AW_SUITE_SLOTS=3` with `os.cpu_count` patched to 12 yields `worker_count == 4`, and `-n 4` reaches the child's `PYTEST_ADDOPTS`); the rendered execute, verify and audit prompts contain `aw suite`.
  - Depends on: E-06, E-07
  - Expected outcome: the new test file passes; the stored-and-served cell fails with E-04's lookup disabled.
  - Execution state: performed

- [x] E-10 Docs, CHANGELOG and spec sync: an `aw suite` paragraph in `docs/cli-human-guide.md` (what it caches, the key, `--no-cache`, `AW_SUITE_SLOTS`, the 14-day expiry, that a cached failure is advisory and never reaches a gate); a `- Changed:` bullet in `CHANGELOG.md`'s `## 2.0.0 (pending)` list; and a dated `aw specs note` on spec `25kzda` recording that a driver-run full suite (Section 5.1's per-lane signal and GATE 2's revalidation) may be satisfied by an exact-key cached PASS and never by a cached failure. No em or en dashes in the docs and CHANGELOG text.
  - Depends on: E-08
  - Expected outcome: the doc paragraph and CHANGELOG bullet exist; the spec's `## Workflow history` carries the note.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The run's existing revalidation cache (`REVALIDATION_CACHE_KEY`, "keyed on the merged TREE id, which is the honest identity of the thing that was tested") is per-run state; this plan adds the cross-run equivalent and keeps that rationale.
- `SUITE_CHECK_ARGV` is a BARE `python3 -m pytest`; the repo contract forbids `-n0`, a second `-q`, and `-p no:randomly` because they change what is measured. Overriding `-n N` via `PYTEST_ADDOPTS` changes parallelism only, not selection or randomization.
- Machine-local state outside the repo tree: the git common dir is shared by every worktree (`runner_shared.git_common_dir`), which is what lets lanes share results.
- `aw test <ipd> -- <cmd>` already exists for tree-bound EVIDENCE capture; `aw suite` is a different verb (run-or-serve the full suite) and does not replace it.
- Behavioral tests only (P16); run the suite bare.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | Agent full suites dominate cost. | 1,258 full-suite tool calls in October session logs (1,047 executor, 211 verifier), median 216s, p90 622s, 91.5h total. |
| F-02 | Exact-tree reuse exists but is modest across arbitrary lanes. | 322 baselines: 284 distinct whole trees, 261 distinct code trees (61 repeats, 19%). |
| F-03 | Some reuse is guaranteed. | Fast-forward integration makes `main`'s tree equal the lane's tested tree; the next baseline is at that tip. |
| F-04 | Oversubscription. | `pyproject.toml` `addopts`: `-n auto`; seven drivers on a 12-core host on 2026-10-12 each started 12-worker suites (load 75-88). |
| F-05 | Static per-file selection does not help. | Median test file transitively imports 154 of 186 modules; a one-file step invalidates 92% of test files. Hence whole-tree keys here, coverage-level selection in Order 04. |

## Proposed changes (ordered, validatable)

1. Key (E-02) and store (E-03).
2. `run_full_suite` with the worker bound (E-04) and the `aw suite` command (E-05).
3. Runner seams (E-06) and agent prompts (E-07).
4. Tests, docs, CHANGELOG (E-08).

## Deferred / out of scope (with reason)

- Caching narrowed runs: quick checks are cheap and their selection is part of the key's complexity; not worth it.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- A cross-machine cache: needs a trust model (a stored PASS is an attestation).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Enforcing that agents use `aw suite` (for example by shimming `pytest`): prompt guidance first; measure adoption in Order 04's data before adding enforcement.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

New `tests/test_suite_cache.py` (E-08); the existing seam tests must still pass: `tests/test_capture_command_contract.py` (`test_run_suite_check_consumer_contract`), `tests/test_oc_runipd.py` (including `WorktreeIsolationTests.test_integration_gate_suite_check_runs_in_primary_checkout`), `tests/test_deferred_reattempt_revalidation.py`, `tests/test_hook_and_suite_fix_it.py`, `tests/test_suite_baseline_direction.py`, `tests/test_suite_baseline_mode_gate.py` (from Order 01), and the CLI surface tests named in E-05; bare suite against E-01. (`tests/test_suite_baseline.py`, named here before review, was deleted by `19313eed7`.) Invariants: (I1) a seam never acts on a cached failure; (I2) a cached PASS needs an exact key over tree, argv, interpreter, distributions and env; (I3) the key computation writes nothing to the real index or object store; (I4) `run_suite_check` still runs in the PRIMARY checkout.

## Spec / documentation sync

`docs/cli-human-guide.md` and `CHANGELOG.md` (the docs E-item). Spec `25kzda` is declared in Scope-Paths and gets a dated `aw specs note` (no normative text rewritten) because Section 5.1 and GATE 2 speak of the driver "re-running the full suite"; letting an exact-key cached PASS answer that question is a change to how that contract is met, and it must be visible in the spec's history rather than discovered from code. The bare-argv contract is preserved (worker count is not selection).

## Open questions

### OQ-01: Is a cached PASS acceptable as the integration gate's verdict?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED yes, for an exact key and a PASS only (a seam never acts on a cached failure, E-06). The gate's question is "is this tree green"; the key covers the tree (tracked plus untracked), the command, the interpreter, the installed packages and the behavior-changing env. The existing per-run `REVALIDATION_CACHE_KEY` already serves one measurement per tree within a run; this extends the same identity across runs. Failures are never served unless confirmed.

### OQ-02: What about tests that read state outside the key (time, network, `.aw/state`)?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED as an accepted, documented limit (documented in the docs E-item): the default selection deselects `slow` and `livecorpus`; conftest sandboxes `AW_HOME`/`XDG_CONFIG_HOME` per test; and a time-dependent test that passes once and fails later would be a flaky test regardless. `--no-cache` is the escape hatch, and stored records expire after 14 days.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-change bare-suite summary line and failing node ids.
  - Observed evidence:
    Ran bare `python3 -m pytest` at starting HEAD `21b8df8a981b409125f4edd78f15348de02e1875` before any edit:
    ```text
    $ python3 -m pytest
    NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    8301 passed, 4 skipped, 18 xfailed, 3 warnings in 484.06s (0:08:04)
    ```
    Failing node ids: none (`0` failed, exit code `0`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of a snippet printing `suite_key(...).digest` for: a clean fixture, a second clean checkout of the same commit, the same after a one-byte tracked edit, after adding an untracked test file, after adding an ignored file, and with `PYTEST_ADDOPTS` set, showing exactly the expected equal/different pattern; plus `git -C <fixture> status --short` and the count of files under `$(git -C <fixture> rev-parse --git-path objects)` before and after, showing the real index and object store untouched.
  - Observed evidence:
    ```text
    === V-02 ===
    clean_1       = a6c31f09e20fd940a351a56de204646a6728e4020a8618bbd975ab6a66b61d18
    clean_2       = a6c31f09e20fd940a351a56de204646a6728e4020a8618bbd975ab6a66b61d18 (equal=True)
    ignored_added = a6c31f09e20fd940a351a56de204646a6728e4020a8618bbd975ab6a66b61d18 (equal=True)
    tracked_edit  = fa1273f9f93a246832398f43c6a4e604d8a705e5496737a34e6b68023d2709d1 (equal=False)
    untracked_add = 16dcbee10734cc49e3616b6326f95246ac3085f33e326d09abc4c3541ef5beec (equal=False)
    pytest_addopts= 2b99cd82eb1ffc67a79f6eb8f097c2aaa11862cad4cf9148fbcb5073eda76b55 (equal=False)
    git status --short before='' after=''
    object file count before=6 after=6
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted E-08 cells for pass-stored, flaky-not-stored and reproducible-failure-stored, plus a `ls <git-common-dir>/aw-suite-cache/` listing and one record's JSON.
  - Observed evidence:
    ```text
    $ python3 -m pytest tests/test_suite_cache.py -k "test_pass_stored_and_served or test_flaky_failure_is_not_stored or test_reproducible_failure_stored_and_not_served_to_seam or test_collection_error_and_corrupt_or_expired_records" -v
    tests/test_suite_cache.py::test_pass_stored_and_served PASSED            [ 25%]
    tests/test_suite_cache.py::test_flaky_failure_is_not_stored PASSED       [ 50%]
    tests/test_suite_cache.py::test_reproducible_failure_stored_and_not_served_to_seam PASSED [ 75%]
    tests/test_suite_cache.py::test_collection_error_and_corrupt_or_expired_records PASSED [100%]
    ============================== 4 passed in 21.84s ==============================

    $ ls "$(git rev-parse --git-common-dir)/aw-suite-cache/"
    253028607a5b16bce9f56d09130a17043adba4f7c192fec3338462b7b92d2155.json

    $ cat "$(git rev-parse --git-common-dir)/aw-suite-cache/253028607a5b16bce9f56d09130a17043adba4f7c192fec3338462b7b92d2155.json"
    {
      "components": {
        "argv": "b78826e4dd491a00b3df7897f1e26fddf4fdfa270d72aaa3f3655a13249e418a",
        "distributions": "2173a1ea6d83c50ff6bfbfa54c995ec427a89267cc3a0aecd5c421a32fa1fe8e",
        "env": "ce6af7314a072d59a6fddb1045ebcc4331712f8742e8e25607a847300e159605",
        "env_vars": {
          "AW_EXECUTION_ROLE": "87eba76e7f316453",
          "AW_NO_REEXEC": "absent",
          "FORCE_COLOR": "absent",
          "NO_COLOR": "absent",
          "PYTEST_ADDOPTS": "absent",
          "PYTHONPATH": "cdb4ee2aea69cc6a",
          "TERM": "ac996ae492f9a987"
        },
        "interpreter": "986d48790bddb2c3c5d6284dac4c576457773db3fa82653855adaaca620b5af3",
        "tree": "9f97e12e2ece0fc7c48183fafcf2bb9f89410506"
      },
      "confirmed": true,
      "digest": "253028607a5b16bce9f56d09130a17043adba4f7c192fec3338462b7b92d2155",
      "duration_seconds": 438.595,
      "exit_code": 0,
      "failures": [],
      "head": "21b8df8a981b409125f4edd78f15348de02e1875",
      "passed": true,
      "recorded_at": "2026-10-14T02:38:17Z",
      "summary": "8313 passed, 4 skipped, 18 xfailed, 3 warnings in 436.43s (0:07:16)",
      "worker_count": 6
    }
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted terminal output of `aw suite` twice in this checkout on an unchanged tree: the first showing xdist's `created: N/N workers` line with the bounded N and the suite summary, the second showing the `aw suite: cached result` line, with `/usr/bin/time` elapsed for each (code path: `run_full_suite` lookup hit).
  - Observed evidence:
    ```text
    $ /usr/bin/time -f "elapsed=%E" env PYTHONPATH=. aw suite && /usr/bin/time -f "elapsed=%E" env PYTHONPATH=. aw suite
    bringing up nodes...
    created: 6/6 workers
    bringing up nodes...
    ...
    NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    8313 passed, 4 skipped, 18 xfailed, 3 warnings in 436.43s (0:07:16)
    elapsed=7:19.69
    aw suite: cached result for tree 9f97e12e2ece (recorded 2026-10-14T02:38:17Z, 438.60s): 8313 passed, 4 skipped, 18 xfailed, 3 warnings in 436.43s (0:07:16)
    elapsed=0:00.95
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `aw suite --help`, `aw suite --explain --agent` output (one valid `aw.agent/v1` record), and the pasted passing run of the three CLI surface test files named in E-05.
  - Observed evidence:
    ```text
    $ PYTHONPATH=. aw suite --help
    usage: aw suite [-h] [--color] [--no-color] [-i | --no-interactive] [--agent]
                    [--json] [--fields FIELDS] [--verbose] [--dir DIR]
                    [--no-cache] [--explain]

    options:
      -h, --help        show this help message and exit
      --color           Force ANSI color output even when stdout is not a TTY.
      --no-color        Disable ANSI color output (equivalent to NO_COLOR=1).
      -i, --interactive
                        Allow interactive prompts on a TTY when inputs are omitted
                        (default when stdin/stdout are a TTY and not in agent/json
                        mode).
      --no-interactive  Never prompt; fail closed with an actionable hint when
                        required inputs are missing (equivalent to
                        AW_NONINTERACTIVE=1). Cannot be combined with --
                        interactive.
      --agent           Machine-readable output (aw.agent/v1 JSONL).
      --json            Emit full structured JSON representation.
      --fields FIELDS   Comma-separated field projection for --agent output
                        (envelope fields are preserved).
      --verbose         Include full nested diagnostics, change details, and
                        evidence dictionaries.
      --dir DIR         Repo root (default: current directory).
      --no-cache        Always run the full suite even on a cache hit, and store
                        the new result.
      --explain         Print the cache key components and digests, and on a miss
                        which component differed from the most recent record for
                        the same HEAD.

    $ PYTHONPATH=. aw suite --explain --agent
    {"schema":"aw.agent/v1","kind":"result","cmd":"suite","command":"suite","outcome":"ok","exit":0,"verified":true,"complete":true,"cacheable":true,"cached":true,"digest":"253028607a5b16bce9f56d09130a17043adba4f7c192fec3338462b7b92d2155","head":"21b8df8a981b409125f4edd78f15348de02e1875","components":{"tree":"9f97e12e2ece0fc7c48183fafcf2bb9f89410506","argv":"b78826e4dd491a00b3df7897f1e26fddf4fdfa270d72aaa3f3655a13249e418a","interpreter":"986d48790bddb2c3c5d6284dac4c576457773db3fa82653855adaaca620b5af3","distributions":"2173a1ea6d83c50ff6bfbfa54c995ec427a89267cc3a0aecd5c421a32fa1fe8e","env":"ce6af7314a072d59a6fddb1045ebcc4331712f8742e8e25607a847300e159605","env_vars":{"AW_EXECUTION_ROLE":"87eba76e7f316453","AW_NO_REEXEC":"absent","FORCE_COLOR":"absent","NO_COLOR":"absent","PYTEST_ADDOPTS":"absent","PYTHONPATH":"cdb4ee2aea69cc6a","TERM":"ac996ae492f9a987"}},"compared_digest":"253028607a5b16bce9f56d09130a17043adba4f7c192fec3338462b7b92d2155","compared_head":"21b8df8a981b409125f4edd78f15348de02e1875","differing_components":[],"reason":"","diagnostics":[]}

    $ python3 -m pytest tests/test_command_surface_declarations.py tests/test_agent_surface_conformance.py tests/test_conformance_matrix_structure.py
    ........................................................................ [ 76%]
    ......................                                                   [100%]
    94 passed in 43.01s
    ```
    Note: `tests/conformance_matrix.py` was left unmodified because `aw suite --agent` in the isolated mutation conformance sweep succeeds and emits a valid `aw.agent/v1` `result` record without needing an exemption entry.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the `git diff` of the three seams, plus a test or scripted run (code path: `run_suite_check` / `start_suite_baseline` / `make_integration_validation_runner` -> `run_full_suite`) showing a record with `cached: true` for a seam measuring an already-measured PASSING tree, `cached: false` otherwise, and a seam measuring a tree with a stored confirmed FAILURE running again (`cached: false`); which baseline-consumption option was chosen; the existing seam tests named in Required tests passing (pasted).
  - Observed evidence:
    Baseline-consumption option chosen: gave `SuiteBaselineRun` a small JSON adapter (`_unpack_suite_baseline_agent_output` in `agent_workflows/runner_shared.py`) that parses the `--agent` JSON record printed by `python -m agent_workflows suite --agent`, extracts `cached` and `digest`, and synthesizes the `failures` + `summary` text so `extract_failures` and `parse_summary` receive the record's `summary` and `failures` directly while fallback raw-pytest output continues to work for unit tests passing custom `argv`.
    Seam diff excerpt (`git diff -U1 agent_workflows/runner_shared.py`):
    ```diff
    @@ -38748,2 +38748,4 @@ class SuiteBaseline:
         worktree_existed_at_start: bool = False
    +    cached: bool = False
    +    digest: str | None = None
    @@ -38768,2 +38770,4 @@ class SuiteBaseline:
                 "worktree_existed_at_start": self.worktree_existed_at_start,
    +            "cached": self.cached,
    +            "digest": self.digest,
             }
    @@ -38983,4 +39037,16 @@ def start_suite_baseline(
    -    proc = subprocess.Popen(
    -        list(argv),
    +    spawn_argv = list(argv)
    +    if tuple(spawn_argv) == tuple(SUITE_CHECK_ARGV):
    +        spawn_argv = [
    +            spawn_argv[0],
    +            "-m",
    +            "agent_workflows",
    +            "suite",
    +            "--agent",
    +        ]
    +    proc = subprocess.Popen(
    +        spawn_argv,
             cwd=str(checkout),
    @@ -43560,2 +43590,4 @@ class SuiteCheckResult(NamedTuple):
         failures: tuple[str, ...] = ()
    +    cached: bool = False
    +    digest: str | None = None
    @@ -43625,16 +43652,11 @@ def run_suite_check(
    -        tool_event, _envelope = run_evidence.capture_command(
    +        res = suite_cache.run_full_suite(
                 repo_dir,
                 argv=list(SUITE_CHECK_ARGV),
    +            use_cache=True,
    +            serve_failures=False,
                 timeout=timeout,
    +            stream=False,
    +            run_id=run_id,
             )
    @@ -43741,2 +43747,4 @@ def _record_revalidation(
                 "failures": list(failures),
    +            "cached": bool(cached),
    +            "digest": digest,
             },
    ```
    Seam cache hit/miss and confirmed-failure re-run verification (`test_runner_seams_cache_hit_miss_and_failure_rerun` in `tests/test_suite_cache.py`, driving `run_suite_check`, `start_suite_baseline`, and `make_integration_validation_runner` -> `run_full_suite`):
    ```text
    $ python3 -m pytest tests/test_suite_cache.py -k test_runner_seams_cache_hit_miss_and_failure_rerun -v
    tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun PASSED [100%]
    ============================== 1 passed in 19.42s ==============================
    ```
    Existing seam tests named in Required tests:
    ```text
    $ python3 -m pytest tests/test_capture_command_contract.py tests/test_oc_runipd.py tests/test_deferred_reattempt_revalidation.py tests/test_hook_and_suite_fix_it.py tests/test_suite_baseline_direction.py tests/test_suite_baseline_mode_gate.py
    ........................................................................ [ 34%]
    ........................................................................ [ 68%]
    .................................................................        [100%]
    209 passed in 30.78s
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted excerpts of a rendered execute (`build_prompt`), verify (`build_verifier_prompt`) and audit (`_build_audit_prompt`) prompt each showing the `aw suite` instruction.
  - Observed evidence:
    ```text
    [build_prompt] Run narrowed checks with `python3 -m pytest <test_file>`; run the FULL suite with `aw suite` (cached when the tree has not changed, bounded worker count); paste its output.
    [build_verifier_prompt] - Run the required tests and validation commands for this IPD (e.g. run narrowed checks with `python3 -m pytest <test_file>`; run the FULL suite with `aw suite`, which serves a cached result when the tree has not changed and runs with a bounded worker count otherwise; paste its output).
    [_build_audit_prompt] - Run the required tests and validation commands for this IPD (e.g. run narrowed checks with `python3 -m pytest <test_file>`; run the FULL suite with `aw suite`, which serves a cached result when the tree has not changed and runs with a bounded worker count otherwise; paste its output).
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: pasted passing `python3 -m pytest tests/test_suite_cache.py`; pasted failing stored-and-served cell with the lookup disabled (then restored); pasted post-change bare suite summary with no new failing node id versus V-01.
  - Observed evidence:
    Passing `tests/test_suite_cache.py`:
    ```text
    $ python3 -m pytest tests/test_suite_cache.py
    .........                                                                [100%]
    9 passed in 28.90s
    ```
    With lookup disabled in `agent_workflows/suite_cache.py` (`read_cached_record` returning `None`) and then restored:
    ```text
    $ python3 -m pytest tests/test_suite_cache.py
    ..FFFF...                                                                [100%]
    =================================== FAILURES ===================================
    _________________________ test_pass_stored_and_served __________________________
        second = json.loads(second_proc.stdout.strip().splitlines()[-1])
        assert second["exit"] == 0
    >   assert second["cached"] is True
    E   assert False is True
    tests/test_suite_cache.py:258: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_suite_cache.py::test_runner_seams_cache_hit_miss_and_failure_rerun
    FAILED tests/test_suite_cache.py::test_collection_error_and_corrupt_or_expired_records
    FAILED tests/test_suite_cache.py::test_pass_stored_and_served - assert False ...
    FAILED tests/test_suite_cache.py::test_reproducible_failure_stored_and_not_served_to_seam
    4 failed, 5 passed in 13.56s
    ```
    Post-change full suite summary (no new failing node id versus V-01; 0 failed):
    ```text
    NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    8313 passed, 4 skipped, 18 xfailed, 3 warnings in 436.43s (0:07:16)
    ```
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: pasted `aw suite tests/test_cli.py; echo rc=$?`, `aw suite -k x; echo rc=$?` and `aw suite tests/test_cli.py::x; echo rc=$?` each showing the refusal text and `rc=2`, plus `ls <git-common-dir>/aw-suite-cache/ | wc -l` before and after showing no new record; and the matching E-08 refusal cells passing.
  - Observed evidence:
    ```text
    $ ls "$(git rev-parse --git-common-dir)/aw-suite-cache/" | wc -l
    1
    $ PYTHONPATH=. aw suite tests/test_cli.py; echo rc=$?
    aw suite runs the FULL suite only; run a narrowed selection with plain python3 -m pytest
    rc=2
    $ PYTHONPATH=. aw suite -k x; echo rc=$?
    aw suite runs the FULL suite only; run a narrowed selection with plain python3 -m pytest
    rc=2
    $ PYTHONPATH=. aw suite tests/test_cli.py::x; echo rc=$?
    aw suite runs the FULL suite only; run a narrowed selection with plain python3 -m pytest
    rc=2
    $ ls "$(git rev-parse --git-common-dir)/aw-suite-cache/" | wc -l
    1
    $ python3 -m pytest tests/test_suite_cache.py -k test_narrowed_selection_refusals -v
    tests/test_suite_cache.py::test_narrowed_selection_refusals PASSED       [100%]
    ============================== 1 passed in 3.21s ===============================
    ```
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: `git diff docs/cli-human-guide.md CHANGELOG.md` pasted with no em/en dash (`grep -nP '[\x{2013}\x{2014}]'` over the added lines returns nothing), and the pasted new `## Workflow history` line of spec `25kzda` plus `aw specs check` output.
  - Observed evidence:
    ```text
    $ git diff docs/cli-human-guide.md CHANGELOG.md
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 32e48c456..20f087d21 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Changed: added `aw suite` (`agent_workflows/suite_cache.py`) as the single full-suite entry point with a tree-keyed result cache in `<git-common-dir>/aw-suite-cache` (14-day expiry, `--no-cache` bypass, `--explain` key breakdown) and a bounded xdist worker count (`max(2, cpus // slots)` from `AW_SUITE_SLOTS`, default `max(1, cpus // 6)`), and routed the runner's `run_suite_check`, `start_suite_baseline`, and `make_integration_validation_runner` seams through `run_full_suite` so an exact-key cached pass is reused across lanes and checkouts while a cached failure is never served to a gate.
     - Added: `aw checkup` command and periodic CI health checks with configurable interval (`ci_checkup_interval_commits`, default 100), workflow (`ci_checkup_workflow`, default `tests.yml`), and branch (`ci_checkup_branch`, default `main`) in `project.json`, showing checkup status in run start and run end banners, `aw attention`, and `aw doctor`.
    diff --git a/docs/cli-human-guide.md b/docs/cli-human-guide.md
    index 840844f30..8e2674890 100644
    --- a/docs/cli-human-guide.md
    +++ b/docs/cli-human-guide.md
    @@ -116,6 +116,7 @@ in your own scripts for "the command could not run at all".
     | Only the fields you care about (agent) | `aw check plans --agent --fields findings` |
     | Bounded output with a continuation hint | `aw find plans --agent --limit 20` |
     | Launch an IPD with a saved model alias | `aw run as gem <selector>` |
    +| Run the full test suite with tree-keyed caching | `aw suite` |

     ## Naming a model once instead of on every run

    @@ -126,3 +127,8 @@ made default for you, and `aw setup` offers to set one up with a question that d
     [Runner profiles](runner-profiles.md) is the complete reference: every command form, the exact
     per-field override precedence, storage and privacy, and what happens on a bad or missing
     profile.
    +
    +## Running the full test suite (`aw suite`)
    +
    +`aw suite` runs or serves the repository's bare full `pytest` suite with a bounded xdist worker count (`max(2, cpus // slots)` where `slots` comes from `AW_SUITE_SLOTS`, default `max(1, cpus // 6)`) and caches passing verdicts and confirmed reproducible failures in `<git-common-dir>/aw-suite-cache/<digest>.json` with a 14-day expiry. The cache key (`digest`) is a SHA-256 over the working-tree git tree (including tracked edits and untracked non-ignored files), the normalized argv after the interpreter (excluding `-n`), `sys.version` and `sys.executable`, the sorted `name==version` installed distributions, and behavior-changing environment variables (`PYTEST_ADDOPTS`, `PYTHONPATH`, `AW_NO_REEXEC`, `NO_COLOR`, `FORCE_COLOR`, `TERM`, and `AW_EXECUTION_ROLE`; inspect with `aw suite --explain`). State outside the key (wall clock, network, or `.aw/state`) is bounded by default marker deselection (`slow` and `livecorpus`), per-test `AW_HOME`/`XDG_CONFIG_HOME` sandboxing, and the 14-day record expiry; pass `--no-cache` to force a fresh run and update the stored entry. A cached failure is advisory for `aw suite` only and never reaches a runner gate (every gate failure and gate re-check is always an observed live run).
    +

    $ git diff docs/cli-human-guide.md CHANGELOG.md | grep -nP '^\+.*[\x{2013}\x{2014}]'
    (no matches)

    $ git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    +- 2026-10-14 note (aw specs): IPD 0o0wt2 (suiteeff-02): Section 5.1's per-lane suite check (run_suite_check), the pre-work baseline (start_suite_baseline), and GATE 2's post-merge revalidation (make_integration_validation_runner) route through aw suite (agent_workflows/suite_cache.py:run_full_suite) and may be satisfied by an exact-key cached PASS in <git-common-dir>/aw-suite-cache/<digest>.json; a cached failure is advisory only and is never served to a gate.

    $ PYTHONPATH=. aw specs check
    aw specs check: all specs conform. 40 specs checked.
    ```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its open questions (OQ-01, OQ-02) are resolved. Depends on `9ec94f` executed. Run `aw ipd begin 0o0wt2` before the first edit. Scope fence: `- Scope-Paths:` declares every path this plan expects to change, including the spec it annotates; an out-of-scope edit is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`; `tests/conformance_matrix.py` may legitimately be unmodified, per E-05). Every `V-*` MUST carry the ACTUAL pasted runner output; never claim a pass that was not run. Commit only Scope-Paths via `aw commit 0o0wt2 -- <paths>`; never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns the terminal transition and the executor does NOT run `aw ipd finalize`; run by hand, finish with `aw ipd finalize 0o0wt2` once `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status: executed` and never `git mv` the file.
