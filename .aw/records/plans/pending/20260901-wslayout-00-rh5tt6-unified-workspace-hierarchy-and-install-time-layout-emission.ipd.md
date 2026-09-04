# IPD: Unified Workspace Hierarchy and Install-Time Layout Emission Orchestrator

- Date: 2026-09-01
- Kind: orchestrator
- Concern: Workspace layout definitions are currently fragmented across 5 Python modules and inaccessible to non-Python tooling. Spec kw5y2s establishes a single-source Python layout model in layout.py and install-time emission of .aw/system/layout.json and schema for non-Python tools.
- Scope: Coordinate execution of the 5-plan child set wslayout implementing Spec kw5y2s across core modeling, internal module consolidation, install-time emission, and CLI surface.
- Scope-Paths: agent_workflows/layout.py, agent_workflows/artifact_types.py, agent_workflows/selectors.py, agent_workflows/record_producers.py, agent_workflows/project_schema.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/command_surface.py, agent_workflows/doctor.py, .aw/.gitignore, tests/
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: wslayout
- Order: 0
- Highest E allocated: 02
- Author: antigravity
- Id: rh5tt6
- From-Spec: kw5y2s

## Workflow history
- 2026-09-04 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 5 (orchestrator rh5tt6 only): APPROVE WITH REVISIONS APPLIED; PR-024..PR-030 all FIXED. The round-4 spec-gate REOPENING is STALE: kw5y2s was re-approved --by-human 459s AFTER the plans were demoted (298be4b2 -> 3e05c2ba), so ipd-lifecycle.md:16 is satisfied and readiness moves no-go -> go-pending-approval. PR-024 HIGH: stale reopened-gate claim, fixed here and in all five children. PR-025 HIGH: Scope-Paths union claim was FALSE (missing .aw/.gitignore, command_surface.py, doctor.py). PR-026 HIGH: emission has TWO CLI install paths (aw setup via cli._install_one), so the call must sit inside install_into_repo. PR-027 HIGH: 'root .gitignore untouched' asserted something false about the installer, and .aw/.gitignore is GENERATED so hauwqh must edit the template AND the back-fill list. PR-028 MEDIUM: engine.install() survived in OQ-03 after round 4 claimed it corrected. PR-029 MEDIUM: stale collision/count baselines re-measured (16 not 6 lifecycle diagnostics; 2r306y not e32j35). PR-030 MEDIUM: contract clause 1 called two resolved child OQs open, and the honesty rule was missing. Five children remain Status: to-review and were NOT review candidates this round.
- 2026-09-04 to-review (aw set): Applied deterministic plan-review repairs; controlling spec kw5y2s awaits renewed human approval.

- 2026-09-04 reviewed (antigravity): /aw plan-review-long: APPROVE WITH REVISIONS APPLIED; PR-019..PR-023 fixed across Set (all 5 children reviewed and brought to Status: reviewed with execution contracts and readiness; F-9 advisory resolved).
- 2026-09-02 reviewed (aw set): plan-review round 2 (orchestrator): APPROVE WITH REVISIONS APPLIED; PR-010..PR-014 fixed; spec kw5y2s now approved so the round-1 external gate is cleared

- 2026-09-01 draft (antigravity): created orchestrator.
- 2026-09-01 to-review (antigravity): authored complete orchestrator plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001..PR-008. Author-phase lint conforming for all six plans; every finding is semantic. Review record: .aw/records/reviews/20260901-wslayout-00-rh5tt6-unified-workspace-hierarchy-and-install-time-layout-emission.review.md
- 2026-09-01 /plan-review question loop (maintainer): OQ-1 and OQ-2 asked interactively and ANSWERED, so neither remains blocking. OQ-1 = UNION vocabulary (keep `roadmaps`, add `reviews`/`backlog`/`other`). OQ-2 = emitted layout files GITIGNORED via the framework-owned `.aw/.gitignore`. Verdict unchanged (the remaining findings still require a replan).
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all eight findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2 at HEAD `12159af5`, scoped to the ORCHESTRATOR: APPROVE WITH REVISIONS APPLIED; PR-010..PR-014 all FIXED. THE ROUND-1 BLOCKER IS CLEARED: spec `kw5y2s` is now `approved` `--by-human`, so `ipd-lifecycle.md:16` is satisfied and readiness moves NO-GO -> GO - PENDING HUMAN APPROVAL. Round 1's fixes were VERIFIED against the children rather than trusted (dependencies reconciled, union vocabulary pinned, the two missing test files now created by their owners, `test_setup_repo_cli.py` dropped), and the union claim was re-measured against live code (10 + 9 -> 12 = eleven classes plus the `records` carve-out; exclusions exactly seven). PR-010 HIGH: the orchestrator had NO execution contract; added ten clauses including a scope fence, the honesty rule, path-scoped commits, and the expected-`tk1gqo`-diagnostic note, plus the two MEASURED live scope collisions (`e32j35` on `selectors.py`, `6knsrx` on `engine.py`) with per-child re-measurement required. PR-011 HIGH: both V-items were unfalsifiable one-liners; V-01 now demands per-child executed-path, status, lint and NON-EMPTY child evidence, and V-02 demands the end-to-end install/gitignore/read/absent proof that no child owns. PR-012 MEDIUM: completion criteria still asserted `aw setup-repo` bakes files, contradicting round 1's own PR-003 fix. PR-013 MEDIUM: cross-IPD validation was four vague bullets, now five falsifiable cross-cutting assertions with measured baselines. PR-014 LOW: prose-bullet Findings converted to the evidence table the template expects. Status to-review -> reviewed. Review record round 2 appended.

## Goal

Coordinate the implementation of Spec kw5y2s across 5 child plans, ensuring zero regression to existing Python callers and deterministic emission of .aw/system/layout.json during install.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Child Set Execution & Integration

