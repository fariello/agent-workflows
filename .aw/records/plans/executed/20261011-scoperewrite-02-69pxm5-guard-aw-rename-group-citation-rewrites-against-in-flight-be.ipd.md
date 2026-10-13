# IPD: Guard aw rename/group citation rewrites against in-flight begin receipts

- Date: 2026-10-11
- Kind: child
- Concern: `aw rename` and `aw group` (and their plans/research spellings `aw plans mv`/`set-assign`, `aw research mv`/`set-assign`) rewrite every citation of a renamed artifact across `artifact_core.REFERENCE_SCAN_ROOTS`, which includes `.aw/records/plans`, and NONE of the three rewrite backends (`artifact_rename`, `plans_refs`, `research_refs`) consults a begin receipt first. A plan mid-execution has a receipt that FREEZES its `Scope-Paths` and its E/V action blocks (`ipd_lifecycle.frozen_region_digest`), so a rewritten citation inside that frozen region makes `ipd_lifecycle.receipt_is_current` False, and because a rename is a removal plus an addition, rcptwiden `63425h`'s additive-widening accept (`ipd_lifecycle.widening_is_acceptable`, which requires `not cmp.removed`) does not rescue it: `finalize_precheck` refuses as STALE and the lane strands. Backlog `23p80m` (raised as F-06 of executed plan `5h3qyy`) carries this; authoring REPRODUCED it end to end on all three backends (F-01).
- Scope: IN: (a) one shared, generic in-flight edit filter in `artifact_refs` that drops every planned rewrite whose target file is a plan file with a begin receipt present, REUSING `artifact_refs.classify_citing_plans_for_rewrite` (5h3qyy E-04) as the liveness predicate rather than defining liveness a second time, and returns one human-readable skip note per skipped file; (b) wiring that filter immediately after edit PLANNING at each of the four planning call sites (`artifact_rename.run_rename_generic`, `artifact_rename.run_group_generic`, `plans_refs.apply_renames`, `research_refs._apply_renames`), so preview and apply, human and `--agent`/`--json`, all see the same filtered edit set and the skip notes flow through each backend's existing `warnings` -> printed line + `MutationResult.notes` channel; (c) behavior tests driving the real CLI verbs; (d) a DECISIONS.md entry recording skip-and-report over refuse; (e) a one-sentence amendment to the plans-adopter spec Section 4.5, whose "rewriting citations" contract this narrows; (f) one CHANGELOG line. OUT: `plans_archive` (a shard move is DIR-only and its module docstring records it is "a CITATION NO-OP (no reference rewrite)", so it has no rewrite to guard); the status setters (already guarded by `5h3qyy`); any override flag to force-rewrite an in-flight plan (`--no-refs` already exists for the opposite direction, and a force flag would re-create the hazard on demand; see OQ-01); repairing citations left stale by a skip (the in-flight plan's own author fixes them after finalize, exactly as D159 leaves skipped status-setter citations).
- Scope-Paths: agent_workflows/artifact_refs.py, agent_workflows/artifact_rename.py, agent_workflows/plans_refs.py, agent_workflows/research_refs.py, tests/test_rename_receipt_guard.py, DECISIONS.md, CHANGELOG.md, .aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md
- Scope-Exceeded: .aw/records/backlog/open/20261012-nj13xp-01-nj13xp-test-finalize-sendback-e2e-runs-aw-ipd-scaffold-wi.backlog.md (follow-up defect the executor found and filed instead of fixing out of scope); .aw/records/backlog/open/20261012-t8icgt-01-t8icgt-renaming-an-in-flight-plan-s-own-file-while-its-be.backlog.md (E-08 files F-07 as a new backlog item whose id6 is minted, so it cannot be declared in advance plan Scope check)
- Item-Dependencies: executed:5h3qyy
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 23p80m
- Blocks-Release: next
- Set: scoperewrite
- Order: 2
- Highest E allocated: 08
- Author: opencode/claude-opus
- Id: 69pxm5

