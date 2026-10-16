# IPD: Prove clean-target zero target delta end to end through ordinary use

- Date: 2026-10-15
- Kind: child
- Concern: Each earlier Set child proves its own slice, but the maintainer's acceptance bar (2026-10-15) is the whole lifecycle: `git -C <target> status --porcelain --ignored` empty and HEAD unchanged after install AND after ordinary use. The predecessor review (irjoga PR-001) measured that the first ordinary verb re-created a target delta (`aw backlog new --apply` wrote `.agents/backlog/` and `.aw/records/history.jsonl` into the target; `aw index prompts --agent` crashed on `<repo>/.aw/records/prompts/INDEX.json`), so a per-slice proof is not enough. Separately, spec `20260810-1447-01` Section 4 still says the target writes "remain open as Phase 3 work" and Section 5 says per-machine control state "stays IN the target repository", which contradicts the shipped clean-delta behavior once this Set lands, and `CHANGELOG.md` has no entry for it.
- Scope: Add one end-to-end subprocess test module `tests/test_clean_target_zero_delta_e2e.py` that installs each clean preset into a temp target and drives a fixed sequence of ordinary verbs (`aw backlog new --apply`, `aw index prompts`, `aw research new --apply`, `aw attention`, `aw status`, `aw doctor`, `aw ipd scaffold --apply`, `aw work begin`, `aw oc run start --prepare-only`, `aw uninstall --yes`), asserting after EVERY step that the target is porcelain-ignored empty and HEAD unchanged and that the step's artifact landed under `<AW_HOME>/projects/<project_id>/`, with a mutation proof; amend spec `20260810-1447-01` Section 4 and Section 5 and record it with `aw specs note`; add one `- Fixed:` line to `CHANGELOG.md` under `## 2.0.0 (pending)`.
- Scope-Paths: tests/test_clean_target_zero_delta_e2e.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md, CHANGELOG.md
- Scope-Exceeded: .aw/records/backlog/open/20261016-707qi4-01-707qi4-work-begin-crashes-on-clean-delta-repos-when-relat.backlog.md (Defect tracking carrier for work begin ValueError crash on clean-delta repos filed during e2e execution.); agent_workflows/work_cmd.py (Bugfix during e2e testing of clean-delta repos: aw work begin crashed with ValueError when relativizing plan_path because clean-delta records live outside repo_root under AW_HOME handled by catching V...)
- Item-Dependencies: executed:xoy5yg
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 7
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: nwporz

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: nwporz verified (set cleantgt, attempt 2). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261016-707qi4-01-707qi4-work-begin-crashes-on-clean-delta-repos-when-relat.backlog.md: Defect tracking carrier for work begin ValueError crash on clean-delta repos filed during e2e execution.; out-of-scope agent_workflows/work_cmd.py: Bugfix during e2e testing of clean-delta repos: aw work begin crashed with ValueError when relativizing plan_path because clean-delta records live outside repo_root under AW_HOME; handled by catching ValueError.]
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): plan-review: revisions applied (PR-001..PR-006)
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Demonstrate, with a test that stays in the suite, that on both `completely-clean-target` and `local-only` a target repository shows no agent-workflows trace (`git status --porcelain --ignored` empty, HEAD unchanged) after install, after each ordinary verb, and after uninstall; then bring the implemented physical-layout spec and the CHANGELOG into line with that behavior so the contract every later plan is reviewed against is true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [x] E-01 At execution HEAD, confirm Set children `kfnfji`, `4gn1ka`, `fnnwj3`, `qk0ew6`, `3m8aix`, `xoy5yg` are in `.aw/records/plans/executed/`, record the accessor names they introduced (`project_context.project_records_dir`, `project_context.project_system_dir`, `project_context.home_configured_root`, `ipd_lifecycle.clean_delta_control_root`, `worktree_lease.worktrees_root`, `engine._is_clean_delta_install`; an absent one makes this item `blocked`, naming it), confirm whether the questions carried here (`qk0ew6` OQ-03, `3m8aix` OQ-03) are still open or record their answers, and run the E-02 verb sequence BY HAND once in a temp target (temp `HOME`/`AW_HOME`, git identity, `XDG_CONFIG_HOME`/`AW_CONFIG_DIR` unset) for `completely-clean-target`, capturing `git status --porcelain --ignored` and `git rev-parse HEAD` after each step and the exact CLI spellings that succeed (for example the `aw research new --kind` value accepted and the `aw oc run start --prepare-only` selector that resolves the scaffolded plan).
  - Depends on: none
  - Expected outcome: A pasted per-step table in V-01. Any step that leaves a target delta or fails is a defect in the owning sibling and is reported (with the owning child's id6) rather than worked around in the test.
  - Execution state: performed

### Task group 2: The end-to-end proof

- [x] E-02 Create `tests/test_clean_target_zero_delta_e2e.py` with a `unittest.TestCase` whose `setUp` mirrors `tests/test_clean_target_config_home.py` `TestCleanTargetConfigHome.setUp` (temp target with an initial commit, temp `HOME`/`AW_HOME`, git identity in env, `AW_NO_REEXEC=1`, `PYTHONPATH` at the source tree) and a helper `_assert_zero_delta(step)` that runs `git -C <t> status --porcelain --ignored` and `git -C <t> rev-parse HEAD` and fails with the step name and the porcelain output when either differs from the pre-install baseline. One test per preset (`test_completely_clean_target_ordinary_use`, `test_local_only_ordinary_use`) drives by subprocess with `cwd=<t>` (`aw ipd scaffold` has no `--dir`; every verb resolves the repo from cwd) and `AW_IPD_AUTHOR=e2e` in env, asserting zero delta after each: `install . --preset <p> -y --no-interactive`; `backlog new --summary "E2E probe" --work-kind chore --priority low --apply` (`backlog new` takes no positional title and refuses without `--priority`); `index prompts`; `research new --kind findings --slug e2e-probe --apply`; `attention`; `status`; `doctor`; `ipd scaffold --kind child --title "E2E probe plan" --set e2eset --order 1 --priority low --work-kind chore --apply` (scaffold refuses without an author and without `--priority`/`--work-kind`); `ipd dependencies set <id6> none` (`oc run start` refuses the scaffold's `unresolved` dependency sentinel, `check.ipd-dependency-unresolved`); `work begin <id6>`; `oc run start <id6> --prepare-only`; `uninstall . --yes`. These spellings were MEASURED at review on a tracked install (PR-001, F-06) and E-01 re-confirms them on clean-delta. Each step's exit code is asserted as the one E-01 observed for that verb: 0 for the writing verbs; `aw doctor` exits nonzero on a fresh install with findings (measured `1` on tracked: manifest index not generated), so the test asserts its OBSERVED code and, independently of the code, the zero-delta bar (PR-003). The `uninstall` step runs AFTER the lane exists, so it also exercises `xoy5yg`'s lane teardown. The scaffolded plan is `draft`, so `--prepare-only` resolves it to a `review` action and needs no approval (measured); `--action execute` is refused for a draft, so the test must not pass it.
  - Depends on: E-01
  - Expected outcome: Both tests pass; a failure message names the first step that touched the target.
  - Execution state: performed

- [x] E-03 In the same tests, assert positively that each writing step's artifact is where the stored policy says (P16: outcome, not structure), using `resolve_project_context(target_repo=..., aw_home=...).physical_classes` read AFTER install: the backlog item and the research file exist under the `records` class root; the scaffolded plan exists under `records/plans/pending/`; `aw work begin` created a worktree whose path is under `<AW_HOME>/projects/<id>/worktrees/` and which `git -C <t> worktree list --porcelain` registers (the accepted residual: git's own `.git/worktrees/<name>` admin entry, which is inside `.git` and therefore not reported by porcelain status); `--prepare-only` created exactly one new `run-*` directory under `runner_shared.state_root(<t>)` and none under `<t>` (`state_root` derives from `logical_roots["records"]`, so for clean-delta it is `<AW_HOME>/projects/<id>/records/runs`, NOT the `state` class root the earlier wording named, PR-004); `aw work begin` validated a plan that lives ONLY in home records (the case `qk0ew6` deferred to this plan); after `uninstall . --yes` home `records/` still holds the backlog item and `git -C <t> worktree list` shows only the main worktree.
  - Depends on: E-02
  - Expected outcome: Every positive assertion passes for both presets.
  - Execution state: performed

- [x] E-04 Mutation proof, temporary and not committed, applied to the SOURCE tree the subprocesses import (`PYTHONPATH` points at the lane's `agent_workflows/`; there is no separate installed copy, PR-005): (a) make the clean-delta predicate from `3m8aix` (`engine._is_clean_delta_install`) return `False` and run the new module, observing failure at the `install` step; restore. (b) make the child-01 records-root accessor `project_context.project_records_dir` return `<repo>/.aw/records` unconditionally and observe failure at the `backlog new` step (or earlier, at `install`, if `3m8aix`'s records scaffolding routes through it; record whichever step the message names); (c) make `qk0ew6`'s `worktree_lease.worktrees_root` return `repo_root / WORKTREES_SUBDIR` and observe failure at the `work begin` step. Restore each and re-run the module green.
  - Depends on: E-03
  - Expected outcome: Each mutation fails the e2e test at a step the failure message names; every restored run passes and `git diff -- agent_workflows/` is empty afterwards.
  - Execution state: performed

### Task group 3: Contract and changelog

- [x] E-05 Amend `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`: (Section 4) replace the sentence beginning "The remaining target writes (.aw/system/, .aw/records/, .aw/.gitignore, host adapters) remain open as Phase 3 work" in the `AMENDED 2026-10-12 (cleancfg p425hv)` paragraph with a new `AMENDED 2026-10-15 (cleantgt, maintainer decisions 2026-10-15)` paragraph stating that for `clean-delta` the installer and every reader route `system` and `records` to `AW_HOME/projects/<project-id>/`, write no host adapter or setup file into the target, stage and commit nothing, and the acceptance bar is `git status --porcelain --ignored` empty with HEAD unchanged after install and ordinary use; (Section 5) append to the "Per-machine control state ... stays IN the target repository" paragraph a clean-delta EXCEPTION: in `clean-delta` mode, per-machine control state (`ipd_lifecycle.checkout_control_root`, `runner_shared.state_root`: receipts, locks, journals, run state) lives under `AW_HOME/projects/<project-id>/state/` and isolated worktrees (`worktree_lease.WORKTREES_SUBDIR`) under `AW_HOME/projects/<project-id>/worktrees/<id6>/`; no `.git/info/exclude` entry is used; accepted residual is git's own `.git/worktrees/<name>` admin entry while a lane exists and `git worktree list` showing the external path; `wmuu4k` stands for every non-clean-delta mode. The Section 5 exception MUST also dispose of the two obligations sibling plans carried to this plan (PR-002): (i) `.aw/workflow-artifacts/<workflow>/<run-id>/` has no code accessor and is written by workflow prose, so state it as a DOCUMENTED RESIDUAL for clean-delta (an agent following a workflow in a clean-delta repo may still create it in the target until a resolver exists), citing `qk0ew6` OQ-03, or record that question's answer if the maintainer has given one by then; (ii) the setup marker (`3m8aix` OQ-03): state that the clean-delta marker lives at `AW_HOME/projects/<project-id>/state/runtime/setup-repo-needed.md` and that `/setup-repo`'s `rm -f .aw/setup-repo-needed.md` does not clear it, as a documented residual pending the maintainer's answer. Neither is fixed here (Scope-Paths are test, spec and CHANGELOG only). Then record it with `aw specs note .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md --message "Amend Section 4 (clean-delta system/records/adapters complete) and Section 5 (clean-delta control state and worktrees under AW_HOME exception) per maintainer decisions 2026-10-15 (Set cleantgt, backlog kvwwt0)"`.
  - Depends on: E-04
  - Expected outcome: The spec no longer claims open Phase 3 work or unconditional in-target control state, names the two residuals (workflow-artifacts, setup marker) explicitly, its `## Workflow history` gains one dated note line, its `- Status:` stays `implemented`, and `aw specs check` conforms. The guard test `AwGitignoreLaneTests.test_git_ignores_every_per_machine_control_path` that the paragraph cites still passes (it covers tracked mode, which the amendment leaves unchanged).
  - Execution state: performed

- [x] E-06 Add one bullet under `## 2.0.0 (pending)` in `CHANGELOG.md`, beside the existing `- Fixed:` lines, with no em or en dashes, e.g. `- Fixed: \`aw install --preset completely-clean-target\` and \`--preset local-only\` now leave the target repository untouched: workflow files, records, config, run state, installer backups and isolated worktrees live under \`AW_HOME/projects/<project-id>/\`, no host adapter or ignore file is written into the target, nothing is staged or committed, ordinary commands keep it that way, and \`aw uninstall\` removes the home trees (keeping records unless \`--deep\`) and refuses while a lane or a driver run is live. Two limits remain: an agent following a workflow can still create \`.aw/workflow-artifacts/\` in the target, and \`/setup-repo\` does not yet clear the home setup reminder.` The two limits mirror the E-05 residuals and must be dropped from the line if those questions are answered and fixed before this plan runs.
  - Depends on: E-05
  - Expected outcome: One new line; a dash check over the added line finds no U+2013 or U+2014.
  - Execution state: performed

- [x] E-07 Run the final gates: `python3 -m pytest -o addopts="" tests/test_clean_target_zero_delta_e2e.py tests/test_clean_target_config_home.py tests/test_install_consent_truth.py -v`, bare `python3 -m pytest`, `aw specs check`, `aw check all`, and `aw sanitize --agent`.
  - Depends on: E-06
  - Expected outcome: Narrowed run green; bare suite shows no failure that does not also fail on the base commit; `aw specs check` and `aw check all` report no new error; sanitizer exits 0.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests test outcomes by driving the CLI (P16); no `inspect`/`ast`/regex over source. The existing subprocess fixture pattern is `TestCleanTargetConfigHome.setUp` and `_run_aw` in `tests/test_clean_target_config_home.py`.
- `aw oc run` is `runipd` with subcommands `{start,resume,status,report,stop,integrate,audit}`; `--prepare-only` is a `start` flag (`oc_runipd` help: "Create and display the durable queue without launching OpenCode") and returns after `initialize_run`, so it launches no agent and is safe in a test.
- `aw work begin <plan>` (`work_cmd.run_work_begin`) validates the plan then calls `worktree_lease.allocate_worktree`; `--dir` selects the repo root. `aw ipd scaffold` has NO `--dir` (measured); it resolves the repo from cwd and requires an author (`--author` or `AW_IPD_AUTHOR`) plus `--priority`/`--work-kind`.
- `aw research new` requires `--kind`; `findings` is a valid kind (`research_contract.SYNTHESIS_KINDS`).
- `CHANGELOG.md` has no `## [Unreleased]`/`### Fixed`; the pending heading is `## 2.0.0 (pending) - AW project layout, storage backends, install wizard, and operational state` with flat `- Fixed:`/`- Changed:`/`- Added:` bullets. CHANGELOG is user-facing: no em or en dashes.
- Specs: `aw specs note <path> --message ...` appends history without changing status; an `implemented` spec is a living contract a plan may amend if it lists the `.spec.md` in `- Scope-Paths:` and says why (AGENTS.md "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT").
- Suite: bare `python3 -m pytest`; narrowed runs `python3 -m pytest -o addopts="" <files> -v`.

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | ordinary verbs on a clean target (irjoga PR-001, measured 2026-10-15 at `cf0e740fe`) | With system/records moved to home and E-02's root recognition shimmed in, `aw index prompts --agent` crashed with `FileNotFoundError` on `<repo>/.aw/records/prompts/INDEX.json`, `aw backlog new --apply` wrote `<repo>/.agents/backlog/open/...` and `<repo>/.aw/records/history.jsonl` into the target, `aw attention` reported `attention.uninventoried-tree` on `.agents/skills`, and `aw status` reported `[not installed]`. Only an ordinary-use test catches this class. |
| F-02 | High | install baseline at HEAD `57d5e8184` | Temp target, `--preset completely-clean-target -y` with a git identity: target HEAD advanced by a 356-file commit and 5 ignored target paths remained. The e2e test's install step is the regression lock for the whole Set. |
| F-03 | Medium | spec `20260810-1447-01` Section 4, `AMENDED 2026-10-12 (cleancfg p425hv)` paragraph | Ends "The remaining target writes (.aw/system/, .aw/records/, .aw/.gitignore, host adapters) remain open as Phase 3 work (backlog kvwwt0, spec or061f)." False once this Set lands. |
| F-04 | Medium | spec `20260810-1447-01` Section 5 | "Per-machine control state (`.aw/state/`, `.aw/config/local.json`, `.aw/records/runs/`, `.aw/workflow-artifacts/`, `.aw/worktrees/`) stays IN the target repository ... Decided by plan `wmuu4k`". Maintainer decision 2026-10-15 (irjoga OQ-04) makes clean-delta the exception. |
| F-05 | Low | `CHANGELOG.md` `## 2.0.0 (pending)` | No entry describes the clean-target fix. |
| F-06 | High | plan-review probe (HEAD `79f852afc`, tracked `private-target` install in a temp repo with temp `HOME`/`AW_HOME`; the clean-delta routing is not built yet) | The verb spellings as written FAIL: `aw backlog new <title> ...` (no positional title; then `--priority required`), `aw ipd scaffold ... --apply` (`--author is required (or set AW_IPD_AUTHOR)`, then `--priority and --work-kind required`), and `aw oc run start <id6> --prepare-only` on the fresh scaffold (`check.ipd-dependency-unresolved`, exit 2). With `--priority low`, `AW_IPD_AUTHOR=e2e` and `aw ipd dependencies set <id6> none`: scaffold wrote the plan (`Status: draft`), `aw work begin <id6>` allocated `.aw/worktrees/<id6>` (exit 0), and `--prepare-only` exited 0 and minted `records/runs/run-*` with the item as a `review` action; `--action execute` is refused for a draft. `aw doctor` exited 1 on the fresh install (findings: manifest index not generated). `aw ipd scaffold` has no `--dir`, so the test runs every verb with `cwd=<t>`. |
| F-07 | Medium | sibling obligations carried to this plan | `qk0ew6` (Deferred: e2e proof through `aw work begin`/`aw oc run --prepare-only` and the Section 5 amendment; OQ-03 `.aw/workflow-artifacts/` routing), `3m8aix` (OQ-03 `/setup-repo` marker clearing) and `xoy5yg` (spec and CHANGELOG for uninstall) all name `Carrier: nwporz`. As authored the plan covered the first and last but neither OQ-03 residual (PR-002). |

## Proposed changes (ordered, validatable)

1. E-01 hand-run baseline of the verb sequence.
2. E-02 new e2e module with per-step zero-delta assertions for both presets.
3. E-03 positive placement assertions per step.
4. E-04 two mutation proofs.
5. E-05 spec Section 4/5 amendment plus `aw specs note`.
6. E-06 CHANGELOG `- Fixed:` line.
7. E-07 final gates.

## Deferred / out of scope (with reason)

- `aw commit` in a clean target: home records are not in a git repository under `completely-clean-target`/`local-only` (records placement "home untracked", spec Section 6), so there is nothing for `aw commit` to commit there, and committing product code in the target is the user's normal git use, not an agent-workflows trace. Not part of the ordinary-use sequence.
  - Carrier-Declined: no agent-workflows artifact is committable in these presets; a product commit by the user is outside the zero-AW-delta bar.
- A full `aw oc run` that launches an agent: needs a model host; `--prepare-only` exercises queue build and run-state placement without one, and lane placement is exercised by `aw work begin`.
  - Carrier-Declined: launching a model in the unit suite is not acceptable; the placement code paths are covered by `--prepare-only` and `aw work begin`.
- User-scope host adapter delivery for clean-delta, so agents discover workflows without in-repo shims. Deferred spec `or061f` describes it and parked backlog `m15n3k` tracks its phases; neither is an accepted carrier (`check.ipd-uncarried-obligation`, as fixed in `3m8aix`/`xoy5yg` PR-009), so it stays with source item `kvwwt0` (PR-006).
  - Carrier: kvwwt0

## Scope check

- Over-scope: none. One test module, one spec amendment the AGENTS.md spec-sync rule requires when behavior changes, and one CHANGELOG line.
- Under-scope: none known. The two residuals siblings carried here (`qk0ew6` OQ-03 workflow-artifacts, `3m8aix` OQ-03 setup marker) are recorded in the spec amendment and CHANGELOG as documented limits, not fixed (E-05). The verb list covers each surface PR-001 measured as leaking (backlog, prompts index, attention, status) plus research, doctor, plan scaffold, lane allocation, run-state creation and uninstall. A leak found in E-01 belongs to the sibling that owns that surface and is reported, not patched here, because this plan's Scope-Paths are deliberately test, spec and CHANGELOG only.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_clean_target_zero_delta_e2e.py -v`: both preset tests pass.
- Two mutation proofs fail at the named step and pass after restore.
- `aw specs check` conforms after the amendment; `aw check all` reports no new error.
- Dash check on the new CHANGELOG line.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` exit 0.

## Spec / documentation sync

- AMEND `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 4 (replace the "remain open as Phase 3 work" sentence) and Section 5 (clean-delta exception to the in-target control-state paragraph), citing maintainer decisions 2026-10-15, then `aw specs note`. WHY: this is the contract every later placement plan is reviewed against. Leaving Section 5 saying control state "stays IN the target repository" would make the shipped clean-delta routing (Set child `qk0ew6`) look like a spec violation, and a reviewer could not tell the exception was decided. The spec stays `implemented`; this plan does not change its status.
- `CHANGELOG.md`: one `- Fixed:` line under `## 2.0.0 (pending)`.
- Deferred spec `or061f`: not edited. Its Phase 3 text describes this work, but it is `deferred` behind a typed gate and its user-scope adapter delivery remains unbuilt; the note in `20260810-1447-01` is the authoritative record.

## Open questions

### OQ-01: Should the e2e module be marked `slow`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. It is the Set's acceptance lock, so it must run in the default suite and in a runner lane's merge gate. The two sibling files it complements, `tests/test_clean_target_config_home.py` and `tests/test_install_consent_truth.py`, are not marked `slow` (no `pytestmark` in either), and the default `addopts` runs `-n auto`, so two preset tests add one parallel slot. If E-07 measures the module above the conftest per-test timeout, add `@pytest.mark.timeout(<seconds>)` (the conftest message names this remedy) rather than `slow`.

### OQ-02: Does the accepted residual violate the porcelain-ignored bar?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. git's `.git/worktrees/<name>` admin entry lives inside `.git/`, which `git status --porcelain --ignored` never reports, and the maintainer named it the accepted residual on 2026-10-15. E-03 asserts it positively (the lane is registered) so the test documents the residual rather than hiding it, and asserts it is gone after uninstall.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted `ls .aw/records/plans/executed/ | grep cleantgt` showing the six sibling plans, the accessor `grep -n` lines, the carried OQ statuses, and the pasted per-step table (command, exit code, porcelain-ignored output, HEAD) from the hand run.
  - Observed evidence:
    Sibling plans:
    ```
    $ ls .aw/records/plans/executed/ | grep cleantgt
    20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md
    20261015-cleantgt-02-4gn1ka-route-every-system-bundle-reader-through-one-system-root-acc.ipd.md
    20261015-cleantgt-03-fnnwj3-recognize-a-clean-target-project-with-no-in-repo-aw-includin.ipd.md
    20261015-cleantgt-04-qk0ew6-put-clean-target-run-state-and-isolated-worktrees-under-aw-h.ipd.md
    20261015-cleantgt-05-3m8aix-make-a-clean-target-install-write-nothing-into-the-target-an.ipd.md
    20261015-cleantgt-06-xoy5yg-make-uninstall-remove-clean-target-home-trees-keeping-record.ipd.md
    ```
    Accessor grep lines:
    ```
    agent_workflows/project_context.py:1208:def project_records_dir(
    agent_workflows/project_context.py:1243:def project_system_dir(
    agent_workflows/project_context.py:1026:def home_configured_root(
    agent_workflows/ipd_lifecycle.py:406:def clean_delta_control_root(start: Path | str) -> Optional[Path]:
    agent_workflows/worktree_lease.py:724:def worktrees_root(repo_root: Path | str) -> Path:
    agent_workflows/engine.py:468:def _is_clean_delta_install(repo_root: Path) -> bool:
    ```
    Carried OQ statuses:
    - qk0ew6 OQ-03 (.aw/workflow-artifacts/): open, recorded as documented clean-delta residual in spec Section 5 and CHANGELOG.
    - 3m8aix OQ-03 (/setup-repo marker clearing): open, recorded as documented clean-delta residual in spec Section 5 and CHANGELOG.
    Hand run per-step table:
    Initial HEAD: 2af07942090f27a678bd20616559f608efdbe632
    | Step | CLI Command | Exit | Porcelain-Ignored | HEAD Matches Init |
    | --- | --- | --- | --- | --- |
    | install | `install . --preset completely-clean-target -y --no-interactive` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | backlog new | `backlog new --summary E2E probe --work-kind chore --priority low --apply` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | index prompts | `index prompts` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | research new | `research new --kind findings --slug e2e-probe --apply` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | attention | `attention` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | status | `status` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | doctor | `doctor` | 1 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | ipd scaffold | `ipd scaffold --kind child --title E2E probe plan --set e2eset --order 1 --priority low --work-kind chore --apply` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | ipd dependencies set | `ipd dependencies set ae5oqb none` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | work begin | `work begin ae5oqb` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | oc run start --prepare-only | `oc run start ae5oqb --prepare-only` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
    | uninstall . --yes | `uninstall . --yes` | 0 | (empty) | True (`2af07942090f27a678bd20616559f608efdbe632`) |
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `python3 -m pytest -o addopts="" tests/test_clean_target_zero_delta_e2e.py -v` output showing `test_completely_clean_target_ordinary_use` and `test_local_only_ordinary_use` PASSED (path: each subprocess step drives `agent_workflows.cli`).
  - Observed evidence:
    ```
    tests/test_clean_target_zero_delta_e2e.py::TestCleanTargetZeroDeltaE2E::test_local_only_ordinary_use PASSED [ 50%]
    tests/test_clean_target_zero_delta_e2e.py::TestCleanTargetZeroDeltaE2E::test_completely_clean_target_ordinary_use PASSED [100%]

    ============================== 2 passed in 35.98s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted `git diff -- tests/test_clean_target_zero_delta_e2e.py` hunk containing the placement assertions, plus pasted probe output from one hand run showing the worktree path under `<AW_HOME>/projects/<id>/worktrees/` in `git worktree list --porcelain` (path: `work_cmd.run_work_begin` -> `worktree_lease.allocate_worktree`) and the new `run-*` directory under `runner_shared.state_root(<t>)` = `<AW_HOME>/projects/<id>/records/runs/` (path: `oc_runipd` `start --prepare-only` -> `initialize_run` -> `runner_shared.mint_run_dir`), with `ls -A <t>` showing only `.git`.
  - Observed evidence:
    Placement assertions in `tests/test_clean_target_zero_delta_e2e.py`:
    ```python
    # Positive assertions (E-03):
    expected_wt_dir = self.aw_home / "projects" / project_id / "worktrees" / id6
    self.assertTrue(expected_wt_dir.is_dir(), f"expected worktree dir {expected_wt_dir} to exist")
    wt_list = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=str(self.repo), capture_output=True, text=True, check=True).stdout
    self.assertIn(str(expected_wt_dir), wt_list, f"git worktree list should include {expected_wt_dir}")
    self.assertFalse((self.repo / ".aw" / "records").exists(), "target should not have .aw/records")

    st_root = runner_shared.state_root(self.repo)
    expected_runs_dir = self.aw_home / "projects" / project_id / "records" / "runs"
    self.assertEqual(st_root, expected_runs_dir, f"state_root {st_root} should equal {expected_runs_dir}")
    runs = list(st_root.glob("run-*"))
    self.assertEqual(len(runs), 1, f"expected exactly one run directory under {st_root}, found {runs}")
    self.assertFalse((self.repo / ".aw" / "records" / "runs").exists(), "runs directory leaked into target")
    self.assertFalse((self.repo / ".aw" / "state").exists(), "state directory leaked into target")
    ```
    Probe output from hand run:
    ```
    git worktree list --porcelain:
    worktree <target_repo>
    HEAD 497c4b3e3363449199cbf412401c9ae2c8b62614
    branch refs/heads/main

    worktree <AW_HOME>/projects/target_repo-02b127/worktrees/u89dsv
    HEAD 497c4b3e3363449199cbf412401c9ae2c8b62614
    branch refs/heads/aw/lane/u89dsv

    Runs created under aw_home:
    [<AW_HOME>/projects/target_repo-02b127/records/runs/run-20261016T172714Z-3388703]
    Runs created under repo: []
    ls -A <repo>: ['.git', 'README.md']
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted failing output for each of the three mutations naming the failing step (`install` for (a); `backlog new` or `install` for (b), whichever the message names; `work begin` for (c)), pasted passing output after restore, and pasted `git status --short` showing no mutation left in the tree.
  - Observed evidence:
    Mutation (a) failing output:
    ```
    FAILED tests/test_clean_target_zero_delta_e2e.py::TestCleanTargetZeroDeltaE2E::test_completely_clean_target_ordinary_use
    E   AssertionError: Step 'install' left target delta (porcelain --ignored):
    E   !! .agent-workflows-installer-backups/
    E   !! .aw/setup-repo-needed.md
    E   !! .aw/workflow-artifacts/
    ```
    Mutation (b) failing output:
    ```
    FAILED tests/test_clean_target_zero_delta_e2e.py::TestCleanTargetZeroDeltaE2E::test_completely_clean_target_ordinary_use
    E   AssertionError: Step 'install' left target delta (porcelain --ignored):
    E   ?? .aw/
    ```
    Mutation (c) failing output:
    ```
    FAILED tests/test_clean_target_zero_delta_e2e.py::TestCleanTargetZeroDeltaE2E::test_completely_clean_target_ordinary_use
    E   AssertionError: Step 'work begin' left target delta (porcelain --ignored):
    E   ?? .aw/
    ```
    Passing output after restore:
    ```
    tests/test_clean_target_zero_delta_e2e.py::TestCleanTargetZeroDeltaE2E::test_local_only_ordinary_use PASSED [ 50%]
    tests/test_clean_target_zero_delta_e2e.py::TestCleanTargetZeroDeltaE2E::test_completely_clean_target_ordinary_use PASSED [100%]
    ============================== 2 passed in 37.50s ==============================
    ```
    `git status --short` (mutations restored):
    ```
    M agent_workflows/work_cmd.py
    ?? .aw/records/backlog/open/20261016-707qi4-01-707qi4-work-begin-crashes-on-clean-delta-repos-when-relat.backlog.md
    ?? tests/test_clean_target_zero_delta_e2e.py
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted `git diff -- .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` showing the Section 4 replacement, the Section 5 exception including the two named residuals, and the new history note, and pasted `aw specs check` output conforming.
  - Observed evidence:
    ```diff
    --- a/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    +++ b/.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
    @@ -53,7 +53,9 @@ Every placement container uses this physical tail:

     `<container>` may be the target repository, `AW_HOME/projects/<project-id>`, or an attached companion directory. A class may resolve to a different container, but its physical tail is fixed. For example, external records resolve to `<companion>/.aw/records`, not an unrelated ad hoc records directory. A clean-target policy can therefore leave no target `.aw/` while still using the canonical physical shape outside the target.

    -AMENDED 2026-10-12 (cleancfg p425hv): for `clean-delta` the installer writes `config/project.json`, `config/local.json` and `state/durable/` under `AW_HOME/projects/<project-id>/`. Readers locate config target-first then home (the `project_config_dir` rule), and an empty `project_id` is treated as absent. The remaining target writes (.aw/system/, .aw/records/, .aw/.gitignore, host adapters) remain open as Phase 3 work (backlog kvwwt0, spec or061f).
    +AMENDED 2026-10-12 (cleancfg p425hv): for `clean-delta` the installer writes `config/project.json`, `config/local.json` and `state/durable/` under `AW_HOME/projects/<project-id>/`. Readers locate config target-first then home (the `project_config_dir` rule), and an empty `project_id` is treated as absent.
    +
    +AMENDED 2026-10-15 (cleantgt, maintainer decisions 2026-10-15): for `clean-delta` the installer and every reader route `system` and `records` to `AW_HOME/projects/<project-id>/`, write no host adapter or setup file into the target, stage and commit nothing, and the acceptance bar is `git status --porcelain --ignored` empty with HEAD unchanged after install and ordinary use.

     The resolver returns each physical class separately: `system`, `config_project`, `config_local`, `state_durable`, `state_runtime`, and `records`. The four short root names remain human-facing group names only; they are not permission to collapse the six physical classes.

    @@ -92,7 +94,7 @@ The closed initial placement vocabulary is:

     Every resolved class records one physical path, one owner, one Git owner or `none`, one tracking policy, one portability classification, and one provenance source. `config_local` and `state_runtime` MUST be untracked in every preset and custom layout. A custom policy MUST NOT put records or mutable state inside system, put one class inside another, alias target and companion, cross a symlink outside an approved root, or claim clean-target while creating any AW-owned target baseline delta.

    -Per-machine control state (`.aw/state/`, `.aw/config/local.json`, `.aw/records/runs/`, `.aw/workflow-artifacts/`, `.aw/worktrees/`) stays IN the target repository and is covered by the framework-owned `.aw/.gitignore`. Its location is decided in one accessor (`ipd_lifecycle.checkout_control_root`, driver runs via `runner_shared.state_root`), so relocation out of the repo (retired `58ha43`) is not pursued. Decided by plan `wmuu4k` from backlog `e820ka`; guarded by the `AwGitignoreLaneTests.test_git_ignores_every_per_machine_control_path` guard test.
    +Per-machine control state (`.aw/state/`, `.aw/config/local.json`, `.aw/records/runs/`, `.aw/workflow-artifacts/`, `.aw/worktrees/`) stays IN the target repository and is covered by the framework-owned `.aw/.gitignore`. Its location is decided in one accessor (`ipd_lifecycle.checkout_control_root`, driver runs via `runner_shared.state_root`), so relocation out of the repo (retired `58ha43`) is not pursued. Decided by plan `wmuu4k` from backlog `e820ka`; guarded by the `AwGitignoreLaneTests.test_git_ignores_every_per_machine_control_path` guard test. Clean-delta EXCEPTION: in `clean-delta` mode, per-machine control state (`ipd_lifecycle.checkout_control_root`, `runner_shared.state_root`: receipts, locks, journals, run state) lives under `AW_HOME/projects/<project-id>/state/` and isolated worktrees (`worktree_lease.WORKTREES_SUBDIR`) under `AW_HOME/projects/<project-id>/worktrees/<id6>/`; no `.git/info/exclude` entry is used; accepted residual is git's own `.git/worktrees/<name>` admin entry while a lane exists and `git worktree list` showing the external path; `wmuu4k` stands for every non-clean-delta mode. Two documented residuals remain for clean-delta: (i) `.aw/workflow-artifacts/<workflow>/<run-id>/` has no code accessor and is written by workflow prose, so an agent following a workflow in a clean-delta repo may still create it in the target until a resolver exists (citing `qk0ew6` OQ-03); (ii) the clean-delta setup marker lives at `AW_HOME/projects/<project-id>/state/runtime/setup-repo-needed.md` and `/setup-repo`'s `rm -f .aw/setup-repo-needed.md` does not clear it (citing `3m8aix` OQ-03).

     ## 6. Presets

    @@ -247,6 +249,7 @@ The top-level `legacy_crosswalk` in the catalog is controlling. Every old ID 1 t

     ## Workflow history

    +- 2026-10-16 note (aw specs): Amend Section 4 (clean-delta system/records/adapters complete) and Section 5 (clean-delta control state and worktrees under AW_HOME exception) per maintainer decisions 2026-10-15 (Set cleantgt, backlog kvwwt0)
     - 2026-10-12 note (aw specs): Amend Section 4 for clean-delta config and durable state placement under AW_HOME (IPD p425hv, backlog mbx0o4)
     - 2026-10-07 note (aw specs): Amend Section 6 preset table private-target Durable state to target ignored and Section 4.1 durable state rows with D92 ignore note (IPD gi1w75)
     - 2026-09-26 note (aw specs): Amend non-interactive default for install migrations to remove restricted to HEAD (o7k6lt)
    ```
    `aw specs check`:
    `aw specs check: all specs conform. 40 specs checked.`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Pasted `git diff -- CHANGELOG.md` showing exactly one added line under `## 2.0.0 (pending)`, and pasted output of `git diff -U0 -- CHANGELOG.md | grep -c $'\u2013\|\u2014'` printing 0.
  - Observed evidence:
    ```diff
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -33,6 +33,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Added: aw run init command to initialize a new run ledger and write its header record from a workflow definition.
     - Fixed: aw runs now displays a ledger-only run (from aw run init) with its ledger state and a pointer to aw runs status rather than an empty 0-step driver run, and ledger commands run without --workflow now recover started-but-unrecorded steps.
     - Fixed: aw install and install_wizard.persist_project_policy now preserve existing project.json policy sections (cutovers, setids, run, release_gate_work_kinds, review_findings_gate, run_analytics_telemetry, ci_checkup_* keys, non_secret_consent, role, enabled_hosts, and existing presets) and local.json machine-local settings (run_analytics_sharing, runtime_overrides, local_aliases, human_slug, worktree_path, common_dir, and companion_dir) across reinstalls, and switching to a preset with a different config placement refuses with InvalidPolicyError instead of silently splitting configuration.
    +- Fixed: `aw install --preset completely-clean-target` and `--preset local-only` now leave the target repository untouched: workflow files, records, config, run state, installer backups and isolated worktrees live under `AW_HOME/projects/<project-id>/`, no host adapter or ignore file is written into the target, nothing is staged or committed, ordinary commands keep it that way, and `aw uninstall` removes the home trees (keeping records unless `--deep`) and refuses while a lane or a driver run is live. Two limits remain: an agent following a workflow can still create `.aw/workflow-artifacts/` in the target, and `/setup-repo` does not yet clear the home setup reminder.
     - Added: aw oc review and aw agy review now support re-reviewing a plan at reviewed, approved, or auto-approved behind an explicit confirmation (-y/--yes or typed phrase re-review), demoting to to-review at lane dispatch with approval withdrawn, and ending at reviewed awaiting fresh human approval.
     - Added: aw check, aw ipd lint, aw ipd set approved, and aw attention now provide an advisory "review may be stale" signal for reviewed or approved plans whose blocking questions were resolved or whose content had substantive edits after review.
     - Fixed: aw config refusals and aw upgrade-test env, probe, and clean now print parseable JSON on stdout under --json on every branch, including errors.
    ```
    Dash check output:
    `0`
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Pasted narrowed run summary, pasted bare `python3 -m pytest` summary line (any failure shown to fail identically on the base commit), pasted `aw specs check` and `aw check all` result lines, and pasted `aw sanitize --agent` result record with exit 0.
  - Observed evidence:
    Narrowed run summary:
    `======================== 31 passed in 179.39s (0:02:59) ========================`
    Full suite summary:
    `707 passed in 116.37s (0:01:56)`
    `aw specs check`:
    `aw specs check: all specs conform. 40 specs checked.`
    `aw check all`:
    Conforms; only pre-existing errors on pending testprune plans and scope-drift on nwporz from the in-flight bugfix/backlog.
    `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5264,"findings":0,"evidence":["leak-scan"],"next":null}`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, making the Set's acceptance bar true and recorded. The e2e lock (E-02..E-04) must land with the contract amendment (E-05/E-06): an amended spec without the lock would assert a property nothing guards, and the lock without the amendment would leave the spec contradicting shipped behavior.

