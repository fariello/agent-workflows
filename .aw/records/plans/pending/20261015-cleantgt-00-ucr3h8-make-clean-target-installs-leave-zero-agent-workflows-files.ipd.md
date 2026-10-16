# IPD: Make clean-target installs leave zero agent-workflows files in the target repository, through ordinary use

- Date: 2026-10-15
- Kind: orchestrator
- Concern: Backlog `kvwwt0`. `aw install --preset completely-clean-target` and `--preset local-only` (`delivery_mode: clean-delta`) still write and auto-commit 356 files into the target (re-measured 2026-10-15 at HEAD `57d5e8184`), and plan `irjoga`'s review measured that even a fixed installer is defeated on first ordinary use because record and system paths are hard-wired to `<repo>/.aw/...` across dozens of modules. Maintainer decisions 2026-10-15 (recorded on `irjoga` OQ-03/OQ-04): build the full feature now as an ordered Set; in clean-delta mode nothing from agent-workflows may appear in the target working tree, ignored or not, so control state and isolated worktrees also live under `AW_HOME/projects/<project_id>/`. Purpose stated by the maintainer: let a person or group use agent-workflows on a public repository without its presence being visible.
- Scope: Orchestrate seven children in strict order: (01) one records-root accessor adopted by every records reader/writer; (02) one system-root accessor adopted by every system-bundle reader/writer; (03) recognize a clean-target project with no in-repo `.aw`, including from a worktree outside the repo; (04) put clean-target control state and isolated worktrees under `AW_HOME`; (05) make the installer write nothing into the target and restore the truthful consent text; (06) make uninstall remove the home trees, keeping records unless `--deep`; (07) prove zero target delta end to end through ordinary use on both presets, and amend spec `20260810-1447-01` plus CHANGELOG. Replaces the single plan `irjoga`, which is retired as superseded by this Set. This plan carries orchestration only.
- Scope-Paths: .aw/records/plans/pending/20261015-cleantgt-00-ucr3h8-make-clean-target-installs-leave-zero-agent-workflows-files.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 4ec980a2c583c03acc9a8b58e37a26e96af8b656e2e88b0ed81afcfdce38dd3d
- Coverage-Checked: 2026-10-15 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: high
- From-Backlog: kvwwt0
- Blocks-Release: next
- Set: cleantgt
- Order: 0
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ucr3h8
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review: revisions applied (PR-001..PR-003)
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-10-15 to-review (aw set): authored as the replacement for irjoga per maintainer decision 2026-10-15 (irjoga OQ-03 option A)

- 2026-10-15 coverage pass (aw oc run): fingerprint 4ec980a2c583, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

After this Set, a `completely-clean-target` or `local-only` install, and every ordinary `aw` command run afterwards, leaves `git -C <target> status --porcelain --ignored` empty and the target `HEAD` unchanged, with all agent-workflows system files, records, control state and worktrees under `AW_HOME/projects/<project_id>/`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

THIS IS AN ORCHESTRATOR AND ITS ITEMS ARE ORCHESTRATION ONLY. Each item confirms one child reached `executed` and reads that child's own evidence; none produces an artifact.

### Task group 1: sequence and verify the Set

- [ ] E-01 CONFIRM kfnfji REACHED executed
  - Depends on: none
  - Expected outcome: `kfnfji` is in `executed/`, and its own V-items record the records-root accessor, home-backed records routing for the converted readers/writers, the residual-literal audit, and byte-identical behavior for a repository-backed install.
  - Execution state: pending
- [ ] E-02 CONFIRM 4gn1ka REACHED executed
  - Depends on: E-01
  - Expected outcome: `4gn1ka` is in `executed/`, with its system-root accessor, routed readers/writers, and tracked-install parity recorded in its own V-items.
  - Execution state: pending
- [ ] E-03 CONFIRM fnnwj3 REACHED executed
  - Depends on: E-02
  - Expected outcome: `fnnwj3` is in `executed/` (it also waits on the OUT-OF-SET plan `ivq0nr`, see the Child IPDs note), with its own V-items showing a clean-target root, its subdirectories and an external worktree resolving to the project with no in-repo `.aw`.
  - Execution state: pending
- [ ] E-04 CONFIRM qk0ew6 REACHED executed
  - Depends on: E-03
  - Expected outcome: `qk0ew6` is in `executed/`, with its own V-items showing clean-delta control state and lane worktrees under `AW_HOME` and an inner `aw` in an external lane resolving the same project and control root.
  - Execution state: pending
- [ ] E-05 CONFIRM 3m8aix REACHED executed
  - Depends on: E-04
  - Expected outcome: `3m8aix` is in `executed/`, with its own V-items showing an install of both presets leaves `git status --porcelain --ignored` empty and HEAD unchanged, and the restored ZERO-delta consent line.
  - Execution state: pending
- [ ] E-06 CONFIRM xoy5yg REACHED executed
  - Depends on: E-05
  - Expected outcome: `xoy5yg` is in `executed/`, with its own V-items showing uninstall removes home system/config/state/worktrees, keeps records by default, and removes them under `--deep`.
  - Execution state: pending
- [ ] E-07 CONFIRM nwporz REACHED executed
  - Depends on: E-06
  - Expected outcome: `nwporz` is in `executed/`, with its own V-items showing the ordinary-use end-to-end proof on both presets, the mutation proofs, the spec `20260810-1447-01` amendment and the CHANGELOG line.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `kfnfji` | `20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md` | One records-root accessor adopted by every records reader and writer | none |
