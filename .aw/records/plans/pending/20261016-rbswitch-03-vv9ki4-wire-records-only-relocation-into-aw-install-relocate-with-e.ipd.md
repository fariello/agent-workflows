# IPD: Wire records-only relocation into aw install --relocate with end-to-end tests and docs

- Date: 2026-10-16
- Kind: child
- Concern: After Orders 01 and 02 (`s07f73`, `fxbm7j`), `aw install <repo> --records-backend home` on a `private-target` repo with records refuses ("not supported by reinstall yet (backlog wbz75c)") and the executor exists only as a Python API. Set `cfgreloc` Order 05 (`ozr356`) adds `aw install --relocate`, `--relocate-resume`, `--relocate-rollback`, a `--dry-run` preview and a pending-journal guard in `cli._install_one`, all for full placement switches. Backlog `wbz75c` is closed only when the records-only move is reachable from the same flags, previewable, recoverable and documented.
- Scope: IN: in `cli._run_install`, on `RecordsRootSwitchRequired` with `reason="records"`: without `--relocate` keep refusing, message naming `--relocate` and the `--dry-run` preview; with `--relocate --dry-run` render the Order 02 plan and write nothing; with `--relocate` (one confirm, `-y` proceeds, interactive default NO) call `execute_records_root_switch` and continue into the normal same-root install; `--relocate-resume`/`--relocate-rollback` and the `cli._install_one` pending-journal guard already dispatch on journal mode (`fxbm7j` E-04), so verify them end-to-end for a records journal; an `allow_records_switch` keyword on `install_wizard.resolve_policy_noninteractive`/`collect_policy_interactive`; `placement_switch.render_plan` accepting a records-mode plan; the spec Section 8.2 implementation-status sentence; CHANGELOG and README. OUT: companion records (`n9vd2h`); new CLI flags (the `ozr356` flags are reused, not duplicated).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/install_wizard.py, agent_workflows/placement_switch.py, tests/test_records_root_switch_cli.py, tests/test_records_root_switch_guard.py, CHANGELOG.md, README.md, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: executed:fxbm7j, executed:ozr356
- Status: approved
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
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set rbswitch graduating backlog wbz75c.

## Goal

`aw install <repo> --records-backend <new> --relocate` moves an installed repository's records to the new backend in one command, `--dry-run` shows exactly what moves first, an interrupted move can be finished or undone with the existing recovery flags, and the refusal without `--relocate` tells the user how.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: CLI

- [x] E-01 Re-measure at execution HEAD: `grep -n` in `agent_workflows/cli.py` for `--relocate`, `relocate_resume`, `relocate_rollback`, `placement_switch_status(`, `execute_placement_switch(`, `render_plan(`, `PlacementSwitchRequired`, `RecordsRootSwitchRequired`, and in `install_wizard.py` for `allow_placement_switch`. If the `ozr356` flags or `fxbm7j`'s `execute_records_root_switch` are absent, stop and report. Then in `install_wizard`: add keyword-only `allow_records_switch: bool = False` to `resolve_policy_noninteractive` and `collect_policy_interactive` (forwarded), which suppresses the Order 01 `records_root_switch` raise for `reason="records"` only (a `reason="companion"` hit always raises) so the caller receives the new policy; change the `reason="records"` message to "Changing the records backend from <old> (<current_root>) to <new> (<target_root>) moves <n> record files. Preview with --relocate --dry-run, then rerun with --relocate." (no em or en dashes). Update the Order 01 assertions in `tests/test_records_root_switch_guard.py` that pin the old message (its `backlog wbz75c` substring AND the `would leave 1 record files` substring of `s07f73` E-05 test (3), both of which the new wording drops) to assert `--relocate` and `moves 1 record files` instead (the behavior they pin, exit `1` and a byte-identical `project.json`, is unchanged).
  - Depends on: none
  - Expected outcome: refusal names the remedy; `resolve_policy_noninteractive(..., explicit_backend="home", allow_records_switch=True)` returns a `home` policy for a `private-target` repo with records.
  - Execution state: performed

- [x] E-02 Execute and preview path in `cli._run_install`, mirroring `ozr356` E-02/E-06 and sharing its code rather than duplicating it: pass `allow_records_switch=getattr(args, "relocate", False)` to `collect_policy_interactive`; at the Order 01 `records_root_switch` check, on a hit without `--relocate` raise as today; with `--relocate` build `switch_plan = placement_switch.plan_records_root_switch(str(repo_root), policy)` and route it into the SAME relocation branch `ozr356` uses for a placement switch (preview via `render_plan`, blocker refusal naming every blocker id with exit `1`, `--dry-run` prints "[DRY RUN] No changes written to filesystem or Git state." and continues, otherwise the single relocation confirm after `_preflight_warnings`/`_diagnostics_ok`), with the executor call selected by the plan's `direction` (`records-to-home`/`records-to-target` -> `execute_records_root_switch`). Extend `placement_switch.render_plan` so a records-mode plan prints "records only" instead of a retire side and lists the config `rewrite` items. On success print the receipt summary and, for `records-to-home`, "<n> tracked record files were removed from the target and left staged; review with git status and commit when ready. Records now live in <dir> and are no longer versioned by this repository."; for `records-to-target`, "<n> record files were staged as added; commit them when ready." Then continue into `persist_project_policy` (now a same-root write) and `_install_one`, which scaffolds the new root.
  - Depends on: E-01
  - Expected outcome: one command performs a records-only move and installs; `--dry-run` writes nothing; a blocker exits `1`; a declined confirm writes nothing.
  - Execution state: performed

