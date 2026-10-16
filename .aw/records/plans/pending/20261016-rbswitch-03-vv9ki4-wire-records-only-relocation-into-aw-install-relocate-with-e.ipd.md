# IPD: Wire records-only relocation into aw install --relocate with end-to-end tests and docs

- Date: 2026-10-16
- Kind: child
- Concern: After Orders 01 and 02 (`s07f73`, `fxbm7j`), `aw install <repo> --records-backend home` on a `private-target` repo with records refuses ("not supported by reinstall yet (backlog wbz75c)") and the executor exists only as a Python API. Set `cfgreloc` Order 05 (`ozr356`) adds `aw install --relocate`, `--relocate-resume`, `--relocate-rollback`, a `--dry-run` preview and a pending-journal guard in `cli._install_one`, all for full placement switches. Backlog `wbz75c` is closed only when the records-only move is reachable from the same flags, previewable, recoverable and documented.
- Scope: IN: in `cli._run_install`, on `RecordsRootSwitchRequired` with `reason="records"`: without `--relocate` keep refusing, message naming `--relocate` and the `--dry-run` preview; with `--relocate --dry-run` render the Order 02 plan and write nothing; with `--relocate` (one confirm, `-y` proceeds, interactive default NO) call `execute_records_root_switch` and continue into the normal same-root install; `--relocate-resume`/`--relocate-rollback` and the `cli._install_one` pending-journal guard already dispatch on journal mode (`fxbm7j` E-04), so verify them end-to-end for a records journal; an `allow_records_switch` keyword on `install_wizard.resolve_policy_noninteractive`/`collect_policy_interactive`; `placement_switch.render_plan` accepting a records-mode plan; the spec Section 8.2 implementation-status sentence; CHANGELOG and README. OUT: companion records (`n9vd2h`); new CLI flags (the `ozr356` flags are reused, not duplicated).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/install_wizard.py, agent_workflows/placement_switch.py, tests/test_records_root_switch_cli.py, tests/test_records_root_switch_guard.py, CHANGELOG.md, README.md, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: executed:fxbm7j, executed:ozr356
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: wbz75c
- Blocks-Release: next
- Set: rbswitch
- Order: 3
- Highest E allocated: 05
- Author: opencode
- Id: vv9ki4

## Workflow history
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set rbswitch graduating backlog wbz75c.

## Goal

`aw install <repo> --records-backend <new> --relocate` moves an installed repository's records to the new backend in one command, `--dry-run` shows exactly what moves first, an interrupted move can be finished or undone with the existing recovery flags, and the refusal without `--relocate` tells the user how.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: CLI

- [ ] E-01 Re-measure at execution HEAD: `grep -n` in `agent_workflows/cli.py` for `--relocate`, `relocate_resume`, `relocate_rollback`, `placement_switch_status(`, `execute_placement_switch(`, `render_plan(`, `PlacementSwitchRequired`, `RecordsRootSwitchRequired`, and in `install_wizard.py` for `allow_placement_switch`. If the `ozr356` flags or `fxbm7j`'s `execute_records_root_switch` are absent, stop and report. Then in `install_wizard`: add keyword-only `allow_records_switch: bool = False` to `resolve_policy_noninteractive` and `collect_policy_interactive` (forwarded), which suppresses the Order 01 `records_root_switch` raise for `reason="records"` only (a `reason="companion"` hit always raises) so the caller receives the new policy; change the `reason="records"` message to "Changing the records backend from <old> (<current_root>) to <new> (<target_root>) moves <n> record files. Preview with --relocate --dry-run, then rerun with --relocate." (no em or en dashes). Update the Order 01 assertions in `tests/test_records_root_switch_guard.py` that pin the old message (its `backlog wbz75c` substring AND the `would leave 1 record files` substring of `s07f73` E-05 test (3), both of which the new wording drops) to assert `--relocate` and `moves 1 record files` instead (the behavior they pin, exit `1` and a byte-identical `project.json`, is unchanged).
  - Depends on: none
  - Expected outcome: refusal names the remedy; `resolve_policy_noninteractive(..., explicit_backend="home", allow_records_switch=True)` returns a `home` policy for a `private-target` repo with records.
  - Execution state: pending

