# IPD: Make the install consent plan show real paths and the tracking policy the ignore rules actually apply

- Date: 2026-10-06
- Kind: child
- Concern: Defects D04 and D15 of research report `l6cbbb`, both present at HEAD `474b037a9`. D04: `install_wizard.render_pre_write_plan` first resolves the correct physical paths (`project_context.resolve_project_context(...).physical_classes`, which maps `config_project` to the `project.json` path, `state_durable` to `<state_root>/durable`, `state_runtime` to `<state_root>/runtime`), then its loop over `ROOT_CLASSES` OVERWRITES every entry with `f"{repo_formatted}/.aw/{cls}"` (and the home/companion branches with `.../.aw/{cls}`), so the consent surface lists `.aw/config_project`, `.aw/config_local`, `.aw/state_durable`, `.aw/state_runtime`, none of which is ever created. D15: the `private-target` preset (`install_wizard.get_preset_defaults` and `project_schema.PRESET_PLACEMENTS`) declares `state_durable` as `target-tracked` / `target-git`, and the consent text says "Target Delta: .aw/system/, .aw/config/project.json, .aw/state/durable created/updated.", while the shipped `.aw/.gitignore` template ignores `/state/` as D92 leak containment. A fresh scratch install writes exactly this contradiction into `.aw/config/project.json` (`"state_durable": "target-git"`), and the downstream user committed `state/durable/install.json` because of it.
- Scope: IN: (1) the consent plan prints the physical path each class resolves to, in every placement branch, with a file path where the class is a file; (2) every target-placement preset declares `state_durable` as `target-ignored` / `ignored`, matching the ignore rule, in both preset tables; (3) the "Target Delta" line lists what is written AND whether it is tracked, consistent with the tables; (4) an upgrade over an existing `project.json` that still declares `state_durable: target-git` normalizes it to `ignored` and says so in the install output. OUT: what the installer writes and where (Order 03 `pfub72`); what is staged (Order 04 `gzsfqn`); companion-placement presets (a private companion repo is not a publication surface; unchanged and stated).
- Scope-Paths: agent_workflows/install_wizard.py, agent_workflows/project_schema.py, tests/test_install_consent_truth.py
- Item-Dependencies: none
- Status: to-review
- Blocks-Release: f33nrj
- Work-Kind: bug
- Priority: high
- Set: instbugs
- Order: 2
- Highest E allocated: 05
- Author: antigravity/claude-opus-5.5
- Id: gi1w75

## Workflow history
- 2026-10-07 same-status (aw set): gate on release 2.0.0 (f33nrj) at the maintainer's instruction 2026-10-06: all instbugs plans block 2.0.0

- 2026-10-07 draft (antigravity/claude-opus-5.5): created.
- 2026-10-07 to-review (antigravity/claude-opus-5.5): authored as Order 02 of Set `instbugs` after reproducing D04 (code reading of the overwrite loop) and D15 (scratch `project.json`) at HEAD `474b037a9`.

## Goal

The pre-write consent plan tells the user the truth: the exact paths that will be written, and a tracking policy for each that matches what the shipped ignore rules do, so consent is meaningful and no user is told to commit per-machine state.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-establish

- [ ] E-01 Re-measure at the execution HEAD: call `install_wizard.render_pre_write_plan` for a `private-target` policy against a temp git repo (or run `aw install --dry-run --preset private-target` there with `AW_NO_REEXEC=1` if that path prints the plan) and record the "Resolved Physical Classes" lines; run a real `aw install . --preset private-target -y --no-interactive` into a second temp repo and record `cat .aw/config/project.json` and `git status --short --ignored`.
  - Depends on: none
  - Expected outcome: pasted evidence that the printed paths do not exist after install and that `project.json` says `state_durable: target-git` while `git status --ignored` lists `!! .aw/state/`. STOP and report if either has already changed.
  - Execution state: pending

### Task group 2: fix

- [ ] E-02 In `render_pre_write_plan`, delete the overwrite loop and take each class's path from the resolved context (`ctx.physical_classes`), rendering `config_project` and `config_local` as the JSON file paths the wizard writes (`<config_root>/project.json`, `<config_root>/local.json`) and directory classes with a trailing slash. If the resolver raises, print `unresolved (<reason>)` for the class rather than inventing a path.
  - Depends on: E-01
  - Expected outcome: for every preset, every printed target path is one the install writes or (for runtime/durable directories) creates.
  - Execution state: pending

- [ ] E-03 Change `state_durable` to `Placement.TARGET_IGNORED` / `GitPolicy.IGNORED` in every TARGET-placement preset in `install_wizard.get_preset_defaults` and `project_schema.PRESET_PLACEMENTS`, with a comment citing the `.aw/.gitignore` `/state/` rule and D92. Rewrite the "Target Delta" line to list `.aw/system/` and `.aw/config/project.json` as tracked and `.aw/config/local.json`, `.aw/state/` as written-but-ignored.
  - Depends on: E-02
  - Expected outcome: a fresh install's `project.json` declares `state_durable` as `target-ignored` / `ignored`; the consent text agrees.
  - Execution state: pending