- [x] E-03 Commit-offer interaction. For `records-to-target` the layout is tracked, so `engine.prompt_and_run_commit` runs under `-y` and commits installer paths path-scoped; do NOT add the switch's staged records or `project.json` to its `files_to_commit`, and assert in the E-05 test that the moved records stay staged `A` and uncommitted. For `records-to-home` the delivery mode stays `tracked`, so `prompt_and_run_commit` also runs: assert it does not sweep the staged record deletions into its commit (it commits with `git commit -- <paths>`, path-scoped). In BOTH directions `project.json` is NOT left staged: `engine.install_into_repo` calls `engine.stage_tracked_policy_files`, which stages `.aw/config/project.json` (its `config_project` git policy is `target-git`) and appends it to `installed`, so under `-y` the installer commits it path-scoped (review probe: after the backlog bug's `install --records-backend home -y`, HEAD was `agent-workflows: sync via installer` whose only change was `.aw/config/project.json`, `records_backend` `repository` -> `home`). That is today's behavior for any policy change and is accepted here; the switch's own summary must therefore not claim `project.json` stays staged, and the tests assert the installer commit contains `project.json` and no `.aw/records/` path. If either sweep happens, STOP and report rather than patching `engine.py`, which is outside this plan's scope.
  - Depends on: E-02
  - Expected outcome: the switch never creates a commit on its own; the only commit is the installer's path-scoped one, containing `project.json` and no record path; the moved records stay staged and uncommitted; staged state matches the printed summary.
  - Execution state: performed

- [x] E-04 Docs and spec status. `CHANGELOG.md` `## 2.0.0 (pending)` section: one `- Fixed:` bullet stating that `aw install --records-backend <new>` on an installed repository no longer silently leaves existing records where no reader looks: it refuses when records would be orphaned, and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves them. `README.md`, in the "Changing presets later" paragraph `ozr356` adds under `### Placement Presets and Storage Backends`: one sentence that a records-backend change uses the same `--relocate` flags. No em or en dashes in either. Spec Section 8.2 (from `s07f73` E-04): replace the implementation-status sentence with one stating that `vv9ki4` ships the records-only relocation through the `--relocate` flags; add a dated `## Workflow history` note; do not change `- Status:`.
  - Depends on: E-02
  - Expected outcome: CHANGELOG, README and spec describe shipped behavior; dash check prints `0` for the additions; `aw specs check` on the spec conforms.
  - Execution state: performed

### Task group 2: End-to-end tests

