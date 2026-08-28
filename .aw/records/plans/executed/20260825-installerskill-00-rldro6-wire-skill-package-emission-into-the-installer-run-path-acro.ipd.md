# IPD: Wire skill-package emission into the installer run() path across hosts

- Date: 2026-08-25
- Kind: orchestrator
- Concern: The execset Set (Order 05, 2h7777) proved skill/shim generation at the library level (`build_skill_package` digest parity + `generate_shim_members` drift-free) and exposed `/exec-set` via the existing shim path, but did NOT wire skill-package emission (`host_adapters.generate_adapter_bundle` / `build_skill_package(...).to_files()`) into `engine.install_all` (engine.py:1953), which today writes only `body_members` + `shim_members`. So a real `aw install` never emits the generated skill packages / per-host adapter bundles. Wiring it is a cross-cutting installer-output change (all hosts + uninstall + idempotency + install-diff), deliberately deferred out of the packaging Order (D21-2h7777-D2). Backlog item bplplj (medium).
- Scope: Wire skill-PACKAGE emission (`host_adapters.build_skill_package(...).to_files()` via `AdapterBundle.skill_files()`, host_adapters.py:227/663) into the installer run path so `aw install` writes the generated skill files alongside body + shim members, covering the hosts the bundle already generates, uninstall, idempotency, and install-diff. Single coherent child (01) plus this orchestrator. Deliverable: `install_into_repo` (engine.py:4992) builds the skill member map and merges it into the desired set passed to `install_all` (engine.py:1953), written the same idempotent way as shim members; the framework-namespace predicate (`in_framework_namespace`, engine.py:1632), the prune scan (`collect_target_framework_files`, engine.py:2012) and the prune defense-in-depth guard (engine.py:2072) are extended to recognize the skills directory so orphaned skill files are pruned and re-install is a no-op; uninstall is manifest-driven (`uninstall_repo`, engine.py:3836 removes any file `write_file` recorded in the ownership manifest), so it removes emitted skill files WITHOUT a separate member set once the namespace guard admits them; install-diff/idempotency tests are extended so a fresh install emits the skill package and a re-install is a no-op. NOTE: the per-host `host_adapters` metadata in `AdapterBundle` (host_adapters.py:661) is structured data (`to_dict`), NOT writable files - see OQ-02; this Set does not emit adapter-metadata files unless OQ-02 decides otherwise.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/host_adapters.py, tests/
- Status: executed
- Set: installerskill
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rldro6

## Workflow history
- 2026-08-28 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Whole-Set verification: aw install emits skill packages (AdapterBundle.skill_files) idempotently across generated hosts, orphan skill files pruned, manifest-driven uninstall removes them, no adapter-metadata files (OQ-02 A); child kvfsak executed (5af28bb). 10 skill-emission + 148 install/adapters/shims/layout tests green; 4 pre-existing unrelated CLI-declaration failures out of scope (04-rldro6-D1) [Scope reconciliation - in-scope-unmodified agent_workflows/engine.py: implemented+committed by child kvfsak (5af28bb); orchestrator authors no code; in-scope-unmodified agent_workflows/host_adapters.py: implemented+committed by child kvfsak (5af28bb); orchestrator authors no code; in-scope-unmodified tests/: skill-emission tests added+committed by child kvfsak (5af28bb); orchestrator authors no code]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS (OQ-02/03/04 blocking); adapter-file conflation, namespace/prune/layout gaps, uninstall mechanism, citations, execution contract fixed

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `aw install` actually emit the generated skill packages by wiring `AdapterBundle.skill_files()` (from `generate_adapter_bundle` / `build_skill_package(...).to_files()`) into the installer run path, idempotently and across uninstall + install-diff, closing the gap execset deferred. Whether the per-host `host_adapters` metadata is also emitted as files depends on OQ-02.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; child 01 carries the work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [x] E-01 After child 01 executes, confirm a fresh `aw install` emits the skill-package files (`AdapterBundle.skill_files()`) for the hosts the bundle generates, a re-install is a no-op (idempotent, empty install-diff), an orphaned skill file (from a removed workflow) is pruned, and `uninstall` removes the emitted skill files; full suite green.
  - Depends on: none
  - Expected outcome: install-diff test shows skill-package members on fresh install, empty diff on re-install, pruning of an orphaned skill file, and clean manifest-driven removal on uninstall. If OQ-02 resolves to include adapter-metadata files, they are covered too; otherwise the check explicitly asserts NO adapter-metadata files are emitted.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | emit skill package (kvfsak) | wire `AdapterBundle.skill_files()` into `install_into_repo`->`install_all`; extend `in_framework_namespace`/`collect_target_framework_files`/prune guard for the skills dir; resolve the aw-vs-legacy skills-dir layout (OQ-03); manifest-driven uninstall removes them; idempotency + install-diff tests | none |

