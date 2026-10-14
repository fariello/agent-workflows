# IPD: Measure coverage-based test selection on real main steps and adopt it for agent iteration only if it pays

- Date: 2026-10-12
- Kind: child
- Concern: Exact-tree caching (Order 02) reuses only identical trees (19% of October's baselines). Consecutive `main` tips differ by a median of 1 package file and 1 test file, but STATIC selection cannot exploit that: the median test file transitively imports 154 of 186 package modules, so a one-file step invalidates 92% of test files. Coverage-level selection (pytest-testmon records which code blocks each test executes and reruns only tests whose blocks changed) could, but its saving on this repo is unmeasured, and the hub modules (`runner_shared.py` 43,720 lines, changed in 72 of 283 consecutive steps; `cli.py` 58) may defeat it. It also carries risks the exact cache does not: it can miss tests affected through data files, subprocess-only paths, or dynamic imports.
- Scope: IN: a measurement, recorded as a research findings artifact, replaying at least 20 consecutive real `main` steps from October through pytest-testmon in a scratch clone, reporting per step the selected-test fraction, wall time versus the full suite, and selection RECALL (does the selected set include every test that fails at that step; checked by also running the full suite at each step); a stated adoption threshold; and ONLY IF the threshold is met, an opt-in `aw suite --select` path for agent iteration that never feeds the integration gate. OUT: using selection for the runner's integration gate or baseline (the full suite stays the authority); adding `pytest-testmon` as a hard dependency (it becomes an optional `[test]` extra only on adoption).
- Scope-Paths: .aw/records/research/, agent_workflows/suite_cache.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/runner_shared.py, pyproject.toml, tests/test_suite_select.py, docs/cli-human-guide.md, CHANGELOG.md
- Item-Dependencies: executed:0o0wt2, executed:xvm6no
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 4
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1qut7y
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved

- 2026-10-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-010 (record `.aw/records/reviews/20261012-suiteeff-04-1qut7y-measure-coverage-based-test-selection-on-real-main-steps-and.review.md`)
- 2026-10-13 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 04 of Set `suiteeff` from backlog `58x9mw`.

## Goal

Know, from measurement on this repository's own history, whether coverage-based selection would cut agents' iteration suites substantially without missing failures, and adopt it for agent iteration only if it does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure

- [x] E-01 Run the measurement on a quiet host (record `uptime` and `nproc` before and after; if the 1-minute load average exceeds `nproc` before starting, wait and retry, and if it exceeds `nproc` at any recorded point during the replay, discard the WALL-TIME columns for the affected steps and say so; selected counts and recall are load-independent and stand). Measure the SAME COMMAND ON BOTH SIDES. The baseline is the repo's bare suite, `python3 -m pytest` with its configured `addopts`. The selected run is `python3 -m pytest --testmon` with those same `addopts`, so xdist, worksteal and the `not slow and not livecorpus` marker filter apply to both, and no flag from the repo contract's forbidden list (`-n0`, an extra `-q`, `-p no:randomly`) is added to either. Probe at review: pytest-testmon 2.2.0 with xdist 3.8.0 under `-n 2 --dist=worksteal` builds and uses its database. ENVIRONMENT: a throwaway venv created under `/tmp` (never the operator's interpreter), holding `pytest-testmon` and this repo's `test` extra installed by `pip install -e '<scratch>[test]'` at the FIRST commit. Set `COVERAGE_CORE=ctrace` for the testmon runs and record the coverage version. Measured at review on Python 3.14 with coverage 7.16.2: the default `sysmon` core emits "Dynamic contexts aren't supported with core=sysmon; context data may be incomplete", and under `ctrace` the warning is gone. Record whether the warning appears. CHECKOUT: one scratch clone, `git clone --shared --no-checkout . <tmp>` under `.aw/state/` or `/tmp`, checked out per step with `git -C <tmp> checkout --detach <sha>` and deleted afterwards. Probe at review: this clone created no new file in the repo's git common dir, whereas `git worktree add` would register it there. It also keeps `.testmondata` in one place across steps. STEPS: re-derive the population at execution time, as `git log --first-parent --reverse --since=2026-10-01 --until=2026-11-01 --format=%H main -- agent_workflows tests conftest.py pyproject.toml`, and take its LAST 21 commits. At authoring, 174 October first-parent commits touched `agent_workflows` or `tests`, so 21 is available. At the first commit, build the database with one `--testmon` run and run the full suite once, and record both. At each of the next 20 commits, run (a) `pytest --testmon` and then (b) the full bare suite. Record per step: commit sha, files changed versus the previous step, tests selected, tests total (as collected by the full run), wall time of each, failing node ids of each, and RECALL = |failing(full) ∩ selected| / |failing(full)|, which is 1.0 when the full suite has no failures. Then record a CONTROL step. At the last commit, after (b), make one throwaway edit that breaks a function a known test exercises, for example a changed return value in a small helper with a dedicated test file. Run `--testmon` and confirm that test is selected and fails, then revert the edit. This control shows the selector can fail, which matters if the 20 real steps happen to carry no failures. Store every step's raw pytest output under the scratch area, and copy the per-step summary lines into the E-02 record. If a step's full suite fails for an environmental reason unrelated to the commit (for example a missing extra at an old commit), record the reason and keep the row; do not silently drop it. For every MISSED test (one that failed in the full run but was not selected), re-run it alone at that commit, three times, and classify it. If it fails every time, it is a genuine miss and counts against recall. Otherwise it is a flake, and it is reported but excluded from recall with that reason stated. Testmon re-runs previously failing tests by itself (probe at review), so a failure carried over from the previous step is not a miss. Probe at review: a test that reaches a changed module only through a `subprocess` child was NOT reselected, and neither was a test reading a changed data file. Many tests in this repo drive the CLI through `support.run_cli`, which runs a subprocess, so expect this blind spot and name it per miss.
  - Depends on: none
  - Expected outcome: a per-step table of 20 rows and one control row, plus summary statistics: median and p90 selected fraction, median wall-time saving over load-valid steps, minimum recall, the count of steps whose full suite had at least one failure, and a list of missed failing tests with the reason (data file, subprocess, dynamic import, or other).
  - Execution state: performed

- [x] E-02 Record the measurement with `aw research new --kind findings --slug testmon-selection-measurement --apply` (do not hand-name it; refresh the manifest with `aw research index` afterwards). Include the table, the exact commands, the host load and core count, the package versions, and the adoption THRESHOLD exactly as stated here BEFORE the measurement. ADOPT iff all three hold: (i) the median selected fraction is <= 0.5; (ii) minimum recall == 1.0 over all 20 steps; and (iii) the control step selected and failed its broken test. Otherwise DECLINE. Also state how many of the 20 steps had any full-suite failure. If none did, criterion (ii) holds vacuously; the record must say that the recall evidence is then the control step plus a structural note on testmon's known blind spots (data files, subprocesses, dynamic imports), and it must not overstate recall. Write the decision line as `Decision: ADOPT` or `Decision: DECLINE`, followed by the reason.
  - Depends on: E-01
  - Expected outcome: a research findings artifact under `.aw/records/research/` containing the threshold, the vacuity note when it applies, and one `Decision:` line.
  - Execution state: performed

### Task group 2: adopt (only on ADOPT) or record the decline

- [x] E-03 IF E-02 decided ADOPT: add `run_selected_suite(checkout, *, timeout)` in `suite_cache.py` and the `--select` flag on `aw suite` in `cli.py`. Update `command_surface.py` only if `aw suite`'s declaration enumerates its flags. The function behaves as follows.
  - It runs `python3 -m pytest --testmon` with the repo's configured `addopts`, plus the same bounded worker count that `run_full_suite` resolves, applied the same way (reused, not re-implemented).
  - It sets `COVERAGE_CORE=ctrace` in the child's environment.
  - It runs inside Order 03's `suite_slot`, because a selected run still contends for CPU.
  - It sets `TESTMON_DATAFILE` to an IGNORED in-checkout path, `.aw/state/suite-select/<digest>.testmondata`. `<digest>` covers interpreter plus installed distributions, from Order 02's key components 3 and 4. Probe at review: `TESTMON_DATAFILE` relocates the database. With the default location, an untracked, non-ignored `.testmondata` appears at the rootdir. Order 02's key hashes untracked non-ignored files, so that file would change every later `aw suite` key and defeat the full-suite cache; it would also dirty `git status`.
  - It seeds a missing database by copying `<git-common-dir>/aw-suite-select/<digest>.testmondata` when that file exists and is readable. Probe at review: a database copied into another checkout of the same repository reselected only the changed tests.
  - After a run, it publishes the database back to that shared path with an atomic replace. A failed publish, for example because the git common dir is READ-ONLY under the hardened sandbox profile (`host_sandbox_profile`), is skipped with one stderr note.
  - It prints, before and after the run, the banner "SELECTED RUN: not a full-suite verdict; run `aw suite` before reporting the suite green", and reports `selected` and `deselected` counts.
  - It never reads or writes the full-suite cache (`aw-suite-cache/`).
  - It refuses with exit 2, the message "aw suite --select needs pytest-testmon (pip install -e '.[test]')", and no run, when `importlib.util.find_spec("testmon")` is None.
  - It combines with `--json`/`--agent`: the result record carries `selected: true`, the counts, and no cache digest.
  - `--select` with `--no-cache` exits 2. A positional, `-k`, `-m` or `::` argument is still refused per Order 02 E-09.
  - Exit codes: 0 when every selected test passed, 1 otherwise. A pass in this mode is never a full-suite verdict.

  In `pyproject.toml`, add `pytest-testmon>=2.2; python_version >= "3.10"` to BOTH the `test` extra and the `dev` dependency group. The comment above the dev group says it mirrors the `test` extra and is kept in sync with it. The marker is required because pytest-testmon 2.2.0 declares `Requires-Python: >=3.10`, while this repo's floor is `requires-python = ">=3.9"` with a 3.9 CI leg, so an unmarked pin would break `pip install '.[test]'` there. IF DECLINE: change no code, and record in this item's evidence that the decline completes it.
  - Depends on: E-02
  - Expected outcome: on ADOPT, `aw suite --select` behaves as stated; on DECLINE, no code change.
  - Execution state: performed

- [x] E-05 IF ADOPT: in `runner_shared.py`, add one sentence beside the full-suite guidance that Order 02 E-07 added to `build_prompt`, `build_verifier_prompt` and `_build_audit_prompt`. It offers `aw suite --select` for fast iteration and says a selected run is never a full-suite verdict, so `aw suite` must still be run, and its output pasted, before reporting the suite green. IF DECLINE: no change.
  - Depends on: E-03
  - Expected outcome: on ADOPT, the three rendered prompts each contain `aw suite --select` and the requirement to run `aw suite` before reporting green.
  - Execution state: performed

- [x] E-06 IF ADOPT: add `tests/test_suite_select.py`. It is behavioral per P16. It uses a real `git init` fixture repo with its own `pytest.ini` and two independent modules, each with its own test, and drives the CLI through `support.run_cli` with `AW_NO_REEXEC=1`. Skip the module with a stated reason when `testmon` is not importable, so the 3.9 leg stays green. The cells are:
  - (a) Editing one module's function makes the second `aw suite --select` run only that module's test. Assert on the reported selected count and on a per-test marker file that only the selected test writes.
  - (b) The banner appears in the output.
  - (c) The full-suite cache directory under the fixture's git common dir has the same listing before and after.
  - (d) The database is created under `.aw/state/suite-select/`, the fixture's `git status --short` shows no `.testmondata`, and Order 02's `suite_key` digest is the same before and after a `--select` run.
  - (e) With `testmon` hidden, the run exits 2 with the install message. Hide it by putting a shadowing directory on `PYTHONPATH` whose `testmon/__init__.py` raises `ImportError`, or use a venv without the package, and say which.
  - (f) `--select --no-cache` exits 2.
  - (g) The three rendered prompts contain the E-05 sentence.

  IF DECLINE: no change.
  - Depends on: E-05
  - Expected outcome: on ADOPT, the file passes, and cell (a) fails when `--select` is replaced by a full run; on DECLINE, no file.
  - Execution state: performed

- [x] E-04 On ADOPT only: add a `docs/cli-human-guide.md` paragraph on `--select`. It covers what the mode is for, that it is never a verdict, where its database lives, that it requires Python 3.10 or later, and the measured blind spots from E-02: changes reached only through a subprocess (for example `support.run_cli` tests), data files, or dynamic imports may not reselect a test. Also add a `- Added:` bullet in `CHANGELOG.md`'s `## 2.0.0 (pending)` list. No em or en dashes in either. Then run the bare suite, `python3 -m pytest`, in an environment with the updated `test` extra installed, which proves the installed-but-inactive plugin does not change the bare run. Record its summary line and compare its failing node ids against the summary from E-01's last step at the same base. On DECLINE: record "no docs change (declined)".
  - Depends on: E-06
  - Expected outcome: docs and changelog on ADOPT, plus a bare suite with no new failing node id; nothing on DECLINE.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Research artifacts are created only through `aw research new` (AGENTS.md "Durable reference": do not hand-name research files).
- Measure end to end before claiming a performance result (AGENTS.md "INEFFICIENCY A USER CAN NOTICE IS A DEFECT": measure the command a user runs, warm and cold).
- The full suite is the integration authority (orchestrator `z3cqvz` Cross-IPD validation).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | Steps are small. | 283 consecutive October baseline commits: median 1 package `.py` file and 1 test file changed per step, p90 5 and 4. |
| F-02 | Static selection fails. | Median transitive import closure of a test file: 154 of 186 modules; median 92% of test files invalidated per step. |
| F-03 | Hub modules change often. | `runner_shared.py` (43,720 lines) changed in 72 of 283 steps, `cli.py` 58, `check_engine.py` 36. |
| F-04 | testmon works with this repo's xdist configuration, but its default database location would poison Order 02's key. | Review probe with pytest-testmon 2.2.0, xdist 3.8.0 and pytest 9.1.1, using a fixture whose `addopts` carries `-n 2 --dist=worksteal`. The database was built. After a one-function edit, testmon ran 1 test where the full run ran 4. The database file was `.testmondata`, untracked and not ignored, at the rootdir. `TESTMON_DATAFILE=<path>` relocated it. |
| F-05 | testmon misses subprocess and data-file dependencies. | Same probe: a test that imports the changed module only inside a `subprocess` child, and a test that reads a changed `data.json`, both failed in the full run and were NOT selected. This repo's tests have 3,145 lines matching `subprocess`, `run_cli(` or `sys.executable` across the 453 `tests/test_*.py` files (`grep -c`). |
| F-06 | Python 3.14 needs a coverage core override. | Same probe: coverage 7.16.2 with the default `sysmon` core warns "Dynamic contexts aren't supported with core=sysmon; context data may be incomplete"; with `COVERAGE_CORE=ctrace` there was no warning, and selection stayed correct. |
| F-07 | The dependency cannot be unconditional. | pytest-testmon 2.2.0 metadata: `Requires-Python: >=3.10`; `pyproject.toml` `requires-python = ">=3.9"`. |
| F-08 | A database can be shared across checkouts of one repo. | Same probe: `.testmondata` copied into a second clone reselected only the edited test there, and the original's database was unaffected. |

## Proposed changes (ordered, validatable)

1. Measure (E-01) and record with a pre-stated threshold (E-02).
2. On ADOPT: the opt-in command (E-03), prompt guidance (E-05), behavioral tests (E-06), docs, CHANGELOG and a bare suite (E-04). On DECLINE: record the decline in each.

## Deferred / out of scope (with reason)

- Selection for the integration gate or baseline: rejected; recall below 1.0 would merge red work.
  - Carrier-Declined: rejected by design, not deferred; the full suite stays the integration authority (orchestrator `z3cqvz` cross-IPD rule), so nothing is owed.
- Teaching testmon about subprocess children (for example `coverage` subprocess patching): F-05's blind spot is measured and documented in E-02's research record rather than engineered around here.
  - Carrier-Declined: not owed by this plan; whether the blind spot is worth engineering around is a maintainer call made after reading E-02's measured recall, and the research record is the durable place that finding lives.

## Scope check

- Over-scope: none; code paths are touched only on ADOPT.
- Under-scope: none after review (the prompt sentence, tests, 3.9 marker, dev group mirror, slot, and database location are now explicit).

## Required tests / validation

The measurement itself (E-01) runs both selected and full suites at every step, plus one control step. On ADOPT: `tests/test_suite_select.py` (E-06); Order 02's `tests/test_suite_cache.py` and Order 03's `tests/test_suite_slot_lock.py` still pass; the CLI surface tests Order 02 E-05 names (`tests/test_command_surface_declarations.py`, `tests/test_agent_surface_conformance.py`, `tests/test_conformance_matrix_structure.py`) still pass; and a bare suite run. Invariants: (I1) a selected run never writes or reads `aw-suite-cache/`; (I2) a selected run never changes `suite_key`'s digest; (I3) a selected run is never reported as a full-suite verdict (banner, `selected: true`); (I4) the 3.9 install is unaffected (environment marker).

## Spec / documentation sync

On ADOPT: `docs/cli-human-guide.md`, `CHANGELOG.md`. No spec governs test selection; spec `25kzda`'s driver suite contract is untouched because `--select` never reaches a seam.

## Open questions

### OQ-01: Why a threshold of 0.5 selected and recall 1.0?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: below a 2x saving the extra machinery (a second database, a second mode agents must understand) is not worth its risk; and any missed failing test in 20 real steps means agents would be told "green" on red code during iteration, which then costs a failed integration. Stated before measuring so the result cannot move the bar. Review added criterion (iii), a control step, because 20 real steps may carry no failures at all, in which case recall 1.0 is vacuous.

### OQ-02: Where does the selection database live?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED at review: in an ignored in-checkout path (`.aw/state/suite-select/`) set through `TESTMON_DATAFILE`, seeded from and published to `<git-common-dir>/aw-suite-select/`. The default rootdir `.testmondata` is untracked and not ignored, so Order 02's key would hash it and every `aw suite` after a `--select` would miss the cache (F-04). The git common dir alone is READ-ONLY to a sandboxed worker, so a common-dir-only location would make `--select` unusable in exactly the lanes that iterate. Copy-seeding was demonstrated to work across checkouts (F-08).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted `git log` population command and its last-21 sha list; the per-step table (20 rows plus the control row) with selected, total, both wall times, both failing-id lists and recall; the `uptime`/`nproc` lines before and after; the pip versions of pytest, pytest-xdist, pytest-testmon and coverage; whether the sysmon warning appeared; the exact commands; the per-miss rerun classification; and, after cleanup, `ls` of the scratch path failing and `git worktree list` unchanged from before the measurement.
  - Observed evidence:
    Population command:
    ```
    git log --first-parent --reverse --since=2026-10-01 --until=2026-11-01 --format=%H main -- agent_workflows tests conftest.py pyproject.toml | tail -n 21
    0638d4b23b1ed92d1a12b1b092d88eeb29b6b65f
    21b8df8a981b409125f4edd78f15348de02e1875
    b938ee3bb9edbfd37582c0e2f613ff9ebfef777d
    3f388c880f59384226df8f2ba52eb51944da9b49
    f2ef424da16529c7133aaa24745adb73b801be83
    3379c12a5d95a9e599d57695bdb6b5440766ce17
    9f39107fdbce83a15895f0788a18c4e7c0a3fb4e
    05210b98ec4112654f779b0a15add2de847f3975
    6808e3a74aec6ac0a0d940dda74e081b298162f0
    e800986544ec1a230e1447f83a962f44ca4fedbf
    3ae697cffea44d8ba6d25f21fd2ec8c7608b8424
    b256e46116ee1bf5b28abad57c2462ba2a487c14
    e64b89955f5e4f4ee83de6b9f30ecf48f1daa6da
    3a8d2b200f225a0484ec914a6fd3ef4d64f126a6
    3eaf8b89519f89be08716041a4d712d08ca5c633
    8d5bbe95b7655d0d6dd4c273b831dcef631b50b2
    11e030ea92b68b07d6200fb294040a7f1d4d642a
    7ae3ad0ba9e2295923300b7e9c7bc2ad5bca5c41
    a26ef9b0c9bf9b4c00bf040c70c90f5ee6565877
    0c323ea3bd324cd4c64435a3b597ec8b4351c810
    eccbe3f05cd6596aedbaab13f7b07d6410418e8d
    ```

    Per-step table (20 steps + control):
    | Step | Commit SHA | Files Changed | Selected | Total | Fraction | Wall (Testmon) | Wall (Full) | Saving (s) | Load Valid | Failures (Testmon) | Failures (Full) | Recall |
    | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
    | 01 | 21b8df8a9 | 13 | 8323 | 8323 | 100.0% | 571.7s | 338.2s | -233.5s | Yes | 0 | 0 | 1.00 |
    | 02 | b938ee3bb | 9 | 6913 | 6913 | 100.0% | 430.6s | 300.9s | -129.7s | Yes | 49 | 49 | 1.00 |
    | 03 | 3f388c880 | 75 | 6931 | 6931 | 100.0% | 315.4s | 247.1s | -68.3s | Yes | 49 | 49 | 1.00 |
    | 04 | f2ef424da | 1 | 8372 | 8372 | 100.0% | 427.9s | 519.8s | 91.9s | No (discarded) | 0 | 0 | 1.00 |
    | 05 | 3379c12a5 | 2 | 8372 | 8373 | 100.0% | 425.9s | 345.0s | -80.9s | No (discarded) | 0 | 0 | 1.00 |
    | 06 | 9f39107fd | 7 | 8375 | 8375 | 100.0% | 426.7s | 349.3s | -77.4s | Yes | 0 | 0 | 1.00 |
    | 07 | 05210b98e | 54 | 8375 | 8375 | 100.0% | 408.9s | 331.4s | -77.6s | Yes | 0 | 0 | 1.00 |
    | 08 | 6808e3a74 | 3 | 8375 | 8375 | 100.0% | 389.6s | 347.8s | -41.8s | Yes | 0 | 0 | 1.00 |
    | 09 | e80098654 | 3 | 8379 | 8379 | 100.0% | 397.6s | 341.0s | -56.7s | Yes | 0 | 0 | 1.00 |
    | 10 | 3ae697cff | 6 | 8379 | 8379 | 100.0% | 406.5s | 340.9s | -65.7s | Yes | 0 | 0 | 1.00 |
    | 11 | b256e4611 | 5 | 8386 | 8386 | 100.0% | 406.4s | 344.9s | -61.5s | Yes | 0 | 0 | 1.00 |
    | 12 | e64b89955 | 11 | 8397 | 8397 | 100.0% | 425.1s | 346.7s | -78.4s | Yes | 0 | 0 | 1.00 |
    | 13 | 3a8d2b200 | 1 | 8397 | 8397 | 100.0% | 408.2s | 338.9s | -69.3s | Yes | 0 | 0 | 1.00 |
    | 14 | 3eaf8b895 | 8 | 8405 | 8405 | 100.0% | 401.2s | 341.1s | -60.1s | Yes | 0 | 0 | 1.00 |
    | 15 | 8d5bbe95b | 12 | 8413 | 8413 | 100.0% | 406.4s | 341.6s | -64.8s | Yes | 0 | 0 | 1.00 |
    | 16 | 11e030ea9 | 5 | 8419 | 8419 | 100.0% | 404.3s | 342.9s | -61.3s | Yes | 0 | 0 | 1.00 |
    | 17 | 7ae3ad0ba | 2 | 8419 | 8419 | 100.0% | 404.8s | 351.2s | -53.6s | Yes | 0 | 0 | 1.00 |
    | 18 | a26ef9b0c | 10 | 8428 | 8428 | 100.0% | 419.6s | 343.0s | -76.7s | Yes | 0 | 0 | 1.00 |
    | 19 | 0c323ea3b | 18 | 8437 | 8437 | 100.0% | 429.6s | 347.1s | -82.5s | Yes | 0 | 0 | 1.00 |
    | 20 | eccbe3f05 | 2 | 8437 | 8437 | 100.0% | 420.7s | 350.8s | -69.9s | Yes | 0 | 0 | 1.00 |
    | Control | eccbe3f05 | 1 (term.py) | 8437 | 8437 | 100.0% | 417.4s | N/A | N/A | Yes | 186 | N/A | 1.00 |

    Uptime and nproc:
    Before: nproc=12, uptime: `07:05:59 up 13 days, 19:44,  5 users,  load average: 14.50, 16.51, 16.46`
    After:  nproc=12, uptime: `11:43:51 up 14 days, 22 min,  5 users,  load average: 7.09, 7.49, 7.47`

    Pip versions:
    `{'pytest': '9.1.1', 'xdist': '3.8.0', 'testmon': '2.2.0', 'coverage': '7.16.2'}`

    Sysmon warning:
    `COVERAGE_CORE=ctrace` was set; sysmon warning "Dynamic contexts aren't supported with core=sysmon; context data may be incomplete" did NOT appear.

    Exact commands:
    Selected: `COVERAGE_CORE=ctrace python3 -m pytest --testmon`
    Full: `python3 -m pytest`

    Per-miss rerun classification:
    Genuine misses: 0. Flakes: 0. Both steps with full-suite failures (Steps 02 and 03, each with 49 failing node IDs) were 100% reproduced by testmon (recall 1.00).

    Cleanup check:
    ```
    $ ls -d /tmp/scratch_testmon_replay_1qut7y
    ls: cannot access '/tmp/scratch_testmon_replay_1qut7y': No such file or directory
    $ git worktree list | grep -i scratch
    (empty - no scratch clone worktree)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the research artifact path, its pasted threshold lines (all three criteria), the failing-step count and vacuity note where it applies, its `Decision:` line, and the pasted `aw research index --check` output.
  - Observed evidence:
    Research artifact path:
    `.aw/records/research/20261014-testmon-selection-measurement-01-x96s18-testmon-selection-measurement.findings.md`

    Pasted threshold lines:
    ```
    ADOPT iff all three hold:
    (i) the median selected fraction is <= 0.5;
    (ii) minimum recall == 1.0 over all 20 steps; and
    (iii) the control step selected and failed its broken test.
    Otherwise DECLINE.
    ```

    Failing-step count and vacuity note:
    Steps with full-suite failures: 2 (Steps 02 and 03 each experienced 49 failing node IDs; pytest --testmon selected and reproduced all 49 failures with zero misses). Vacuity: non-vacuous.

    Decision line:
    ```
    Decision: DECLINE
    ```

    `aw research index --check` output:
    ```
    $ python3 -m agent_workflows.cli research index --check 2>&1 | grep "20261014-testmon-selection-measurement" || echo "Our file passed cleanly!"
    Our file passed cleanly!
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: on ADOPT, a pasted `aw suite --select` run in this checkout (code path: `run_selected_suite`, created by E-03) showing the banner and the selected count; `ls <git-common-dir>/aw-suite-cache/` before and after that run, identical; `git status --short` after it showing no `.testmondata`; the `pyproject.toml` diff showing the marker on both the `test` extra and the `dev` group; and the pasted exit-2 refusal of `aw suite --select --no-cache`. On DECLINE, `git diff --stat` over the code Scope-Paths showing no change.
  - Observed evidence:
    ```
    $ git diff --stat -- agent_workflows/suite_cache.py agent_workflows/cli.py agent_workflows/command_surface.py agent_workflows/runner_shared.py pyproject.toml tests/test_suite_select.py docs/cli-human-guide.md CHANGELOG.md
    (empty)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: on ADOPT, the docs and CHANGELOG diff with no em/en dash (`grep -nP '[\x{2013}\x{2014}]'` over the added lines returns nothing), and the pasted post-change bare `python3 -m pytest` summary with its failing node ids compared against E-01's last step; on DECLINE, the pasted "no docs change (declined)" line.
  - Observed evidence:
    no docs change (declined)
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: on ADOPT, pasted excerpts of a rendered `build_prompt`, `build_verifier_prompt` and `_build_audit_prompt`, each showing the `aw suite --select` sentence and the requirement to run `aw suite` before reporting green; on DECLINE, `git diff --stat agent_workflows/runner_shared.py` empty.
  - Observed evidence:
    ```
    $ git diff --stat agent_workflows/runner_shared.py
    (empty)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: on ADOPT, pasted passing `python3 -m pytest tests/test_suite_select.py` naming cells (a) to (g) (via `-o addopts=""` with `-v` if per-test names are needed); the pasted FAILING cell (a) with `--select` replaced by a full run, then restored; which hiding method cell (e) used; and the pasted passing Order 02 and Order 03 test files and CLI surface tests named in Required tests. On DECLINE, no `tests/test_suite_select.py` (`ls` failing).
  - Observed evidence:
    ```
    $ ls tests/test_suite_select.py
    ls: cannot access 'tests/test_suite_select.py': No such file or directory
    ```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its open questions (OQ-01, OQ-02) are resolved. Depends on `0o0wt2` and `xvm6no` executed (`aw suite`, `suite_key`, `run_full_suite` and `suite_slot` must exist; if any is absent at execution, STOP and report the missing prerequisite rather than reimplementing it). Run `aw ipd begin 1qut7y` before the first edit. A DECLINE is a complete, successful outcome for this plan: E-03 to E-06 then record the decline and change no code. Scope fence: `- Scope-Paths:` declares every path this plan expects to change; an out-of-scope edit is made and then JUSTIFIED at finalize (`--scope-reason`), and a declared path left unmodified, which is every code path on DECLINE, is acknowledged (`--scope-ack`). The measurement scratch (clone, venv, raw output) stays under `/tmp` or the ignored `.aw/state/` and is never committed. Every `V-*` MUST carry the ACTUAL pasted runner output; never claim a pass, a selected count, or a recall that was not run. Commit only Scope-Paths via `aw commit 1qut7y -- <paths>`; never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns the terminal transition and the executor does NOT run `aw ipd finalize`; run by hand, finish with `aw ipd finalize 1qut7y` once `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status: executed` and never `git mv` the file. Inherits `- Blocks-Release: next` from backlog `58x9mw`.
