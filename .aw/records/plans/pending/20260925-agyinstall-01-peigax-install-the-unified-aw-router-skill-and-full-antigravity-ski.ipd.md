# IPD: Install the unified aw router skill and full Antigravity skill coverage

- Date: 2026-09-25
- Kind: child
- Concern: Antigravity discovers slash commands only through `.agents/skills/<name>/SKILL.md`, and the installer emits no `aw` skill there, so `/aw` (and every workflow reachable only as a command shim) is invisible in Antigravity; `host_adapters` also still treats antigravity as a runner-template-only host.
- Scope: Add a generated `aw` router skill package to the canonical adapter bundle so every install writes `.agents/skills/aw/SKILL.md`; map antigravity's native `skill` feature to the router role and list it among the v1 hosts; test and document it.
- Scope-Paths: agent_workflows/host_adapters.py, tests/test_agy_skill_install.py, docs/skill-selection.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: high
- Id: peigax
- From-Backlog: u0fmeu
- Blocks-Release: next
- Set: agyinstall
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog u0fmeu; re-measured a real `aw install` into a scratch repo (46 skill packages, no `.agents/skills/aw/`, 17 workflows with no skill) and the antigravity rows of `V1_HOSTS` / `HOST_FEATURE_ROLE_MAP`.

## Goal

After `aw install` / `aw setup` into any repo, Antigravity shows `/aw` in its slash menu and can dispatch every workflow verb through it, because the installer writes a generated, manifest-tracked `.agents/skills/aw/SKILL.md` router; `host_adapters` records antigravity's skill feature as a router like OpenCode and Codex.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: router skill generator

- [ ] E-01 Add `host_adapters.build_aw_router_skill_package(workflows, skill_dir=SHARED_SKILLS_DIR, target_layout="aw")` returning a `SkillPackage` named `aw`: frontmatter `name: aw`, a trigger description containing both "Use when" and "Do not use", a `semantic-digest` computed with `workflow_profile.semantic_digest` over the sorted `(command, body)` pairs of the manifest rows (reuse the one digest scheme, no new algorithm), a body that mirrors `engine.aw_dispatcher_shim` (read `<workflows_dir>/index.md`, treat the first argument as the verb, resolve and read-and-execute the body, bare `/aw` lists verbs), a compact verb list of the non-catalog rows (`not engine.is_concern_catalog_row(w)`), and one `reference/canonical-body.md` resource pointing at the manifest. Raise `AdapterGenerationError` if any manifest row's `command` slugifies to `aw` (name collision). Export it in `__all__`.
  - Depends on: none
  - Expected outcome: the returned package has `validate_skill_package(pkg) == []`, `pkg.within_budget()` is True, and `pkg.main_file_path()` is `.agents/skills/aw/SKILL.md`.
  - Execution state: pending

- [ ] E-02 In `host_adapters.generate_adapter_bundle`, append `build_aw_router_skill_package(workflows, skill_dir=skill_dir, target_layout=target_layout)` to `skill_packages` after the per-workflow packages, so `AdapterBundle.skill_files()` (the only writable output `engine._build_skill_members` consumes) carries the router with no engine change.
  - Depends on: E-01
  - Expected outcome: `generate_adapter_bundle(...).skill_files()` contains `.agents/skills/aw/SKILL.md` and `.agents/skills/aw/reference/canonical-body.md`.
  - Execution state: pending

### Task group 2: antigravity host mapping