- [ ] E-02 Execute and preview path in `cli._run_install`, mirroring `ozr356` E-02/E-06 and sharing its code rather than duplicating it: pass `allow_records_switch=getattr(args, "relocate", False)` to `collect_policy_interactive`; at the Order 01 `records_root_switch` check, on a hit without `--relocate` raise as today; with `--relocate` build `switch_plan = placement_switch.plan_records_root_switch(str(repo_root), policy)` and route it into the SAME relocation branch `ozr356` uses for a placement switch (preview via `render_plan`, blocker refusal naming every blocker id with exit `1`, `--dry-run` prints "[DRY RUN] No changes written to filesystem or Git state." and continues, otherwise the single relocation confirm after `_preflight_warnings`/`_diagnostics_ok`), with the executor call selected by the plan's `direction` (`records-to-home`/`records-to-target` -> `execute_records_root_switch`). Extend `placement_switch.render_plan` so a records-mode plan prints "records only" instead of a retire side and lists the config `rewrite` items. On success print the receipt summary and, for `records-to-home`, "<n> tracked record files were removed from the target and left staged; review with git status and commit when ready. Records now live in <dir> and are no longer versioned by this repository."; for `records-to-target`, "<n> record files were staged as added; commit them when ready." Then continue into `persist_project_policy` (now a same-root write) and `_install_one`, which scaffolds the new root.
  - Depends on: E-01
  - Expected outcome: one command performs a records-only move and installs; `--dry-run` writes nothing; a blocker exits `1`; a declined confirm writes nothing.
  - Execution state: pending

- [ ] E-03 Commit-offer interaction. For `records-to-target` the layout is tracked, so `engine.prompt_and_run_commit` runs under `-y` and commits installer paths path-scoped; do NOT add the switch's staged records or `project.json` to its `files_to_commit`, and assert in the E-05 test that the moved records stay staged `A` and uncommitted. For `records-to-home` the delivery mode stays `tracked`, so `prompt_and_run_commit` also runs: assert it does not sweep the staged record deletions into its commit (it commits with `git commit -- <paths>`, path-scoped). In BOTH directions `project.json` is NOT left staged: `engine.install_into_repo` calls `engine.stage_tracked_policy_files`, which stages `.aw/config/project.json` (its `config_project` git policy is `target-git`) and appends it to `installed`, so under `-y` the installer commits it path-scoped (review probe: after the backlog bug's `install --records-backend home -y`, HEAD was `agent-workflows: sync via installer` whose only change was `.aw/config/project.json`, `records_backend` `repository` -> `home`). That is today's behavior for any policy change and is accepted here; the switch's own summary must therefore not claim `project.json` stays staged, and the tests assert the installer commit contains `project.json` and no `.aw/records/` path. If either sweep happens, STOP and report rather than patching `engine.py`, which is outside this plan's scope.
  - Depends on: E-02
  - Expected outcome: the switch never creates a commit on its own; the only commit is the installer's path-scoped one, containing `project.json` and no record path; the moved records stay staged and uncommitted; staged state matches the printed summary.
  - Execution state: pending

- [ ] E-04 Docs and spec status. `CHANGELOG.md` `## 2.0.0 (pending)` section: one `- Fixed:` bullet stating that `aw install --records-backend <new>` on an installed repository no longer silently leaves existing records where no reader looks: it refuses when records would be orphaned, and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves them. `README.md`, in the "Changing presets later" paragraph `ozr356` adds under `### Placement Presets and Storage Backends`: one sentence that a records-backend change uses the same `--relocate` flags. No em or en dashes in either. Spec Section 8.2 (from `s07f73` E-04): replace the implementation-status sentence with one stating that `vv9ki4` ships the records-only relocation through the `--relocate` flags; add a dated `## Workflow history` note; do not change `- Status:`.
  - Depends on: E-02
  - Expected outcome: CHANGELOG, README and spec describe shipped behavior; dash check prints `0` for the additions; `aw specs check` on the spec conforms.
  - Execution state: pending

### Task group 2: End-to-end tests

