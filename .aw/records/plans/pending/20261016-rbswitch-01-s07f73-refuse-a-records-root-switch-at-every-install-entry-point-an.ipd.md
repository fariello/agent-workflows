# IPD: Refuse a records-root switch at every install entry point and specify it

- Date: 2026-10-16
- Kind: child
- Concern: Backlog `wbz75c`: on an installed repository, `aw install <repo> --records-backend home -y --no-interactive` (no `--preset`) exits `0`, rewrites `<repo>/.aw/config/project.json` with `records_backend: home` while keeping `preset: private-target` and `delivery_mode: tracked`, and `project_context.resolve_project_context` then returns `<AW_HOME>/projects/<id>/records` as the records root while every existing record stays in `<repo>/.aw/records/` where no reader looks. The config directory does not change, so neither the `on0keo` label guard nor the `ppu39q` path detector (`install_wizard.config_placement_switch`, which compares CONFIG directories) fires. Nothing refuses a records-root change today.
- Scope: IN: a pure detector `install_wizard.records_root_switch(repo_path, policy, existing_policy=None) -> Optional[RecordsRootSwitch]` comparing the CURRENT records root (stored policy) with the records root the new policy resolves, firing only on an installed repo whose current root holds record-bearing files and only when `config_placement_switch` does not already report a full placement switch; a typed `RecordsRootSwitchRequired(InvalidPolicyError)`; the refusal in `resolve_policy_noninteractive`, at the top of `persist_project_policy` (before any write) and in `cli._run_install` right after the `ppu39q` check (before the dry-run render and every write); spec Section 8.2 describing the records-root switch contract. OUT: actually moving records (Order 02 `fxbm7j`), the `--relocate` wiring (Order 03 `vv9ki4`), companion records (backlog `n9vd2h`).
- Scope-Paths: agent_workflows/install_wizard.py, agent_workflows/cli.py, tests/test_records_root_switch_guard.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: executed:ppu39q
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: wbz75c
- Blocks-Release: next
- Set: rbswitch
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: s07f73

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set rbswitch graduating backlog wbz75c.

## Goal

No install path can repoint the records resolver away from a records tree that still holds records: a records-backend change that would orphan records refuses before writing anything, with one shared detector, and the contract for doing it deliberately is specified first.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Detector and refusals

