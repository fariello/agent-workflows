# IPD: Put the coverage-record and proposal-fallback history writers on the UTC clock so no history writer still reads the local date

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `auf552` reports that `## Workflow history` dates desync across UTC midnight because one writer reads the LOCAL date while another reads the UTC date. The backlog and `status_set` halves the item names were already converged by executed plan `5ivkdh` (Set `7qvs1c`) and are guarded by `tests/test_history_date_clock.py` and the derived-surface guard from executed plan `ayhveg`; both pass at this HEAD. But the defect CLASS the item describes is still live in two history writers that neither plan's census covered, because both were written AFTER `5ivkdh`'s E-05 audit (`coverage_record.py` first appears in commit `c4dc37203`, 2026-10-06; `5ivkdh` executed 2026-10-03). Measured live in this lane at HEAD `9e3b99850` under `TZ=Pacific/Honolulu` inside a skew window (local `2026-10-11`, UTC `2026-10-12`): `coverage_record.write` wrote `- 2026-10-11 coverage pass (aw oc run): fingerprint d6bcfbc5630b, model m` into a tracked plan's `## Workflow history`, while every `5ivkdh`-converted writer records `2026-10-12` at the same instant. The second site, `runner_shared.perform_coordinator_proposal_file`'s inner `_write_fallback_record`, stamps its `- <date> created (proposal fallback)` history line from `dt.date.today()`.
- Scope: IN: route the two residual HISTORY-record date writers (`coverage_record.write`'s workflow-history line and its `- Coverage-Checked:` date, and the proposal-fallback backlog record's `created` history line) through the existing `artifact_core.utc_history_date()`; add timezone-parameterized behavioral tests that drive both writers under a zone east and west of UTC and assert the UTC date; re-run the `date.today()`-class census over `agent_workflows/` and record a verdict for every site so no HISTORY writer is left unaccounted for. OUT, each with a reason under "Deferred": FILENAME date prefixes (D55 rules them LOCAL); the walkthrough `- Date:` front matter in `set_records.render_walkthrough` (front matter, not a history record); the `setdisp` dispatch unification; closing the backlog item (the runner sets `graduated`).
- Scope-Paths: agent_workflows/coverage_record.py, agent_workflows/runner_shared.py, tests/test_history_date_clock_residual.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: auf552
- From-Spec: 2vev8j
- Blocks-Release: next
- Set: auf552
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8chbn9
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005 (all fixed; both writers re-driven local-dated under Honolulu at review; child-process tests now pin PYTHONPATH and drop the ambient worker role; record `.aw/records/reviews/20261011-auf552-01-8chbn9-put-the-coverage-record-and-proposal-fallback-history-writer.review.md`)
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog auf552. The backlog/status_set divergence the item names is already fixed by executed 5ivkdh and guarded by executed ayhveg (5 TZ suites, 26 passed at HEAD 9e3b99850); this plan owns the two residual local-clock history writers (coverage_record.write, runner proposal fallback) measured live under TZ=Pacific/Honolulu (local 2026-10-11, UTC 2026-10-12). Clock RESOLVED from spec 2vev8j 4.4 and DECISIONS.md D55. Bare suite baseline: 6 failed, 7213 passed, 2 skipped (all six non-project-cwd tests, untouched here).

- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Finish what backlog `auf552` asks for: an artifact's recorded history date depends only on when the
action happened, never on the machine's timezone or on which writer recorded it. The backlog and
`status_set` writers already do this; this plan converts the two history writers that were added after
the `5ivkdh` census (the coverage record and the proposal fallback) and pins both with behavioral
timezone tests, leaving filename dates on the local clock per D55.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline and failing tests first

- [x] E-01 Record a live baseline at your own execution HEAD before any edit: run the bare suite (`python3 -m pytest`) and the five shipped TZ suites (`python3 -m pytest tests/test_history_date_clock.py tests/test_history_date_clock_parity.py tests/test_history_date_clock_readers.py tests/test_history_date_clock_sidecar.py tests/test_scaffold_history_clock.py`), and record the failure SET (test ids), not only the counts. The authoring numbers (`6 failed, 7213 passed, 2 skipped`; `26 passed`) are context only, since the suite drifts.
  - Depends on: none
  - Expected outcome: the pasted summary lines and failing test ids of both runs at the execution HEAD, recorded before any source edit.
  - Execution state: performed

