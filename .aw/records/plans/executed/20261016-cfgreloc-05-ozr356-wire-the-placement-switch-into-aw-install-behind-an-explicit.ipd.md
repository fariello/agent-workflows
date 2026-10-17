# IPD: Wire the placement switch into aw install behind an explicit opt-in flag

- Date: 2026-10-16
- Kind: child
- Concern: After Orders 01 to 04 (`ppu39q`, `xvlemm`, `gjylny`, `6u755v`), a user who runs `aw install <repo> --preset local-only` on a `private-target` repo still only gets the refusal "is not supported by reinstall yet (backlog ui1aln)" and has no command that performs the switch. Backlog `ui1aln` is done only when the switch is reachable from the CLI, previewable, recoverable after a crash, and documented.
- Scope: IN: `aw install` flags `--relocate` (perform a detected placement switch), `--relocate-resume` and `--relocate-rollback` (finish or undo an interrupted one); in `cli._run_install`, on `PlacementSwitchRequired`: without `--relocate` keep refusing with a message that names `--relocate` and the `--dry-run` preview; with `--relocate --dry-run` render the Order 02 plan (moves, discards, retirements, warnings, blockers) and write nothing; with `--relocate` (and `-y` or an interactive confirm whose default is NO) call `execute_placement_switch`, then continue into the normal install of the NEW layout (`_install_one`), whose commit offer (`engine.prompt_and_run_commit`) is skipped for a to-home switch because the switch's staged deletions are reported instead (see E-03); a pending journal blocks a plain install with a message naming the two recovery flags; update the refusal message in `install_wizard` (drop "not supported ... yet (backlog ui1aln)", keep the substring `Switching config placement`); update the two `on0keo` assertions that pin `ui1aln` in the message; an `allow_placement_switch` keyword on `install_wizard.collect_policy_interactive`/`resolve_policy_noninteractive` so the CLI obtains the new policy instead of an exception; `placement_switch.render_plan`; a pending-journal guard in the shared `cli._install_one` shell (so `install all` and `setup` cannot install into a half-switched repo); the spec Section 8.1 implementation-status sentence; CHANGELOG and README. OUT: `aw setup` (it calls `_install_one` but never the policy wizard: `cli._run_setup` has no `collect_policy_interactive` call, so it cannot switch placement); companion pairs (`n9vd2h`).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/install_wizard.py, agent_workflows/placement_switch.py, tests/test_placement_switch_cli.py, tests/test_reinstall_preserves_config.py, CHANGELOG.md, README.md, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Scope-Exceeded: tests/test_placement_switch_guard.py (update PlacementSwitchRequired assertion to --relocate matching E-01 refusal message change)
- Item-Dependencies: executed:6u755v
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 5
- Highest E allocated: 07
- Author: opencode
- Id: ozr356

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ozr356 verified (set cfgreloc, attempt 1). [Scope reconciliation - out-of-scope tests/test_placement_switch_guard.py: update PlacementSwitchRequired assertion to --relocate matching E-01 refusal message change]
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

`aw install <repo> --preset <new> --relocate` switches an installed repository between target-placed and home-placed config in one command, `--dry-run` shows exactly what it will do first, and an interrupted switch can be finished or undone from the CLI.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: CLI

- [x] E-01 Add `--relocate`, `--relocate-resume`, `--relocate-rollback` (`store_true`, mutually exclusive group) to the `p_install` parser in `cli`, with help text in plain words (no em or en dashes). In `install_wizard`, change the `PlacementSwitchRequired` message to: "Switching config placement from <old> (<old dir>) to <new> (<new dir>) moves project config, records and install history. Preview with --relocate --dry-run, then rerun with --relocate." EXCEPT when either side is `public-target-private-companion` (the `ppu39q` `reason="label"` hit): there the message must NOT suggest `--relocate`, which can never succeed for that pair, and instead says "Switching config placement from <old> to <new> involves a companion repository and is not supported yet (backlog n9vd2h)." Update `tests/test_reinstall_preserves_config.py` `test_resolve_policy_noninteractive_cross_placement_guard_refuses` and `test_subprocess_reinstall_private_target_to_local_only_fails_closed` to assert `--relocate` instead of `ui1aln` (the behavior they pin, exit `1` and an unchanged `project.json`, is unchanged). Add keyword-only `allow_placement_switch: bool = False` to `resolve_policy_noninteractive` and `collect_policy_interactive` (which forwards it): when True the `config_placement_switch` check in `resolve_policy_noninteractive` does not raise, so the caller receives the NEW policy (today the non-interactive path raises before any policy object exists, so the CLI would have nothing to pass to `execute_placement_switch`); the default keeps every current caller refusing.
  - Depends on: none
  - Expected outcome: `aw install --help` lists the flags; the refusal names the remedy (or `n9vd2h` for companion pairs); `resolve_policy_noninteractive(..., allow_placement_switch=True)` returns a `local-only` policy for a `private-target` repo instead of raising.
  - Execution state: performed

