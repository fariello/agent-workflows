# IPD: Run a periodic checkup every N commits and show its result

- Date: 2026-10-12
- Kind: child
- Concern: Nothing in this toolkit reads CI's result, and the slow checks (for example `aw check --source-anchors`, about 5s) run only when someone asks. So CI was red for 1,623 main commits unseen, and stale spec pointers accumulate until someone sweeps them. The maintainer often runs 3 to 6 `aw oc run` / `aw agy run` processes in parallel, so whatever runs the checkup must run it once, not six times.
- Scope: (1) A setting `ci_checkup_interval_commits` in `.aw/config/project.json` (default 100; `0` disables). (2) A checkup that (a) asks GitHub, read-only, for the latest completed `tests.yml` run on main and the newest passing one, via the `gh` CLI, and (b) runs the slow checks (today exactly `check.spec-anchor-stale`, as `aw check --source-anchors` runs it; the list is one named tuple in `checkup.py`), then saves one record under `.aw/state/checkup/last.json`: the main commit it ran at, the time, CI's latest conclusion and commit, the last passing commit and how many first-parent main commits ago it was, and the slow-check finding counts. (3) Trigger: at the start of an `aw oc run` / `aw agy run`, if main has advanced at least N first-parent commits past the saved record (or no record exists), the run takes a non-blocking lock (`.aw/state/checkup/lock`); the run that gets it performs the checkup, every other run skips it and carries on. (4) `aw checkup` runs it on demand. (5) `aw attention` and `aw doctor` show the saved record as one line, read-only, never calling GitHub themselves.
- Scope-Paths: agent_workflows/checkup.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/runner_shared.py, agent_workflows/attention.py, agent_workflows/doctor.py, agent_workflows/config.py, tests/test_checkup.py, CHANGELOG.md, README.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 5st6e5
- Blocks-Release: next
- Set: cihealth
- Order: 2
- Highest E allocated: 07
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: n7xlhm
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (aw set): plan-review done
- 2026-10-12 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored during /plan-review of Set gradfix from the maintainer's 2026-10-12 design ruling.
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The maintainer always sees, in `aw attention` and `aw doctor`, whether CI is passing and how many commits ago it last passed, refreshed at least every N main commits by exactly one run, at no cost to commands people run interactively.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the checkup

- [x] E-01 Add the setting and the record. Read `ci_checkup_interval_commits` through the existing project-config loader (default 100, `0` disables, a non-integer or negative value falls back to the default with a warning, as `config.release_gate_work_kinds` does). Read two companion keys the same way so the checkup is not hard-wired to this repository: `ci_checkup_workflow` (default `tests.yml`) and `ci_checkup_branch` (default `main`); every later item uses these, never literals. Define the record schema with a version field and write it atomically (temp file, then rename) under `.aw/state/checkup/last.json`, which is gitignored local state. Resolve the directory against the PRIMARY checkout, not a lane worktree, so every run and worktree shares one record: reuse the existing resolver (`runner_shared.runs_repo_root`, which delegates to `attention._resolve_runs_repo_root`) rather than deriving a new one from the git common dir. The record holds commit ids, times, conclusions and counts only, never paths or account names.
  - Depends on: none
  - Expected outcome: a loader for the setting and a writer and reader for the record, both shared by every caller.
  - Execution state: performed

- [x] E-02 Read CI's result. A function that calls `gh run list --workflow <ci_checkup_workflow> --branch <ci_checkup_branch> --json headSha,conclusion,status,createdAt --limit <k>` as an argv list (no shell), read-only, with a bounded timeout, finds the newest completed run and the newest `success`, and counts first-parent commits from that success's commit to main (`git rev-list --count --first-parent <sha>..<ci_checkup_branch>`). Every failure (no `gh`, not logged in, no network, no remote, the workflow not present in this repository, a success older than the window, the commit not in local history) yields an explicit UNKNOWN with the reason, never a guess and never an exception. Widen `--limit` once if no success is in the first page, then report "no passing run in the last <k> runs".
  - Depends on: E-01
  - Expected outcome: a typed result (PASSING / FAILING / UNKNOWN, latest run commit, last passing commit, commits since) for a scripted `gh` returning each shape.
  - Execution state: performed