- [ ] E-03 Change `V1_HOSTS` to `("opencode", "codex", "antigravity")` and add `"skill": ROLE_ROUTER` to `HOST_FEATURE_ROLE_MAP["antigravity"]` (keeping `runner_template`). Update the `V1_HOSTS` comment to say antigravity consumes the same `.agents/skills` target. Do not touch the registry: `build_host_adapter` still gates any `supported` claim on `HostCapabilityRegistry.query_capability`, so the new feature lands in `unverified_features` until a probe promotes it (no forged capability).
  - Depends on: none
  - Expected outcome: `build_host_adapter("antigravity", HostCapabilityRegistry(), "1.0.0").to_dict()` shows `role_map["skill"] == "router"`, `is_v1` True, and `"skill"` in `unverified_features` (not `supported_features`).
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-04 Add `tests/test_agy_skill_install.py` with: (a) a real `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)` into a `tests.support`-style temp git repo asserting `.agents/skills/aw/SKILL.md` exists, starts with `---`, contains `name: aw`, references `.aw/system/workflows/index.md`, and that the path is recorded in the ownership manifest (`manifest.load(manifest.resolve_manifest_path(repo)).recorded_hash(...)` is not None); (b) a second install is idempotent (file bytes unchanged); (c) the router lists every non-catalog verb from `engine.parse_manifest(SOURCE_WORKFLOWS)` (sync with repo workflows); (d) `validate_skill_package` returns `[]` for the router; (e) the collision guard raises `AdapterGenerationError`; (f) the antigravity adapter mapping from E-03.
  - Depends on: E-02, E-03
  - Expected outcome: all new tests pass with the change; test (a) fails on the unpatched tree.
  - Execution state: pending

- [ ] E-05 Document the router: in `docs/skill-selection.md` add a "The `aw` router skill" subsection (one generated package that dispatches any verb, digest over the whole manifest, why it exists: Antigravity has no command-shim directory, so `/aw` and command-only workflows such as `plan-review` are reached through it); add a CHANGELOG `2.0.0 (pending)` bullet in user-facing prose with no em or en dashes.
  - Depends on: E-01
  - Expected outcome: `grep -n "aw router" docs/skill-selection.md` and a CHANGELOG hit for `.agents/skills/aw/SKILL.md`.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-04, E-05
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Skill generation has ONE generator: `engine._build_skill_members` calls `host_adapters.generate_adapter_bundle(...).skill_files()` and the commit `5af28bbb` ("feat(installer): emit generated skill packages in the install run path") forbids forking it. Adding the router inside `generate_adapter_bundle` keeps that rule and inherits manifest recording, idempotent skip-unchanged, orphan prune and manifest-driven uninstall for free.
- Skills land in `engine.SKILLS_DIR` / `host_adapters.SHARED_SKILLS_DIR` (`.agents/skills`) for BOTH layouts, and `HOST_SKILL_DIR["antigravity"]` is already `.agents/skills`, so no path change is needed.
- Capability claims are evidence-gated: `build_host_adapter` only lists a feature as `supported` when the registry says so. Even OpenCode currently reports `supported_features: []` (measured), so adding the antigravity mapping cannot overclaim.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Install already writes skills to `.agents/skills` unconditionally (not host-gated), so requirement 1 ("install agy skills by default") is met for per-workflow skills. | Scratch `aw install` into a fresh git repo: `ls .agents/skills \| wc -l` -> 46. |
| F-2 | No `aw` skill is emitted; `/aw` exists only as `.opencode/commands/aw.md` / `.claude/commands/aw.md` via `engine.generate_shim_members` ("shims[f\"{shim_dir}/aw.md\"] = aw_dispatcher_shim(") over `COMMAND_SHIM_DIRS`, which has no Antigravity entry. | Same probe: `ls .agents/skills \| grep -x aw` empty; `.opencode/commands/aw.md` present. |
| F-3 | 17 workflows classify as `POLICY_GENERATED_COMMAND` in `classify_discovery_policy` and get NO skill: release-review, release-review-plan, plan-review, plan-review-long, spec-review, verify-execution, ipd-lifecycle, getting-started, verify, spec, incident, release-notes, migrate, benchmark, setup-repo, scaffold, assess-all. In Antigravity they are reachable only through a router. | Python probe over `engine.parse_manifest(resolve_source_root(None))`. |
| F-4 | `V1_HOSTS = ("opencode", "codex")`; `HOST_FEATURE_ROLE_MAP["antigravity"]` is only `{"runner_template": ROLE_NONINTERACTIVE_RUNTIME}`. | `host_adapters.py` constants; `build_host_adapter("antigravity", ...)` role_map probe. |
| F-5 | No executed or pending plan carries `From-Backlog: u0fmeu` or emits an `aw` skill. The former `tests/test_installer_skill_emission.py` was removed in `19313eed` (test trim), so skill emission currently has no dedicated test. | `grep -rl "From-Backlog: u0fmeu" .aw/records` empty; `git log --diff-filter=D`. |

