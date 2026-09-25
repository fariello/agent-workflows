# IPD: Teach the layout migration preflight that .agents/skills and the installer-written .aw files are known, so a legacy repo can migrate

- Date: 2026-09-25
- Kind: child
- Concern: THE 2.0.0 LAYOUT MIGRATION REFUSES ESSENTIALLY EVERY REAL LEGACY REPO, FOR THREE INDEPENDENT REASONS, ALL OF THEM FILES THE INSTALLER ITSELF WRITES. `layout_inventory.classify_item` falls through to `{ownership: unknown, disposition: block-unknown}` for (1) anything under `.agents/skills/` in the `agents` arm, and for (2) `.aw/.gitignore` and (3) `.aw/setup-repo-needed.md` in the `partial-aw` arm. The inventory turns each into an `unknown-owner` error, and `layout_migration.MigrationManager.execute_migration` raises `PreflightGateError` ("Migration plan invalid"). Measured at HEAD `eec5dc49` on four scratch repos: legacy-without-skills migrates (dry run OK); legacy-with-skills, legacy-plus-`.aw/.gitignore`, and legacy-plus-`.aw/setup-repo-needed.md` each raise `PreflightGateError` naming exactly that path. `.agents/skills` is the intended skills location for BOTH layouts (`engine.SKILLS_DIR`, `engine.resolve_skills_dir`), and a keep-legacy install creates both it and `.aw/.gitignore` (plan `je74a0` F-6), so every repo installed by a recent version is in a refused shape.
- Scope: IN: (a) an explicit `skills` branch in `classify_item`'s `agents` arm that PRESERVES the directory in place, with the prefix read from `engine.SKILLS_DIR` via the existing `layout_migration._skills_prefix` authority rather than re-spelled; (b) explicit `partial-aw` branches for `.gitignore` and `setup-repo-needed.md` that leave both where they already are (they are framework-owned files already at their final `.aw/` location); (c) behavioral tests over the four measured shapes plus a combined shape, driving the real inventory and a real dry-run `execute_migration`, and asserting skills content survives an APPLIED migration with `leftover_disposition="remove"`; (d) widening backlog `72qlya`'s text to name all three triggers, per the maintainer's 2026-09-25 ruling. OUT: the install-time default flip, the remembered-answer config, and the fail-soft guard (all plan `je74a0`, Order 2 of this Set, which depends on this plan); any other `block-unknown` path not measured here; changing the preflight's fail-closed rule itself.
- Scope-Paths: agent_workflows/layout_inventory.py, tests/test_layout_inventory.py, .aw/records/backlog/open/20260923-72qlya-01-72qlya-migrate-layout-refuses-agents-skills.backlog.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 72qlya
- Blocks-Release: next
- Set: setprompt
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: vv6y7e

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored on the maintainer's 2026-09-25 /askme rulings on plan je74a0 OQ-03 (fold the classifier fix into this Set, ordered first) and OQ-04 (cover the partial-aw files too). Graduated from backlog 72qlya. All three refusals re-measured at HEAD eec5dc49 on scratch repos.
- 2026-09-25 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `aw migrate-layout` and the install-time migration succeed on a legacy repo that carries `.agents/skills`, `.aw/.gitignore`, or `.aw/setup-repo-needed.md`, leaving each of those exactly where it is, so plan `je74a0` can safely make the migration the default.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE ALL THREE REFUSALS at the executing HEAD. Build four scratch git repos under `/tmp/` (each committed): BASE = `.agents/workflows/VERSION`, `.agents/workflows/index.md`, `.agents/plans/README.md`; then BASE alone, BASE + `.agents/skills/assess/SKILL.md`, BASE + `.aw/.gitignore`, BASE + `.aw/setup-repo-needed.md`. For each, with `AW_HOME` pointed at a scratch dir, call `layout_migration.MigrationManager(str(repo)).execute_migration(dry_run=True, leftover_disposition="remove")` and paste the outcome. Also paste `layout_inventory.classify_item("agents", "skills/assess/SKILL.md")`, `classify_item("partial-aw", ".gitignore")`, and `classify_item("partial-aw", "setup-repo-needed.md")`. If any of the three already migrates, drop it from E-02/E-03 and say so; if all three do, STOP and report that the defect is fixed.
  - Depends on: none
  - Expected outcome: BASE dry run OK; the other three each raise `PreflightGateError` whose detail names `agents:skills`, `partial-aw:.gitignore`, and `partial-aw:setup-repo-needed.md` respectively; the three `classify_item` calls return `disposition: block-unknown`.
  - Execution state: pending