- [x] E-03 Run the slow checks and assemble the checkup. Run each check in the slow-check tuple (today only `check.spec-anchor-stale`, invoked through the same function `aw check --source-anchors` calls, not by shelling out), collect finding counts per rule, with a bounded total time (a check that exceeds it is recorded as UNKNOWN with the reason), combine with E-02, and save the record (E-01). Add `aw checkup` (human output by default, `--agent` emitting an `aw.agent/v1` result record), which always runs, regardless of the interval. Declare the new leaf in `command_surface.COMMAND_INVENTORY` (otherwise `tests/test_command_surface_declarations.py`, which the CLI output-conformance CI job runs, fails on an undeclared leaf).
  - Depends on: E-02
  - Expected outcome: `aw checkup` prints CI state and slow-check counts and writes the record.
  - Execution state: performed

### Task group 2: trigger and display

- [x] E-04 Trigger it from runs, once across parallel runs. At run start in both hosts (the shared path), before the first agent turn: if the interval is not 0 and the branch has advanced at least N first-parent commits past the record's commit (or there is no record, or the record's commit is no longer an ancestor of the branch), try a NON-BLOCKING exclusive lock on `.aw/state/checkup/lock` through `platform_lock.acquire` (non-blocking by default; contention raises `platform_lock.LockBusy`). If acquired, re-read the record inside the lock (a peer may have just finished), and if still due, run the checkup and save it. Record exactly one run event per run start: `checkup-performed` (with the result), `checkup-not-due`, `checkup-skipped-peer` (LockBusy), or `checkup-failed` (with the exception text). Either way the run continues: the checkup never fails or delays a run beyond its own duration, and a checkup that raises is recorded and ignored. Print the result line in the run's start banner and in its end summary.
  - Depends on: E-03
  - Expected outcome: with six runs started together, exactly one performs the checkup and five record a skip; runs are not blocked.
  - Execution state: performed

- [x] E-05 Show it. `aw attention` (human board and `--agent`) and `aw doctor` show one line from the saved record, for example "Checkup 40 commits ago: CI FAILING since 2026-09-27 (1,623 commits); spec pointers: 2 stale", or "No checkup yet: run `aw checkup`". When CI's last pass is more than N commits ago, the line is a warning. They only READ the record; they never call `gh`. Exit codes do not change: `aw attention --check` is untouched, and in `aw doctor` the line is either plain output or a Drift of severity `info` (the only severity `artifact_core.drift_exit_code` exempts), never `warning` or `error`, so CI is not made to depend on itself. If `aw attention --agent` output has a declared field contract, extend it additively.
  - Depends on: E-01
  - Expected outcome: both commands show the line; neither calls GitHub; exit codes unchanged.
  - Execution state: performed

### Task group 3: prove

- [x] E-06 Add `tests/test_checkup.py`, driving the real functions and CLI with a scripted `gh` on PATH (a stub executable printing canned JSON) and a fixture git repo, asserting on outputs, exit codes, the saved record and run events, never on source text. The `gh` stub is the ONLY `gh` the tests see (prepend its directory to PATH), so no test reaches the network. Cases: (a) passing, failing, and unknown (no `gh`, `gh` exits nonzero, malformed JSON, timeout) CI shapes; (b) commits-since computed from first-parent history; (c) the interval: not due below N, due at N, disabled at 0; (d) two concurrent checkups (two processes racing the lock, since `platform_lock.acquire` is non-re-entrant within one process): exactly one runs, the other records `checkup-skipped-peer`; (e) `aw attention` and `aw doctor` show the line from a saved record and never execute the `gh` stub (assert the stub's call log is empty); (f) a raising checkup does not fail the run and records `checkup-failed`; (g) the record is written at the primary-checkout path when the caller is a linked worktree; (h) `ci_checkup_workflow` and `ci_checkup_branch` reach the `gh` argv (read from the stub's call log). Run the bare suite and paste its summary line.
  - Depends on: E-04, E-05
  - Expected outcome: the new module passes; bare suite green.
  - Execution state: performed

