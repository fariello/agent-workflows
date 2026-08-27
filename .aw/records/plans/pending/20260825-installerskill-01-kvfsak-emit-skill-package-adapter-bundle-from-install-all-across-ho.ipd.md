# IPD: Emit skill package + adapter bundle from install_all across hosts, with uninstall/idempotency/install-diff tests

- Date: 2026-08-25
- Kind: child
- Concern: `engine.install_all` (engine.py:1953) writes only `body_members` + `shim_members`; the generated skill packages (`host_adapters.build_skill_package(...).to_files()`, host_adapters.py:349/227, aggregated by `AdapterBundle.skill_files()`, host_adapters.py:663) are never emitted by a real install. This child wires that skill-file emission in. NOTE: `generate_adapter_bundle` (host_adapters.py:677) returns an `AdapterBundle` whose ONLY writable-file output is `skill_files()`; the `host_adapters` field (host_adapters.py:661) is `to_dict`-only metadata with NO file renderer, so there are no "adapter bundle files" to emit unless OQ-02 authorizes a new renderer (default: it does not).
- Scope: Extend the installer run path to emit skill-package members: (1) in `install_into_repo` (engine.py:4992), build the skill member map via `generate_adapter_bundle(...).skill_files()` (equivalently `build_skill_package(...).to_files()` per workflow) and merge it into the desired member set passed to `install_all` (engine.py:1953), writing them with the SAME idempotent write + skip-unchanged logic as `shim_members` (`write_file`, engine.py:1782, which also records each written path into the ownership manifest); (2) extend `in_framework_namespace` (engine.py:1632), the prune scan `collect_target_framework_files` (engine.py:2012), and the prune defense-in-depth guard (engine.py:2072) to recognize the resolved skills directory, and resolve that directory correctly for BOTH the `aw` and legacy layouts (OQ-03) since `SHARED_SKILLS_DIR = ".agents/skills"` (host_adapters.py:60) is the LEGACY path only; (3) ensure the install-diff / desired-set union (engine.py:2062) and `collect_target_framework_files` account for skill files so an orphaned skill file is pruned and a re-install is a no-op. Uninstall needs NO member set: `uninstall_repo` (engine.py:3836) is manifest-driven and removes any file `write_file` recorded, so once (2) admits the skills dir the manifest path removes them. Extend install tests: a fresh install produces the skill package for each generated host; a second install is idempotent (empty diff); an orphaned skill file is pruned; uninstall removes the emitted skill files; and (if OQ-02 keeps them out) no adapter-metadata files are emitted.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/host_adapters.py, tests/
- Status: approved
- Set: installerskill
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: kvfsak
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS (OQ-02/03/04 blocking); materially re-planned emission wiring; adapter-file/namespace/prune/layout/uninstall corrected; E-items right-sized

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Wire skill-PACKAGE emission (`AdapterBundle.skill_files()`) into `install_into_repo`->`install_all`, writing them with the same idempotent `write_file` path as shim members, with the framework-namespace predicate + prune scan extended to recognize the (layout-resolved) skills directory, removed by manifest-driven uninstall, accounted for in install-diff, with tests across the generated hosts. Per-host adapter-metadata files are out of scope unless OQ-02 says otherwise.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

Depends on the blocking OQ resolutions (OQ-02, OQ-03, OQ-04) below; do not execute until they are resolved.

### Task group 1: skills-dir layout + namespace recognition

- [x] E-01 Resolve the skills directory per layout: add a skills-dir resolver in `engine.py` (`resolve_skills_dir`, alongside `resolve_workflows_dir`) and pass the resolved `skill_dir` into `generate_adapter_bundle`/`build_skill_package` (both already accept a `skill_dir` argument). Per DECISION 02-kvfsak-D2 (OQ-03), the resolver returns the shared HOST-CONSUMPTION dir `.agents/skills` for BOTH layouts (skills mirror the command shims - discovered by host tools in a fixed dir - not relocated under `.aw/system/` like framework-read bodies); `.aw/system/skills` would be discovered by no host. Threaded via `_build_skill_members` into the generators.
  - Depends on: none
  - Expected outcome: the resolved skills-dir prefix is `.agents/skills` for both layouts (deliberate evidence-based deviation from the OQ-03 wording; see 02-kvfsak-D2, flagged for human review), and the resolved `skill_dir` drives the generated package paths.
  - Execution state: performed

