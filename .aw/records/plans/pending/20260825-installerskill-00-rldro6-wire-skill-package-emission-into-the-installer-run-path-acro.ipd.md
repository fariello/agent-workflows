# IPD: Wire skill-package emission into the installer run() path across hosts

- Date: 2026-08-25
- Kind: orchestrator
- Concern: The execset Set (Order 05, 2h7777) proved skill/shim generation at the library level (`build_skill_package` digest parity + `generate_shim_members` drift-free) and exposed `/exec-set` via the existing shim path, but did NOT wire skill-package emission (`host_adapters.generate_adapter_bundle` / `build_skill_package(...).to_files()`) into `engine.install_all` (engine.py:1953), which today writes only `body_members` + `shim_members`. So a real `aw install` never emits the generated skill packages / per-host adapter bundles. Wiring it is a cross-cutting installer-output change (all hosts + uninstall + idempotency + install-diff), deliberately deferred out of the packaging Order (D21-2h7777-D2). Backlog item bplplj (medium).
- Scope: Wire skill-PACKAGE emission (`host_adapters.build_skill_package(...).to_files()` via `AdapterBundle.skill_files()`, host_adapters.py:227/663) into the installer run path so `aw install` writes the generated skill files alongside body + shim members, covering the hosts the bundle already generates, uninstall, idempotency, and install-diff. Single coherent child (01) plus this orchestrator. Deliverable: `install_into_repo` (engine.py:4992) builds the skill member map and merges it into the desired set passed to `install_all` (engine.py:1953), written the same idempotent way as shim members; the framework-namespace predicate (`in_framework_namespace`, engine.py:1632), the prune scan (`collect_target_framework_files`, engine.py:2012) and the prune defense-in-depth guard (engine.py:2072) are extended to recognize the skills directory so orphaned skill files are pruned and re-install is a no-op; uninstall is manifest-driven (`uninstall_repo`, engine.py:3836 removes any file `write_file` recorded in the ownership manifest), so it removes emitted skill files WITHOUT a separate member set once the namespace guard admits them; install-diff/idempotency tests are extended so a fresh install emits the skill package and a re-install is a no-op. NOTE: the per-host `host_adapters` metadata in `AdapterBundle` (host_adapters.py:661) is structured data (`to_dict`), NOT writable files - see OQ-02; this Set does not emit adapter-metadata files unless OQ-02 decides otherwise.
- Scope-Paths: agent_workflows/engine.py, agent_workflows/host_adapters.py, tests/
- Status: approved
- Set: installerskill
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rldro6
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS (OQ-02/03/04 blocking); adapter-file conflation, namespace/prune/layout gaps, uninstall mechanism, citations, execution contract fixed

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `aw install` actually emit the generated skill packages by wiring `AdapterBundle.skill_files()` (from `generate_adapter_bundle` / `build_skill_package(...).to_files()`) into the installer run path, idempotently and across uninstall + install-diff, closing the gap execset deferred. Whether the per-host `host_adapters` metadata is also emitted as files depends on OQ-02.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; child 01 carries the work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [ ] E-01 After child 01 executes, confirm a fresh `aw install` emits the skill-package files (`AdapterBundle.skill_files()`) for the hosts the bundle generates, a re-install is a no-op (idempotent, empty install-diff), an orphaned skill file (from a removed workflow) is pruned, and `uninstall` removes the emitted skill files; full suite green.
  - Depends on: none
  - Expected outcome: install-diff test shows skill-package members on fresh install, empty diff on re-install, pruning of an orphaned skill file, and clean manifest-driven removal on uninstall. If OQ-02 resolves to include adapter-metadata files, they are covered too; otherwise the check explicitly asserts NO adapter-metadata files are emitted.
  - Execution state: pending

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
- Status: open
- Owner: none
- Resolution or deferral rationale: `AdapterBundle` (host_adapters.py:655-674) exposes writable files ONLY through `skill_files()`; its `host_adapters` field is `to_dict`-only metadata with no file renderer. The plan title/backlog say "skill-package emission"; the body previously also said "adapter bundle files". Option A (recommended): scope this Set to skill-package files only (matches title + the one existing writable API); adapter-metadata file emission, if ever wanted, is a separate future concern with its own renderer. Option B: add a new adapter-metadata renderer in this Set (contradicts the "no forked generator / reuse existing library" constraint and enlarges scope). MUST be resolved before execution.

### OQ-03: Under the `aw` layout, where do skill files land?

- Blocking: yes
- Status: open
- Owner: none
- Resolution or deferral rationale: `SHARED_SKILLS_DIR = ".agents/skills"` (host_adapters.py:60) is the LEGACY path and `build_skill_package.to_files()` embeds it in the relative paths; `engine.py` has no aw-layout skills-dir resolver (only `resolve_workflows_dir`). Option A: add an aw-layout skills-dir resolver and pass the resolved `skill_dir` into `build_skill_package`/`generate_adapter_bundle` (they already accept a `skill_dir` argument). Option B: keep `.agents/skills` for both layouts (inconsistent with the aw-layout convention that everything framework-owned lives under `.aw/system/`; likely wrong). MUST be resolved before execution because the target path drives write, prune, namespace, and uninstall.

### OQ-04: Extend the framework-namespace predicate + prune scan for the skills dir - confirm approach?

- Blocking: yes
- Status: open
- Owner: none
- Resolution or deferral rationale: For skill files to be written, adopted, pruned when orphaned, and manifest-uninstalled safely, `in_framework_namespace` (engine.py:1632), `collect_target_framework_files` (engine.py:2012), and the prune defense-in-depth guard (engine.py:2072) MUST all recognize the resolved skills dir. Recommended: extend all three to admit the skills-dir prefix resolved per OQ-03, mirroring how shim dirs are handled. MUST be resolved (it is the load-bearing mechanism the original plan omitted).

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of the repo's real test runner showing (a) the new install-emission test passing: a fresh install into a temp repo writes the expected `SKILL.md` + resource files under the resolved skills dir for each generated host; (b) a re-install test showing an empty install-diff / all-skipped `[already current]`; (c) an orphaned-skill-file prune test; (d) an uninstall test showing the skill files removed via the manifest; and (e) the full suite green (paste the actual pass/fail summary line). Also paste `aw ipd lint --phase pre-transition --agent <child>` conforming for child 01.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (orchestrator with a single child; the only execution step here is whole-Set verification).

### Execution contract

1. Open questions: OQ-02, OQ-03, and OQ-04 are BLOCKING and MUST be resolved before this Set executes. While any remains open the Set is NO-GO. OQ-01 is non-blocking (resolved by following the bundle's existing host set).
2. Scope fence: touch only `agent_workflows/engine.py`, `agent_workflows/host_adapters.py`, and `tests/` (per Scope-Paths). Do NOT expand scope; if the work appears to need any other file or a new adapter-metadata renderer beyond what OQ-02 authorizes, STOP and report rather than widening scope.
3. Honesty rule (hard MUST): when you report tests/validation passed, paste the ACTUAL runner output. Never claim a pass you did not run.
4. Commit only this Set's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move on completion: perform the terminal transition as a POST-GATE transaction via `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` (writes the workflow-history line, sets the terminal `Status:`, `git mv` to `executed/`, refreshes the index, path-scoped lifecycle commit). It is NOT an `E-*`/`V-*` item. Do not move to `executed/` until every `E-*` is performed and every `V-*` is verified with concrete pasted evidence.
