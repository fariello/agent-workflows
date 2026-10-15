# IPD: Prove clean-target zero target delta end to end through ordinary use

- Date: 2026-10-15
- Kind: child
- Concern: Each earlier Set child proves its own slice, but the maintainer's acceptance bar (2026-10-15) is the whole lifecycle: `git -C <target> status --porcelain --ignored` empty and HEAD unchanged after install AND after ordinary use. The predecessor review (irjoga PR-001) measured that the first ordinary verb re-created a target delta (`aw backlog new --apply` wrote `.agents/backlog/` and `.aw/records/history.jsonl` into the target; `aw index prompts --agent` crashed on `<repo>/.aw/records/prompts/INDEX.json`), so a per-slice proof is not enough. Separately, spec `20260810-1447-01` Section 4 still says the target writes "remain open as Phase 3 work" and Section 5 says per-machine control state "stays IN the target repository", which contradicts the shipped clean-delta behavior once this Set lands, and `CHANGELOG.md` has no entry for it.
- Scope: Add one end-to-end subprocess test module `tests/test_clean_target_zero_delta_e2e.py` that installs each clean preset into a temp target and drives a fixed sequence of ordinary verbs (`aw backlog new --apply`, `aw index prompts`, `aw research new --apply`, `aw attention`, `aw status`, `aw doctor`, `aw ipd scaffold --apply`, `aw work begin`, `aw oc run start --prepare-only`, `aw uninstall --yes`), asserting after EVERY step that the target is porcelain-ignored empty and HEAD unchanged and that the step's artifact landed under `<AW_HOME>/projects/<project_id>/`, with a mutation proof; amend spec `20260810-1447-01` Section 4 and Section 5 and record it with `aw specs note`; add one `- Fixed:` line to `CHANGELOG.md` under `## 2.0.0 (pending)`.
- Scope-Paths: tests/test_clean_target_zero_delta_e2e.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md, CHANGELOG.md
- Item-Dependencies: executed:xoy5yg
- Status: to-review
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
- 2026-10-15 to-review (aw set): authored review-ready child of Set cleantgt (orchestrator ucr3h8) from backlog kvwwt0

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Demonstrate, with a test that stays in the suite, that on both `completely-clean-target` and `local-only` a target repository shows no agent-workflows trace (`git status --porcelain --ignored` empty, HEAD unchanged) after install, after each ordinary verb, and after uninstall; then bring the implemented physical-layout spec and the CHANGELOG into line with that behavior so the contract every later plan is reviewed against is true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [ ] E-01 At execution HEAD, confirm Set children `kfnfji`, `4gn1ka`, `fnnwj3`, `qk0ew6`, `3m8aix`, `xoy5yg` are in `.aw/records/plans/executed/`, record the accessor names they introduced, and run the E-02 verb sequence BY HAND once in a temp target (temp `HOME`/`AW_HOME`, git identity, `XDG_CONFIG_HOME`/`AW_CONFIG_DIR` unset) for `completely-clean-target`, capturing `git status --porcelain --ignored` and `git rev-parse HEAD` after each step and the exact CLI spellings that succeed (for example the `aw research new --kind` value accepted and the `aw oc run start --prepare-only` selector that resolves the scaffolded plan).
  - Depends on: none
  - Expected outcome: A pasted per-step table in V-01. Any step that leaves a target delta or fails is a defect in the owning sibling and is reported (with the owning child's id6) rather than worked around in the test.
  - Execution state: pending

### Task group 2: The end-to-end proof

- [ ] E-02 Create `tests/test_clean_target_zero_delta_e2e.py` with a `unittest.TestCase` whose `setUp` mirrors `tests/test_clean_target_config_home.py` `TestCleanTargetConfigHome.setUp` (temp target with an initial commit, temp `HOME`/`AW_HOME`, git identity in env, `AW_NO_REEXEC=1`, `PYTHONPATH` at the source tree) and a helper `_assert_zero_delta(step)` that runs `git -C <t> status --porcelain --ignored` and `git -C <t> rev-parse HEAD` and fails with the step name and the porcelain output when either differs from the pre-install baseline. One test per preset (`test_completely_clean_target_ordinary_use`, `test_local_only_ordinary_use`) drives by subprocess, asserting zero delta after each: `install . --preset <p> -y --no-interactive`; `backlog new <title> --summary ... --work-kind chore --apply`; `index prompts`; `research new --kind findings --slug e2e-probe --apply`; `attention`; `status`; `doctor`; `ipd scaffold --kind child --title ... --set e2eset --order 1 --apply`; `work begin <scaffolded id6>`; `oc run start <id6> --prepare-only`; `uninstall . --yes`. Each step's exit code is asserted as the one E-01 observed for that verb (0 for the writing verbs).
  - Depends on: E-01
  - Expected outcome: Both tests pass; a failure message names the first step that touched the target.
  - Execution state: pending

- [ ] E-03 In the same tests, assert positively that each writing step's artifact is where the stored policy says (P16: outcome, not structure), using `resolve_project_context(target_repo=..., aw_home=...).physical_classes` read AFTER install: the backlog item and the research file exist under the `records` class root; the scaffolded plan exists under `records/plans/pending/`; `aw work begin` created a worktree whose path is under `<AW_HOME>/projects/<id>/worktrees/` and which `git -C <t> worktree list --porcelain` registers (the accepted residual: git's own `.git/worktrees/<name>` admin entry, which is inside `.git` and therefore not reported by porcelain status); `--prepare-only` created its run directory under the home state root (the `runner_shared.state_root` resolution for this target) and not under `<t>`; after `uninstall . --yes` home `records/` still holds the backlog item and `git -C <t> worktree list` shows only the main worktree.
  - Depends on: E-02
  - Expected outcome: Every positive assertion passes for both presets.
  - Execution state: pending