- [x] E-03 Extend `in_framework_namespace` (engine.py:1632) to return True for a path under the resolved skills-dir prefix (`SKILLS_DIR + "/"`), mirroring the shim-dir handling, so skill files are adoptable and pass the prune defense-in-depth guard (engine.py:2072) (OQ-04, DECISION 02-kvfsak-D3).
  - Depends on: E-01
  - Expected outcome: a path under the resolved skills dir returns True from `in_framework_namespace`.
  - Execution state: performed

- [x] E-06 Extend `collect_target_framework_files` (engine.py:2012) to recursively scan the resolved skills dir so present-but-orphaned skill files (SKILL.md + reference/ + scripts/) are discoverable by prune.
  - Depends on: E-03
  - Expected outcome: `collect_target_framework_files` includes existing skill files in its returned set.
  - Execution state: performed

### Task group 2: emit + install

- [x] E-04 In `install_into_repo`, build the skill member map via `_build_skill_members` (which calls `generate_adapter_bundle(...).skill_files()`, OQ-02 Option A: skill files only, no adapter-metadata files) and merge it into the desired member set given to `install_all` as `generated_members = {**shim_members, **skill_members}`, written with the SAME idempotent skip-unchanged `write_file` logic as `shim_members` (so each path is recorded in the ownership manifest).
  - Depends on: E-01
  - Expected outcome: a fresh `aw install` writes the skill-package files for each generated host, recorded in the manifest.
  - Execution state: performed

### Task group 3: idempotency, prune, uninstall

- [x] E-05 Include skill members in the desired-set union used for install-diff and prune by passing `generated_members` (shim + skill) to `prune_stale` (whose `desired = set(body_members) | set(shim_members.keys())`, engine.py:2062), so a re-install is a no-op (empty diff / all-skipped) and an orphaned skill file (from a removed workflow) is pruned.
  - Depends on: E-04
  - Expected outcome: second install yields an empty diff; an orphaned skill file is pruned.
  - Execution state: performed

- [x] E-07 Confirm manifest-driven `uninstall_repo` (engine.py:3836) removes the emitted skill files (it reads the ownership manifest that `write_file` populated; skill files record as `kind="file"`, which `plan_uninstall` includes in `remove`; no separate uninstall member set is added). No code change required beyond E-03/E-04; verified by test.
  - Depends on: E-04
  - Expected outcome: `uninstall` removes exactly the emitted skill files and nothing else.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `install_all` (engine.py:1953) writes `body_members` + `shim_members` with idempotent skip-unchanged via `write_file` (engine.py:1782); the desired set is `set(body_members) | set(shim_members)` (engine.py:2062). Skill members must join this set the same way.
- `write_file` (engine.py:1782) records every written path into the ownership manifest (`_record_written`), which is what makes a written file adoptable and removable by manifest-driven uninstall.
- `generate_adapter_bundle` (host_adapters.py:677) returns an `AdapterBundle`; only `AdapterBundle.skill_files()` (host_adapters.py:663) / `build_skill_package(...).to_files()` (host_adapters.py:227) produce writable path->content maps. The `host_adapters` field (host_adapters.py:661) is `to_dict`-only metadata - NOT files. Reuse these generators; do not fork.
- `in_framework_namespace` (engine.py:1632) recognizes ONLY `.agents/workflows/`, `.aw/system/`, and the shim dirs - NOT the skills dir. `collect_target_framework_files` (engine.py:2012) scans only those. The prune loop applies `in_framework_namespace` as a defense-in-depth guard (engine.py:2072). All three must learn the skills dir.
- `SHARED_SKILLS_DIR = ".agents/skills"` (host_adapters.py:60) is the LEGACY layout path; `engine.py` has no aw-layout skills-dir resolver. The target under the `aw` layout is undefined until OQ-03 is resolved.
- `uninstall_repo` (engine.py:3836) is MANIFEST-DRIVEN and takes no member set; it removes what `write_file` recorded (subject to the `in_framework_namespace` guard on the legacy-fallback/prune paths).
- execset deliberately deferred this wiring (D21-2h7777-D2); this child closes exactly that gap.

