# IPD: Refuse a cross-placement policy write at every entry point and specify the placement-switch contract

- Date: 2026-10-16
- Kind: child
- Concern: Plan `on0keo` added a cross-placement refusal only inside `install_wizard.resolve_policy_noninteractive`, comparing the stored `placements["config_project"]` VALUE of the old and new presets. Authoring probes (scratch `AW_HOME`, `AW_NO_REEXEC=1`) show two live bypasses that still produce the `ui1aln` split brain today: (a) the interactive wizard (`collect_policy_interactive`, answer `n` at "Keep current policy", pick `[4] local-only`) on a `private-target` repo returns a `local-only` policy and `persist_project_policy` writes `<AW_HOME>/projects/r-int-e6fa99/config/project.json` while `project_config_dir` still returns `<repo>/.aw/config` holding `preset: private-target`; (b) `aw install <repo> --delivery-mode clean-delta --records-backend home -y --no-interactive` on a `private-target` repo exits `0`, writes `<AW_HOME>/projects/r-dm-7c8422/config/{project,local}.json`, and leaves the in-tree file authoritative with `delivery_mode: tracked`. Root cause: `project_context.resolve_project_context` derives the config root from `delivery_mode` ("elif resolved_delivery_mode == DeliveryMode.TRACKED.value: config_root = ... repo_abs, ".aw", "config""), not from the preset's placement label, so a value-based preset comparison misses delivery-mode-only switches, and the wizard path never reaches the guard at all.
- Scope: IN: a pure path-based detector `install_wizard.config_placement_switch(repo_path, policy)` comparing `project_context.project_config_dir(repo)` (the AUTHORITATIVE dir every reader uses) with the directory `persist_project_policy` would write; a typed `PlacementSwitchRequired(InvalidPolicyError)` carrying both paths and presets; the refusal at the top of `persist_project_policy` (defense in depth, before any write) and in `cli._run_install` right after `collect_policy_interactive` returns (before the dry-run render, companion attach and any write); replacing the value-based check in `resolve_policy_noninteractive` with the shared detector; the placement-switch contract as a new spec Section 8.1. OUT: the planner, executor, retirement and the `--relocate` flag (Orders 02 to 05).
- Scope-Paths: agent_workflows/install_wizard.py, agent_workflows/cli.py, tests/test_placement_switch_guard.py, tests/test_reinstall_preserves_config.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ui1aln
- Blocks-Release: next
- Set: cfgreloc
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: ppu39q

## Workflow history
- 2026-10-16 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cfgreloc graduating backlog ui1aln.

## Goal

No install path can create a second `project.json` that readers ignore: every write that would land in a config directory other than the authoritative one refuses before writing, with one shared detector, and the relocation the later children build is specified in the spec first.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Shared detector and refusals