## Workflow history
- 2026-10-13 executed (opencode its_direct/pt3-claude-opus-5.5-1m-us): finalized during stranded-lane recovery 2026-10-12: the lane's suite_check failed only on host-environment tests later traced to a stray /tmp/.aw (backlog 5tj8g4); the merge of this lane onto current main re-ran green (69pxm5: 7296 passed; akhwp7: 7295 passed) [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261012-nj13xp-01-nj13xp-test-finalize-sendback-e2e-runs-aw-ipd-scaffold-wi.backlog.md: follow-up defect the executor found and filed instead of fixing out of scope; out-of-scope .aw/records/backlog/open/20261012-t8icgt-01-t8icgt-renaming-an-in-flight-plan-s-own-file-while-its-be.backlog.md: E-08 files F-07 as a new backlog item whose id6 is minted, so it cannot be declared in advance (plan Scope check)]
- 2026-10-12 executing (opencode/its_direct/pt3-claude-opus-5.5-1m-us): E-01..E-08 performed and V-01..V-08 pass in lane 69pxm5 (run run-20261012T170951Z-1138207); filed F-07 as backlog t8icgt; runner owns finalize.
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (MEDIUM, fixed: E-04(h) demanded note text on compact --agent output, which projects evidence to key names; now --json data.notes), PR-002 (MEDIUM, fixed: in-flight plan self-rename unguarded, recorded as F-07, pinned by E-04(i), handed off via 23p80m), PR-003 (LOW, fixed: E-02 path resolution for absolute vs relative edit files), PR-004 (LOW, fixed: E-08 files F-07 so it outlives 23p80m). F-01 re-reproduced on all three backends at HEAD ebe34e463; E-02/E-03 design prototyped by wrapping the three planners: in-flight plan unchanged, sibling plan and tests/ file rewritten, rc 0, SKIPPED printed on apply and preview. Record: .aw/records/reviews/20261011-scoperewrite-02-69pxm5-guard-aw-rename-group-citation-rewrites-against-in-flight-be.review.md.
- 2026-10-12 to-review (opencode/claude-opus): graduated from backlog `23p80m`. Authoring reproduced the defect on all three rewrite backends with a live receipt present (F-01), confirmed `classify_citing_plans_for_rewrite` from `5h3qyy` is directly reusable (F-03), and found that the guard must skip the WHOLE citing file rather than only its `Scope-Paths` line because the frozen region also covers E/V action blocks (F-02).
- 2026-10-12 draft (opencode/claude-opus): created.

## Goal

Make every rename/regroup citation rewrite skip, and visibly report, any citing plan that has a live begin receipt, so renaming an artifact can no longer stale an executing plan's frozen contract and strand its lane at finalize. Reuse the in-flight predicate `5h3qyy` already shipped so liveness is defined exactly once.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure the base

- [x] E-01 Re-drive the F-01 reproduction at execution HEAD before editing anything: on a scratch git repo (outside the checkout, under the system temp dir) create a citing pending plan whose `- Scope-Paths:` names a spec, a pending plan, and a research document, write a receipt at `ipd_lifecycle.receipt_path_for(<scratch>, <plan-id6>)`, then run `aw group specs <id6> --set <s> --rename --apply --no-commit`, `aw rename plans <id6> --slug <s> --apply --no-commit` and `aw rename research <id6> --slug <s> --apply --no-commit` through `cli.main`, and record for each whether the in-flight plan's bytes changed. Also re-confirm that `artifact_rename.py`, `plans_refs.py` and `research_refs.py` still contain no receipt consultation (`grep -c 'receipt'` per file) and that `artifact_refs.classify_citing_plans_for_rewrite` still exists with its `(rewritable, must_skip)` return shape. If the reproduction no longer changes the plan on some backend, record that and narrow E-03 to the backends that still do; if `classify_citing_plans_for_rewrite` is gone or reshaped, mark this item `blocked`, because E-02 depends on it.
  - Depends on: none
  - Expected outcome: a dated re-measurement line appended to Findings with the three per-backend `changed: True|False` results and the three grep counts; no source file modified.
  - Execution state: performed

### Task group 2: The shared filter

- [x] E-02 Add `artifact_refs.filter_in_flight_plan_edits(repo_root, edits) -> (kept_edits, skip_notes)`. It is GENERIC over any edit object exposing a `.file` path (both `artifact_refs.RefEdit` and `research_refs.RefEdit` do), so one function serves all three backends. Edit `.file` values are absolute paths in practice (the planner walks under `repo_root`), but resolve a relative one against `repo_root` and compare by `Path.resolve()` so both forms match; a file that resolves outside `repo_root` is never dropped. Partition the distinct `.file` values into PLAN files (a `.ipd.md` file under `.aw/records/plans/` or `.agents/plans/`, any disposition, resolved relative to `repo_root`) and everything else; pass only the plan files to the EXISTING `classify_citing_plans_for_rewrite(repo_root, plan_files)` and do not re-implement its receipt or `- Id:` logic. Drop EVERY edit whose file is in its `must_skip` set (all edits for that file, not only `Scope-Paths` edits, per F-02), keep all others in their original order, and emit one note per skipped file in the form `--- SKIPPED citation rewrite in <repo-relative path>: <reason> (in-flight plan; fix the citation after it finalizes) ---`, matching the `--- WARNING: ... ---` shape the planner's existing warnings use. Non-plan files and plan files without a receipt are never dropped, so with zero receipts present the function returns its input unchanged and no notes.
  - Depends on: E-01
  - Expected outcome: a new function in `artifact_refs.py`; `classify_citing_plans_for_rewrite`, `plan_reference_rewrites_with_warnings` and `apply_reference_rewrites` are byte-unchanged.
  - Execution state: performed

### Task group 3: Wire it into every rewrite planning site