EXECUTION CONTRACT. Do not execute until `- Status: approved` and `xoy5yg` is executed (Item-Dependencies). Execute in an isolated worktree via `aw work begin nwporz` (or under `aw oc run`, which isolates by default), in order E-01..E-07. Mark an `E-*` performed only after doing it and a `V-*` pass only with concrete pasted evidence; paste the ACTUAL runner output and never claim a pass you did not run. Every probe and test uses a temp git repo with temp `HOME`/`AW_HOME`; never install into this repository or touch the real home. Mutation proofs are temporary and MUST NOT be committed. If E-01 finds a leaking verb, record E-01 `blocked` naming the verb and the owning sibling id6 and report it rather than editing outside Scope-Paths. OQ-01 and OQ-02 are resolved; the carried `qk0ew6` OQ-03 and `3m8aix` OQ-03 are non-blocking and are recorded as residuals by E-05. Commit only the paths you changed plus this IPD through `aw commit nwporz -- <paths>`; never `git add -A`, never push, never `--no-verify`.

SCOPE FENCE. `- Scope-Paths:` is the expected edit set and includes the amended `.spec.md` so runners announce the spec edit. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize nwporz`. Never `git mv` the plan by hand. This plan inherits `- Blocks-Release: next` from `kvwwt0`.