- [x] E-07 Document it. README: the `aw checkup` command and the three settings with their defaults. CHANGELOG: one line for the command, the settings, the run-start line, and the attention/doctor line. No em or en dashes in either.
  - Depends on: E-03, E-05
  - Expected outcome: README and CHANGELOG describe what shipped.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Machine output is `aw.agent/v1` records.
- Cross-platform locks go through `platform_lock` (`filelock`), not `fcntl`.
- New CLI leaves are declared in `command_surface.COMMAND_INVENTORY`; `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` enforces it.
- Primary-checkout state resolves through `runner_shared.runs_repo_root`.
- `.github/workflows/tests.yml` triggers on pushes to `main` or `master`; this repository's remote is GitHub.
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | Nothing reads CI. | No caller of `gh run` in `agent_workflows/` (the only `gh` reference is a config path in `oc_runipd.py`). |
| F-02 | `gh` is available and authenticated here and answers in about a second. | `gh run list --workflow tests.yml --limit 200 --json createdAt` returned 200 rows (2026-10-12). |
| F-03 | The slow check exists and is opt-in. | `aw check specs --source-anchors` about 4.2s user against about 1.05s for bare `check specs` (plan `l85xvi` F-03). |
| F-04 | A live-run detector and a lock helper exist. | `runner_shared.peer_drivers`; `platform_lock.acquire` (non-blocking default, raises `LockBusy`, not re-entrant). |
| F-05 | No registry of "slow" checks exists. | No `slow` rule registry in `check_engine`; `--source-anchors` is a flag on `aw check` (`cli.py`, `dest="source_anchors"`). |
| F-06 | `aw doctor` exits 1 on any non-`info` Drift. | `doctor.run_doctor` returns the aggregated Drift list; `artifact_core.drift_exit_code` exempts only `info`. |

## Proposed changes (ordered, validatable)

1. Setting and record (E-01). 2. CI reader (E-02). 3. Checkup and `aw checkup` (E-03). 4. Run trigger with a single-run lock (E-04). 5. Display (E-05). 6. Tests (E-06). 7. Docs (E-07).

## Deferred / out of scope (with reason)

- A background daemon or cron job: not needed; runs and `aw checkup` already happen often enough at this repo's pace (about 100 main commits a day).
  - Carrier-Declined: run-start triggering meets the 100-commit bound whenever runs happen; `aw checkup` covers the rest.
- CI providers other than GitHub Actions: this repo uses GitHub Actions only.
  - Carrier-Declined: the reader returns UNKNOWN without `gh`, so other setups degrade honestly.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `tests/test_checkup.py` (new).
- `tests/test_command_surface_declarations.py` (existing; must stay green with the new leaf).
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

README gains the `aw checkup` command and the settings; CHANGELOG line (E-07). No spec currently describes CI visibility; spec `25kzda` describes run start, and E-04's banner line is additive output, recorded in the CHANGELOG. If the executor finds a spec that lists the run-start steps exhaustively, amend it and justify the path at finalize.

## Open questions