- [x] E-03 Call `filter_in_flight_plan_edits` immediately after edit planning at each of the four planning sites, appending its notes to that site's existing `warnings` list so they reach both the printed output and `MutationResult.notes` through the code each backend already has: `artifact_rename.run_rename_generic` (the `plan_reference_rewrites_with_warnings(repo_root, src.name, new_name)` call), `artifact_rename.run_group_generic` (the per-target `plan_reference_rewrites_with_warnings(repo_root, src.name, dst.name)` call; filter the accumulated `all_edits` once after the loop and append notes to `all_warnings` de-duplicated as that loop already does), `plans_refs.apply_renames` (the `plan_reference_rewrites_with_warnings(repo_root, name_map, plans_dir)` call), and `research_refs._apply_renames` (the `plan_reference_rewrites_with_warnings(repo_root, renames)` call). Filtering at PLANNING time rather than at apply time is deliberate: it makes the preview truthful (a dry run shows the skip it will perform), and because skipped files never enter the edit list they never enter `touched_paths`, so the self-commit path set excludes them with no further change. Do not alter the `update_refs`/`--no-refs` branches, the test-edit interactive filter, the rename order, or any refusal path.
  - Depends on: E-02
  - Expected outcome: all four sites filtered; with no receipts present, every existing rename/group test still passes unchanged.
  - Execution state: performed

### Task group 4: Tests

- [x] E-04 Add `tests/test_rename_receipt_guard.py`, driving the real CLI (`cli.main` with `--dir <tmp git repo>`, following the fixture style of `tests/test_artifact_refs_rewrite.py`) and asserting only on real outputs, exit codes and file bytes (GUIDING_PRINCIPLES P16: never read production source, count callers, or pin comments). Pin: (a) `aw group specs ... --rename --apply` with two citing pending plans, one with a receipt file and one without, leaves the in-flight plan byte-identical, rewrites the other, exits 0, and prints a SKIPPED line naming the in-flight plan; (b) the same for `aw rename plans` (plans_refs backend); (c) the same for `aw rename research` (research_refs backend); (d) a citation inside an E-item action block (not `Scope-Paths`) of an in-flight plan is also left unchanged, pinning F-02; (e) a non-plan citing file (a file under `tests/` in the scratch repo) is still rewritten while an in-flight plan is skipped; (f) PREVIEW (no `--apply`) prints the SKIPPED line and lists no `would rewrite` line for the in-flight plan; (g) with NO receipt anywhere, the in-flight-candidate plan IS rewritten, pinning that the guard is a no-op in the common case; (h) under `--agent`, the record validates with `agent_schema.assert_valid_agent_record` and its `evidence` list names `notes`, and under `--json` the `data.notes` list contains the SKIPPED line. (Measured at review: the COMPACT `--agent` record projects evidence to its key names only, `"evidence":["notes"]`, so the note TEXT is visible only under `--json` or `--agent --verbose`; do not assert the text on compact `--agent` output.); (i) renaming the IN-FLIGHT PLAN ITSELF (`aw rename plans <in-flight id6> --slug <s> --apply`) still succeeds and is unchanged by this plan, recording that behavior as the baseline, since F-07 leaves it out of scope.
  - Depends on: E-03
  - Expected outcome: a new passing test module pinning (a) through (i).
  - Execution state: performed

### Task group 5: Records

- [x] E-05 Append ONE `### D<n>` entry to `DECISIONS.md`, re-deriving `<n>` as one more than the highest existing `### D` number at execution time (D162 was highest at authoring; do not trust that figure), in the house shape (Context, Decision with rejected alternatives and trade-off, Applied). It records that rename/group citation rewriting SKIPS AND REPORTS in-flight plans rather than refusing the rename or rewriting and re-freezing, cites D159 as the posture precedent, and cites F-01 (reproduction) and F-02 (whole-file skip). Modify no existing entry.
  - Depends on: E-03
  - Expected outcome: an append-only diff adding exactly one decision entry.
  - Execution state: performed

- [x] E-06 Amend Section 4.5 ("Regroup / rename verb") of `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md` with ONE added sentence after "rewriting citations by the stable id.": a citing plan holding a live begin receipt is NOT rewritten; the skip is reported and the citation is left for that plan's author to fix after it finalizes (decision D<n> from E-05). Change no other text and do not change the spec's `- Status:`.
  - Depends on: E-05
  - Expected outcome: a one-sentence additive diff in that spec section.
  - Execution state: performed

- [x] E-07 Add one CHANGELOG bullet under the existing `## 2.0.0 (pending)` heading, prefixed `Fixed:`, stating that `aw rename` and `aw group` no longer rewrite citations inside a plan that is mid-execution, and report the skip instead. No new heading; do not reword neighbouring bullets; no em or en dashes (user-facing prose).
  - Depends on: E-04
  - Expected outcome: exactly one new CHANGELOG bullet.
  - Execution state: performed