- [ ] E-05 Create `tests/test_records_root_switch_cli.py` (`pytestmark = pytest.mark.slow`; every case a subprocess `python3 -m agent_workflows install ...` in a scratch dir with `HOME`, `AW_HOME`, `XDG_CONFIG_HOME` inside it, `AW_NO_REEXEC=1`, `PYTHONPATH=<repo root>`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, `timeout=`; a FRESH `install --preset private-target -y --no-interactive` per test after an `--allow-empty` commit, then a committed `.aw/records/backlog/mine.md` and `project.json` key `cutovers.spec_id6 = "2020-01-01"`). Cases: (1) the backlog repro `install <repo> --records-backend home -y --no-interactive` exits `1`, output contains `--relocate`, tree and home unchanged (snapshot); (2) `--records-backend home --relocate --dry-run -y` exits `0`, output names `records only`, the record count and `project.json`, tree and home unchanged; (3) `--records-backend home --relocate -y` exits `0`: `mine.md` byte-identical under `<AW_HOME>/projects/<id>/records/backlog/` and absent in-tree, `python3 -m agent_workflows context --json` (or `resolve_project_context` in a subprocess) reports the home records root and `records_backend: home`, config dir still in-tree, the 2020 cutover preserved, `git diff --cached --name-status` shows `D` for the record and nothing for `project.json`, because the install that follows the switch commits it (see E-03), and every new commit since the pre-run HEAD (`git log --name-only <pre>..HEAD`) is the installer's `agent-workflows: sync via installer` commit and names NO path under `.aw/records/`, and `aw find backlog mine` (or the equivalent reader) finds the record; (4) on (3) after `git commit -qm move`, the reverse `--records-backend repository --relocate -y` returns the record in-tree staged `A`; (5) a dirty `.aw/records` file with `--relocate --dry-run` exits `1` naming `dirty-aw-tree`; (6) recovery: a tiny driver script builds the policy with `resolve_policy_noninteractive(repo, existing_policy=resolve_existing_policy(repo), explicit_backend="home", allow_records_switch=True)` and calls `execute_records_root_switch(repo, policy, fault_injection="after-switch")`; then a plain `install <repo> -y` refuses naming `--relocate-resume`, `install <repo> --relocate-resume -y` exits `0` with the end state of (3); and with `fault_injection="after-copy"`, `--relocate-rollback -y` restores a byte-identical pre-switch tree and an `AW_HOME` with no record files; (7) a declined relocation (`--relocate --no-interactive` without `-y`) exits non-zero, nothing written; (8) `--records-backend companion --relocate --dry-run` refuses naming `n9vd2h` and not suggesting `--relocate`; (9) a repo with scaffold only: `--records-backend home -y` (no `--relocate`) exits `0` as a plain update (Order 01 OQ-01). Run `python3 -m pytest -o addopts="" -m '' tests/test_records_root_switch_cli.py tests/test_records_root_switch_guard.py tests/test_records_root_switch_execute.py tests/test_placement_switch_cli.py tests/test_reinstall_preserves_config.py -v`, bare `python3 -m pytest`, `make test-all`, and `aw sanitize --agent`.
  - Depends on: E-03, E-04
  - Expected outcome: every case passes; full suites green; sanitizer clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- User-facing prose (CHANGELOG, README, CLI help and messages) carries no em or en dashes (`AGENTS.md` execution contract).
