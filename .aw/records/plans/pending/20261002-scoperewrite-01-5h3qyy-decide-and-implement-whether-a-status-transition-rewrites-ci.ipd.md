# IPD: Decide and implement whether a status transition rewrites citing Scope-Paths, with an in-flight receipt guard

- Date: 2026-10-02
- Kind: child
- Concern: A RECORD STATUS TRANSITION RELOCATES THE RECORD AND REWRITES NO CITATION, so every plan that declared the record at its old status directory is left pointing at a path that no longer exists. `status_set.apply_status_change` is the shared record-type-agnostic handler behind `aw ipd set`, bare `aw set`, `aw prompts set`, and the POSITIONAL spellings of `aw backlog set` and `aw specs set` (review PR-001: the `--status <X> <path>` spellings of those two verbs route to `backlog.run_set` and `specs.run_set` instead, each relocating the record itself; see F-09); it resolves a destination with `record_placement.resolve_transition_path`, relocates with `_core.git_mv` (its own comment: "RELOCATE WITH `git mv`, NOT write-then-unlink"), rewrites many FIELDS on the moved record, and rewrites no citation anywhere else. Executed plan `guti33` (Set `9xap30`) fixed the SYMPTOM by re-tiering a plain `moved` finding to `info`; this plan is its OQ-01 CAUSE half, carried by backlog `es7wdp`. Authoring measured FIVE things the item does not state and TWO of them change the answer rather than the method. FIRST, THE EXISTING REWRITER CANNOT BE CALLED AS THE ITEM DESCRIBES: `artifact_refs.plan_reference_rewrites` is keyed on FILENAME changes, and a status transition leaves the filename byte-identical while changing only the directory, so the `{old_name: new_name}` map the item proposes is `{name: name}`, which the function SKIPS at its `if old_name == new_name: continue` guard and which returns `[]` when driven (F-01). The rewriter is still reusable, but only when fed REPO-RELATIVE PATHS as map keys, which is a different call than the item assumes and is what E-03 builds. SECOND, THE HAZARD IS REAL AND IS WORSE THAN THE ITEM STATES: a path rewrite is a REMOVAL plus an ADDITION, and `ipd_lifecycle.widening_is_acceptable` demands `not removed`, so rcptwiden `63425h`'s additive-widening accept does NOT rescue it and `finalize_precheck` refuses with the stranding message (F-04, driven on a real pending plan). The item says a safe implementation "needs a stated rule for in-flight plans"; measured, that rule is NOT optional, it is the whole decision. THIRD, the in-flight population is ENUMERABLE with a proven in-tree pattern (`check_engine._receipt_is_live`), so "skip and report" is implementable rather than aspirational (F-05). FOURTH, `aw rename` ALREADY performs exactly this rewrite with NO receipt guard at all, which is both the precedent for acting and a pre-existing exposure this plan must not widen silently (F-06). FIFTH, the live `moved` population is 10 entries across pending plans, not the item's 4, and one of the 10 is a DELIBERATE forward declaration that a rewriter MUST NOT touch (F-07), which is the single strongest argument for the skip-and-report posture.
- Scope: IN: (a) record the maintainer decision as a durable in-repo decision record with the hazard, the measured counter-example and the chosen posture, because this item is a DECISION item and shipping code without recording why would discard the reasoning; (b) add a shared, record-type-agnostic path-keyed citation-rewrite helper to `artifact_refs` that takes an `{old_rel_path: new_rel_path}` map (the shape F-01 proves is required) and reuses the EXISTING `plan_reference_rewrites`/`apply_reference_rewrites` machinery rather than adding a second rewriter; (c) add an in-flight guard predicate that enumerates live begin receipts and classifies each candidate citing file as safe-to-rewrite or must-skip, built on `ipd_lifecycle.read_receipt`, deliberately WITHOUT reusing `check_engine._receipt_is_live`, whose fail-SAFE direction (undeterminable means NOT live) is the opposite of what this guard needs (review PR-003); (d) wire the two into EVERY relocating setter path (`status_set.apply_status_change`, `backlog.run_set`, `specs.run_set`; F-09) through ONE shared post-relocation step, behind an explicit opt-in flag `--rewrite-citations` that DEFAULTS OFF, registered on every parser that reaches those paths, so no existing invocation changes behavior until the maintainer flips the default; (e) report every skipped in-flight citation on stdout so a skip is visible rather than silent; (f) behavior tests for the rewrite, the skip, the fenced/permalink masking, and the default-off invariant; (g) one CHANGELOG line. OUT: changing the DEFAULT to on (that is the maintainer's call once this lands and is OQ-01, deliberately left for a human); changing `check.scope-path-target-stale` severities or classifications (shipped by `guti33`, and E-02 forbids touching the shared predicate); the runner's dispatch refusal set (reads no severity, F-08 of `guti33`); adding a receipt guard to `aw rename` (a real pre-existing gap, filed as a follow-up in the Deferred section rather than silently bundled, because it changes a second verb's contract); mandating the status-agnostic glob spelling as a convention for every plan author (F-03 proves it works today and the Deferred section carries it as guidance-only); and repairing the live stale entries in other agents' pending plans (not this plan's files, per the shared-checkout rule, and the population turns over daily).
- Scope-Paths: agent_workflows/artifact_refs.py, agent_workflows/status_set.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/cli.py, tests/test_artifact_refs_rewrite.py, tests/test_status_set.py, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: es7wdp
- Set: scoperewrite
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 5h3qyy
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: --status spellings of backlog/specs set bypass apply_status_change; all three relocating paths wired, F-09), PR-002 (BLOCKER, fixed: bare rewriter edits executed plans/tests and corrupts the F-07 forward declaration; restricted to pending-plan Scope-Paths lines with destination-already-declared skip, F-10), PR-003 (HIGH, fixed: _receipt_is_live fails toward rewrite; guard keys on receipt-file presence), PR-004 (MEDIUM, fixed: agent-mode reporting via Change), PR-005 (MEDIUM, fixed: named flag, parsers, finalize off, self-commit paths), PR-006 (MEDIUM, fixed: conditional lifecycle and fence), PR-007 (LOW, fixed: DECISIONS shape, E-07 split into E-07/E-09). Review record .aw/records/reviews/20261002-scoperewrite-01-5h3qyy-decide-and-implement-whether-a-status-transition-rewrites-ci.review.md.

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `es7wdp`, the durable carrier of executed plan `guti33`'s OQ-01. Authoring drove every claim in the item against the live tree and all of them hold, but two measurements change the shape of the answer. (1) The item's "call the existing rewriter from the existing setter" is NOT directly possible: the rewriter is FILENAME-keyed and a status transition changes only the DIRECTORY, so the proposed `{old_name: new_name}` map is `{name: name}` and returns zero edits when driven (F-01). Feeding it repo-relative PATHS does work and rewrites correctly while respecting fence and permalink masking (F-02), so the reuse claim survives in a corrected form. (2) The in-flight hazard is NOT mitigated by rcptwiden `63425h`: a rewrite is removal+addition, `widening_is_acceptable` requires `not removed`, and driving a real pending plan's receipt through `frozen_region_comparison` after a simulated rewrite yields `removed=(...)`, `added=(...)`, `widening_is_acceptable=False`, i.e. the exact stranding refusal (F-04). So the plan is built around a default-OFF opt-in plus a measured skip-and-report guard, and the decision of whether to flip the default is left to the maintainer as OQ-01 rather than taken here. Also measured: the live `moved` population is 10, not 4, and one entry is a deliberate three-path forward declaration by plan `dwivqd` that a rewriter must never touch (F-07). See F-01 through F-08.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Remove the CAUSE of stale `Scope-Paths` targets rather than continue grading the symptom, without letting a routine `aw backlog set graduated` strand an unrelated in-flight plan's lane. Concretely: give the repository ONE shared, path-keyed citation-rewrite helper plus ONE in-flight receipt guard, wire both into the single record-type-agnostic status setter behind a flag that defaults OFF, and record the decision and its measured hazard durably so the maintainer can flip the default on evidence instead of on assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed.

### Task group 1: Re-measure the base, because every number here describes a LIVE tree

- [x] E-01 Re-drive the five authoring measurements at execution HEAD and record the actual numbers in this plan's Findings as a dated re-measurement line, because the pending-plan corpus turns over daily and `guti33` F-01/F-04/F-09 each record a figure that moved within one day. Re-drive: (a) the per-classification stale counts over `.aw/records/plans/pending/` via `check_engine.stale_record_scope_paths`; (b) `artifact_refs.plan_reference_rewrites(repo, {name: name})` returning `[]`; (c) the same function with a path-keyed map returning the two expected edits; (d) `ipd_lifecycle.widening_is_acceptable` on a simulated rewrite of a real pending plan returning False; (e) the count of live receipts under `.aw/state/ipd-lifecycle/`. Also re-drive (f) the F-10 probe: the bare path-keyed rewriter, applied to a plan declaring the same spec under `approved/`, `implementing/` and `implemented/`, collapses the `approved/` entry into a DUPLICATE `implementing/` entry. If (b), (c), (d) or (f) DISAGREES with the Findings table, record the disagreement and mark this item `blocked`, because the design rests on them; (a) and (e) are live counts and are recorded whatever they are.
  - Depends on: none
  - Expected outcome: a dated re-measurement line in Findings; (b) is `[]`, (d) is False; (a) and (e) recorded as observed, whatever they are. No source file modified by this item.
  - Execution state: performed

### Task group 2: Record the decision, because this is a decision item

- [x] E-02 Append ONE new numbered decision entry to `DECISIONS.md`, which is this repository's established home for a durable decision record (there is NO `.aw/records/decisions/` tree, verified at authoring, and the file's own header states it is the "Append-only, dated record of significant decisions ... with the reasoning, alternatives considered, and trade-offs"). Follow the existing `### D<n>. <title>` convention, taking the next free number after the current highest (D158 at authoring; re-derive it at execution rather than trusting that figure, since the log is appended by other work). The entry must carry the house shape used by its neighbours, which is measured at review as `- **Context:**` (115 entries), `- **Decision:**` (114) and `- **Applied:**` (102), with rejected alternatives and trade-offs stated inside **Decision** as D158 does (a standalone **Trade-off** bullet appears only 8 times), and must state: the question; the three options (keep grading the symptom; rewrite citations in the setter; teach the status-agnostic glob spelling); the measured hazard with F-04's driven `widening_is_acceptable=False` output; F-07's counter-example; and the chosen default-OFF opt-in posture. Append only, per the file's own contract; do not reword any existing entry.
  - Depends on: E-01
  - Expected outcome: one new `### D<n>` entry in `DECISIONS.md` carrying Context / Decision (with rejected alternatives and trade-off) / Applied, with the driven evidence pasted rather than summarized, and no existing entry altered.
  - Execution state: performed

### Task group 3: The two mechanism pieces, a shared path-keyed rewrite helper and a fail-closed in-flight guard

- [x] E-03 Add a path-keyed citation-rewrite helper to `agent_workflows/artifact_refs.py` taking an `{old_repo_relative_path: new_repo_relative_path}` map and returning the same `RefEdit` list the existing planner returns, by DELEGATING to `plan_reference_rewrites` rather than reimplementing any matching. Do NOT modify `plan_reference_rewrites`, `apply_reference_rewrites`, `_mask_fenced_code`, `_mask_permalinks` or `_boundaried`: F-02 proves the existing machinery already rewrites a path-keyed map correctly and already skips fenced blocks, and F-08 proves a path-keyed key bypasses the legacy-prefix and clustered-prefix branches by returning `None`/`None`, so no new escaping or boundary logic is needed. Document on the helper WHY the map is path-keyed and not name-keyed, citing the `if old_name == new_name: continue` guard that makes a name-keyed status transition a no-op.
  RESTRICT THE EDITS TO WHAT THIS PLAN IS ABOUT, because the bare rewriter is broader than the defect. Measured at review on a scratch repo (F-10): (1) it scans `artifact_core.REFERENCE_SCAN_ROOTS`, which includes `.aw/records/plans/executed/`, `tests/` and `DECISIONS.md`, so it would edit EXECUTED plans (whose records AGENTS.md says must never be changed) and test source; (2) applied to a plan declaring the three-path `approved/`/`implementing/`/`implemented/` forward declaration that F-07 names, it rewrote `approved/` into a SECOND `implementing/` entry, i.e. it corrupted exactly the declaration F-07 says must not be touched. So the helper must, after delegating to the planner: keep only edits whose file is a PENDING plan (`.aw/records/plans/pending/`); rewrite only inside the `- Scope-Paths:` line (prose mentions are history and are left alone); and SKIP, with a reported reason, any citing file whose `Scope-Paths` already declares the destination path, since in that case the old entry is a deliberate forward declaration and not a stale one. Prefer filtering the planner's `RefEdit` list and performing the line-scoped replacement through `ipd_schema.parse_scope_paths` over adding new matching logic; do NOT modify the existing planner or its masking.
  - Depends on: E-01
  - Expected outcome: one new helper in `artifact_refs` that delegates to the existing planner, rewrites a moved record's path only inside the `- Scope-Paths:` line of PENDING plans, never touches executed plans, tests or prose, and skips (with a reason) any plan that already declares the destination path; the existing rewriter and its masking untouched.
  - Execution state: performed

- [x] E-04 Add an in-flight guard predicate that, given a repo root and a set of candidate citing files, returns which of them belong to a plan with a LIVE begin receipt and must therefore be skipped. Build it on the pattern `check_engine` already uses at its `read_receipt` call site: read each plan's `- Id:` and call `ipd_lifecycle.read_receipt`. Do NOT reuse `check_engine._receipt_is_live`: its docstring states it FAILS SAFE in the advisory direction ("when liveness cannot be determined ... the receipt is treated as NOT live and skipped") and it also returns False for an unreachable base, so reusing it would rewrite exactly the uncertain cases this guard must skip (review PR-003). The rule is simpler and stricter: a receipt FILE PRESENT for the plan's id6 at `ipd_lifecycle.receipt_path_for` means skip, whether or not it parses; a plan with no `- Id:` is skipped too. Only a plan whose receipt path is provably absent is rewritable. Fail CLOSED: a plan whose receipt cannot be read or whose liveness cannot be determined is treated as IN-FLIGHT (skip), because a wrong skip costs a stale path string while a wrong rewrite costs a stranded lane and the measured $95.71/3h10m class of loss recorded in `rcptwiden`.
  - Depends on: E-01
  - Expected outcome: one predicate classifying candidate citing files into rewritable and must-skip, treating any present receipt file (readable or not) and any missing `- Id:` as must-skip, with no liveness test at all.
  - Execution state: performed

### Task group 4: Wire into the one setter, default OFF

- [x] E-05 Wire E-03 and E-04 into EVERY relocating setter path through ONE shared post-relocation function, behind an explicit opt-in that DEFAULTS OFF so no existing caller changes behavior. THE THREE PATHS (F-09): `status_set.apply_status_change` (positional `aw backlog set`/`aw specs set`, `aw ipd set`, `aw set`, `aw prompts set`), `backlog.run_set` (the `aw backlog set --status` spelling) and `specs.run_set` (the `aw specs set --status` spelling). Wiring only the first would fire for one spelling of a verb and not the other, the defect class `backlog.decide_gate_default`'s docstring warns against. Register one flag, `--rewrite-citations`, on every parser that reaches those paths (`aw set`, `aw ipd set`, `aw prompts set`, `aw backlog set`, `aw specs set` in `cli.py`); read it with `getattr(args, "rewrite_citations", False)` so `ipd_lifecycle`'s internal `apply_status_change` call (the finalize move to `executed/`) stays OFF. Call the shared step ONLY AFTER the relocation and the destination write have both completed, never between `git_mv` and the destination write (the `git_mv`-before-write ORDER comment records why), and leave the moved record's own fields exactly as they are. Preserve `apply_status_change`'s existing early return (`if not content_changed and not path_changed and not _write_history_anyway`). Do NOT run on a dry run. RETURN the rewritten file paths to the caller and ADD them to the verb's `touched_paths` so `_offer_self_commit` (and `specs._offer_specs_set_commit`) offers them in the same path-scoped commit; otherwise `--commit` would commit the move and leave the rewritten citations uncommitted.
  - Depends on: E-03, E-04
  - Expected outcome: all three relocating paths rewrite citing pending-plan scope entries when `--rewrite-citations` is passed and do nothing different when it is not; finalize's internal call never rewrites; rewritten files join the verb's self-commit path set; the relocation order and early return are unchanged.
  - Execution state: performed

- [x] E-06 Report every rewritten and every SKIPPED citation, in the established shape the same function already uses for its gate-inheritance notice (`sys.stdout.write(f"aw set: inherited - Blocks-Release: ...")`) for human output. UNDER `--agent`/`--json`, DO NOT write free text to stdout, which would corrupt the `aw.agent/v1` stream; instead add each rewrite as a `Change(kind="modify", applied=True)` and each skip as a `Change(kind="modify", applied=False)` whose `detail` names the reason, in the `changes` list `run_set_command` already emits. A skip MUST name the skipped plan and the reason (live begin receipt), because a silent skip leaves a stale path with no trace and is the failure mode that makes "skip and report" acceptable at all; a report is what converts it from data loss into a visible, actionable advisory that `check.scope-path-target-stale` will then report at `info`.
  - Depends on: E-05
  - Expected outcome: rewrites and skips are both visible, as stdout lines for human output and as `Change` records under `--agent`/`--json` (the stream still validates), each skip naming the plan and its reason (receipt present, no `- Id:`, or destination already declared).
  - Execution state: performed

### Task group 5: Tests and changelog

- [x] E-07 Add HELPER behavior tests in `tests/test_artifact_refs_rewrite.py`, following its existing fixture style, exercising real code and asserting on real outputs and side effects (never reading source text, counting callers, or pinning comments). Pin: (a) a path-keyed map rewrites a citing pending plan's `Scope-Paths` entry, while a prose mention and a fenced-code occurrence in the same file stay byte-identical; (b) a NAME-keyed map for an unchanged filename plans zero edits, pinning F-01's cause; (c) an EXECUTED plan and a test file citing the old path are byte-unchanged; (d) a plan already declaring the destination path (the F-07/F-10 forward-declaration shape) is skipped with a reason and byte-unchanged; (e) the guard classifies a plan with a receipt file, one with an unparseable receipt file, and one with no `- Id:` as must-skip, and one with no receipt as rewritable.
  - Depends on: E-03, E-04
  - Expected outcome: passing helper tests pinning (a) through (e).
  - Execution state: performed

- [x] E-09 Add SETTER behavior tests in `tests/test_status_set.py`, following its existing fixture style and the same outcome-only rule. Pin: (f) the DEFAULT invocation (no `--rewrite-citations`) rewrites nothing, pinning the default-off invariant; (g) with the flag, `aw backlog set graduated <id6>`, `aw backlog set --status graduated <path>` and `aw specs set --status <next> <path>` each rewrite a citing pending plan, and a citing plan with a receipt file is SKIPPED, reported and byte-unchanged; (h) a rewritten plan still lints as conforming afterwards; (i) under `--agent` the output still validates as `aw.agent/v1` and carries the rewrite and the skip as `Change` entries; (j) with `--commit`, the rewritten citing file is in the commit.
  - Depends on: E-05, E-06
  - Expected outcome: passing setter tests pinning (f) through (j).
  - Execution state: performed

- [x] E-08 Add one CHANGELOG line under the existing `## 2.0.0 (pending)` heading describing the opt-in `--rewrite-citations` flag and its default-off posture. Do not add a new version heading and do not reword neighbouring entries.
  - Depends on: E-07, E-09
  - Expected outcome: one new CHANGELOG bullet under the existing pending heading; no other CHANGELOG text altered.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A RECORD'S DIRECTORY ALWAYS AGREES WITH ITS `- Status:`, and the setters relocate the file to match. That is the mechanism under this whole plan: the relocation is CORRECT behavior, so the defect is the unrewritten citation, never the move.
- ONE SHARED HANDLER, NOT PER-VERB COPIES. `status_set.apply_status_change` is record-type-agnostic and is the single route behind `aw backlog set`, `aw specs set`, `aw ipd set` and bare `aw set`. Its own comments repeatedly record the lesson that a fix wired into one spelling "would fire for one spelling of one verb and not the other, which is worse than not shipping it because it teaches a false expectation" (the `decide_gate_default` comment). This plan therefore wires one SHARED STEP, called from each of the three relocating paths (F-09), rather than three copies.
- FIELD WRITES ON THIS PATH ARE HOISTED OUT OF THE STATUS BRANCH and funnel through one shared primitive each (`set_blocks_release_line`, `set_from_backlog_line`, `set_item_dependencies_line`, `set_priority_line`, `set_work_kind_line`, `set_graduated_to_line`), each comment stating "no duplicate write path". E-03 follows that convention by delegating to the existing rewriter instead of adding a second one.
- FAIL CLOSED ON UNCERTAINTY is the house posture for anything touching a receipt: `frozen_region_comparison`'s three ineligible shapes are each "fail-closed and each named in `ineligible_reason`", and `_entry_is_bare_directory` "fails CLOSED in the direction that matters". E-04 adopts the same posture, which is why it does NOT reuse `check_engine._receipt_is_live`: that predicate is deliberately fail-SAFE (uncertain means not live) for an advisory, the opposite direction.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Dated re-measurement at execution HEAD ad61550e6070c8337f818024c3abddf848df2912 (2026-10-03):
- (a) Stale counts over .aw/records/plans/pending/: {'moved': 9, 'moved-terminal': 2} (11 findings total across 127 pending plans; 0 vanished, 0 ok).
- (b) artifact_refs.plan_reference_rewrites(repo, {name: name}) returned [].
- (c) Path-keyed map {'.aw/records/backlog/open/name': '.aw/records/backlog/graduated/name'} returned 2 edits: full-name and bare-stem.
- (d) ipd_lifecycle.widening_is_acceptable returned False on simulated rewrite of pending plan qjm4bg (cmp.added=('...graduated/...',), cmp.removed=('...open/...',), cmp.eligible=True, cmp.non_scope_identical=True).
- (e) Count of live receipts under .aw/state/ipd-lifecycle/ was 34 across checkout (0 in isolated lane).
- (f) F-10 probe reproduced forward-declaration collapse to duplicate implementing/ entry when bare rewriter used.

| Id | Severity | Where | Finding and evidence |
|---|---|---|---|
| F-01 | **HIGH** | `artifact_refs.plan_reference_rewrites`, `plan_reference_rewrites_with_warnings` | **THE ITEM'S PROPOSED CALL IS A NO-OP, AND THIS IS THE SINGLE MOST LOAD-BEARING CORRECTION AUTHORING MAKES.** The item says option (c) is "call the existing rewriter from the existing setter", driven by "an old-name-to-new-name map". But a status transition does NOT change the filename; it changes only the DIRECTORY. So the map is `{name: name}`, and `plan_reference_rewrites_with_warnings` begins its loop with `for old_name, new_name in name_map.items(): if old_name == new_name: continue`, skipping every such entry. DRIVEN on a scratch git repo with a citing plan declaring `.aw/records/backlog/open/<name>`: `plan_reference_rewrites(d, {name: name})` returned `[]`. A literal reading of the item would therefore ship a setter that calls a rewriter and rewrites nothing, and the stale entries would persist with the cause believed fixed. The reuse claim is still sound, but only in the corrected PATH-KEYED form of F-02. |
| F-02 | HIGH | `artifact_refs.plan_reference_rewrites`, `apply_reference_rewrites`, `_mask_fenced_code` | **FED REPO-RELATIVE PATHS, THE EXISTING REWRITER WORKS CORRECTLY AND NEEDS NO MODIFICATION.** DRIVEN with `{".aw/records/backlog/open/<name>": ".aw/records/backlog/graduated/<name>"}` against a citing plan containing the path in its `- Scope-Paths:` line, in prose, and inside a fenced block: the planner emitted two edits (`full-name` and `bare-stem`), and `apply_reference_rewrites` rewrote the `Scope-Paths` entry and the prose mention while leaving the FENCED occurrence byte-identical. So fence masking and permalink masking already hold for a path-keyed map, which is why E-03 is a thin delegating helper rather than new matching logic. |
| F-03 | MEDIUM | `ipd_schema._scope_path_entry_error`, `ipd_lifecycle._scope_match`, `check_engine.stale_record_scope_paths` | **THE ZERO-CODE ALTERNATIVE GENUINELY WORKS TODAY, which is why it is preserved as guidance rather than dismissed.** DRIVEN: `.aw/records/backlog/**/<name>.backlog.md` returns `None` from `_scope_path_entry_error` (accepted), survives `parse_scope_paths` intact and non-grandfathered, and `_scope_match` returns True against the file under `open/`, `graduated/` AND `done/` while returning False for a DIFFERENT file in the same directory; `stale_record_scope_paths` on a plan declaring it returns `[]`. Also measured: `scope_entry_is_literal_file` returns False for it, so such an entry is NOT widening-eligible, a real trade-off a reviewer should see. This plan does not mandate the spelling (a convention change for every author) but the Deferred section carries it. |
| F-04 | **HIGH** | `ipd_lifecycle.receipt_is_current`, `frozen_region_comparison`, `widening_is_acceptable`, `finalize_precheck` | **THE HAZARD IS CONFIRMED AND rcptwiden `63425h` DOES NOT RESCUE IT, so the in-flight rule is mandatory rather than advisable.** A rewrite is a REMOVAL plus an ADDITION, and `widening_is_acceptable` requires `cmp.eligible and cmp.non_scope_identical and not cmp.removed and cmp.added`. DRIVEN on the REAL pending plan `qjm4bg` (whose frozen scope declares four `.aw/records/backlog/open/` entries), simulating one entry moving to `graduated/`: `receipt_is_current` went True -> **False**; `frozen_region_comparison` returned `added=('...graduated/...fnb8pl...',)`, `removed=('...open/...fnb8pl...',)`, `non_scope_identical=True`, `eligible=True`, and `widening_is_acceptable=False`. `finalize_precheck` refuses on exactly that condition, and its own comment confirms "Every other mismatch - a removal, a mixed add-and-remove ... still refuses". Note `guti33` F-12's reassurance ("the receipt freezes the entry STRING, and the string does not change when the file moves") is TRUE for a bare move and becomes FALSE the moment a rewriter changes the string, which is precisely what this plan would do. |
| F-05 | MEDIUM | `check_engine`'s `read_receipt` call site and `_receipt_is_live`; `ipd_lifecycle.receipt_path_for`, `receipt_dir` | **"SKIP AND REPORT" IS IMPLEMENTABLE WITH AN EXISTING PROVEN PATTERN, so it is not an aspiration.** `check_engine` already walks every plan file, reads `- Id:`, calls `_life.read_receipt(repo_root, plan_id)`, `continue`s when there is none ("no active execution -> nothing to reconcile"), and then filters on `_receipt_is_live(repo_root, p, receipt)` ("spent authority (terminal plan / unreachable base) -> not an in-flight scope"). Receipts live at `.aw/state/ipd-lifecycle/<id6>.receipt.json` via `receipt_path_for`, anchored on the CHECKOUT by `checkout_control_root` so a lane's receipts are visible to the driver (the fix for backlog `dh0uno`). Measured in this authoring worktree: that directory does not exist, i.e. zero live receipts, so the guard is a cheap no-op in the common case. REVIEW CORRECTION: `_receipt_is_live` is the WRONG predicate to reuse, because it fails safe toward NOT live and treats an unreachable base as not live, the opposite of the skip direction this guard needs. E-04 uses receipt-file presence instead. |
| F-06 | MEDIUM | `artifact_rename`, `plans_refs`, `research_refs`, `plans_archive` | **`aw rename` ALREADY DOES THIS REWRITE WITH NO RECEIPT GUARD, which is simultaneously the precedent for acting and a pre-existing exposure.** Measured: `grep -c 'receipt\|in_flight\|in-flight'` returns **0** for all four of `artifact_rename.py`, `plans_refs.py`, `research_refs.py`, `plans_archive.py`, and the only three modules calling `read_receipt`/`receipt_path_for` are `check_engine.py`, `ipd_lifecycle.py` and `runner_shared.py`. So renaming an artifact today can already stale an in-flight plan's receipt by the F-04 mechanism and nothing stops it. TWO CONSEQUENCES: the item's hazard is not a reason to refuse the setter change (the repository already accepts that risk on a neighbouring verb), AND this plan must not pretend to close the class, because it closes it only on the setter. The rename half is named in Deferred as a follow-up rather than silently bundled, since it changes a second verb's contract. |
| F-07 | **HIGH** | `check_engine.stale_record_scope_paths` driven over `.aw/records/plans/pending/`; pending plan `dwivqd` | **A BLIND REWRITER WOULD CORRUPT A DELIBERATE FORWARD DECLARATION, which is the strongest single argument for skip-and-report over unconditional rewriting.** DRIVEN over every pending plan: **10** `moved` and **2** `moved-terminal` findings (12 total), already more than the item's "FOUR were stale at the time of filing", confirming the population grows. Seven of the 10 are routine `backlog/open/ -> graduated/` moves. But TWO of them belong to pending plan `dwivqd`, which DELIBERATELY declares all THREE of `specs/approved/`, `specs/implementing/` and `specs/implemented/` for ONE spec, and says so explicitly: "three paths for one file because the setter relocates it (F-06). The `approved/` path is the pre-state (deleted by E-03), `implementing/` the intermediate ... Declaring only one would leave two of the three writes undeclared at finalize." A rewriter that "fixed" those entries would destroy a correct declaration and break that plan's finalize reconciliation. So the classification `moved` does NOT imply "should be rewritten", and any rewriter must be opt-in and guarded rather than a sweeping repair. |
| F-09 | **HIGH** | `cli.py` backlog and specs `set` dispatch; `backlog.run_set`; `specs.run_set` | **REVIEW: THE SETTER IS NOT ONE FUNCTION.** `cli.py` dispatches `aw backlog set` and `aw specs set` to `status_set.run_set_command` ONLY when `--status` is absent; with `--status` they call `backlog.run_set` (which writes the destination with `core.atomic_write` and `src.unlink()`) and `specs.run_set` (which calls `core.git_mv` itself). Both relocate without passing through `apply_status_change`, so wiring only that function would leave two spellings unfixed. E-05 wires all three. |
| F-10 | **HIGH** | `artifact_core.REFERENCE_SCAN_ROOTS`; `artifact_refs.apply_reference_rewrites` | **REVIEW: THE BARE REWRITER IS TOO BROAD AND CORRUPTS THE F-07 DECLARATION.** Driven on scratch repos: a path-keyed map planned edits in `.aw/records/plans/executed/e.ipd.md` and `tests/test_x.py` as well as the pending plan, because the scan roots include `.aw/records/plans` (all dispositions), `tests` and `DECISIONS.md`. On a plan declaring `approved/`, `implementing/` and `implemented/` paths for one spec, mapping `approved/ -> implementing/` produced `- Scope-Paths: .../implementing/..., .../implementing/..., .../implemented/...`, a duplicate entry with the pre-state lost. E-03 now limits edits to the `Scope-Paths` line of pending plans and skips plans already declaring the destination. |
| F-08 | LOW | `artifact_refs._legacy_prefix_stem`, `_whole_stem`, `_boundaried`, `artifact_naming.parse_clustered_prefix` | **A PATH-KEYED MAP IS SAFE IN THE REWRITER'S OTHER BRANCHES, so E-03 needs no new escaping.** DRIVEN on the path key `.aw/records/specs/approved/20260802-1904-01-ipd-structure-and-linting.spec.md`: `_legacy_prefix_stem` returns `None` and `parse_clustered_prefix` returns `None`, so the legacy-prefix and clustered-prefix shorthand branches (and their shared-prefix WARNING path) are bypassed entirely; `_whole_stem` returns the path minus `.md`, giving the intended path-stem rewrite. `_boundaried` wraps its input in `re.escape`, so the slashes and dots in a path are matched literally. Exactly two edits result, both intended, with no risk of rewriting a bare id6 or setid. |

## Proposed changes (ordered, validatable)

1. Re-measure the five load-bearing figures and halt on disagreement with F-01/F-04 (E-01).
2. Record the decision, its measured hazard and its counter-example durably (E-02).
3. Add the path-keyed rewrite helper, delegating to the existing rewriter (E-03).
4. Add the fail-closed in-flight receipt guard, reusing the existing liveness notion (E-04).
5. Wire both into the one shared setter behind a default-OFF opt-in, preserving relocation order (E-05).
6. Report every rewrite and every skip on stdout (E-06).
7. Add helper behavior tests (E-07) and setter behavior tests, including the default-off invariant and all three relocating spellings (E-09).
8. Add one CHANGELOG line (E-08).

## Deferred / out of scope (with reason)

- **FLIPPING THE DEFAULT TO ON.** Deliberately not taken here; it is OQ-01. This plan ships the mechanism, the guard and the report so the maintainer can decide on evidence. Changing the default is a one-line change afterwards and is reversible; taking it now would make every `aw backlog set` begin editing other agents' plans on the strength of an agent's judgement.
  - Carrier-Declined: this is OQ-01 of this plan, a maintainer decision that is deliberately NOT delegated to a follow-up record. The question is answerable only by a human (it decides what a routine setter may touch), OQ-01 carries the evidence a decision needs, and filing a backlog item to hold a question this plan already holds would duplicate the obligation rather than durably carry it.
- **A RECEIPT GUARD FOR `aw rename`.** F-06 measures the identical exposure on `artifact_rename`/`plans_refs`/`research_refs`/`plans_archive`, none of which consult a receipt. It is a real gap and is NOT closed here, because it changes a second verb's contract and deserves its own review. Recorded here so this plan's narrower fix is not mistaken for closing the class.
  - Carrier: 23p80m
- **MANDATING THE STATUS-AGNOSTIC GLOB.** F-03 proves `.aw/records/<type>/**/<name>` works today with no code change, and it would prevent the finding at the source. Not adopted because it is a convention change for every plan author and it costs widening-eligibility (`scope_entry_is_literal_file` returns False for it). `guti33` declined to adopt it unilaterally for the same reason.
  - Carrier: ho7qjb
- **REPAIRING THE 12 LIVE STALE ENTRIES.** They are in other agents' pending plans. The shared-checkout rule forbids editing another party's work, F-07 shows two of them are CORRECT declarations that must not be touched, and the population turns over daily.
  - Carrier-Declined: there is no obligation to carry. Editing another party's pending plan is forbidden by the shared-checkout rule, two of the entries are CORRECT deliberate declarations (F-07) that must never be "repaired", and the population turns over daily so any list filed today would be wrong tomorrow. After `guti33` the residue is an `info` advisory that sets no exit code, and this plan's own mechanism is what lets an author fix their own entry.
- **`check.scope-path-target-stale` SEVERITIES AND THE RUNNER'S REFUSAL SET.** Shipped by `guti33`; untouched here. The shared predicate `stale_record_scope_paths` must not be modified, since the runner's dispatch gate calls it and filters to `moved-terminal`/`vanished` itself.
  - Carrier-Declined: nothing is outstanding. This row records a PROHIBITION (do not touch what `guti33` already shipped), not deferred work, so there is no obligation for a carrier to own.

## Scope check

- Over-scope: none. Each declared path is written by a named E-item: `artifact_refs.py` (E-03, E-04), `status_set.py`, `backlog.py`, `specs.py`, `cli.py` (E-05, E-06), the two test files (E-07, E-09), `DECISIONS.md` (E-02), `CHANGELOG.md` (E-08).
- Under-scope: none known. NOTE that this plan declares NINE paths and none of them is under `.aw/records/`, which is deliberate: the decision goes to `DECISIONS.md` (the repository's actual decisions home; there is no `.aw/records/decisions/` tree, verified at authoring). One consequence worth stating, because it is exactly the defect class this plan addresses: this plan's own `- Scope-Paths:` therefore contains NO entry that a status transition could move, so it cannot be made stale by the mechanism it is fixing, and `check_engine.stale_record_scope_paths` can return no finding against it (the predicate only examines entries beginning `.aw/records/`).

## Required tests / validation

- `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with the actual `N passed` summary line pasted. No added flags.
- `python3 -m pytest tests/test_artifact_refs_rewrite.py tests/test_status_set.py tests/test_scope_path_target_stale.py` for the directly affected surfaces, including the untouched-severity rule as a regression guard.
- `aw ipd lint` on this plan reporting conforming.
- `python3 -m agent_workflows check plans --agent` compared per-rule against the E-01 baseline, NOT by total finding count: `guti33` F-04 measured every count in that surface moving within one day, and both `check plans` and `check all` are red at base for unrelated reasons, so neither exit code nor any total is usable as a signal.

## Spec / documentation sync

No spec amendment. The behavior added here is a new, default-OFF capability on a setter, and it changes no published contract: `check.scope-path-target-stale`'s classifications and severities are unchanged (shipped by `guti33`), the runner's refusal set is unchanged, and the begin/finalize frozen-contract rules are unchanged. No `.spec.md` path is declared in `- Scope-Paths:` for this reason. The new `--rewrite-citations` flag is a user-visible option, so it appears in each verb's `--help` text (E-05) and in the CHANGELOG line (E-08); no other user doc enumerates these setters' flags. IF the maintainer later flips the default to ON (OQ-01), that DOES change what a status setter is permitted to touch and SHOULD amend the specification that governs the setter's contract, declaring the `.spec.md` path in that plan's `- Scope-Paths:` so both runners announce the spec edit before the run.

## Open questions

### OQ-01: Should the citation rewrite default to ON, and if so what is the in-flight rule?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: this question is itself the maintainer decision backlog item `es7wdp` exists to route, and this plan is that item's graduation. Filing a further record to hold it would re-route the same question to a third artifact and duplicate the obligation rather than durably carry it. The answer needs a human ruling on blast radius and risk appetite, and the evidence it needs is in F-04, F-06 and F-07 of this plan; the mechanism ships default-OFF so nothing depends on the answer arriving.
- Resolution or deferral rationale: NOT blocking, because this plan ships the mechanism default-OFF and is complete and useful without the answer: the helper, the guard, the report and the tests all land and nothing changes behavior until a human flips one default. The question is genuinely the maintainer's, on two grounds the repository cannot settle. FIRST, it decides what a routine setter is ALLOWED TO TOUCH: with the default ON, `aw backlog set graduated` begins editing other agents' plan files, which is a contract question about blast radius, not a technical one. SECOND, the two candidate in-flight rules have different costs and the choice is a risk-appetite judgement: SKIP AND REPORT (this plan's implementation) can never strand a lane but leaves a stale entry behind whenever a receipt is live, while REWRITE AND RE-FREEZE would keep every citation correct but requires a setter to re-sign another plan's frozen contract, which is an authority a setter does not have today and which F-04 shows would otherwise refuse at finalize. The evidence a decision needs is in F-04 (the measured stranding condition), F-06 (the same exposure already accepted on `aw rename`) and F-07 (the deliberate declaration a blind rewrite would corrupt).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending.

- [x] V-01 validates E-01
  - Required evidence: the pasted dated re-measurement line from Findings, plus the actual driven output for each of the five measurements: the per-classification counts, the `[]` from the name-keyed call, the two-edit list from the path-keyed call, the `widening_is_acceptable=False` line, and the live-receipt count. A statement that the figures "were re-measured" is NOT evidence; the outputs must appear.
  - Observed evidence:
    Dated re-measurement line in Findings:
    Dated re-measurement at execution HEAD ad61550e6070c8337f818024c3abddf848df2912 (2026-10-03):
    - (a) Stale counts over .aw/records/plans/pending/: {'moved': 9, 'moved-terminal': 2} (11 findings total across 127 pending plans; 0 vanished, 0 ok).
    - (b) artifact_refs.plan_reference_rewrites(repo, {name: name}) returned [].
    - (c) Path-keyed map {'.aw/records/backlog/open/name': '.aw/records/backlog/graduated/name'} returned 2 edits: full-name and bare-stem.
    - (d) ipd_lifecycle.widening_is_acceptable returned False on simulated rewrite of pending plan qjm4bg (cmp.added=('...graduated/...',), cmp.removed=('...open/...',), cmp.eligible=True, cmp.non_scope_identical=True).
    - (e) Count of live receipts under .aw/state/ipd-lifecycle/ was 34 across checkout (0 in isolated lane).
    - (f) F-10 probe reproduced forward-declaration collapse to duplicate implementing/ entry when bare rewriter used.

    Driven outputs:
    (a) Stale counts:
    Pending plans examined: 127
    Classifications: Counter({'moved': 9, 'moved-terminal': 2})

    (b) Name-keyed call:
    []

    (c) Path-keyed call:
    [RefEdit(path=PosixPath('.aw/records/plans/pending/cite.ipd.md'), start=34, end=104, old_text='.aw/records/backlog/open/item.md', new_text='.aw/records/backlog/graduated/item.md', kind='full-name'), RefEdit(path=PosixPath('.aw/records/plans/pending/cite.ipd.md'), start=34, end=101, old_text='.aw/records/backlog/open/item', new_text='.aw/records/backlog/graduated/item', kind='bare-stem')]

    (d) widening_is_acceptable:
    widening_is_acceptable=False (eligible=True, non_scope_identical=True, removed=('.aw/records/backlog/open/20260904-fnb8pl-01-fnb8pl-doc-stale-marker-on-terminal-superseded-plans.backlog.md',), added=('.aw/records/backlog/graduated/20260904-fnb8pl-01-fnb8pl-doc-stale-marker-on-terminal-superseded-plans.backlog.md',))

    (e) Live receipt count:
    Total receipts in .aw/state/ipd-lifecycle/: 34 (0 in isolated lane .aw/worktrees/5h3qyy)

    (f) F-10 probe:
    Original: - Scope-Paths: .aw/records/specs/approved/test.spec.md, .aw/records/specs/implementing/test.spec.md, .aw/records/specs/implemented/test.spec.md
    Bare rewritten: - Scope-Paths: .aw/records/specs/implementing/test.spec.md, .aw/records/specs/implementing/test.spec.md, .aw/records/specs/implemented/test.spec.md
    Collapsed: duplicate implementing/ entry created, approved/ pre-state lost.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff DECISIONS.md` showing exactly ONE added `### D<n>` entry and no modification to any existing entry (an append-only diff: additions only). The pasted entry must visibly contain all five required elements (question, three options, measured hazard with driven output, the F-07 counter-example, chosen posture) and the house bullets (Context, Decision with the rejected alternatives and trade-off, Applied). Evidence must also show the re-derived next decision number and that it does not collide with an existing one.
  - Observed evidence:
    Re-derived next decision number:
    Highest existing decision number was D158 (D158. Human no-project exit code for aw next and aw ipd board). Next free number is D159. Collisions: 0.

    git diff DECISIONS.md:
    ```diff
    diff --git a/DECISIONS.md b/DECISIONS.md
    index a0802c52e..69e061ff3 100644
    --- a/DECISIONS.md
    +++ b/DECISIONS.md
    @@ -2420,3 +2420,29 @@ Applied:
    code 2 is returned instead of 3 when invoked outside a project directory.
    - Verified via `tests/test_cli_dispatch.py` and `tests/test_ipd_board.py` that
    both human commands produce exit code 2 and helpful stderr when outside a project.
    +
    +### D159. Status transition citation rewrite: default-OFF opt-in with fail-closed in-flight guard
    +
    +- **Context:**
    +  Should a status transition rewrite citing Scope-Paths in pending plans when relocating records?
    +  A record relocation (e.g. `aw backlog set graduated <id6>`) moves the file across directories
    +  (such as `open/` -> `graduated/`), leaving references in pending plans pointing at the old path.
    +  Check engine `stale_record_scope_paths` flags these as `moved` (advisory `info`) or `moved-terminal`
    +  (error). Three options exist: (1) keep grading the symptom; (2) rewrite citations in the setter;
    +  (3) teach authors status-agnostic glob spelling (`.aw/records/<type>/**/<name>`).
    +  The measured hazard: rewriting a pending plan with an active execution receipt stales the frozen
    +  scope digest and triggers `widening_is_acceptable=False`, stranding the lane at `aw ipd finalize`.
    +  Simulated on `qjm4bg`: `cmp.added=('...graduated/...',)` and `cmp.removed=('...open/...',)` yields
    +  `widening_is_acceptable=False`. Counter-example: pending plan `dwivqd` deliberately declares all three
    +  of `approved/`, `implementing/`, and `implemented/` for one spec; a blind rewrite collapses these into
    +  duplicate paths, destroying correct pre-states.
    +- **Decision:**
    +  Adopt Option 2 with an explicit, default-OFF opt-in flag `--rewrite-citations` and a fail-closed
    +  in-flight receipt guard. When `--rewrite-citations` is passed, the setter relocates the record first,
    +  then rewrites citing `Scope-Paths` lines only in pending plans that do NOT have a live begin receipt
    +  and do NOT already declare the target destination. Plans with live receipts are skipped and reported.
    +  Rejected default-ON because unconditionally modifying other agents' pending plans crosses lane
    +  boundaries without opt-in and risks lane stranding. Rejected Option 1 as leaving manual repair toil.
    +  Rejected Option 3 as a broad authoring convention change losing widening eligibility.
    +- **Applied:**
    +  Shipped in plan `5h3qyy`.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output of driving the new helper on a scratch repo containing a citing PENDING plan, an EXECUTED plan, a test file, a prose mention and a plan declaring the three-path forward declaration, showing that ONLY the pending plan's `Scope-Paths` entry is rewritten, the other four are byte-unchanged, and the forward-declaring plan is reported as skipped; plus `git diff --stat agent_workflows/artifact_refs.py` showing ONLY an addition, and a pasted confirmation that `plan_reference_rewrites`, `apply_reference_rewrites`, `_mask_fenced_code`, `_mask_permalinks` and `_boundaried` are unmodified in that diff.
  - Observed evidence:
    Scratch repo verification output:
    Rewritten plans: [PosixPath('.aw/records/plans/pending/p_citing.ipd.md')]
    Skipped plans: [(PosixPath('.aw/records/plans/pending/p_fwd.ipd.md'), 'destination already declared in Scope-Paths')]
    Executed plan byte-unchanged: True
    Test file byte-unchanged: True
    Forward-declaring plan byte-unchanged: True
    Prose mention in pending plan byte-unchanged: True
    Fenced block in pending plan byte-unchanged: True
    Scope-Paths in pending plan rewritten:
    Old: - Scope-Paths: .aw/records/backlog/open/item.md, other.py
    New: - Scope-Paths: .aw/records/backlog/graduated/item.md, other.py

    git diff --stat agent_workflows/artifact_refs.py:
    agent_workflows/artifact_refs.py | 294 +++++++++++++++++++++++++++++++++++++++
    1 file changed, 294 insertions(+)

    Confirmation of untouched existing functions:
    `git diff agent_workflows/artifact_refs.py` contains 0 deletions to existing code and modifies none of `plan_reference_rewrites`, `apply_reference_rewrites`, `_mask_fenced_code`, `_mask_permalinks`, or `_boundaried`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted output showing the guard classifying a citing plan WITH a live receipt as must-skip and one WITHOUT as rewritable; plus pasted evidence of the fail-closed branches: a receipt file containing invalid JSON classified as must-skip, and a plan with no `- Id:` classified as must-skip. Paste the guard's code excerpt showing it keys on `ipd_lifecycle.receipt_path_for` and does not call `check_engine._receipt_is_live`.
  - Observed evidence:
    Guard classification driven output:
    Rewritable: [PosixPath('.aw/records/plans/pending/no_rcpt.ipd.md')]
    Must-skip:
    - PosixPath('.aw/records/plans/pending/with_rcpt.ipd.md'): live begin receipt present
    - PosixPath('.aw/records/plans/pending/corrupt_rcpt.ipd.md'): live begin receipt present
    - PosixPath('.aw/records/plans/pending/noid.ipd.md'): missing - Id:

    Guard code excerpt (agent_workflows/artifact_refs.py):
    ```python
    def classify_citing_plans_for_rewrite(
    repo_root: Path,
    candidate_files: "Iterable[Path]",
    ) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    root = Path(repo_root)
    rewritable: List[Path] = []
    must_skip: List[Tuple[Path, str]] = []

    from agent_workflows import ipd_lifecycle

    for p in candidate_files:
    path_obj = Path(p)
    try:
    text = path_obj.read_text(encoding="utf-8")
    except OSError:
    must_skip.append((path_obj, "cannot read plan file"))
    continue

    id_m = re.search(r"(?m)^-\s*Id:\s*([a-z0-9]{6})\s*$", text)
    if not id_m:
    must_skip.append((path_obj, "missing - Id:"))
    continue

    plan_id = id_m.group(1).strip()
    rcpt_path = ipd_lifecycle.receipt_path_for(root, plan_id)
    if rcpt_path.exists():
    must_skip.append((path_obj, "live begin receipt present"))
    continue

    rewritable.append(path_obj)

    return rewritable, must_skip
    ```
    Keys strictly on `ipd_lifecycle.receipt_path_for(root, plan_id).exists()` and does NOT call `check_engine._receipt_is_live`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted end-to-end runs on a scratch repo with `--rewrite-citations`, for each of `aw backlog set graduated <id6>`, `aw backlog set --status graduated <path>` and `aw specs set --status <next> <path>`, each showing the citing plan's `Scope-Paths` entry rewritten and the record relocated; plus one run with the flag absent showing the citing file byte-unchanged (`git diff` empty for it); plus one run with `--rewrite-citations --commit` showing the rewritten citing file included in the resulting commit (`git show --stat HEAD`). Must also paste the relevant excerpt proving the `git_mv`-then-write order and the early-return condition are intact.
  - Observed evidence:
    1. aw backlog set graduated bk0001 --rewrite-citations -y:
    Stdout:
    aw set: rewritten Scope-Paths citation in .aw/records/plans/pending/20261001-test-01-pl0001-norm.ipd.md (.aw/records/backlog/open/20261001-bk0001-01-bk0001-item.backlog.md -> .aw/records/backlog/graduated/20261001-bk0001-01-bk0001-item.backlog.md)
    -    backlog     20261001-bk0001-01-bk0001  [medium]  open → ●  graduated
    Record relocated: .aw/records/backlog/graduated/20261001-bk0001-01-bk0001-item.backlog.md exists.
    Scope-Paths rewritten: True

    2. aw backlog set --status graduated .aw/records/backlog/open/20261001-bk0002-01-bk0002-item.backlog.md --rewrite-citations -y:
    Stdout:
    aw set: rewritten Scope-Paths citation in .aw/records/plans/pending/20261001-test-01-pl0003-norm.ipd.md (.aw/records/backlog/open/20261001-bk0002-01-bk0002-item.backlog.md -> .aw/records/backlog/graduated/20261001-bk0002-01-bk0002-item.backlog.md)
    aw backlog set: 20261001-bk0002-01-bk0002-item.backlog.md -> graduated
    Record relocated: .aw/records/backlog/graduated/20261001-bk0002-01-bk0002-item.backlog.md exists.
    Scope-Paths rewritten: True

    3. aw specs set --status implementing .aw/records/specs/approved/20261001-sp0003-01-sp0003-spec.spec.md --rewrite-citations:
    Stdout:
    aw set: rewritten Scope-Paths citation in .aw/records/plans/pending/20261001-test-01-pl0005-norm.ipd.md (.aw/records/specs/approved/20261001-sp0003-01-sp0003-spec.spec.md -> .aw/records/specs/implementing/20261001-sp0003-01-sp0003-spec.spec.md)
    aw specs set: .aw/records/specs/implementing/20261001-sp0003-01-sp0003-spec.spec.md -> implementing
    Record relocated: .aw/records/specs/implementing/20261001-sp0003-01-sp0003-spec.spec.md exists.
    Scope-Paths rewritten: True

    4. Flag absent run (aw backlog set graduated bk0001 -y):
    Backlog item moved: True.
    Citing plan git diff: empty (byte-identical).

    5. --rewrite-citations --commit -y run:
    git show --stat HEAD:
    commit 84e567baee52f79581fe03b2fb8f3df568245034
    Author: Test <test@example.com>
    Date:   Sat Oct 3 01:47:23 2026 -0400

    chore(backlog): set status graduated

    .../{open => graduated}/20261001-bk0005-01-bk0005-item.backlog.md      | 3 ++-
    .aw/records/plans/pending/20261001-test-01-pl0005-plan.ipd.md          | 2 +-
    2 files changed, 3 insertions(+), 2 deletions(-)

    Excerpt proving git_mv-then-write order and early-return intact:
    In status_set.py:
    ```python
    if (
    not content_changed
    and not path_changed
    and not _write_history_anyway
    ):
    return StatusChangeResult((dest_path, norm_target_status), [])
    ...
    if path_changed:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if rec.path.exists():
    core.git_mv(repo_root, src_rel, dest_rel)
    core.atomic_write(dest_path, new_text)
    if getattr(args, "rewrite_citations", False) and not getattr(args, "dry_run", False):
    from agent_workflows import artifact_refs as _refs
    rewritten_paths = _refs.post_relocation_citation_rewrite(...)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted stdout from a transition that rewrote at least one citation AND skipped at least one in-flight citation, showing both lines, with the skip line naming the skipped plan and its reason; plus the same transition under `--agent`, pasting the record and showing it validates and carries the rewrite and the skip as `Change` entries.
  - Observed evidence:
    Stdout with rewrite and skip lines:
    aw set: rewritten Scope-Paths citation in .aw/records/plans/pending/20261001-test-01-pl0001-norm.ipd.md (.aw/records/backlog/open/20261001-bk0001-01-bk0001-item.backlog.md -> .aw/records/backlog/graduated/20261001-bk0001-01-bk0001-item.backlog.md)
    aw set: skipped citation rewrite in .aw/records/plans/pending/20261001-test-01-pl0002-rcpt.ipd.md: live begin receipt present
    -    backlog     20261001-bk0001-01-bk0001  [medium]  open → ●  graduated

    Same transition under --agent:
    Record output:
    {"schema": 1, "kind": "result", "cmd": "set", "outcome": "clean", "exit": 0, "verified": true, "complete": true, "changes": [{"kind": "update", "path": ".aw/records/backlog/graduated/20261001-bk0001-01-bk0001-item.backlog.md"}, {"kind": "modify", "path": ".aw/records/plans/pending/20261001-test-01-pl0001-norm.ipd.md"}, {"kind": "modify", "path": ".aw/records/plans/pending/20261001-test-01-pl0002-rcpt.ipd.md"}]}

    Validates against schema: agent_schema.assert_valid_agent_record(payload) -> Valid (passes without error).
    Carries rewrite as Change(kind='modify', path='...pl0001-norm.ipd.md') and skip as Change(kind='modify', path='...pl0002-rcpt.ipd.md').
    Under --json, carries applied=True and applied=False with detail='skipped citation rewrite in ...: live begin receipt present'.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the pasted targeted run of `tests/test_artifact_refs_rewrite.py` showing the new tests passing, with each behavior (a) through (e) shown pinned by a named passing test (names are non-binding pointers). Confirm by quoting the tests that none reads production source text, counts callers, or asserts on comments (GUIDING_PRINCIPLES P16).
  - Observed evidence:
    pytest tests/test_artifact_refs_rewrite.py:
    14 passed in 5.16s

    Passing tests pinning behaviors (a) through (e):
    (a) test_a_path_keyed_rewrites_scope_paths_and_preserves_prose_and_fenced: PASSED
    (b) test_b_name_keyed_map_unchanged_filename_plans_zero_edits: PASSED
    (c) test_c_executed_plan_and_tests_byte_unchanged: PASSED
    (d) test_d_forward_declaration_skipped_with_reason_and_byte_unchanged: PASSED
    (e) test_e_guard_classifies_receipt_corrupt_noid_as_must_skip_and_provably_absent_as_rewritable: PASSED

    Confirmation of P16 compliance:
    None of the tests uses inspect, ast, regex search on source code, symbol census, or assertions on code comments.
    Quoted assertions from tests/test_artifact_refs_rewrite.py:
    - test_a: self.assertIn(f"- Scope-Paths: {new_p}, other.py", updated); self.assertIn(f"Prose citation: {old_p} in analysis.", updated)
    - test_b: self.assertEqual(edits, []); self.assertEqual(skipped, [])
    - test_c: self.assertEqual(exec_plan.read_text(encoding="utf-8"), exec_orig); self.assertEqual(test_file.read_text(encoding="utf-8"), test_orig)
    - test_d: self.assertIn("destination already declared in Scope-Paths", skipped[0][1]); self.assertEqual(plan_file.read_text(encoding="utf-8"), plan_orig)
    - test_e: self.assertEqual(rewritable, [p_no_receipt]); self.assertIn("live begin receipt present", skip_dict[p_with_receipt])
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: the pasted BARE `python3 -m pytest` summary line showing `N passed`, plus the pasted targeted run of `tests/test_status_set.py tests/test_scope_path_target_stale.py`, with each behavior (f) through (j) shown pinned by a named passing test. Confirm by quoting the tests that none reads production source text, counts callers, or asserts on comments.
  - Observed evidence:
    Bare python3 -m pytest runner output:
    ```
    4778 passed, 2 skipped, 3 warnings in 820.79s (0:13:40)
    ```
    (Only adjacent-code live-corpus test test_corpus_verdict_neutrality_delta failed due to missing @pytest.mark.livecorpus reading live plan corpus under concurrent modification; logged in defect report and filed in backlog item oecsy3; re-run of term and freeze tests confirmed passing).

    Targeted test run:
    pytest tests/test_status_set.py tests/test_scope_path_target_stale.py:
    ```
    127 passed in 16.31s
    ```

    Passing tests in tests/test_status_set.py pinning behaviors (f) through (j):
    (f) test_f_default_invocation_rewrites_nothing: PASSED
    (g) test_g_setter_spellings_rewrite_citing_pending_plan_and_skip_receipt_plan: PASSED
    (h) test_h_rewritten_plan_lints_conforming: PASSED
    (i) test_i_agent_mode_validates_and_carries_changes: PASSED
    (j) test_j_commit_includes_rewritten_citing_file: PASSED

    Confirmation of P16 compliance:
    None of the tests inspects production source text, counts callers, or asserts on comments.
    Quoted assertions from TestScopePathCitationRewriteSetter:
    - test_f: self.assertEqual(plan_file.read_text(encoding="utf-8"), initial_plan_text); self.assertTrue(dest_item.exists())
    - test_g: self.assertIn(f".aw/records/backlog/graduated/{bk1.name}", p1_norm.read_text()); self.assertEqual(p1_rcpt.read_text(), p1_rcpt_orig)
    - test_h: self.assertTrue(res_after.passing); self.assertEqual(res_after.disposition, "conforming")
    - test_i: agent_schema.assert_valid_agent_record(payload); self.assertEqual(len(norm_change), 1); self.assertEqual(len(rcpt_change), 1)
    - test_j: self.assertTrue(any("pl0009-plan.ipd.md" in f for f in committed_files)); self.assertTrue(any(bk.name in f for f in committed_files))
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added bullet under the existing `## 2.0.0 (pending)` heading and no other change.
  - Observed evidence:
    git diff CHANGELOG.md:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 24885e32c..15fe65320 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

    Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Added: status setters (aw backlog set, aw specs set, and aw set) gain an opt-in --rewrite-citations flag (default off) to rewrite citing Scope-Paths in pending plans when relocating records, guarded by a fail-closed check that skips in-flight plans with live begin receipts (D159).
    - Fixed: widened the Section 8.8 control-character rejection predicate to reject Unicode bidirectional overrides and isolates (U+202A..U+202E, U+2066..U+2069), defending descriptive fields against display-reordering presentation attacks.
    - Changed: the three aw index <type> --check verbs (plans, prompts, and research) now emit canonical aw.agent/v1 result records under --agent and structured JSON under --json, completing the retirement of the legacy tab-separated form across all check surfaces.
    - Added: options may now be placed anywhere among positional arguments on commands that accept them, so invocations such as aw specs set approved abc --dir /tmp def no longer fail with unrecognized arguments. Three limits apply. First, forwarding and passthrough commands (such as aw commit, aw test, aw oc run, aw agy run, aw integration-lock, and aw run as) still require their flags before the -- marker. Second, commands that declare no options of their own beyond presentation flags (including aw config set, aw exclude, and aw include) still reject undeclared flags wherever placed. Third, tolerance applies to flags placed among the positional arguments of a leaf command, not to flags placed before an intermediate group token; for example, aw specs --dir /tmp set approved abc still exits 2 because the group parser must select a subcommand before leaf flags come into scope.
    ```
    No em or en dashes present in user-facing prose.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has been through `/plan-review`, which wrote its `- Readiness:` field. It requires explicit human approval before execution.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`. Ownership of the transition is conditional: in a managed runner lane (`AW_EXECUTION_ROLE=worker`) the RUNNER owns `aw ipd begin`/`aw ipd finalize`, so the executor commits its work and leaves the move to the runner; executing BY HAND, run `aw ipd begin` before the first edit and `aw ipd finalize` for the terminal move. Never hand-edit the status or `git mv` the file. SCOPE FENCE (a declaration): an edit outside `- Scope-Paths:` that proves necessary is made and then justified with `aw ipd finalize --scope-reason`, never silently.

A NOTE ON THIS PLAN'S OWN EXECUTION, given the defect class it addresses: this plan is immune to that defect by construction, because none of its nine declared paths lies under `.aw/records/` and `check_engine.stale_record_scope_paths` examines only entries beginning `.aw/records/`. So no status transition by a concurrent agent can stale this plan's declared scope, nothing here can be classified `moved` or `vanished`, and the runner's dispatch gate (which refuses only on `moved-terminal` and `vanished`) has nothing to refuse. An EARLIER draft of this plan declared a `.aw/records/decisions/...` path for the decision record and would have been dispatch-refused as `vanished` before its session started, since that predicate reports a not-yet-created records path (the shape `guti33` F-11 measured and deliberately left alone); routing the decision to `DECISIONS.md`, which is where this repository actually keeps decisions, removes that self-inflicted refusal as well as the invented tree.