### OQ-01: Default interval?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: 100 commits, adjustable (maintainer, 2026-10-12).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the setting's value under a missing, valid, zero, and malformed config (pasted), and a written record (pasted JSON) at the primary-checkout path when called from a lane.
  - Observed evidence:
    Settings evaluation:
    ```
    missing: 100 tests.yml main
    valid: 50 ci.yml master
    zero: 0
    WARNING: ci_checkup_interval_commits in /tmp/tmprzkvd0rz/.aw/config/project.json is -10, which is negative. Using default 100 instead.
    negative: 100
    WARNING: ci_checkup_interval_commits in /tmp/tmprzkvd0rz/.aw/config/project.json is 'not-an-int', which is not an integer. Using default 100 instead.
    non-int: 100
    ```
    Primary-checkout path when called from a lane:
    ```
    lane cwd: n7xlhm
    resolved primary: agent-workflows
    checkup path: <primary_checkout>/.aw/state/checkup/last.json
    ```
    Written record at primary-checkout path from linked worktree:
    ```json
    {
      "schema_version": 1,
      "commit": "f01a8a81d72afceb56a06bf1653d0688c54bfbcd",
      "time": "2026-10-14T00:08:42Z",
      "ci": {
        "status": "UNKNOWN",
        "health": "UNKNOWN",
        "conclusion": null,
        "latest_commit": null,
        "latest_run_created_at": null,
        "last_passing_commit": null,
        "last_passing_created_at": null,
        "commits_since_last_pass": null,
        "reason": "gh exited 1: failed to determine base repo: no git remotes found"
      },
      "slow_checks": {
        "status": "PASSING",
        "finding_counts": {
          "check.spec-anchor-stale": 0
        },
        "total_findings": 0,
        "reason": null
      }
    }
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: E-06 (a), (b) and (h) passing, plus one real `aw checkup --agent` run against this repository (pasted). If `gh` is unavailable or unauthenticated at execution, the pasted UNKNOWN result with its reason is acceptable evidence for the real run.
  - Observed evidence:
    E-06 (a), (b), (h) test run:
    ```
    ======================= 10 passed, 6 deselected in 1.03s =======================
    tests/test_checkup.py::test_commits_since_first_parent PASSED            [ 10%]
    tests/test_checkup.py::test_ci_shape_passing PASSED                      [ 20%]
    tests/test_checkup.py::test_ci_shape_unknown_malformed_json PASSED       [ 30%]
    tests/test_checkup.py::test_ci_shape_commit_not_in_local_history PASSED  [ 40%]
    tests/test_checkup.py::test_custom_workflow_and_branch_reach_gh_argv PASSED [ 50%]
    tests/test_checkup.py::test_ci_shape_failing_with_prior_pass PASSED      [ 60%]
    tests/test_checkup.py::test_ci_shape_unknown_nonzero_exit PASSED         [ 70%]
    tests/test_checkup.py::test_ci_shape_widen_limit_when_no_pass_in_page_1 PASSED [ 80%]
    tests/test_checkup.py::test_ci_shape_unknown_no_gh PASSED                [ 90%]
    tests/test_checkup.py::test_ci_shape_unknown_timeout PASSED              [100%]
    ```
    Real `aw checkup --agent` run:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"checkup","outcome":"ok","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["ci","slow_checks"],"next":null}
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted human and `--agent` output of `aw checkup`, and the record it wrote.
  - Observed evidence:
    Human output:
    ```
    WARN     Checkup 0 commits ago: CI FAILING since 2026-09-27 (1,767 commits); spec pointers: 0 stale
      CI Status: FAILING
      Latest completed: cancelled (commit f6ba67c817a)
      Last passing: commit f69ad318af1, 1,767 commits ago
      Slow checks:
        - check.spec-anchor-stale: 0 finding(s)
      Saved record: .aw/state/checkup/last.json
    ```
    Agent output:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"checkup","outcome":"ok","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["ci","slow_checks"],"next":null}
    ```
    Saved record `.aw/state/checkup/last.json`:
    ```json
    {
      "schema_version": 1,
      "commit": "6947d3c6759d1a62fdfae835a6c34bf66ff9b513",
      "time": "2026-10-14T00:09:20Z",
      "ci": {
        "status": "FAILING",
        "health": "FAILING",
        "conclusion": "cancelled",
        "latest_commit": "f6ba67c817a7812bb04ec3a2bddc79153e186a61",
        "latest_run_created_at": "2026-10-13T04:41:00Z",
        "last_passing_commit": "f69ad318af1b1ee7a959062d4588cc3a3a837992",
        "last_passing_created_at": "2026-09-27T17:56:17Z",
        "commits_since_last_pass": 1767,
        "reason": null
      },
      "slow_checks": {
        "status": "PASSING",
        "finding_counts": {
          "check.spec-anchor-stale": 0
        },
        "total_findings": 0,
        "reason": null
      }
    }
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: E-06 (c), (d) and (f) passing, showing the `checkup-skipped-peer` and `checkup-failed` events, produced by the run-start path E-04 creates.
  - Observed evidence:
    ```
    ======================= 3 passed, 13 deselected in 0.89s =======================
    tests/test_checkup.py::test_interval_check PASSED                        [ 33%]
    tests/test_checkup.py::test_raising_checkup_records_checkup_failed PASSED [ 66%]
    tests/test_checkup.py::test_concurrency_lock_busy PASSED                 [100%]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: E-06 (e) passing, and pasted `aw attention` and `aw doctor` excerpts with the line, with each command's exit code pasted before and after a record exists, unchanged.
  - Observed evidence:
    E-06 (e) test passing:
    ```
    tests/test_checkup.py::test_attention_and_doctor_read_record_zero_gh_calls PASSED [100%]
    ```
    `aw attention` excerpt:
    ```
    Checkup 0 commits ago: CI FAILING since 2026-09-27 (1,767 commits); spec pointers: 0 stale
    ```
    `aw doctor` excerpt:
    ```
      Checkup:     Checkup 0 commits ago: CI FAILING since 2026-09-27 (1,767 commits); spec pointers: 0 stale
    ```
    Exit code check before and after record:
    ```
    BEFORE RECORD:
    attention exit code: 2
    doctor exit code: 1
    AFTER RECORD:
    attention exit code: 2
    doctor exit code: 1
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the new module passing (including (g)), `tests/test_command_surface_declarations.py` passing, and the bare-suite summary line.
  - Observed evidence:
    ```
    tests/test_checkup.py ................                                   [100%]
    ============================== 16 passed in 1.96s ==============================

    tests/test_command_surface_declarations.py ..                            [100%]
    ============================== 2 passed in 0.38s ===============================

    Bare suite summary line:
    1 failed, 8279 passed, 4 skipped, 18 xfailed, 3 warnings in 561.35s (0:09:21)
    (The single failure was midnight UTC date boundary rollover in test_fresh_install_and_reinstall_state_records comparing running version date string; verified immediately passing upon re-run: 3 passed in 4.44s).
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the README and CHANGELOG diff.
  - Observed evidence:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index eb705fdde..67f76bb96 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Added: `aw checkup` command and periodic CI health checks with configurable interval (`ci_checkup_interval_commits`, default 100), workflow (`ci_checkup_workflow`, default `tests.yml`), and branch (`ci_checkup_branch`, default `main`) in `project.json`, showing checkup status in run start and run end banners, `aw attention`, and `aw doctor`.
     - Added: merge-time stale spec line-anchor citation gate refuses integration of lanes that introduce new stale spec line citations (cause spec-anchor-new-stale) before the merge-and-revalidate gate, with bounded fix-it retry turns and fail-open behavior on unknown detector errors.

     - Fixed: runs with verification on no longer start a background test-suite baseline they never read.
    diff --git a/README.md b/README.md
    index 1b1408019..3b6ce1a48 100644
    --- a/README.md
    +++ b/README.md
    @@ -246,6 +246,23 @@ and an under-powered analysis REFUSES with its observed sample size instead of e
     [Run analytics](docs/run-analytics.md), whose privacy section names the shared detector's measured
     blind spots rather than implying it covers everything.

    +### Periodic CI checkup (`aw checkup`)
    +
    +Run `aw checkup` to inspect GitHub Actions CI health and run registered slow checks (such as stale spec line-anchor citations) locally:
    +
    +```bash
    +aw checkup           # human summary of latest CI result and slow checks
    +aw checkup --agent   # machine-readable aw.agent/v1 result record
    +```
    +
    +The checkup runs automatically at run start when the branch advances past the configured commit interval. Configure checkup behavior in `.aw/config/project.json`:
    +
    +- `ci_checkup_interval_commits`: Interval in commits between periodic run-start checkups (default `100`, `0` disables).
    +- `ci_checkup_workflow`: Workflow file to inspect via `gh run list` (default `tests.yml`).
    +- `ci_checkup_branch`: Target branch to inspect (default `main`).
    +
    +Checkup results are displayed in run-start banners, run-end summaries, `aw attention`, and `aw doctor`.
    +
     ### Concise agent reporting

     Installing agent-workflows also makes concise, essential-information-only reporting the
    ```
    Em/en dash check: 0 found.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit n7xlhm -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize n7xlhm` only after `aw ipd lint --phase pre-transition` conforms.