## Findings

The skill-package GENERATORS exist and are verified (execset). But wiring is NOT "purely joining a member set": review found the installer has no concept of a skills directory at all - `in_framework_namespace`, `collect_target_framework_files`, and the prune guard omit it, there is no aw-layout skills-dir resolver, and `generate_adapter_bundle`'s adapter-metadata half produces no files. The real work spans a layout resolver, three namespace/prune touch-points, the emit-and-merge, and the idempotency/prune/uninstall wiring - larger and different from the original two E-items, which also misdescribed uninstall as taking a member set.

## Proposed changes (ordered, validatable)

1. `engine.py`: add an aw-layout skills-dir resolver; pass the resolved `skill_dir` into the generators (E-01).
2. `engine.py`: extend `in_framework_namespace` (1632), `collect_target_framework_files` (2012), and the prune guard (2072) to recognize the skills dir.
3. `engine.py` `install_into_repo` (4992): merge `skill_files()` into the desired set passed to `install_all`.
4. `engine.py`: include skill members in the desired-set union (2062) for install-diff + prune; verify manifest-driven `uninstall_repo` removes them.
5. `tests/`: fresh-install emits per host; re-install idempotent; orphaned skill file pruned; uninstall removes; (if OQ-02 keeps them out) no adapter-metadata files emitted.

## Deferred / out of scope (with reason)

- Skill/adapter CONTENT generation: already delivered by execset; not touched here.
- Per-host adapter-METADATA file emission: no writable renderer exists (`host_adapters` is `to_dict`-only); out of scope unless OQ-02 explicitly authorizes adding one.

## Scope check

- Over-scope: none.
- Under-scope (found in plan-review, now corrected above): the original checklist omitted the skills-dir layout resolver, the `in_framework_namespace`/`collect_target_framework_files`/prune-guard extensions, and misdescribed uninstall - all REQUIRED for correct emission + prune + uninstall.

## Required tests / validation

- A fresh install into a temp repo emits the skill-package files (`SKILL.md` + resources) for each generated host under the layout-resolved skills dir (assert files present and path-correct for the `aw` layout).
- A second install yields an empty install-diff / all `[already current]` (idempotent, no duplication).
- Removing a workflow then re-installing prunes its now-orphaned skill file.
- `uninstall` removes exactly the emitted skill files (via the manifest) and nothing else.
- If OQ-02 keeps adapter-metadata files out of scope, a test asserts NO adapter-metadata files are written.
- Validation MUST paste the ACTUAL test-runner output (see V-items); never an un-run "tests pass" claim.

## Spec / documentation sync

- Update installer docs to note skill-package emission is part of `aw install`, including the layout-resolved target directory.

## Open questions

### OQ-01: Emit skill packages for all hosts, or only the hosts the bundle already generates?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED (DECISION 02-kvfsak-D4). Follow `generate_adapter_bundle`'s existing behavior: it builds ONE skill-package family per skill-entry-point workflow (`classify_discovery_policy == POLICY_SKILL_ENTRY_POINT`) using a single `skill_dir`; it does not fan skill FILES out per host (the per-host distinction is in the `to_dict`-only `host_adapters` metadata, not files). No new host policy.

### OQ-02: Does this child emit per-host adapter-metadata FILES, or only skill-package files?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED - Option A (DECISION 02-kvfsak-D1). Emit ONLY skill-package files (`AdapterBundle.skill_files()`); do NOT emit adapter-metadata files. `host_adapters` is `to_dict`-only metadata with no file renderer (host_adapters.py:654-674); Option A matches the title, the one writable API, and the no-forked-generator constraint. A test (`test_no_adapter_metadata_files_emitted`) asserts no adapter-metadata files are written. Mirrors orchestrator OQ-02.

