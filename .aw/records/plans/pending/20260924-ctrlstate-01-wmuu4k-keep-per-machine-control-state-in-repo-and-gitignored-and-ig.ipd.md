# IPD: Keep per-machine control state in-repo and gitignored, and ignore the lane worktrees root in managed repos

- Date: 2026-09-24
- Kind: child
- Concern: Backlog `e820ka` asks WHETHER to relocate per-machine control state out of the repository now that the state-fork defect (`dh0uno`) is closed. Re-measured at HEAD `cfc7f5c1`: the fork is closed by `ipd_lifecycle.checkout_control_root` (one in-repo root keyed on `git rev-parse --git-common-dir`), so LOCATION causes no live failure and relocation is hygiene only. The decision is therefore KEEP IN-REPO, GITIGNORED. But the inventory found ONE remaining concrete harm: the lane worktrees root `.aw/worktrees/` (`worktree_lease.WORKTREES_SUBDIR`, plus owner records under `worktree_lease.OWNERS_SUBDIR`) is ignored in THIS repo only by its hand-written root `.gitignore` (".aw/worktrees/"), and NOT by the framework-owned `engine._AW_GITIGNORE_TEMPLATE` nor the `engine._ensure_aw_gitignore` back-fill. Probe in a fresh `git init` repo after `_ensure_aw_gitignore`: `.aw/state/x`, `.aw/config/local.json`, `.aw/records/runs/x`, `.aw/workflow-artifacts/x` are all ignored, while a real `git worktree add .aw/worktrees/abc123` plus `.aw/worktrees/.owners/abc123.json` shows `?? .aw/worktrees/.owners/abc123.json` and `?? .aw/worktrees/abc123/` in `git status --porcelain`. In a managed repo a driver run therefore offers every lane checkout (as an embedded gitlink) and every owner record to `git add -A`, contradicting the module's own comment "Inside the gitignored worktrees root, so it is never committed".
- Scope: IN: (a) add the anchored `/worktrees/` pattern to `engine._AW_GITIGNORE_TEMPLATE` and to the `engine._ensure_aw_gitignore` back-fill; (b) add a `/worktrees/` row to `tests/test_installer.py` `AwGitignoreLaneTests.LANES`; (c) add an end-to-end guard test asserting real `git check-ignore` ignores every per-machine control path in a freshly installed repo; (d) record the keep-in-repo decision in spec `20260810-1447-01` Section 5 and resolve it as OQ-01. OUT: any XDG relocation, migration path, Windows fallback (moot under the decision); the root `.gitignore` of this repo (already correct); non-repository records backends.
- Scope-Paths: agent_workflows/engine.py, tests/test_installer.py, .aw/.gitignore, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- Set: ctrlstate
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: wmuu4k
- From-Backlog: e820ka

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog e820ka; re-measured with `git check-ignore` in a fresh repo after `_ensure_aw_gitignore` that every control path is ignored EXCEPT `.aw/worktrees/`, which a real `git worktree add` shows as untracked.

## Goal

Close the backlog decision with evidence (keep per-machine control state in-repo, gitignored, behind the single accessor `ipd_lifecycle.checkout_control_root`), fix the one remaining harm (lane worktrees root not ignored in managed repos), and pin every control path's ignored status with a guard test that fails if any lane is dropped.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: guard tests first (must fail before the fix)

- [ ] E-01 Add a row to `tests/test_installer.py` `AwGitignoreLaneTests.LANES` for the lane worktrees root: pattern `/worktrees/`, anchored `True`, a pre-lane back-fill body equal to the current template minus that line (e.g. the body ending with `/workflow-artifacts/`), and a `why` naming `worktree_lease.WORKTREES_SUBDIR` and the owner records.
  - Depends on: none
  - Expected outcome: `test_every_lane_is_present_anchored_backfilled_and_idempotent` fails before E-03 because the template carries 0 pattern lines for this lane.
  - Execution state: pending
