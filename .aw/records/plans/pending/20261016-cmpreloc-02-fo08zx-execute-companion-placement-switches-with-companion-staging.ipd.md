# IPD: Execute companion placement switches with companion staging and attach or detach

- Date: 2026-10-16
- Kind: child
- Concern: Backlog `n9vd2h`: the cfgreloc executor (`placement_switch.execute_placement_switch`, plan `6u755v`) stages only in the target repository and never touches a companion identity, so a switch into or out of `public-target-private-companion` must keep refusing until the transaction can (1) create, stage into and remove from a SECOND git repository (the companion), (2) attach or detach the companion binding (`storage.attach_companion` writes `<companion>/.aw/companion_identity.json`, `<repo>/.aw/state/durable/companion_attachment.json` and the companion `.gitignore`; `storage.detach_companion` removes the attachment record), and (3) untrack or retrack the in-tree `project.json` for the two in-place pairs, all inside the same journal, verify, single-flip, resume and rollback discipline (spec `20260810-1447-01` Section 8.1, written by `ppu39q`). Order 01 (`xc8nae`) supplies the plan.
- Scope: IN: companion handling inside `execute_placement_switch`, `resume_placement_switch`, `rollback_placement_switch` and `placement_switch_status` for plans carrying `companion_action`; the `in-place` direction (config rewritten in place, no retirement); the attach and detach phases; per-repository staging (target and companion) with an ignore filter; companion entries in the journal and receipt; companion fault points; tests. OUT: CLI, docs and spec (Order 03 `y1e2m9`); `cli._run_install`'s own fresh-install companion attach, which stays as is.
- Scope-Paths: agent_workflows/placement_switch.py, tests/test_placement_switch_companion_execute.py
- Item-Dependencies: executed:xc8nae, executed:6u755v
- Status: to-review
- Work-Kind: feature
- Priority: low
- From-Backlog: n9vd2h
- Set: cmpreloc
- Order: 2
- Highest E allocated: 05
- Author: opencode
- Id: fo08zx

## Workflow history

- 2026-10-16 cross-reference (opencode, from /plan-review of xc8nae PR-001): Order 01 `xc8nae` now KEEPS `companion-unsupported` as an ordinary blocker beside a full companion census, so the cfgreloc executor and `ozr356` keep refusing companion pairs until this plan ships. This plan must remove that blocker in `placement_switch.plan_placement_switch` in the same change that adds executor support, and update `xc8nae`'s tests that assert it; its review should add that step explicitly. Also from that review: pair (d)'s `config_project` item carries `dest_git=None` (the new in-tree `project.json` stays untracked, F-02), and the target `dirty-aw-tree` rule now ignores exactly the untracked `.aw/config/project.json` a fresh companion install leaves.
- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored review-ready child of Set cmpreloc graduating backlog n9vd2h.

## Goal

A switch into or out of `public-target-private-companion` either completes with records in their new repository (staged there, never committed), exactly one authoritative `project.json`, the companion attached or detached to match the new preset, and the old footprint retired, or leaves the old side fully authoritative with the companion byte-identical to before; a crash at any phase resumes to the first outcome or rolls back to the second.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Transaction

- [ ] E-01 Companion preparation and per-repository staging. In the copy phase of `execute_placement_switch` (`6u755v` E-02), before copying any item: when `plan.companion_create`, `mkdir` the companion directory and run `git -C <companion> init -q`, journaling `created_companion: true` (rollback deletes the whole directory only when this flag is set). Copy items exactly as `6u755v` E-02 (copy2 with `follow_symlinks=False`, hash-identical re-check, journal per item and per created directory). After verify, stage per destination repository using the item's `dest_git`: for `"target"` the existing `6u755v` path (ensure `<repo>/.aw/.gitignore` with `engine._ensure_aw_gitignore`, filter with `git check-ignore --stdin -n -v --non-matching`, stage with `git add --pathspec-from-file=-`); for `"companion"` FIRST ensure the companion `.gitignore` carries the records untracked lanes the target's `.aw/.gitignore` already ignores (`records/*/untracked/`, `records/history.jsonl`, `records/runs/`, and the six generated `records/{plans,research,prompts}/INDEX.{json,md}`), appending only missing lines and journaling the file's prior bytes (or `created_companion_gitignore: true`), because `storage.materialize_companion_storage` ignores only `.aw/config/local.json` and `.aw/state/runtime/` (Order 01 F-05) and a plain stage would commit-stage box-local run state and absolute paths into the private companion; then filter and stage in the companion with the same two git commands run via `git -C <companion>`. Journal staged paths per repository (`staged: {"target": [...], "companion": [...]}`). Every git call into either repository uses `GIT_OPTIONAL_LOCKS=0`.
  - Depends on: none
  - Expected outcome: after `verified`, moved records exist at both sides byte-identical, are staged `A` in their destination repository, ignored lanes are on disk but unstaged, and the old side is still authoritative.
  - Execution state: pending