- [x] E-02 Create `tests/test_history_date_clock_residual.py` with two behavioral tests, each parameterized over `Pacific/Kiritimati` (UTC+14) and `Pacific/Honolulu` (UTC-10). (a) Coverage record: write a minimal plan file into a `tempfile` directory and call `coverage_record.write(plan, "pass", (), model="m", tool="aw oc run")` in a CHILD process whose `env=` carries `TZ=<zone>`, `AW_NO_REEXEC=1`, and `PYTHONPATH` with the repository root PREPENDED (as `tests/conformance_matrix._pinned_env` does; measured at review, this lane's ambient `PYTHONPATH` lists the MAIN checkout first, so a child run from a temp `cwd` imports another checkout's `agent_workflows` and the test would exercise the wrong code) (the subprocess shape `tests/test_history_date_clock.py` uses, which leaves the pytest worker's process-global time state untouched); the child is a `python -c` snippet run with `cwd=` the temp directory; assert the written `- <date> coverage pass` history line AND the `- Coverage-Checked: <date>` field both equal the child's UTC date, read from the child (`datetime.datetime.now(datetime.timezone.utc).date().isoformat()` printed beside the call) so a run straddling midnight cannot flake. (b) Proposal fallback: drive `runner_shared.perform_coordinator_proposal_file` with a `material` proposal and a patched `runner_shared.integration_lock` that yields `IntegrationLockOutcome(acquired=False, ...)` (the exact shape `tests/test_run_proposal_channel.py::test_coordinator_performer_held_integration_lock` uses), also in a child process under `TZ=<zone>` with the same `PYTHONPATH` rule and `AW_EXECUTION_ROLE` REMOVED from the child env (declared, not inherited, per `tests/support.execution_role`; the runner exports `AW_EXECUTION_ROLE=worker`, measured in this lane), driven against a temp `git init` repo with `state={"repo": <tmp>, "run_id": ...}` and `item={"id6": ...}` and no plan file (demonstrated at review: this shape writes `proposals/01-<id6>-proposal.backlog.md` with the fallback history line), and assert the `created (proposal fallback)` history line in the saved `proposals/*proposal.backlog.md` carries the child's UTC date. Each test also asserts the skew is OBSERVABLE (the child's local date differs from its UTC date, both printed by the child) and calls `pytest.skip` with a stated reason for a zone that is not in skew at run time, rather than passing vacuously. Note the coverage, which is why these two zones are the right pair: Honolulu (UTC-10) is in skew from 00:00 to 10:00 UTC and Kiritimati (UTC+14) from 10:00 to 24:00 UTC, so at every instant EXACTLY ONE zone is in skew (measured at review at 05:45 UTC: Honolulu skewed, Kiritimati did not). One parameter therefore always exercises the property and the other skips. To make a broken skew probe visible, each case first probes BOTH zones (one tiny child each, printing local and UTC dates) and asserts exactly one of them is in skew before deciding whether to skip itself. Run the new file at the E-01 HEAD and confirm it FAILS for the right reason on whichever zone is in skew.
  - Depends on: E-01
  - Expected outcome: a new test file whose tests exercise the real writers and assert on file content; a pasted run at the unedited HEAD showing at least one failure whose message names the local date where the UTC date was expected (or, outside every skew window, the explicit skip reason).
  - Execution state: performed

### Task group 2: Convert the two writers

