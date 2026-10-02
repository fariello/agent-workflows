# IPD: Decide and implement whether a status transition rewrites citing Scope-Paths, with an in-flight receipt guard

- Date: 2026-10-02
- Kind: child
- Concern: A RECORD STATUS TRANSITION RELOCATES THE RECORD AND REWRITES NO CITATION, so every plan that declared the record at its old status directory is left pointing at a path that no longer exists. `status_set.apply_status_change` is the ONE record-type-agnostic handler behind `aw backlog set`, `aw specs set`, `aw ipd set` and bare `aw set`; it resolves a destination with `record_placement.resolve_transition_path`, relocates with `_core.git_mv` (its own comment: "RELOCATE WITH `git mv`, NOT write-then-unlink"), rewrites many FIELDS on the moved record, and rewrites no citation anywhere else. Executed plan `guti33` (Set `9xap30`) fixed the SYMPTOM by re-tiering a plain `moved` finding to `info`; this plan is its OQ-01 CAUSE half, carried by backlog `es7wdp`. Authoring measured FIVE things the item does not state and TWO of them change the answer rather than the method. FIRST, THE EXISTING REWRITER CANNOT BE CALLED AS THE ITEM DESCRIBES: `artifact_refs.plan_reference_rewrites` is keyed on FILENAME changes, and a status transition leaves the filename byte-identical while changing only the directory, so the `{old_name: new_name}` map the item proposes is `{name: name}`, which the function SKIPS at its `if old_name == new_name: continue` guard and which returns `[]` when driven (F-01). The rewriter is still reusable, but only when fed REPO-RELATIVE PATHS as map keys, which is a different call than the item assumes and is what E-03 builds. SECOND, THE HAZARD IS REAL AND IS WORSE THAN THE ITEM STATES: a path rewrite is a REMOVAL plus an ADDITION, and `ipd_lifecycle.widening_is_acceptable` demands `not removed`, so rcptwiden `63425h`'s additive-widening accept does NOT rescue it and `finalize_precheck` refuses with the stranding message (F-04, driven on a real pending plan). The item says a safe implementation "needs a stated rule for in-flight plans"; measured, that rule is NOT optional, it is the whole decision. THIRD, the in-flight population is ENUMERABLE with a proven in-tree pattern (`check_engine._receipt_is_live`), so "skip and report" is implementable rather than aspirational (F-05). FOURTH, `aw rename` ALREADY performs exactly this rewrite with NO receipt guard at all, which is both the precedent for acting and a pre-existing exposure this plan must not widen silently (F-06). FIFTH, the live `moved` population is 10 entries across pending plans, not the item's 4, and one of the 10 is a DELIBERATE forward declaration that a rewriter MUST NOT touch (F-07), which is the single strongest argument for the skip-and-report posture.
- Scope: IN: (a) record the maintainer decision as a durable in-repo decision record with the hazard, the measured counter-example and the chosen posture, because this item is a DECISION item and shipping code without recording why would discard the reasoning; (b) add a shared, record-type-agnostic path-keyed citation-rewrite helper to `artifact_refs` that takes an `{old_rel_path: new_rel_path}` map (the shape F-01 proves is required) and reuses the EXISTING `plan_reference_rewrites`/`apply_reference_rewrites` machinery rather than adding a second rewriter; (c) add an in-flight guard predicate that enumerates live begin receipts and classifies each candidate citing file as safe-to-rewrite or must-skip, built on the SAME `read_receipt` + liveness pattern `check_engine._receipt_is_live` already uses; (d) wire the two into `status_set.apply_status_change` behind an explicit opt-in flag that DEFAULTS OFF, so no existing invocation changes behavior until the maintainer flips the default; (e) report every skipped in-flight citation on stdout so a skip is visible rather than silent; (f) behavior tests for the rewrite, the skip, the fenced/permalink masking, and the default-off invariant; (g) one CHANGELOG line. OUT: changing the DEFAULT to on (that is the maintainer's call once this lands and is OQ-01, deliberately left for a human); changing `check.scope-path-target-stale` severities or classifications (shipped by `guti33`, and E-02 forbids touching the shared predicate); the runner's dispatch refusal set (reads no severity, F-08 of `guti33`); adding a receipt guard to `aw rename` (a real pre-existing gap, filed as a follow-up in the Deferred section rather than silently bundled, because it changes a second verb's contract); mandating the status-agnostic glob spelling as a convention for every plan author (F-03 proves it works today and the Deferred section carries it as guidance-only); and repairing the live stale entries in other agents' pending plans (not this plan's files, per the shared-checkout rule, and the population turns over daily).
- Scope-Paths: agent_workflows/artifact_refs.py, agent_workflows/status_set.py, tests/test_artifact_refs_rewrite.py, tests/test_status_set.py, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: es7wdp
- Set: scoperewrite
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 5h3qyy

## Workflow history

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `es7wdp`, the durable carrier of executed plan `guti33`'s OQ-01. Authoring drove every claim in the item against the live tree and all of them hold, but two measurements change the shape of the answer. (1) The item's "call the existing rewriter from the existing setter" is NOT directly possible: the rewriter is FILENAME-keyed and a status transition changes only the DIRECTORY, so the proposed `{old_name: new_name}` map is `{name: name}` and returns zero edits when driven (F-01). Feeding it repo-relative PATHS does work and rewrites correctly while respecting fence and permalink masking (F-02), so the reuse claim survives in a corrected form. (2) The in-flight hazard is NOT mitigated by rcptwiden `63425h`: a rewrite is removal+addition, `widening_is_acceptable` requires `not removed`, and driving a real pending plan's receipt through `frozen_region_comparison` after a simulated rewrite yields `removed=(...)`, `added=(...)`, `widening_is_acceptable=False`, i.e. the exact stranding refusal (F-04). So the plan is built around a default-OFF opt-in plus a measured skip-and-report guard, and the decision of whether to flip the default is left to the maintainer as OQ-01 rather than taken here. Also measured: the live `moved` population is 10, not 4, and one entry is a deliberate three-path forward declaration by plan `dwivqd` that a rewriter must never touch (F-07). See F-01 through F-08.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Remove the CAUSE of stale `Scope-Paths` targets rather than continue grading the symptom, without letting a routine `aw backlog set graduated` strand an unrelated in-flight plan's lane. Concretely: give the repository ONE shared, path-keyed citation-rewrite helper plus ONE in-flight receipt guard, wire both into the single record-type-agnostic status setter behind a flag that defaults OFF, and record the decision and its measured hazard durably so the maintainer can flip the default on evidence instead of on assertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed.

### Task group 1: Re-measure the base, because every number here describes a LIVE tree

- [ ] E-01 Re-drive the five authoring measurements at execution HEAD and record the actual numbers in this plan's Findings as a dated re-measurement line, because the pending-plan corpus turns over daily and `guti33` F-01/F-04/F-09 each record a figure that moved within one day. Re-drive: (a) the per-classification stale counts over `.aw/records/plans/pending/` via `check_engine.stale_record_scope_paths`; (b) `artifact_refs.plan_reference_rewrites(repo, {name: name})` returning `[]`; (c) the same function with a path-keyed map returning the two expected edits; (d) `ipd_lifecycle.widening_is_acceptable` on a simulated rewrite of a real pending plan returning False; (e) the count of live receipts under `.aw/state/ipd-lifecycle/`. If any measurement DISAGREES with the Findings table, stop and report rather than proceeding, because the design rests on (b) and (d).
  - Depends on: none
  - Expected outcome: a dated re-measurement line in Findings; (b) is `[]`, (d) is False; (a) and (e) recorded as observed, whatever they are. No source file modified by this item.
  - Execution state: pending

### Task group 2: Record the decision, because this is a decision item

- [ ] E-02 Append ONE new numbered decision entry to `DECISIONS.md`, which is this repository's established home for a durable decision record (there is NO `.aw/records/decisions/` tree, verified at authoring, and the file's own header states it is the "Append-only, dated record of significant decisions ... with the reasoning, alternatives considered, and trade-offs"). Follow the existing `### D<n>. <title>` convention, taking the next free number after the current highest (D158 at authoring; re-derive it at execution rather than trusting that figure, since the log is appended by other work). The entry must carry the house shape used by its neighbours, namely **Decision**, **Alternatives considered** and **Trade-off**, and must state: the question; the three options (keep grading the symptom; rewrite citations in the setter; teach the status-agnostic glob spelling); the measured hazard with F-04's driven `widening_is_acceptable=False` output; F-07's counter-example; and the chosen default-OFF opt-in posture. Append only, per the file's own contract; do not reword any existing entry.
  - Depends on: E-01
  - Expected outcome: one new `### D<n>` entry in `DECISIONS.md` carrying Decision / Alternatives considered / Trade-off, with the driven evidence pasted rather than summarized, and no existing entry altered.
  - Execution state: pending

### Task group 3: The two mechanism pieces, a shared path-keyed rewrite helper and a fail-closed in-flight guard

- [ ] E-03 Add a path-keyed citation-rewrite helper to `agent_workflows/artifact_refs.py` taking an `{old_repo_relative_path: new_repo_relative_path}` map and returning the same `RefEdit` list the existing planner returns, by DELEGATING to `plan_reference_rewrites` rather than reimplementing any matching. Do NOT modify `plan_reference_rewrites`, `apply_reference_rewrites`, `_mask_fenced_code`, `_mask_permalinks` or `_boundaried`: F-02 proves the existing machinery already rewrites a path-keyed map correctly and already skips fenced blocks, and F-08 proves a path-keyed key bypasses the legacy-prefix and clustered-prefix branches by returning `None`/`None`, so no new escaping or boundary logic is needed. Document on the helper WHY the map is path-keyed and not name-keyed, citing the `if old_name == new_name: continue` guard that makes a name-keyed status transition a no-op.
  - Depends on: E-01
  - Expected outcome: one new helper in `artifact_refs` that plans the two expected edits (full-path and path-stem) for a status-directory change, with the existing rewriter and its masking untouched.
  - Execution state: pending

- [ ] E-04 Add an in-flight guard predicate that, given a repo root and a set of candidate citing files, returns which of them belong to a plan with a LIVE begin receipt and must therefore be skipped. Build it on the SAME pattern `check_engine` already uses at its `read_receipt` call site: read each plan's `- Id:`, call `ipd_lifecycle.read_receipt`, and treat a receipt as live using the existing liveness notion (`check_engine._receipt_is_live`), reusing that helper if it is importable rather than hand-rolling a second definition of "live". Fail CLOSED: a plan whose receipt cannot be read or whose liveness cannot be determined is treated as IN-FLIGHT (skip), because a wrong skip costs a stale path string while a wrong rewrite costs a stranded lane and the measured $95.71/3h10m class of loss recorded in `rcptwiden`.
  - Depends on: E-01
  - Expected outcome: one predicate classifying candidate citing files into rewritable and must-skip, fail-closed on any uncertainty, with no second definition of receipt liveness introduced.
  - Execution state: pending

### Task group 4: Wire into the one setter, default OFF

- [ ] E-05 Wire E-03 and E-04 into `status_set.apply_status_change` at the point AFTER the relocation is known, behind an explicit opt-in that DEFAULTS OFF so no existing caller changes behavior. Place the call after `dest_path` is resolved and the `moving` decision is made, build the one-entry path map from the old and new repo-relative paths, run E-04's guard, rewrite only the unguarded files, and leave the moved record's own fields exactly as they are. Preserve the function's existing early-return (`if not content_changed and not path_changed and not _write_history_anyway`) and its `git_mv`-before-write ORDER, whose comment records that writing first makes `git mv` refuse; a rewrite must not be inserted between the move and the destination write.
  - Depends on: E-03, E-04
  - Expected outcome: the setter can rewrite citing scope entries when explicitly asked, does nothing different when not asked, and the relocation order and early-return are unchanged.
  - Execution state: pending

- [ ] E-06 Report every rewritten and every SKIPPED citation on stdout, in the established shape the same function already uses for its gate-inheritance notice (`sys.stdout.write(f"aw set: inherited - Blocks-Release: ...")`). A skip MUST name the skipped plan and the reason (live begin receipt), because a silent skip leaves a stale path with no trace and is the failure mode that makes "skip and report" acceptable at all; a report is what converts it from data loss into a visible, actionable advisory that `check.scope-path-target-stale` will then report at `info`.
  - Depends on: E-05
  - Expected outcome: rewrites and skips are both visible on stdout, each skip naming the plan and the live-receipt reason.
  - Execution state: pending

### Task group 5: Tests and changelog

- [ ] E-07 Add behavior tests, exercising real code and asserting on real outputs and side effects (never reading source text, counting callers, or pinning comments): (a) a path-keyed map rewrites a citing plan's `Scope-Paths` entry and its prose mention, while leaving a fenced-code occurrence untouched; (b) a NAME-keyed map for an unchanged filename plans zero edits, pinning F-01's cause so a future author cannot reintroduce the name-keyed call; (c) a citing plan with a live begin receipt is SKIPPED and reported, and its file is byte-unchanged; (d) the setter's DEFAULT path rewrites nothing, pinning the default-off invariant; (e) a rewrite does not invalidate a NON-in-flight plan. Put rewrite-helper tests in `tests/test_artifact_refs_rewrite.py` and setter-wiring tests in `tests/test_status_set.py`, following each file's existing fixture style.
  - Depends on: E-05, E-06
  - Expected outcome: five behavior tests covering rewrite, the name-keyed no-op, the in-flight skip, the default-off invariant, and the non-in-flight case; all passing.
  - Execution state: pending

- [ ] E-08 Add one CHANGELOG line under the existing `## 2.0.0 (pending)` heading describing the opt-in citation rewrite and its default-off posture. Do not add a new version heading and do not reword neighbouring entries.
  - Depends on: E-07
  - Expected outcome: one new CHANGELOG bullet under the existing pending heading; no other CHANGELOG text altered.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A RECORD'S DIRECTORY ALWAYS AGREES WITH ITS `- Status:`, and the setters relocate the file to match. That is the mechanism under this whole plan: the relocation is CORRECT behavior, so the defect is the unrewritten citation, never the move.
- ONE SHARED HANDLER, NOT PER-VERB COPIES. `status_set.apply_status_change` is record-type-agnostic and is the single route behind `aw backlog set`, `aw specs set`, `aw ipd set` and bare `aw set`. Its own comments repeatedly record the lesson that a fix wired into one spelling "would fire for one spelling of one verb and not the other, which is worse than not shipping it because it teaches a false expectation" (the `decide_gate_default` comment). This plan therefore wires one place.
- FIELD WRITES ON THIS PATH ARE HOISTED OUT OF THE STATUS BRANCH and funnel through one shared primitive each (`set_blocks_release_line`, `set_from_backlog_line`, `set_item_dependencies_line`, `set_priority_line`, `set_work_kind_line`, `set_graduated_to_line`), each comment stating "no duplicate write path". E-03 follows that convention by delegating to the existing rewriter instead of adding a second one.
- FAIL CLOSED ON UNCERTAINTY is the house posture for anything touching a receipt: `frozen_region_comparison`'s three ineligible shapes are each "fail-closed and each named in `ineligible_reason`", and `_entry_is_bare_directory` "fails CLOSED in the direction that matters". E-04 adopts the same posture.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Where | Finding and evidence |
|---|---|---|---|
| F-01 | **HIGH** | `artifact_refs.plan_reference_rewrites`, `plan_reference_rewrites_with_warnings` | **THE ITEM'S PROPOSED CALL IS A NO-OP, AND THIS IS THE SINGLE MOST LOAD-BEARING CORRECTION AUTHORING MAKES.** The item says option (c) is "call the existing rewriter from the existing setter", driven by "an old-name-to-new-name map". But a status transition does NOT change the filename; it changes only the DIRECTORY. So the map is `{name: name}`, and `plan_reference_rewrites_with_warnings` begins its loop with `for old_name, new_name in name_map.items(): if old_name == new_name: continue`, skipping every such entry. DRIVEN on a scratch git repo with a citing plan declaring `.aw/records/backlog/open/<name>`: `plan_reference_rewrites(d, {name: name})` returned `[]`. A literal reading of the item would therefore ship a setter that calls a rewriter and rewrites nothing, and the stale entries would persist with the cause believed fixed. The reuse claim is still sound, but only in the corrected PATH-KEYED form of F-02. |
| F-02 | HIGH | `artifact_refs.plan_reference_rewrites`, `apply_reference_rewrites`, `_mask_fenced_code` | **FED REPO-RELATIVE PATHS, THE EXISTING REWRITER WORKS CORRECTLY AND NEEDS NO MODIFICATION.** DRIVEN with `{".aw/records/backlog/open/<name>": ".aw/records/backlog/graduated/<name>"}` against a citing plan containing the path in its `- Scope-Paths:` line, in prose, and inside a fenced block: the planner emitted two edits (`full-name` and `bare-stem`), and `apply_reference_rewrites` rewrote the `Scope-Paths` entry and the prose mention while leaving the FENCED occurrence byte-identical. So fence masking and permalink masking already hold for a path-keyed map, which is why E-03 is a thin delegating helper rather than new matching logic. |
| F-03 | MEDIUM | `ipd_schema._scope_path_entry_error`, `ipd_lifecycle._scope_match`, `check_engine.stale_record_scope_paths` | **THE ZERO-CODE ALTERNATIVE GENUINELY WORKS TODAY, which is why it is preserved as guidance rather than dismissed.** DRIVEN: `.aw/records/backlog/**/<name>.backlog.md` returns `None` from `_scope_path_entry_error` (accepted), survives `parse_scope_paths` intact and non-grandfathered, and `_scope_match` returns True against the file under `open/`, `graduated/` AND `done/` while returning False for a DIFFERENT file in the same directory; `stale_record_scope_paths` on a plan declaring it returns `[]`. Also measured: `scope_entry_is_literal_file` returns False for it, so such an entry is NOT widening-eligible, a real trade-off a reviewer should see. This plan does not mandate the spelling (a convention change for every author) but the Deferred section carries it. |
| F-04 | **HIGH** | `ipd_lifecycle.receipt_is_current`, `frozen_region_comparison`, `widening_is_acceptable`, `finalize_precheck` | **THE HAZARD IS CONFIRMED AND rcptwiden `63425h` DOES NOT RESCUE IT, so the in-flight rule is mandatory rather than advisable.** A rewrite is a REMOVAL plus an ADDITION, and `widening_is_acceptable` requires `cmp.eligible and cmp.non_scope_identical and not cmp.removed and cmp.added`. DRIVEN on the REAL pending plan `qjm4bg` (whose frozen scope declares four `.aw/records/backlog/open/` entries), simulating one entry moving to `graduated/`: `receipt_is_current` went True -> **False**; `frozen_region_comparison` returned `added=('...graduated/...fnb8pl...',)`, `removed=('...open/...fnb8pl...',)`, `non_scope_identical=True`, `eligible=True`, and `widening_is_acceptable=False`. `finalize_precheck` refuses on exactly that condition, and its own comment confirms "Every other mismatch - a removal, a mixed add-and-remove ... still refuses". Note `guti33` F-12's reassurance ("the receipt freezes the entry STRING, and the string does not change when the file moves") is TRUE for a bare move and becomes FALSE the moment a rewriter changes the string, which is precisely what this plan would do. |
| F-05 | MEDIUM | `check_engine`'s `read_receipt` call site and `_receipt_is_live`; `ipd_lifecycle.receipt_path_for`, `receipt_dir` | **"SKIP AND REPORT" IS IMPLEMENTABLE WITH AN EXISTING PROVEN PATTERN, so it is not an aspiration.** `check_engine` already walks every plan file, reads `- Id:`, calls `_life.read_receipt(repo_root, plan_id)`, `continue`s when there is none ("no active execution -> nothing to reconcile"), and then filters on `_receipt_is_live(repo_root, p, receipt)` ("spent authority (terminal plan / unreachable base) -> not an in-flight scope"). Receipts live at `.aw/state/ipd-lifecycle/<id6>.receipt.json` via `receipt_path_for`, anchored on the CHECKOUT by `checkout_control_root` so a lane's receipts are visible to the driver (the fix for backlog `dh0uno`). Measured in this authoring worktree: that directory does not exist, i.e. zero live receipts, so the guard is a cheap no-op in the common case. E-04 reuses `_receipt_is_live` rather than defining liveness a second time. |
| F-06 | MEDIUM | `artifact_rename`, `plans_refs`, `research_refs`, `plans_archive` | **`aw rename` ALREADY DOES THIS REWRITE WITH NO RECEIPT GUARD, which is simultaneously the precedent for acting and a pre-existing exposure.** Measured: `grep -c 'receipt\|in_flight\|in-flight'` returns **0** for all four of `artifact_rename.py`, `plans_refs.py`, `research_refs.py`, `plans_archive.py`, and the only three modules calling `read_receipt`/`receipt_path_for` are `check_engine.py`, `ipd_lifecycle.py` and `runner_shared.py`. So renaming an artifact today can already stale an in-flight plan's receipt by the F-04 mechanism and nothing stops it. TWO CONSEQUENCES: the item's hazard is not a reason to refuse the setter change (the repository already accepts that risk on a neighbouring verb), AND this plan must not pretend to close the class, because it closes it only on the setter. The rename half is named in Deferred as a follow-up rather than silently bundled, since it changes a second verb's contract. |
| F-07 | **HIGH** | `check_engine.stale_record_scope_paths` driven over `.aw/records/plans/pending/`; pending plan `dwivqd` | **A BLIND REWRITER WOULD CORRUPT A DELIBERATE FORWARD DECLARATION, which is the strongest single argument for skip-and-report over unconditional rewriting.** DRIVEN over every pending plan: **10** `moved` and **2** `moved-terminal` findings (12 total), already more than the item's "FOUR were stale at the time of filing", confirming the population grows. Seven of the 10 are routine `backlog/open/ -> graduated/` moves. But TWO of them belong to pending plan `dwivqd`, which DELIBERATELY declares all THREE of `specs/approved/`, `specs/implementing/` and `specs/implemented/` for ONE spec, and says so explicitly: "three paths for one file because the setter relocates it (F-06). The `approved/` path is the pre-state (deleted by E-03), `implementing/` the intermediate ... Declaring only one would leave two of the three writes undeclared at finalize." A rewriter that "fixed" those entries would destroy a correct declaration and break that plan's finalize reconciliation. So the classification `moved` does NOT imply "should be rewritten", and any rewriter must be opt-in and guarded rather than a sweeping repair. |
| F-08 | LOW | `artifact_refs._legacy_prefix_stem`, `_whole_stem`, `_boundaried`, `artifact_naming.parse_clustered_prefix` | **A PATH-KEYED MAP IS SAFE IN THE REWRITER'S OTHER BRANCHES, so E-03 needs no new escaping.** DRIVEN on the path key `.aw/records/specs/approved/20260802-1904-01-ipd-structure-and-linting.spec.md`: `_legacy_prefix_stem` returns `None` and `parse_clustered_prefix` returns `None`, so the legacy-prefix and clustered-prefix shorthand branches (and their shared-prefix WARNING path) are bypassed entirely; `_whole_stem` returns the path minus `.md`, giving the intended path-stem rewrite. `_boundaried` wraps its input in `re.escape`, so the slashes and dots in a path are matched literally. Exactly two edits result, both intended, with no risk of rewriting a bare id6 or setid. |

## Proposed changes (ordered, validatable)

1. Re-measure the five load-bearing figures and halt on disagreement with F-01/F-04 (E-01).
2. Record the decision, its measured hazard and its counter-example durably (E-02).
3. Add the path-keyed rewrite helper, delegating to the existing rewriter (E-03).
4. Add the fail-closed in-flight receipt guard, reusing the existing liveness notion (E-04).
5. Wire both into the one shared setter behind a default-OFF opt-in, preserving relocation order (E-05).
6. Report every rewrite and every skip on stdout (E-06).
7. Add five behavior tests, including the default-off and name-keyed-no-op invariants (E-07).
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

- Over-scope: none. Each declared path is written by a named E-item: `artifact_refs.py` (E-03), `status_set.py` (E-05, E-06), the two test files (E-07), `DECISIONS.md` (E-02), `CHANGELOG.md` (E-08).
- Under-scope: none known. NOTE that this plan declares SIX paths and none of them is under `.aw/records/`, which is deliberate: the decision goes to `DECISIONS.md` (the repository's actual decisions home; there is no `.aw/records/decisions/` tree, verified at authoring). One consequence worth stating, because it is exactly the defect class this plan addresses: this plan's own `- Scope-Paths:` therefore contains NO entry that a status transition could move, so it cannot be made stale by the mechanism it is fixing, and `check_engine.stale_record_scope_paths` can return no finding against it (the predicate only examines entries beginning `.aw/records/`).

## Required tests / validation

- `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with the actual `N passed` summary line pasted. No added flags.
- `python3 -m pytest tests/test_artifact_refs_rewrite.py tests/test_status_set.py tests/test_scope_path_target_stale.py` for the directly affected surfaces, including the untouched-severity rule as a regression guard.
- `aw ipd lint` on this plan reporting conforming.
- `python3 -m agent_workflows check plans --agent` compared per-rule against the E-01 baseline, NOT by total finding count: `guti33` F-04 measured every count in that surface moving within one day, and both `check plans` and `check all` are red at base for unrelated reasons, so neither exit code nor any total is usable as a signal.

## Spec / documentation sync

No spec amendment. The behavior added here is a new, default-OFF capability on a setter, and it changes no published contract: `check.scope-path-target-stale`'s classifications and severities are unchanged (shipped by `guti33`), the runner's refusal set is unchanged, and the begin/finalize frozen-contract rules are unchanged. No `.spec.md` path is declared in `- Scope-Paths:` for this reason. IF the maintainer later flips the default to ON (OQ-01), that DOES change what a status setter is permitted to touch and SHOULD amend the specification that governs the setter's contract, declaring the `.spec.md` path in that plan's `- Scope-Paths:` so both runners announce the spec edit before the run.

## Open questions

### OQ-01: Should the citation rewrite default to ON, and if so what is the in-flight rule?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: this question is itself the maintainer decision backlog item `es7wdp` exists to route, and this plan is that item's graduation. Filing a further record to hold it would re-route the same question to a third artifact and duplicate the obligation rather than durably carry it. The answer needs a human ruling on blast radius and risk appetite, and the evidence it needs is in F-04, F-06 and F-07 of this plan; the mechanism ships default-OFF so nothing depends on the answer arriving.
- Resolution or deferral rationale: NOT blocking, because this plan ships the mechanism default-OFF and is complete and useful without the answer: the helper, the guard, the report and the tests all land and nothing changes behavior until a human flips one default. The question is genuinely the maintainer's, on two grounds the repository cannot settle. FIRST, it decides what a routine setter is ALLOWED TO TOUCH: with the default ON, `aw backlog set graduated` begins editing other agents' plan files, which is a contract question about blast radius, not a technical one. SECOND, the two candidate in-flight rules have different costs and the choice is a risk-appetite judgement: SKIP AND REPORT (this plan's implementation) can never strand a lane but leaves a stale entry behind whenever a receipt is live, while REWRITE AND RE-FREEZE would keep every citation correct but requires a setter to re-sign another plan's frozen contract, which is an authority a setter does not have today and which F-04 shows would otherwise refuse at finalize. The evidence a decision needs is in F-04 (the measured stranding condition), F-06 (the same exposure already accepted on `aw rename`) and F-07 (the deliberate declaration a blind rewrite would corrupt).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending.

- [ ] V-01 validates E-01
  - Required evidence: the pasted dated re-measurement line from Findings, plus the actual driven output for each of the five measurements: the per-classification counts, the `[]` from the name-keyed call, the two-edit list from the path-keyed call, the `widening_is_acceptable=False` line, and the live-receipt count. A statement that the figures "were re-measured" is NOT evidence; the outputs must appear.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff DECISIONS.md` showing exactly ONE added `### D<n>` entry and no modification to any existing entry (an append-only diff: additions only). The pasted entry must visibly contain all five required elements (question, three options, measured hazard with driven output, the F-07 counter-example, chosen posture) and the three house subheadings (Decision, Alternatives considered, Trade-off). Evidence must also show the re-derived next decision number and that it does not collide with an existing one.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output of driving the new helper on a scratch repo with a path-keyed map, showing the two planned edits; plus `git diff --stat agent_workflows/artifact_refs.py` showing ONLY an addition, and a pasted confirmation that `plan_reference_rewrites`, `apply_reference_rewrites`, `_mask_fenced_code`, `_mask_permalinks` and `_boundaried` are unmodified in that diff.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted output showing the guard classifying a citing plan WITH a live receipt as must-skip and one WITHOUT as rewritable; plus pasted evidence of the fail-closed branch, i.e. an unreadable or undeterminable receipt classified as in-flight (skip). Must also show the guard does not define a second liveness notion, by naming the reused symbol in the pasted code excerpt.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted end-to-end run of a status transition on a scratch repo with the opt-in ON, showing the citing plan's `Scope-Paths` entry rewritten and the record relocated; plus the same transition with the opt-in absent showing the citing file byte-unchanged (`git diff` empty for it). Must also paste the relevant excerpt proving the `git_mv`-then-write order and the early-return condition are intact.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted stdout from a transition that rewrote at least one citation AND skipped at least one in-flight citation, showing both lines, with the skip line naming the skipped plan and the live-receipt reason.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted BARE `python3 -m pytest` summary line showing `N passed`, plus the pasted targeted run of `tests/test_artifact_refs_rewrite.py tests/test_status_set.py tests/test_scope_path_target_stale.py`. The five new tests must be named in the evidence and must be shown passing. Must also confirm no test reads production source text, counts callers, or asserts on comments (GUIDING_PRINCIPLES P16).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added bullet under the existing `## 2.0.0 (pending)` heading and no other change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries no `- Readiness:` field, which is the correct absent state for an unreviewed plan: that field is an OUTPUT of `/plan-review` and hand-writing it would forge the attestation the auto-approve predicate reads first. It requires explicit human approval before execution.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE and paste the actual runner output; never claim a test result that was not produced. Mark an `E-*` item `performed` only after performing it, and a `V-*` item `pass` only after inspecting the evidence in a separate pass. Do not claim done, and do not move this plan to `.aw/records/plans/executed/`, until `aw ipd lint --phase pre-transition` reports conforming and every `V-*` item carries concrete pasted evidence with `Result: pass`.

A NOTE ON THIS PLAN'S OWN EXECUTION, given the defect class it addresses: this plan is immune to that defect by construction, because none of its six declared paths lies under `.aw/records/` and `check_engine.stale_record_scope_paths` examines only entries beginning `.aw/records/`. So no status transition by a concurrent agent can stale this plan's declared scope, nothing here can be classified `moved` or `vanished`, and the runner's dispatch gate (which refuses only on `moved-terminal` and `vanished`) has nothing to refuse. An EARLIER draft of this plan declared a `.aw/records/decisions/...` path for the decision record and would have been dispatch-refused as `vanished` before its session started, since that predicate reports a not-yet-created records path (the shape `guti33` F-11 measured and deliberately left alone); routing the decision to `DECISIONS.md`, which is where this repository actually keeps decisions, removes that self-inflicted refusal as well as the invented tree.