- [x] E-08 File F-07 as its own backlog item so it survives this plan's close of `23p80m`: run `aw backlog new` (Work-Kind `bug`, so it carries `- Blocks-Release: next` per the live-bug gate unless the maintainer exempts it) with a summary naming "renaming an in-flight plan's own file while its begin receipt is live" and a body quoting F-07's reproduction, then replace the F-07 deferred row's `- Carrier: 23p80m` with the new item's id6. Before filing, re-drive F-07's reproduction on a scratch repo and paste whether the rename still succeeds; if a later change already guards it, record that and file nothing.
  - Depends on: E-04
  - Expected outcome: a new backlog item id6 (or a recorded "already guarded" result), and the F-07 deferred row's carrier pointing at it.
  - Execution state: performed

## Project conventions discovered (Step 0)

- ONE LIVENESS PREDICATE. `5h3qyy` shipped `artifact_refs.classify_citing_plans_for_rewrite`, which fails CLOSED (a receipt file present, readable or corrupt, or a missing `- Id:`, means must-skip) and deliberately does NOT reuse `check_engine._receipt_is_live`, whose fail-safe direction is the opposite. The backlog item asks to reuse that predicate rather than define liveness a second time; E-02 does exactly that.
- RECEIPTS ARE CHECKOUT-ANCHORED. `ipd_lifecycle.receipt_dir` resolves through `checkout_control_root`, so a rename run inside a lane sees the main checkout's receipts (the backlog `dh0uno` fix). The guard therefore works from a lane without extra plumbing.
- REWRITE BACKENDS SHARE A WARNINGS CHANNEL. Each of the three backends already turns planner `warnings` into printed lines AND `MutationResult.notes`, and `cli.map_mutation_result_to_command_result` (the `if mr.notes:` branch) surfaces notes as `Evidence(key="notes")` and `data["notes"]` in machine output. Routing skip notes through that list gives human and machine reporting with no new output path.
- `touched_paths` IS THE COMMIT PATH SET and is built only from applied edits, so an edit removed before apply never reaches a self-commit.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Where | Finding and evidence |
|---|---|---|---|
| F-01 | **HIGH** | `artifact_rename.run_group_generic`, `plans_refs.apply_renames`, `research_refs._apply_renames` | **REPRODUCED ON ALL THREE BACKENDS at HEAD `3f4ccd32c`.** Scratch git repo, citing pending plan `p22222` with a receipt at `.aw/state/ipd-lifecycle/p22222.receipt.json` and `- Scope-Paths:` naming a spec, a pending plan and a research doc. Driven through `cli.main`: `aw group specs s11111 --set newgrp --rename --apply --no-commit` printed `rewrote 1x '20260701-grp-01-s11111-my-spec.spec.md' -> '20260701-newgrp-01-s11111-my-spec.spec.md' in .aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md`, rc 0, `in-flight plan changed: True`; `aw rename plans p33333 --slug zz` rc 0, `in-flight plan changed: True`; `aw rename research r44444 --slug zz` rc 0, `in-flight plan changed: True`. Final `- Scope-Paths: 20260701-p33333-01-p33333-zz.ipd.md, .aw/records/research/20260701-seta-01-r44444-zz.reference-research.md`. Every frozen entry was rewritten while a receipt was present. |
| F-02 | **HIGH** | `ipd_lifecycle.frozen_region_digest`, `_requirements_from_plan` | **THE GUARD MUST SKIP THE WHOLE FILE, NOT ONLY ITS `Scope-Paths` LINE.** The frozen region covers `Scope-Paths` AND each E-item and V-item action block (`_requirements_from_plan` builds `must` and `validation` from `ipd_lint.leaf_action_blocks`). Unlike the status setter (which `5h3qyy` limited to the `Scope-Paths` line), the rename rewriter edits citations ANYWHERE in the file, including E/V action text, so a `Scope-Paths`-only guard would still stale a receipt whose plan names the renamed artifact in an E-item. Prose outside E/V blocks is not frozen, but skipping the whole file is simpler, fails closed, and costs only a stale prose citation the author fixes after finalize. |
| F-03 | MEDIUM | `artifact_refs.classify_citing_plans_for_rewrite` | **THE 5h3qyy PREDICATE IS DIRECTLY REUSABLE.** Signature `(repo_root, candidate_files) -> (rewritable, must_skip_with_reasons)`; it reads each file's `- Id:` and checks `ipd_lifecycle.receipt_path_for(repo_root, id6).exists()`. It is not tied to `Scope-Paths` or to pending plans, so feeding it the plan files among a rename's edit targets is a correct use. It treats a missing `- Id:` as must-skip; measured at authoring, every `.ipd.md` under `.aw/records/plans/` carries `- Id:` (the only 7 files without one are the `README.md`/`STATUS.md` manifests, which the planner already skips via `_SKIP_NAMES`), so restricting the predicate to `.ipd.md` files avoids a spurious skip. |
| F-04 | MEDIUM | `artifact_rename.py`, `plans_refs.py`, `research_refs.py`, `plans_archive.py` | **NO GUARD EXISTS AND `plans_archive` NEEDS NONE.** `grep -c 'receipt\|in_flight\|in-flight'` over the four modules at authoring HEAD: 0 matches in total. `plans_archive`'s module docstring states a shard move "changes the plan's path but NOT its filename, and plans are cited by basename/stem, so it is a CITATION NO-OP (no reference rewrite)", and it imports no reference rewriter, so it is out of scope. |
| F-05 | LOW | four planning call sites | **THE PLANNING SITES ARE FOUR, NOT THREE.** `artifact_rename` plans edits in two functions (`run_rename_generic` and, per target, `run_group_generic`), plus `plans_refs.apply_renames` and `research_refs._apply_renames`; `plans_refs.run_set_assign`/`run_mv` and `research_refs.run_set_assign`/`run_mv` route through those last two. Wiring at planning time covers every verb spelling and both preview and apply. |
| F-07 | LOW | `plans_refs` rename of the in-flight plan itself | (review, 2026-10-12, HEAD `ebe34e463`) RENAMING THE IN-FLIGHT PLAN ITSELF IS A DIFFERENT HAZARD AND IS NOT COVERED. Driven: `aw rename plans p22222 --slug renamed --apply --no-commit` with `p22222`'s receipt present renamed the executing plan's file, rc 0. The receipt keys on the id6 (`receipt_path_for(repo_root, id6)`), so finalize still FINDS the receipt; the open question is whether a runner holding the old path strands. That is a source-file move, not a citation rewrite, so this plan's filter (which drops EDITS) cannot reach it; it is reported here, not fixed, and E-04 (i) pins today's behavior so a later fix is a visible change. |
| F-08 | MEDIUM | E-01 re-measurement + `filter_in_flight_plan_edits` | (execution, 2026-10-12, HEAD `09cf2ec24`) RE-MEASURED: driven against an unmodified `git archive HEAD` export of `agent_workflows`, `aw group specs` changed: True, `aw rename plans` changed: True, `aw rename research` changed: True (rc 0 each); `grep -c receipt` = 0 in `artifact_rename.py`, `plans_refs.py`, `research_refs.py`; `classify_citing_plans_for_rewrite` importable with its `(rewritable, must_skip)` shape. EXECUTION FINDING: the 5h3qyy predicate fails closed on a plan with no `- Id:`, and two existing rename tests (`test_artifact_refs_rewrite.py` c/d) cite from such a plan; dropping those would regress every legacy citing plan. Since `ipd_lifecycle.begin` refuses to bind a receipt to a plan lacking a valid id6, such a plan cannot be in flight, so the filter honors only the predicate's receipt verdict (decision 04-69pxm5-D1). |
| F-06 | LOW | `.aw/state/ipd-lifecycle/` | Live exposure is latent: the receipt directory does not exist in this authoring lane, so zero live receipts here. The guard is a cheap no-op in the common case and the defect bites only when a rename coincides with an execution. |

