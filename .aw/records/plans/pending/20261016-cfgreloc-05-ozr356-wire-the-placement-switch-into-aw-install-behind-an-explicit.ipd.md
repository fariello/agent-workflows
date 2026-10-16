# IPD: Wire the placement switch into aw install behind an explicit opt-in flag

- Date: 2026-10-16
- Kind: child
- Concern: After Orders 01 to 04 (`ppu39q`, `xvlemm`, `gjylny`, `6u755v`), a user who runs `aw install <repo> --preset local-only` on a `private-target` repo still only gets the refusal "is not supported by reinstall yet (backlog ui1aln)" and has no command that performs the switch. Backlog `ui1aln` is done only when the switch is reachable from the CLI, previewable, recoverable after a crash, and documented.
- Scope: IN: `aw install` flags `--relocate` (perform a detected placement switch), `--relocate-resume` and `--relocate-rollback` (finish or undo an interrupted one); in `cli._run_install`, on `PlacementSwitchRequired`: without `--relocate` keep refusing with a message that names `--relocate` and the `--dry-run` preview; with `--relocate --dry-run` render the Order 02 plan (moves, discards, retirements, warnings, blockers) and write nothing; with `--relocate` (and `-y` or an interactive confirm whose default is NO) call `execute_placement_switch`, then continue into the normal install of the NEW layout (`_install_one`), whose commit offer (`engine.prompt_and_run_commit`) is skipped for a to-home switch because the switch's staged deletions are reported instead (see E-03); a pending journal blocks a plain install with a message naming the two recovery flags; update the refusal message in `install_wizard` (drop "not supported ... yet (backlog ui1aln)", keep the substring `Switching config placement`); update the two `on0keo` assertions that pin `ui1aln` in the message; CHANGELOG and README. OUT: `aw setup` (it calls `_install_one` but never the policy wizard: `cli._run_setup` has no `collect_policy_interactive` call, so it cannot switch placement); companion pairs (`n9vd2h`).
- Scope-Paths: agent_workflows/cli.py, agent_workflows/install_wizard.py, tests/test_placement_switch_cli.py, tests/test_reinstall_preserves_config.py, CHANGELOG.md, README.md
- Item-Dependencies: executed:6u755v
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 5
- Highest E allocated: 05
- Author: opencode
- Id: ozr356

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

`aw install <repo> --preset <new> --relocate` switches an installed repository between target-placed and home-placed config in one command, `--dry-run` shows exactly what it will do first, and an interrupted switch can be finished or undone from the CLI.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: CLI

- [ ] E-01 Add `--relocate`, `--relocate-resume`, `--relocate-rollback` (`store_true`, mutually exclusive group) to the `p_install` parser in `cli`, with help text in plain words (no em or en dashes). In `install_wizard`, change the `PlacementSwitchRequired` message to: "Switching config placement from <old> (<old dir>) to <new> (<new dir>) moves project config, records and install history. Preview with --relocate --dry-run, then rerun with --relocate." Update `tests/test_reinstall_preserves_config.py` `test_resolve_policy_noninteractive_cross_placement_guard_refuses` and `test_subprocess_reinstall_private_target_to_local_only_fails_closed` to assert `--relocate` instead of `ui1aln` (the behavior they pin, exit `1` and an unchanged `project.json`, is unchanged).
  - Depends on: none
  - Expected outcome: `aw install --help` lists the flags; the refusal names the remedy.
  - Execution state: pending