## Proposed changes (ordered, validatable)

1. E-01 router package builder in `host_adapters`.
2. E-02 include it in `generate_adapter_bundle` (sole install seam).
3. E-03 antigravity `skill -> router` mapping plus `V1_HOSTS`.
4. E-04 tests, E-05 docs, E-06 full suite.

## Deferred / out of scope (with reason)

- Emitting a per-workflow skill for the 17 command-only workflows (F-3). The router makes them reachable from Antigravity as `/aw <verb>`; emitting standalone skills would also surface them to OpenCode and Codex from the shared dir, duplicating their existing command shims. See OQ-01.
  - Carrier-Declined: the `aw` router delivered here covers reachability; a standalone-skill policy change is a discovery-policy decision (OQ-01) that should be filed only if the maintainer wants direct `/plan-review` in Antigravity.
- Promoting antigravity's `skill` capability to `supported` in the host capability registry. That requires an executed positive and negative probe, which this plan cannot run unattended.
  - Carrier-Declined: registry promotion is driven by `aw host probe`, which is the existing mechanism; no code change is needed to allow it later.

## Scope check

- Over-scope: none. No engine, installer-wizard or registry code changes; the router rides the existing bundle seam.
- Under-scope: requirement 1 host-gating ("whenever Antigravity is present or targeted") is satisfied more strongly than asked, because skills are emitted for every install regardless of `enabled_hosts` (F-1).

## Required tests / validation

New `tests/test_agy_skill_install.py` (real install into a temp repo, idempotence, verb sync, package validation, collision guard, adapter mapping) plus the bare suite. The install-emits-router test must be shown failing on the unpatched tree.

## Spec / documentation sync

- `docs/skill-selection.md`: new router subsection (E-05).
- `CHANGELOG.md`: one user-facing bullet (E-05).
- No `.spec.md` is amended: the skill-package contract (`validate_skill_package`) is unchanged and the router satisfies it.

## Open questions

### OQ-01: Should command-only workflows also get standalone skills?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default for this plan is NO: the `aw` router gives Antigravity access to all 17 (`/aw plan-review ...`) without duplicating OpenCode/Codex command shims in the shared skills dir. The maintainer may later want direct `/plan-review` in Antigravity, which is a `classify_discovery_policy` change with cross-host effects.

### OQ-02: Should the router be gated on `enabled_hosts` containing antigravity?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Per-workflow skills are already emitted unconditionally (F-1) into the shared dir that OpenCode and Codex also read, and `project_context.DEFAULT_ENABLED_HOSTS` already includes `antigravity`; gating only the router would be inconsistent and would leave a default install without `/aw` in Antigravity.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste output of `python3 -c "from agent_workflows import engine, host_adapters as h; wf=engine.parse_manifest(engine.resolve_source_root(None)); p=h.build_aw_router_skill_package(wf); print(p.main_file_path(), h.validate_skill_package(p), p.within_budget(), p.main_file_bytes())"` showing `.agents/skills/aw/SKILL.md [] True <bytes under 8192>`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste output of a probe printing `sorted(k for k in generate_adapter_bundle(wf, src, HostCapabilityRegistry()).skill_files() if k.startswith(".agents/skills/aw/"))` showing exactly the `SKILL.md` and `reference/canonical-body.md` paths.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste output of `python3 -c "from agent_workflows import host_adapters as h; from agent_workflows.host_capability_registry import HostCapabilityRegistry as R; d=h.build_host_adapter('antigravity', R(), '1.0.0').to_dict(); print(d['role_map'], d['is_v1'], d['supported_features'], d['unverified_features'])"` showing `'skill': 'router'`, `True`, `[]`, and `skill` among unverified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_agy_skill_install.py` passing with the change, AND the same command run with only E-02's append reverted (a temporary edit removing the append line, never `git stash`) showing the install-emits-router test FAILING, then restored.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `grep -n "aw\` router\|aw router" docs/skill-selection.md` and `grep -n "agents/skills/aw/SKILL.md" CHANGELOG.md` hits, and `grep -nP "\x{2013}|\x{2014}"` on the added CHANGELOG lines returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing `passed` with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <this plan> -- <Scope-Paths>`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