## Proposed changes (ordered, validatable)

1. Re-drive the reproduction and the precondition checks (E-01).
2. Add the generic in-flight edit filter reusing the 5h3qyy predicate (E-02).
3. Wire it at the four planning sites through the existing warnings channel (E-03).
4. Add CLI-driven behavior tests across all three backends (E-04).
5. Record the decision, amend the spec sentence, add the CHANGELOG line (E-05, E-06, E-07).
6. File F-07 (in-flight plan self-rename) as its own backlog item (E-08).

## Deferred / out of scope (with reason)

- **A FORCE FLAG TO REWRITE AN IN-FLIGHT PLAN ANYWAY.** Not added; see OQ-01.
  - Carrier-Declined: there is no outstanding need. A forced rewrite re-creates exactly the stranding this plan removes, and the only legitimate actor wanting it (the in-flight plan's own executor) can fix its own citation after finalize; nobody has asked for the flag.
- **`plans_archive` shard moves.** Not a rewrite path (F-04).
  - Carrier-Declined: there is nothing to guard; the module performs no reference rewrite by design.
- **Renaming or regrouping the in-flight plan ITSELF** (F-07). A file move of the executing plan, not a citation rewrite into it, so the edit filter cannot reach it, and whether it strands a lane is unmeasured. Carried by backlog `t8icgt`, filed by E-08 on 2026-10-12 replacing the interim carrier `23p80m`; its file lies outside `- Scope-Paths:` and is justified at finalize with `--scope-reason`.
  - Carrier: t8icgt
- **Repairing citations left behind by a skip.** Left to the skipped plan's own author, as D159 does for the status setters; the skip note names the file, and the stale citation surfaces through the existing dangling-citation and `check.scope-path-target-stale` checks.
  - Carrier-Declined: the work belongs to another party's in-flight plan, which the shared-checkout rule forbids editing, and the existing checks already surface it.

## Scope check

- Over-scope: none. Each declared path is written by a named E-item: `artifact_refs.py` (E-02), `artifact_rename.py`, `plans_refs.py`, `research_refs.py` (E-03), `tests/test_rename_receipt_guard.py` (E-04), `DECISIONS.md` (E-05), the plans-adopter spec (E-06), `CHANGELOG.md` (E-07). E-08 writes one new `.aw/records/backlog/` file, which cannot be named in advance (its id6 is minted); it is justified at finalize with `--scope-reason`.
- Under-scope: none known. `cli.py` is deliberately NOT declared: skip notes ride the existing `MutationResult.notes` -> `Evidence(key="notes")` path, so no CLI change is needed. The one `.aw/records/` entry, the plans-adopter spec, sits in `implemented/`, whose only onward move is `superseded/`, so a concurrent status transition staling it during this plan's execution is unlikely; if it does move, `check.scope-path-target-stale` reports it and finalize's `--scope-reason` covers the edit.

## Required tests / validation

- `python3 -m pytest tests/test_rename_receipt_guard.py tests/test_artifact_refs_rewrite.py tests/test_rename_group_machine_output.py tests/test_plans_rename_selectors.py tests/test_research_rename_frontmatter.py tests/test_plans_group_order_preservation.py` for the new and directly adjacent surfaces.
- `python3 -m pytest` run BARE (configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with the actual `N passed` summary line pasted; no added flags.
- `aw ipd lint` on this plan reporting conforming.

## Spec / documentation sync

AMENDS `.aw/records/specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md` Section 4.5 (E-06), declared in `- Scope-Paths:` so both runners announce the spec edit. WHY: that section states the regroup/rename verb works by "rewriting citations by the stable id" with no exception, and this plan adds one (a citing plan with a live begin receipt is skipped and reported). Leaving the spec unamended would make the shipped behavior contradict its own contract. The amendment is one additive sentence; no requirement is removed. No user README enumerates rename's rewrite behavior; the CHANGELOG line (E-07) is the user-facing note.

## Open questions

### OQ-01: Should a rename touching an in-flight plan skip and report, refuse, or rewrite and re-freeze?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence: skip and report. D159 (`DECISIONS.md`) already chose skip-and-report for the identical hazard on the status setters, on the measured grounds that a wrong skip leaves only a stale string while a wrong rewrite strands a lane. REFUSING the whole rename would make an unrelated maintainer action fail because of someone else's execution, which is a larger blast radius than one stale citation. REWRITE-AND-RE-FREEZE would require the rename verb to re-sign another plan's frozen contract, an authority D159 records no setter has. Consistency with D159 also means one mental model for every citation rewriter in the repo. A maintainer preferring a different posture can change it later; the choice is reversible and isolated to `filter_in_flight_plan_edits`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted dated re-measurement line in Findings plus the actual driven output for each of the three backends (the `rewrote ...` lines, the rc, and the `changed: True|False` result), the three pasted `grep -c` counts, and a pasted `python3 -c` showing `classify_citing_plans_for_rewrite` is importable from `agent_workflows.artifact_refs`. A statement that it "was re-measured" is not evidence.
  - Observed evidence: Dated line: Findings row F-08 (2026-10-12, HEAD `09cf2ec24`). Driven against an unmodified `git archive HEAD` export of `agent_workflows` (PYTHONPATH pointed at the export):
    ```text
    $ aw group specs s11111 --set newgrp --rename --apply --no-commit
    rewrote 1x '20260701-grp-01-s11111-my-spec.spec.md' -> '20260701-newgrp-01-s11111-my-spec.spec.md' in .aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md
    rewrote 1x '20260701-grp-01-s11111-my-spec.spec' -> '20260701-newgrp-01-s11111-my-spec.spec' in .aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md
    rc=0 in-flight plan changed: True
    $ aw rename plans p33333 --slug zz --apply --no-commit
    rewrote 1x [full-name] in /tmp/aw_repro69_.../.aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md
    rewrote 1x [bare-stem] in /tmp/aw_repro69_.../.aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md
    rc=0 in-flight plan changed: True
    $ aw rename research r44444 --slug zz --apply --no-commit
    rewrote 1x '20260701-seta-01-r44444-topic.reference-research.md' -> '20260701-seta-01-r44444-zz.reference-research.md' in /tmp/aw_repro69_.../...p22222-x.ipd.md
    rc=0 in-flight plan changed: True
    final: ['- Scope-Paths: 20260701-newgrp-01-s11111-my-spec.spec.md, 20260701-p33333-01-p33333-zz.ipd.md, .aw/records/research/20260701-seta-01-r44444-zz.reference-research.md']
    artifact_rename 0
    plans_refs 0
    research_refs 0
    $ python3 -c "from agent_workflows.artifact_refs import classify_citing_plans_for_rewrite as f; print(f)"
    <function classify_citing_plans_for_rewrite at 0x7e4be12a6610>
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of calling `filter_in_flight_plan_edits` directly on a scratch repo with edits targeting (i) a pending plan with a receipt, (ii) an executed plan with a receipt, (iii) a pending plan without a receipt, (iv) a non-plan file under `tests/`, showing (i) and (ii) dropped with one note each and (iii) and (iv) kept in original order; plus the same call with zero receipts showing output equal to input and no notes. Paste the function's code excerpt showing it calls `classify_citing_plans_for_rewrite` and contains no receipt-path logic of its own, and a pasted `git diff agent_workflows/artifact_refs.py` showing additions only.
  - Observed evidence: Direct call on a scratch repo (edits: (i) pending aaaaaa with receipt [two edits], (iii) pending cccccc no receipt, (ii) executed bbbbbb with receipt, (iv) tests/test_x.py):
    ```text
    ('file', 'kind', 'old', 'new', 'hits')
    no receipts: unchanged= True notes= []
    kept: ['.aw/records/plans/pending/20260701-x-01-cccccc-x.ipd.md', 'tests/test_x.py']
    --- SKIPPED citation rewrite in .aw/records/plans/pending/20260701-x-01-aaaaaa-x.ipd.md: live begin receipt present (in-flight plan; fix the citation after it finalizes) ---
    --- SKIPPED citation rewrite in .aw/records/plans/executed/20260701-x-01-bbbbbb-x.ipd.md: live begin receipt present (in-flight plan; fix the citation after it finalizes) ---
    ```
    Excerpt: liveness comes only from `_, must_skip = classify_citing_plans_for_rewrite(repo_root, list(plan_files))`; the function contains no `receipt_path_for` call. It ignores the predicate's `missing - Id:` verdict (`_CLASSIFY_MISSING_ID_REASON`), because `ipd_lifecycle.begin` refuses to bind a receipt to a plan without a valid id6 (decision 04-69pxm5-D1, Findings F-08). `git diff --numstat agent_workflows/artifact_refs.py`: `72	0` (additions only; `classify_citing_plans_for_rewrite`, `plan_reference_rewrites_with_warnings`, `apply_reference_rewrites` untouched).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff` excerpts for `artifact_rename.py`, `plans_refs.py` and `research_refs.py` showing the filter call immediately after each of the four planning calls named in E-03 and its notes appended to that site's warnings list, with no other change to those functions; plus the re-run of the E-01 reproduction after the change showing `changed: False` for all three backends and a SKIPPED line in each output (produced by the E-03 wiring through each backend's existing warnings print).
  - Observed evidence: `git diff` (excerpts): `run_rename_generic` adds, right after `plan_reference_rewrites_with_warnings(repo_root, src.name, new_name)`: `ref_edits, _in_flight_notes = _refs.filter_in_flight_plan_edits(repo_root, ref_edits)` / `warnings = list(warnings) + _in_flight_notes`; `run_group_generic` adds after the per-target loop `all_edits, _in_flight_notes = _refs.filter_in_flight_plan_edits(repo_root, all_edits)` plus de-duplicated append to `all_warnings`; `plans_refs.apply_renames` and `research_refs._apply_renames` add the same two lines after their planning call. numstat: artifact_rename 8/0, plans_refs 3/0, research_refs 3/0. Re-run of the E-01 reproduction on the changed tree:
    ```text
    $ aw group specs s11111 --set newgrp --rename --apply --no-commit
    --- SKIPPED citation rewrite in .aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md: live begin receipt present (in-flight plan; fix the citation after it finalizes) ---
    rc=0 in-flight plan changed: False
    $ aw rename plans p33333 --slug zz --apply --no-commit
    --- SKIPPED citation rewrite in .aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md: live begin receipt present (in-flight plan; fix the citation after it finalizes) ---
    rc=0 in-flight plan changed: False
    $ aw rename research r44444 --slug zz --apply --no-commit
    --- SKIPPED citation rewrite in .aw/records/plans/pending/20260701-x-01-p22222-x.ipd.md: live begin receipt present (in-flight plan; fix the citation after it finalizes) ---
    rc=0 in-flight plan changed: False
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the pasted targeted run of `tests/test_rename_receipt_guard.py` showing it passing, with behaviors (a) through (i) each mapped to a named passing test (names non-binding); the pasted targeted run of the adjacent test modules listed under Required tests; and the pasted BARE `python3 -m pytest` summary line. Quote the assertions showing the tests check exit codes, stdout and file bytes only and never read production source (P16).
  - Observed evidence: Targeted run (`python3 -m pytest -o addopts="" -v tests/test_rename_receipt_guard.py`): test_a_group_specs_skips_in_flight_plan (a), test_b_rename_plans_skips_in_flight_plan (b), test_c_rename_research_skips_in_flight_plan (c), test_d_citation_in_action_block_is_also_left_unchanged (d), test_e_non_plan_citing_file_still_rewritten (e), test_f_preview_reports_skip_and_no_would_rewrite_for_in_flight (f), test_g_no_receipt_means_plan_is_rewritten (g), test_h_machine_output_carries_skip_note (h), test_i_renaming_the_in_flight_plan_itself_still_succeeds (i): all PASSED, `9 passed in 1.42s`. Adjacent modules: `74 passed in 13.78s`. Bare suite `python3 -m pytest`: first run `39 failed, 7183 passed, 2 skipped` - all 39 in non-project/temp-dir tests (test_no_project_exit_is_cannot_run, test_explicit_dir_non_project, ...) failing because a stray `/tmp/.aw` project tree (44 leaked `e2e-test-plan` files, not from this lane) makes every `/tmp` scratch dir resolve "inside an AW project"; the same 40 failed on an unmodified HEAD export too. With a clean temp root: `TMPDIR=/var/tmp python3 -m pytest` -> `7222 passed, 2 skipped, 3 warnings in 253.57s (0:04:13)`. Assertions use only rc, stdout and bytes: `self.assertEqual(rc, 0, out)`, `self.assertFalse(self._changed(self.in_flight), out)`, `self.assertIn(SKIP_MARK, out)`, `agent_schema.assert_valid_agent_record(rec)`, `self.assertTrue(any(SKIP_MARK in n for n in data["data"]["notes"]), data)`; the module reads no production source.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `git diff DECISIONS.md` showing additions only, exactly one new `### D<n>` entry with Context, Decision (rejected alternatives and trade-off) and Applied bullets citing D159, F-01 and F-02; plus pasted evidence of the re-derived `<n>` (the highest existing `### D` heading before the edit) showing no collision.
  - Observed evidence: Highest heading before the edit: `2651:### D162. Command exit_contract ...`; `grep -c '^### D163'` was 0 before, 1 after (`2665:### D163. Rename/regroup citation rewriting skips and reports in-flight plans`). `git diff --numstat DECISIONS.md`: `10	0`, zero removed lines. The entry has Context (cites F-01), Decision (whole-file skip per F-02, reuse of the D159 predicate, two rejected alternatives: refuse / rewrite-and-re-freeze, and a Trade-off citing D159), and Applied.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted `git diff` of the plans-adopter spec showing exactly one added sentence in Section 4.5 citing the E-05 decision number, no removed lines, and an unchanged `- Status:` line.
  - Observed evidence: `git diff --numstat` on the spec: `1	1` (one physical line re-wrapped); word diff shows only the inserted sentence `A citing plan holding a live begin receipt is NOT rewritten; the skip is reported and the citation is left for that plan's author to fix after it finalizes (decision D163).` placed after "citations by the stable id."; `- Status: implemented` (line 4) unchanged and absent from the diff.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added `Fixed:` bullet under the existing `## 2.0.0 (pending)` heading, no other change, and no em or en dash in the added line.
  - Observed evidence: `git diff CHANGELOG.md`: one added line, inserted at the top of the `## 2.0.0 (pending)` Fixed bullets: `+- Fixed: aw rename and aw group no longer rewrite citations inside a plan that is mid-execution (one holding a begin receipt), so renaming an artifact can no longer strand that plan at finalize; each skipped plan is reported instead.` numstat `1	0`; dash count in added line: `0`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the pasted re-run of F-07's reproduction (rc and resulting file names); the pasted `aw backlog new` output naming the new id6 and the new file's front matter (`- Work-Kind:`, `- Blocks-Release:` or exemption); and the pasted F-07 deferred row showing `- Carrier: <new id6>`. Or, if already guarded, the pasted reproduction showing the refusal.
  - Observed evidence: F-07 re-run: test_i (`aw rename plans p22222 --slug renamed --apply --no-commit` with p22222's receipt present) rc 0, old file gone, `20260701-x-01-p22222-renamed.ipd.md` exists: still unguarded. `aw backlog new ... --apply` -> `aw backlog new: wrote .../.aw/records/backlog/open/20261012-t8icgt-01-t8icgt-renaming-an-in-flight-plan-s-own-file-while-its-be.backlog.md`; front matter: `- Id: t8icgt`, `- Status: open`, `- Blocks-Release: next`, `- Priority: low`, `- Work-Kind: bug`. Deferred row now reads `- Carrier: t8icgt (filed by E-08 on 2026-10-12, ...)`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires `/plan-review` and explicit human approval before execution.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`. Ownership of the transition is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`, so the executor commits its work and leaves the move to the runner; executing BY HAND, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit the status or `git mv` the file. SCOPE FENCE: an edit outside `- Scope-Paths:` that proves necessary is made and then justified with `aw ipd finalize --scope-reason`, never silently.

A NOTE ON THIS PLAN'S OWN EXECUTION: E-01 and the tests build their scratch repositories under the system temp directory, never inside the checkout, and write receipts only there, so no real `.aw/state/ipd-lifecycle/` receipt is created or touched.