### Task group 2: classify the three paths

- [ ] E-02 ADD THE SKILLS BRANCH to `layout_inventory.classify_item`'s `label == "agents"` arm, BEFORE its terminal `block-unknown` return: when `first == "skills"` return `{"ownership": "host-adapter-candidate", "lifecycle_class": "host-adapter-candidate", "expected_destination_class": "host-adapter-in-place", "disposition": "preserve"}`, which is the treatment the host-adapter branch already gives regenerable shims a host tool discovers at a fixed path, for the same reason. `execute_migration` already skips every mapping whose `destination_root_class` is `host-adapter-in-place` ("they are NEVER moved"), so this keeps the directory in place without new migration logic. Derive `"skills"` from `engine.SKILLS_DIR` (strip the leading `.agents/`) rather than re-spelling it, following `layout_migration._skills_prefix`'s stated reason ("so a future relocation of the skills directory moves this guard with it"); import lazily inside the branch to keep `layout_inventory`'s import graph unchanged, as `_skills_prefix` does. Carry a comment citing `72qlya`. Also update `layout_inventory`'s coarse root classifier (the function ending `return "unknown-agents-content"`) only if E-01 or the tests show it gates the preflight; otherwise leave it and say so.
  - Depends on: E-01
  - Expected outcome: `classify_item("agents", "skills/assess/SKILL.md")` returns `disposition: preserve` with `expected_destination_class: host-adapter-in-place`; the legacy-with-skills dry run succeeds.
  - Execution state: pending