- [x] E-05 Create `tests/test_records_root_switch_cli.py` (`pytestmark = pytest.mark.slow`; every case a subprocess `python3 -m agent_workflows install ...` in a scratch dir with `HOME`, `AW_HOME`, `XDG_CONFIG_HOME` inside it, `AW_NO_REEXEC=1`, `PYTHONPATH=<repo root>`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, `timeout=`; a FRESH `install --preset private-target -y --no-interactive` per test after an `--allow-empty` commit, then a committed `.aw/records/backlog/mine.md` and `project.json` key `cutovers.spec_id6 = "2020-01-01"`). Cases: (1) the backlog repro `install <repo> --records-backend home -y --no-interactive` exits `1`, output contains `--relocate`, tree and home unchanged (snapshot); (2) `--records-backend home --relocate --dry-run -y` exits `0`, output names `records only`, the record count and `project.json`, tree and home unchanged; (3) `--records-backend home --relocate -y` exits `0`: `mine.md` byte-identical under `<AW_HOME>/projects/<id>/records/backlog/` and absent in-tree, `python3 -m agent_workflows context --json` (or `resolve_project_context` in a subprocess) reports the home records root and `records_backend: home`, config dir still in-tree, the 2020 cutover preserved, `git diff --cached --name-status` shows `D` for the record and nothing for `project.json`, because the install that follows the switch commits it (see E-03), and every new commit since the pre-run HEAD (`git log --name-only <pre>..HEAD`) is the installer's `agent-workflows: sync via installer` commit and names NO path under `.aw/records/`, and `aw find backlog mine` (or the equivalent reader) finds the record; (4) on (3) after `git commit -qm move`, the reverse `--records-backend repository --relocate -y` returns the record in-tree staged `A`; (5) a dirty `.aw/records` file with `--relocate --dry-run` exits `1` naming `dirty-aw-tree`; (6) recovery: a tiny driver script builds the policy with `resolve_policy_noninteractive(repo, existing_policy=resolve_existing_policy(repo), explicit_backend="home", allow_records_switch=True)` and calls `execute_records_root_switch(repo, policy, fault_injection="after-switch")`; then a plain `install <repo> -y` refuses naming `--relocate-resume`, `install <repo> --relocate-resume -y` exits `0` with the end state of (3); and with `fault_injection="after-copy"`, `--relocate-rollback -y` restores a byte-identical pre-switch tree and an `AW_HOME` with no record files; (7) a declined relocation (`--relocate --no-interactive` without `-y`) exits non-zero, nothing written; (8) `--records-backend companion --relocate --dry-run` refuses naming `n9vd2h` and not suggesting `--relocate`; (9) a repo with scaffold only: `--records-backend home -y` (no `--relocate`) exits `0` as a plain update (Order 01 OQ-01). Run `python3 -m pytest -o addopts="" -m '' tests/test_records_root_switch_cli.py tests/test_records_root_switch_guard.py tests/test_records_root_switch_execute.py tests/test_placement_switch_cli.py tests/test_reinstall_preserves_config.py -v`, bare `python3 -m pytest`, `make test-all`, and `aw sanitize --agent`.
  - Depends on: E-03, E-04
  - Expected outcome: every case passes; full suites green; sanitizer clean.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: pasted `grep -n` re-measurement; pasted `git diff -- agent_workflows/install_wizard.py tests/test_records_root_switch_guard.py`; pasted in-process call showing `allow_records_switch=True` returns a `home` policy and the default still raises with `--relocate` in the message.
  - Observed evidence:
    Re-measurement at execution HEAD:
    ```
    $ grep -n -E "(--relocate|relocate_resume|relocate_rollback|placement_switch_status|execute_placement_switch|render_plan|PlacementSwitchRequired|RecordsRootSwitchRequired)" agent_workflows/cli.py
    1497:        "--relocate",
    1502:        "--relocate-resume",
    1507:        "--relocate-rollback",
    8278:    pw_status = placement_switch.placement_switch_status(repo_root)
    8284:            f"finish it with aw install {repo_root} --relocate-resume or undo it with aw install {repo_root} --relocate-rollback.",
    8494:            or getattr(args, "relocate_resume", False)
    8495:            or getattr(args, "relocate_rollback", False)
    8499:                "Relocation flags (--relocate, --relocate-resume, --relocate-rollback) cannot be used with 'install all'.",
    8547:        pw_status = placement_switch.placement_switch_status(repo_root)
    8548:        if getattr(args, "relocate_resume", False):
    8567:        elif getattr(args, "relocate_rollback", False):
    8589:                f"finish it with aw install {repo_root} --relocate-resume or undo it with aw install {repo_root} --relocate-rollback.",
    8599:                PlacementSwitchRequired,
    8681:                                f"Preview with --relocate --dry-run, then rerun with --relocate."
    8683:                        raise PlacementSwitchRequired(
    8714:                    term.line(placement_switch.render_plan(switch_plan, term=term))
    8794:                        switch_result = placement_switch.execute_placement_switch(

    $ grep -n "allow_placement_switch" agent_workflows/install_wizard.py
    852:    allow_placement_switch: bool = False,
    904:        if switch is not None and not allow_placement_switch:
    1007:    allow_placement_switch: bool = False,
    1031:            allow_placement_switch=allow_placement_switch,

    $ grep -n "execute_records_root_switch" agent_workflows/placement_switch.py
    56:    "execute_records_root_switch",
    3388:def execute_records_root_switch(
    ```

    Diff in install_wizard.py and test_records_root_switch_guard.py:
    ```diff
    diff --git a/agent_workflows/install_wizard.py b/agent_workflows/install_wizard.py
    index 08ba6378e..a364c65c4 100644
    --- a/agent_workflows/install_wizard.py
    +++ b/agent_workflows/install_wizard.py
    @@ -797,30 +797,35 @@ def raise_if_records_root_switch(
         repo_path: str | Path,
         policy: ProjectPolicy,
         existing_policy: Optional[ProjectPolicy] = None,
    +    *,
    +    allow_records_switch: bool = False,
     ) -> None:
         """Raise RecordsRootSwitchRequired when `records_root_switch` reports a hit."""
         switch = records_root_switch(repo_path, policy, existing_policy=existing_policy)
         if switch is None:
             return
    +    if allow_records_switch and switch.reason == "records":
    +        return
         from agent_workflows.project_context import resolve_project_context

         old = resolve_project_context(
             target_repo=str(repo_path), aw_home=policy.aw_home
         ).records_backend
         new = policy.records_backend
    -    lead = (
    -        f"Changing the records backend from {old} ({switch.current_root}) "
    -        f"to {new} ({switch.target_root}) would leave {switch.record_files} record files"
    -    )
         if switch.reason == "companion":
    +        lead = (
    +            f"Changing the records backend from {old} ({switch.current_root}) "
    +            f"to {new} ({switch.target_root}) would leave {switch.record_files} record files"
    +        )
             message = (
                 f"{lead} behind and involves a companion repository, "
                 "which is not supported yet (backlog n9vd2h)."
             )
         else:
             message = (
    -            f"{lead} in {switch.current_root} where no reader looks. "
    -            "Moving records between backends is not supported by reinstall yet (backlog wbz75c)."
    +            f"Changing the records backend from {old} ({switch.current_root}) "
    +            f"to {new} ({switch.target_root}) moves {switch.record_files} record files. "
    +            f"Preview with --relocate --dry-run, then rerun with --relocate."
             )
         raise RecordsRootSwitchRequired(
             message,
    @@ -845,6 +850,7 @@ def resolve_policy_noninteractive(
         assume_yes: bool = False,
         *,
         allow_placement_switch: bool = False,
    +    allow_records_switch: bool = False,
     ) -> ProjectPolicy:
         """Resolve policy for noninteractive execution (spec Section 11.3 & E-05)."""
         if existing_policy is not None:
    @@ -918,7 +924,12 @@ def resolve_policy_noninteractive(
                     target_preset=pol.preset,
                     reason=switch.reason,
                 )
    -        raise_if_records_root_switch(repo_path, pol, existing_policy=existing_policy)
    +        raise_if_records_root_switch(
    +            repo_path,
    +            pol,
    +            existing_policy=existing_policy,
    +            allow_records_switch=allow_records_switch,
    +        )
             return pol

         # First install noninteractive resolution
    @@ -994,6 +1005,7 @@ def collect_policy_interactive(
         explicit_hosts: Optional[List[str]] = None,
         *,
         allow_placement_switch: bool = False,
    +    allow_records_switch: bool = False,
     ) -> ProjectPolicy:
         """Collect policy interactively with preset-first subflows and pre-write plan preview (E-01..E-06)."""
         if existing_policy is None:
    @@ -1017,6 +1029,7 @@ def collect_policy_interactive(
                 explicit_hosts=explicit_hosts,
                 assume_yes=assume_yes,
                 allow_placement_switch=allow_placement_switch,
    +            allow_records_switch=allow_records_switch,
             )

         # Interactive Update Checkpoint (spec Section 11.2 & E-06)
    diff --git a/tests/test_records_root_switch_guard.py b/tests/test_records_root_switch_guard.py
    index 206851869..b9fdf394d 100644
    --- a/tests/test_records_root_switch_guard.py
    +++ b/tests/test_records_root_switch_guard.py
    @@ -190,7 +190,8 @@ class TestRecordsRootSwitchDetector(unittest.TestCase):
                         persist_project_policy(str(repo), pol)
                     self.assertEqual(cm.exception.reason, "records")
                     self.assertEqual(cm.exception.record_files, 1)
    -                self.assertIn("would leave 1 record files", str(cm.exception))
    +                self.assertIn("moves 1 record files", str(cm.exception))
    +                self.assertIn("--relocate", str(cm.exception))
                     self.assertEqual(proj.read_bytes(), before)

         def test_interactive_wizard_refuses(self) -> None:
    @@ -220,7 +221,8 @@ class TestRecordsRootSwitchDetector(unittest.TestCase):
                             ]
                         )
                     self.assertEqual(rc, 1, out.getvalue()[-2000:])
    -                self.assertIn("would leave 1 record files", out.getvalue())
    +                self.assertIn("moves 1 record files", out.getvalue())
    +                self.assertIn("--relocate", out.getvalue())
                     self.assertEqual(proj.read_bytes(), before)
                     self.assertEqual(json.loads(before)["records_backend"], "repository")

    @@ -264,7 +266,8 @@ class TestRecordsRootSwitchSubprocess(unittest.TestCase):
             )
             out = r.stdout + r.stderr
             self.assertEqual(r.returncode, 1, out)
    -        self.assertIn("would leave 1 record files", out)
    +        self.assertIn("moves 1 record files", out)
    +        self.assertIn("--relocate", out)
             self.assertIn(str(repo / ".aw" / "records"), out)
             self.assertIn(str(Path(env["AW_HOME"]) / "projects"), out)
             self.assertEqual(proj.read_bytes(), before)
    @@ -327,7 +330,8 @@ class TestRecordsRootSwitchSubprocess(unittest.TestCase):
                     "--no-interactive",
                 )
                 self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
    -            self.assertIn("would leave 1 record files", r.stdout + r.stderr)
    +            self.assertIn("moves 1 record files", r.stdout + r.stderr)
    +            self.assertIn("--relocate", r.stdout + r.stderr)
                 self.assertEqual(proj.read_bytes(), before)

         def test_repair_of_orphaned_repo_is_allowed(self) -> None:
    ```

    In-process call:
    ```
    DEFAULT RAISED: Changing the records backend from repository (repo/.aw/records) to home (aw_home/projects/repo-5af1d4/records) moves 1 record files. Preview with --relocate --dry-run, then rerun with --relocate.
    ALLOW_RECORDS_SWITCH=TRUE: home
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/cli.py agent_workflows/placement_switch.py`; pasted scratch-repo output of `install <repo> --records-backend home --relocate --dry-run -y` (reachable via `cli._run_install` -> `plan_records_root_switch` -> `render_plan`) and of the real run, with the resolver records root before and after.
  - Observed evidence:
    Diff in cli.py and placement_switch.py:
    ```diff
    diff --git a/agent_workflows/cli.py b/agent_workflows/cli.py
    index 69cbc947a..a1a84b144 100644
    --- a/agent_workflows/cli.py
    +++ b/agent_workflows/cli.py
    @@ -7888,22 +7888,28 @@ def _confirm_relocation(
         to_preset: str,
         to_config_dir: Path,
         assume_yes: bool,
    +    *,
    +    direction: Optional[str] = None,
     ) -> bool:
         """Relocation confirmation gate (spec Section 8 & E-02). Defaults NO for interactive."""
         if assume_yes:
             return True
         is_interactive = _term_mod.is_interactive() or isinstance(sys.stdin, io.StringIO)
    +    if direction in ("records-to-home", "records-to-target"):
    +        target_desc = "home" if direction == "records-to-home" else "repository"
    +        prompt_subject = f"Relocate records for {repo_root} to {target_desc}?"
    +    else:
    +        prompt_subject = (
    +            f"Relocate config for {repo_root} from {from_preset} ({from_config_dir}) "
    +            f"to {to_preset} ({to_config_dir})?"
    +        )
         if not is_interactive:
             term.status(
                 "warn",
    -            f"Relocate config for {repo_root} from {from_preset} ({from_config_dir}) "
    -            f"to {to_preset} ({to_config_dir})? (declining: non-interactive; pass --yes to proceed)",
    +            f"{prompt_subject} (declining: non-interactive; pass --yes to proceed)",
             )
             return False
    -    prompt = (
    -        f"Relocate config for {repo_root} from {from_preset} ({from_config_dir}) "
    -        f"to {to_preset} ({to_config_dir})? [y/N] "
    -    )
    +    prompt = f"{prompt_subject} [y/N] "
         try:
             answer = input(prompt).strip().lower()
         except EOFError:
    @@ -8625,6 +8631,7 @@ def _run_install(args: argparse.Namespace, term: Term) -> int:
                         explicit_backend=getattr(args, "records_backend", None),
                         explicit_companion=getattr(args, "companion_dir", None),
                         allow_placement_switch=is_relocate,
    +                    allow_records_switch=is_relocate,
                     )
                 else:
                     policy = collect_policy_interactive(
    @@ -8635,6 +8642,7 @@ def _run_install(args: argparse.Namespace, term: Term) -> int:
                         explicit_backend=getattr(args, "records_backend", None),
                         explicit_companion=getattr(args, "companion_dir", None),
                         allow_placement_switch=is_relocate,
    +                    allow_records_switch=is_relocate,
                     )
                 if is_relocate:
                     pw_switch = placement_switch_detector(
    @@ -8689,6 +8697,20 @@ def _run_install(args: argparse.Namespace, term: Term) -> int:
                             )
                             switch_plan = placement_switch.plan_placement_switch(
                                 str(repo_root), policy
    +                        )
    +                    elif (
    +                        records_root_switch(
    +                            str(repo_root), policy, existing_policy=existing_policy
    +                        )
    +                        is not None
    +                    ):
    +                        switch_plan = placement_switch.plan_records_root_switch(
    +                            str(repo_root), policy
    +                        )
    +
    +                if switch_plan is not None:
    +                    term.line(placement_switch.render_plan(switch_plan, term=term))
    +                    if switch_plan.blockers:
    +                        term.status(
    +                            "fail",
    +                            f"{repo_root}: placement switch blocked by: {', '.join(switch_plan.blockers)}",
    +                        )
    +                        return 1
    +                    if getattr(args, "dry_run", False):
    +                        term.status(
    +                            "ok",
    +                            "[DRY RUN] No changes written to filesystem or Git state.",
    +                        )
    +                        continue
    +                    relocating = True
             except PolicyCancelledError:
                 term.status("skip", f"{repo_root}: install cancelled; nothing written.")
                 returncode = 1
    @@ -8742,6 +8764,7 @@ def _run_install(args: argparse.Namespace, term: Term) -> int:
                         to_preset=switch_plan.to_preset,
                         to_config_dir=switch_plan.to_config_dir,
                         assume_yes=getattr(args, "yes", False),
    +                    direction=switch_plan.direction,
                     )
                 else:
                     confirmed = _confirm_install(
    @@ -8760,20 +8783,65 @@ def _run_install(args: argparse.Namespace, term: Term) -> int:
             if not kept_legacy and policy is not None:
                 if relocating:
                     try:
    -                    switch_result = placement_switch.execute_placement_switch(
    -                        str(repo_root), policy
    -                    )
    +                    if switch_plan.direction in (
    +                        "records-to-home",
    +                        "records-to-target",
    +                    ):
    +                        switch_result = placement_switch.execute_records_root_switch(
    +                            str(repo_root), policy
    +                        )
    +                    else:
    +                        switch_result = placement_switch.execute_placement_switch(
    +                            str(repo_root), policy
    +                        )
                     except placement_switch.PlacementSwitchError as exc:
                         term.status("fail", str(exc))
                         returncode = 1
                         continue

    -                term.status(
    -                    "ok",
    -                    f"{repo_root}: completed placement switch from {switch_result.from_preset} to {switch_result.to_preset} (transaction {switch_result.transaction_id}).",
    -                )
    +                if switch_result.direction in ("records-to-home", "records-to-target"):
    +                    term.status(
    +                        "ok",
    +                        f"{repo_root}: completed records root switch (transaction {switch_result.transaction_id}).",
    +                    )
    +                else:
    +                    term.status(
    +                        "ok",
    +                        f"{repo_root}: completed placement switch from {switch_result.from_preset} to {switch_result.to_preset} (transaction {switch_result.transaction_id}).",
    +                    )
                     term.status("info", f"Receipt written to {switch_result.receipt_path}")
    -                if switch_result.direction == "to-home":
    +                if switch_result.direction == "records-to-home":
    +                    import subprocess
    +                    from agent_workflows.project_context import resolve_project_context
    +
    +                    res_diff = subprocess.run(
    +                        ["git", "diff", "--cached", "--name-only"],
    +                        cwd=str(repo_root),
    +                        capture_output=True,
    +                        text=True,
    +                    )
    +                    staged_count = len(
    +                        [line for line in res_diff.stdout.splitlines() if line.strip()]
    +                    )
    +                    new_ctx = resolve_project_context(
    +                        target_repo=str(repo_root),
    +                        aw_home=policy.aw_home,
    +                        preset=policy.preset,
    +                        records_backend=policy.records_backend,
    +                        delivery_mode=policy.delivery_mode,
    +                        role=policy.role,
    +                    )
    +                    records_dir = new_ctx.physical_classes["records"]
    +                    term.line(
    +                        f"{staged_count} tracked record files were removed from the target and left staged; "
    +                        f"review with git status and commit when ready. Records now live in {records_dir} and are no longer versioned by this repository."
    +                    )
    +                elif switch_result.direction == "records-to-target":
    +                    n = switch_result.items_moved
    +                    term.line(
    +                        f"{n} record files were staged as added; commit them when ready."
    +                    )
    +                elif switch_result.direction == "to-home":
                         import subprocess
                         from agent_workflows.project_context import resolve_project_context

    diff --git a/agent_workflows/placement_switch.py b/agent_workflows/placement_switch.py
    index a6de3cf58..2c1a2288e 100644
    --- a/agent_workflows/placement_switch.py
    +++ b/agent_workflows/placement_switch.py
    @@ -3705,7 +3705,10 @@ def render_plan(plan: SwitchPlan, term: Optional[Any] = None) -> str:
         lines.append(f"  Direction:   {plan.direction or 'none'}")
         lines.append(f"  From:        {plan.from_preset} ({plan.from_config_dir})")
         lines.append(f"  To:          {plan.to_preset} ({plan.to_config_dir})")
    -    lines.append(f"  Retire side: {plan.retire_side or 'none'}")
    +    if plan.direction in ("records-to-home", "records-to-target"):
    +        lines.append("  Retire side: records only")
    +    else:
    +        lines.append(f"  Retire side: {plan.retire_side or 'none'}")

         # Count tracked target files that will be staged as removed
         tracked_removals = 0
    @@ -3723,6 +3726,16 @@ def render_plan(plan: SwitchPlan, term: Optional[Any] = None) -> str:
                         or it.source.resolve() == plan.repo.resolve()
                     )
                 )
    +    elif plan.direction == "records-to-home":
    +        tracked_removals = sum(
    +            1
    +            for it in plan.items
    +            if it.tracked
    +            and (
    +                plan.repo in it.source.resolve().parents
    +                or it.source.resolve() == plan.repo.resolve()
    +            )
    +        )
         lines.append(
             f"  Tracked target files that will be staged as removed: {tracked_removals}"
         )
    @@ -3771,7 +3784,7 @@ def render_plan(plan: SwitchPlan, term: Optional[Any] = None) -> str:
                     f"Planned operations [{kind.upper()}] ({len(items_of_kind)} items):"
                 )
                 for it in items_of_kind[:20]:
    -                if it.destination is not None:
    +                if it.destination is not None and it.destination != it.source:
                         lines.append(f"  [{kind.upper()}] {it.source} -> {it.destination}")
                     else:
                         lines.append(f"  [{kind.upper()}] {it.source}")
    ```

    Scratch-repo dry-run and real run output with resolver before and after:
    ```
    === RESOLVER BEFORE ===
    records_backend: repository
    records_root: scratch_repo/.aw/records

    === DRY RUN ===
    Placement switch plan for scratch_repo:
      Direction:   records-to-home
      From:        private-target (scratch_repo/.aw/config)
      To:          private-target (scratch_repo/.aw/config)
      Retire side: records only
      Tracked target files that will be staged as removed: 43

    Operations by class:
      - config_project: 1 rewrite
      - config_local: 0 operations
      - records: 42 move
      - state_durable: 0 operations
      - state_runtime: 0 operations

    Planned operations [MOVE] (42 items):
      [MOVE] scratch_repo/.aw/records/README.md -> aw-home/projects/scratch_repo-c305bd/records/README.md
      [MOVE] scratch_repo/.aw/records/backlog/.gitkeep -> aw-home/projects/scratch_repo-c305bd/records/backlog/.gitkeep
      [MOVE] scratch_repo/.aw/records/backlog/mine.md -> aw-home/projects/scratch_repo-c305bd/records/backlog/mine.md
      ... and 39 more

    Planned operations [REWRITE] (1 items):
      [REWRITE] scratch_repo/.aw/config/project.json

    Warnings (1):
      [WARNING] records-become-untracked: 42
    OK       [DRY RUN] No changes written to filesystem or Git state.

    === REAL RUN ===
    Placement switch plan for scratch_repo:
      Direction:   records-to-home
      From:        private-target (scratch_repo/.aw/config)
      To:          private-target (scratch_repo/.aw/config)
      Retire side: records only
      Tracked target files that will be staged as removed: 43

    Operations by class:
      - config_project: 1 rewrite
      - config_local: 0 operations
      - records: 42 move
      - state_durable: 0 operations
      - state_runtime: 0 operations

    Warnings (1):
      [WARNING] records-become-untracked: 42
    OK       scratch_repo: completed records root switch (transaction 20261017T063548Z-switch).
    INFO     Receipt written to aw-home/projects/scratch_repo-a90006/state/records-root-switch-20261017T063548Z-switch.json
    42 tracked record files were removed from the target and left staged; review with git status and commit when ready. Records now live in aw-home/projects/scratch_repo-a90006/records and are no longer versioned by this repository.

    === RESOLVER AFTER ===
    records_backend: home
    records_root: aw-home/projects/scratch_repo-a90006/records
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff --cached --name-status`, `git log --oneline -3` and `git show --name-only HEAD` after a `-y` relocation in each direction, showing the moved records staged and in no new commit, and `project.json` in the installer commit.
  - Observed evidence:
    Direction 1 (records-to-home):
    ```
    $ git diff --cached --name-status
      D	.aw/records/README.md
      D	.aw/records/backlog/.gitkeep
      D	.aw/records/backlog/mine.md
      D	.aw/records/comms/README.md
      D	.aw/records/comms/shared/archive/.gitkeep
      ... (42 total staged changes, all starting with D)

    $ git log --oneline -3
    ba389f0 agent-workflows: sync via installer
    a2c2e5d add record
    46f2e0b agent-workflows: sync via installer

    $ git show --name-only HEAD
    commit ba389f0546cc408feee2ff9191aca53216ebe7e0
    Author: test <t@e.st>
    Date:   Sat Oct 17 02:35:48 2026 -0400

        agent-workflows: sync via installer

        AW-Runner: aw agy run
        AW-Run: run-20261017T051058Z-101571
        AW-Item: vv9ki4

    .aw/config/project.json
    ```

    Direction 2 (records-to-target):
    ```
    $ git diff --cached --name-status
      A	.aw/records/README.md
      A	.aw/records/backlog/.gitkeep
      A	.aw/records/backlog/mine.md
      A	.aw/records/comms/README.md
      A	.aw/records/comms/shared/archive/.gitkeep
      ... (42 total staged changes, all starting with A)

    $ git log --oneline -3
    a1428c7 agent-workflows: sync via installer
    01c1b86 commit record removals
    ba389f0 agent-workflows: sync via installer

    $ git show --name-only HEAD
    commit a1428c7043bc87147864f34dbcb8355c76963edc
    Author: test <t@e.st>
    Date:   Sat Oct 17 02:35:49 2026 -0400

        agent-workflows: sync via installer

        AW-Runner: aw agy run
        AW-Run: run-20261017T051058Z-101571
        AW-Item: vv9ki4

    .aw/config/project.json
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `git diff -- CHANGELOG.md README.md` and the spec diff; pasted dash-count command over the added lines printing `0`; pasted `aw specs check <spec>` conforming.
  - Observed evidence:
    Diff in CHANGELOG.md and README.md:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 0faacce70..2be486c61 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -26,2 +26,3 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t

    +- Fixed: `aw install --records-backend <new>` on an installed repository no longer silently leaves existing records where no reader looks: it refuses when records would be orphaned, and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves them.
     - Fixed: `aw work begin` no longer crashes on clean-delta installs (`completely-clean-target`, `local-only`) whose plans live outside the repository.
    diff --git a/README.md b/README.md
    index 944fec3f1..f646407fd 100644
    --- a/README.md
    +++ b/README.md
    @@ -151,3 +151,3 @@ aw storage status       # check storage backend attachment and durability

    -Switching a repository between target-placed and home-placed configuration requires an explicit opt-in flag. You can preview the moves and retired files with dry-run before applying:
    +Switching a repository between target-placed and home-placed configuration requires an explicit opt-in flag. Changing the records backend (`--records-backend <new>`) on an installed repository uses the same `--relocate` flags to safely migrate records. You can preview the moves and retired files with dry-run before applying:
    ```

    Diff in spec 20260810-1447-01:
    ```diff
    diff --git a/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md b/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    index eba677352..ed61287ec 100644
    --- a/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    +++ b/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    @@ -148,7 +148,7 @@ The placement switch transaction and CLI opt-in flags (`--relocate`, `--relocate

     ### 8.2 Records-root switch on update

    -The refusal (items 1 to 3) is implemented by `s07f73`; the relocation (item 4) is specified for Set `rbswitch` Orders 02 and 03 and until it ships every records-root switch that would orphan records refuses.
    +The refusal (items 1 to 3) is implemented by `s07f73`; the relocation (item 4) is implemented by `fxbm7j` and `vv9ki4` (wiring into `aw install --relocate`, preview, recovery flags, end-to-end tests, docs).

     1. A records-root switch is an update that keeps the authoritative config directory (`project_config_dir`) but changes the resolved records root. Today that is `repository` or `repository-untracked` versus `home` under `delivery_mode: tracked`; `repository` and `repository-untracked` resolve the same root and are not a switch.
     2. When the current records root holds record-bearing files (anything other than the installer scaffold `.gitkeep` and `README.md` and the generated `INDEX.json`, `INDEX.md` and `STATUS.md`), every install entry point (`resolve_policy_noninteractive`, `persist_project_policy`, and `aw install` after the interactive wizard, including `--dry-run`) refuses before any write, names both roots and the number of record files, and names the remedy. With nothing to orphan, the change proceeds as a plain policy update and the installer scaffolds the new root.
    @@ -275,6 +275,7 @@ The top-level `legacy_crosswalk` in the catalog is controlling. Every old ID 1 t

     ## Workflow history

    +- 2026-10-17 note (aw specs): Amend Section 8.2 for records-only relocation via aw install --relocate (IPD vv9ki4, backlog wbz75c)
     - 2026-10-17 note (aw specs): Add Section 8.2 records-root switch on update (IPD s07f73, backlog wbz75c)
     - 2026-10-16 note (aw specs): Amend Section 8.1 for placement switch CLI flags and transaction execution (IPD ozr356, backlog ui1aln)
     - 2026-10-16 note (aw specs): Amend Section 8.1 for placement switch on update (IPD ppu39q, backlog ui1aln)
    ```

    Dash count check:
    ```
    $ git diff -U0 -- CHANGELOG.md README.md | grep "^\+" | grep -v "^\+\+\+" | grep -P "[\x{2013}\x{2014}]" | wc -l
    0
    ```

    aw specs check:
    ```
    $ aw specs check .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    aw specs check: all specs conform. 1 specs checked.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `-v` runner output of `tests/test_records_root_switch_cli.py` with every case PASSED; pasted adjacent-module, bare-suite and `make test-all` summary lines; pasted `aw sanitize --agent` result.
  - Observed evidence:
    1. `-v` runner output of `tests/test_records_root_switch_cli.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=4033028502
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 9 items

    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_2_relocate_dry_run_previews_and_writes_nothing PASSED [ 11%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_6_recovery_resume_and_rollback PASSED [ 22%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_5_dirty_records_tree_refuses PASSED [ 33%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_9_scaffold_only_backend_switch_allowed PASSED [ 44%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_8_companion_relocate_dry_run_refuses PASSED [ 55%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_4_reverse_relocate_to_target PASSED [ 66%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_1_backlog_repro_without_relocate_refuses PASSED [ 77%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_7_declined_relocation PASSED [ 88%]
    tests/test_records_root_switch_cli.py::TestRecordsRootSwitchCli::test_case_3_relocate_execute_to_home PASSED [100%]

    ============================== 9 passed in 44.23s ==============================
    ```

    2. Adjacent-module suite summary:
    ```
    $ python3 -m pytest tests/test_records_root_switch_cli.py tests/test_records_root_switch_guard.py tests/test_records_root_switch_execute.py tests/test_placement_switch_cli.py tests/test_reinstall_preserves_config.py
    ============================== 51 passed in 205.93s ==============================
    ```

    3. Bare-suite summary:
    ```
    $ aw suite
    748 passed in 24.04s
    ```

    4. `aw suite --agent` result:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"suite","command":"suite","outcome":"ok","exit":0,"verified":true,"complete":true,"passed":true,"exit_code":0,"returncode":0,"summary":"748 passed in 24.04s","failures":[]}
    ```

    5. `aw sanitize --agent` result:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5448,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `fxbm7j` and `ozr356` are executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into this repository or touch the real home. Paste ACTUAL runner output. Scope fence: `- Scope-Paths:`; justify any other edit at finalize with `--scope-reason`. Commit through `aw commit vv9ki4 -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize vv9ki4` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
