# IPD: Add aw suite: one full-suite entry point with a tree-keyed result cache and a bounded worker count

- Date: 2026-10-12
- Kind: child
- Concern: Full suites run with no memory of identical prior runs and at `-n auto` regardless of how many other suites are running. Measured over October: 1,258 agent full-suite invocations (median 216s, p90 622s, 91.5h total); of the 322 runner baselines, 61 (19%) were at a code tree (`agent_workflows`, `tests`, `conftest.py`, `pyproject.toml`, `tools`) already seen; and three handoffs are exact repeats BY CONSTRUCTION: a fast-forward integration leaves `main`'s tree equal to the lane's last-tested tree, the next item's baseline is taken at the tip the integration gate just measured, and lanes dispatched from one base share it. The runner has three suite seams that each spawn their own pytest: `runner_shared.run_suite_check` (argv `SUITE_CHECK_ARGV`), `start_suite_baseline` (same argv in a detached checkout), and post-merge revalidation (`make_integration_validation_runner` -> injected `suite_check` in the materialized merge result). Agents are told only "e.g. `python3 -m pytest <test_file> -v`" (`runner_shared` execute/verify prompt templates, "Run the required tests and validation commands for this IPD").
- Scope: IN: a new `agent_workflows/suite_cache.py` (key computation, store, lookup) and a new `aw suite` command that runs the repository's bare full suite through it with a bounded worker count; route the three runner seams through the same library function; update the execute and verify prompt templates to direct full-suite runs to `aw suite`; docs and CHANGELOG. OUT: narrowed runs (`aw suite` refuses a test selection and points at plain pytest, so quick checks stay fast and uncached); the machine-wide lock (Order 03); test selection (Order 04); changing `pyproject.toml` `addopts` for humans.
- Scope-Paths: agent_workflows/suite_cache.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/runner_shared.py, tests/test_suite_cache.py, docs/cli-human-guide.md, CHANGELOG.md
- Item-Dependencies: executed:9ec94f
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0o0wt2

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 02 of Set `suiteeff` from backlog `58x9mw`.

## Goal

Every full-suite run, by a runner or an agent, goes through one command that returns the stored result when the exact same code was already measured, and otherwise runs with a worker count sized to the machine instead of to all of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the cache key and store