- [ ] E-02 Attach, detach and the authority flip. In the switch phase (`6u755v` E-03), for `in-place` plans rewrite `project.json` at the SAME path atomically from the old document (carrying `cutovers`, `setids`, consent and unknown keys exactly as `6u755v` E-03) with `preset`, `placements`, `git_policies`, `delivery_mode`, `records_backend` from `new_policy`, and write `local.json` per Order 01's `config_local` rewrite; there are no old config files to remove. For `to-home`/`to-target` plans the `6u755v` E-03 flip is unchanged. Then: `companion_action == "attach"`: journal `attach_started: true` with the prior bytes (or absence) of `<companion>/.aw/companion_identity.json` and `<repo>/.aw/state/durable/companion_attachment.json`, call `storage.attach_companion(repo, companion_dir)` (it re-runs `validate_companion_preflight`; a raise -> run the E-04 rollback and raise `PlacementSwitchError` with its text), and stage the identity file in the companion; `"detach"`: journal the attachment record's bytes, call `storage.detach_companion(repo)`. `config_retrack == "untrack"`: `git rm -q --cached -- .aw/config/project.json` in the target (left staged, matching a fresh companion install, Order 01 F-02); `"track"`: `git add -- .aw/config/project.json`. Journal `switched`. Assert, as `6u755v` E-03 does, `project_context.project_config_dir(repo)` equals the new config dir, AND `resolve_project_context(target_repo=repo).physical_classes["records"]` equals the plan's records destination root, AND `resolve_project_context(target_repo=repo).preset` equals the new preset; on mismatch run the E-04 rollback and raise. Re-running the phase on resume is idempotent (rewrites the same files; `attach_companion` rewrites the same identity; `detach_companion` on an absent record is a no-op).
  - Depends on: E-01
  - Expected outcome: readers resolve the new preset, the new records root and one `project.json`; the companion identity and attachment record match the new preset.
  - Execution state: pending

- [ ] E-03 Post-switch phases. `sources-removed`: remove move sources with the item's `source_git` (`git rm -q -f -- <rels>` batched per repository for tracked sources, `unlink` otherwise), then the `discard` sources (including the attachment record for a detach when `detach_companion` did not already remove it). Never delete the companion directory, its `.git`, its `.gitignore` or its `.aw/companion_identity.json` on a detach (Order 01 warning `companion-left-in-place`; `storage.detach_companion` "without deleting companion data"). `retired`: skip entirely when `plan.retire_side is None` (in-place pairs: the target keeps its system footprint, which the companion preset also places in the target per `install_wizard.get_preset_defaults` `RootClass.SYSTEM.value: Placement.TARGET_TRACKED.value`); otherwise call `retire_footprint` exactly as `6u755v` E-04, with `preserve` additionally holding `.aw/state/durable/companion_attachment.json` for an attach to-target switch. `done`: the receipt gains `companion_dir`, `companion_action`, `staged` per repository, and the companion's untouched-leftover list; it is written under the new side's `state_durable/migrations/` as before; then delete the control dir.
  - Depends on: E-02
  - Expected outcome: a completed switch leaves no control dir, a receipt naming both repositories' staged paths, the companion repository present after a detach, and no commit created in either repository.
  - Execution state: pending

- [ ] E-04 Recovery for companion plans. Extend `rollback_placement_switch` (`6u755v` E-05; still refused from `sources-removed` onward) with, after its existing step (1) and before its step (4): restore `<companion>/.aw/companion_identity.json` and `<repo>/.aw/state/durable/companion_attachment.json` to their journaled prior bytes or absence; undo `config_retrack` (`git reset -q -- .aw/config/project.json` in the target, which restores the index entry to `HEAD`); unstage every journaled companion path (`git -C <companion> rm -q --cached --ignore-unmatch -- <rels>`) and delete the copied companion destinations; restore the companion `.gitignore` to its journaled prior bytes (or delete it when `created_companion_gitignore`); delete the companion directory only when `created_companion`, and only after confirming it holds nothing but what this transaction created (else raise `PlacementSwitchError` and keep the journal). `resume_placement_switch` continues companion phases from the journal's frozen plan as for cfgreloc plans. Add fault points `"after-attach"` (after the attach or detach call, before `switched` is journaled) and `"mid-companion-stage"` (after the first companion path is staged); unknown values still raise `ValueError`.
  - Depends on: E-03
  - Expected outcome: every fault point resumes to the completed state; every pre-`sources-removed` fault point rolls back to a byte-identical target, companion (working tree and index) and `AW_HOME`.
  - Execution state: pending