- [ ] E-04 Mutation proof, temporary and not committed: (a) in the installed copy under test, make the clean-delta predicate from `3m8aix` (`engine._is_clean_delta_install`) return `False` and run the new module, observing failure at the `install` step; restore. (b) make the child-01 records-root accessor return `<repo>/.aw/records` unconditionally and observe failure at the `backlog new` step; restore. Re-run the module green.
  - Depends on: E-03
  - Expected outcome: Each mutation fails the e2e test at the named step; both restored runs pass.
  - Execution state: pending

### Task group 3: Contract and changelog

- [ ] E-05 Amend `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`: (Section 4) replace the sentence beginning "The remaining target writes (.aw/system/, .aw/records/, .aw/.gitignore, host adapters) remain open as Phase 3 work" in the `AMENDED 2026-10-12 (cleancfg p425hv)` paragraph with a new `AMENDED 2026-10-15 (cleantgt, maintainer decisions 2026-10-15)` paragraph stating that for `clean-delta` the installer and every reader route `system` and `records` to `AW_HOME/projects/<project-id>/`, write no host adapter or setup file into the target, stage and commit nothing, and the acceptance bar is `git status --porcelain --ignored` empty with HEAD unchanged after install and ordinary use; (Section 5) append to the "Per-machine control state ... stays IN the target repository" paragraph a clean-delta EXCEPTION: in `clean-delta` mode, per-machine control state (`ipd_lifecycle.checkout_control_root`, `runner_shared.state_root`: receipts, locks, journals, run state) lives under `AW_HOME/projects/<project-id>/state/` and isolated worktrees (`worktree_lease.WORKTREES_SUBDIR`) under `AW_HOME/projects/<project-id>/worktrees/<id6>/`; no `.git/info/exclude` entry is used; accepted residual is git's own `.git/worktrees/<name>` admin entry while a lane exists and `git worktree list` showing the external path; `wmuu4k` stands for every non-clean-delta mode. Then record it with `aw specs note .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md --message "Amend Section 4 (clean-delta system/records/adapters complete) and Section 5 (clean-delta control state and worktrees under AW_HOME exception) per maintainer decisions 2026-10-15 (Set cleantgt, backlog kvwwt0)"`.
  - Depends on: E-04
  - Expected outcome: The spec no longer claims open Phase 3 work or unconditional in-target control state, its `## Workflow history` gains one dated note line, its `- Status:` stays `implemented`, and `aw specs check` conforms.
  - Execution state: pending

- [ ] E-06 Add one bullet under `## 2.0.0 (pending)` in `CHANGELOG.md`, beside the existing `- Fixed:` lines, with no em or en dashes, e.g. `- Fixed: \`aw install --preset completely-clean-target\` and \`--preset local-only\` now leave the target repository untouched: workflow files, records, config, run state, installer backups and isolated worktrees live under \`AW_HOME/projects/<project-id>/\`, no host adapter or ignore file is written into the target, nothing is staged or committed, ordinary commands keep it that way, and \`aw uninstall\` removes the home trees (keeping records unless \`--deep\`) and refuses while a lane is live.`
  - Depends on: E-05
  - Expected outcome: One new line; a dash check over the added line finds no U+2013 or U+2014.
  - Execution state: pending