- [ ] E-01 Track and coordinate execution of child plans wpu5zu (Order 01), zvk796 (Order 02), rodj06 (Order 03), hauwqh (Order 04), and 30jug9 (Order 05).
  - Depends on: none
  - Expected outcome: All 5 child plans executed, verified, and finalized into executed/.
  - Execution state: pending
  - SERIAL, IN TABLE ORDER, and gated on the predecessor reaching `executed`. Metadata verified at round 5 against the sequence table, value by value: `zvk796`, `rodj06` and `hauwqh` each declare `- Item-Dependencies: executed:wpu5zu` (they import `layout.py`), and `30jug9` declares `executed:hauwqh,executed:zvk796` (BOTH, correcting this item's earlier "05 declares `executed:hauwqh`", which named only one of the two). Do not re-derive the sequence from prose; read the metadata.
  - BEFORE EACH CHILD, re-measure concurrent scope collisions per execution-contract item 5. This is a per-child action, not a one-time Set-start check, because colliding work may land mid-Set. Round-5 live overlaps: `selectors.py` vs APPROVED `2r306y` (hits Order 02), `cli.py` vs 7 non-wslayout pending plans (hits Order 05). Round 2's `e32j35` and `6knsrx` are both superseded and are NOT current examples.
  - Coordination only: this item performs NO product edit and writes no code.

### Task group 2: End-to-End Release Gate & Conformance

- [ ] E-02 Execute repository-wide test suite and leak sanitization across all integrated layout changes.
  - Depends on: E-01
  - Expected outcome: Full pytest test suite passes bare, aw check passes, aw sanitize passes clean.
  - Execution state: pending
  - AND PERFORM THE END-TO-END BEHAVIORAL PROOF, which is the part no child owns: in a temporary target repo, run a real install, confirm both layout files were emitted, confirm both are gitignored through the framework-owned `.aw/.gitignore` and that the ROOT `.gitignore` carries no layout entry (NOT that the root file is unchanged; the installer legitimately writes an `aw:block` into it), confirm the layout surface reads the emitted file, and confirm it degrades gracefully when the file is absent (the fresh-clone case the GITIGNORED ruling creates).
  - Also run the cross-IPD vocabulary-parity assertion (see Cross-IPD validation): the combined result of Orders 02 and 03 is the shipping state, and no single child observes it.
  - Run the suite BARE, `python3 -m pytest`, from the PRIMARY checkout. Do not add `-n0`, a second `-q`, or `-p no:randomly`; `pyproject.toml` `addopts` already supplies the intended flags.

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Set dependencies |
|---:|---|---|---|
| 01 | `wpu5zu` | Core Layout Model and JSON Schema in layout.py | approved spec |
| 02 | `zvk796` | Consolidate artifact_types.py and selectors.py into layout model | 01 |
| 03 | `rodj06` | Consolidate record_producers.py and project_schema.py into layout model | 01 |
| 04 | `hauwqh` | Install-time layout.json and schema emission in engine.py | 01 |
| 05 | `30jug9` | Add aw layout CLI command and workspace health check rule | 02 and 04 |

## Completion criteria (the whole Set is done only when)

- `agent_workflows/layout.py` exists as the single source of truth for workspace layout definitions, carrying the UNION vocabulary (eleven record classes plus the `records` root carve-out) per the maintainer ruling.
- `artifact_types.py`, `record_producers.py`, `selectors.py`, and `project_schema.py` re-export from `layout.py` with backward compatibility PROVEN, not asserted: every public name each module exported before still exists with an identical value, and the bare full suite passes.
- `engine.install_into_repo()` (`engine.py:5420-5576`) bakes `.aw/system/layout.json` and `.aw/system/layout.schema.json` during installation, as the SOLE emission site. The emission call MUST live inside `install_into_repo` itself, not in a caller: verified at round 5 that the function has three callers (`engine.run()` for `aw install` at `:5656`; `cli._install_one` for `aw setup` at `cli.py:4226`, reached from `cli._run_setup:5748`; and direct library use), so wiring a caller would leave `aw setup` silently un-emitting.
- `/aw setup-repo` is NOT a CLI verb (round 1 PR-003): it is an agent slash-command backed by a workflow body, and it inherits emission transitively from `aw install` with no code of its own. `aw setup`, by contrast, IS a real CLI verb and a genuine second install path; it inherits emission only because it funnels through `install_into_repo`.
- Both emitted files are GITIGNORED via the framework-owned `.aw/.gitignore`, and the user's root `.gitignore` carries NO layout entry. Stated precisely at round 5 (PR-027): "root `.gitignore` untouched" was WRONG as a completion criterion, because `install_into_repo` already writes an untracked-safety `aw:block` and the installer-backups line into that file (`engine.py:2576,2698-2735` via `:5506-5507`). The requirement is that this Set adds no layout entry there, not that the file never changes.
- The gitignore entries reach BOTH a fresh install and an already-installed repo, because a target's `.aw/.gitignore` is generated from `engine._AW_GITIGNORE_TEMPLATE` and back-filled by `_ensure_aw_gitignore`; editing only this repo's checked-in copy would be a no-op for every target (`hauwqh` E-02).
- The layout surface (`aw layout` or whatever `30jug9` OQ-01 settles on) and `aw check` verify layout presence and validity, and both behave correctly when the file is ABSENT (the fresh-clone case).
- All 5 child plans are finalized in `executed/` with every `V-*` carrying non-empty pasted evidence.
- Full pytest suite passes bare, `aw sanitize` is clean, and no NEW `aw check` diagnostic CLASS appeared. Compare CLASSES, not counts, against a baseline you measure yourself on unmodified HEAD immediately before Order 01. The "six" figure repeated by earlier rounds is now WRONG: re-measured at round 5, `check.lifecycle-transition-invalid` fires 16 times repo-wide, 14 of them on these six wslayout plans (up from 6 because every review round APPENDS a history line and each new line adds another derived transition for the inverted parser to reject), and `aw check` overall reports 35 findings across six rule classes (`check.lifecycle-transition-invalid` 16, `check.name-nonconformant` 7, `check.scope-drift` 5, `check.setid-collision` 5, `check.from-backlog-dangling` 1, `check.from-backlog-gate-mismatch` 1), none of which this Set causes. THE COUNT WILL RISE AGAIN as this Set's own execution writes history lines, so a count-based assertion would fail for a reason unrelated to the work; that is exactly why the criterion is class-based.

## Cross-IPD validation

These are the checks NO single child can perform, which is the orchestrator's reason to exist.

- THE VOCABULARY DID NOT NARROW END TO END. After all children, assert the model's `record_classes` is still a superset of both live source vocabularies. RE-MEASURED AT ROUND 5 and unchanged, so this baseline is current, not inherited: `ARTIFACT_TYPES` has 10 members (`backlog, comms, other, plans, prompts, releases, research, roadmaps, specs, walkthroughs`), `RecordClass` has 9 (`comms, plans, prompts, records, releases, research, reviews, specs, walkthroughs`), whose union is 12 names, which is the eleven modeled classes PLUS the `records` root carve-out held separately. `roadmaps` must still be present and `aw rename roadmaps` / `aw group roadmaps` must still work. RE-MEASURE THE BASELINE YOURSELF before Order 01 rather than quoting these numbers: three of the four modules named here are edited by this Set, and a number quoted from a review round is evidence about the past.
- THE EMITTED FILE MATCHES THE MODEL. Compare the schema `layout.py` generates against the emitted `.aw/system/layout.json`, in a temporary repo, after a real install.
- BACKWARD COMPATIBILITY ACROSS THE WHOLE SUITE, not per child. Each consolidating child validates its own two files plus the bare suite; only here is the COMBINED result of Orders 02 and 03 observed, which is the state that actually ships.
- THE NET-NEW CLI BEHAVIOR WORKS. `aw check reviews` errors today (re-measured at round 5, unchanged: `outcome: error, exit 2, target: reviews`). The union vocabulary makes `reviews` a CLI noun, so that command MUST succeed after the Set, and `aw check roadmaps` must not have regressed. Assert both. The conditional "If" was removed at round 5: spec Section 3.2 item 2 states plainly that `reviews` becoming an accepted noun is intended net-new behavior the implementing plan must test, so this is a requirement, not a contingency.
- THE `other` COMPLEMENT DID NOT SWALLOW `reviews`. This is the cross-cutting half of a trap `wpu5zu` F-5 records only for itself, and it is measured differently NOW than the round-2 text claims. `selectors.record_dirs(repo, "other")` returns `['.aw/records/prompt-library']` today, NOT the `['.aw/records/reviews', '.aw/records/prompt-library']` the earlier rounds recorded, because commit `d802e917` ("stop the `other` catch-all from claiming the reviews tree") added `NON_PRIMARY_RECORD_DIRS = frozenset({'reviews'})` to `_OTHER_SWEEP_SKIP_DIRS` (`selectors.py:183-185`). Order 02 owns preserving that isolation; the CROSS-CUTTING risk is that Order 02 preserves it while Order 03 simultaneously adds `reviews` as an ordinary `RecordClass` member with `subpath: reviews`, and only the combined state reveals whether `other` re-captured the reviews tree. After all children, assert `record_dirs(repo, "other")` still EXCLUDES any reviews path.
- THE FRESH-CLONE CASE. Because emission is gitignored, a fresh clone has no `layout.json` until an install runs. Assert every reader tolerates its absence rather than crashing, and that `aw check` reports the absence as the distinguished non-failing state the spec's ruling requires.

## Project conventions discovered (Step 0)

- `agent_workflows/`: Core framework modules.
- `Spec kw5y2s`: Unified Workspace Hierarchy Specification and Machine-Readable Install-Time Layout Emission, now `approved` (F-2).
- A lifecycle transition is a POST-gate step performed with `aw ipd finalize`, never an E-item (`ipd-lifecycle` workflow).
- Execution against an unapproved controlling spec is forbidden (`ipd-lifecycle.md:16`); that gate is now satisfied.
- `.aw/.gitignore` is the FRAMEWORK-OWNED ignore file and already carries this convention for other generated paths; the user's root `.gitignore` is never touched (`.aw/.gitignore:1-15`).
- `engine.install_into_repo()` (`engine.py:5420-5576`) is the sole install CHOKEPOINT in Python, and wiring emission there covers every user-facing install path BY CONSTRUCTION. Verified at round 5 that there are THREE distinct callers, which the earlier "sole install entry point" wording obscured: `aw install` via `engine.run()` (`engine.py:5656`), `aw setup` (the machine-wide first-run wizard) via `cli._run_setup` -> `cli._install_one` (`cli.py:5748` -> `cli.py:4226`), and direct library use. `aw setup` is a REAL second CLI verb, not a synonym for `aw install`; because both funnel through `install_into_repo`, one emission site still suffices, but a plan that wired emission into `engine.run()` instead would silently miss `aw setup`.
- `/aw setup-repo` is an agent slash-command backed by a workflow body with no Python call site, and `aw install` RECOMMENDS it as a follow-up (`engine.py:3600-3607`, "NEXT STEP ... run /setup-repo"). There is no `aw update` verb. Note the line range earlier rounds cited for this text (`3581-3597`) is off: the recommendation block is at `3598-3613` inside `print_summary` (`engine.py:3515-3613`), and `3581` lands on the staging notice above it.
- `.aw/.gitignore` in a TARGET repo is GENERATED from `engine._AW_GITIGNORE_TEMPLATE` (`engine.py:4208-4222`) by `_ensure_aw_gitignore` (`:5236-5261`), not copied from this repo's file. So `hauwqh` E-02 must add the two entries to BOTH the template (for fresh installs) AND the back-fill `additions` list (for repos installed before this change), which is exactly the idempotency requirement E-02 states; editing only the checked-in `.aw/.gitignore` would change nothing for any target.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies the intended flags.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The decomposition is sound and survived two review rounds.** Pure new code first (Order 01), isolated refactor of legacy modules second (02 and 03), install emission third (04), user-facing surface last (05). Round 1's own REPLAN call was withdrawn on exactly this basis: the sequence was never the problem. | Round 1 review record, D-6. |
| F-2 | **THE SPEC GATE IS CLEARED AGAIN; the round-4 "reopened" claim was true when written and is now STALE.** The terminology correction was reviewed and RE-APPROVED after the plans were demoted: spec `kw5y2s` is `- Status: approved` with a `--by-human` attestation. The demotion commit `298be4b2` (00:10:38 -0400) PRECEDED the re-approval commit `3e05c2ba` (00:18:17 -0400) by 459 seconds, which is why the plan text outlived its own premise. `ipd-lifecycle.md:16` is satisfied; the remaining gate is ordinary human approval of these six plans. | `.aw/records/specs/20260901-kw5y2s-...spec.md:4` (`- Status: approved`) and its history line `2026-09-04 approved (aw set, --by-human)`; `git log` timestamps of `298be4b2` vs `3e05c2ba`; `aw specs check --agent` -> `outcome: clean, checked: 26`. |
| F-3 | **Round 1's fixes are REAL, re-verified at round 5 by re-reading the children rather than trusting the record.** `Item-Dependencies` match the sequence table on all five children (`zvk796`/`rodj06`/`hauwqh` -> `executed:wpu5zu`, `30jug9` -> `executed:hauwqh,executed:zvk796`); `wpu5zu` E-01 carries the union vocabulary with the `records` carve-out, the `other` complement carve-out and pinned exclusions; `rodj06` E-02 and `hauwqh` E-03 CREATE the previously-missing test files; `tests/test_setup_repo_cli.py` is gone from scope. Re-confirmed absent on disk at round 5: `agent_workflows/layout.py`, `tests/test_layout.py`, `tests/test_record_producers.py`, `tests/test_engine_install.py`, `tests/test_cli_layout.py` all do not exist, so every "CREATE" claim in the Set is still a create. | Round-5 scan of `- Item-Dependencies:` across the Set; `ls` of the five not-yet-existing paths; `wpu5zu` E-01 consumer-interface block; `rodj06` E-02; `hauwqh` E-03. |
| F-4 | **The union vocabulary claim CHECKS OUT against live code, RE-MEASURED at round 5 and unchanged.** `ARTIFACT_TYPES` = 10 members, `RecordClass` = 9, union = 12 names, which is exactly the eleven modeled record classes plus `records` held separately as the empty-subpath carve-out (`_RECORD_CLASS_SUBPATHS[RecordClass.RECORDS] == ""`). `EXCLUDED_RECORD_DIRS` is exactly the seven the plans pin (`.git, .system_generated, __pycache__, runs, scratch, temp, tmp`). Aliases include `roadmap -> roadmaps` and `misc`/`others -> other` as `wpu5zu` E-01 requires. `KNOWN_PRIMARY_TYPES` is the distinct 9-member set (`ARTIFACT_TYPES` minus `other`). | Live import at round-5 HEAD `cf7dceea` (the round-2 citation `12159af5` is stale); `record_producers.py:136`; `artifact_types.py:12-39`; `selectors.EXCLUDED_RECORD_DIRS`, `selectors.KNOWN_PRIMARY_TYPES`. |
| F-5 | **Both premises the Set relies on are STILL true at round 5, so its work is not already done.** `aw layout` does not exist (`invalid choice: 'layout'`, and the verb list printed by the parser confirms it), and `aw check reviews` still errors (`outcome: error, exit 2, target: reviews`), which is the net-new behavior `30jug9` owns. | `python3 -m agent_workflows layout`; `aw check reviews --agent`, both re-run at round 5. |
| F-6 | **PR-009's tooling defect is unresolved, WILL fire during execution, and its count GROWS with every review round.** Re-measured at round 5: `check.lifecycle-transition-invalid` fires 16 times repo-wide (14 on these six plans, 2 on unrelated ones), up from the 9/6 recorded at round 2, because each appended history line yields another derived transition for the newest-first-assuming parser to reject. Backlog `tk1gqo` is still `open` AND carries `- Blocks-Release: next`. The executor must expect the diagnostic, must NOT "fix" it by reordering histories, and must assert diagnostic CLASSES rather than counts. | `aw check plans --agent` at round 5 (16 total, 14 on wslayout); `.aw/records/backlog/open/20260901-historder-01-tk1gqo-...backlog.md:2-3`. |
| F-7 | **REVIEW FINDING (round 2): the orchestrator had NO execution contract at all**, while its own children and comparable orchestrators in this repo carry one (compare `3m0urk`'s eight-clause contract). Added, including the scope fence, the honesty rule, path-scoped commits, and the lifecycle-transition-is-not-an-E-item rule. | Round 2 diff of this file; `3m0urk` gate section. |
| F-9 | **RESOLVED (round 4): the five children are now reviewed and Status: reviewed.** The full Set was reviewed in batch; all child plans now carry execution contracts, verified citations, bare suite validation with baseline re-measurement, and `- Readiness: go-pending-approval`. | Round 4 review across the Set; all children `Status: reviewed`. |
| F-13 | **THE SET CANNOT EXECUTE YET, and the reason is now the CHILDREN's readiness rather than the spec.** Round 5 reviewed the ORCHESTRATOR only (the invocation named this file alone), so this plan is `reviewed` / `go-pending-approval` while all five children remain `Status: to-review` / `Readiness: no-go` from the round-4 demotion. Round 5 DID correct the stale reopened-spec-gate paragraph inside each child (that claim was false in all six files), but correcting one false paragraph is NOT a review, so no child was promoted. CONSEQUENCE: before Order 01 may run, either re-review the five children (`/plan-review` or `/plan-review-long` over Set `wslayout`) so they can reach `reviewed`/`go-pending-approval`, or have the maintainer approve them directly. Do not read this orchestrator's `go-pending-approval` as clearance for the Set. | This plan `- Status:`/`- Readiness:` vs each child's; round-5 edits to the five children's gate paragraphs; commit `298be4b2` (the demotion). |
| F-10 | **REVIEW FINDING (round 5): the `Scope-Paths` union claim was FALSE as declared.** Three paths declared by children were absent from this orchestrator's `Scope-Paths`: `.aw/.gitignore` (`hauwqh` E-02), `agent_workflows/command_surface.py` and `agent_workflows/doctor.py` (both `30jug9` E-01/E-02). Since the plan's own `Scope check` asserts its scope IS the children's union, the declaration contradicted the plan. Added; re-verified that every child-declared path is now covered. | Round-5 set-difference of the children's `- Scope-Paths:` against this plan's; `30jug9:7`; `hauwqh:7`. |
| F-11 | **REVIEW FINDING (round 5): emission has TWO CLI install paths, and the plans described only one.** `install_into_repo` is a chokepoint with three callers: `engine.run()` for `aw install`, `cli._install_one` for `aw setup` (a real verb, the machine-wide first-run wizard, distinct from both `aw install` and the `/setup-repo` slash-command), and direct library use. Wiring emission inside the shared function is correct and covers all three; wiring a caller would leave `aw setup` silently un-emitting, and no validation as previously written would have caught it. | `agent_workflows/engine.py:5420-5576`, `:5656`; `cli.py:5639-5757`, `:4202-4314`, `:4226`; verified by calling `install_into_repo` directly into a temporary repo at round 5. |
| F-12 | **REVIEW FINDING (round 5): the "root `.gitignore` untouched" criterion asserted something FALSE about the installer.** `install_into_repo` legitimately writes an untracked-safety `aw:block` and the installer-backups line into the TARGET's root `.gitignore` (`:2576`, `:2698-2735`, called at `:5506-5507`), verified in a temporary installed repo. The criterion is now "the root file carries no LAYOUT entry". Separately, a target's `.aw/.gitignore` is GENERATED from `_AW_GITIGNORE_TEMPLATE` and back-filled by `_ensure_aw_gitignore`, so `hauwqh` E-02 must edit both the template and the back-fill list; editing this repo's checked-in copy alone is a no-op for every target. | `engine.py:2576,2698-2735,4208-4222,5236-5261,5506-5507`; temporary-repo install at round 5 showing the root `aw:block` plus a preserved pre-existing user line; template-vs-installed-file diff. |
| F-8 | **Concurrent scope must be re-measured immediately before each child, and round 5 measured the CURRENT collisions rather than only saying the old ones expired.** Round 2's named conflicts are indeed gone: `e32j35` and `6knsrx` are both `Status: superseded` under `plans/superseded/`. The LIVE overlaps today are: `agent_workflows/selectors.py` declared by APPROVED plan `2r306y` (Set `rununify`), which `zvk796` rewrites; and `agent_workflows/cli.py` declared by 7 non-wslayout pending plans (`0soncw` approved, `mjx7ne` approved, `d7bnhc` approved, `p0l1to` reviewed, `ygzq71` reviewed, `p7xhhm` reviewed, `i6015i` reviewed), which `30jug9` edits. `engine.py`, `check_engine.py`, `record_producers.py`, `project_schema.py` and `artifact_types.py` currently have NO non-wslayout claimant. | Round-5 scan of `- Scope-Paths:` across `.aw/records/plans/pending/*.ipd.md` with each plan's `- Status:`; `2r306y:7,9`; `e32j35`/`6knsrx` resolved under `plans/superseded/`. |

## Proposed changes (ordered, validatable)

1. Execute Plan 01 (wpu5zu): Core Layout Model & JSON Schema in layout.py.
2. Execute Plan 02 (zvk796): Consolidate artifact_types.py and selectors.py.
3. Execute Plan 03 (rodj06): Consolidate record_producers.py and project_schema.py.
4. Execute Plan 04 (hauwqh): Install-time layout.json and schema emission in engine.py.
5. Execute Plan 05 (30jug9): Add aw layout CLI command and workspace health check rule.
6. Verify orchestrator end-to-end integration (E-02).

## Deferred / out of scope (with reason)

- Out of scope: changing on-disk layout paths of existing records (spec maintains exact path compatibility).

## Scope check

- Over-scope: none. This orchestrator's `Scope-Paths` is the UNION of what the children edit (verified at round 5 after adding the three paths it was missing); the orchestrator's own commits touch only this plan file. Recorded so the breadth is understood as delegation, not as an intent to edit eleven modules from here.
- Under-scope: none in this plan. Note the children own two test files that DO NOT EXIST yet and must be CREATED, not edited (round 1 PR-002, verified still absent at round 2): `tests/test_record_producers.py` (created by `rodj06` E-02) and `tests/test_engine_install.py` (created by `hauwqh` E-03). `tests/test_layout.py` is likewise new (`wpu5zu` E-02). `tests/test_setup_repo_cli.py` was correctly DROPPED from scope, since no such CLI surface exists.
- Concurrent-scope collision, recorded rather than resolved, RE-MEASURED at round 5 (PR-010, PR-029): `agent_workflows/selectors.py` is also declared by APPROVED plan `2r306y` (Set `rununify`), and `agent_workflows/cli.py` by 7 non-wslayout pending plans. The round-2 examples (`e32j35`, `6knsrx`) are both superseded. See execution-contract item 5; the mitigation is re-measurement immediately before each child, not a change to this plan's scope.
- Round 5 also RECONCILED `Scope-Paths` with the children's actual union, which had drifted: `.aw/.gitignore` (edited by `hauwqh` E-02), `agent_workflows/command_surface.py` and `agent_workflows/doctor.py` (both edited by `30jug9`) were declared by children but ABSENT from this orchestrator's declaration, so the union claim below was false as written. The four new test files are covered by the `tests/` directory entry. Verified after the fix: every child-declared path is now covered by this plan's `Scope-Paths`.

## Required tests / validation

- Every child's own validation suite passing, with actual pasted output per child.
- Bare full repository `python3 -m pytest` from the PRIMARY checkout, baseline re-measured on unmodified HEAD at execution time (round 1 observed `4004 passed, 3 skipped, 4 xfailed`; treat that as historical, not as the target).
- `aw check --agent` showing no NEW diagnostic CLASS versus a baseline measured on unmodified HEAD at execution time. `check.lifecycle-transition-invalid` is expected and is a known tooling defect (backlog `tk1gqo`); do NOT assert a fixed count, which grows as history lines accumulate (re-measured at round 5: 16 repo-wide, 14 on this Set).
- `aw sanitize --agent` passing clean.
- The end-to-end install-and-read proof described in V-02, performed in a temporary target repo, which is the only evidence that the Set's actual purpose was achieved.

## Spec / documentation sync

- Aligned with spec `kw5y2s`, which is `approved` again after the maintainer-directed installer and layout-API terminology correction was reviewed and re-approved `--by-human` (F-2). Treat the approved spec as IMMUTABLE during execution: a plan-time edit to an approved spec would invalidate the attestation.
- If execution discovers a further factual defect in the spec, do not silently diverge and do not edit it: record the discrepancy and report it, since only the maintainer may re-approve.
- No user-facing documentation is named by this orchestrator. The user-visible surface (`aw layout` or its chosen alternative) is `30jug9`'s, and its own plan owns any docs and completion wiring that surface needs.

## Open questions

### OQ-01: What is the true unified record-class vocabulary?

- Blocking: no
- Status: resolved
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-01 by the maintainer, asked interactively: the
  vocabulary is the UNION. Keep every type that exists today, INCLUDING `roadmaps`, and ADD the missing
  ones (`reviews`, `backlog`, `other`) where a module lacks them. The model DOCUMENTS reality rather
  than redefining it, so the consolidation deletes nothing and breaks nothing.
  WHY THE QUESTION EXISTED: draft spec `kw5y2s:59-73` presented a `record_classes` table as the single
  source of truth, but it matched NEITHER existing vocabulary. Measured at HEAD: `ARTIFACT_TYPES`
  (`agent_workflows/artifact_types.py:12-23`) contains `roadmaps`, which the spec omitted; `RecordClass`
  (`agent_workflows/record_producers.py:85-101`) contains `records` (empty subpath, `:136`), which the
  spec omitted; the spec added `reviews` (not an accepted CLI noun: `aw check reviews` errored) and
  `backlog`/`other` (absent from `RecordClass`). `roadmaps` is live in 12 modules with working verbs
  `run_rename_roadmaps`/`run_group_roadmaps` (`agent_workflows/artifact_rename.py:827-828,855-856`) and
  5 artifacts on disk, so deriving from the spec's list would have deleted a shipped CLI surface.
  WHERE IT IS NOW ENCODED: spec Section 3.2 (eleven classes with per-row provenance) and Section 3.2.1
  (the `records` empty-subpath carve-out); `wpu5zu` E-01/E-02 and V-01; `zvk796` E-01 and V-01;
  `rodj06` E-01 and V-01; `30jug9` E-03 and V-03.
  CONSEQUENCES CARRIED: `roadmaps` must survive every derivation; `records` needs an explicit carve-out
  rather than an ordinary subpath entry; and `reviews` becoming a CLI noun is net-new behavior that
  `aw check reviews` must now accept, tested rather than assumed.

### OQ-02: Is the emitted `.aw/system/layout.json` git-tracked or gitignored?

- Blocking: no
- Status: resolved
- Finding: PR-004
- Resolution or deferral rationale: RESOLVED 2026-09-01 by the maintainer, asked interactively:
  GITIGNORED, via a `.gitignore` INSIDE the `.aw/` directory (the framework-owned file), never the
  user's root `.gitignore`.
  WHY THE QUESTION EXISTED: the spec's own rationale for install-time emission is to eliminate git drift
  (`kw5y2s:40-43`), yet the plans never stated trackedness, and the two in-repo precedents point in
  OPPOSITE directions. `.aw/system/` is tracked here (156 files) and the sibling generated marker
  `.aw/system/VERSION` is tracked, while one day earlier the maintainer decided the analogous case the
  other way in backlog `ila6vl` (stop tracking the generated INDEX manifests, 328 commits in 14 days).
  Guessing would have either recreated that churn or contradicted the spec's stated purpose.
  WHY THE CHOSEN MECHANISM IS NOT NEW: `.aw/.gitignore` already exists and already carries this exact
  convention for four other generated or box-local paths, and its header states it "lives inside the
  framework-owned `.aw/` tree; it is NOT the user's root `.gitignore`" (`.aw/.gitignore:1-15`).
  WHERE IT IS NOW ENCODED: spec Section 2.3 (the ruling, its reasoning, and the consequence) and the
  updated Sections 6.1/7/8; `hauwqh` E-02 (add `system/layout.json` and `system/layout.schema.json`,
  idempotently) with V-02 requiring `git check-ignore -v` evidence and proof the root `.gitignore` is
  untouched; `30jug9` E-01 (the command must work with no emitted file) and E-02 (the presence/drift
  rule is the loud-failure backstop).
  CONSEQUENCE CARRIED: a fresh clone has NO layout.json until an install runs, so every non-Python
  reader must tolerate absence, CI reading it needs an install step first, and git will never show a
  diff for a stale emitted file, which is precisely why the `aw check` rule became required rather than
  optional.

### OQ-03: Which install entry point receives the emission wiring?

- Blocking: no
- Status: resolved
- Finding: PR-003
- Resolution or deferral rationale: RESOLVED 2026-09-01 (measured from the repository, then the spelling
  corrected by the maintainer): `engine.install_into_repo()` (`agent_workflows/engine.py:5420-5576`),
  reached by `aw install`, is the SOLE emission site. NAME CORRECTED AT ROUND 5: this paragraph still read
  `engine.install()` after round 4's PR-021 claimed the correction was applied "across `hauwqh` and
  `rh5tt6`"; it had in fact been missed here, and no function named `engine.install` exists.
  The draft spec and two plans named `aw setup-repo` and `aw update` as install entry points; neither is
  a CLI verb. The correct spelling is `/aw setup-repo` (alias `/setup-repo`), an AGENT SLASH-COMMAND
  backed by a workflow BODY (`.aw/system/workflows/setup-repo/setup-repo.md`, shim
  `.opencode/commands/setup-repo.md`; see `.aw/system/workflows/index.md:108,121`), so it has no Python
  call site into which file emission could be wired.
  THE RELATIONSHIP IS THE REVERSE OF THE PLANS' ASSUMPTION: `aw install` runs FIRST and then RECOMMENDS
  `/setup-repo` as a follow-up conformance pass (`agent_workflows/engine.py:3581-3597`, "NEXT STEP ...
  run /setup-repo"). `/aw setup-repo` therefore inherits emission transitively at zero cost, and no
  emission code belongs in the workflow body. There is likewise no `aw update` verb; `aw install` is
  idempotent and is itself the update path.
  WHERE IT IS NOW ENCODED: spec Section 6.1 (rewritten, with the four install-time steps and an explicit
  paragraph on why the slash-command needs no code) plus Sections 7.1 and 8.2; `hauwqh` E-01 (sole
  emission site) with V-01 requiring evidence that the workflow body is untouched, `Scope` and
  `Scope-Paths` corrected, and `tests/test_setup_repo_cli.py` dropped from scope because there is no
  such CLI surface to test.
  REFINED AT ROUND 5 (PR-026): "sole emission site" is correct about the FUNCTION but was being read as
  "sole install path", which is false. `install_into_repo` is a CHOKEPOINT with three callers, and the
  second CLI one is the real verb `aw setup` (the machine-wide first-run wizard), reached by
  `cli._run_setup` -> `cli._install_one` -> `engine.install_into_repo` (`cli.py:5748`, `:4226`). Wiring
  emission INSIDE `install_into_repo` covers `aw install`, `aw setup`, and library callers by
  construction; wiring it into `engine.run()` would cover only `aw install`. V-02 now demands proof the
  call sits in the shared function.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste, for EACH of the five children (`wpu5zu`, `zvk796`, `rodj06`, `hauwqh`, `30jug9`), its resolved path under `.aw/records/plans/executed/`, its `- Status: executed` line, and the `aw ipd lint --phase pre-transition --agent` result showing `conforming`. Then paste a per-child confirmation that every one of its `V-*` items carries NON-EMPTY observed evidence and `Result: pass`, because a child can be moved to `executed/` with blank evidence and this is the orchestrator's only chance to catch that.
  - PLUS the dependency-vs-table reconciliation, pasted as the LITERAL values, not as an assertion that they agree: each child's resolved `- Item-Dependencies:` beside the sequence-table row. Required result at completion time: `zvk796`, `rodj06`, `hauwqh` -> `executed:wpu5zu`; `30jug9` -> `executed:hauwqh,executed:zvk796` (BOTH edges, since Order 05 needs the `reviews` noun from Order 02 as well as emission from Order 04). A single-edge value on `30jug9` is a FAILED validation.
  - PLUS proof the EXECUTION ORDER actually observed matches that graph, from the children's own `## Workflow history` `executed` lines in chronological order. Metadata declaring an edge is not evidence the edge was honored, and a Set executed out of order can still leave every plan `executed` and every lint `conforming`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the COMPLETE bare `python3 -m pytest` summary line run from the PRIMARY checkout, with the baseline RE-MEASURED on unmodified HEAD at execution time and any delta explained change-by-change (do not reuse round 1's `4004 passed, 3 skipped, 4 xfailed`, which predates later commits).
  - PLUS `aw check --agent` output, asserting no NEW diagnostic CLASS versus the baseline you measured yourself on unmodified HEAD. Compare CLASSES, never counts: `check.lifecycle-transition-invalid` is EXPECTED (backlog `tk1gqo`) and its count RISES as this Set's own execution appends history lines, so a count assertion fails for an unrelated reason. Round-5 baseline for orientation only: 35 findings across `check.lifecycle-transition-invalid` (16), `check.name-nonconformant` (7), `check.scope-drift` (5), `check.setid-collision` (5), `check.from-backlog-dangling` (1), `check.from-backlog-gate-mismatch` (1).
  - PLUS `aw sanitize --agent` showing `outcome: clean`.
  - PLUS THE END-TO-END BEHAVIORAL PROOF this Set exists for, which no child owns alone, performed in a temporary target repo AFTER a real install: show `.aw/system/layout.json` and `.aw/system/layout.schema.json` were emitted; show `git check-ignore -v` attributes BOTH to the framework-owned `.aw/.gitignore`; show the target's ROOT `.gitignore` carries no layout entry (`grep -n layout .gitignore` -> no match). Do NOT assert the root `.gitignore` is unchanged: the installer legitimately writes an untracked-safety `aw:block` and the backups line into it (`engine.py:2576,2698-2735` via `install_into_repo:5506-5507`), verified in a temporary repo at round 5, so a no-diff assertion would fail correctly-working code.
  - PLUS both install-path proofs (PR-026), because `install_into_repo` has more than one CLI caller: show emission happens via `aw install` AND via `aw setup` (`cli._run_setup` -> `cli._install_one` -> `engine.install_into_repo`, `cli.py:5748,4226`). One of the two is enough ONLY if you also show the emission call sits inside `install_into_repo` itself rather than in a caller.
  - PLUS `aw layout` (the surface `30jug9` OQ-01 settled on) reading the emitted file, AND the same command degrading gracefully when the file is ABSENT (the fresh-clone case the GITIGNORED ruling creates).
  - PLUS the `other`-complement isolation assertion from Cross-IPD validation: `record_dirs(repo, "other")` still excludes every reviews path after Orders 02 and 03 have BOTH landed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXTERNAL SPEC GATE IS CLEARED (re-measured at round 5). The round-4 text said the gate was "reopened" because the maintainer-directed installer/layout-API terminology correction had returned spec `kw5y2s` to `to-review`. That correction was then reviewed and RE-APPROVED, but the plans had already been demoted 459 seconds earlier, so the claim outlived its premise. Measured now: `kw5y2s` is `- Status: approved` with a `--by-human` attestation in its workflow history, so `ipd-lifecycle.md:16` is satisfied. The ONLY remaining gate is ordinary human approval of these six plans (`Status: approved`), which no agent may self-grant.

RE-VERIFY THE GATE AT EXECUTION TIME RATHER THAN TRUSTING THIS PARAGRAPH. This Set has now twice carried a spec-gate statement that was accurate when written and false when read, in both directions. Before starting Order 01, run `aw specs set`-independent verification: read the spec's `- Status:` line and confirm it is `approved` with a `--by-human` history record. If it is anything else, STOP; that is a genuine prerequisite-absent condition, not a scope question.

Execution contract:

1. Human approval of the plans is required. ZERO open questions remain anywhere in the Set, re-verified at round 5: this orchestrator's OQ-01/02/03 are all `Status: resolved`, and the only two child questions (`zvk796` OQ-01 traversal exclusions, `30jug9` OQ-01 CLI naming) are BOTH `Status: resolved` by maintainer ruling on 2026-09-03, not `open` as clause 1 previously claimed. `rodj06`, `hauwqh` and `wpu5zu` carry none. Nothing in this Set is waiting on a decision; it is waiting only on a signature.
2. Execute children SERIALLY in the table order, and only after confirming the controlling spec is `approved` (see the gate paragraph above). Do not start Order 02, 03, or 04 before `wpu5zu` is `executed`, and do not start Order 05 before BOTH `zvk796` and `hauwqh` are `executed`: its `aw check reviews` proof needs the new noun from Order 02 and the emitted-layout behavior from Order 04.
3. THE HONESTY RULE, which outranks every convenience: when you report that tests passed, PASTE THE ACTUAL RUNNER OUTPUT. Never claim a result you did not observe, never summarize a run you did not perform, and never fill an `Observed evidence:` field from memory or from a matching execution checkmark. Run the suite BARE (`python3 -m pytest`); do not add `-n0`, a second `-q`, or `-p no:randomly`, since `pyproject.toml` `addopts` already supplies the intended flags. If a validation cannot be performed, say so plainly and leave it `pending`; an honest gap is acceptable and a fabricated pass is not.
4. The orchestrator itself authors NO product code and touches only its own file. Product changes, tests, and commits belong to the children.
5. RE-MEASURE CONCURRENT SCOPE COLLISIONS IMMEDIATELY BEFORE EACH CHILD, not once at Set start. Round 2's `e32j35` and `6knsrx` are both SUPERSEDED and no longer live. The collisions measured at round 5 (see F-8) are `agent_workflows/selectors.py` vs APPROVED plan `2r306y`, affecting Order 02, and `agent_workflows/cli.py` vs 7 non-wslayout pending plans, affecting Order 05. Treat even these as historical by the time you read them: re-derive the set with a scan of `- Scope-Paths:` over `.aw/records/plans/pending/*.ipd.md`, then verify mergeability before editing. STOP and report only if a file you must edit is being changed concurrently and the two change sets cannot be safely combined.
6. Validation requires ACTUAL pasted commands, exit codes, and file contents. A clean structural lint is not evidence of behavior, and this Set has already been bitten by that: round 1 found the orchestrator's open-question section had never been PARSED by the linter (prose bullets instead of `### OQ-NN:` headings), so an earlier "lint conforming" was a false negative on that section.
7. Commit only files the executing plan changed, path-scoped. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
8. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
9. Scope fence (a DECLARATION so the runner can reconcile afterwards): this orchestrator's declared Scope-Paths are the union the children edit; the orchestrator's OWN commits touch only this plan file. An out-of-scope edit is permitted but must be JUSTIFIED with a per-path `aw ipd finalize --scope-reason`, and a declared-but-unmodified path needs a `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a file you must edit is being changed concurrently and the two sets of changes cannot be safely combined (this is the item-5 case).
10. `check.lifecycle-transition-invalid` fires on all six of these plans and is a KNOWN TOOLING DEFECT, not a plan defect (round 1 PR-009, filed as backlog `tk1gqo`, still `open`, and now carrying `- Blocks-Release: next`). Re-measured at round 5: 16 reports repo-wide, 14 on this Set, and the number RISES with every history line any tool or reviewer appends. Do NOT "fix" it by reordering these histories to newest-first: that would contradict the oldest-first convention every other plan follows, and `tk1gqo` records that this workaround was already considered and rejected. Expect the diagnostic, leave it alone, and assert diagnostic CLASSES not counts.
11. After all children and both orchestrator E/V items pass, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`. The lifecycle transition is a POST-gate step, never an E-item.