- [ ] E-01 Re-run the backlog probe at execution HEAD in a scratch directory under `/tmp` (scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`, `AW_NO_REEXEC=1`, `PYTHONPATH=<worktree>`): `git init`, `--allow-empty` commit, `python3 -m agent_workflows install <repo> --preset private-target -y --no-interactive`, add and commit `.aw/records/backlog/mine.md`, then `python3 -m agent_workflows install <repo> --records-backend home -y --no-interactive`. Print the exit code, `preset`/`records_backend`/`delivery_mode` from `<repo>/.aw/config/project.json`, `resolve_project_context(target_repo=repo).logical_roots["records"]`, and whether `mine.md` exists under each of the two roots. Also probe the reverse: a fresh repo installed `--preset private-target --records-backend home`, a record written under the home records root, then `install <repo> --records-backend repository -y --no-interactive`. Re-measure the current symbol locations (`grep -n` for `def config_placement_switch`, `def persist_project_policy`, `def resolve_policy_noninteractive`, `class PlacementSwitchRequired`, and the `config_placement_switch(` call in `cli._run_install`). If `config_placement_switch` is absent, `ppu39q` has not executed: stop and report.
  - Depends on: none
  - Expected outcome: both directions reproduce the orphaning (exit `0`, resolver root moved, the record left only under the old root); offsets recorded.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/install_wizard.py` add `RecordsRootSwitch = NamedTuple(current_root: Path, target_root: Path, record_files: int, reason: str)`, `class RecordsRootSwitchRequired(InvalidPolicyError)` (attributes `current_root`, `target_root`, `current_backend`, `target_backend`, `record_files`, `reason`) and a pure (no writes) `records_root_switch(repo_path, policy, existing_policy=None) -> Optional[RecordsRootSwitch]`. It returns `None` unless ALL of: (1) the repository is installed, meaning any of `project.json`, `local.json`, `config.json`, `policy.json` exists in `project_context.project_config_dir(repo_path, aw_home=policy.aw_home)` (a first install has no current records root to orphan); (2) `config_placement_switch(repo_path, policy, existing_policy=existing_policy)` returns `None` (a full placement switch is owned by Set `cfgreloc`, whose relocation moves records too, so this detector must not refuse a `--relocate` that `ozr356` allows); (3) `current_root = resolve_project_context(target_repo=repo_path, aw_home=policy.aw_home).logical_roots["records"]` and `target_root`, the same call passing `policy.delivery_mode`, `records_backend`, `preset`, `role`, `companion_dir`, differ after `Path.resolve()`. Then: if either the stored or the new `records_backend` is `companion`, return `reason="companion"` regardless of content (companion records involve a second repository, backlog `n9vd2h`); otherwise count record-bearing files under `current_root` (every regular file or symlink EXCEPT those named `.gitkeep`, `README.md`, `INDEX.json`, `INDEX.md`, which the installer scaffolds or `aw index` regenerates) and return `reason="records"` with the count when it is at least one, else `None`. The scaffold exclusion is deliberate: it is what lets an already-orphaned repository (the backlog probe state, whose new root holds only scaffold) be repaired by switching back without a refusal. `repository` and `repository-untracked` resolve the same root, so that pair is `None` here (`ProjectPolicy.validate` already refuses tracked records going untracked).
  - Depends on: E-01
  - Expected outcome: one pure detector; `None` for first installs, same-root changes and full placement switches; a hit naming both roots and the record count for the backlog probe in both directions.
  - Execution state: pending

- [ ] E-03 Call the detector at all three entry points, each raising `RecordsRootSwitchRequired` before any write: (a) in `resolve_policy_noninteractive`, on the existing-policy branch, immediately after the `ppu39q` `config_placement_switch` check and before `return pol`, with `existing_policy=existing_policy`; (b) in `persist_project_policy`, immediately after the `ppu39q` guard and before `config_dir.mkdir` (no `existing_policy`); (c) in `cli._run_install`, immediately after the `ppu39q` `config_placement_switch` call that follows `collect_policy_interactive`, with `existing_policy=existing_policy`, so the existing `except PolicyError as exc: term.status("fail", str(exc)); return 1` handler reports it and nothing (dry-run render, `storage.attach_companion`, `persist_project_policy`) runs. Message for `reason="records"`: "Changing the records backend from <old> (<current_root>) to <new> (<target_root>) would leave <n> record files in <current_root> where no reader looks. Moving records between backends is not supported by reinstall yet (backlog wbz75c)." For `reason="companion"`: "Changing the records backend from <old> to <new> involves a companion repository and is not supported yet (backlog n9vd2h)." No em or en dashes (CLI messages are user-facing).
  - Depends on: E-02
  - Expected outcome: the E-01 probes now exit `1` naming both roots, with `project.json` byte-identical and no new file under `<AW_HOME>/projects/`.
  - Execution state: pending

- [ ] E-04 Amend spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`: add `### 8.2 Records-root switch on update` immediately after Section 8.1 (written by `ppu39q`), stating: (1) a records-root switch is an update that keeps the authoritative config directory but changes the resolved records root (today `repository` or `repository-untracked` versus `home` under `delivery_mode: tracked`); (2) when the current records root holds record-bearing files (anything but installer scaffold `.gitkeep`/`README.md` and generated `INDEX.json`/`INDEX.md`), every entry point refuses before any write and names the remedy, and with nothing to orphan the change proceeds as a plain policy update; (3) companion records refuse (backlog `n9vd2h`); (4) the deliberate move applies the Section 8.1 / 11.2 discipline to the `records` class alone: lock, journal, copy-verify, one atomic rewrite of `project.json` carrying every other key as the authority flip, source removal after it, resume and rollback, tracked removals and additions left STAGED and never committed; (5) a full placement switch (Section 8.1) subsumes a records-root switch. Open the section with an implementation-status sentence: the refusal is implemented by `s07f73`; the relocation is specified for Set `rbswitch` Orders 02 and 03 and until it ships every records-root switch that would orphan records refuses. Add a dated `## Workflow history` note line. Do not change the spec's `- Status:`. If Section 8.1 is absent at execution HEAD, stop and report (the `ppu39q` dependency is broken).
  - Depends on: none
  - Expected outcome: spec carries Section 8.2; `aw specs check` on the spec conforms.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-05 Create `tests/test_records_root_switch_guard.py` (`unittest.TestCase`, each test in its own `tempfile.TemporaryDirectory` with `AW_HOME`, `XDG_CONFIG_HOME`, `HOME` patched via `patch.dict(os.environ, ...)`; subprocesses get an explicit `env=` with `AW_NO_REEXEC=1`, `PYTHONPATH`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, `timeout=`; a FRESH install per test after an `--allow-empty` initial commit). Cases: (1) detector `None` on a fresh (never installed) repo; `None` on an installed `private-target` repo given a policy with the same backend; `None` given a `local-only` policy (a config placement switch, owned by `cfgreloc`); `None` for `repository` -> `repository-untracked` on a repo with no tracked records; `None` when the current root holds only scaffold files; a `reason="records"` hit with `record_files == 1` after committing `.aw/records/backlog/mine.md` given `records_backend=home`; a `reason="companion"` hit for `records_backend=companion`; (2) `persist_project_policy` with the `home` policy on that repo raises `RecordsRootSwitchRequired` and `project.json` is byte-identical; (3) subprocess `install <repo> --records-backend home -y --no-interactive` exits `1`, output contains `would leave 1 record files` and both roots, `project.json` byte-identical, `mine.md` still the only copy, no `AW_HOME/projects/*/records/backlog/mine.md`; (4) the same with `--dry-run` exits `1` and writes nothing; (5) reverse direction: repo installed `--preset private-target --records-backend home` with a home record, `install <repo> --records-backend repository -y --no-interactive` exits `1`; (6) repair of an already-orphaned repo: install `private-target`, then (with scaffold only, no user record) `install --records-backend home -y` exits `0`, then write a record into `<repo>/.aw/records/backlog/` (simulating the backlog bug's leftover), then `install --records-backend repository -y` exits `0` and the resolver root is back in-tree and the record is visible; (7) the interactive path: drive `cli.main(["--no-color", "install", repo, "--records-backend", "home"])` with a patched `sys.stdin = io.StringIO("y\n")` (or the answer sequence E-01 records as reaching a `home` backend; record the sequence used) and assert `rc == 1` and `project.json` byte-identical. Mark the subprocess class `@pytest.mark.slow`. Mutation proof, three temporary mutations each restored before the next: (M1) remove the `cli._run_install` call: test (7) fails; (M2) remove the `cli._run_install` and `resolve_policy_noninteractive` calls: test (4) fails (dry-run exits `0`); (M3) remove the `persist_project_policy` call: test (2) fails. Restore and show `git diff` empty for both source files. Run `python3 -m pytest -o addopts="" -m '' tests/test_records_root_switch_guard.py tests/test_placement_switch_guard.py tests/test_reinstall_preserves_config.py tests/test_records_untracked_backend.py tests/test_install_consent_truth.py tests/test_clean_target_config_home.py -v` and bare `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: new module passes; M1 fails (7), M2 fails (4), M3 fails (2); all pass after restore; adjacent suites and the bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `project_context` is PURE ("ZERO filesystem writes"); the detector calls only its readers.
- `ppu39q` (Set `cfgreloc` Order 01) already establishes the pattern this plan mirrors: a NamedTuple-returning pure detector, a typed `InvalidPolicyError` subclass, and three call sites (`resolve_policy_noninteractive`, `persist_project_policy`, `cli._run_install` after `collect_policy_interactive`).
- Tests are behavioral and run in scratch dirs (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"); subprocess install tests use the `tests/test_reinstall_preserves_config.py` `_make_env` shape and `@pytest.mark.slow`.
- A plan amending a spec lists it in `- Scope-Paths:` and says why in the spec-sync section.
- Commit through `aw commit s07f73 -- <paths>`; never push.

## Findings

| # | Severity | Location | Finding |
|---|---|---|---|
| F-01 | High | `install_wizard.resolve_policy_noninteractive` (existing-policy branch, `backend = explicit_backend or existing_policy.records_backend`) | An explicit `--records-backend` on an installed repo is accepted with no comparison to the stored backend. Authoring probe (scratch `AW_HOME`, `AW_NO_REEXEC=1`): second install exited `0`; `project.json` read `preset: private-target`, `records_backend: home`; `resolve_project_context` printed `home <AW_HOME>/projects/repo-1582b4/records`; `ls <repo>/.aw/records/backlog` printed `mine.md`; the home `records/backlog/` held only `.gitkeep`. |
| F-02 | High | `project_context.resolve_project_context` (`# records root` block) | The records root is selected by `resolved_records_backend` alone ("if resolved_records_backend in (RecordsBackend.REPOSITORY.value, RecordsBackend.REPOSITORY_UNTRACKED.value)" -> `<repo>/.aw/records`, else `HOME` -> `project_aw_dir/records`), independently of the config root, so a backend change moves the records root without moving the config root. |
| F-03 | Medium | `ppu39q` E-02 `config_placement_switch` | Compares CONFIG directories (and preset labels); a records-only change keeps both, so it returns `None` here by design. The two detectors are complementary. |
| F-04 | Medium | `layout_migration.MigrationManager` via `aw migrate-layout apply --target-backend home` | Not a usable remedy today: authoring probe on the same repo printed `FAIL Migration plan invalid: [{'rule': 'unknown-owner', 'detail': 'partial-aw:inbox has unknown owner/disposition', ...}]` and moved nothing; its switch phase also writes the legacy `config.json`, not `project.json` (`cfgreloc` `xvlemm` F-01). |
| F-05 | Info | spec `20260810-1447-01` Section 8 | "a placement change invokes migration planning rather than silently moving files" is violated: nothing is planned and the resolver silently switches. |
| F-06 | Info | `cli._run_setup` | Reads `args.records_backend` only to refuse `repository-untracked`, then calls `_install_one`, which never persists policy, so `aw setup` cannot switch the records root; no call site needed there. |

## Proposed changes (ordered, validatable)

1. Re-measure and reproduce both directions (E-01).
2. Shared detector and typed error (E-02).
3. Refusal at the three entry points (E-03).
4. Spec Section 8.2 (E-04).
5. Tests with a mutation proof (E-05).

## Deferred / out of scope (with reason)

- Moving records between backends on request: Order 02 and Order 03 of this Set.
  - Carrier: vv9ki4
- Companion records backends.
  - Carrier: n9vd2h
- A doctor finding for repositories already orphaned by the bug before this fix: the remedy (switching back, test (6)) is allowed by the scaffold exclusion, and the bug never shipped in a tagged release (`git show v1.3.0-rc.1:agent_workflows/cli.py | grep -c records-backend` printed `0`).
  - Carrier-Declined: no released victims; the switch-back repair is tested here.

## Scope check

- Over-scope: none; the spec section is the contract Orders 02 and 03 are reviewed against.
- Under-scope: none; `persist_project_policy` has a single call site (`grep -n "persist_project_policy(" agent_workflows/*.py` prints `cli.py` once plus its definition), and `aw setup` cannot write policy (F-06).

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_records_root_switch_guard.py -v` passes, including the slow subprocess class.
- Mutations M1, M2, M3 each fail their named test and pass after restore.
- Adjacent suites listed in E-05 and bare `python3 -m pytest` pass; `aw specs check` on the amended spec conforms.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` with Section 8.2 (E-04). WHY: Section 8 forbids silently moving or switching storage on update, and Section 8.1 (from `ppu39q`) only covers config placement; the records-only case needs its own contract before Order 02 implements a destructive move. No CHANGELOG entry here: Order 03 (`vv9ki4`) adds the single user-facing entry once the remedy exists.

## Open questions

### OQ-01: Refuse always, or only when records would be orphaned?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Only when the current root holds record-bearing files. A backend change on a repo with nothing but scaffold loses nothing (the installer re-scaffolds the new root), and refusing it would also block the repair of an already-orphaned repo (E-05 test (6)). The scaffold set is exactly what the installer writes plus the regenerated index files, matching `cfgreloc` `xvlemm` E-01, which discards `INDEX.json`/`INDEX.md` as regenerable.

### OQ-02: Extend the cfgreloc detector instead of adding a second one?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: A separate detector. `config_placement_switch` is consumed by the `cfgreloc` planner (`xvlemm` E-01) as the definition of a config placement switch, and widening it would make `plan_placement_switch` treat records-only changes as config relocations it does not handle. The new detector explicitly yields to it (E-02 condition 2), so exactly one refusal fires for any request.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted probe output for both directions (exit code, the three `project.json` fields, the resolver records root, where the record exists) and the pasted `grep -n` offsets.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/install_wizard.py` showing `RecordsRootSwitch`, `RecordsRootSwitchRequired` and `records_root_switch` with its three gating conditions; a pasted in-process call printing the detector result for the probe repo (`reason="records"`, `record_files=1`) and `None` for a `local-only` policy on the same repo.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff -- agent_workflows/cli.py` and the three call sites in the `install_wizard.py` diff; pasted re-run of both E-01 probes (reachable via `cli._run_install` -> `collect_policy_interactive` -> `resolve_policy_noninteractive` -> `records_root_switch`) showing exit `1`, the message naming both roots and the count, `sha256sum` of `project.json` identical before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff` of the spec showing Section 8.2 after 8.1 plus the history line, and pasted `aw specs check <spec>` output conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `-v` output of `tests/test_records_root_switch_guard.py` with every case PASSED; pasted failure lines for M1 (test 7), M2 (test 4), M3 (test 2) and the post-restore pass with `git diff --stat` empty for the source files; pasted adjacent-suite and bare-suite summary lines; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `ppu39q` is executed. EXECUTION CONTRACT: all open questions are resolved. Run every probe and test in scratch directories with `AW_HOME`, `XDG_CONFIG_HOME` and `HOME` inside them; never install into this repository or touch the real home. Paste ACTUAL runner output; never claim a pass you did not run. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; justify any other edit at finalize with `--scope-reason`. Commit only this plan's paths through `aw commit s07f73 -- <paths>`; never `git add -A`, never push. Under `aw oc run` / `aw agy run` the runner finalizes; by hand, `aw ipd finalize s07f73` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
