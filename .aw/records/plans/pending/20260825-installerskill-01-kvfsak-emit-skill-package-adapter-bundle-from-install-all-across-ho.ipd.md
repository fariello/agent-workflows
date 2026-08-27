# IPD: Emit skill package + adapter bundle from install_all across hosts, with uninstall/idempotency/install-diff tests

- Date: 2026-08-25
- Kind: child
- Concern: `engine.install_all` (engine.py:1953) writes only `body_members` + `shim_members`; the generated skill packages (`host_adapters.build_skill_package(...).to_files()`, host_adapters.py:349/227, aggregated by `AdapterBundle.skill_files()`, host_adapters.py:663) are never emitted by a real install. This child wires that skill-file emission in. NOTE: `generate_adapter_bundle` (host_adapters.py:677) returns an `AdapterBundle` whose ONLY writable-file output is `skill_files()`; the `host_adapters` field (host_adapters.py:661) is `to_dict`-only metadata with NO file renderer, so there are no "adapter bundle files" to emit unless OQ-02 authorizes a new renderer (default: it does not).
- Scope: Extend the installer run path to emit skill-package members: (1) in `install_into_repo` (engine.py:4992), build the skill member map via `generate_adapter_bundle(...).skill_files()` (equivalently `build_skill_package(...).to_files()` per workflow) and merge it into the desired member set passed to `install_all` (engine.py:1953), writing them with the SAME idempotent write + skip-unchanged logic as `shim_members` (`write_file`, engine.py:1782, which also records each written path into the ownership manifest); (2) extend `in_framework_namespace` (engine.py:1632), the prune scan `collect_target_framework_files` (engine.py:2012), and the prune defense-in-depth guard (engine.py:2072) to recognize the resolved skills directory, and resolve that directory correctly for BOTH the `aw` and legacy layouts (OQ-03) since `SHARED_SKILLS_DIR = ".agents/skills"` (host_adapters.py:60) is the LEGACY path only; (3) ensure the install-diff / desired-set union (engine.py:2062) and `collect_target_framework_files` account for skill files so an orphaned skill file is pruned and a re-install is a no-op. Uninstall needs NO member set: `uninstall_repo` (engine.py:3836) is manifest-driven and removes any file `write_file` recorded, so once (2) admits the skills dir the manifest path removes them. Extend install tests: a fresh install produces the skill package for each generated host; a second install is idempotent (empty diff); an orphaned skill file is pruned; uninstall removes the emitted skill files; and (if OQ-02 keeps them out) no adapter-metadata files are emitted.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/host_adapters.py, tests/
- Status: reviewed
- Set: installerskill
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: kvfsak

## Workflow history
- 2026-08-27 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS (OQ-02/03/04 blocking); materially re-planned emission wiring; adapter-file/namespace/prune/layout/uninstall corrected; E-items right-sized

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Wire skill-PACKAGE emission (`AdapterBundle.skill_files()`) into `install_into_repo`->`install_all`, writing them with the same idempotent `write_file` path as shim members, with the framework-namespace predicate + prune scan extended to recognize the (layout-resolved) skills directory, removed by manifest-driven uninstall, accounted for in install-diff, with tests across the generated hosts. Per-host adapter-metadata files are out of scope unless OQ-02 says otherwise.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

Depends on the blocking OQ resolutions (OQ-02, OQ-03, OQ-04) below; do not execute until they are resolved.

### Task group 1: skills-dir layout + namespace recognition

- [ ] E-01 Resolve the skills directory per layout: add an aw-layout skills-dir resolver in `engine.py` (alongside `resolve_workflows_dir`, engine.py:137) and pass the resolved `skill_dir` into `generate_adapter_bundle`/`build_skill_package` (both already accept a `skill_dir` argument), so a fresh install under the `aw` layout does NOT write to the legacy `.agents/skills` path (OQ-03).
  - Depends on: none
  - Expected outcome: the resolved skills-dir prefix is `.aw`-correct under the `aw` layout and `.agents/skills` under legacy.
  - Execution state: pending

- [ ] E-03 Extend `in_framework_namespace` (engine.py:1632) to return True for a path under the resolved skills-dir prefix, mirroring the shim-dir handling, so skill files are adoptable and pass the prune defense-in-depth guard (engine.py:2072) (OQ-04).
  - Depends on: E-01
  - Expected outcome: a path under the resolved skills dir returns True from `in_framework_namespace`.
  - Execution state: pending

- [ ] E-06 Extend `collect_target_framework_files` (engine.py:2012) to scan the resolved skills dir so present-but-orphaned skill files are discoverable by prune.
  - Depends on: E-03
  - Expected outcome: `collect_target_framework_files` includes existing skill files in its returned set.
  - Execution state: pending

### Task group 2: emit + install

- [ ] E-04 In `install_into_repo` (engine.py:4992), build the skill member map via `generate_adapter_bundle(...).skill_files()` and merge it into the desired member set given to `install_all` (engine.py:1953), written with the SAME idempotent skip-unchanged `write_file` logic as `shim_members` (so each path is recorded in the ownership manifest).
  - Depends on: E-01
  - Expected outcome: a fresh `aw install` writes the skill-package files for each generated host, recorded in the manifest.
  - Execution state: pending

