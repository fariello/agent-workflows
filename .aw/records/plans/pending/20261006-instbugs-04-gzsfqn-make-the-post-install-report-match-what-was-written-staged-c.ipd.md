# IPD: Make the post-install report match what was written, staged, committed and ignored

- Date: 2026-10-06
- Kind: child
- Concern: Defect D03 of research report `l6cbbb` and a new defect N1, both reproduced at HEAD `474b037a9` and re-reproduced at review HEAD `dcffc9691` in a package.json-only scratch target. D03: `aw install . --preset private-target -y --no-interactive` printed "Changes committed successfully", yet afterwards `git status --short` shows `?? .aw/config/` and `git ls-files .aw/config` is empty: `config/project.json`, the portable policy the `.aw/.gitignore` template says "SHOULD be committed", was written by `install_wizard.persist_project_policy` (called from `cli._run_install` BEFORE `cli._install_one`) but never staged, because `engine.prompt_and_run_commit` builds its path list from `result["installed"]`, `pruned`, `agents_status`, `artifacts` and the ignore statuses, and the wizard's writes are in none of them; nor does the "Installed or updated" listing show it. The same run also printed "Git: staging changes (no commit)" and "Changes are STAGED but NOT committed. Review and commit" (both from `engine.print_summary`, which runs before the commit offer) and then "Changes committed successfully", so the log contradicts itself. N1: the same fresh install printed "Gitignore (run scratch): .aw/workflow-artifacts/ is NOT ignored (... re-run `aw install` to add the framework-owned .aw/.gitignore rule)" although `git check-ignore -v` attributes `.aw/workflow-artifacts/README.md` to `.aw/.gitignore:75:/workflow-artifacts/`. In `engine.install_into_repo`, `gitignore_status = check_gitignore(plan)` is computed before `create_setup_artifacts` (which reaches `_ensure_aw_gitignore`) writes the framework `.aw/.gitignore`, so on a fresh repo the advisory reports a state that the same run then fixes; on an upgrade the same line correctly says "is ignored by .aw/.gitignore".
- Scope: IN: (1) every file the install writes into a TRACKED class (per the policy's git policies after Order 02) is staged together with the framework files and appears in the "Installed or updated" listing, so the suggested commit (or the `-y` auto-commit) captures the whole install; (2) the run-scratch and other gitignore advisories are computed after every ignore file the run writes; (3) the closing report states what actually happened: the summary describes the staged set without claiming a final outcome, and exactly one closing line follows the commit offer: committed (with the commit sha), staged-not-committed with the command to run, or commit failed. OUT: what is written and where (Orders 02 and 03); ignored classes are never staged (they stay ignored); the separate listing of the gitignored `.aw/workflow-artifacts/README.md` as `[added]` (see Deferred).
- Scope-Paths: agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/install_wizard.py, tests/test_install_report_truth.py
- Item-Dependencies: executed:pfub72
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: instbugs
- Order: 4
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: gzsfqn

## Workflow history
- 2026-10-07 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Reviewed at lane HEAD `dcffc9691`; plan committed and byte-identical to the lane input, so no pre-review snapshot. Re-reproduced D03 and N1 with a scratch `-y` install (F-04), and measured that a non-interactive run without `-y` aborts at `cli._confirm_install` before writing anything and that an upgrade over a committed install leaves an empty `git status` while still printing the STAGED line (F-05, F-06). Fixed: the wizard write site is `cli._run_install`, outside `install_into_repo`, and `_install_one` is shared with `aw install all` and `aw setup`, so the staging handoff is specified (PR-001); E-05(c)'s decline case was unreachable non-interactively, rewritten to drive `engine.prompt_and_run_commit` directly (PR-002); E-04 left "Git: staging changes (no commit)" and the stale STAGED line on a no-change upgrade, now covered (PR-003); `sync_cutovers_on_install` rewrites `project.json` on upgrade too, so upgrade staging is covered by E-02 and tested (PR-004); E-03's "batch path" premise corrected (one shared core) (PR-005); OQ-01 premise corrected (no decline path through the confirm gate) (PR-006); `- Blocks-Release: next` (PR-007); gate gains resolved-OQ statement, honesty rule, scope fence, temp HOME and conditional finalize ownership (PR-008).
- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 04 of Set `instbugs` after reproducing D03 and finding N1 in a scratch target at HEAD `474b037a9`.

## Goal

After a fresh `aw install`, the commit the installer makes (or suggests) contains every tracked file the install wrote, `git status --porcelain` shows nothing left over except ignored paths, and every line of the install report is true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD (after Orders 02 and 03): fresh `aw install . --preset private-target -y --no-interactive > log 2>&1` in a temp git repo containing only a committed `package.json`, with `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir and a git identity in the environment; record `git status --short`, `git ls-files .aw/config`, `git check-ignore -v .aw/workflow-artifacts/README.md`, and the log lines containing "Gitignore (run scratch)", "Git: staging", "STAGED", and "committed". Then commit any leftover, re-run the same install (upgrade) and record `git status --short` and the same log lines.
  - Depends on: none
  - Expected outcome: pasted evidence of `?? .aw/config/`, the false advisory, and the contradictory messages, with the HEAD sha. STOP and report any part already fixed, and narrow the plan to what remains.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Make the wizard's writes visible to staging. The writer is `install_wizard.persist_project_policy`, called from `cli._run_install` before `cli._install_one`; `config.sync_cutovers_on_install` (called inside it, and again inside `engine.install_into_repo`) may rewrite `project.json` on every run. Implement it as one helper in `engine` (e.g. `stage_tracked_policy_files(repo_root, use_git, installed)`), called inside `engine.install_into_repo` after `sync_cutovers_on_install`, so `aw install`, `aw install all` and `aw setup` all get it from the one shared core: for each wizard-written path (today `.aw/config/project.json`) whose class git policy in the stored `project.json` is `target-git` and which `git status --porcelain -- <path>` reports as new or modified, stage it through `_stage_installed_file` and append `"<path> [install]"` or `"<path> [overwrite]"` to `installed`, so both the listing and `prompt_and_run_commit` include it. Never stage a path whose class policy is `ignored`, nor any path `git check-ignore` reports ignored. Have `persist_project_policy` return (in its dict, under a new key) the repo-relative paths it wrote, so the helper's path list is not a second hard-coded copy.
  - Depends on: E-01
  - Expected outcome: after a fresh `-y` install, `git ls-files .aw/config` lists `.aw/config/project.json` and the listing shows it; `.aw/config/local.json` and `.aw/state/` remain untracked and ignored; an upgrade whose cutover sync changes `project.json` stages and commits it too.
  - Execution state: pending

- [ ] E-03 Move the `check_gitignore(plan)` evaluation in `engine.install_into_repo` (the one shared core reached by `engine.run`, `cli._install_one`, `aw install all` and `aw setup`) to after the last step in that function that writes an ignore file (`create_setup_artifacts` and anything after it that can append to `.aw/.gitignore`), keeping the writer order recorded at "Canonical step order (D83)" unchanged. Check whether `backups_ignore_status`/`untracked_ignore_status` read ignore state rather than report their own write; move any that do the same way.
  - Depends on: E-02
  - Expected outcome: a fresh install prints "Gitignore (run scratch): .aw/workflow-artifacts/ is ignored by .aw/.gitignore (correct ...)", matching `git check-ignore`.
  - Execution state: pending

- [ ] E-04 Make the closing report truthful. In `engine.print_summary`, replace "Git: staging changes (no commit)" with a neutral statement of fact (e.g. "Git: changes staged; commit offered below") and remove the "Changes are STAGED but NOT committed" block from the summary. In `engine.prompt_and_run_commit`, emit exactly one closing line on every path where the run changed something: on a successful commit, "Changes committed: <short sha>" read from `git rev-parse --short HEAD`; on a failed commit, the existing error plus the staged-not-committed line; on decline or non-interactive without `-y`, the staged-not-committed line plus the existing manual command; when its filtered set is empty (nothing changed), no staged claim at all. Both `engine.run` and `cli._install_one` call these two functions in the same order, so one change covers every entry point.
  - Depends on: E-03
  - Expected outcome: a `-y` fresh run's log contains the committed line with a sha `git log -1 --format=%h` confirms and no "STAGED but NOT committed"; a no-change upgrade's log contains neither.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_install_report_truth.py` (mark `slow` like `tests/test_installer.py`, since it runs real installs) driving `aw install . --preset private-target -y --no-interactive` in a subprocess into a temp git repo (non-Python: committed `package.json` only; `AW_NO_REEXEC=1`, temp `HOME`, git identity in env): (a) after `-y`, `git status --porcelain` is empty and `git ls-files .aw/config` contains `project.json` but not `local.json`; (b) the captured output's run-scratch line says "is ignored" and agrees with `git check-ignore -q .aw/workflow-artifacts/README.md` (exit 0); (c) the `-y` output contains the committed line with the HEAD short sha and does not contain "STAGED but NOT committed"; (d) a second `-y` install leaves `git status --porcelain` empty and its output contains neither the staged line nor a false committed line when nothing changed; (e) the decline path, which a non-interactive CLI run cannot reach (`cli._confirm_install` aborts first without `-y`): build an `InstallPlan` with `yes=False` for a temp repo with one staged change, call `engine.prompt_and_run_commit` under a non-interactive stdout, and assert the output contains the staged-not-committed line and the manual command and not the committed line. Prove (a) can fail by dropping the E-02 staging call and pasting the failure, then revert.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The install never pushes and only commits under `-y` or on consent (`cli._install_one` comment: "Offer to commit (auto under --yes; prompt otherwise; on decline it prints how to commit").
- The `.aw/.gitignore` template comment in `engine` states `project.json` "is portable policy and SHOULD be committed", which is the authority for staging it.
- Canonical install step order is recorded at the call site ("Canonical step order (D83)"); moving the advisory must keep that order for writers.
- `engine.prompt_and_run_commit` already filters its path list through `git status --porcelain` ("DROP PATHS GIT SEES NO CHANGE IN"); new entries ride that filter.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `project.json` is left untracked after a committed install. | scratch: `git status --short` -> `?? .aw/config/`; `git ls-files .aw/config` empty; log "Changes committed successfully." |
| F-02 | The log says both staged-not-committed and committed. | scratch log: "Git: staging changes (no commit)", "Changes are STAGED but NOT committed. Review and commit, e.g.:" then later "Changes committed successfully." |
| F-03 | The run-scratch advisory is computed before the ignore file exists. | `engine.install_into_repo`: `gitignore_status = check_gitignore(plan)` precedes `artifacts = create_setup_artifacts(repo_root, use_git, dry_run=dry_run)`; fresh log "is NOT ignored"; upgrade log "is ignored by .aw/.gitignore (correct ...)" |
| F-04 | (review) All three reproduce at lane HEAD `dcffc9691`. | scratch `-y` install: `?? .aw/config/`, `git ls-files .aw/config` empty, `git check-ignore -v` -> `.aw/.gitignore:75:/workflow-artifacts/`, log lines "is NOT ignored", "STAGED but NOT committed", "Changes committed successfully." |
| F-05 | (review) A non-interactive run without `-y` writes nothing. | same install without `-y`: "aborted; nothing changed.", empty index and status; `cli._confirm_install` returns False when not interactive |
| F-06 | (review) A no-change upgrade still prints the STAGED line. | upgrade over a committed install: `git status --short` empty, log still "Changes are STAGED but NOT committed"; `print_summary` gates it on `installed or pruned`, and the manifest is appended as `[overwrite]` every run |
| F-07 | (review) The wizard write is outside the shared core. | `cli._run_install` calls `persist_project_policy(...)` then `_install_one(...)`; `_install_one` is also called by `cli._install_all` and by `aw setup`, and calls `engine.install_into_repo`, `engine.print_summary`, `engine.prompt_and_run_commit` |
| F-08 | (review) The gitignored run-scratch README is listed as added. | log "[added    ] .aw/workflow-artifacts/README.md"; `git ls-files .aw/workflow-artifacts` empty; `ensure_workflow_artifacts_readme` "never staged: this README documents an UNTRACKED tree" |

## Proposed changes (ordered, validatable)

1. Stage and list tracked-class wizard writes inside the shared core (E-02).
2. Compute advisories last (E-03).
3. Truthful closing report, one closing line (E-04).
4. Tests (E-05).

## Deferred / out of scope (with reason)

- WHERE STATE IS WRITTEN AND ITS GIT POLICY.
  - Carrier: pfub72
- The "Installed or updated" listing marks the gitignored `.aw/workflow-artifacts/README.md` as `[added]` (F-08). It is not staged, not committed and not left dirty, so the commit and status are correct; only its listing tag misleads. It is a listing-format question shared by every ignored scaffold file and does not affect D03/N1.
  - Carrier-Declined: not owed; the review records it as an observation only, and the file's handling is correct by design (`ensure_workflow_artifacts_readme`).

## Scope check

- Over-scope: none.
- Under-scope: none known; E-01 narrows the plan if a part was fixed in the meantime.

## Required tests / validation

- `tests/test_install_report_truth.py` (E-05) with the mutation proof; run narrowed with `python3 -m pytest -o addopts="" -n auto tests/test_install_report_truth.py` since it is `slow`.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A: no spec states the install report text (searched `.aw/records/specs` for "STAGED but NOT committed", "sync via installer", `prompt_and_run_commit`: no hits); the behavior now matches the existing `cli._install_one` comment.

## Open questions

### OQ-01: Should the installer stage `config/project.json` even when the user declines the commit?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: yes, exactly as it stages the framework files today. On an interactive run the user can decline the commit prompt in `prompt_and_run_commit` (a non-interactive run without `-y` never reaches it: `cli._confirm_install` aborts first, F-05). That decline prints "Changes are STAGED but NOT committed" with a manual command; a staged set missing one tracked file makes that suggested commit incomplete, which is the defect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit fresh and upgrade `git status --short`, `git ls-files .aw/config`, `git check-ignore -v` line, and the log lines, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE a post-edit fresh `-y` install's `git status --porcelain` (empty), `git ls-files .aw/config` (project.json only), `git status --short --ignored | grep '^!!'` (local.json and state still ignored), and the listing line for `project.json`; plus an upgrade after hand-deleting the `cutovers` key from the committed `project.json`, showing `git status --porcelain` empty afterwards and `git show --stat HEAD` including `project.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the fresh install's run-scratch line and `git check-ignore -v .aw/workflow-artifacts/README.md`, agreeing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE from a fresh `-y` log `grep -c "STAGED but NOT committed"` (0), the "Git:" line, and the committed line, plus `git log -1 --format=%h` matching its sha; and from a no-change upgrade log the same grep (0) and the absence of a committed line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: all three fixes are the same surface (the install's closing report and the staged set it describes); they share one test fixture.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute after Order 03 (`pfub72`) is executed; execute E-items in order. Commit only files changed for this plan through `aw commit gzsfqn -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. Run every real install with `AW_NO_REEXEC=1`, `HOME` pointed at a temp dir, and a git identity in the environment. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize gzsfqn`, never by a hand `git mv`.