- [ ] E-07 Run the final gates: `python3 -m pytest -o addopts="" tests/test_clean_target_zero_delta_e2e.py tests/test_clean_target_config_home.py tests/test_install_consent_truth.py -v`, bare `python3 -m pytest`, `aw specs check`, `aw check all`, and `aw sanitize --agent`.
  - Depends on: E-06
  - Expected outcome: Narrowed run green; bare suite shows no failure that does not also fail on the base commit; `aw specs check` and `aw check all` report no new error; sanitizer exits 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests test outcomes by driving the CLI (P16); no `inspect`/`ast`/regex over source. The existing subprocess fixture pattern is `TestCleanTargetConfigHome.setUp` and `_run_aw` in `tests/test_clean_target_config_home.py`.
- `aw oc run` is `runipd` with subcommands `{start,resume,status,report,stop,integrate,audit}`; `--prepare-only` is a `start` flag (`oc_runipd` help: "Create and display the durable queue without launching OpenCode") and returns after `initialize_run`, so it launches no agent and is safe in a test.
- `aw work begin <plan>` (`work_cmd.run_work_begin`) validates the plan then calls `worktree_lease.allocate_worktree`; `--dir` selects the repo root.
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
- User-scope host adapter delivery for clean-delta, so agents discover workflows without in-repo shims.
  - Carrier: or061f

## Scope check

- Over-scope: none. One test module, one spec amendment the AGENTS.md spec-sync rule requires when behavior changes, and one CHANGELOG line.
- Under-scope: none known. The verb list covers each surface PR-001 measured as leaking (backlog, prompts index, attention, status) plus research, doctor, plan scaffold, lane allocation, run-state creation and uninstall. A leak found in E-01 belongs to the sibling that owns that surface and is reported, not patched here, because this plan's Scope-Paths are deliberately test, spec and CHANGELOG only.

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

- [ ] V-01 validates E-01
  - Required evidence: Pasted `ls .aw/records/plans/executed/ | grep cleantgt` showing the six sibling plans, and the pasted per-step table (command, exit code, porcelain-ignored output, HEAD) from the hand run.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted `python3 -m pytest -o addopts="" tests/test_clean_target_zero_delta_e2e.py -v` output showing `test_completely_clean_target_ordinary_use` and `test_local_only_ordinary_use` PASSED (path: each subprocess step drives `agent_workflows.cli`).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted `git diff -- tests/test_clean_target_zero_delta_e2e.py` hunk containing the placement assertions, plus pasted probe output from one hand run showing the worktree path under `<AW_HOME>/projects/<id>/worktrees/` in `git worktree list --porcelain` (path: `work_cmd.run_work_begin` -> `worktree_lease.allocate_worktree`) and the run directory under the home state root (path: `oc_runipd` `start --prepare-only` -> `initialize_run`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted failing output for each mutation naming the failing step (`install` for (a), `backlog new` for (b)), pasted passing output after restore, and pasted `git status --short` showing no mutation left in the tree.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff -- .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` showing the Section 4 replacement, the Section 5 exception and the new history note, and pasted `aw specs check` output conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Pasted `git diff -- CHANGELOG.md` showing exactly one added line under `## 2.0.0 (pending)`, and pasted output of `git diff -U0 -- CHANGELOG.md | grep -c $'\u2013\|\u2014'` printing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Pasted narrowed run summary, pasted bare `python3 -m pytest` summary line (any failure shown to fail identically on the base commit), pasted `aw specs check` and `aw check all` result lines, and pasted `aw sanitize --agent` result record with exit 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Do not execute until `- Status: approved` and `xoy5yg` is executed (Item-Dependencies). Execute in an isolated worktree via `aw work begin nwporz` (or under `aw oc run`, which isolates by default), in order E-01..E-07. Mark an `E-*` performed only after doing it and a `V-*` pass only with concrete pasted evidence; paste the ACTUAL runner output and never claim a pass you did not run. Every probe and test uses a temp git repo with temp `HOME`/`AW_HOME`; never install into this repository or touch the real home. Mutation proofs are temporary and MUST NOT be committed. If E-01 finds a leaking verb, stop and report it against the owning sibling id6 rather than editing outside Scope-Paths. Commit only the paths you changed plus this IPD through `aw commit nwporz -- <paths>`; never `git add -A`, never push, never `--no-verify`.

SCOPE FENCE. `- Scope-Paths:` is the expected edit set and includes the amended `.spec.md` so runners announce the spec edit. An out-of-scope edit is permitted only when justified at finalize with `--scope-reason <path>=<why>`; acknowledge a declared path left unmodified with `--scope-ack`.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize nwporz`. Never `git mv` the plan by hand. This plan inherits `- Blocks-Release: next` from `kvwwt0`.