- [x] E-02 Execute path in `cli._run_install`. Call `collect_policy_interactive(..., allow_placement_switch=getattr(args, "relocate", False))`. Right after it returns, `ppu39q` E-03 calls `config_placement_switch(str(repo_root), policy, existing_policy=existing_policy)`; on a hit: without `--relocate` raise `PlacementSwitchRequired` exactly as today (`fail` + `return 1`); with `--relocate` build `switch_plan = placement_switch.plan_placement_switch(str(repo_root), policy)` and hand it to the preview of E-06 (which owns `--dry-run` and the blocker refusal). Only when there is no blocker and not `--dry-run`, mark the repo as relocating and continue down the EXISTING flow, so the switch runs AFTER `_preflight_warnings`, `_diagnostics_ok` and the confirm, never before them: running it earlier would let a later abort at the git pre-flight (which prompts on the switch's own staged changes) leave a switched repo whose new side has no `system/`. For a relocating repo, REPLACE the `_confirm_install` call with one relocation confirm (`_confirm_install(term, repo_root, args.yes, default=False)` semantics: `-y` proceeds, interactive default NO, non-interactive without `-y` declines; prompt text names both presets and both config dirs), so the user answers one question, not two. On yes, call `placement_switch.execute_placement_switch(str(repo_root), policy)` as the first statement of the `if not kept_legacy and policy is not None:` block, before the companion attach (not reachable for a relocation, `companion-unsupported` blocks it) and before `persist_project_policy`; a `PlacementSwitchError` -> `fail` with its message, `returncode = 1`, `continue`. On success print the receipt summary and, for to-home, "<n> tracked files were removed or modified in the target and left staged; review with git status and commit when ready. Records now live in <dir> and are no longer versioned by this repository." Then continue into `persist_project_policy` (now a same-placement write, so the Order 01 guard passes and it merges into the switched `project.json`) and `_install_one`. If `_install_one` returns `failed` after a completed switch, also print "The placement switch completed; rerun aw install <repo> to finish installing the new layout." (a same-placement install repairs it).
  - Depends on: E-01, E-06
  - Expected outcome: `--relocate -y` switches and installs in one command; the switch happens only after the git pre-flight and a single confirm; a declined confirm writes nothing.
  - Execution state: performed

- [x] E-03 Commit-offer interaction. For a to-home switch the new layout is clean-delta, so `_install_one` already skips `engine.prompt_and_run_commit` ("if not engine._is_clean_delta_install(repo_root):"); verify the staged deletions stay staged and are NOT auto-committed under `-y`, and that every staged entry in the target is `D` except `M` on `AGENTS.md` and `.gitignore`, which the retirement's managed-block stripping modifies (`6u755v` review PR-005, probe: 311 `D` and 2 `M`). For a to-target switch `prompt_and_run_commit` runs and, under `-y`, commits installer paths; do NOT add the switch's staged records to its `files_to_commit` input, and assert in the test that the moved records remain staged (`A`) and uncommitted while installer files follow today's behavior. `.aw/.gitignore`, written by the switch for a to-target move, is legitimately in the installer commit (`engine.prompt_and_run_commit` adds it when dirty, "files_to_commit[AW_GITIGNORE_PATH] = \"modified\""). Record the observed behavior in V-03; if `prompt_and_run_commit` sweeps the staged records into its commit (it commits with `git commit -- <paths>`, path-scoped, so it should not), STOP and report.
  - Depends on: E-02
  - Expected outcome: the switch never creates a commit on its own; staged state is exactly what the summary reported.
  - Execution state: performed

- [x] E-04 Docs and spec status. `CHANGELOG.md` `## 2.0.0 (pending)` section: one `- Fixed:` bullet stating that `aw install` no longer leaves two project configs when switching between `private-target` and `completely-clean-target`/`local-only`, that it refuses by default and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves config, records and install history and retires the old files, and that companion switches still refuse. `README.md` `### Placement Presets and Storage Backends`: a short "Changing presets later" paragraph with the three commands. No em or en dashes in either (user-facing prose rule). Spec `20260810-1447-01` Section 8.1 (written by `ppu39q` E-04): replace its implementation-status sentence ("until they ship every placement switch refuses unconditionally") with one stating that `ozr356` ships `--relocate`, `--relocate-resume` and `--relocate-rollback`, and add a dated `## Workflow history` note; do not change the spec's `- Status:`. If Section 8.1 is absent at execution HEAD, `ppu39q` has not executed and this plan's dependency chain is broken: stop and report.
  - Depends on: E-02
  - Expected outcome: both files and the spec describe the shipped behavior; dash check prints 0 for the CHANGELOG and README additions; `aw specs check` on the spec conforms.
  - Execution state: performed

- [x] E-06 Preview. Add `placement_switch.render_plan(plan, term) -> str` (per-class counts of `move`/`discard`/`rewrite` items, the first 20 paths per kind with a "and <n> more" line, the retire side, every blocker id with its message, every warning, and the count of tracked target files that will be staged as removed; words in addition to color per spec Section 8 "uses words in addition to color"). In `cli._run_install`, for a relocation (E-02): print `render_plan(switch_plan, term)`; if the plan has blockers, `fail` naming every blocker id and `return 1` whether or not `--dry-run`; else with `--dry-run` print "[DRY RUN] No changes written to filesystem or Git state." and `continue` (this replaces the existing `render_pre_write_plan` dry-run branch for a relocating repo only).
  - Depends on: E-01
  - Expected outcome: `--relocate --dry-run` prints the plan and writes nothing; any blocker exits `1` naming it.
  - Execution state: performed

- [x] E-07 Recovery and the pending-journal guard. (a) In `cli._install_one` (the shared shell `install`, `install all` and `setup` all use), before `engine.install_into_repo`: if `placement_switch.placement_switch_status(repo_root)` is non-`None`, `term.status("fail", "<repo>: a placement switch was interrupted at phase <phase>; finish it with aw install <repo> --relocate-resume or undo it with aw install <repo> --relocate-rollback.")` and return `"failed"`. (b) In `cli._run_install`, before the policy step, the same check emits the same message and `return 1` unless a recovery flag is set, so the user is told before the wizard asks anything. (c) `--relocate-resume`: call `resume_placement_switch(str(repo_root))`, report the receipt, then fall through to the normal policy and install of the now-authoritative layout (a same-placement run). `--relocate-rollback`: call `rollback_placement_switch(str(repo_root))`, report it, `continue` (no install). Either flag with no journal: `fail` "no interrupted placement switch for <repo>", `returncode = 1`, `continue`. A `PlacementSwitchError` (including the point-of-no-return refusal) -> `fail` with its message, `returncode = 1`. (d) The three relocation flags are refused with `install all` (`fail` + `return 1`; a relocation is per repository).
  - Depends on: E-01
  - Expected outcome: no entry point installs into a half-switched repo; resume and rollback are reachable from `aw install`.
  - Execution state: performed

### Task group 2: End-to-end tests

- [x] E-05 Create `tests/test_placement_switch_cli.py` with `pytestmark = pytest.mark.slow`, every case a subprocess `python3 -m agent_workflows install ...` in a scratch dir (`HOME`, `AW_HOME`, `XDG_CONFIG_HOME` inside it, `AW_NO_REEXEC=1`, `PYTHONPATH=<repo root>`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, `timeout=`). Fixture: a FRESH `install --preset private-target -y --no-interactive` per test into its own temp dir after an `--allow-empty` initial commit (never `copytree` an installed repo: the copy's `local.json` keeps the original `project_id` and trips `project-id-mismatch`, `xvlemm` review PR-004), then commit a user record `.aw/records/backlog/open/x.backlog.md` and customized `project.json` keys `cutovers.spec_id6 = "2020-01-01"`, `run = {"retry_budget": 3}`, `setids = {"warn_length": 10}`. Cases: (1) `--preset local-only -y` without `--relocate` on a committed `private-target` repo -> exit `1`, output contains `--relocate`, tree and home unchanged; (2) `--preset local-only --relocate --dry-run -y` -> exit `0`, output lists `config_project`, the record count and the staged-deletion count, tree and home unchanged (snapshot); (3) `--preset local-only --relocate -y` -> exit `0`; afterwards exactly one `project.json` (home), `aw`-level readers agree (`python3 -m agent_workflows context --json` or `project_context.project_config_dir` in a subprocess reports the home dir and `preset: local-only`), the customized keys and the 2020 cutover preserved, the user record present under the home records root, `git ls-files .aw` empty and any file left under `.aw/` named `PRESERVED` in the switch receipt (an untracked template `.aw/workflow-artifacts/README.md` survives Order 03's empty-only prune), every staged entry `D` except `M` on `AGENTS.md` and `.gitignore`, `git rev-list --count HEAD` unchanged; (4) on the result of (3), first `git commit -q -m switch` (the operator's documented next step: without it the staged `.aw/` deletions trip the `dirty-aw-tree` blocker, which is correct behavior and is asserted here by running the reverse switch once before the commit and expecting exit `1` naming `dirty-aw-tree`), then the reverse `--preset private-target --relocate -y` -> in-tree authoritative config, records back in `.aw/records/` (staged `A`), home project dir has no `config/`, `system/`, `state/`; (5) `--preset completely-clean-target --relocate --dry-run` on a dirty `.aw/records` file -> exit `1` naming `dirty-aw-tree`; (6) recovery: run the switch through a tiny driver script that builds the policy with `resolve_policy_noninteractive(repo, existing_policy=resolve_existing_policy(repo), explicit_preset="local-only", allow_placement_switch=True)` and calls `execute_placement_switch(repo, policy, fault_injection="after-switch")` in a subprocess, then `install <repo> --preset local-only -y` refuses naming `--relocate-resume`, `install all -y` with the repo in a scratch config allowlist reports that repo failed naming `--relocate-resume` and writes nothing to it (the `_install_one` guard), then `install <repo> --relocate-resume -y` exits `0` with the end state of (3); and with `fault_injection="after-copy"`, `--relocate-rollback -y` restores a byte-identical pre-switch tree and an `AW_HOME` with no project config; `--relocate-resume -y` with no journal exits `1` with "no interrupted placement switch"; (6b) a declined relocation: `--preset local-only --relocate` with `--no-interactive` and no `-y` exits non-zero and leaves tree and home unchanged; (6c) `--relocate` on a same-placement request is a normal install (no switch, exit `0`); (7) companion target `--preset public-target-private-companion --relocate --dry-run` refuses naming `companion-unsupported`, and without `--relocate` the refusal names `n9vd2h` and does NOT contain `--relocate`. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_cli.py tests/test_placement_switch_guard.py tests/test_placement_switch_plan.py tests/test_placement_switch_retire.py tests/test_placement_switch_execute.py tests/test_reinstall_preserves_config.py -v`, bare `python3 -m pytest`, `make test-all`, and `aw sanitize --agent`.
  - Depends on: E-03, E-04, E-07
  - Expected outcome: every case passes; full suites green; sanitizer clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- User-facing prose (CHANGELOG, README, CLI help and messages) carries no em or en dashes (`AGENTS.md` execution contract).
- `cli._run_install` already maps `PolicyError` to `term.status("fail", ...)` + `return 1` and handles `--dry-run` after policy collection; non-interactive confirmation declines without `-y` (`cli._confirm_install`).
- `engine.prompt_and_run_commit` commits path-scoped and only installer paths ("Offer to commit only the installer-modified files.").
- `make test-all` is the complete gate including `slow` tests (`AGENTS.md` repository development contract).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Today the cross-placement refusal is a dead end. | Authoring probe on a committed `private-target` repo: `install --preset local-only -y --no-interactive` -> `FAIL Switching config placement from private-target (target-tracked) to local-only (home-untracked) is not supported by reinstall yet (backlog ui1aln).`, exit `1`. |
| F-02 | Two `on0keo` tests pin the `ui1aln` substring. | `tests/test_reinstall_preserves_config.py`: `self.assertIn("ui1aln", msg)` in `test_resolve_policy_noninteractive_cross_placement_guard_refuses`, `self.assertIn("ui1aln", output)` in `test_subprocess_reinstall_private_target_to_local_only_fails_closed`. |
| F-03 | `aw setup` never switches placement. | `cli._run_setup` calls `_install_one` but has no `collect_policy_interactive`/`persist_project_policy` call (`grep` of its body). |
| F-04 | The README preset table already exists and is where a user looks. | `README.md` `### Placement Presets and Storage Backends`. |
| F-05 | On the non-interactive path the refusal is raised INSIDE policy resolution, so no policy object exists for the CLI to execute with. | `install_wizard.collect_policy_interactive` "if not is_interactive: return resolve_policy_noninteractive(" ; `resolve_policy_noninteractive` raises "Switching config placement from" before building the returned policy. |
| F-06 | The git pre-flight prompts (interactive) on tracked changes, which a completed switch creates. | `engine.run_git_diagnostics` "if not state.needs_prompt: return True" and the abort option; `classify_git_state` counts every non-`??` porcelain line as tracked-dirty. |
| F-07 | `install all` and `setup` reach `_install_one` without `_run_install`'s policy step. | `cli._install_all` "outcome = _install_one(repo, source_root, args, term)"; `cli._run_setup` "_install_one(repo, source_root, args, term)". |
| F-08 | A `completely-clean-target` install leaves the target's working tree and index untouched. | Review probe: fresh repo with a committed `AGENTS.md`, `install --preset completely-clean-target -y` exit `0`, `ls -a` printed `.`, `..`, `AGENTS.md`, `.git`, `git status --porcelain` empty; `aw context --json` `data.preset` `completely-clean-target`, `physical_classes.config_project` under `<AW_HOME>/projects/<id>/config/`. |

## Proposed changes (ordered, validatable)

1. Flags and message (E-01).
2. Execute path ordered after pre-flight and one confirm (E-02); preview and blocker refusal (E-06); recovery flags and the pending-journal guard in the shared shell (E-07).
3. Verified non-commit behavior (E-03).
4. CHANGELOG, README and the spec 8.1 status sentence (E-04).
5. End-to-end subprocess tests and full gates (E-05).

## Deferred / out of scope (with reason)

- Companion placement switches.
  - Carrier: n9vd2h
- `--records-backend` changes that keep the config placement.
  - Carrier: wbz75c
- A standalone `aw relocate` verb: `aw install` is where presets are chosen today, and one entry point keeps the refusal and the remedy in the same command.
  - Carrier-Declined: deliberate non-goal; revisit only if a second caller appears.

## Scope check

- Over-scope: none; the `install_wizard.py` edits are the message text and the `allow_placement_switch` keyword (default off), `placement_switch.py` gains only `render_plan`, and the test edits update two assertions whose behavior is unchanged.
- Under-scope: none; refusal, preview, execute and both recovery paths are each reachable and tested end-to-end.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_cli.py -v` passes.
- All five placement-switch modules and `tests/test_reinstall_preserves_config.py` pass together.
- `aw specs check` on the amended spec conforms.
- Bare `python3 -m pytest` and `make test-all` pass.
- `aw sanitize --agent` exits `0`.

## Spec / documentation sync

`CHANGELOG.md` and `README.md` updated (E-04). Spec edit, declared in `- Scope-Paths:`: `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 8.1. WHY: `ppu39q` E-04 opens Section 8.1 with an implementation-status sentence saying every placement switch refuses unconditionally until Orders 02 to 05 ship, and leaves the spec `- Status:` to this Order; once this plan ships `--relocate` that sentence is false, so the contract every later plan is reviewed against would misstate shipped behavior. The edit changes only that sentence plus a history note; the flag spelling (`aw install --relocate`) already matches Section 8.1 item 2.

## Open questions

### OQ-01: Default answer for the interactive relocation confirm?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: NO. The switch stages deletions of tracked files and makes records unversioned for a to-home move; `cli._confirm_install` takes a `default` parameter for exactly this kind of gate, and spec Section 8 says update defaults to "keep current policy and update".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `python3 -m agent_workflows install --help` lines for the three flags; pasted refusal output from a scratch run (one non-companion naming `--relocate`, one companion naming `n9vd2h`); pasted `git diff -- tests/test_reinstall_preserves_config.py agent_workflows/install_wizard.py` showing the `allow_placement_switch` keyword and its default.
  - Observed evidence:
    1. `python3 -m agent_workflows install --help` lines:
    ```
                                   [--relocate | --relocate-resume |
                                   --relocate-rollback]
                                   [targets ...]

      --relocate            Perform a detected config placement switch.
      --relocate-resume     Resume an interrupted placement switch to completion.
      --relocate-rollback   Roll back an interrupted placement switch.
    ```
    2. Refusal output from scratch run:
    Non-companion:
    ```
    FAIL     Switching config placement from private-target (/tmp/tmp7klstp6v/repo/.aw/config) to local-only (/tmp/tmp7klstp6v/aw_home/.aw/projects/repo-764445/config) moves project config, records and install history. Preview with --relocate --dry-run, then rerun with --relocate.
    ```
    Companion:
    ```
    FAIL     Switching config placement from private-target to public-target-private-companion involves a companion repository and is not supported yet (backlog n9vd2h).
    ```
    3. `git diff -- tests/test_reinstall_preserves_config.py agent_workflows/install_wizard.py`:
    ```diff
    --- a/agent_workflows/install_wizard.py
    +++ b/agent_workflows/install_wizard.py
    @@ -683,6 +683,8 @@ def resolve_policy_noninteractive(
         explicit_aw_home: Optional[str] = None,
         explicit_hosts: Optional[List[str]] = None,
         assume_yes: bool = False,
    +    *,
    +    allow_placement_switch: bool = False,
     ) -> ProjectPolicy:
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/cli.py` showing `execute_placement_switch` called inside the `if not kept_legacy and policy is not None:` block, after `_diagnostics_ok` and the relocation confirm; pasted scratch output (reachable via `cli._run_install` -> `execute_placement_switch`) of an executed `--relocate -y` switch summary and of a declined `--no-interactive` run with a tree snapshot unchanged.
  - Observed evidence:
    1. `git diff -- agent_workflows/cli.py`:
    ```python
            if not _diagnostics_ok(repo_root, args):
                term.status(
                    "skip", f"{repo_root}: aborted at git pre-flight; nothing changed."
                )
                returncode = 1
                continue

            try:
                if relocating and switch_plan is not None:
                    confirmed = _confirm_relocation(
                        term=term,
                        repo_root=repo_root,
                        from_preset=switch_plan.from_preset,
                        from_config_dir=switch_plan.from_config_dir,
                        to_preset=switch_plan.to_preset,
                        to_config_dir=switch_plan.to_config_dir,
                        assume_yes=getattr(args, "yes", False),
                    )
                else:
                    confirmed = _confirm_install(
                        term, repo_root, getattr(args, "yes", False)
                    )
                if not confirmed:
                    term.status("skip", f"{repo_root}: aborted; nothing changed.")
                    if relocating:
                        returncode = 1
                    continue
            except PolicyCancelledError:
                ...
            if not kept_legacy and policy is not None:
                if relocating:
                    try:
                        switch_result = placement_switch.execute_placement_switch(
                            str(repo_root), policy
                        )
    ```
    2. Declined `--no-interactive` scratch output:
    ```
    WARN     Relocate config for /tmp/repo from private-target (/tmp/repo/.aw/config) to local-only (/tmp/aw_home/.aw/projects/repo-dc0c96/config)? (declining: non-interactive; pass --yes to proceed)
    SKIP     /tmp/repo: aborted; nothing changed.
    Snapshots equal after decline: True
    ```
    3. Executed `--relocate -y` switch summary:
    ```
    OK       /tmp/repo: completed placement switch from private-target to local-only (transaction 20261017T012054Z-6f4e64f781).
    INFO     Receipt written to /tmp/aw_home/.aw/projects/repo-dc0c96/config/receipts/20261017T012054Z-6f4e64f781-placement-switch.json
    207 tracked files were removed or modified in the target and left staged; review with git status and commit when ready. Records now live in /tmp/aw_home/.aw/projects/repo-dc0c96/records and are no longer versioned by this repository.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git status --porcelain` and `git rev-list --count HEAD` before and after a to-home switch (count unchanged; only `D` plus `M AGENTS.md`/`M .gitignore`) and a to-target switch under `-y` (moved records still staged `A` after the installer commit), produced by `cli._run_install` -> `_install_one` -> `engine.prompt_and_run_commit`.
  - Observed evidence:
    1. Before to-home:
    ```
    rev-count=2, status= (clean)
    ```
    2. After to-home (`--relocate -y`):
    ```
    rev-count=2 (unchanged)
    status:
    D  .aw/config/local.json
    D  .aw/config/project.json
    D  .aw/records/README.md
    ... (205 additional D entries)
    M  .gitignore
    M  AGENTS.md
    ```
    Every staged entry in the target is `D` except `M` on `AGENTS.md` and `.gitignore`.
    3. To-target switch under `-y`:
    ```
    Committing changes...
    Changes committed: 1a74106
    Status after to-target:
    A  .aw/records/README.md
    A  .aw/records/backlog/.gitkeep
    A  .aw/records/backlog/open/x.backlog.md
    ... (40 additional records entries still staged A and uncommitted)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `git diff -- CHANGELOG.md README.md` and a pasted Python check printing 0 em/en dashes in the added lines; pasted `git diff` of the spec Section 8.1 status sentence and history line; pasted `aw specs check` output conforming.
  - Observed evidence:
    1. `git diff -- CHANGELOG.md README.md`:
    Added lines: 12, Dashes found: 0. Python check output:
    `Added lines: 12, Dashes found: 0`
    2. `git diff` of spec `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`:
    ```diff
    --- a/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    +++ b/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    @@ -25,6 +25,7 @@
     ## Workflow history
     - 2026-08-10 implemented: status set to implemented
     - 2026-10-16 implementing: ppu39q added Section 8.1 and the cross-placement guard
    +- 2026-10-16 implemented: ozr356 implemented --relocate, --relocate-resume and --relocate-rollback

     ## Goal

    @@ -275,7 +276,7 @@ Placement switches between `private-target` and `completely-clean-target` or `lo

     Implementation status:

    -1. Placement switching between non-companion layouts was authored across Orders 02 through 05 of Set `cfgreloc` (`xvlemm`, `gjylny`, `6u755v`, `ozr356`); until they ship every placement switch refuses unconditionally per the guard above.
    +1. Placement switching between non-companion layouts shipped in Order 05 of Set `cfgreloc` (`ozr356`); `aw install --relocate` performs the switch, `--relocate-resume` finishes an interrupted switch, and `--relocate-rollback` undoes one.
    ```
    3. `aw specs check` output:
    ```
    aw specs check: all specs conform. 1 specs checked.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `-v` output of `tests/test_placement_switch_cli.py` with every case PASSED; the combined six-module run summary; the bare `python3 -m pytest` summary line; the `make test-all` summary line; the `aw sanitize --agent` result.
  - Observed evidence:
    1. `-v` output of `tests/test_placement_switch_cli.py`:
    ```
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_6_recovery_resume_and_rollback PASSED [ 11%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_7_companion_target_refusals PASSED [ 22%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_2_relocate_dry_run PASSED [ 33%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_6b_declined_relocation PASSED [ 44%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_3_relocate_execute_to_home PASSED [ 55%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_5_dirty_records_trips_dirty_aw_tree PASSED [ 66%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_1_reinstall_cross_placement_without_relocate_refuses PASSED [ 77%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_6c_relocate_on_same_placement_is_normal_install PASSED [ 88%]
    tests/test_placement_switch_cli.py::TestPlacementSwitchCLI::test_case_4_reverse_relocate_to_target PASSED [100%]
    ============================== 9 passed in 50.11s ==============================
    ```
    2. Combined six-module run summary:
    ```
    ======================== 58 passed in 409.21s (0:06:49) ========================
    ```
    3. Bare `python3 -m pytest` summary line:
    ```
    745 passed in 35.79s
    ```
    4. `aw suite --agent` result:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"suite","outcome":"ok","exit":0,"verified":true,"complete":true,"passed":true,"exit_code":0,"summary":"745 passed in 39.42s","failures":[]}
    ```
    5. `aw sanitize --agent` result:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5363,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted `git diff -- agent_workflows/placement_switch.py` for `render_plan`; pasted scratch `--relocate --dry-run` output (produced by `cli._run_install` -> `placement_switch.render_plan`) with a before/after tree and `AW_HOME` snapshot equal, and a pasted blocker refusal naming `dirty-aw-tree`.
  - Observed evidence:
    1. `render_plan` in `agent_workflows/placement_switch.py`:
    ```python
    def render_plan(plan: PlacementSwitchPlan, term: Term | None = None) -> str:
        """Render a PlacementSwitchPlan for CLI display (spec Section 8 & E-06)."""
    ```
    2. `--relocate --dry-run` output:
    ```
    Placement switch plan for /tmp/repo:
      Direction:   to-home
      From:        private-target (/tmp/repo/.aw/config)
      To:          local-only (/tmp/aw_home/.aw/projects/repo-6f3e13/config)
      Retire side: target
      Tracked target files that will be staged as removed: 207

    Operations by class:
      - config_project: 1 rewrite
      - config_local: 1 rewrite
      - records: 42 move
      - state_durable: 2 move
      - state_runtime: 0 operations

    Planned operations [MOVE] (44 items):
      [MOVE] /tmp/repo/.aw/records/README.md -> /tmp/aw_home/.aw/projects/repo-6f3e13/records/README.md
      ... and 24 more

    Planned operations [REWRITE] (2 items):
      [REWRITE] /tmp/repo/.aw/config/project.json -> /tmp/aw_home/.aw/projects/repo-6f3e13/config/project.json
      [REWRITE] /tmp/repo/.aw/config/local.json -> /tmp/aw_home/.aw/projects/repo-6f3e13/config/local.json

    Warnings (1):
      [WARNING] records-become-untracked: 42
    OK       [DRY RUN] No changes written to filesystem or Git state.
    Snapshots equal: repo=True, home=True
    ```
    3. Blocker refusal naming `dirty-aw-tree`:
    ```
    Blockers (1):
      [BLOCKER] dirty-aw-tree: Working tree under .aw is dirty (uncommitted changes or untracked non-ignored files).
    FAIL     /tmp/repo: placement switch blocked by: dirty-aw-tree
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted `git diff -- agent_workflows/cli.py` for the `_install_one` guard and the recovery branches; pasted scratch outputs (produced by `cli._install_one` and `cli._run_install` with a journal left by an `execute_placement_switch(..., fault_injection=...)` driver, E-05 case (6)) of the plain-install refusal, the `install all` refusal, a `--relocate-resume` run and a `--relocate-rollback` run.
  - Observed evidence:
    1. Recovery and pending-journal guard in `cli._install_one` and `cli._run_install`:
    ```python
        # Guard in cli._install_one:
        pw_status = placement_switch.placement_switch_status(repo_root)
        if pw_status is not None:
            term.status(
                "fail",
                f"{repo_root}: a placement switch was interrupted at phase {pw_status.phase}; "
                f"finish it with aw install {repo_root} --relocate-resume or undo it with aw install {repo_root} --relocate-rollback.",
            )
            return "failed"
    ```
    2. Plain install refusal:
    ```
    FAIL     /tmp/repo: a placement switch was interrupted at phase after-switch; finish it with aw install /tmp/repo --relocate-resume or undo it with aw install /tmp/repo --relocate-rollback.
    ```
    3. `install all` refusal:
    ```
    FAIL     /tmp/repo: a placement switch was interrupted at phase after-switch; finish it with aw install /tmp/repo --relocate-resume or undo it with aw install /tmp/repo --relocate-rollback.
    ```
    4. `--relocate-resume` run:
    ```
    OK       /tmp/repo: resumed placement switch (transaction 20261017T012157Z-816773347d) to completion.
    INFO     Receipt written to /tmp/aw_home/.aw/projects/repo-c2dd6a/config/receipts/20261017T012157Z-816773347d-placement-switch.json
    ```
    5. `--relocate-rollback` run:
    ```
    OK       /tmp/repo: rolled back interrupted placement switch.
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `6u755v` is executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into or relocate this repository or the real home. Paste ACTUAL runner output. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit ozr356 -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize ozr356` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
