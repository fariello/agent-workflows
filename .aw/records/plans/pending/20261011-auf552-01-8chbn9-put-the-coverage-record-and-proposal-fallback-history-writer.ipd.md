# IPD: Put the coverage-record and proposal-fallback history writers on the UTC clock so no history writer still reads the local date

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `auf552` reports that `## Workflow history` dates desync across UTC midnight because one writer reads the LOCAL date while another reads the UTC date. The backlog and `status_set` halves the item names were already converged by executed plan `5ivkdh` (Set `7qvs1c`) and are guarded by `tests/test_history_date_clock.py` and the derived-surface guard from executed plan `ayhveg`; both pass at this HEAD. But the defect CLASS the item describes is still live in two history writers that neither plan's census covered, because both were written AFTER `5ivkdh`'s E-05 audit (`coverage_record.py` first appears in commit `c4dc37203`, 2026-10-06; `5ivkdh` executed 2026-10-03). Measured live in this lane at HEAD `9e3b99850` under `TZ=Pacific/Honolulu` inside a skew window (local `2026-10-11`, UTC `2026-10-12`): `coverage_record.write` wrote `- 2026-10-11 coverage pass (aw oc run): fingerprint d6bcfbc5630b, model m` into a tracked plan's `## Workflow history`, while every `5ivkdh`-converted writer records `2026-10-12` at the same instant. The second site, `runner_shared.perform_coordinator_proposal_file`'s inner `_write_fallback_record`, stamps its `- <date> created (proposal fallback)` history line from `dt.date.today()`.
- Scope: IN: route the two residual HISTORY-record date writers (`coverage_record.write`'s workflow-history line and its `- Coverage-Checked:` date, and the proposal-fallback backlog record's `created` history line) through the existing `artifact_core.utc_history_date()`; add timezone-parameterized behavioral tests that drive both writers under a zone east and west of UTC and assert the UTC date; re-run the `date.today()`-class census over `agent_workflows/` and record a verdict for every site so no HISTORY writer is left unaccounted for. OUT, each with a reason under "Deferred": FILENAME date prefixes (D55 rules them LOCAL); the walkthrough `- Date:` front matter in `set_records.render_walkthrough` (front matter, not a history record); the `setdisp` dispatch unification; closing the backlog item (the runner sets `graduated`).
- Scope-Paths: agent_workflows/coverage_record.py, agent_workflows/runner_shared.py, tests/test_history_date_clock_residual.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
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

## Workflow history
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

- [ ] E-01 Record a live baseline at your own execution HEAD before any edit: run the bare suite (`python3 -m pytest`) and the five shipped TZ suites (`python3 -m pytest tests/test_history_date_clock.py tests/test_history_date_clock_parity.py tests/test_history_date_clock_readers.py tests/test_history_date_clock_sidecar.py tests/test_scaffold_history_clock.py`), and record the failure SET (test ids), not only the counts. The authoring numbers (`6 failed, 7213 passed, 2 skipped`; `26 passed`) are context only, since the suite drifts.
  - Depends on: none
  - Expected outcome: the pasted summary lines and failing test ids of both runs at the execution HEAD, recorded before any source edit.
  - Execution state: pending

- [ ] E-02 Create `tests/test_history_date_clock_residual.py` with two behavioral tests, each parameterized over `Pacific/Kiritimati` (UTC+14) and `Pacific/Honolulu` (UTC-10). (a) Coverage record: write a minimal plan file into a `tempfile` directory and call `coverage_record.write(plan, "pass", (), model="m", tool="aw oc run")` in a CHILD process whose `env=` carries `TZ=<zone>` and `AW_NO_REEXEC=1` (the subprocess shape `tests/test_history_date_clock.py` uses, which leaves the pytest worker's process-global time state untouched); assert the written `- <date> coverage pass` history line AND the `- Coverage-Checked: <date>` field both equal the child's UTC date, read from the child (`datetime.datetime.now(datetime.timezone.utc).date().isoformat()` printed beside the call) so a run straddling midnight cannot flake. (b) Proposal fallback: drive `runner_shared.perform_coordinator_proposal_file` with a `material` proposal and a patched `runner_shared.integration_lock` that yields `IntegrationLockOutcome(acquired=False, ...)` (the exact shape `tests/test_run_proposal_channel.py::test_coordinator_performer_held_integration_lock` uses), also in a child process under `TZ=<zone>`, and assert the `created (proposal fallback)` history line in the saved `proposals/*proposal.backlog.md` carries the child's UTC date. Each test also asserts the skew is OBSERVABLE (the child's local date differs from its UTC date) and calls `pytest.skip` with a stated reason when neither zone is in a skew window at run time, rather than passing vacuously. Run the new file at the E-01 HEAD and confirm it FAILS for the right reason on whichever zone is in skew.
  - Depends on: E-01
  - Expected outcome: a new test file whose tests exercise the real writers and assert on file content; a pasted run at the unedited HEAD showing at least one failure whose message names the local date where the UTC date was expected (or, outside every skew window, the explicit skip reason).
  - Execution state: pending

