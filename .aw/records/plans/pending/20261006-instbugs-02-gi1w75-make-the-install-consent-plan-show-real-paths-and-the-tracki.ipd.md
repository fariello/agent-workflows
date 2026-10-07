# IPD: Make the install consent plan show real paths and the tracking policy the ignore rules actually apply

- Date: 2026-10-06
- Kind: child
- Concern: Defects D04 and D15 of research report `l6cbbb`, both present at HEAD `474b037a9`. D04: `install_wizard.render_pre_write_plan` first resolves the correct physical paths (`project_context.resolve_project_context(...).physical_classes`, which maps `config_project` to the `project.json` path, `state_durable` to `<state_root>/durable`, `state_runtime` to `<state_root>/runtime`), then its loop over `ROOT_CLASSES` OVERWRITES every entry with `f"{repo_formatted}/.aw/{cls}"` (and the home/companion branches with `.../.aw/{cls}`), so the consent surface lists `.aw/config_project`, `.aw/config_local`, `.aw/state_durable`, `.aw/state_runtime`, none of which is ever created. D15: the `private-target` preset (`install_wizard.get_preset_defaults` and `project_schema.PRESET_PLACEMENTS`) declares `state_durable` as `target-tracked` / `target-git`, and the consent text says "Target Delta: .aw/system/, .aw/config/project.json, .aw/state/durable created/updated.", while the shipped `.aw/.gitignore` template ignores `/state/` as D92 leak containment. A fresh scratch install writes exactly this contradiction into `.aw/config/project.json` (`"state_durable": "target-git"`), and the downstream user committed `state/durable/install.json` because of it.
- Scope: IN: (1) the consent plan prints the physical path each class resolves to, in every placement branch, with a file path where the class is a file; (2) every target-placement preset declares `state_durable` as `target-ignored` / `ignored`, matching the ignore rule, in all THREE places that derive it (`install_wizard.get_preset_defaults` private-target and custom branches, `project_schema.PRESET_PLACEMENTS`, and the per-class `git_policies` computed in `project_context.resolve_project_context`), plus the spec 6 preset table row; (3) the "Target Delta" line lists what is written AND whether it is tracked, consistent with the tables; (4) an upgrade over an existing `project.json` that still declares `state_durable: target-git` normalizes it to `ignored` and says so in the install output. OUT: what the installer writes and where (Order 03 `pfub72`); what is staged (Order 04 `gzsfqn`); companion-placement presets (a private companion repo is not a publication surface; unchanged and stated); clean-delta presets writing `.aw/config/` and `.aw/state/` into the target despite the 'ZERO AW-owned target files' line (backlog `mbx0o4`, found at review).
- Scope-Paths: agent_workflows/install_wizard.py, agent_workflows/project_schema.py, agent_workflows/project_context.py, tests/test_install_consent_truth.py, tests/fixtures/awphysical/order02/e01-portable-and-local.json, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- Blocks-Release: next
- Set: instbugs
- Order: 2
- Highest E allocated: 06
- Author: antigravity/claude-opus-5.5
- Id: gi1w75

## Workflow history
- 2026-10-07 reviewed (aw set): plan-review

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007. Reviewed in an isolated review-sweep lane; plan committed and byte-identical to the lane input, so no pre-review snapshot. Reproduced D04 on all four presets and D15 with a scratch install (F-07). Fixed: third `state_durable: target-git` derivation in `project_context.resolve_project_context` and the `custom` preset branch added to E-03 (PR-001); E-04 rewritten after measuring that upgrades already discard the stored policy (PR-002); spec `20260810-1447-01` Section 6 contradicts E-03, amendment added as E-06/V-06 with the spec in Scope-Paths (PR-003); E-02 now passes `companion_dir`, removes the invented-path fallback on resolver failure, and has a checkable outcome for non-target presets (PR-004); clean-delta presets writing into the target filed as backlog `mbx0o4` (PR-005); `- Blocks-Release: next` (PR-006); gate gains honesty rule, scope fence, temp HOME, conditional finalize ownership (PR-007). OQ-01 ratified from backlog `2812t3`.
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

