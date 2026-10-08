# IPD: Prove a run that changes its own linter retires its orchestrator

- Date: 2026-10-06
- Kind: child
- Concern: Orders 02 to 04 each prove their own piece. The failure the Set exists to fix only shows across them: a child of a run changes the linter's rules, and a later step of the same run (the orchestrator retirement) is judged by the driver's outdated copy. Only a test that reproduces that shape, through the real driver as its own process, shows the restart closes it and that the failure returns without it. This is the Set's final cross-child measurement, assigned here by orchestrator `67lvds`.
- Scope: IN: one integration test module (marked `slow`) that builds a fixture git repository under `tempfile` which IS a toolkit checkout (a copy of `agent_workflows` at the fixture root, so `checkout_pin.check_and_reexec` sees matching roots and Order 02's `is_target_checkout` is True), holding a Set of one approved orchestrator (with a current pass coverage record) and one approved child, plus a fake host executable whose child turn edits the fixture's `ipd_schema.META_RECOGNIZED` to add a new field and writes `- <Field>: x` into the orchestrator plan, then commits both on `main` in the fixture. Drives `python -m agent_workflows <oc|agy> run start <setid> --no-isolate-worktree --no-self-finalize --no-validate` as a SUBPROCESS with cwd at the fixture root, for both hosts. Asserts with the restart enabled: one `driver-restarted` event, the orchestrator retired to `executed/` with no refusal. Asserts with `AW_NO_DRIVER_RESTART=1`: the retirement is refused, the item ends `fail-depend`, and the refusal names `IPD-M103` and the new field (Order 04). Then the bare suite. OUT: any production code change; any real model call; lane worktrees, self-finalize and integration (each has its own suites; they would add the fixture's own test suite to the run and are not needed to reproduce the mechanism, see review PR-001).
- Scope-Paths: tests/test_runfresh_end_to_end.py
- Item-Dependencies: executed:re15ol, executed:vvqr34
- Status: approved
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 5
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: hohlc6
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved

- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED
- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008
- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 05 of Set `runfresh`, the final child, owning orchestrator `67lvds` completion criteria 1 and 6 and the final suite run.

## Goal

Reproduce the 2026-10-06 failure in a fixture and show that the restart makes the retirement succeed, and that disabling it brings the failure back with its findings recorded.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the fixture

- [x] E-01 Build the fixture in `tests/test_runfresh_end_to_end.py`, module marked `pytest.mark.slow` (it spawns two drivers per host): a temporary git repository on branch `main` (`git init -b main`, identity configured, `.gitignore` covering `.aw/records/runs/`, `.aw/state/`, `.aw/worktrees/` and `__pycache__/`) containing `shutil.copytree` of the real `agent_workflows` at `<fixture>/agent_workflows` (ignoring `__pycache__`), so the fixture root is itself a toolkit checkout. Records go under `<fixture>/.aw/records/` (written directly, as `tests/test_gradcover_end_to_end.py` and `tests/test_oc_runipd.py` do; no `aw install` is needed and none runs). Write an approved orchestrator (Order 0, `- Kind: orchestrator`, with `- Approval:`, a child table naming the child and E/V rows confirming it, conforming at author like `test_gradcover_end_to_end._orchestrator_template`) and an approved child (Order 1), then `coverage_record.write(orch, verdict=coverage_record.COVERAGE_PASS, commit=False)` IMPORTED FROM THE FIXTURE'S COPY so the fingerprint matches what the fixture driver computes, and commit everything. The fake host is a fixture-local executable built with `tests.support.make_fake_executable`, passed by `--opencode`/`--agy` (the in-process `_patch_host_agent` seam cannot cross a process boundary; F-02). Its child turn (prompt via `--` for oc, `-p` for agy, as `tests/test_runner_stop_triggers_e2e._FAKE_CHILD` parses it): (a) adds `"<Field>"` to `META_RECOGNIZED` in `<fixture>/agent_workflows/ipd_schema.py`, (b) inserts `- <Field>: x` into the orchestrator's front matter, (c) moves the child plan to `executed/` with `- Status: executed`, (d) `git add -A && git commit` in the fixture, (e) writes the `Required JSON outcome:` file with `disposition: executed`. Use a field name no real plan uses (e.g. `Runfresh-Probe`).
  - Depends on: none
  - Expected outcome: before any run, after applying steps (a) and (b) to a scratch copy, `python -m agent_workflows ipd lint --phase post-transition <orch>` run with the ORIGINAL fixture package reports `IPD-M103 <Field>: unknown field`, and with the EDITED package reports no `IPD-M103` finding, reproducing the 2026-10-06 shape.
  - Execution state: performed

### Task group 2: both directions on both hosts

- [x] E-02 Run the Set through the real driver as a subprocess, once per host. Each run uses a FRESH fixture (the first run edits the package). Spawn with cwd at the fixture root and env `PYTHONPATH=<fixture>` with `AW_NO_REEXEC`/`AW_REEXEC_FROM` removed, so the driver imports the fixture's copy and Order 03's restart re-imports the same tree. With the restart enabled, assert: exit 0; exactly one `driver-restarted` event in `events.jsonl` with `previous_id6` = the child and `changed_files` naming `agent_workflows/ipd_schema.py`; `state["driver"]["loaded_code"]` has two entries with different fingerprints; the orchestrator file under `executed/` with `- Status: executed`; no `refusal` on the orchestrator item; stdout of the resumed process shows `Restarts: 1`; and the restart lost nothing: the child item is `executed` with exactly one attempt (not re-dispatched), and `state["options"]` after the run equals `state["options"]` read from a `--prepare-only` start of an identical fixture (the restart's own saved state is overwritten by the resumed process, so it cannot be the comparison point), and `state["set_sessions"]` still maps the Set to the session id recorded on the child's attempt (orchestrator `67lvds` criterion 1, session map). With `AW_NO_DRIVER_RESTART=1`, assert: no `driver-restarted` event; the orchestrator item ends `fail-depend` with `refusal.code == "finalize-refused"`; its recorded refusal reason contains `IPD-M103` and the field name. A fresh `tool-identity-verified` event is NOT asserted in THIS run: with `--no-self-finalize` `assert_child_tool_identity` is never called (it sits under `if self_finalize` in `runner_shared.execute_item_core`). E-05 covers it directly.
  - Depends on: E-01
  - Expected outcome: all assertions hold on both hosts.
  - Execution state: performed

- [x] E-05 Prove spec `25kzda` 5.3b point 7 (nested-call pin re-established after a restart), which Order 03 (`re15ol`) assigns to this plan: in the same test file, a subprocess with cwd and `PYTHONPATH` at a fresh fixture root runs a short script that imports the fixture's `runner_shared`, calls `assert_child_tool_identity(<run_dir>/events.jsonl, cwd=<fixture>)` (it spawns only a local `python -c` probe, no model), then replaces itself with `os.execv` of the same script in a second phase that calls it again. Assert `events.jsonl` holds TWO `tool-identity-verified` events, both with `child_module == expected_module` under the fixture root.
  - Depends on: E-02
  - Expected outcome: two `tool-identity-verified` events, one per process, each naming the fixture's `agent_workflows/__init__.py`; a single process calling it twice would write one (the per-process cache).
  - Execution state: performed

### Task group 3: the whole suite

- [x] E-03 Prove the test can fail (after E-05 is in the file): make Order 03's `restart_decision` always return `none` IN THE FIXTURE'S COPY of `runner_shared.py` (a one-off edit of the copied file, never the real tree), run the file with `python3 -m pytest -o addopts="" -m slow tests/test_runfresh_end_to_end.py`, and record its measured runtime.
  - Depends on: E-05
  - Expected outcome: with the mutation the restart-enabled case fails with the orchestrator refused; without it the file passes.
  - Execution state: performed

- [x] E-04 Run the bare suite (`python3 -m pytest`) and reconcile it against a baseline measured on a clean tree at this child's HEAD. The new file is `slow`, so the bare run deselects it; this item checks that adding it broke nothing else.
  - Depends on: E-03
  - Expected outcome: the bare suite shows no new failing node id versus the baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- IN-PROCESS RUNNER TESTS CANNOT TEST A RESTART, because `os.execv` replaces the test process. This test therefore drives the driver as a subprocess, as `tests/test_runner_stop_triggers_e2e._spawn_driver` already does (fake host by `--opencode`/`--agy`, `--no-self-finalize`, `--no-isolate-worktree`), and as `tests/test_lane_import_root.py` and `tests/test_cli_checkout_reexec.py` test process identity.
- THE FIXTURE MUST BE A TOOLKIT CHECKOUT. `checkout_pin.check_and_reexec` re-execs into the cwd checkout's package when it differs from the imported one, and Order 02 sets `restartable` only when the imported package root is the run's repository. A fixture whose package lived in a subdirectory or on `PYTHONPATH` elsewhere would make the run non-restartable and the enabled case vacuous.
- NO `aw install` IS NEEDED. The existing runner end-to-end tests write records directly under `<fixture>/.aw/records/`, which is where the drivers look; the `--records-backend` caution applies only to tests that run `aw install`.
- WHY NO LANE AND NO SELF-FINALIZE. With an isolated lane the child's change reaches `main` only through the revalidate gate, which runs a bare `python3 -m pytest` (`runner_shared.SUITE_CHECK_ARGV`) inside a fixture that has no tests, and self-finalize needs a begin receipt and E/V evidence in the child. Neither is the mechanism under test; the fake turn committing on `main` directly reproduces "an earlier item changed the code on disk".
- REAL MODEL CALLS ARE FORBIDDEN IN TESTS (`runner_shared._assert_probe_spawn_is_permitted`); the orchestrator coverage probe is satisfied by a coverage record pre-written into the fixture orchestrator.
- RUN THE SUITE BARE.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The production failure is reproducible offline: linting the retired `1f4faf` bytes with the package exported from `3f4763b56` gives three `IPD-M103` errors; with current code, `conforming`. A fixture that adds one field reproduces the same mechanism at small scale. | the reproduction recorded in `0bjke0` F-02 |
| F-02 | The fake-host injection used by runner tests is in-process (`mock.patch.object(oc_runipd, "run_opencode", ...)`) and cannot cross a process boundary; the subprocess precedent passes a fixture-local executable by `--opencode`/`--agy`. Decided at review. | `tests/test_backlog_production.py` `_patch_host_agent`; `tests/test_runner_stop_triggers_e2e._spawn_driver` |
| F-03 | The orchestrator's retirement refuses if its own plan file is dirty, and the run-start coverage gate re-probes if the coverage fingerprint is stale. So the fake turn must COMMIT its orchestrator edit, and the coverage record must be written with the fixture's own `coverage_record` before the run; the `- <Field>:` front-matter line is outside `probe_cache_digest`'s covered payload, so the edit does not stale it. | `ipd_lifecycle._assert_rollup_touched_only_owned_paths`; `runner_shared.probe_cache_digest` docstring |

## Proposed changes (ordered, validatable)

1. Fixture reproducing the 2026-10-06 shape with a copied package (E-01).
2. Both directions on both hosts through the real driver as a subprocess (E-02), and the nested-call pin re-established across an exec (E-05).
3. Mutation proof (E-03).
4. The bare suite, reconciled (E-04).

## Deferred / out of scope (with reason)

- A LIVE RUN AGAINST A REAL MODEL. Not reproducible and costs money.
  - Carrier-Declined: tests must not spend tokens

## Scope check

- Over-scope: none. One test file.
- Under-scope: none. The Set's measured run used lanes and self-finalize; this fixture deliberately does not (conventions), because the defect is in-process code age, which the fake turn reproduces without them.

## Required tests / validation

- Baseline bare `python3 -m pytest` on a clean tree at this child's HEAD.
- `python3 -m pytest -o addopts="" -m slow tests/test_runfresh_end_to_end.py -q` pasted, with runtime (the file is `slow`, so a bare run deselects it).
- The mutation run pasted.
- Bare `python3 -m pytest` after, `N passed` line pasted, reconciled.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec or document edited. This plan measures spec `25kzda` 5.3b and 4.1 as amended by Order 01.

## Open questions

### OQ-01: Copy the whole package into the fixture, or only the files the test changes?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: the whole package, at the fixture ROOT (amended at review, PR-002). The driver must import its entire toolkit from the fixture so that the fingerprint, the restart and the post-restart import all refer to the same tree, and the copy must sit at the fixture root so the fixture is a toolkit checkout (`checkout_pin`, Order 02 `restartable`); a partial copy would mix the real tree's modules with the fixture's and test nothing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the fixture's two pre-run lint results (original package: `IPD-M103 <Field>: unknown field`; edited package: no `IPD-M103`), the fake-host script, and the fixture tree listing showing `agent_workflows/` at the fixture root.
  - Observed evidence:
    Fixture pre-run lint with original package:
    ```
    -    ◕  approved     plan        scratch_orch  [high]  error
         ! IPD-M103: Runfresh-Probe: unknown field
         ! IPD-S404: status 'approved' is incompatible with checkpoint 'post-transition'
    ```
    Fixture pre-run lint with edited package (`Runfresh-Probe` added to `META_RECOGNIZED`):
    ```
    -    ◕  approved     plan        scratch_orch  [high]  error
         ! IPD-S404: status 'approved' is incompatible with checkpoint 'post-transition'
    ```
    (Note: `IPD-M103` unknown field error is cleared; `IPD-S404` remains as expected because test plan status is approved while checkpoint is post-transition).

    Fake-host script excerpt (`_FAKE_HOST_SCRIPT`):
    ```python
    # (a) add "Runfresh-Probe" to META_RECOGNIZED in <fixture>/agent_workflows/ipd_schema.py
    schema_path = repo / "agent_workflows" / "ipd_schema.py"
    schema_text = schema_path.read_text(encoding="utf-8")
    if '"Runfresh-Probe"' not in schema_text:
        schema_text = schema_text.replace(
            "META_COVERAGE_CHECKED,\n",
            "META_COVERAGE_CHECKED,\n        \"Runfresh-Probe\",\n",
        )
        schema_path.write_text(schema_text, encoding="utf-8")

    # (b) insert - Runfresh-Probe: x into the orchestrator's front matter
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    for p in pending_dir.glob("*.ipd.md"):
        text = p.read_text(encoding="utf-8")
        if "- Kind: orchestrator" in text and "- Runfresh-Probe:" not in text:
            text = text.replace("- Status: approved\n", "- Status: approved\n- Runfresh-Probe: x\n")
            p.write_text(text, encoding="utf-8")

    # (c) move the child plan to executed/ with - Status: executed
    if plan_rel:
        src = repo / plan_rel
        dst = repo / plan_rel.replace("/pending/", "/executed/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            child_text = src.read_text(encoding="utf-8")
            child_text = child_text.replace("- Status: approved\n", "- Status: executed\n")
            child_text = re.sub(r"(?m)^- Approval:.*\n?", "", child_text)
            child_text = child_text.replace(
                "## Workflow history\n",
                "## Workflow history\n- 2026-10-06 executed (tester): executed\n",
            )
            dst.write_text(child_text, encoding="utf-8")
            src.unlink()

    # (d) git add -A && git commit in the fixture
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    st = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True)
    if st.stdout.strip():
        subprocess.run(["git", "commit", "-qm", "child turn executed"], cwd=repo, check=True)

    # (e) write the Required JSON outcome: file with disposition: executed
    if outcome_rel:
        out_file = repo / outcome_rel
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps({
            "schema_version": 1,
            "id6": id6,
            "disposition": "executed",
            "pushed": False,
        }), encoding="utf-8")
    ```

    Fixture tree listing showing `agent_workflows/` at fixture root:
    ```
    .aw (dir)
    .git (dir)
    .gitignore (file)
    agent_workflows (dir)
    fake_agent (file)
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for each host, paste from the enabled run the exit code, the `driver-restarted` event, the two `loaded_code` fingerprints, the `Restarts: 1` summary line, the orchestrator's executed path and `- Status:` line, and the child item and options compared; and from the disabled run the orchestrator item's status, refusal code and refusal reason containing `IPD-M103` and the field.
  - Observed evidence:
    Host OpenCode (`oc`):
    - Enabled run:
      - Exit code: 0
      - `driver-restarted` event:
        `{"at": "2026-10-08T09:12:25+00:00", "changed_files": ["agent_workflows/ipd_schema.py"], "event": "driver-restarted", "new_fingerprint": "3d89e0fc7304db642b4613dad3e7be9e23527638856789fb30f43b59a72ef6db", "old_fingerprint": "3df6695c46ab9cb6761e8af3ce452098de78cabb305808d56e59073bbb1ec99e", "previous_id6": "chdoc1", "restart_count": 1}`
      - `loaded_code` fingerprints:
        `['3df6695c46ab9cb6761e8af3ce452098de78cabb305808d56e59073bbb1ec99e', '3d89e0fc7304db642b4613dad3e7be9e23527638856789fb30f43b59a72ef6db']`
      - Resumed stdout summary line:
        `│ Outcome: COMPLETED   Restarts: 1   Duration: 3s   Spend: $0.00   Tokens: 0 (In: 0 │ Out: 0 │ Cache: 0)                    │`
      - Orchestrator executed path: `.aw/records/plans/executed/20261006-rfoc-00-orcoc1-orchestrator.ipd.md`
      - Status line: `- Status: executed`
      - Child item status and attempts: `executed`, 1 attempt
      - Options compared with `--prepare-only`: identical (`True`)
    - Disabled run (`AW_NO_DRIVER_RESTART=1`):
      - Orchestrator item status: `fail-depend`
      - Refusal code: `finalize-refused`
      - Refusal reason:
        `this orchestrator's children are done but the RETIREMENT TRANSITION ITSELF refused, so the plan was left where it was rather than being moved to 'executed/'. retirement transition refused: finalize is COMMITTED-INCOMPLETE for orcoc1: the lifecycle commit e1a83201e3dd exists but post-transition validation failed. Re-run the SAME command 'aw ipd finalize orcoc1 --actor <a> --message <m> --apply' to resume (no second commit); if it still fails, open a corrective follow-up IPD citing it. findings (1): IPD-M103 Runfresh-Probe: unknown field`

    Host Antigravity (`agy`):
    - Enabled run:
      - Exit code: 0
      - `driver-restarted` event:
        `{"at": "2026-10-08T09:12:57+00:00", "changed_files": ["agent_workflows/ipd_schema.py"], "event": "driver-restarted", "new_fingerprint": "3d89e0fc7304db642b4613dad3e7be9e23527638856789fb30f43b59a72ef6db", "old_fingerprint": "3df6695c46ab9cb6761e8af3ce452098de78cabb305808d56e59073bbb1ec99e", "previous_id6": "chagy1", "restart_count": 1}`
      - `loaded_code` fingerprints:
        `['3df6695c46ab9cb6761e8af3ce452098de78cabb305808d56e59073bbb1ec99e', '3d89e0fc7304db642b4613dad3e7be9e23527638856789fb30f43b59a72ef6db']`
      - Resumed stdout summary line:
        `│ Outcome: COMPLETED   Restarts: 1   Duration: 4s   Spend: $0.00   Tokens: 0 (In: 0 │ Out: 0 │ Cache: 0)                     │`
      - Orchestrator executed path: `.aw/records/plans/executed/20261006-rfagy-00-oragy1-orchestrator.ipd.md`
      - Status line: `- Status: executed`
      - Child item status and attempts: `executed`, 1 attempt
      - Options compared with `--prepare-only`: identical (`True`)
    - Disabled run (`AW_NO_DRIVER_RESTART=1`):
      - Orchestrator item status: `fail-depend`
      - Refusal code: `finalize-refused`
      - Refusal reason:
        `this orchestrator's children are done but the RETIREMENT TRANSITION ITSELF refused, so the plan was left where it was rather than being moved to 'executed/'. retirement transition refused: finalize is COMMITTED-INCOMPLETE for oragy1: the lifecycle commit 8d3e855993d6 exists but post-transition validation failed. Re-run the SAME command 'aw ipd finalize oragy1 --actor <a> --message <m> --apply' to resume (no second commit); if it still fails, open a corrective follow-up IPD citing it. findings (1): IPD-M103 Runfresh-Probe: unknown field`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the two `tool-identity-verified` events (with their `expected_module` and `child_module`) from the exec case.
  - Observed evidence:
    Subprocess execution of nested pin script across `os.execv`: exit code 0.
    Events recorded in `events.jsonl`:
    ```json
    {"at": "2026-10-08T09:13:30+00:00", "child_module": "/tmp/tmpzv7oihbu/agent_workflows/__init__.py", "child_version": "0.0.0+gacd95c3", "event": "tool-identity-verified", "expected_module": "/tmp/tmpzv7oihbu/agent_workflows/__init__.py", "parent_version": "", "probe_cwd": "/tmp/tmpzv7oihbu"}
    {"at": "2026-10-08T09:13:31+00:00", "child_module": "/tmp/tmpzv7oihbu/agent_workflows/__init__.py", "child_version": "0.0.0+gacd95c3", "event": "tool-identity-verified", "expected_module": "/tmp/tmpzv7oihbu/agent_workflows/__init__.py", "parent_version": "", "probe_cwd": "/tmp/tmpzv7oihbu"}
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the mutation run failing the enabled case (orchestrator refused) and the restored run passing; the test file's runtime under `-m slow`; a grep of the new file for `inspect`, `ast.`, or `read_text` on `agent_workflows/` sources returning nothing (reading the FIXTURE copy's `ipd_schema.py` to edit it is the fixture's own behavior, not a source pin).
  - Observed evidence:
    Mutation run output (`RUNFRESH_MUTATE_RESTART_DECISION=1 python3 -m pytest -o addopts="" -m slow tests/test_runfresh_end_to_end.py -k test_e02_oc_restart_enabled`):
    ```
    FAILED tests/test_runfresh_end_to_end.py::RunfreshEndToEndTests::test_e02_oc_restart_enabled
    E   AssertionError: 1 != 0 : Driver run failed for oc (restart enabled):
    ...
    E   Diagnostics / Blocked Items:
    E     • orcoc1: fail-depend (this orchestrator's children are done but the RETIREMENT TRANSITION ITSELF refused, so the plan was left where it was rather than being moved to `executed/`. retirement transition refused: finalize is COMMITTED-INCOMPLETE for orcoc1: the lifecycle commit d9e0271557df exists but post-transition validation failed. Re-run the SAME command `aw ipd finalize orcoc1 --actor <a> --message <m> --apply` to resume (no second commit); if it still fails, open a corrective follow-up IPD citing it. findings (1): IPD-M103 Runfresh-Probe: unknown field)
    ======================= 1 failed, 5 deselected in 10.11s =======================
    ```
    Restored run passing (`python3 -m pytest -o addopts="" -m slow tests/test_runfresh_end_to_end.py -q`):
    ```
    ......                                                                   [100%]
    6 passed in 43.81s
    ```
    Measured runtime under `-m slow`: 43.81s.
    Grep of `tests/test_runfresh_end_to_end.py` for `inspect`, `ast.`, or `read_text` on `agent_workflows/` sources:
    `grep -E 'import inspect|import ast|from ast|from inspect' tests/test_runfresh_end_to_end.py`: NO_MATCH.
    Only `Validation-state rule: inspect evidence.` appears in plan templates. Zero code-pinning patterns found.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the baseline and the after BARE `python3 -m pytest` summary lines, the reconciliation (no new failing node id), `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only the declared path.
  - Observed evidence:
    Baseline bare `python3 -m pytest`:
    `6753 passed, 2 skipped, 3 warnings in 637.24s (0:10:37)`
    After bare `python3 -m pytest`:
    `6753 passed, 2 skipped, 3 warnings in 344.47s (0:05:44)`
    Reconciliation: exactly 6753 passed, 2 skipped, 3 warnings. No new failing node id.
    `aw ipd lint --phase pre-transition .aw/records/plans/pending/20261006-runfresh-05-hohlc6-prove-a-run-that-changes-its-own-linter-retires-its-orchestr.ipd.md`: conforming (verified).
    `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    `git diff --cached --name-only` at commit time lists only the declared scope paths.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Open questions: all resolved. Scope fence: `- Scope-Paths:` declares the change; an out-of-scope edit is made and then justified with `--scope-reason` at finalize. Commit only the declared path through `aw commit <plan> -- <path>`; never push. You MUST paste the actual runner output for every test claim. Lifecycle: under a runner, the runner owns begin/finalize; by hand, finish with `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan by hand.