- [ ] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` before the first edit; record its summary line and failing node ids.
  - Depends on: none
  - Expected outcome: a recorded summary line and failing-node-id list.
  - Execution state: pending

- [ ] E-02 Create `agent_workflows/suite_cache.py` with `suite_key(checkout: Path, argv: Sequence[str]) -> SuiteKey`. The key is a SHA-256 over: (1) the WORKING-TREE tree id, computed without touching the real index by `git add -A` into a temporary index (`GIT_INDEX_FILE=<tmp>`, seeded from `HEAD`) followed by `git write-tree`, so tracked edits AND untracked non-ignored files are both covered; (2) the argv after the interpreter, plus the effective `addopts` read from `pyproject.toml`; (3) `sys.version` and `sys.executable`; (4) a digest of the sorted `name==version` list of installed distributions (`importlib.metadata.distributions()`); (5) the sorted values of environment variables that change what the suite does (`PYTEST_ADDOPTS`, `PYTHONPATH`, `AW_NO_REEXEC`, `NO_COLOR`, `FORCE_COLOR`, `TERM`). Return the components alongside the digest so a miss can say WHICH component changed. Fail open: any git or metadata error yields `SuiteKey(None, reason)`, meaning "uncacheable", never a guess.
  - Depends on: E-01
  - Expected outcome: two checkouts at the same commit with no edits produce the same digest; a one-byte edit to a tracked file, a new untracked `tests/test_x.py`, a changed `PYTEST_ADDOPTS` or a different interpreter each produce a different one; an ignored file (`.aw/state/x`) does not.
  - Execution state: pending

- [ ] E-03 Add the store in `suite_cache.py`: records live under `<git-common-dir>/aw-suite-cache/<digest>.json` (shared by every linked worktree of the repo, never inside a lane, never tracked), written atomically, holding `{digest, components, passed, exit_code, summary, failures, duration_seconds, recorded_at, worker_count}`. Store a PASS directly. Store a FAILURE only after one confirming re-run of the failing node ids reproduces it (`python -m pytest <ids> -o addopts="" -q -p no:randomly` is NOT used; re-run with the same addopts minus the marker filter, restricted to the ids), recording `confirmed: true`; an unconfirmed failure is returned but not stored, so a flake is never replayed. Prune records older than 14 days on write. Lookups never raise.
  - Depends on: E-02
  - Expected outcome: a pass is stored and served; a failure that does not reproduce is not stored; a corrupt record is ignored and overwritten.
  - Execution state: pending

### Task group 2: the command and the worker bound

- [ ] E-04 Add `run_full_suite(checkout, *, argv=SUITE_CHECK_ARGV, use_cache=True, timeout) -> SuiteRunResult` in `suite_cache.py`: compute the key; on a hit print `aw suite: cached result for tree <short> (recorded <when>, <duration>s): <summary>` and return it with `cached: true`; on a miss run the suite with `-n <workers>` where `workers = max(2, os.cpu_count() // slots)` and `slots` is read from `AW_SUITE_SLOTS` (default `max(1, os.cpu_count() // 6)`, the same default Order 03's lock uses), passing it through `PYTEST_ADDOPTS` appended so the repo's own `addopts` (`-n auto`) is overridden without editing `pyproject.toml`; stream the suite's output unchanged so a human sees progress; store per E-03. Reuse `parse_suite_summary` and `extract_suite_failures` from `runner_shared` (move them into `suite_cache` and re-export from `runner_shared` under the same names if that avoids an import cycle).
  - Depends on: E-03
  - Expected outcome: a miss runs pytest with the bounded `-n` visible in its header line; an immediate second call returns the cached result in under 5 seconds.
  - Execution state: pending

- [ ] E-05 Register `aw suite` in `cli.py` and `command_surface.py` (class read-only for the cache-hit path is false because it runs a suite; declare it `mutation` like `integration-lock`, `exit_contract=(0, 1, 2)`): flags `--no-cache` (always run, still store), `--json`/`--agent` (the structured `SuiteRunResult`), `--explain` (print the key components and, on a miss, which component differs from the most recent record for the same HEAD). It refuses positional test selections, `-k` or `::` with exit 2 and the message "aw suite runs the FULL suite only; run a narrowed selection with plain python3 -m pytest", so it never becomes a slower path for quick checks. Exit code mirrors the suite (0 pass, 1 fail), 2 for refusal or an unrunnable suite.
  - Depends on: E-04
  - Expected outcome: `aw suite` runs or serves the full suite; `aw suite tests/x.py` exits 2 with the refusal text.
  - Execution state: pending

### Task group 3: adoption by the runner and the agents

- [ ] E-06 Route the runner's three seams through `run_full_suite`: `run_suite_check` (primary checkout), `start_suite_baseline`'s spawned argv (the detached baseline checkout: run `python -m agent_workflows suite --agent` there instead of bare pytest, keeping the existing `extract_failures`/`parse_summary` consumption working on its JSON), and the post-merge revalidation `suite_check` call. Each keeps its existing fail-closed semantics: a cache hit on a PASS counts as the measured verdict; a FAILURE (cached-confirmed or fresh) is still a failure; an uncacheable key just runs. Do NOT change which tree each seam measures. Record `cached: true|false` and the digest on the existing records (`attempt["suite_check"]`, the baseline record, the revalidation record) so a reader can see the reuse.
  - Depends on: E-05
  - Expected outcome: after a fast-forward integration, the next item's baseline at the new tip is served from cache (same tree), visible as `cached: true` on its record.
  - Execution state: pending

- [ ] E-07 Update the execute and verify prompt templates in `runner_shared.py` (the two "Run the required tests and validation commands for this IPD" lines and the verifier's "Run and Verify Test Suite" step) to say: run narrowed checks with `python3 -m pytest <test_file>`; run the FULL suite with `aw suite` (cached when the tree has not changed, bounded worker count); paste its output. Keep the existing `{test_tool}` substitution.
  - Depends on: E-05
  - Expected outcome: a rendered execute prompt and a rendered verify prompt both contain `aw suite`.
  - Execution state: pending

- [ ] E-08 Tests and docs. Add `tests/test_suite_cache.py` (behavioral, P16; real `git init` fixture repos with a tiny pytest suite, `AW_NO_REEXEC=1`, `PYTHONPATH` at this checkout): key stability and sensitivity cells per E-02's expected outcome; pass stored and served (second `python -m agent_workflows suite --agent` reports `cached: true` and does not create the fixture's run-marker file the test writes from inside its test); flaky failure (a test that fails once then passes, via a marker file) is NOT stored; reproducible failure IS stored with `confirmed: true`; refusal of `tests/x.py` exits 2; worker bound (`AW_SUITE_SLOTS=3` on a stubbed `os.cpu_count()` of 12 yields `-n 4` in the recorded `worker_count`); a rendered execute prompt contains `aw suite`. Add an `aw suite` paragraph to `docs/cli-human-guide.md` and a `- Changed:` bullet to `CHANGELOG.md`; no em or en dashes.
  - Depends on: E-06, E-07
  - Expected outcome: the new test file passes; the stored-and-served cell fails with E-04's lookup disabled.
  - Execution state: pending

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
- A cross-machine cache: needs a trust model (a stored PASS is an attestation).
- Enforcing that agents use `aw suite` (for example by shimming `pytest`): prompt guidance first; measure adoption in Order 04's data before adding enforcement.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

New `tests/test_suite_cache.py` (E-08); existing `tests/test_suite_baseline.py` and the runner suites covering `run_suite_check` and revalidation must still pass; bare suite against E-01.

## Spec / documentation sync

`docs/cli-human-guide.md` and `CHANGELOG.md` (E-08). No spec amendment: no spec governs how the suite is invoked beyond the bare-argv contract, which is preserved (worker count is not selection).

## Open questions

### OQ-01: Is a cached PASS acceptable as the integration gate's verdict?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED yes, for an exact key only. The gate's question is "is this tree green"; the key covers the tree (tracked plus untracked), the command, the interpreter, the installed packages and the behavior-changing env. The existing per-run `REVALIDATION_CACHE_KEY` already serves one measurement per tree within a run; this extends the same identity across runs. Failures are never served unless confirmed.

### OQ-02: What about tests that read state outside the key (time, network, `.aw/state`)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as an accepted, documented limit: the default selection deselects `slow` and `livecorpus`; conftest sandboxes `AW_HOME`/`XDG_CONFIG_HOME` per test; and a time-dependent test that passes once and fails later would be a flaky test regardless. `--no-cache` is the escape hatch, and stored records expire after 14 days.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change bare-suite summary line and failing node ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a snippet printing `suite_key(...).digest` for: a clean fixture, the same after a one-byte tracked edit, after adding an untracked test file, after adding an ignored file, and with `PYTEST_ADDOPTS` set, showing exactly the expected equal/different pattern; plus `git -C <fixture> status --short` before and after showing the real index untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted E-08 cells for pass-stored, flaky-not-stored and reproducible-failure-stored, plus a `ls <git-common-dir>/aw-suite-cache/` listing and one record's JSON.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted terminal output of `aw suite` twice in this checkout on an unchanged tree: the first showing pytest's header with the bounded `-n` value and its summary, the second showing the `aw suite: cached result` line, with `/usr/bin/time` elapsed for each.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `aw suite --help`, `aw suite tests/test_cli.py; echo rc=$?` (refusal, rc=2), and `aw suite --explain --agent` output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the `git diff` of the three seams, plus a test or scripted run (code path: `run_suite_check` / `start_suite_baseline` / `make_integration_validation_runner` -> `run_full_suite`) showing a record with `cached: true` for a seam measuring an already-measured tree and `cached: false` otherwise; existing seam tests passing (pasted).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted excerpts of a rendered execute prompt and a rendered verify prompt showing the `aw suite` instruction.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted passing `python3 -m pytest tests/test_suite_cache.py`; pasted failing stored-and-served cell with the lookup disabled (then restored); pasted post-change bare suite summary with no new failing node id versus V-01; `git diff docs/cli-human-guide.md CHANGELOG.md` with no em/en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Ready for `/plan-review` then human approval. Depends on `9ec94f` executed. Commit only Scope-Paths via `aw commit 0o0wt2 -- <paths>`; never push; paste real output into each `V-*`.
