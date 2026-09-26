# IPD: Stop the upgrade rehearsal calling the live .agents/skills install output orphaned leftovers

- Date: 2026-09-26
- Kind: child
- Concern: After a MIGRATING rehearsal, `derive_observations` reports the live `.agents/skills` install output as BOTH `orphaned-skills` ("unreferenced duplicates a host may still discover") and `legacy-leftovers` (it counts every file under `.agents/`), although `.agents/skills` is the INTENDED skills directory for both layouts (`engine.SKILLS_DIR`, `engine.resolve_skills_dir`). The harness whose job is to produce evidence a human judges therefore pushes that human toward deleting working install output, and it already misled backlog `x15f0q` once (corrected by plan `z1yefm` F-06). Measured at HEAD `f46b6775`: `derive_observations({"baseline_layout":"legacy","layout":"aw+litter","legacy_files_remaining":92,"legacy_breakdown":{"skills":92}})` returns `['empty-legacy-dirs', 'legacy-leftovers', 'orphaned-skills']`.
- Scope: IN: in `agent_workflows/upgrade_rehearsal.py` (the post-`8ud1is` home of the harness logic): delete the `orphaned-skills` observation; exclude the `engine.resolve_skills_dir(layout)` subtree from the `legacy-leftovers` count and its breakdown detail; record the live skills-file count in the probe state; add the inverse observation `skills-missing` (a migrated run with no files under the skills directory); make the human `report` line say how many of the `.agents/` files are the live skills install; update the restored `ProbeAndObservationTests.OBSERVATIONS` row that pins the defect and add rows plus one real-probe test. OUT: changing `legacy_breakdown`'s attribution rule (a restored test pins it and it stays correct); changing where the installer writes skills; the tool's other observations; the `tools/aw_upgrade_test.py` shim (it re-exports, so it needs no edit).
- Scope-Paths: agent_workflows/upgrade_rehearsal.py, tests/test_aw_upgrade_test.py
- Item-Dependencies: executed:8ud1is
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: izfscm
- Blocks-Release: next
- Set: upgrehearse
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: sbo3hl

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog izfscm. Re-measured at HEAD f46b6775: the skills-only migrated state emits empty-legacy-dirs, legacy-leftovers AND orphaned-skills; engine.resolve_skills_dir returns .agents/skills for every layout. Ordered after 8ud1is (the package move plus the full test restore) because this plan edits the post-move module and the restored test row that pins the defect.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A migrating rehearsal that leaves `.agents/skills` in place reports nothing about it (that is the correct outcome), a rehearsal that LOSES the skills directory says so, and genuine leftovers elsewhere under `.agents/` are still reported with a count that no longer includes the live skills install.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce on the moved code

- [ ] E-01 CONFIRM THE PRECONDITION AND REPRODUCE. Confirm plan `8ud1is` is executed: `agent_workflows/upgrade_rehearsal.py` exists, `tools/aw_upgrade_test.py` is a re-exporting shim, and `tests/test_aw_upgrade_test.py` is restored with the `ProbeAndObservationTests.OBSERVATIONS` row "a migrating run that left the skills tree behind" expecting `["empty-legacy-dirs", "legacy-leftovers", "orphaned-skills"]`. Then paste the kinds `upgrade_rehearsal.derive_observations` returns for (a) that row's exact state dict, and (b) `{"baseline_layout":"legacy","layout":"aw","legacy_files_remaining":95,"legacy_breakdown":{"skills":92,"workflows":3}}`, and paste `engine.resolve_skills_dir("aw")` and `engine.resolve_skills_dir("legacy")`.
  - Depends on: none
  - Expected outcome: (a) `['empty-legacy-dirs', 'legacy-leftovers', 'orphaned-skills']`; (b) `['legacy-leftovers', 'orphaned-skills']` with a note counting 95 files; both resolver calls return `.agents/skills`. If `orphaned-skills` no longer fires, report that and narrow E-03 to what still reproduces.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-02 RECORD THE LIVE SKILLS COUNT IN THE PROBE. In `upgrade_rehearsal.probe`, add `state["skills_dir"]` (the repo-relative path from `engine.resolve_skills_dir`, passing `"aw"` when `detect_layout` starts with `aw` or is `dual`, else `"legacy"`) and `state["skills_files"]` (the count of files at any depth under that directory, 0 when absent). Import `engine` LAZILY inside the helper, as `layout_migration._skills_prefix` does and for its stated reason (keep the import graph unchanged; read the ONE authority so a relocation moves this check with it). Do NOT change `legacy_breakdown` or the meaning of `legacy_files_remaining` (still every file under `.agents/`): the restored `test_legacy_breakdown_attributes_leftovers_to_subtrees` and the `PROBES` table pin both, and they are correct as attribution.
  - Depends on: E-01
  - Expected outcome: a probe of a sandbox holding `.agents/skills/a/SKILL.md` reports `skills_dir == ".agents/skills"` and `skills_files == 1`.
  - Execution state: pending