### Task group 2: Tests

- [ ] E-05 Create `tests/test_placement_switch_companion_execute.py` (`pytestmark = pytest.mark.slow`; fixtures exactly as Order 01 E-03: fresh real install per test, companion committed after install, user record committed in its owning repository; customized `project.json` keys `cutovers.spec_id6 = "2020-01-01"`, `setids = {"warn_length": 10}`). Cases: (1) for each of the four representative pairs (a) `private-target` -> companion with a nonexistent companion path, (b) companion -> `private-target`, (c) companion -> `local-only`, (d) `local-only` -> companion with an existing empty committed companion: run `execute_placement_switch`; assert exactly one `project.json` for the project, `project_config_dir` and `resolve_project_context` preset and records root equal the new side, customized keys preserved, `x.backlog.md` byte-identical at the destination and staged `A` in the destination repository (`git -C <dest> diff --cached --name-status`), the source removal staged `D` in the source repository, `git rev-list --count HEAD` unchanged in BOTH repositories, `records/runs/r1/state.json` (written before the switch) present at the destination and NOT staged, `<companion>/.aw/companion_identity.json` present with the target's `project_id` after an attach, `companion_attachment.json` absent after a detach while the companion directory and its `.git` remain, receipt present, control dir gone; for (a) `git -C <repo> diff --cached --name-status -- .aw/config/project.json` shows `D` (untracked) and the file still on disk; (2) every fault point (the `6u755v` set plus `after-attach` and `mid-companion-stage`) in pairs (a) and (c): `resume_placement_switch` reaches the case (1) end state; (3) every pre-`sources-removed` fault point in pairs (a) and (d): `rollback_placement_switch` leaves the target tree, the target index, `AW_HOME`, and (for (d)) the companion tree and index byte-identical to a pre-switch snapshot (paths, sha256, `git status --porcelain`, `git diff --cached`), and for (a) the companion directory absent; (4) a blocker from Order 01 (`companion-dirty`) refuses with nothing written in either repository or `AW_HOME`; (5) an attach whose preflight fails at switch time (pair (d) with an existing companion: write a `<companion>/.aw/companion_identity.json` naming another `project_id`, then call `execute_placement_switch`, which plans after acquiring the lock per `6u755v` E-01 and must refuse naming `companion-preflight` with nothing written in either repository or `AW_HOME`). Mutation proofs, each restored before the next: (M1) skip the companion `.gitignore` extension; case (1)(a) must fail on the `records/runs/r1/state.json` not-staged assertion; (M2) skip the companion-index unstage in rollback; case (3)(d) must fail on the companion `git diff --cached` snapshot. Run `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_companion_execute.py tests/test_placement_switch_execute.py tests/test_placement_switch_companion_plan.py -v` and bare `python3 -m pytest`.
  - Depends on: E-04
  - Expected outcome: all cases pass; M1 and M2 each fail their named case, then pass after restore; the cfgreloc executor tests still pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The transaction discipline (lock sibling of control dir under `<AW_HOME>/placement-switches/`, frozen plan in the journal, copy-verify-switch-remove, single flip with a reader assertion, staged never committed, rollback window closed at `sources-removed`) is `6u755v`'s and is reused, not redesigned.
- Git staging of a mixed ignored/non-ignored set uses `git check-ignore --stdin -n -v --non-matching` then `git add --pathspec-from-file=-` (`6u755v` F-05).
- Companion identity and attachment writes go through `storage.attach_companion`/`storage.detach_companion`, the same calls `cli._run_install` and `aw storage` use.
- Mutation proofs are temporary and never committed.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `storage.attach_companion` writes three things: the companion identity, the target-side attachment record, and the companion layout and `.gitignore`. | `storage.attach_companion` calls `create_companion_identity` (`<companion>/.aw/companion_identity.json`), `write_local_attachment_record` (`<repo>/.aw/state/durable/companion_attachment.json`) and `materialize_companion_storage` (`.aw/config`, `.aw/state/durable`, `.aw/records` dirs and `.gitignore`). |
| F-02 | `storage.detach_companion` only unlinks the attachment record and reports `"companion_deleted": False`. | Its body: `p = Path(target_canon) / LOCAL_ATTACHMENT_RELPATH ... p.unlink()`. |
| F-03 | The companion `.gitignore` does not ignore the records untracked lanes. | `storage.materialize_companion_storage` `ignore_content = ".aw/config/local.json\n.aw/state/runtime/\n"`; the target's `.aw/.gitignore` (`engine._AW_GITIGNORE_TEMPLATE`) ignores `records/*/untracked/`, `records/history.jsonl`, `records/runs/` and the `INDEX` files, and explains that `records/runs/` holds absolute paths (D92). |
| F-04 | The companion preset keeps config and durable state in the target, so `private-target` <-> companion changes neither config dir nor state dir. | Order 01 (`xc8nae`) F-01 authoring probe. |
| F-05 | `cli._run_install` creates and `git init`s a missing companion during a fresh install. | `cli._run_install` "if getattr(policy, \"create_companion\", False) or not comp_p.exists(): comp_p.mkdir(...)" then `["git", "-C", str(comp_p), "init"]`. |