### Task group 2: Convert the two writers

- [ ] E-03 In `coverage_record.write`, replace `today = datetime.date.today().isoformat()` with `artifact_core.utc_history_date()` (function-local import, matching the module's "All first-party imports function-local" docstring rule), so both the `- Coverage-Checked:` field and the `- <date> coverage <verdict>` history line read UTC. Drop the `datetime` import only if nothing else in the module uses it. Do not change the line formats: `ipd_lint._COVERAGE_HIST_RE` and `coverage_record._CHECKED_LINE_RE` parse them.
  - Depends on: E-02
  - Expected outcome: `coverage_record.write` records the UTC date in both places; the E-02 coverage test passes under both zones; `tests/test_coverage_record.py` still passes.
  - Execution state: pending

- [ ] E-04 In `runner_shared.perform_coordinator_proposal_file`'s inner `_write_fallback_record`, replace `dt.date.today().strftime('%Y-%m-%d')` in the `- ... created (proposal fallback)` history line with `artifact_core.utc_history_date()` (function-local import, as the existing `from agent_workflows import artifact_core as _core` sites in that module do). Leave the fallback filename (`{pos:02d}-{item_id6}-proposal.{ext}`, which carries no date) and every other line unchanged.
  - Depends on: E-02
  - Expected outcome: the fallback backlog record's history line carries the UTC date; the E-02 fallback test passes under both zones; `tests/test_run_proposal_channel.py` still passes.
  - Execution state: pending

### Task group 3: Census and record

- [ ] E-05 Re-run the history-writer census over `agent_workflows/` with `rg -n "date\.today\(\)|datetime\.now\(\)\.|\.now\(\)\.date\(\)|_now\(\)\.date\(\)" agent_workflows`, and produce a verdict table with one row per hit: HISTORY (writes a `## Workflow history` record or a history-like attested date, and must be UTC), FILENAME (D55, stays local), or NEITHER (front matter, run id, telemetry, read-only comparison), each with a one-line reason. Confirm the only HISTORY rows are the two converted in E-03/E-04 and that each now reads `utc_history_date`. If a NEW HISTORY site is found, do NOT widen this plan's scope: file it with `aw backlog new --work-kind bug` (gated per AGENTS.md) and cite the new id6 in the table. Then add one `Fixed:` line to `CHANGELOG.md` under the pending release section stating that the coverage record and the proposal-fallback record now stamp history dates in UTC like every other history writer (no em or en dashes; user-facing prose).
  - Depends on: E-03, E-04
  - Expected outcome: a pasted census command and full verdict table with no HISTORY site left on the local clock or unaccounted for; one CHANGELOG line.
  - Execution state: pending

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
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE. Both write a dated record into an artifact's `## Workflow history` (the proposal fallback writes a backlog record that is filed later), and spec `2vev8j` 4.4 (approved, human-attested) rules every history writer UTC. `- Coverage-Checked:` is the same attested date as the history line written in the same call, so it follows the history clock rather than D55 (which governs human-facing NAMES, not attestation fields); keeping the two values identical also keeps the coverage record internally consistent. No maintainer decision required.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted bare-suite summary line and its full list of failing test ids, and the pasted five-TZ-suite summary line, both at the execution HEAD (`git rev-parse --short HEAD` pasted) and both captured before any source edit.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted run of `python3 -m pytest -o addopts="" -v tests/test_history_date_clock_residual.py` at the UNEDITED HEAD showing at least one failure whose assertion message shows the local date where the UTC date was expected (produced by the E-02 tests driving `coverage_record.write` and `runner_shared.perform_coordinator_proposal_file`), plus `date -u` and `TZ=Pacific/Honolulu date` / `TZ=Pacific/Kiritimati date` pasted at the same moment. If no zone is in skew at that moment, paste the skip output and re-run inside a skew window; a vacuous pass is not acceptable evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `git diff` of `agent_workflows/coverage_record.py`; the pasted passing run of the E-02 coverage tests for both zones; the pasted passing run of `tests/test_coverage_record.py`; and one driven call under a skew-window TZ showing the written `- Coverage-Checked:` and `coverage pass` history lines carrying the UTC date.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `git diff` of `agent_workflows/runner_shared.py` limited to the `_write_fallback_record` history line; the pasted passing run of the E-02 fallback tests for both zones; and the pasted passing run of `tests/test_run_proposal_channel.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted census command and its full output, the verdict table covering every hit, and an explicit statement that no HISTORY site remains on the local clock (or the id6 of each newly filed backlog item); the `git diff` of `CHANGELOG.md`; the pasted bare `python3 -m pytest` summary after all edits with its failing test ids compared against the V-01 set (no new failure); and the pasted five-TZ-suite run passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Follow the AGENTS.md execution contract: commit only the declared Scope-Paths through `aw commit 8chbn9 -- <paths>`, never push, and paste actual runner output for every claimed test result. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item is `pass` with observed evidence; use `aw ipd finalize` (or the runner's self-finalize) for the terminal transition.