- [ ] E-02 Add an end-to-end test (new method in `AwGitignoreLaneTests`, e.g. `test_git_ignores_every_per_machine_control_path`) that runs `init_repo`, `INS._ensure_aw_gitignore(root)`, creates one file under each of `.aw/state/`, `.aw/config/local.json`, `.aw/records/runs/<id>/`, `.aw/workflow-artifacts/<wf>/`, `.aw/worktrees/<lane>/`, `.aw/worktrees/.owners/<lane>.json`, and asserts `git check-ignore -q` returns 0 for each, listing all misses in one failure message. Also assert `.aw/config/project.json` is NOT ignored (portable, tracked), so the test cannot pass via an over-broad pattern.
  - Depends on: none
  - Expected outcome: fails before E-03 naming exactly the two `.aw/worktrees/` paths.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 In `agent_workflows/engine.py`, add an anchored `/worktrees/` line with a short comment (per-lane git worktrees and their owner records, `worktree_lease.WORKTREES_SUBDIR`; anchored for the `/inbox/` reason) to `_AW_GITIGNORE_TEMPLATE`, and add `"/worktrees/"` to the line-anchored back-fill loop in `_ensure_aw_gitignore` (alongside the `"/workflow-artifacts/"` loop). Then regenerate this repo's `.aw/.gitignore` by running `python3 -c "from pathlib import Path; from agent_workflows import engine as E; E._ensure_aw_gitignore(Path('.'))"` so the tracked copy keeps matching the template.
  - Depends on: E-01, E-02
  - Expected outcome: both new tests pass; `.aw/.gitignore` gains one `/worktrees/` line.
  - Execution state: pending

### Task group 3: record the decision

- [ ] E-04 Append to spec `20260810-1447-01` Section 5 ("Placement and Git policy") a short paragraph: per-machine control state (`.aw/state/`, `.aw/config/local.json`, `.aw/records/runs/`, `.aw/workflow-artifacts/`, `.aw/worktrees/`) stays IN the target repository and is covered by the framework-owned `.aw/.gitignore`; its location is decided in one accessor (`ipd_lifecycle.checkout_control_root`, driver runs via `runner_shared.state_root`), so relocation out of the repo (retired `58ha43`) is not pursued; decided by plan `wmuu4k` from backlog `e820ka`; guarded by the E-02 test.
  - Depends on: E-03
  - Expected outcome: the spec names all five paths and the guard test.
  - Execution state: pending
- [ ] E-05 Run the bare suite `python3 -m pytest`.
  - Depends on: E-03, E-04
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The framework-owned `.aw/.gitignore` has ONE contract written in TWO places (template for fresh installs, back-fill list for installed repos); `AwGitignoreLaneTests` exists to force a lane into both ("a lane must be added to BOTH").
- Top-level `.aw/`-relative directory patterns are ANCHORED (`/inbox/`, `/state/`, `/workflow-artifacts/`) because a bare name matches at any depth (measured `/inbox/` incident).
- `check_engine` already treats `.aw/state/` and `.aw/worktrees/` as "gitignored RUNTIME scratch", so the fix makes that assumption true in managed repos.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Inventory of per-machine control state and its ignore coverage (measured at HEAD `cfc7f5c1`, fresh repo after `engine._ensure_aw_gitignore`, plus this repo):

| Path | Writer | Ignored in managed repo | Ignored here |
|---|---|---|---|
| `.aw/state/` (receipts, finalize lock, journals, install state) | `ipd_lifecycle.receipt_dir`, `finalize_lock_path`, `finalize_journal_path` | yes (`.aw/.gitignore` "/state/") | yes |
| `.aw/config/local.json` | config layer | yes ("/config/local.json") | yes |
| `.aw/records/runs/<run-id>/` | `runner_shared.state_root` | yes ("records/runs/") | yes |
| `.aw/workflow-artifacts/` | workflow run scratch | yes ("/workflow-artifacts/") | yes |
| `.aw/worktrees/<lane>/`, `.aw/worktrees/.owners/` | `worktree_lease` (`WORKTREES_SUBDIR`, `OWNERS_SUBDIR`) | NO: `git status` shows `?? .aw/worktrees/abc123/` | yes, root `.gitignore` only |
| `.aw/inbox/`, `records/*/untracked/`, `records/history.jsonl` | human drop / sidecars | yes | yes |