## Proposed changes (ordered, validatable)

1. Companion creation and per-repository staging with an ignore filter (E-01).
2. In-place flip, attach/detach and config retracking with a reader assertion (E-02).
3. Source removal per repository, skipped retirement for in-place pairs, receipt (E-03).
4. Rollback and resume for the companion state, new fault points (E-04).
5. Tests with snapshots of both repositories and two mutation proofs (E-05).

## Deferred / out of scope (with reason)

- CLI reachability, preview, docs and spec: Order 03.
  - Carrier: y1e2m9
- Deleting a detached companion repository: the user owns its git history and remote; `aw storage detach` deliberately preserves it, and so does this switch.
  - Carrier-Declined: deliberate non-goal, consistent with `storage.detach_companion`.
- Rewriting target git history to purge records that were tracked there before an attach: destructive and outside an install.
  - Carrier-Declined: deliberate non-goal; the Order 01 warning `records-leave-target-history` tells the operator.

## Scope check

- Over-scope: none.
- Under-scope: none; every companion obligation (second-repo staging, attach, detach, retrack, rollback of companion state, resume) has an E-item and a test case.

## Required tests / validation

- `python3 -m pytest -o addopts="" -m '' tests/test_placement_switch_companion_execute.py -v` passes, all fault points included.
- M1 and M2 fail their named cases, then pass after restore.
- The cfgreloc executor and the Order 01 planner modules still pass; bare `python3 -m pytest` passes.

## Spec / documentation sync

N/A: implements spec `20260810-1447-01` Section 8.1 items 4 to 7 for companion pairs; Order 03 (`y1e2m9`) amends item 3, which today says companion switches refuse. If execution finds the Section 8.1 contract unimplementable for a companion pair, STOP and record a blocking open question.

## Open questions

### OQ-01: Where does the journal live when the target and companion are two repositories?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Unchanged: `<AW_HOME>/placement-switches/<project_id>/` (`6u755v` OQ-02). It is outside both repositories and outside every retired side, and the project id is derived from the target path, so resume finds it from the target alone.

### OQ-02: Untrack the in-tree `project.json` when moving into the companion preset?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes, staged `git rm --cached` (the file stays on disk). A fresh companion install leaves it untracked (Order 01 F-02), the preset's whole purpose is a public target, and leaving a tracked file the preset does not track would make a switched repo differ from a freshly installed one. It is staged, never committed, so the operator sees it in `git status` before anything is published.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff -- agent_workflows/placement_switch.py` for the companion preparation and staging; pasted scratch run of pair (a) with `fault_injection="after-copy"` (produced by `execute_placement_switch`) showing `git -C <companion> diff --cached --name-only` listing `records/backlog/open/x.backlog.md` and not `records/runs/r1/state.json`, and the extended companion `.gitignore`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted scratch pair (a) and (c) runs (produced by `execute_placement_switch`) printing `project_config_dir`, the resolved preset and records root, the list of `project.json` files for the project, the companion identity's `project_id` after (a), and the attachment record's absence after (c).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted receipt JSON from a pair (b) run and `git rev-list --count HEAD` before and after in both repositories, produced by `execute_placement_switch`; pasted listing showing the companion directory and its `.git` still present after the detach.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted per-fault-point resume and rollback outcomes from the test run (produced by `resume_placement_switch`/`rollback_placement_switch`), including the companion index snapshot equality for pair (d) and the companion directory absence for pair (a).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `-v` runner output of the three modules passing; pasted M1 and M2 failure lines, `git diff --stat` after restore, and the passing re-run; pasted bare-suite summary line; pasted `aw sanitize --agent` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`) and after `xc8nae` and `6u755v` are executed. EXECUTION CONTRACT: all open questions are resolved. Scratch directories only; never run a switch against this repository, a real companion, or the real home. Paste ACTUAL runner output. Mutation proofs are temporary and MUST NOT be committed. Scope fence: `- Scope-Paths:`; justify any other edit at finalize. Commit through `aw commit fo08zx -- <paths>`; never `git add -A`, never push. Under a runner the runner finalizes; by hand, `aw ipd finalize fo08zx` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