- [ ] E-03 FIX `derive_observations`. (1) DELETE the `orphaned-skills` block entirely: both of its clauses are false (skills are not installed "under the .aw layout", and the files are current manifest rows, verified by `z1yefm`). (2) In the `legacy-leftovers` block, compute the leftover count as `legacy_files_remaining` minus the breakdown entry for the skills subtree, where the subtree key is the first path component of `engine.resolve_skills_dir(...)` BELOW `.agents/` (today `skills`), and drop that key from the printed `detail`; if the resolved skills dir is not under `.agents/`, subtract nothing. Fire only when the remaining count is positive. Computing this in `derive_observations` (rather than only in `probe`) is deliberate: the restored table hands state dicts straight to `derive_observations`, so that is where the behavior must live to be tested. (3) ADD `skills-missing`: fires when the run MIGRATED (the existing `migrated` predicate) AND `state.get("skills_files") == 0` with the key PRESENT; its note says the installer writes skills to `<skills_dir>` for every layout, so their absence after a migration is the reportable defect. The key-present condition keeps every existing row that omits `skills_files` silent. Keep the kind order the report prints (`dual-layout`, `empty-legacy-dirs`, `legacy-leftovers`, `skills-missing`, `legacy-kept`, then the version and remote kinds) and keep the function's DESCRIPTIVE, never-a-verdict docstring.
  - Depends on: E-02
  - Expected outcome: state (a) from E-01 yields `['empty-legacy-dirs']`; state (b) yields `['legacy-leftovers']` with a note counting 3 files and a detail of `workflows=3`; a migrated state with `skills_files: 0` yields `['skills-missing']`.
  - Execution state: pending