- [ ] E-02 In `cli._run_install`: (a) before the policy step, if `placement_switch.placement_switch_status(repo_root)` is non-`None` and neither recovery flag is set, fail with a message naming the phase and both recovery flags, `return 1`; with `--relocate-resume`/`--relocate-rollback` call the matching Order 04 function, report its result and `continue` (rollback) or fall through to the normal install of the now-authoritative layout (resume); (b) on `PlacementSwitchRequired` raised by the Order 01 check: without `--relocate` keep the current `fail` + `return 1`; with `--relocate` build the plan with `plan_placement_switch`, render it (new `placement_switch.render_plan(plan, term)`: per-class counts, the first 20 paths per kind, every blocker and warning, the staged-deletion count, plain words in addition to color per spec Section 8 "uses words in addition to color"), and on `--dry-run` stop there with `return 0` if no blocker else `1`; if blockers, `fail` + `return 1`; otherwise confirm (`-y` skips; interactive prompt default NO; non-interactive without `-y` declines, matching `cli._confirm_install`) and call `execute_placement_switch(str(repo_root), policy)`. On success, print the receipt summary and the honest note for to-home ("<n> tracked files were removed from the target and left staged; review with git status and commit when ready. Records now live in <dir> and are no longer versioned by this repository.") and continue into `persist_project_policy` (now a same-placement write, so the Order 01 guard passes) and `_install_one`.
  - Depends on: E-01
  - Expected outcome: refusal, preview, execute, resume and rollback all reachable from `aw install`.
  - Execution state: pending

- [ ] E-03 Commit-offer interaction. For a to-home switch the new layout is clean-delta, so `_install_one` already skips `engine.prompt_and_run_commit` ("if not engine._is_clean_delta_install(repo_root):"); verify the staged deletions stay staged and are NOT auto-committed under `-y`, and that `git status` in the target shows only the switch's `D` entries. For a to-target switch `prompt_and_run_commit` runs and, under `-y`, commits installer paths; do NOT add the switch's staged records to its `files_to_commit` input, and assert in the test that the moved records remain staged (`A`) and uncommitted while installer files follow today's behavior. Record the observed behavior in V-03; if `prompt_and_run_commit` sweeps the staged records into its commit (it commits with `git commit -- <paths>`, path-scoped, so it should not), STOP and report.
  - Depends on: E-02
  - Expected outcome: the switch never creates a commit on its own; staged state is exactly what the summary reported.
  - Execution state: pending

- [ ] E-04 Docs. `CHANGELOG.md` `## 2.0.0 (pending)` section: one `- Fixed:` bullet stating that `aw install` no longer leaves two project configs when switching between `private-target` and `completely-clean-target`/`local-only`, that it refuses by default and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves config, records and install history and retires the old files, and that companion switches still refuse. `README.md` `### Placement Presets and Storage Backends`: a short "Changing presets later" paragraph with the three commands. No em or en dashes in either (user-facing prose rule).
  - Depends on: E-02
  - Expected outcome: both files describe the shipped behavior; dash check prints 0.
  - Execution state: pending

### Task group 2: End-to-end tests