| 02 | `4gn1ka` | `20261015-cleantgt-02-4gn1ka-route-every-system-bundle-reader-through-one-system-root-acc.ipd.md` | One system-root accessor adopted by every system-bundle reader and writer | executed:kfnfji |
| 03 | `fnnwj3` | `20261015-cleantgt-03-fnnwj3-recognize-a-clean-target-project-with-no-in-repo-aw-includin.ipd.md` | Recognize a clean-target project with no in-repo `.aw`, including from an external worktree | executed:4gn1ka, executed:ivq0nr |
| 04 | `qk0ew6` | `20261015-cleantgt-04-qk0ew6-put-clean-target-run-state-and-isolated-worktrees-under-aw-h.ipd.md` | Clean-delta control state and isolated worktrees under `AW_HOME` | executed:fnnwj3 |
| 05 | `3m8aix` | `20261015-cleantgt-05-3m8aix-make-a-clean-target-install-write-nothing-into-the-target-an.ipd.md` | Installer writes nothing into the target; truthful consent text | executed:qk0ew6 |
| 06 | `xoy5yg` | `20261015-cleantgt-06-xoy5yg-make-uninstall-remove-clean-target-home-trees-keeping-record.ipd.md` | Uninstall removes home trees, keeps records unless `--deep` | executed:3m8aix |
| 07 | `nwporz` | `20261015-cleantgt-07-nwporz-prove-clean-target-zero-target-delta-end-to-end-through-ordi.ipd.md` | Ordinary-use end-to-end proof, spec amendment, CHANGELOG | executed:xoy5yg |

EXTERNAL DEPENDENCY. `fnnwj3` (Order 03) also declares `executed:ivq0nr`, a plan OUTSIDE this Set (Set `nj13xp`). At review (2026-10-15) `ivq0nr` was `reviewed` with `Readiness: no-go` because its OQ-01 is `Blocking: yes`, `Owner: maintainer` (should `find_project_root` stop climbing at a `.git` boundary with no AW marker). Until a human answers that question and `ivq0nr` is approved and executed, the runner marks `fnnwj3` `dependency-blocked` and Orders 04-07 wait behind it; Orders 01-02 can run first.

## Completion criteria (the whole Set is done only when)

- A clean-target install of both presets leaves zero target delta. Owner: 3m8aix
- Every ordinary `aw` command exercised in the proof leaves zero target delta, and its output lands under `AW_HOME`. Owner: nwporz
- Uninstall removes the home trees per the records-retention rule. Owner: xoy5yg
- Spec `20260810-1447-01` Sections 4 and 5 describe the clean-delta exception and CHANGELOG records the fix. Owner: nwporz

## Cross-IPD validation

- The accessors added by `kfnfji` and `4gn1ka` are the ones every later child calls (no second path derivation): checked in `nwporz`'s end-to-end proof, which fails if any verb writes in-tree. Owner: nwporz
- Repository-backed (non-clean-delta) installs are unchanged: each of `kfnfji` and `4gn1ka` records parity, and the bare full suite passes at every child's finalize. Owner: kfnfji, 4gn1ka

## Deferred / out of scope (with reason)

- Closing backlog `kvwwt0` as `done` after the Set ships. This is a backlog-record act, not orchestrator work. The automatic HANDOFF close will ALWAYS refuse, because the superseded plan `irjoga` still carries `- From-Backlog: kvwwt0` and a superseded carrier can never become executed (measured at review: `runner_shared.evaluate_backlog_close(..., 'kvwwt0')` lists the `superseded/` irjoga path among "IPD carrier(s) not executed", and `check_engine.evaluate_blocking_close` refuses `done` without evidence). The item stays `graduated` and release-blocking, which is visible in `aw attention`. Once `nwporz` is executed, close it with `aw backlog set done kvwwt0 --evidence <nwporz's executed/ path>` (the SATISFIED route, which accepts an executed plan; verified at review against an executed plan). Do NOT edit irjoga's `From-Backlog` to unblock the HANDOFF route, because that rewrites a terminal record.
  - Carrier: kvwwt0
- Global user-scope host adapter delivery (`~/.config/opencode/`, `~/.claude/`) for clean-delta installs: spec `or061f` names it a separate feature; this Set only stops target writes.
  - Carrier-Declined: independent feature owned by deferred spec `or061f`, not required for zero target delta.

## Scope check

- Over-scope: none.
- Under-scope: none; every whole-Set criterion names an owning child.

## Required tests / validation

This plan runs no tests; the whole-Set measurement is performed by `nwporz`.

## Open questions

### OQ-01: Does this Set replace `irjoga`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved 2026-10-15: yes. The maintainer chose option (A) on `irjoga` OQ-03 (build it as a Set); `irjoga` is retired to `superseded/` pointing at this orchestrator, and its OQ-04 decision is carried into `qk0ew6`.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `kfnfji`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `4gn1ka`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `fnnwj3`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `qk0ew6`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `3m8aix`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: `xoy5yg`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: `nwporz`'s path in `executed/` and its V-items' pasted results quoted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Orchestration only: run the Set with `aw oc run cleantgt` (each child in its own isolated worktree, in dependency order) after review and approval of each plan, or by hand through the `exec-set` workflow, executing each child in its own isolated worktree (`aw work begin <id6>`) in the Order shown and never on the shared main checkout. This plan's items are confirmations only: tick E-NN and fill V-NN only from the child's own `executed/` file, quoting its pasted V-item results (HONESTY: never record a pass you did not read). Scope fence: `- Scope-Paths:` is a declaration; an out-of-scope edit is justified at finalize with `--scope-reason`. Commits go only through `aw commit ucr3h8 -- <this plan path>` after checking `git diff --cached --name-only`; never `git add -A`, never push, never tag. Lifecycle: under a runner, the runner retires this orchestrator to `executed/` once every child is executed on disk; by hand, after every V-item passes and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize ucr3h8`. Never hand-`git mv` it.