Single child; orchestrator verifies. The child's approach was found materially incomplete in review (see the plan-review findings and OQ-02/OQ-03/OQ-04 below) and must be re-planned before execution: its checklist did not name the `in_framework_namespace`/`collect_target_framework_files` extensions, misdescribed uninstall as taking a member set, and conflated non-writable adapter metadata with skill FILES.

## Completion criteria (the whole Set is done only when)

- `aw install` emits the skill-package files (`AdapterBundle.skill_files()`) for the hosts the bundle already generates. (Per-host adapter-metadata FILES only if OQ-02 decides to add a renderer.)
- The framework-namespace predicate + prune scan recognize the skills directory, so an orphaned skill file (from a removed workflow) is pruned and a re-install is idempotent (no duplicate writes / empty install-diff).
- The skills-dir target path is correct for BOTH the `aw` and legacy layouts (OQ-03).
- Manifest-driven `uninstall_repo` removes the emitted skill files (they are recorded by `write_file`); tests confirm removal.
- Install/install-diff tests assert all of the above and the suite is green.

## Cross-IPD validation

- Emission reuses the existing `build_skill_package`/`AdapterBundle.skill_files()` library (no forked generator) and the same idempotent `write_file` path as shim members.
- Discovered in review (blocking, feed into the child re-plan): (a) `generate_adapter_bundle` produces writable files ONLY via `skill_files()`; the `host_adapters` field is `to_dict`-only metadata with no file renderer (host_adapters.py:655-674), so "adapter bundle members" as files do not exist unless OQ-02 adds a renderer. (b) `in_framework_namespace` (engine.py:1632) and `collect_target_framework_files` (engine.py:2012) do not recognize the skills dir; the prune guard (engine.py:2072) will skip skill paths and orphaned skill files can never be pruned unless these are extended. (c) `SHARED_SKILLS_DIR = ".agents/skills"` (host_adapters.py:60) is the LEGACY path; `engine.py` has no aw-layout skills-dir resolver, so the target under the `aw` layout is undefined (OQ-03). (d) `uninstall_repo` (engine.py:3836) is manifest-driven and takes NO member set; it removes what `write_file` recorded, so no separate "uninstall member set" is needed (correcting the child's E-02 wording).

## Deferred / out of scope (with reason)

- Changing the CONTENT of skill/adapter generation (execset already proved digest parity): out of scope; this set only WIRES emission into install.

## Scope check

- Over-scope: none.
- Under-scope (discovered in plan-review, now folded into the child re-plan): the original plan under-scoped the wiring - it named only the desired-set union but not the `in_framework_namespace` predicate, the `collect_target_framework_files` prune scan, the prune defense-in-depth guard, or the aw-vs-legacy skills-dir layout resolution. These are REQUIRED for idempotent emission + prune + uninstall and are now enumerated in Cross-IPD validation and OQ-02/03/04.

## Required tests / validation

Aggregate of child 01: fresh-install emits skill-package files for the hosts the bundle generates; re-install idempotent (empty diff / all-skipped); an orphaned skill file is pruned; manifest-driven uninstall removes the emitted skill files; install-diff tests updated. If OQ-02 keeps adapter-metadata files out of scope, a test asserts none are emitted. Validation MUST paste the actual runner output (see V-01), never an un-run "tests pass" claim.

## Open questions

### OQ-01: Emit skill packages for all hosts, or only v1 live-capable hosts?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Follow `generate_adapter_bundle`'s existing v1-vs-deferred host distinction (host_adapters.py:62-66); emit for the hosts the bundle already generates, no new host policy here.

### OQ-02: Does this Set emit per-host adapter-metadata FILES, or only skill-package files?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED - Option A, mirrored from the executed child kvfsak (DECISION 02-kvfsak-D1). Emit ONLY skill-package files (`AdapterBundle.skill_files()`); do NOT emit adapter-metadata files (`host_adapters` is `to_dict`-only, no file renderer). The child's `test_no_adapter_metadata_files_emitted` asserts none are written. Verified green in this orchestrator's E-01/V-01.

### OQ-03: Under the `aw` layout, where do skill files land?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED, mirrored from the executed child kvfsak (DECISION 02-kvfsak-D2), with a deliberate evidence-based DEVIATION from the Option-A wording, flagged for human review. Added `resolve_skills_dir(target_layout)` in `engine.py` and threaded the result as `skill_dir` into the generators (satisfying the "add a resolver, pass resolved skill_dir" structural requirement). The resolver returns the shared HOST-CONSUMPTION dir `.agents/skills` for BOTH layouts because a skill package must be DISCOVERED by a host tool at a fixed dir (like the command shims `.opencode/commands`/`.claude/commands`, which are layout-independent); `.aw/system/skills` would be discovered by no host, and `migration_compact` already uses `.agents/skills` for both layouts. If the maintainer prefers `.aw/system/skills` or per-host native dirs, only `resolve_skills_dir` changes. Verified green in E-01/V-01.

### OQ-04: Extend the framework-namespace predicate + prune scan for the skills dir - confirm approach?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED as recommended, mirrored from the executed child kvfsak (DECISION 02-kvfsak-D3). Extended `in_framework_namespace` (admits `SKILLS_DIR + "/"`) and `collect_target_framework_files` (recursively scans the resolved skills dir); the prune defense-in-depth guard then admits skill paths automatically via the updated predicate. Verified by the child's namespace/collect tests and the orphan-prune tests, re-run green in this orchestrator's E-01/V-01.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of the repo's real test runner showing (a) the new install-emission test passing: a fresh install into a temp repo writes the expected `SKILL.md` + resource files under the resolved skills dir for each generated host; (b) a re-install test showing an empty install-diff / all-skipped `[already current]`; (c) an orphaned-skill-file prune test; (d) an uninstall test showing the skill files removed via the manifest; and (e) the full suite green (paste the actual pass/fail summary line). Also paste `aw ipd lint --phase pre-transition --agent <child>` conforming for child 01.
  - Observed evidence: Whole-Set verification run against the executed child kvfsak (implementation in commit 5af28bb, now in .aw/records/plans/executed/). Runner: `python3 -m pytest tests/test_installer_skill_emission.py -n0 -m ''` -> `10 passed in 14.51s`, with the named cases: (a) `SkillEmissionInstallTests::test_fresh_install_emits_skill_packages_and_records_manifest` PASSED (writes `.agents/skills/<name>/SKILL.md` + `reference/` + `scripts/` per generated host and matches the ownership manifest); (b) `test_reinstall_is_idempotent_no_op_for_skills` PASSED (0 newly-installed, all `[already current]`, 0 pruned); (c) `test_orphaned_tracked_skill_file_is_pruned` + `test_orphaned_untracked_skill_file_is_pruned` PASSED (orphan removed via `[git rm]`/`[rm]`); (d) `test_uninstall_removes_emitted_skill_files_via_manifest` PASSED (manifest-driven removal, 0 remaining); plus `test_no_adapter_metadata_files_emitted` (OQ-02 Option A), `NamespaceAndCollectTests` x2 (in_framework_namespace + collect_target_framework_files admit the skills dir), and `SkillsDirResolverTests` x2 (resolver + threading). Regression: `python3 -m pytest tests/test_installer.py tests/test_host_adapters_skills.py tests/test_command_shims.py tests/test_layout_migration.py -m slow` -> `148 passed in 22.91s`. Child pre-transition lint: `aw ipd lint --phase pre-transition` on kvfsak (executed) conforming. Full-suite run `python3 -m pytest tests/ -m ''` -> `4 failed, 2698 passed, 1 skipped`; the 4 failures (test_cli_conformance_matrix UndeclaredLeafGuardTests x2, test_command_surface_declarations::test_zero_undeclared_parser_leaves, test_cli::test_every_subparser_has_fuller_description) are PRE-EXISTING and UNRELATED - they flag undeclared/empty-description CLI runner leaves (oc/agy/antigravity/pwatch/runs/ipd dependencies set/research pending/research set-outcome) added by concurrent work on main, OUTSIDE installerskill Scope-Paths (engine.py/host_adapters.py/tests), and the executed child kvfsak's V-05 already documented them as pre-existing (proven by stashing the engine.py change and re-running to the same failure). See DECISION 04-rldro6-D1. The installerskill Set's own acceptance criteria are all green.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (orchestrator with a single child; the only execution step here is whole-Set verification).

### Execution contract

1. Open questions: OQ-02, OQ-03, and OQ-04 are BLOCKING and MUST be resolved before this Set executes. While any remains open the Set is NO-GO. OQ-01 is non-blocking (resolved by following the bundle's existing host set).
2. Scope fence: touch only `agent_workflows/engine.py`, `agent_workflows/host_adapters.py`, and `tests/` (per Scope-Paths). Do NOT expand scope; if the work appears to need any other file or a new adapter-metadata renderer beyond what OQ-02 authorizes, STOP and report rather than widening scope.
3. Honesty rule (hard MUST): when you report tests/validation passed, paste the ACTUAL runner output. Never claim a pass you did not run.
4. Commit only this Set's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: perform the terminal transition as a POST-GATE transaction via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` (writes the workflow-history line, sets the terminal `Status:`, `git mv` to `executed/`, refreshes the index, path-scoped lifecycle commit). It is NOT an `E-*`/`V-*` item. Do not move to `executed/` until every `E-*` is performed and every `V-*` is verified with concrete pasted evidence.