- [ ] E-05 Create `tests/test_placement_switch_cli.py` with `pytestmark = pytest.mark.slow`, every case a subprocess `python3 -m agent_workflows install ...` in a scratch dir (`HOME`, `AW_HOME`, `XDG_CONFIG_HOME` inside it, `AW_NO_REEXEC=1`, `PYTHONPATH=<repo root>`, `timeout=`). Cases: (1) `--preset local-only -y` without `--relocate` on a committed `private-target` repo -> exit `1`, output contains `--relocate`, tree and home unchanged; (2) `--preset local-only --relocate --dry-run -y` -> exit `0`, output lists `config_project`, the record count and the staged-deletion count, tree and home unchanged (snapshot); (3) `--preset local-only --relocate -y` -> exit `0`; afterwards exactly one `project.json` (home), `aw`-level readers agree (`python3 -m agent_workflows context --json` or `project_context.project_config_dir` in a subprocess reports the home dir and `preset: local-only`), the customized keys and the 2020 cutover preserved, the user record present under the home records root, `.aw/` absent from the target working tree, `git status --porcelain` shows only `D` lines, `git rev-list --count HEAD` unchanged; (4) the reverse `--preset private-target --relocate -y` on the result of (3) -> in-tree authoritative config, records back in `.aw/records/` (staged `A`), home project dir has no `config/`, `system/`, `state/`; (5) `--preset completely-clean-target --relocate --dry-run` on a dirty `.aw/records` file -> exit `1` naming `dirty-aw-tree`; (6) recovery: run the switch through a tiny driver script that calls `execute_placement_switch(..., fault_injection="after-switch")` in a subprocess, then `install <repo> --preset local-only -y` refuses naming `--relocate-resume`, then `install <repo> --relocate-resume -y` exits `0` with the end state of (3); and with `fault_injection="after-copy"`, `--relocate-rollback -y` restores a byte-identical pre-switch tree; (7) companion target `--preset public-target-private-companion --relocate --dry-run` refuses naming `companion-unsupported`. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_cli.py tests/test_placement_switch_guard.py tests/test_placement_switch_plan.py tests/test_placement_switch_retire.py tests/test_placement_switch_execute.py tests/test_reinstall_preserves_config.py -v`, bare `python3 -m pytest`, `make test-all`, and `aw sanitize --agent`.
  - Depends on: E-03, E-04
  - Expected outcome: every case passes; full suites green; sanitizer clean.
  - Execution state: pending

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

## Proposed changes (ordered, validatable)

1. Flags and message (E-01).
2. `_run_install` branches for refuse, preview, execute, resume, rollback (E-02).
3. Verified non-commit behavior (E-03).
4. CHANGELOG and README (E-04).
5. End-to-end subprocess tests and full gates (E-05).

## Deferred / out of scope (with reason)

- Companion placement switches.
  - Carrier: n9vd2h
- `--records-backend` changes that keep the config placement.
  - Carrier: wbz75c
- A standalone `aw relocate` verb: `aw install` is where presets are chosen today, and one entry point keeps the refusal and the remedy in the same command.
  - Carrier-Declined: deliberate non-goal; revisit only if a second caller appears.

## Scope check

- Over-scope: none; the `install_wizard.py` edit is the message text, and the test edits update two assertions whose behavior is unchanged.
- Under-scope: none; refusal, preview, execute and both recovery paths are each reachable and tested end-to-end.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_cli.py -v` passes.
- All five placement-switch modules and `tests/test_reinstall_preserves_config.py` pass together.
- Bare `python3 -m pytest` and `make test-all` pass.
- `aw sanitize --agent` exits `0`.

## Spec / documentation sync

`CHANGELOG.md` and `README.md` updated (E-04). No spec edit: spec Section 8.1 (Order 01 `ppu39q`) already names `aw install --relocate` as the opt-in; if the flag spelling changes during execution, that is a spec edit and needs the spec added to `- Scope-Paths:` first.

## Open questions

### OQ-01: Default answer for the interactive relocation confirm?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: NO. The switch stages deletions of tracked files and makes records unversioned for a to-home move; `cli._confirm_install` takes a `default` parameter for exactly this kind of gate, and spec Section 8 says update defaults to "keep current policy and update".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -m agent_workflows install --help` lines for the three flags; pasted refusal output from a scratch run; pasted `git diff -- tests/test_reinstall_preserves_config.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/cli.py`; pasted scratch outputs (reachable via `cli._run_install` -> `plan_placement_switch`/`execute_placement_switch`) of the preview, the executed switch summary, and the pending-journal refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git status --porcelain` and `git rev-list --count HEAD` before and after a to-home and a to-target switch under `-y`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff -- CHANGELOG.md README.md` and a pasted Python check printing 0 em/en dashes in the added lines.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `-v` output of `tests/test_placement_switch_cli.py` with every case PASSED; the combined six-module run summary; the bare `python3 -m pytest` summary line; the `make test-all` summary line; the `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `6u755v` is executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never install into or relocate this repository or the real home. Paste ACTUAL runner output. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit ozr356 -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize ozr356` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