- [ ] E-03 ADD THE TWO PARTIAL-AW BRANCHES to `classify_item`'s `label == "partial-aw"` arm, before its terminal `block-unknown` return, for `posix == ".gitignore"` and `posix == "setup-repo-needed.md"`. Both are framework-owned files ALREADY at their final location (`engine._ensure_aw_gitignore` writes `.aw/.gitignore`; `engine.SETUP_MARKER_PATH` is `.aw/setup-repo-needed.md`), so they must be neither moved nor refused. Use the arm's existing precedent for live in-place content, the `state`/`durable`/`runtime` branch (`disposition: "skip"`, excluded from the map, "PRESERVED IN PLACE"), with an ownership of `system` and a comment explaining that the migration must not relocate a file onto its own path. Read the marker filename from `engine.SETUP_MARKER_PATH` rather than re-spelling it. Before choosing `skip`, confirm by reading `execute_migration` and the inventory error pass that a `skip` disposition is not itself reported as an error and does not cause the file to be deleted by `_handle_leftovers` (whose roots are `.agents` and `workflow-artifacts`, not `.aw`); paste what you read.
  - Depends on: E-01
  - Expected outcome: both `classify_item` calls return `disposition: skip`; the two partial-aw dry runs succeed; both files are byte-identical after an applied migration.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 ADD `tests/test_layout_inventory.py` (it does not exist; the nearest classifier coverage is indirect, via mocked `execute_migration` in `tests/test_installer.py`'s `InstallLeftoverDispositionThreadingTests`, which cannot see a classification). Drive the REAL inventory and the REAL `MigrationManager` on temp git repos built as in E-01, with `AW_HOME` isolated to a temp dir. Cases: (1) the three single-trigger shapes each dry-run cleanly; (2) a COMBINED shape carrying all three triggers dry-runs cleanly, since a fix for one could still leave the repo refused by another; (3) an APPLIED migration (`dry_run=False`, `leftover_disposition="remove"`) on the combined shape leaves `.agents/skills/assess/SKILL.md`, `.aw/.gitignore`, and `.aw/setup-repo-needed.md` present and byte-identical, and creates `.aw/system/`; (4) direct `classify_item` assertions for the three paths; (5) a NEGATIVE control: an unrelated unknown path such as `.agents/mystery.txt` still classifies `block-unknown` and still refuses, so the fix did not open the gate wholesale.
  - Depends on: E-02, E-03
  - Expected outcome: all cases pass; cases (1) through (4) fail against the pre-change classifier and case (5) passes both before and after.
  - Execution state: pending

- [ ] E-05 WIDEN BACKLOG `72qlya` so its record states the maintainer's ruling: add a history record with `aw backlog note 72qlya -m "..."` naming the two `partial-aw` triggers, the 2026-09-25 ruling that this plan covers both, and this plan's id6. Do NOT set the item `done` or `graduated` here: `graduated` is set when this plan is approved and handed off (it is being set at authoring, see the gate), and `done` requires the code to be executed and validated, which happens at finalize.
  - Depends on: none
  - Expected outcome: `72qlya`'s workflow history names all three triggers and cites this plan.
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` before and after the change and compare failing node IDs.
  - Depends on: E-04
  - Expected outcome: the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.agents/skills` is the intended skills location for BOTH layouts: `engine.SKILLS_DIR = ".agents/skills"`, and `engine.resolve_skills_dir` returns it for either layout because "a skill package is discovered by host tools that scan a fixed directory, so - like the command shims - it is not relocated under `.aw/system/`".
- The skills prefix has ONE authority, `engine.SKILLS_DIR`, and `layout_migration._skills_prefix` already reads it lazily and explains why (a relocation must move the guard with it). Plan `z1yefm` E-04 added the same guard to `_is_removable_leftover` so `remove` never deletes skills; this plan closes the matching gap in the classifier.
- Host-discovered paths are classified `host-adapter-in-place` / `preserve` and `execute_migration` skips them outright ("Host-required discovery files (host-adapter-in-place) are preserved at their exact repo-root path per spec S3.1/S9; they are NEVER moved").
- Live in-place content under `.aw/` uses `disposition: skip` (the `partial-aw` arm's `state`/`durable`/`runtime` branch: "PRESERVED IN PLACE and excluded from the map").
- The preflight is fail-closed by design: an unknown path is an error, not a warning. This plan classifies three KNOWN paths; it does not relax the rule, and E-04 case (5) pins that.
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `eec5dc49`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `layout_inventory.classify_item`, `agents` arm | `.agents/skills/...` falls through to `block-unknown`. | `classify_item("agents","skills/assess/SKILL.md")` -> `{'ownership': 'unknown', 'lifecycle_class': 'review-required', 'expected_destination_class': 'unknown', 'disposition': 'block-unknown'}`; legacy-with-skills dry run -> `PreflightGateError: Migration plan invalid: [{'rule': 'unknown-owner', 'detail': 'agents:skills has unknown owner/disposition', ...` |
| F-2 | BLOCKER | `classify_item`, `partial-aw` arm | `.aw/.gitignore` falls through to `block-unknown`, independently of skills. | `classify_item("partial-aw",".gitignore")` -> `block-unknown`; BASE + `.aw/.gitignore` dry run -> `PreflightGateError: ... 'partial-aw:.gitignore has unknown owner/disposition'` (sole error) |
| F-3 | BLOCKER | `classify_item`, `partial-aw` arm | `.aw/setup-repo-needed.md` falls through to `block-unknown`, independently of both. | `classify_item("partial-aw","setup-repo-needed.md")` -> `block-unknown`; BASE + marker dry run -> `PreflightGateError: ... 'partial-aw:setup-repo-needed.md has unknown owner/disposition'` (sole error) |
| F-4 | INFO | control | A legacy repo carrying none of the three migrates, so the rest of the preflight is sound and the fix is confined to classification. | BASE dry run -> `OK (dry-run)` |
| F-5 | HIGH | install path | The installer itself creates two of the three triggers, so the refused shape is the common case rather than an edge case. | plan `je74a0` F-6: a keep-legacy `install --yes` on a bare legacy repo produced `.agents/skills` and `.aw/.gitignore` |
| F-6 | LOW | tests | No test exercises `classify_item` or a real preflight; the installer tests mock `MigrationManager`, which is why all three refusals shipped. | `rg -ln "layout_inventory\|PreflightGateError\|execute_migration" tests` -> only `tests/test_installer.py`, whose hits are `MockMgr.return_value.execute_migration` |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the three refusals and the control.
2. E-02 preserves `.agents/skills` in place, via the host-adapter treatment.
3. E-03 skips `.aw/.gitignore` and `.aw/setup-repo-needed.md` in place.
4. E-04 adds real-path tests, including a combined shape, an applied migration, and a negative control.
5. E-05 records the widened scope on backlog `72qlya`.
6. E-06 runs the bare suite before and after.

## Deferred / out of scope (with reason)

- Flipping the install-time migration default, the remembered-answer config, and the fail-soft guard.
  - Carrier: je74a0
  - Rationale: that is Order 2 of this Set, which now depends on this plan (`- Item-Dependencies: executed:vv6y7e`).
- Auditing every other `block-unknown` fall-through for further unmeasured triggers.
  - Carrier-Declined: only these three were measured in real installer output; guessing at others would be classifying paths with no evidence of how they arise. E-04's negative control keeps the gate closed for them.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/layout_migration.py` is deliberately NOT declared: `execute_migration` already skips `host-adapter-in-place` and honors `skip`, so no migration logic should change. If E-03's read shows otherwise, declare it and justify at finalize.
- Scope-Paths justification: `layout_inventory.py` holds the classifier; the new test file holds E-04; the backlog item receives E-05's note.

## Required tests / validation

- `tests/test_layout_inventory.py` (new): the three single triggers, the combined shape, an applied migration preserving all three byte-identically, direct classifier assertions, and a negative control. Cases (1) to (4) shown failing against the pre-change classifier.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

## Spec / documentation sync

- N/A for specs: the physical-layout spec's install-target contract (Section 11.3) requires install to detect a legacy layout and offer migration; it does not enumerate per-path dispositions, and this plan makes that offer succeed rather than changing it. No `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs change: nothing documents the refusal, and the behavior restored is the documented one.

## Open questions

### OQ-01: Should `.agents/skills` be preserved in place or relocated into `.aw/`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: PRESERVED IN PLACE, from repository evidence. `engine.resolve_skills_dir` returns `.agents/skills` for BOTH layouts and states why (host tools scan a fixed directory); `z1yefm` E-04 already protects it from `remove` for the same reason; and relocating it would break host skill discovery exactly as relocating the command shims did (the host-adapter branch comment records that finding). Backlog `72qlya`'s own suggested fix names this disposition.

### OQ-02: Which disposition fits the two `.aw/` files: `preserve` or `skip`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: `skip`, from repository evidence, with E-03 required to confirm it by reading before writing. Both files are already at their final `.aw/` location, so there is nothing to move; the `partial-aw` arm's own precedent for live in-place content is `skip` ("PRESERVED IN PLACE and excluded from the map"), and `preserve` in this codebase is paired with a destination class that implies a mapping. E-04 case (3) asserts both files survive an applied migration byte-identically, which is what either disposition must deliver.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the four dry-run outcomes and the three `classify_item` results, each with the path named in the `PreflightGateError` detail.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the `agents` arm showing the `skills` branch and the lazy `engine.SKILLS_DIR` read; paste the new `classify_item("agents","skills/assess/SKILL.md")` result and the legacy-with-skills dry run succeeding.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the `partial-aw` arm and the lines of `execute_migration` / the inventory error pass read to confirm `skip` is neither an error nor a deletion; paste both new `classify_item` results and both dry runs succeeding.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_layout_inventory.py -o addopts="" -q` passing with the case count; then the same command with the E-02 and E-03 hunks temporarily reverted, showing cases (1) to (4) FAILING and case (5) still passing; then passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `aw backlog note` output and the resulting top history record of `72qlya` naming all three triggers and this plan's id6.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Three classification entries so the layout migration stops refusing files the installer itself writes: `.agents/skills` is preserved in place (host tools scan it there), and `.aw/.gitignore` plus `.aw/setup-repo-needed.md` are left where they already are. The preflight stays fail-closed for every other unknown path, and a negative-control test pins that. No migration logic, install behavior, or default changes here; the default flip is plan `je74a0` (Order 2), which waits on this one.

This plan implements the maintainer's 2026-09-25 rulings recorded in plan `je74a0` OQ-03 (fold the classifier fix into this Set, ordered first) and OQ-04 (cover the two `.aw/` files as well). It graduates backlog `72qlya` and inherits its `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/layout_inventory.py` (`classify_item` only), the new `tests/test_layout_inventory.py`, and backlog `72qlya`'s history. `layout_migration.py` is expected to be READ and not modified. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-04 must show the new tests FAILING against the pre-change classifier, because the existing tests mock the migration manager and so could not catch this regression.

GENUINE STOP CONDITIONS: if E-01 finds all three already migrate, retire this plan rather than execute it; if E-03's read shows `skip` would delete or refuse the file, stop and report rather than guessing a third disposition.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `72qlya` `done` with `--evidence` citing the executed plan; its release gate is preserved by that handoff.