- `cli._run_install` maps `PolicyError` to `term.status("fail", ...)` + `return 1`; non-interactive confirmation declines without `-y` (`cli._confirm_install`).
- `engine.prompt_and_run_commit` commits path-scoped installer paths only ("Offer to commit only the installer-modified files.").
- `make test-all` is the complete gate including `slow` tests.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The bug is reachable from one flag on a normal reinstall. | Authoring probe: `install <repo> --records-backend home -y --no-interactive` on a committed `private-target` repo exited `0` and the resolver root moved to `<AW_HOME>/projects/repo-1582b4/records` while `mine.md` stayed in-tree. |
| F-02 | The recovery flags and the `_install_one` guard are being built by `ozr356`. | `ozr356` E-01 (flags), E-07 (guard in `cli._install_one`, recovery dispatch); `fxbm7j` E-04 makes the recovery API mode-aware, so no new flag is needed. |
| F-03 | A `records-to-home` move keeps `delivery_mode: tracked`, so the commit offer still runs. | `_install_one` skips `engine.prompt_and_run_commit` only "if not engine._is_clean_delta_install(repo_root)" is False; a `private-target` repo with `records_backend: home` is still tracked delivery (authoring probe `project.json`: `delivery_mode: tracked`). |
| F-05 | The install after a switch commits `project.json` under `-y`. | `engine.stage_tracked_policy_files` ("stage wizard-written policy files whose class git policy is target-git") runs inside `engine.install_into_repo`; `engine.prompt_and_run_commit` then commits `installed` paths with `git commit -- <paths>` under `plan.yes`. Review probe: the backlog-bug reinstall produced commit `agent-workflows: sync via installer` touching only `.aw/config/project.json`. |
| F-04 | `aw setup` cannot change the records backend of an installed repo. | `cli._run_setup` reads `args.records_backend` only to refuse `repository-untracked`, and `_install_one` never persists policy (`s07f73` F-06). |

## Proposed changes (ordered, validatable)

1. Message, `allow_records_switch` keyword, test assertion updates (E-01).
2. Execute and preview through the shared `ozr356` relocation branch (E-02).
3. Verified non-commit behavior (E-03).
4. CHANGELOG, README, spec 8.2 status sentence (E-04).
5. End-to-end subprocess tests and full gates (E-05).

## Deferred / out of scope (with reason)

- Companion records backends.
  - Carrier: n9vd2h
- A standalone `aw storage move-records` verb: `aw install` is where the backend is chosen, and `ozr356` already declined a separate relocate verb for the same reason.
  - Carrier-Declined: deliberate non-goal; one entry point keeps refusal and remedy in the same command.

## Scope check

- Over-scope: none; `install_wizard.py` gains a keyword (default off) and a message, `placement_switch.py` only a `render_plan` branch, and the guard-test edit swaps one asserted substring.
- Under-scope: none; refusal, preview, execute, resume, rollback and the guard are each reached end-to-end.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_records_root_switch_cli.py -v` passes, every case.
- The adjacent modules listed in E-05, bare `python3 -m pytest` and `make test-all` pass.
- `aw specs check` on the spec conforms; `aw sanitize --agent` clean.

## Spec / documentation sync

Amends spec `20260810-1447-01` Section 8.2's implementation-status sentence (E-04). WHY: Order 01 wrote it as "until it ships every records-root switch that would orphan records refuses"; once this plan ships `--relocate` for records that sentence is false. Also adds the user-facing CHANGELOG `Fixed:` bullet and a README sentence.

## Open questions

### OQ-01: New flag or reuse `--relocate`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Reuse. `--relocate` already means "perform the storage move this install detected"; the plan kind (placement or records) is decided by the detectors, never by the user, and the recovery flags operate on whatever journal exists (`fxbm7j` E-04). A second flag would let a user pick the wrong one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `grep -n` re-measurement; pasted `git diff -- agent_workflows/install_wizard.py tests/test_records_root_switch_guard.py`; pasted in-process call showing `allow_records_switch=True` returns a `home` policy and the default still raises with `--relocate` in the message.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/cli.py agent_workflows/placement_switch.py`; pasted scratch-repo output of `install <repo> --records-backend home --relocate --dry-run -y` (reachable via `cli._run_install` -> `plan_records_root_switch` -> `render_plan`) and of the real run, with the resolver records root before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff --cached --name-status`, `git log --oneline -3` and `git show --name-only HEAD` after a `-y` relocation in each direction, showing the moved records staged and in no new commit, and `project.json` in the installer commit.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff -- CHANGELOG.md README.md` and the spec diff; pasted dash-count command over the added lines printing `0`; pasted `aw specs check <spec>` conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `-v` runner output of `tests/test_records_root_switch_cli.py` with every case PASSED; pasted adjacent-module, bare-suite and `make test-all` summary lines; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `fxbm7j` and `ozr356` are executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into this repository or touch the real home. Paste ACTUAL runner output. Scope fence: `- Scope-Paths:`; justify any other edit at finalize with `--scope-reason`. Commit through `aw commit vv9ki4 -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize vv9ki4` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
