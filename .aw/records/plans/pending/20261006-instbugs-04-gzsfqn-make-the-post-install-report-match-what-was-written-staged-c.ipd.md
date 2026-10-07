# IPD: Make the post-install report match what was written, staged, committed and ignored

- Date: 2026-10-06
- Kind: child
- Concern: Defect D03 of research report `l6cbbb` and a new defect N1, both reproduced at HEAD `474b037a9` in a scratch target. D03: `aw install . --preset private-target -y --no-interactive` printed "Changes committed successfully", yet afterwards `git status --short` shows `?? .aw/config/` and `git ls-files .aw/config` is empty: `config/project.json`, the portable policy the `.aw/.gitignore` template says "SHOULD be committed", was written by `install_wizard.persist_project_policy` but never staged, because `engine.prompt_and_run_commit` stages from `result["installed"]` and the wizard's writes are not in it; nor does the "Installed or updated" listing show it. The same run also printed "Changes are STAGED but NOT committed. Review and commit" BEFORE committing under `-y`, so the log contradicts itself. N1: the same fresh install printed "Gitignore (run scratch): .aw/workflow-artifacts/ is NOT ignored (run scratch carries local paths ...; re-run `aw install` to add the framework-owned .aw/.gitignore rule)" although `git status --short --ignored` lists `!! .aw/workflow-artifacts/`; on the upgrade run the same line said "is ignored by .aw/.gitignore (correct ...)". In the install sequence `gitignore_status = check_gitignore(plan)` is computed before `create_setup_artifacts` (which reaches `_ensure_aw_gitignore`) writes the framework `.aw/.gitignore`, so on a fresh repo the advisory reports a state that the same run then fixes.
- Scope: IN: (1) every file the install writes into a TRACKED class (per the policy's git policies after Order 02) is staged together with the framework files and appears in the "Installed or updated" listing, so the suggested commit (or the `-y` auto-commit) captures the whole install; (2) the run-scratch and other gitignore advisories are computed after every ignore file the run writes; (3) the closing message states what actually happened: committed (with the commit sha) under `-y`, or staged-not-committed otherwise, never both. OUT: what is written and where (Orders 02 and 03); ignored classes are never staged (they stay ignored).
- Scope-Paths: agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/install_wizard.py, tests/test_install_report_truth.py
- Item-Dependencies: executed:pfub72
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: instbugs
- Order: 4
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: gzsfqn

## Workflow history

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 04 of Set `instbugs` after reproducing D03 and finding N1 in a scratch target at HEAD `474b037a9`.

## Goal

After a fresh `aw install`, the commit the installer makes (or suggests) contains every tracked file the install wrote, `git status --porcelain` shows nothing left over except ignored paths, and every line of the install report is true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD (after Orders 02 and 03): fresh `aw install . --preset private-target -y --no-interactive > log` in a temp git repo with `AW_NO_REEXEC=1`; record `git status --short`, `git ls-files .aw/config`, and the log lines containing "Gitignore (run scratch)", "STAGED", and "committed".
  - Depends on: none
  - Expected outcome: pasted evidence of `?? .aw/config/`, the false advisory, and the contradictory messages. STOP and report any part already fixed, and narrow the plan to what remains.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 Make the wizard's writes visible to staging: have `persist_project_policy` return (or the install path collect) the repo-relative paths it wrote, filter them to classes whose git policy is `target-git` (today `config/project.json`), stage them with the same mechanism `install_all` uses, and append them to `result["installed"]` so both the listing and `prompt_and_run_commit` include them. Never stage a path in an ignored class even if `git check-ignore` would allow it.
  - Depends on: E-01
  - Expected outcome: after a fresh install, `git ls-files .aw/config` lists `.aw/config/project.json` and the listing shows it; `.aw/config/local.json` and `.aw/state/` remain untracked and ignored.
  - Execution state: pending

- [ ] E-03 Move the `check_gitignore(plan)` evaluation (and any sibling advisory that reads ignore state) to after the last step that writes an ignore file in this run, in both the single-repo and batch install paths, so the advisory reflects the final state.
  - Depends on: E-02
  - Expected outcome: a fresh install prints "Gitignore (run scratch): .aw/workflow-artifacts/ is ignored by .aw/.gitignore (correct ...)", matching `git check-ignore`.
  - Execution state: pending

- [ ] E-04 Make the closing message truthful: print "Changes are STAGED but NOT committed" only when the run ends with staged, uncommitted changes; under `-y` (auto-commit) print the commit line with its short sha instead; when the commit is declined print the staged message and the suggested command, as today.
  - Depends on: E-03
  - Expected outcome: a `-y` run's log contains exactly one of the two messages, the committed one, with a sha that `git log -1 --format=%h` confirms.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_install_report_truth.py` driving a real install into a temp git repo (non-Python: `package.json` only): (a) after `-y`, `git status --porcelain` is empty and `git ls-files .aw/config` contains `project.json` but not `local.json`; (b) the captured output's run-scratch line agrees with `git check-ignore -q .aw/workflow-artifacts/` (both ignored); (c) the `-y` output contains the committed line with the HEAD sha and not the staged line; a non-interactive run that declines the commit (or `--no-commit` equivalent if one exists) contains the staged line and not the committed line. Prove (a) can fail by dropping the E-02 staging and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The install never pushes and only commits under `-y` or on consent (`engine.prompt_and_run_commit` docstring: "auto under --yes; prompt otherwise; on decline it prints how to commit").
- The `.aw/.gitignore` template states `config/project.json` "is portable policy and SHOULD be committed", which is the authority for staging it.
- Canonical install step order is recorded at the call site ("Canonical step order (D83)"); moving the advisory must keep that order for writers.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `project.json` is left untracked after a committed install. | scratch: `git status --short` -> `?? .aw/config/`; `git ls-files .aw/config` empty; log "Changes committed successfully." |
| F-02 | The log says both staged-not-committed and committed. | scratch log: "Changes are STAGED but NOT committed. Review and commit, e.g.:" then later "Changes committed successfully." |
| F-03 | The run-scratch advisory is computed before the ignore file exists. | install sequence: `gitignore_status = check_gitignore(plan)` precedes `artifacts = create_setup_artifacts(repo_root, use_git, dry_run=dry_run)`; fresh log "is NOT ignored"; upgrade log "is ignored by .aw/.gitignore (correct ...)"; `git status --ignored` -> `!! .aw/workflow-artifacts/` |

## Proposed changes (ordered, validatable)

1. Stage and list tracked-class wizard writes (E-02).
2. Compute advisories last (E-03).
3. Truthful closing message (E-04).
4. Tests (E-05).

## Deferred / out of scope (with reason)

- WHERE STATE IS WRITTEN AND ITS GIT POLICY.
  - Carrier: pfub72

## Scope check

- Over-scope: none.
- Under-scope: none known; E-01 narrows the plan if a part was fixed in the meantime.

## Required tests / validation

- `tests/test_install_report_truth.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- N/A: no spec states the install report text; the behavior now matches the existing `prompt_and_run_commit` docstring.

## Open questions

### OQ-01: Should the installer stage `config/project.json` even when the user declines the commit?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: yes, exactly as it stages the framework files today. The decline path prints "Changes are STAGED but NOT committed"; a staged set missing one tracked file makes that suggested commit incomplete, which is the defect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit `git status --short`, `git ls-files .aw/config`, and the three log lines, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE a post-edit fresh `-y` install's `git status --porcelain` (empty), `git ls-files .aw/config` (project.json only), `git status --short --ignored | grep '^!!'` (local.json and state still ignored), and the listing line for `project.json`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the fresh install's run-scratch line and `git check-ignore -v .aw/workflow-artifacts/README.md`, agreeing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE `grep -c "STAGED but NOT committed"` (0) and the committed line from a `-y` log, plus `git log -1 --format=%h` matching its sha.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: all three fixes are the same surface (the install's closing report and the staged set it describes); they share one test fixture.

EXECUTION CONTRACT. Execute after Order 03 (`pfub72`) is executed. Execute E-items in order. Commit only files changed for this plan through `aw commit gzsfqn -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed gzsfqn`.