- [ ] E-01 Re-run the two authoring bypass probes at execution HEAD in a scratch directory under `/tmp` (scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`, `AW_NO_REEXEC=1`, `PYTHONPATH=<worktree>`): (a) install `--preset private-target -y --no-interactive`, then drive `collect_policy_interactive` with `sys.stdin = io.StringIO("n\n4\nprivate\n\n\n\n\n")` and call `persist_project_policy`; (b) install `--preset private-target`, then `install <repo> --delivery-mode clean-delta --records-backend home -y --no-interactive`. For each, print `project_config_dir(repo)`, the stored `preset`/`delivery_mode` there, and the list of `<AW_HOME>/projects/*/config/project.json`. Re-measure the current symbol locations (`grep -n` for `def persist_project_policy`, `def resolve_policy_noninteractive`, `Switching config placement`, `policy = collect_policy_interactive(` in `cli.py`).
  - Depends on: none
  - Expected outcome: both probes reproduce the split brain (a home `project.json` exists while the reader resolves the in-tree one with a different preset or delivery mode); offsets recorded.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/install_wizard.py` add `class PlacementSwitchRequired(InvalidPolicyError)` with attributes `current_dir`, `target_dir`, `current_preset`, `target_preset`, `reason`, and a pure (no writes) `config_placement_switch(repo_path, policy, existing_policy=None) -> Optional[PlacementSwitch]`, where `PlacementSwitch` is a `NamedTuple(current_dir: Path, target_dir: Path, reason: str)` (so Order 02's "returns `None`" test is unchanged). It returns a hit in exactly two cases, else `None`:
  (a) `reason="path"`: ANY of the files `project_context.project_config_dir` keys on (`project.json`, `local.json`, `config.json`, `policy.json`) exists in `current_dir = project_context.project_config_dir(repo_path, aw_home=policy.aw_home)`, and `target_dir`, the parent of `resolve_project_context(target_repo=repo_path, aw_home=policy.aw_home, delivery_mode=policy.delivery_mode, records_backend=policy.records_backend, preset=policy.preset, role=policy.role, companion_dir=policy.companion_dir).physical_classes["config_project"]`, differs after `Path.resolve()` on both. Keying on project.json alone would miss a legacy `config.json` or a `local.json`-only repo, which `project_config_dir` still resolves in-tree (review probe: in-tree `local.json` only, reader `<repo>/.aw/config`, `local-only` writer `<AW_HOME>/projects/r-a6fe62/config/project.json`). No such file means a first install, never a switch.
  (b) `reason="label"`: ONLY when `existing_policy` is passed, the `on0keo` label comparison moved verbatim from `resolve_policy_noninteractive` (`existing_policy.placements["config_project"]` or its preset default, versus `get_preset_defaults(policy.preset)[0]["config_project"]`) differs; `current_dir == target_dir` is allowed here. This branch MUST be kept: the companion preset resolves its config writer in-tree under `delivery_mode=tracked` (review probe: `writer-companion <repo>/.aw/config/project.json`, reader `<repo>/.aw/config`), so a path-only detector would silently ALLOW `private-target` -> `public-target-private-companion`, which today refuses and which backlog `n9vd2h` and spec 8.1 item 3 say keeps refusing; and `test_resolve_policy_noninteractive_cross_placement_guard_refuses` passes `existing_policy` with no config on disk, so only this branch refuses there.
  Replace the inline block in `resolve_policy_noninteractive` (the `if new_cfg_placement != existing_cfg_placement:` raise) with `config_placement_switch(repo_path, <policy it is about to return>, existing_policy=existing_policy)`, raising `PlacementSwitchRequired`. The message keeps the substrings `Switching config placement`, both preset names and `ui1aln` (asserted by `on0keo` tests `test_resolve_policy_noninteractive_cross_placement_guard_refuses` and `test_subprocess_reinstall_private_target_to_local_only_fails_closed`) and also names `current_dir` and `target_dir`, because a delivery-mode-only switch has the same preset on both sides and the preset names alone do not explain the refusal. Add `config_placement_switch(repo_path, policy)` (path branch only, NO `existing_policy`: a label comparison against a disk-loaded policy would refuse `tests/test_reinstall_preserves_config.py` `test_preserves_companion_dir_for_companion_backend`, whose repo has only an in-tree `local.json`) as the FIRST statement after `dry_run` handling in `persist_project_policy`, raising before `config_dir.mkdir`.
  - Depends on: E-01
  - Expected outcome: one detector; the noninteractive path still refuses every pair it refused before (including companion pairs) with the same substrings; `persist_project_policy` cannot write a second config dir.
  - Execution state: pending

- [ ] E-03 In `cli._run_install`, immediately after `policy = collect_policy_interactive(...)` returns inside the existing `try`, call `config_placement_switch(str(repo_root), policy, existing_policy=existing_policy)` (the label branch included, so an interactive companion pick refuses exactly as the noninteractive one does) and on a hit raise `PlacementSwitchRequired`, which the existing `except PolicyError as exc: term.status("fail", str(exc)); return 1` handler reports. This runs before the `--dry-run` render, `storage.attach_companion` and `persist_project_policy`, so a refused switch writes nothing (including the interactive and `--delivery-mode` paths of E-01).
  - Depends on: E-02
  - Expected outcome: both E-01 bypass probes now exit `1` (the CLI one) or raise (the API one) with no new file under `<AW_HOME>/projects/`.
  - Execution state: pending

- [ ] E-04 Amend spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`: add `### 8.1 Placement switch on update` after Section 8's existing paragraphs, stating: (1) a placement switch is any update whose resolved `config/project.json` directory differs from the authoritative one (`project_config_dir`); (2) without explicit opt-in (`aw install --relocate`) every entry point refuses before any write and names the remedy; (3) supported pairs in this release are between `private-target` and the home-placed presets (`completely-clean-target`, `local-only`) and between the two home-placed presets only when their config directory differs (it does not today, so that pair is a same-placement refresh); companion switches refuse (backlog `n9vd2h`); (4) the switch applies the Section 11.2 transaction discipline (writer lock, per-item journal, verify before switch, switch last, resume, rollback, independent check) to classes `config_project`, `state_durable` (durable install history only) and `records`, with `config_local` re-derived, `system` and host adapters re-materialized by the install that follows, and `state_runtime` plus worktree lanes not carried (a live or work-holding lane blocks); because the two sides may be on different filesystems and the old side must stay fully authoritative until the switch, items are COPIED and hash-verified before the switch and their sources removed only after it, so no permanent twin remains (the Section 11.2 no-twin outcome, reached as copy-verify-switch-remove rather than an in-place move); (5) the authority flip is a single atomic write of the merged new `project.json` (all `cutovers`, `setids` and unknown keys carried) followed by removal of every old config file `project_config_dir` keys on (`project.json`, `local.json`, `config.json`, `policy.json`); rollback is available until the old footprint is retired, after which the remedy is a switch back; (6) old-side tracked files are removed with `git rm` and left STAGED, never committed, and moved records become untracked when leaving the target (the operator is told); (7) refusal blockers: uncommitted or unmerged changes under the old `.aw/`, a non-empty destination not created by this transaction, a live lane, an unparseable `project.json`. Add a dated `## Workflow history` note line. Section 8's existing sentence "a placement change invokes migration planning rather than silently moving files" is the anchor this extends, not a reversal. Because the spec is `- Status: implemented` while items (2) opt-in and (4) to (6) are not built until Orders 02 to 05, open Section 8.1 with an explicit implementation-status sentence: the refusal (items 1 to 3 and 7 as refusal) is implemented by `ppu39q`; `--relocate` and the transaction are specified for Set `cfgreloc` Orders 02 to 05 and until they ship every placement switch refuses unconditionally. Do not change the spec's `- Status:` (that is `aw specs` territory and Order 05's call).
  - Depends on: none
  - Expected outcome: spec carries Section 8.1; `aw specs check` on the spec conforms.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-05 Create `tests/test_placement_switch_guard.py` (`unittest.TestCase`, each test in its own `tempfile.TemporaryDirectory` with `AW_HOME`, `XDG_CONFIG_HOME`, `HOME` patched inside it via `patch.dict(os.environ, ...)`, and an explicit `env=` with `AW_NO_REEXEC=1` and `PYTHONPATH` for subprocesses): (1) `config_placement_switch` returns `None` for a fresh repo, `None` for a same-placement policy, a `reason="path"` hit with both dirs for a `private-target` repo given a `local-only` policy, a `reason="path"` hit for a repo whose in-tree `.aw/config` holds only `local.json` (no `project.json`) given a `local-only` policy, and a `reason="label"` hit for `existing_policy=private-target` given a `public-target-private-companion` policy (companion dir in the temp dir); (2) `persist_project_policy` with a `local-only` policy on a `private-target` repo raises `PlacementSwitchRequired` and creates nothing under `AW_HOME/projects`; (3) the interactive wizard path of E-01 (a) END TO END, in process: `sys.stdin = io.StringIO("n\n4\nprivate\n\n\n\n\n")` (patched via `unittest.mock.patch("sys.stdin", ...)`) then `cli.main(["--no-color", "install", repo])` WITHOUT `-y`/`--no-interactive`; `collect_policy_interactive` treats a `StringIO` stdin as interactive ("or isinstance(sys.stdin, io.StringIO)"), and the review probe showed this exact call returns `rc 0` and writes `<AW_HOME>/projects/r-40d5aa/config/project.json` today. Assert `rc == 1`, `.aw/config/project.json` byte-identical and no `AW_HOME/projects/*/config/project.json`. If the answer sequence no longer reaches `local-only` at execution HEAD, re-derive it from the prompts E-01 prints and record the sequence used; (4) subprocess `install <repo> --delivery-mode clean-delta --records-backend home -y --no-interactive` on a `private-target` repo exits `1`, output contains `Switching config placement`, `.aw/config/project.json` byte-identical, no `AW_HOME/projects/*/config/project.json`; (5) `--dry-run` with the same flags also exits `1` and writes nothing. Mark the subprocess class `@pytest.mark.slow` (the repo convention; `tests/test_reinstall_preserves_config.py` `TestReinstallPreservesConfigSubprocess`). Mutation proof, three separate temporary mutations, each restored before the next: (M1) delete only the E-03 call in `cli._run_install`: test (3) must fail (the noninteractive tests (4)/(5) keep passing because `resolve_policy_noninteractive` already refuses them, so E-03 is proven by the interactive test alone; the `persist_project_policy` guard then raises an uncaught `PlacementSwitchRequired` instead of `rc 1`); (M2) delete the E-03 call AND the detector call in `resolve_policy_noninteractive`: test (5) must fail (`--dry-run` exits `0`); (M3) delete only the detector call in `persist_project_policy`: test (2) must fail. Restore and confirm with `git diff` (empty for both source files). A mutation under which no test fails is a missing test and must be fixed before V-05 passes. Then run `python3 -m pytest -o addopts="" tests/test_placement_switch_guard.py tests/test_reinstall_preserves_config.py tests/test_install_consent_truth.py tests/test_records_untracked_backend.py tests/test_clean_target_config_home.py -m ''` and bare `python3 -m pytest`.
  - Depends on: E-02, E-03
  - Expected outcome: new module passes; M1 fails (3), M2 fails (5), M3 fails (2), all pass after restore; the `on0keo` suite and `tests/test_clean_target_config_home.py` (which calls `persist_project_policy` directly on fresh repos) stay green; bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `project_context` is PURE (module docstring "PURE: ZERO filesystem writes"); the detector calls only its readers.
- Tests exercise behavior through functions and subprocesses, never source inspection (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").
- Subprocess install tests use scratch `AW_HOME`/`XDG_CONFIG_HOME`/`HOME`, `AW_NO_REEXEC=1` and `PYTHONPATH` (`tests/test_reinstall_preserves_config.py` `_make_env`).
- A plan amending a spec lists it in `- Scope-Paths:` and says why in the spec-sync section (`AGENTS.md` "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT").
- Commit through `aw commit ppu39q -- <paths>`; never push.

## Findings

| # | Severity | Location | Finding |
|---|---|---|---|
| F-01 | High | `cli._run_install` -> `collect_policy_interactive` (interactive branch) -> `persist_project_policy` | The interactive wizard never calls `resolve_policy_noninteractive`, so the `on0keo` guard is not on its path. Authoring probe: wizard answers `n`, `4` on a `private-target` repo returned `POLICY local-only`; after `persist_project_policy`, `READER <repo>/.aw/config private-target` and `HOME ['<AW_HOME>/projects/r-int-e6fa99/config/project.json']`. |
| F-02 | High | `install_wizard.resolve_policy_noninteractive` (`existing_cfg_placement` / `new_cfg_placement`) and `project_context.resolve_project_context` (`config root` block) | The guard compares preset placement LABELS, but the resolver picks the config root from `delivery_mode`. `--delivery-mode clean-delta --records-backend home` keeps `preset` and so passes the guard. Authoring probe: exit `0`; home `config/project.json` and `local.json` written; reader still `<repo>/.aw/config` with `delivery_mode: tracked`. |
| F-03 | Medium | `install_wizard.persist_project_policy` | Writes to `ctx.physical_classes["config_project"]` with no check that it is the authoritative dir, so any future caller can reintroduce the split brain. |
| F-04 | Info | spec `20260810-1447-01` Section 8 | "a placement change invokes migration planning rather than silently moving files" is the only contract text; no section defines what a placement switch moves, discards or refuses. |
| F-06 | High | `project_context.resolve_project_context` (companion preset, `delivery_mode=tracked`) | Review probe: for `public-target-private-companion` the resolved config writer is `<repo>/.aw/config/project.json`, the same dir `project_config_dir` returns for a `private-target` repo. A path-only detector therefore ALLOWS `private-target` -> companion, which `on0keo` refuses today (review probe: `REFUSED: Switching config placement from private-target (target-tracked) to public-target-private-companion (companion-tracked)`). E-02 keeps the label comparison as a second branch. |
| F-07 | Medium | `project_context.project_config_dir` ("Rules, in order" 1) | The reader returns `<repo>/.aw/config` when ANY of `project.json`, `local.json`, `config.json`, `policy.json` exists, so a detector gated on `project.json` alone misses a `local.json`-only or legacy repo (review probe: reader in-tree, `local-only` writer at home). |
| F-05 | Info | `--preset` choices in `cli` `p_install` | Valid names are `private-target`, `public-target-private-companion`, `completely-clean-target`, `local-only`; `clean-target` is rejected by argparse (authoring probe: "invalid choice: 'clean-target'"), so tests must use the canonical names. |

## Proposed changes (ordered, validatable)

1. Re-measure and reproduce both bypasses (E-01).
2. Shared path-based detector, typed error, refusal in `persist_project_policy` and `resolve_policy_noninteractive` (E-02).
3. Refusal in `cli._run_install` before any write (E-03).
4. Spec Section 8.1 contract (E-04).
5. Tests with a mutation proof (E-05).

## Deferred / out of scope (with reason)

- The relocation itself (planner, retirement, executor, `--relocate`): later Orders of this Set.
  - Carrier: ozr356
- Companion placement switches: a second repository is involved.
  - Carrier: n9vd2h
- `--records-backend` changes that keep the config placement and orphan records.
  - Carrier: wbz75c

## Scope check

- Over-scope: none. The spec section is the design contract the backlog item says the relocation "needs"; placing it in the first child lets Orders 02 to 05 be reviewed against it.
- Under-scope: none; every install path that writes `project.json` goes through `cli._run_install` or `persist_project_policy` (`grep -n "persist_project_policy(" agent_workflows/*.py` shows the single call site in `cli._run_install`).

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_guard.py` passes, including the subprocess class.
- Mutations M1 (E-03 call), M2 (E-03 plus the `resolve_policy_noninteractive` call) and M3 (the `persist_project_policy` call) each fail their named test and pass after restore.
- `python3 -m pytest -o addopts="" -m '' tests/test_reinstall_preserves_config.py tests/test_install_consent_truth.py tests/test_records_untracked_backend.py tests/test_clean_target_config_home.py` passes.
- Bare `python3 -m pytest` passes; `aw specs check` on the amended spec conforms.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` with Section 8.1 (E-04). WHY: Section 8 promises that a placement change "invokes migration planning" but defines nothing about it; Orders 02 to 05 implement a destructive transaction (tracked-file deletion, moved records), and every reviewer of those plans needs one contract to check them against. No CHANGELOG entry in this child: Order 05 (`ozr356`) adds the single user-facing entry once the feature exists, so the CHANGELOG never describes a half-built switch.

## Open questions

### OQ-01: Compare stored placement labels or resolved paths?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved paths. F-02 shows labels and paths diverge (`resolve_project_context` keys the config root off `delivery_mode` and a `local.json` `config_root` binding), and the bug is literally "the reader and the writer use different directories". Comparing `project_config_dir` with the writer's `physical_classes["config_project"]` parent is the exact predicate of the defect. Amended at review (PR-001): paths are the PRIMARY predicate, but the label comparison is retained as a second branch whenever the caller has an `existing_policy`, because the companion preset resolves its config writer to the same in-tree dir (F-06) and a paths-only detector would newly allow a switch the spec and `n9vd2h` say must refuse. Both branches are demonstrated by review probes quoted in F-06 and F-07.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted probe output for (a) and (b) showing the reader dir, its stored preset/delivery mode, and the home `project.json` list, plus the pasted `grep -n` offsets.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- agent_workflows/install_wizard.py` showing the detector, the typed error, and both call sites; pasted output of `python3 -m pytest -o addopts="" tests/test_reinstall_preserves_config.py -m '' -v` passing (all classes, including the slow subprocess class holding `test_subprocess_reinstall_private_target_to_local_only_fails_closed`; `-k cross_placement` alone would miss it); a pasted in-process call showing `resolve_policy_noninteractive` on an `existing_policy=private-target` with `explicit_preset="public-target-private-companion"` still raises `PlacementSwitchRequired` (`reason="label"`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff -- agent_workflows/cli.py`; pasted re-run of both E-01 probes after the change (reachable via `cli._run_install` -> `collect_policy_interactive` -> `config_placement_switch`) showing exit `1`/the raised error, the message naming both directories, and an empty home `project.json` list; for probe (a) the run is `cli.main(["--no-color", "install", repo])` with the StringIO stdin of E-05 test (3), which reaches `cli._run_install` -> `collect_policy_interactive` (StringIO counts as interactive) -> `config_placement_switch`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff` of the spec showing Section 8.1 and the history line, and pasted `aw specs check <spec>` output conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `-v` output of `tests/test_placement_switch_guard.py` passing; pasted failure lines for each of M1 (test 3), M2 (test 5) and M3 (test 2) and the post-restore pass plus `git diff --stat` showing the restore; pasted adjacent-suite and bare-suite summary lines; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Run every probe and test in scratch directories with `AW_HOME`, `XDG_CONFIG_HOME` and `HOME` inside them; never install into this repository or touch the real home. Paste ACTUAL runner output; never claim a pass you did not run. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; an edit outside it must be justified at finalize with `--scope-reason`. Commit only this plan's paths through `aw commit ppu39q -- <paths>`; never `git add -A`, never push. Under `aw oc run` / `aw agy run` the runner finalizes; by hand, `aw ipd finalize ppu39q` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