- F-1: the fork defect was RESOLUTION, not LOCATION, and is closed: `ipd_lifecycle.checkout_control_root` docstring "the MAIN worktree's `.aw`, derived from `git rev-parse --git-common-dir`". No concrete harm from in-repo location remains while each path is ignored.
- F-2: the only live harm is the worktrees root in managed repos (table row 5). This repo masks it because its root `.gitignore` carries ".aw/worktrees/"; `diff` of the rendered template against this repo's `.aw/.gitignore` is empty, confirming no `/worktrees/` in the framework file.
- F-3: backlog claim "Every worktree of a checkout now resolves ONE in-repo, gitignored control root" is TRUE for `.aw/state/`; the implied "all control state is gitignored" is FALSE for managed repos (F-2).

## Proposed changes (ordered, validatable)

1. Guard tests that fail today (E-01, E-02).
2. Template + back-fill `/worktrees/`, regenerate `.aw/.gitignore` (E-03).
3. Record the decision in spec Section 5 (E-04).
4. Bare suite (E-05).

## Deferred / out of scope (with reason)

- XDG relocation, migration of existing receipts, Windows/XDG-absent fallback, and moving the driver run root (backlog `e820ka` questions 2 to 4): moot under the keep-in-repo decision; revisitable in one function if a future need appears.
  - Carrier-Declined: decided against by OQ-01; no successor work exists to carry.
- Ignore coverage for non-repository records backends (companion/home), where `runner_shared.state_root` follows the records root outside the target: not a target-repo tracking hazard and not measured here.
  - Carrier-Declined: no observed harm; companion ignore policy is owned by spec `20260810-1447-01` Section 5 `companion-untracked`.

## Scope check

- Over-scope: none.
- Under-scope: none; this repo's root `.gitignore` already covers `.aw/worktrees/` and is left untouched.

## Required tests / validation

- `tests/test_installer.py::AwGitignoreLaneTests` new row and new end-to-end test, shown failing before E-03 and passing after.
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

- Amend spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` Section 5 (declared in `- Scope-Paths:`). WHY: that section owns the `target-ignored` placement policy and says `config_local` and `state_runtime` MUST be untracked; it is the natural home for the decision that per-machine control state stays target-ignored rather than relocated, and for naming the worktrees root, which it currently omits. The edit adds a policy statement and does not change any existing rule.

## Open questions

### OQ-01: Relocate per-machine control state out of the repository?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Resolution or deferral rationale: NO; keep in-repo and gitignored. Evidence: the `dh0uno` fork is closed by `ipd_lifecycle.checkout_control_root` (resolution fix, not location); every control path except `.aw/worktrees/` is already ignored in a freshly installed repo (Findings table), and that one gap is fixed here by a gitignore line rather than a relocation; relocation would add a migration and a Windows/XDG fallback for hygiene only. Because location is decided in one accessor, a later relocation stays a contained change. A maintainer may reverse this at review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: BEFORE E-03, paste `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_every_lane_is_present_anchored_backfilled_and_idempotent` showing `1 failed` with a message naming the lane worktrees row and "carries 0 pattern line(s)"; AFTER E-03 the same command shows `1 passed`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: BEFORE E-03, paste `python3 -m pytest -o addopts="" -q tests/test_installer.py -k test_git_ignores_every_per_machine_control_path` showing `1 failed` whose message names `.aw/worktrees/` paths and no other; AFTER E-03 `1 passed`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `git diff -- .aw/.gitignore agent_workflows/engine.py` showing one added `/worktrees/` template line, one back-fill entry, and one added `/worktrees/` line in `.aw/.gitignore`; paste `diff <(python3 -c "from agent_workflows import engine as E; print(E._AW_GITIGNORE_TEMPLATE, end='')") .aw/.gitignore && echo SAME` printing `SAME`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `grep -n "worktrees\|wmuu4k\|e820ka" .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` showing the new Section 5 paragraph naming all five paths, `checkout_control_root`, and the guard test.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the final summary line of bare `python3 -m pytest` showing `N passed` and 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`- Status: approved`). Commit through `aw commit wmuu4k -- <Scope-Paths>` only, never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted observed evidence.