### Task group 3: idempotency, prune, uninstall

- [ ] E-05 Include skill members in the desired-set union used for install-diff and prune (engine.py:2062) so a re-install is a no-op (empty diff / all-skipped) and an orphaned skill file (from a removed workflow) is pruned.
  - Depends on: E-04
  - Expected outcome: second install yields an empty diff; an orphaned skill file is pruned.
  - Execution state: pending

- [ ] E-07 Confirm manifest-driven `uninstall_repo` (engine.py:3836) removes the emitted skill files (it reads the ownership manifest that `write_file` populated; no separate uninstall member set is added).
  - Depends on: E-04
  - Expected outcome: `uninstall` removes exactly the emitted skill files and nothing else.
  - Execution state: pending

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
- Status: open
- Owner: none
- Resolution or deferral rationale: Follow `generate_adapter_bundle`'s existing host set (host_adapters.py:684, `ALL_ADAPTER_HOSTS`) and its skill-entry-point policy (`classify_discovery_policy`); no new host policy here.

### OQ-02: Does this child emit per-host adapter-metadata FILES, or only skill-package files?

- Blocking: yes
- Status: open
- Owner: none
- Resolution or deferral rationale: `AdapterBundle` exposes writable files ONLY via `skill_files()`; `host_adapters` is `to_dict`-only metadata with no file renderer (host_adapters.py:655-674). Option A (recommended): skill-package files only (matches the title + the one writable API + the "no forked generator" constraint). Option B: add a new adapter-metadata renderer (enlarges scope, contradicts the reuse constraint). MUST be resolved before execution. Mirrors orchestrator OQ-02.

### OQ-03: Under the `aw` layout, where do skill files land?

- Blocking: yes
- Status: open
- Owner: none
- Resolution or deferral rationale: `SHARED_SKILLS_DIR = ".agents/skills"` is legacy; `build_skill_package.to_files()` embeds it; `engine.py` has no aw-layout skills-dir resolver. Option A (recommended): add an aw-layout resolver and pass the resolved `skill_dir` into the generators (they accept `skill_dir`). Option B: keep `.agents/skills` for both (inconsistent with the aw layout). MUST be resolved - the path drives write, prune, namespace, and uninstall. Mirrors orchestrator OQ-03.

### OQ-04: Extend `in_framework_namespace` + prune scan + prune guard for the skills dir - confirm?

- Blocking: yes
- Status: open
- Owner: none
- Resolution or deferral rationale: Required so skill files are written, adopted, pruned when orphaned, and manifest-uninstalled. Recommended: extend `in_framework_namespace` (engine.py:1632), `collect_target_framework_files` (engine.py:2012), and the prune guard (engine.py:2072) to admit the resolved skills-dir prefix, mirroring shim-dir handling. MUST be resolved (load-bearing mechanism the original plan omitted). Mirrors orchestrator OQ-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted test output proving the aw-layout skills-dir resolver returns a `.aw`-correct prefix under the `aw` layout and `.agents/skills` under legacy, and that the resolved `skill_dir` is threaded into the generators (a generated skill path is under the resolved dir).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Pasted test output showing a path under the resolved skills dir returns True from `in_framework_namespace` and passes the prune defense-in-depth guard.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Pasted test-runner output: a fresh install into a temp repo writes `SKILL.md` + resource files under the resolved skills dir for each generated host, and the paths are recorded in the ownership manifest.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Pasted test-runner output: second install yields an empty diff / all `[already current]`; an orphaned skill file is pruned. Plus the full-suite green summary line and `aw ipd lint --phase pre-transition --agent <this plan>` conforming.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Pasted test output showing `collect_target_framework_files` includes an existing skill file in its returned set.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Pasted test-runner output: manifest-driven `uninstall` removes exactly the emitted skill files and nothing else; (if OQ-02 keeps them out) no adapter-metadata files are written.
  - Observed evidence:
  - Result: pending




## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one cohesive concern (emit skill-package files through the installer and make them prune/uninstall-correct). The added E-items are the load-bearing sub-steps of that one concern (layout resolution, namespace recognition, emit, idempotency), not separate concerns; they stay within the single `install`+skills surface. If execution reveals they are genuinely independent test-surfaces, STOP and split into an ordered Set rather than padding one pass.

### Execution contract

1. Open questions: OQ-02, OQ-03, OQ-04 are BLOCKING and MUST be resolved before execution; while any is open the plan is NO-GO. OQ-01 is non-blocking.
2. Scope fence: touch only `agent_workflows/engine.py`, `agent_workflows/host_adapters.py`, and `tests/` (per Scope-Paths). Do NOT expand scope; if it appears to need another file or a new adapter-metadata renderer beyond what OQ-02 authorizes, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/validation passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit only this plan's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: as a POST-GATE transaction (not an `E-*`/`V-*` item) run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` to write the workflow-history line, set terminal `Status:`, `git mv` to `executed/`, refresh the index, and make the path-scoped lifecycle commit. Do not move to `executed/` until every `E-*` is performed and every `V-*` is verified with concrete pasted evidence.