- [x] E-03 In `coverage_record.write`, replace `today = datetime.date.today().isoformat()` with `artifact_core.utc_history_date()` (function-local import, matching the module's "All first-party imports function-local" docstring rule), so both the `- Coverage-Checked:` field and the `- <date> coverage <verdict>` history line read UTC. The module-level `import datetime` is used ONLY by that line (measured at review), so remove it. Do not change the line formats: `ipd_lint._COVERAGE_HIST_RE` and `coverage_record._CHECKED_LINE_RE` parse them.
  - Depends on: E-02
  - Expected outcome: `coverage_record.write` records the UTC date in both places; the E-02 coverage test passes under both zones; `tests/test_coverage_record.py` still passes.
  - Execution state: performed

- [x] E-04 In `runner_shared.perform_coordinator_proposal_file`'s inner `_write_fallback_record`, replace `dt.date.today().strftime('%Y-%m-%d')` in the `- ... created (proposal fallback)` history line with `artifact_core.utc_history_date()` (function-local import, as the existing `from agent_workflows import artifact_core as _core` sites in that module do). Leave the fallback filename (`{pos:02d}-{item_id6}-proposal.{ext}`, which carries no date) and every other line unchanged.
  - Depends on: E-02
  - Expected outcome: the fallback backlog record's history line carries the UTC date; the E-02 fallback test passes under both zones; `tests/test_run_proposal_channel.py` still passes.
  - Execution state: performed

### Task group 3: Census and record

- [x] E-05 Re-run the history-writer census over `agent_workflows/` with BOTH `rg -n "date\.today\(\)|datetime\.now\(\)\.|\.now\(\)\.date\(\)|_now\(\)\.date\(\)" agent_workflows` AND `rg -n "datetime\.now\(\s*\)|time\.localtime\(|time\.strftime\(\"%Y" agent_workflows -g '*.py'` (the first alone misses a bare `datetime.now()` assigned and formatted later, e.g. `prompts._now`, and `time.strftime` without `gmtime`), and produce a verdict table with one row per hit: HISTORY (writes a `## Workflow history` record or a history-like attested date, and must be UTC), FILENAME (D55, stays local), or NEITHER (front matter, run id, telemetry, read-only comparison), each with a one-line reason. Confirm the only HISTORY rows are the two converted in E-03/E-04 and that each now reads `utc_history_date`. If a NEW HISTORY site is found, do NOT widen this plan's scope: file it with `aw backlog new --work-kind bug` (gated per AGENTS.md) and cite the new id6 in the table. Then add one `- Fixed:` line to `CHANGELOG.md` under the pending `## 2.0.0 (pending)` heading, beside the existing `- Fixed:` entries, stating that the coverage record and the proposal-fallback record now stamp history dates in UTC like every other history writer (no em or en dashes; user-facing prose).
  - Depends on: E-03, E-04
  - Expected outcome: a pasted census command and full verdict table with no HISTORY site left on the local clock or unaccounted for; one CHANGELOG line.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Spec `2vev8j` Section 4.4, "One timezone for every writer": "Every writer, tool and human-facing helper alike, records UTC; local time is a RENDER-TIME concern only." Approved with a human attestation; cited as binding by executed plans `5ivkdh` and `ayhveg`.
- `DECISIONS.md` D55, "Human-facing timestamps use LOCAL time, not UTC": filename date prefixes stay machine-local. This plan touches no filename date.
- The single shared helper already exists: `artifact_core.utc_history_date()`, whose docstring reads "DO NOT CALL THIS FOR FILENAME DATES". No new helper is needed.
- TZ tests run the code under test in a CHILD process with `TZ` in `env=` (`tests/test_history_date_clock.py`, `tests/test_history_date_clock_readers.py`), never by exporting `TZ` for the suite, because `time.tzset()` mutates process-global state under `-n auto` and `pytest-randomly`.
- `coverage_record` keeps first-party imports function-local ("All first-party imports function-local" in `coverage_record.write`'s docstring).
- Tests must exercise behavior and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the census in E-05 is an authoring-time audit recorded in this plan, NOT a test that greps source.
- Run the suite bare as `python3 -m pytest` (repo-local development contract).

## Findings

| ID | Finding | Evidence | Consequence |
|---|---|---|---|
| F-01 | The two writers backlog `auf552` names are ALREADY fixed. | Executed plan `5ivkdh` routed `backlog._render_item`, `backlog.run_note`, `backlog._reattach_history` and `status_set.apply_status_change` through `artifact_core.utc_history_date`; at HEAD `9e3b99850` the five TZ suites report `26 passed in 16.69s`, including `tests/test_history_date_clock.py::...::test_backlog_set_both_spellings_record_utc_date`. | This plan does not re-fix them; it closes the residual of the same defect class. |
| F-02 | `coverage_record.write` stamps a tracked plan's history line from the LOCAL date. | `today = datetime.date.today().isoformat()` feeds both `f"- Coverage-Checked: {today} {checked_model}"` and `f"- {today} coverage {verdict} ({tool_str}): ..."`. Driven live under `TZ=Pacific/Honolulu` (local `2026-10-11`, UTC `2026-10-12`): output `'- Coverage-Checked: 2026-10-11 by m'` and `'- 2026-10-11 coverage pass (aw oc run): fingerprint d6bcfbc5630b, model m'`. | Every orchestrator plan the coverage gate records into gets a history line one day off its neighbors across UTC midnight, exactly the `auf552` symptom. |
| F-03 | The proposal-fallback record stamps its history line from the LOCAL date. | `runner_shared.perform_coordinator_proposal_file` -> `_write_fallback_record`: `- {dt.date.today().strftime('%Y-%m-%d')} created (proposal fallback): Proposal from {item_id6}`. The file lands under the gitignored `.aw/records/runs/<run>/proposals/` (`.aw/.gitignore` `records/runs/`), but it is a backlog record meant to be filed later, so its history line becomes tracked when it is. | Same defect class; lower exposure (only on a fallback path). |
| F-04 | Why the existing guards missed both. | `coverage_record.py` first appears in `c4dc37203` (2026-10-06), after `5ivkdh` executed (2026-10-03), so its E-05 census could not see it. `tests/test_history_date_clock_parity.py::derive_history_writing_surface` derives only `... set` / `... note` mutation verbs from `command_surface.COMMAND_INVENTORY`, so `ipd coverage` and the runner's internal proposal path are outside its surface. | A census at execution HEAD (E-05) is required, not assumed. Extending the derived guard's surface is not needed for these two sites because E-02 pins them directly. |
| F-06 | Both writers re-measured at review (HEAD `b1b2fab2b`, 05:45 UTC 2026-10-12): `coverage_record.write` under `TZ=Pacific/Honolulu` wrote `- Coverage-Checked: 2026-10-11 by m` and `- 2026-10-11 coverage pass ...` (UTC `2026-10-12`), and under `TZ=Pacific/Kiritimati` (no skew at that hour) `2026-10-12`; `perform_coordinator_proposal_file` with a held lock under Honolulu wrote `- 2026-10-11 created (proposal fallback): Proposal from fb0001` while UTC was `2026-10-12`. The five TZ suites (`26 passed`) and `tests/test_coverage_record.py` + `tests/test_run_proposal_channel.py` (`26 passed`) pass at that HEAD. The lane's ambient `PYTHONPATH` lists the main checkout first and `AW_EXECUTION_ROLE=worker` is exported. | Confirms F-02/F-03; drives the child-process env rules in E-02. |
| F-05 | Line formats are parsed elsewhere. | `ipd_lint._COVERAGE_HIST_RE` matches `^-\s+(?:\d{4}-\d{2}-\d{2})\s+coverage\s+(pass|fail)\b`; `coverage_record._CHECKED_LINE_RE` parses `- Coverage-Checked:`. | Only the date VALUE may change, never the format. |

## Proposed changes (ordered, validatable)

1. Baseline the suite and the TZ suites at the execution HEAD (E-01).
2. Add the failing timezone-parameterized behavioral tests for both writers (E-02).
3. Convert `coverage_record.write` to `artifact_core.utc_history_date()` (E-03).
4. Convert the proposal-fallback history line to `artifact_core.utc_history_date()` (E-04).
5. Re-run the census, record the verdict table, add the CHANGELOG line (E-05).

## Deferred / out of scope (with reason)

- FILENAME date prefixes (`backlog.run_new`, `specs._today` for the filename, `releases`, `set_records` plan/spec name dates, `ipd_authoring` filename): `DECISIONS.md` D55 rules them LOCAL and current. Changing them would reverse a deliberate decision.
  - Carrier-Declined: not a defect; D55 is a deliberate, current ruling and the two clocks compose as written.
- `set_records.render_walkthrough`'s `- Date:` front matter: a narrative document's front-matter date, not a history record; already classified NEITHER by `5ivkdh` E-05.
  - Carrier-Declined: not a defect; front-matter document dates are not history records under spec 2vev8j 4.4.
- Extending `tests/test_history_date_clock_parity.py`'s derived surface beyond `set`/`note` verbs: a broader redesign of that guard; the two residual sites are pinned directly by E-02. If E-05 finds further non-verb history writers, E-05 itself files them as a gated bug backlog item rather than widening this plan.
  - Carrier-Declined: not needed for this defect; E-02 pins both residual writers directly and E-05 files any further site it finds.
- The dispatch-fork unification of the two backlog setter spellings: owned by open backlog item `fcnz1r`, as `5ivkdh` already recorded.
  - Carrier: fcnz1r
- Setting backlog `auf552` to `graduated`/`done`: owned by the runner and the lifecycle, not this plan.
  - Carrier-Declined: not a work item; the lifecycle tooling performs it.

## Scope check

- Over-scope: none. Two one-line production edits, one new test file, one CHANGELOG line; every path is declared.
- Under-scope: none known. If the E-05 census at execution HEAD finds a third HISTORY site, it is filed as a gated bug backlog item and cited, so it is carried rather than dropped.

## Required tests / validation

1. `python3 -m pytest tests/test_history_date_clock_residual.py` fails at the unedited HEAD for the right reason (E-02) and passes after E-03/E-04, under both zones (V-02, V-03, V-04).
2. Regression: `python3 -m pytest tests/test_coverage_record.py tests/test_run_proposal_channel.py` and the five shipped TZ suites pass (V-03, V-04).
3. The bare suite `python3 -m pytest` shows no failure absent from the E-01 baseline failure set (V-05).
4. `aw ipd lint` on this plan conforms at each phase.

## Spec / documentation sync

- Spec `2vev8j` Section 4.4: no amendment. This plan implements the existing ruling; no `.spec.md` is touched or declared.
- `CHANGELOG.md`: one `Fixed:` line (E-05).
- `DECISIONS.md`: no change; D55 is unaffected.

## Open questions

### OQ-01: Which clock do these two writers use?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE. Both write a dated record into an artifact's `## Workflow history` (the proposal fallback writes a backlog record that is filed later), and spec `2vev8j` 4.4 (approved, human-attested) rules every history writer UTC. `- Coverage-Checked:` is the same attested date as the history line written in the same call, so it follows the history clock rather than D55 (which governs human-facing NAMES, not attestation fields); keeping the two values identical also keeps the coverage record internally consistent. No maintainer decision required.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted bare-suite summary line and its full list of failing test ids, and the pasted five-TZ-suite summary line, both at the execution HEAD (`git rev-parse --short HEAD` pasted) and both captured before any source edit.
  - Observed evidence:
    Execution HEAD:
    ```
    $ git rev-parse --short HEAD
    a2bc77935
    ```
    Five TZ suites run at execution HEAD before any source edit:
    ```
    $ python3 -m pytest tests/test_history_date_clock.py tests/test_history_date_clock_parity.py tests/test_history_date_clock_readers.py tests/test_history_date_clock_sidecar.py tests/test_scaffold_history_clock.py
    ..........................                                               [100%]
    26 passed in 32.19s
    ```
    Bare suite baseline run at execution HEAD before any source edit:
    ```
    $ python3 -m pytest
    7615 passed, 2 skipped, 3 warnings in 1067.75s (0:17:47)
    ```
    Failing test IDs: empty set (0 failures).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted run of `python3 -m pytest -o addopts="" -v tests/test_history_date_clock_residual.py` at the UNEDITED HEAD showing at least one failure whose assertion message shows the local date where the UTC date was expected (produced by the E-02 tests driving `coverage_record.write` and `runner_shared.perform_coordinator_proposal_file`), plus `date -u` and `TZ=Pacific/Honolulu date` / `TZ=Pacific/Kiritimati date` pasted at the same moment, and the child's printed `agent_workflows.__file__` (or equivalent) showing it imported THIS checkout. If no zone is in skew at that moment, paste the skip output and re-run inside a skew window; a vacuous pass is not acceptable evidence.
  - Observed evidence:
    Dates at time of test run:
    ```
    $ date -u; TZ=Pacific/Honolulu date; TZ=Pacific/Kiritimati date
    Tue Oct 13 05:46:27 AM UTC 2026
    Mon Oct 12 07:46:27 PM HST 2026
    Tue Oct 13 07:46:27 PM +14 2026
    ```
    Child imported this checkout:
    `child: utc=2026-10-13 local=2026-10-12 pkg=<repo>/agent_workflows/__init__.py`

    Pasted failure run at unedited HEAD:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_history_date_clock_residual.py
    FAILED tests/test_history_date_clock_residual.py::test_coverage_record_write_records_utc_date[Pacific/Honolulu] - AssertionError: Coverage-Checked date 2026-10-12 did not match UTC date 2026-10-13 (local was 2026-10-12)
    FAILED tests/test_history_date_clock_residual.py::test_proposal_fallback_record_records_utc_date[Pacific/Honolulu] - AssertionError: Proposal fallback history date 2026-10-12 did not match UTC date 2026-10-13 (local was 2026-10-12)
    SKIPPED tests/test_history_date_clock_residual.py::test_coverage_record_write_records_utc_date[Pacific/Kiritimati]: Pacific/Kiritimati is not in skew at this hour (local date 2026-10-13 == UTC date 2026-10-13)
    SKIPPED tests/test_history_date_clock_residual.py::test_proposal_fallback_record_records_utc_date[Pacific/Kiritimati]: Pacific/Kiritimati is not in skew at this hour (local date 2026-10-13 == UTC date 2026-10-13)
    ========================= 2 failed, 2 skipped in 2.35s =========================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the `git diff` of `agent_workflows/coverage_record.py`; the pasted passing run of the E-02 coverage tests for both zones; the pasted passing run of `tests/test_coverage_record.py`; and one driven call under a skew-window TZ showing the written `- Coverage-Checked:` and `coverage pass` history lines carrying the UTC date.
  - Observed evidence:
    `git diff agent_workflows/coverage_record.py`:
    ```diff
    diff --git a/agent_workflows/coverage_record.py b/agent_workflows/coverage_record.py
    index 57fbaf059..8e705b632 100644
    --- a/agent_workflows/coverage_record.py
    +++ b/agent_workflows/coverage_record.py
    @@ -18,1 +17,0 @@
    -import datetime
    @@ -157,1 +155,3 @@
    -    today = datetime.date.today().isoformat()
    +    from agent_workflows import artifact_core as _core
    +
    +    today = _core.utc_history_date()
    ```
    Passing run of E-02 coverage tests for both zones:
    ```
    $ python3 -m pytest tests/test_history_date_clock_residual.py -k test_coverage_record_write_records_utc_date
    1 passed, 1 skipped in 3.51s
    ```
    Passing run of `tests/test_coverage_record.py`:
    ```
    $ python3 -m pytest tests/test_coverage_record.py
    7 passed in 3.84s
    ```
    Driven call under Honolulu skew window (local 2026-10-12, UTC 2026-10-13):
    ```
    child: utc=2026-10-13 local=2026-10-12 pkg=<repo>/agent_workflows/__init__.py
    - Coverage-Checked: 2026-10-13 by m
    - 2026-10-13 coverage pass (aw oc run): fingerprint a6407a54a8e1, model m
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the `git diff` of `agent_workflows/runner_shared.py` limited to the `_write_fallback_record` history line; the pasted passing run of the E-02 fallback tests for both zones; and the pasted passing run of `tests/test_run_proposal_channel.py`.
  - Observed evidence:
    `git diff agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 759efc90d..252cb44e8 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -41836,6 +41836,8 @@ def perform_coordinator_proposal_file(
             else:
    +            from agent_workflows import artifact_core as _core
    +
                 fallback_content = f"""- Id: {item_id6}
     - Status: open
     """
    @@ -41847,1 +41849,1 @@ def perform_coordinator_proposal_file(
     ## Workflow history
    -- {dt.date.today().strftime('%Y-%m-%d')} created (proposal fallback): Proposal from {item_id6}
    +- {_core.utc_history_date()} created (proposal fallback): Proposal from {item_id6}
    ```
    Passing run of E-02 fallback tests for both zones:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_history_date_clock_residual.py -k test_proposal_fallback_record_records_utc_date
    tests/test_history_date_clock_residual.py::test_proposal_fallback_record_records_utc_date[Pacific/Honolulu] PASSED [ 50%]
    tests/test_history_date_clock_residual.py::test_proposal_fallback_record_records_utc_date[Pacific/Kiritimati] SKIPPED [100%]
    1 passed, 1 skipped in 2.37s
    ```
    Passing run of `tests/test_run_proposal_channel.py`:
    ```
    $ python3 -m pytest tests/test_run_proposal_channel.py
    19 passed in 7.27s
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the pasted census command and its full output, the verdict table covering every hit, and an explicit statement that no HISTORY site remains on the local clock (or the id6 of each newly filed backlog item); the `git diff` of `CHANGELOG.md`; the pasted bare `python3 -m pytest` summary after all edits with its failing test ids compared against the V-01 set (no new failure); and the pasted five-TZ-suite run passing.
  - Observed evidence:
    Pasted census commands and outputs:
    ```
    $ rg -n "date\.today\(\)|datetime\.now\(\)\.|\.now\(\)\.date\(\)|_now\(\)\.date\(\)" agent_workflows
    agent_workflows/research_archive.py:291:    t = today or date.today()
    agent_workflows/plans_archive.py:198:    t = today or date.today()
    agent_workflows/backlog.py:1256:    today = datetime.date.today().strftime("%Y%m%d")
    agent_workflows/engine.py:475:    base = datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_workflows/engine.py:484:    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    agent_workflows/engine.py:6710:                            else datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_workflows/workflow_artifacts_prune.py:200:        today = datetime.date.today()
    agent_workflows/prompts.py:467:    return _now().date().isoformat()
    agent_workflows/set_records.py:176:    today = datetime.date.today().isoformat()
    agent_workflows/set_records.py:267:    date = datetime.date.today().strftime("%Y%m%d")
    agent_workflows/set_records.py:348:    today = datetime.date.today().strftime("%Y%m%d")
    agent_workflows/storage.py:347:        "created_at": datetime.now().isoformat(),
    agent_workflows/storage.py:390:        "attached_at": datetime.now().isoformat(),
    agent_workflows/artifact_adopt.py:779:    adopted_on = date_str or date.today().strftime("%Y%m%d")
    agent_workflows/specs.py:531:    return datetime.date.today().isoformat()
    agent_workflows/ipd_schema.py:504:    # and the check is pure (no repo, no cutover, no date.today()).
    agent_workflows/research_refs.py:689:    date_str = date.today().strftime("%Y%m%d") if raw_date is None else raw_date
    agent_workflows/upgrade_rehearsal.py:435:    stamp = stamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_workflows/upgrade_rehearsal.py:748:        "probed_at": datetime.now().isoformat(timespec="seconds"),
    agent_workflows/upgrade_rehearsal.py:971:            "created_at": datetime.now().isoformat(timespec="seconds"),
    agent_workflows/releases.py:84:    today = date.today().strftime("%Y%m%d")
    agent_workflows/ipd_authoring.py:529:    when = date.today().strftime("%Y-%m-%d")
    agent_workflows/ipd_authoring.py:581:            date=date.today().strftime("%Y%m%d"),
    agent_workflows/research_cmd.py:265:    today = date_str or date.today().strftime("%Y%m%d")
    agent_workflows/research_cmd.py:377:    today = date_str or date.today().strftime("%Y%m%d")

    $ rg -n "datetime\.now\(\s*\)|time\.localtime\(|time\.strftime\(\"%Y" agent_workflows -g '*.py'
    agent_workflows/run_analytics_cache.py:802:    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    agent_workflows/agy_sessions.py:326:                    s.start_time.strftime("%Y-%m-%d %H:%M:%S") if s.start_time else "-"
    agent_workflows/agy_sessions.py:329:                    s.end_time.strftime("%Y-%m-%d %H:%M:%S") if s.end_time else "-"
    agent_workflows/agy_sessions.py:358:        start_str = s.start_time.strftime("%Y-%m-%d %H:%M:%S") if s.start_time else "-"
    agent_workflows/agy_sessions.py:359:        end_str = s.end_time.strftime("%Y-%m-%d %H:%M:%S") if s.end_time else "-"
    agent_workflows/commit_lock.py:744:            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
    agent_workflows/runners_monitor.py:581:            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    agent_workflows/run_analytics_telemetry.py:687:    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(whole))
    agent_workflows/layout_migration.py:616:                timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    agent_workflows/layout_migration.py:743:            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:871:                    "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:872:                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:878:                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:898:                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1084:                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1095:                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1125:            "switched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1148:                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1160:            "retained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1186:                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1209:                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/layout_migration.py:1290:                "switched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/prompts.py:98:    return _dt.datetime.now()
    agent_workflows/config.py:1477:        install_timestamp or time.strftime("%Y-%m-%d", time.gmtime()), compact=False
    agent_workflows/engine.py:475:    base = datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_workflows/engine.py:484:    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    agent_workflows/engine.py:4354:    # record. A single install issues several independent `datetime.now()` timestamps
    agent_workflows/engine.py:6710:                            else datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_workflows/render_stream.py:1500:    t_str = time.strftime("%H:%M:%S", time.localtime(now_ts))
    agent_workflows/storage.py:347:        "created_at": datetime.now().isoformat(),
    agent_workflows/storage.py:390:        "attached_at": datetime.now().isoformat(),
    agent_workflows/upgrade_rehearsal.py:435:    stamp = stamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    agent_workflows/upgrade_rehearsal.py:748:        "probed_at": datetime.now().isoformat(timespec="seconds"),
    agent_workflows/upgrade_rehearsal.py:971:            "created_at": datetime.now().isoformat(timespec="seconds"),
    agent_workflows/pwatch.py:1026:            stamp = time.strftime("%Y%m%d-%H%M%S")
    agent_workflows/pwatch.py:1065:            now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now_epoch))
    agent_workflows/pwatch.py:1066:            now_display = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now_epoch))
    agent_workflows/install_history.py:103:    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    agent_workflows/compat_migration.py:568:            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/compat_migration.py:772:            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    agent_workflows/worktree_lease.py:730:        "allocated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    ```

    Full census verdict table:
    | File & line | Call | Verdict | Rationale |
    |---|---|---|---|
    | `research_archive.py:291` | `date.today()` | FILENAME | Read-only archive age calculation against local filename prefix `YYYYMMDD` (D55) |
    | `plans_archive.py:198` | `date.today()` | FILENAME | Read-only archive age calculation against local filename prefix `YYYYMMDD` (D55) |
    | `backlog.py:1256` | `datetime.date.today().strftime("%Y%m%d")` | FILENAME | Backlog filename prefix `YYYYMMDD`, local per D55 |
    | `engine.py:475, 484` | `datetime.now().strftime(...)` | NEITHER | Internal temporary run identifier |
    | `engine.py:6710` | `datetime.now().strftime(...)` | NEITHER | Telemetry / run timestamp |
    | `workflow_artifacts_prune.py:200` | `datetime.date.today()` | NEITHER | Read-only age prune comparison |
    | `prompts.py:467` | `_now().date().isoformat()` | FILENAME | Helper for prompt new filename prefix date derivation, local per D55 |
    | `set_records.py:176` | `datetime.date.today().isoformat()` | NEITHER | `close_on_answer` default argument; status update delegates to `backlog.run_set` |
    | `set_records.py:267` | `datetime.date.today().strftime("%Y%m%d")` | FILENAME | New spec filename prefix `YYYYMMDD`, local per D55 |
    | `set_records.py:348` | `datetime.date.today().strftime("%Y%m%d")` | FILENAME | New plan filename prefix `YYYYMMDD`, local per D55 |
    | `storage.py:347, 390` | `datetime.now().isoformat()` | NEITHER | Internal storage cache metadata |
    | `artifact_adopt.py:779` | `date.today().strftime("%Y%m%d")` | FILENAME | Adopted artifact filename prefix `YYYYMMDD`, local per D55 |
    | `specs.py:531` | `datetime.date.today().isoformat()` | NEITHER | `_today()` helper for local filename derivation in `run_new`, local per D55 |
    | `ipd_schema.py:504` | comment | NEITHER | Comment mentioning date.today() |
    | `research_refs.py:689` | `date.today().strftime("%Y%m%d")` | FILENAME | Research refs filename prefix `YYYYMMDD`, local per D55 |
    | `upgrade_rehearsal.py:435, 748, 971` | `datetime.now(...)` | NEITHER | Rehearsal test probe timestamps |
    | `releases.py:84` | `date.today().strftime("%Y%m%d")` | FILENAME | Release filename prefix `YYYYMMDD`, local per D55 |
    | `ipd_authoring.py:529` | `date.today().strftime("%Y-%m-%d")` | NEITHER | Document front-matter `- Date:` metadata, local per D55 |
    | `ipd_authoring.py:581` | `date.today().strftime("%Y%m%d")` | FILENAME | `run_scaffold` filename prefix, local per D55 |
    | `research_cmd.py:265, 377` | `date.today().strftime("%Y%m%d")` | FILENAME | Research note and comparison filename prefix `YYYYMMDD`, local per D55 |
    | `run_analytics_cache.py:802` | `time.strftime(..., time.gmtime())` | NEITHER | Cache telemetry timestamp, UTC |
    | `agy_sessions.py:326, 329, 358, 359` | `s.start_time.strftime(...)` | NEITHER | Session viewer display formatting |
    | `commit_lock.py:744` | `time.strftime(..., time.gmtime())` | NEITHER | Commit lock timestamp, UTC |
    | `runners_monitor.py:581` | `time.strftime(...)` | NEITHER | Interactive monitor display formatting |
    | `run_analytics_telemetry.py:687` | `time.strftime(..., time.gmtime())` | NEITHER | Telemetry timestamp, UTC |
    | `layout_migration.py` (14 calls) | `time.strftime(..., time.gmtime())` | NEITHER | Migration log and journal timestamps, UTC |
    | `prompts.py:98` | `_dt.datetime.now()` | NEITHER | Internal prompt cache timestamp helper |
    | `config.py:1477` | `time.strftime(..., time.gmtime())` | NEITHER | Config install timestamp fallback, UTC |
    | `engine.py:4354` | comment | NEITHER | Comment mentioning datetime.now() |
    | `render_stream.py:1500` | `time.strftime(..., time.localtime())` | NEITHER | Interactive terminal status rendering |
    | `pwatch.py:1026, 1065, 1066` | `time.strftime(...)` | NEITHER | Process watcher console display |
    | `install_history.py:103` | `time.strftime(..., time.gmtime())` | NEITHER | Install history timestamp, UTC |
    | `compat_migration.py:568, 772` | `time.strftime(..., time.gmtime())` | NEITHER | Migration record timestamps, UTC |
    | `worktree_lease.py:730` | `time.strftime(..., time.gmtime())` | NEITHER | Worktree lease timestamp, UTC |

    Statement on HISTORY sites:
    Every HISTORY site in `agent_workflows/` is accounted for. The two residual sites converted in E-03 (`coverage_record.write`) and E-04 (`runner_shared.perform_coordinator_proposal_file` -> `_write_fallback_record`) both now route through `artifact_core.utc_history_date()`. No residual HISTORY writer remains on the local clock, and no uncarried HISTORY site exists in `agent_workflows/`.

    `git diff CHANGELOG.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index d993b6e31..d5ed8dee2 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -58,6 +58,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Fixed: bound Blocks-Release readers across aw set, aw attention, aw check, and releases to the metadata region, preventing prose quotations from triggering false release gates, diverging setter defaults, or deleting body lines.
     - Fixed: corrected the message prefix printed by aw specs set --status when inheriting a release gate from a backlog item, so it attributes the notice to aw specs set rather than aw set.
     - Fixed: unified artifact workflow history dates onto the UTC clock across all history writers per spec 2vev8j Section 4.4, while human-facing artifact filename date prefixes deliberately remain on the local machine clock per DECISIONS.md D55.
    +- Fixed: the coverage record and the proposal-fallback record now stamp history dates in UTC like every other history writer, preventing workflow history date desync across UTC midnight.
     - Added: status setters (aw backlog set, aw specs set, and aw set) gain an opt-in --rewrite-citations flag (default off) to rewrite citing Scope-Paths in pending plans when relocating records, guarded by a fail-closed check that skips in-flight plans with live begin receipts (D159).
     - Fixed: widened the Section 8.8 control-character rejection predicate to reject Unicode bidirectional overrides and isolates (U+202A..U+202E, U+2066..U+2069), defending descriptive fields against display-reordering presentation attacks.
     - Changed: the three aw index <type> --check verbs (plans, prompts, and research) now emit canonical aw.agent/v1 result records under --agent and structured JSON under --json, completing the retirement of the legacy tab-separated form across all check surfaces.
    ```

    Bare `python3 -m pytest` suite post-edits:
    ```
    7617 passed, 4 skipped, 3 warnings in 781.08s (0:13:01)
    ```
    Comparison with V-01 baseline:
    - Baseline: 7615 passed, 2 skipped, 0 failures.
    - Post-edits: 7617 passed, 4 skipped, 0 failures.
    - Difference: +2 passed (the new residual tests), +2 skipped (Kiritimati runs of the 2 parameterized tests), 0 new failures.

    Five-TZ-suite run post-edits:
    ```
    $ python3 -m pytest tests/test_history_date_clock.py tests/test_history_date_clock_parity.py tests/test_history_date_clock_readers.py tests/test_history_date_clock_sidecar.py tests/test_scaffold_history_clock.py
    ..........................                                               [100%]
    26 passed in 22.97s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Follow the AGENTS.md execution contract: commit only the declared Scope-Paths through `aw commit 8chbn9 -- <paths>`, never `git add -A`, never push; verify `git diff --cached --name-only` before each commit; and paste actual runner output for every claimed test result, never a result you did not run. `- Scope-Paths:` is a declaration for the finalize scope reconciliation: an out-of-scope edit that proves necessary is made and justified with `--scope-reason <path>=<why>`, not a reason to stop; a NEW history site found by E-05 is filed, not fixed here. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item is `pass` with observed evidence. Lifecycle: under `aw oc run` / `aw agy run` the runner self-finalizes; a hand executor runs `aw ipd finalize 8chbn9 --actor <agent/model> --message <...> --apply`, never a hand-rolled `git mv`.