### OQ-03: Under the `aw` layout, where do skill files land?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED (DECISION 02-kvfsak-D2), with a deliberate evidence-based DEVIATION from the recommended-wording flagged for human review. Added a centralized resolver `resolve_skills_dir(target_layout)` in `engine.py` and threaded its result as `skill_dir` into the generators (satisfying the "add a resolver, pass resolved skill_dir" structural requirement). The resolver returns the shared HOST-CONSUMPTION dir `.agents/skills` for BOTH layouts rather than a `.aw`-prefixed dir: a skill package exists to be DISCOVERED by a host tool scanning a fixed dir (exactly like the command shims `.opencode/commands`/`.claude/commands`, which are layout-independent), whereas `resolve_workflows_dir` relocates only the framework's OWN bodies. `.aw/system/skills` would be discovered by no host, defeating emission; and `migration_compact` already uses `.agents/skills` for both layouts. If the maintainer prefers `.aw/system/skills` or per-host native dirs, only `resolve_skills_dir` + the generator host loop change. Mirrors orchestrator OQ-03.

### OQ-04: Extend `in_framework_namespace` + prune scan + prune guard for the skills dir - confirm?

- Blocking: yes
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: RESOLVED as recommended (DECISION 02-kvfsak-D3). Extended `in_framework_namespace` (admits `SKILLS_DIR + "/"`) and `collect_target_framework_files` (recursively scans the resolved skills dir); the prune defense-in-depth guard (engine.py:2072) then admits skill paths automatically via the updated predicate, and `_stage_installed_file` routes them to the hard `git add` path (skill files are tracked, like workflow bodies). Verified by V-03/V-06 and the orphan-prune tests. Mirrors orchestrator OQ-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted test output proving the skills-dir resolver and that the resolved `skill_dir` is threaded into the generators (a generated skill path is under the resolved dir). NOTE per DECISION 02-kvfsak-D2 (OQ-03): the resolver returns `.agents/skills` for BOTH layouts (deliberate evidence-based deviation from the original "`.aw`-correct" wording; skills are host-consumption artifacts like the command shims), flagged for human review.
  - Observed evidence: `tests/test_installer_skill_emission.py::SkillsDirResolverTests` -> `test_resolver_returns_shared_host_dir_for_both_layouts` asserts `resolve_skills_dir("aw") == resolve_skills_dir("legacy") == ".agents/skills" == SKILLS_DIR`; `test_resolved_skill_dir_is_threaded_into_generators` asserts every `generate_adapter_bundle(..., skill_dir=resolve_skills_dir(layout)).skill_files()` path starts with the resolved `skill_dir`, for both layouts. Full file run (serial, `-n0`): `10 passed in 14.75s` (see V-05 for the run line). Smoke: `resolve_skills_dir aw: .agents/skills` / `resolve_skills_dir legacy: .agents/skills`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Pasted test output showing a path under the resolved skills dir returns True from `in_framework_namespace` and passes the prune defense-in-depth guard.
  - Observed evidence: `tests/test_installer_skill_emission.py::NamespaceAndCollectTests::test_skill_path_is_in_framework_namespace` asserts `in_framework_namespace(".agents/skills/release-review/SKILL.md")` and `.../scripts/verify_digest.py` are True, while `src/app.py` and `.agents/other/thing.md` are False (predicate did not go broad). The orphan-prune tests (V-05) exercise the defense-in-depth guard end-to-end (a skill orphan is actually pruned, which requires `in_framework_namespace` to admit it). Smoke: `in_framework_namespace skill: True` / `in_framework_namespace nonskill: False`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Pasted test-runner output: a fresh install into a temp repo writes `SKILL.md` + resource files under the resolved skills dir for each generated host, and the paths are recorded in the ownership manifest.
  - Observed evidence: `tests/test_installer_skill_emission.py::SkillEmissionInstallTests::test_fresh_install_emits_skill_packages_and_records_manifest` installs into a temp git repo, asserts a non-empty set of `.agents/skills/<name>/SKILL.md` routers each accompanied by `reference/canonical-body.md` + `scripts/verify_digest.py`, and asserts the manifest's `.agents/skills/*` entries equal the on-disk skill fileset. `::test_no_adapter_metadata_files_emitted` asserts every emitted skills-dir file matches `^<name>/(SKILL.md|reference/.+|scripts/.+)$` (OQ-02 Option A: no adapter-metadata files). Smoke on the real source bundle: `num skill files: 135` / `num SKILL.md: 45` / `manifest skill entries: 135` / `layout: aw`.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Pasted test-runner output: second install yields an empty diff / all `[already current]`; an orphaned skill file is pruned. Plus the full-suite green summary line and `aw ipd lint --phase pre-transition --agent <this plan>` conforming.
  - Observed evidence: `::test_reinstall_is_idempotent_no_op_for_skills` asserts a second install newly-installs 0 skill files, reports every skill file `[already current]` (count == fresh fileset), and prunes 0 (smoke on real bundle: `re-install skill installed(non-skip): 0` / `re-install skill skipped: 135 -> ['.agents/skills/advise-architect/SKILL.md [already current]']` / `re-install skill pruned: 0`). `::test_orphaned_tracked_skill_file_is_pruned` -> committed orphan pruned (`.agents/skills/zzz-orphan/SKILL.md [git rm]`, orphan exists False); `::test_orphaned_untracked_skill_file_is_pruned` -> `.agents/skills/yyy-orphan/SKILL.md [rm]`, orphan exists False. New-file run (serial `-n0`): `tests/test_installer_skill_emission.py ..........  [100%]` -> `10 passed in 14.75s`. Regression (install+adapters+shims+layout): `python3 -m pytest tests/test_installer.py tests/test_host_adapters_skills.py tests/test_command_shims.py tests/test_layout_migration.py -m slow` -> `148 passed in 26.18s`. Full suite `python3 -m pytest tests/ -m ''` -> 4 failures, all PRE-EXISTING and UNRELATED (undeclared CLI parser leaves in test_command_surface_declarations/test_cli/test_cli_conformance_matrix: `agy run`, `oc runipd`, `research pending`, `ipd dependencies set`, ...); proven pre-existing by re-running them with my engine.py change stashed (same `14 != 0 : Found undeclared parser leaves` failure), and outside this plan's Scope-Paths (introduced by concurrent work on main, HEAD 2b102631 -> 275324a during this turn). `aw ipd lint --phase pre-transition` on this plan reports conforming after these E/V updates.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: Pasted test output showing `collect_target_framework_files` includes an existing skill file in its returned set.
  - Observed evidence: `tests/test_installer_skill_emission.py::NamespaceAndCollectTests::test_collect_target_framework_files_includes_skill_files` writes `.agents/skills/demo/SKILL.md` into a temp repo and asserts it appears in `collect_target_framework_files(repo, target_layout="aw")`. Also covered transitively by the orphan-prune tests (V-05), which require the orphan to be collected before it can be pruned.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: Pasted test-runner output: manifest-driven `uninstall` removes exactly the emitted skill files and nothing else; (if OQ-02 keeps them out) no adapter-metadata files are written.
  - Observed evidence: `tests/test_installer_skill_emission.py::SkillEmissionInstallTests::test_uninstall_removes_emitted_skill_files_via_manifest` installs + commits, records the on-disk skill fileset, runs `uninstall_repo(repo, use_git=True)`, and asserts the count of `removed .agents/skills/...` actions equals the fileset size and that zero skill files remain. Smoke on real bundle: `skill files before uninstall: 135` / `uninstall removed skill actions: 135` / `skill files after uninstall: 0`. No-adapter-metadata coverage is in `::test_no_adapter_metadata_files_emitted` (V-04).
  - Result: pass




## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one cohesive concern (emit skill-package files through the installer and make them prune/uninstall-correct). The added E-items are the load-bearing sub-steps of that one concern (layout resolution, namespace recognition, emit, idempotency), not separate concerns; they stay within the single `install`+skills surface. If execution reveals they are genuinely independent test-surfaces, STOP and split into an ordered Set rather than padding one pass.

### Execution contract

1. Open questions: OQ-02, OQ-03, OQ-04 are BLOCKING and MUST be resolved before execution; while any is open the plan is NO-GO. OQ-01 is non-blocking.
2. Scope fence: touch only `agent_workflows/engine.py`, `agent_workflows/host_adapters.py`, and `tests/` (per Scope-Paths). Do NOT expand scope; if it appears to need another file or a new adapter-metadata renderer beyond what OQ-02 authorizes, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/validation passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit only this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: as a POST-GATE transaction (not an `E-*`/`V-*` item) run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` to write the workflow-history line, set terminal `Status:`, `git mv` to `executed/`, refresh the index, and make the path-scoped lifecycle commit. Do not move to `executed/` until every `E-*` is performed and every `V-*` is verified with concrete pasted evidence.