- [ ] E-04 On upgrade, when the loaded `project.json` declares a target-placement `state_durable` with `target-git`, rewrite it to `target-ignored` / `ignored` and print one line naming the change and why (D92), leaving any already-committed state file to the existing already-tracked warning (which prints the `git rm --cached` remedy; observed at HEAD).
  - Depends on: E-03
  - Expected outcome: an upgrade over a `project.json` carrying `target-git` leaves it carrying `ignored` and prints the normalization line once; a second install prints nothing new.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_install_consent_truth.py`: (a) for each preset whose placements are target-side, render the plan for a temp repo, extract every target path, run the real install into that repo, and assert each path exists (a file for the config classes, a directory or its parent for state classes); (b) assert a fresh install's `project.json` `git_policies["state_durable"] == "ignored"` and that `git check-ignore` reports the durable directory ignored, so declaration and behavior agree; (c) upgrade case: seed `project.json` with `target-git`, reinstall, assert it now says `ignored` and the output names the change. Prove (a) can fail by restoring the overwrite loop and pasting the failure.
  - Depends on: E-04
  - Expected outcome: the new tests pass; the mutation fails (a); no test reads production source.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The physical-path authority is `project_context.resolve_project_context` (`physical_classes`); the renderer already calls it, so the fix removes a second derivation rather than adding one.
- The `.aw/.gitignore` template's `/state/` comment is the recorded authority for "state is never committed" (D92, "Verified 2026-09-12").
- Install idempotence: re-running `aw install` must be safe and quiet when nothing changes.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The renderer computes correct paths then discards them for target placements. | `render_pre_write_plan`: `resolved_roots = {k: _format_path(str(v)) for k, v in ctx.physical_classes.items()}` followed by `for cls in ROOT_CLASSES:` ... `resolved_roots[cls] = f"{repo_formatted}/.aw/{cls}"` |
| F-02 | The report's log shows the effect: `config_project : <target-repo>/.aw/config_project [target] (target-git)`; none of the four printed directories existed after install. | report `l6cbbb` D04 |
| F-03 | Fresh HEAD install writes the contradiction. | scratch `project.json` `"state_durable": "target-tracked"` / `"target-git"`; `git status --short --ignored` -> `!! .aw/state/` |
| F-04 | The already-tracked warning exists and fires on upgrade. | upgrade log at HEAD: "Warning: these files are ALREADY git-tracked but match the untracked patterns: ... .aw/state/durable/install.json ... git rm --cached <path>" |

## Proposed changes (ordered, validatable)

1. Renderer reads resolved paths only (E-02).
2. Presets and delta text agree with the ignore rule (E-03).
3. Upgrade normalizes stale declarations (E-04).
4. Tests (E-05).

## Deferred / out of scope (with reason)

- WHERE THE STATE FILES ARE WRITTEN, and the duplicate root copies.
  - Carrier: pfub72
- STAGING `project.json`.
  - Carrier: gzsfqn

## Scope check

- Over-scope: none.
- Under-scope: companion presets keep `state_durable: companion-git`; a private companion is the user's own private store and D92 is about publication. Recorded so a reader does not assume it was missed.

## Required tests / validation

- `tests/test_install_consent_truth.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- Spec `20260810-1447-01-physical-aw-hierarchy-placement-and-migration` (cited by `install_wizard`'s module docstring): if it tabulates `state_durable` as tracked for `private-target`, add a dated history note via `aw specs note` recording the alignment with D92; if it does not, N/A. The executor states which.

## Open questions

### OQ-01: Is aligning `state_durable` to `ignored` a reversal of a deliberate design?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED from repository evidence: no. The later, deliberate and verified ruling is the `.aw/.gitignore` template's `/state/` rule (D92 leak containment), which this repository applies to itself in its root `.gitignore`; the maintainer ruled it on 2026-09-12 (backlog `2812t3`, done). The `project_schema.RootClass` docstring records that ruling and says the preset's remaining `target-tracked` divergence was left unfixed "because changing preset output is a contract change with its own blast radius". Blast radius MEASURED for this plan: the only reader of `git_policies` per class in `agent_workflows/` is `ProjectPolicy` validation in `install_wizard.py` (the "config_local and state_runtime MUST NOT be tracked in Git" invariant), and path resolution (`project_context.resolve_project_context`) derives the state paths from the delivery mode, not the placement value. So the contract change is the `project.json` value itself, which E-04 migrates on upgrade. The reviewer should confirm accepting that change; that is the decision this plan asks review to ratify. E-03 also rewrites the `RootClass` docstring paragraph that describes the divergence, since it no longer exists. Recorded in orchestrator `i99ykd` OQ-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit "Resolved Physical Classes" lines, the scratch `project.json` git policies, and `git status --short --ignored`, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the post-edit "Resolved Physical Classes" lines for `private-target`, then `ls -d` of each printed path after a real install showing each exists.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE a fresh install's `project.json` placements and git policies showing `state_durable` `target-ignored`/`ignored`, and the new "Target Delta" line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the upgrade output line announcing the normalization, `project.json` before and after, and a second install's output showing no repeat.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D04 and D15 share one surface (the consent plan and the preset tables that feed it); fixing one without the other leaves the consent plan accurate about paths and wrong about tracking, or the reverse.

EXECUTION CONTRACT. Execute E-items in order. Commit only files changed for this plan through `aw commit gi1w75 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. On completion move the plan to `executed/` with `aw ipd set executed gi1w75`.