- [ ] E-04 MAKE THE HUMAN REPORT HONEST. In `upgrade_rehearsal.report`, when `skills_files` is positive, extend the `Legacy:` line with `of which <n> are the live skills install under <skills_dir>`, so a reader of the raw count is not left to infer that those files are leftovers.
  - Depends on: E-02
  - Expected outcome: `report()` on a result whose state has `legacy_files_remaining: 95, skills_files: 92` prints a `Legacy:` line naming both numbers and the skills directory.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 UPDATE THE RESTORED TABLE AND ADD BEHAVIORAL TESTS in `tests/test_aw_upgrade_test.py`. (1) Change the row "a migrating run that left the skills tree behind" to expect `["empty-legacy-dirs"]` and rewrite its `why` to state that `.agents/skills` surviving a migration is the CORRECT outcome and firing on it pushes a reviewer to delete live install output (backlog `izfscm`). Changing this expectation is the point of the plan, not a relaxation: the old expectation pinned the defect. (2) Add rows: skills plus three `workflows` leftovers after a migration -> `["legacy-leftovers"]`; a migrated state with `skills_files: 0` -> `["skills-missing"]`; a NOT-migrated legacy-kept state with `skills_files: 0` -> `["legacy-kept"]` (proving `skills-missing` keys on the migration, not on the count). (3) Add one REAL-PROBE test: create a sandbox from a legacy source with `create_sandbox`, then in the sandbox delete `.agents/workflows`, write `.aw/system/VERSION`, and write two files under `.agents/skills/x/`; assert `probe(sandbox)["observations"]` kinds contain neither `orphaned-skills` nor `legacy-leftovers`, and that `skills_files == 2`; then delete `.agents/skills` and assert `skills-missing` appears. (4) A test that `report()` output (captured stdout) names the skills count per E-04. No test reads source text.
  - Depends on: E-03, E-04
  - Expected outcome: the new and changed tests pass after the fix; against the pre-fix module the changed row, the three-leftover row, the skills-missing row, the real-probe test and the report test FAIL, and the legacy-kept row passes both before and after.
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs.
  - Depends on: E-05
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.agents/skills` is the skills location for BOTH layouts: `engine.SKILLS_DIR = ".agents/skills"` and `engine.resolve_skills_dir` returns it for any `target_layout` because "a skill package is discovered by host tools that scan a fixed directory". `engine.install_into_repo` writes the skill packages there via `engine._build_skill_members` on every install.
- The skills prefix has ONE authority; `layout_migration._skills_prefix` reads `engine.SKILLS_DIR` lazily and explains why. This plan follows that precedent instead of re-spelling the path.
- `derive_observations` is DESCRIPTIVE by design (its docstring), and the restored table's failure message says "the fix for a spurious finding is to narrow the predicate, never to delete the observation". Deleting `orphaned-skills` is consistent with that rule: the observation is not spurious on some states, its premise is false on every state, and its useful inverse (`skills-missing`) replaces it.
- Plan `8ud1is` (Order 1, approved, pending) moves the logic to `agent_workflows/upgrade_rehearsal.py`, leaves `tools/aw_upgrade_test.py` as a re-exporting shim, and restores `tests/test_aw_upgrade_test.py` from `19313eed^` in full; the tests reach internals as `uat.<name>` through the shim, so the shim needs no edit here.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only; no source-text or structure pins. Suites run bare as `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775` against `tools/aw_upgrade_test.py` (the pre-move location; `8ud1is` moves the same functions verbatim).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `derive_observations`, `orphaned-skills` block | Fires whenever a migrating run leaves any file under `.agents/skills`, i.e. on every successful migration, with a note whose two clauses are both false. | skills-only state -> `['empty-legacy-dirs', 'legacy-leftovers', 'orphaned-skills']` |
| F-2 | HIGH | `derive_observations`, `legacy-leftovers` block; `probe` | `legacy_files_remaining` counts every file under `.agents/` including the live skills install, so the leftover finding double-reports the same files. | `probe` sets `legacy_files_remaining = sum(... legacy.rglob("*") ...)` over `sandbox / ".agents"`; the same state fires `legacy-leftovers` with 92 files |
| F-3 | INFO | `engine.resolve_skills_dir` | Returns `.agents/skills` for both layouts. | `resolve_skills_dir(target_layout)` body is `return SKILLS_DIR`; `SKILLS_DIR = ".agents/skills"` |
| F-4 | MEDIUM | restored test | The restored table row "a migrating run that left the skills tree behind" PINS the defect, with a `why` asserting the skills are "ORPHANED SKILLS a host may still discover". | `git show 19313eed^:tests/test_aw_upgrade_test.py`, the row expecting `["empty-legacy-dirs", "legacy-leftovers", "orphaned-skills"]` |
| F-5 | LOW | nothing reports the real defect | No observation fires when a migration LOSES `.agents/skills`, which is what would break host skill discovery. | no `skills-missing` or equivalent kind exists in `derive_observations` |
| F-6 | INFO | provenance | This observation propagated one wrong conclusion into a tracked record already. | backlog `izfscm` WHY IT MATTERS: origin of the "unreferenced duplicates" claim in `x15f0q`, corrected by `z1yefm` F-06 |

## Proposed changes (ordered, validatable)

1. E-01 confirms `8ud1is` landed and reproduces on the moved module.
2. E-02 records `skills_dir` / `skills_files` in the probe from the engine's one authority.
3. E-03 deletes `orphaned-skills`, excludes the skills subtree from `legacy-leftovers`, adds `skills-missing`.
4. E-04 makes the human `Legacy:` line name the live skills count.
5. E-05 corrects the restored row, adds rows and a real-probe test.
6. E-06 bare suite.

## Deferred / out of scope (with reason)

- Re-deriving other `.agents/` subtrees that may be legitimately kept after a migration (for example host shims).
  - Carrier-Declined: none has been measured misreported; the backlog item and the rehearsal evidence name only the skills tree, and guessing at others would narrow a predicate without evidence.
- Changing `legacy_breakdown` or `legacy_files_remaining` semantics.
  - Carrier-Declined: both are correct as ATTRIBUTION and pinned by restored tests; the defect is in how `derive_observations` interprets them, which E-03 fixes.

## Scope check

- Over-scope: none.
- Under-scope: `tools/aw_upgrade_test.py` is deliberately not declared: after `8ud1is` it re-exports every attribute, so the new behavior reaches `uat.<name>` without an edit. If E-01 finds the shim does not re-export, that is a defect in `8ud1is` to report, not to fix here.
- Scope-Paths justification: `upgrade_rehearsal.py` holds `probe`, `derive_observations`, and `report`; the test file holds the restored table this plan must correct.

## Required tests / validation

- `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` passing after, with the E-05 cases shown FAILING against the pre-fix module.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A: no spec describes the rehearsal harness's observation kinds (confirmed by `8ud1is`'s spec-sync section, which declares none), and no `.spec.md` is in `- Scope-Paths:`.
- The module docstring's USAGE section does not list observation kinds, so no docstring edit is needed beyond `derive_observations`'s own, which stays accurate.

## Open questions

### OQ-01: Delete `orphaned-skills`, or keep it narrowed?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: DELETE, from repository evidence. There is no state in which files under `engine.resolve_skills_dir(...)` are orphaned by a migration, because the resolver returns the same path for both layouts and the installer writes skills there on every run (`engine.install_into_repo` -> `_build_skill_members`). A narrowed predicate would have no true-positive case. Backlog `izfscm`'s suggested fix names exactly this ("Drop the `orphaned-skills` observation, or invert it"), and the inverse is added as `skills-missing`.

### OQ-02: Should `skills-missing` fire on a migrated state that omits `skills_files`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO. Absence of the key means the caller did not measure it (every existing restored row, and any state produced by an older probe persisted in a sandbox marker), and the restored table's clean row exists precisely so that a good upgrade produces silence. Firing on an unmeasured value would make that row fail and teach the reader to ignore the list, the failure `derive_observations`'s docstring warns about.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls agent_workflows/upgrade_rehearsal.py`, the `8ud1is` plan's `- Status:` line, the restored row as it reads before the edit, the two `derive_observations` outputs, and the two `resolve_skills_dir` outputs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of `probe` and the new helper showing the lazy `engine` import; paste a `probe(...)` run on a scratch sandbox holding one skills file printing `skills_dir` and `skills_files`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `derive_observations` diff showing the `orphaned-skills` block removed and `skills-missing` added; paste the kinds for state (a), state (b) (with the note text showing 3 files and `workflows=3`), and a migrated `skills_files: 0` state.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `report` diff and the captured `Legacy:` line for a result with 95 legacy files of which 92 are skills.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_aw_upgrade_test.py -o addopts="" -q` passing with its count; then the same run with the E-02/E-03/E-04 hunks temporarily reverted, showing the changed row, the three-leftover row, the skills-missing row, the real-probe test and the report test FAILING while the legacy-kept row passes; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The rehearsal harness stops telling a reviewer that the live `.agents/skills` install is orphaned leftover material: the `orphaned-skills` observation is removed, the leftover count excludes the skills directory, and a new `skills-missing` observation reports the case that actually matters (a migration that lost the skills). One restored test row that pinned the wrong answer is corrected. Graduates backlog `izfscm` and inherits its `- Blocks-Release: next`. Runs strictly after `8ud1is` (`- Item-Dependencies: executed:8ud1is`).

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/upgrade_rehearsal.py` (`probe`, `derive_observations`, `report`, and one small skills-dir helper) and `tests/test_aw_upgrade_test.py` (the observation table plus the new tests). If an edit outside those paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-05 must show the new tests FAILING against the pre-fix module.

GENUINE STOP CONDITION: if E-01 finds `8ud1is` not executed, do not execute this plan (the runner's dependency re-check enforces this).

Commit ONLY through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `izfscm` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