- [ ] E-02 In `render_pre_write_plan`, delete the overwrite loop (`for cls in ROOT_CLASSES:` ... `resolved_roots[cls] = f"{repo_formatted}/.aw/{cls}"`) and take each class's path from `ctx.physical_classes` only (it already maps `config_project`/`config_local` to `<config_root>/project.json` / `local.json`; render directory classes with a trailing slash). Pass `policy.companion_dir` into the resolver call (today it is not passed, so the companion records path resolves to the `<repo>.aw/records` default even when the policy names another directory). If the resolver raises, print `unresolved (<reason>)` for every class rather than inventing a path (today the `except Exception: resolved_roots = {}` falls through to the invented paths). Remove the `ctx.logical_roots` fallback branch, which would print four-root paths under six-class labels.
  - Depends on: E-01
  - Expected outcome: for the target-placement presets (`private-target`, `custom` default), every printed path is one a real install writes or creates; for every preset the printed path equals `resolve_project_context(...).physical_classes[cls]` for the same inputs. (Clean-delta presets print resolver home paths that today's install does not honor; that writer gap is backlog `mbx0o4`, not this item.)
  - Execution state: pending

- [ ] E-03 Change `state_durable` to `Placement.TARGET_IGNORED` / `GitPolicy.IGNORED` for TARGET placement in all three derivations: `install_wizard.get_preset_defaults` (the `PRIVATE_TARGET` branch AND the `custom` fallback branch, both of which emit `TARGET_TRACKED`/`TARGET_GIT` today), `project_schema.PRESET_PLACEMENTS[private-target]`, and the `RootClass.STATE_DURABLE.value: GitPolicy.TARGET_GIT.value if resolved_preset in (PRIVATE_TARGET, SOURCE_CHECKOUT) ...` arm of the `git_policies` dict in `project_context.resolve_project_context` (which `resolve_existing_policy` does not read, but `aw` status surfaces do via `ctx.git_policies`). Add one comment at each site citing the `.aw/.gitignore` `/state/` rule (`engine._AW_GITIGNORE_TEMPLATE`) and D92. Rewrite the `project_schema.RootClass` docstring paragraph that records the divergence ("The remaining divergence ... recorded in backlog `2812t3` rather than fixed here") to say it is now resolved by this plan. Update `tests/fixtures/awphysical/order02/e01-portable-and-local.json` `state_durable` to `target-ignored`/`ignored` only if a test using it asserts the preset output (it is a parse fixture; leave it and say so if no assertion depends on the value). Rewrite the "Target Delta" line for tracked delivery to list `.aw/system/` and `.aw/config/project.json` as tracked and `.aw/config/local.json`, `.aw/state/` as written-but-ignored.
  - Depends on: E-02
  - Expected outcome: a fresh install's `project.json` declares `state_durable` as `target-ignored` / `ignored`; `resolve_project_context(...).git_policies["state_durable"]` is `ignored` for `private-target`; the consent text agrees.
  - Execution state: pending

- [ ] E-04 Make the upgrade normalization VISIBLE. Review measurement (Findings F-06): the upgrade path does not read the stored `placements`/`git_policies` at all (`install_wizard.resolve_existing_policy` builds a `ProjectPolicy` without them, so `__post_init__` refills preset defaults, and `persist_project_policy` rewrites `project.json` from that policy), so after E-03 an upgrade ALREADY rewrites the stored value. The work is therefore: in the `cli` install path immediately before `persist_project_policy`, read the existing `.aw/config/project.json` (if present) and, when its `git_policies.state_durable` is `target-git` and the policy about to be written says `ignored`, print one `term.status("info", ...)` line naming the change and why (D92 leak containment; `.aw/.gitignore` ignores `/state/`). Any already-committed state file stays with the existing already-tracked warning (which prints the `git rm --cached` remedy; observed at HEAD). Do NOT add a new rewrite path.
  - Depends on: E-03
  - Expected outcome: an upgrade over a `project.json` carrying `target-git` leaves it carrying `ignored` and prints the normalization line once; a second install prints no such line.
  - Execution state: pending

- [ ] E-06 Amend spec `20260810-1447-01-physical-aw-hierarchy-placement-and-migration` (status `implemented`) Section 6 preset table: the `private-target` row's "Durable state" cell `target tracked` becomes `target ignored`, and the Section 3 table rows for `state/durable/install.json`, `history/installs.jsonl`, `actions/` and `migrations/` ("MAY be tracked according to policy") gain the note that the shipped `.aw/.gitignore` ignores `state/` (D92), so policy no longer selects tracking. Record the amendment with `aw specs note` naming this plan.
  - Depends on: E-03
  - Expected outcome: the spec's preset table and the shipped preset agree; `aw specs check` reports no new finding for this spec.
  - Execution state: pending

### Task group 3: pin it

- [ ] E-05 Add `tests/test_install_consent_truth.py`: (a) for each preset whose placements are target-side, render the plan for a temp repo, extract every target path, run the real install into that repo (with `HOME` pointed at a temp dir), and assert each path exists (a file for the config classes, a directory or its parent for state classes); and for every preset assert each printed path equals `resolve_project_context(...).physical_classes[cls]`; (a2) assert `resolve_project_context` for `private-target` returns `git_policies["state_durable"] == "ignored"`; (b) assert a fresh install's `project.json` `git_policies["state_durable"] == "ignored"` and that `git check-ignore` reports the durable directory ignored, so declaration and behavior agree; (c) upgrade case: seed `project.json` with `target-git`, reinstall, assert it now says `ignored` and the output names the change. Prove (a) can fail by restoring the overwrite loop and pasting the failure.
  - Depends on: E-04, E-06
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
| F-05 | (review) A THIRD derivation of `state_durable: target-git` exists, in `project_context.resolve_project_context`'s per-class `git_policies` dict (`RootClass.STATE_DURABLE.value: GitPolicy.TARGET_GIT.value if resolved_preset in (Preset.PRIVATE_TARGET.value, ProjectRole.SOURCE_CHECKOUT.value) ...`), and `install_wizard.get_preset_defaults`'s `custom` fallback branch emits the same. The original plan named only two tables. | `project_context.resolve_project_context` "Git Policies calculation per physical class"; `get_preset_defaults` `else:` "Default fallback for custom" |
| F-06 | (review) The upgrade path ignores stored `placements`/`git_policies`: seeding `project.json` with `git_policies: {"state_durable": "untracked", "system": "untracked"}` and calling `resolve_existing_policy` then `resolve_policy_noninteractive` yields `state_durable = target-git` (the preset default), so the stored value never survives an upgrade and E-03 alone migrates it; E-04 only needs to announce it. | Review probe at lane HEAD: `existing git_policies.state_durable = target-git` / `resolved git_policies.state_durable = target-git`; `resolve_existing_policy` constructs `ProjectPolicy(...)` without `placements`/`git_policies`, and `ProjectPolicy.__post_init__` fills preset defaults |
| F-07 | (review) Reproduced D04 at lane HEAD across all four presets. `private-target` prints `<R>/.aw/config_project`, `<R>/.aw/state_durable` while the resolver returns `<R>/.aw/config/project.json`, `<R>/.aw/state/durable`; companion and home branches likewise print `.../.aw/<cls>` paths that the resolver does not return. | Review probe calling `render_pre_write_plan` and `resolve_project_context` per preset |
| F-08 | (review) Clean-delta presets write into the target: `aw install --preset completely-clean-target -y --no-interactive` left `.aw/config/{local,project}.json` and `.aw/state/durable/install.json` in the target while the plan says "ZERO AW-owned target files". `persist_project_policy` hard-codes `p_repo / ".aw" / "config"`. Out of this plan's scope (a writer, not the consent surface); filed. | Scratch install with temp `HOME`; backlog `mbx0o4` |
| F-09 | (review) Spec `20260810-1447-01` (implemented) Section 6 tabulates `private-target` Durable state as `target tracked`, so E-03 contradicts an approved contract unless the spec is amended in the same change. | spec Section 6 "Presets" table, `private-target` row |

## Proposed changes (ordered, validatable)

1. Renderer reads resolved paths only (E-02).
2. Presets (all three derivations) and delta text agree with the ignore rule (E-03).
3. Upgrade announces the normalization it already performs once E-03 lands (E-04).
4. Spec 6 preset table amended (E-06).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- WHERE THE STATE FILES ARE WRITTEN, and the duplicate root copies.
  - Carrier: pfub72
- STAGING `project.json`.
  - Carrier: gzsfqn
- CLEAN-DELTA PRESETS WRITING `.aw/config/` AND `.aw/state/` INTO THE TARGET (F-08).
  - Carrier: mbx0o4

## Scope check

- Over-scope: none.
- Under-scope: companion presets keep `state_durable: companion-git`; a private companion is the user's own private store and D92 is about publication. Recorded so a reader does not assume it was missed.

## Required tests / validation

- `tests/test_install_consent_truth.py` (E-05) with the mutation proof.
- Bare `python3 -m pytest` summary line pasted against a pre-edit baseline.

## Spec / documentation sync

- Spec `20260810-1447-01-physical-aw-hierarchy-placement-and-migration` (implemented; listed in Scope-Paths): it DOES tabulate `private-target` Durable state as `target tracked` (F-09), so E-06 amends the Section 6 row and the Section 3 durable-state rows, and records the amendment with `aw specs note`. WHY: the spec is the contract every other plan is reviewed against; leaving it saying `tracked` after the preset says `ignored` reintroduces the exact contradiction D15 is about. The `install_wizard` module docstring cites the spec under the legacy path `.agents/docs/specs/...`; correct that citation to `.aw/records/specs/implemented/...` while there.
- `project_schema.RootClass` docstring: the divergence paragraph is rewritten (E-03).

## Open questions

### OQ-01: Is aligning `state_durable` to `ignored` a reversal of a deliberate design?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED from repository evidence: no. The later, deliberate and verified ruling is the `.aw/.gitignore` template's `/state/` rule (D92 leak containment), which this repository applies to itself in its root `.gitignore`; the maintainer ruled it on 2026-09-12 (backlog `2812t3`, done). The `project_schema.RootClass` docstring records that ruling and says the preset's remaining `target-tracked` divergence was left unfixed "because changing preset output is a contract change with its own blast radius". Blast radius MEASURED for this plan: the only reader of `git_policies` per class in `agent_workflows/` is `ProjectPolicy` validation in `install_wizard.py` (the "config_local and state_runtime MUST NOT be tracked in Git" invariant), and path resolution (`project_context.resolve_project_context`) derives the state paths from the delivery mode, not the placement value. So the contract change is the `project.json` value itself, which E-04 migrates on upgrade. Ratified at review 2026-10-07: backlog `2812t3` "Remaining divergence" names option (a) "emit `target-ignored`/`ignored` for `state_durable` in the presets, matching reality" as an honest fix and asks only that it get its own plan, which this is; the blast-radius measurement was extended at review to the third derivation in `project_context.resolve_project_context` (F-05) and to the upgrade path, which rewrites the stored value from preset defaults anyway (F-06). E-03 also rewrites the `RootClass` docstring paragraph that describes the divergence, since it no longer exists. Recorded in orchestrator `i99ykd` OQ-01.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the pre-edit "Resolved Physical Classes" lines, the scratch `project.json` git policies, and `git status --short --ignored`, with the HEAD sha.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the post-edit "Resolved Physical Classes" lines for `private-target`, then `ls -d` of each printed path after a real install showing each exists; and PASTE the lines for `public-target-private-companion` beside `resolve_project_context(...).physical_classes` for the same inputs, showing they match.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE a fresh install's `project.json` placements and git policies showing `state_durable` `target-ignored`/`ignored`, `resolve_project_context(target_repo=<that repo>).git_policies["state_durable"]` printing `ignored`, `get_preset_defaults("custom")` showing the same, and the new "Target Delta" line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the upgrade output line announcing the normalization, `project.json` before and after, and a second install's output showing no repeat.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE `git diff` of the spec's Section 6 `private-target` row and Section 3 durable-state rows, the `aw specs note` output, and `aw specs check` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the narrowed run of the new test file, the mutation failure, and the bare-suite summary line against the baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: D04 and D15 share one surface (the consent plan and the preset tables that feed it); fixing one without the other leaves the consent plan accurate about paths and wrong about tracking, or the reverse.

EXECUTION CONTRACT. OQ-01 is resolved; no question is open. Execute E-items in dependency order (E-01, E-02, E-03, E-04, E-06, E-05). Commit only files changed for this plan through `aw commit gi1w75 -- <paths>`, never `git add -A`, never push; verify the staged set with `git diff --cached --name-only` first, since this is a shared checkout. HONESTY RULE (hard MUST): every `V-*` demands PASTED actual output; run the suite BARE as `python3 -m pytest` and paste the actual summary line; a claim without pasted output does not satisfy any item. Run every real install with `AW_NO_REEXEC=1` and `HOME` pointed at a temp dir so no operator home is written. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION, and it now includes the spec this plan amends; an out-of-scope edit is made and then justified at finalize with `--scope-reason`, and a declared path left unmodified (for example the fixture, if no assertion depends on it) is acknowledged with `--scope-ack`. LIFECYCLE, CONDITIONAL OWNERSHIP: under `aw oc run` / `aw agy run` the runner finalizes this plan after its merge-and-revalidate gate, so the executor does not; in a hand execution, the executor fills every `V-*`, confirms `aw ipd lint --phase pre-transition` conforms, and transitions with `aw ipd finalize gi1w75`, never by a hand `git mv`.
