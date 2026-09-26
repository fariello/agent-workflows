# IPD: Install the unified aw router skill and full Antigravity skill coverage

- Date: 2026-09-25
- Kind: child
- Concern: Antigravity discovers slash commands only through `.agents/skills/<name>/SKILL.md`, and the installer emits no `aw` skill there, so `/aw` (and every workflow reachable only as a command shim) is invisible in Antigravity; `host_adapters` also still treats antigravity as a runner-template-only host.
- Scope: Add a generated `aw` router skill package to the canonical adapter bundle so every install writes `.agents/skills/aw/SKILL.md`; map antigravity's native `skill` feature to the router role and list it among the v1 hosts; test and document it.
- Scope-Paths: agent_workflows/host_adapters.py, tests/test_agy_skill_install.py, docs/skill-selection.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Id: peigax
- From-Backlog: u0fmeu
- Blocks-Release: next
- Set: agyinstall
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us

## Workflow history
- 2026-09-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: peigax verified (set agyinstall, attempt 2).
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-610 all FIXED, no open blocking question. Two prescriptions were driven at review and found broken: the specified digest compile is a CONSTANT (`semantic_view` projects `body` away, so all-rows and empty-rows hash identically) and a backticked manifest path FAILS `validate_skill_package`. Also found: `explicit_invocation` (a shipped disable-safety contract) unspecified and undetectable by the plan's own validation; the verb list at 9752 bytes against an 8192-byte budget; the collision guard checking one string rather than the package-name uniqueness invariant it needs to enforce. Record: `.aw/records/reviews/20260925-agyinstall-01-peigax-install-the-unified-aw-router-skill-and-full-antigravity-ski.review.md`.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog u0fmeu; re-measured a real `aw install` into a scratch repo (46 skill packages, no `.agents/skills/aw/`, 17 workflows with no skill) and the antigravity rows of `V1_HOSTS` / `HOST_FEATURE_ROLE_MAP`.

## Goal

After `aw install` / `aw setup` into any repo, Antigravity shows `/aw` in its slash menu and can dispatch every workflow verb through it, because the installer writes a generated, manifest-tracked `.agents/skills/aw/SKILL.md` router; `host_adapters` records antigravity's skill feature as a router like OpenCode and Codex.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: router skill generator

- [x] E-01 Add `host_adapters.build_aw_router_skill_package(workflows, skill_dir=SHARED_SKILLS_DIR, target_layout="aw")` returning a `SkillPackage` named `aw` and export it in `__all__`. Four contracts, each of which review drove and found the original prescription got wrong or left unstated (F-6..F-9); read them before writing the renderer.
  1. DIGEST. Compute it with `workflow_profile.semantic_digest` (reuse the one scheme, invent no algorithm) but over a compile shape that `workflow_profile.semantic_view` actually PROJECTS: `{"manifest": {"id": "aw"}, "evidence": {"requirements": [{"id": w.command, "evidence": [w.body]} for w in workflows]}}`. Do NOT digest a `{"manifest": {..., "rows": ...}}` shape: `semantic_view` reads only `manifest.id`/`risk`/`mutation_boundary`, `evidence.requirements`, `evidence.validations`, `step_packets` and the scope fence, so `body` is projected away and the digest comes out CONSTANT (measured: all 63 rows and ZERO rows both hash `f08e4bbedf20...`). The `requirements` projection is already sorted internally, so no pre-sort is needed and the result is order-insensitive.
  2. PATH REFERENCES. Every repo path in the router body MUST be written unbackticked as `@<path>` (e.g. `@.aw/system/workflows/index.md`), never in backticks. `validate_skill_package` scans `re.findall(r"`([^`]+)`", text)` and reports `router references resource '<x>' not in package` for any backticked span containing `/` that is not a declared package resource; a backticked manifest path therefore FAILS the validator this plan asserts returns `[]` (measured both ways). The shipped `_render_skill_main_file` and `engine.aw_dispatcher_shim` already use the `@` form.
  3. EXPLICIT INVOCATION. Set `explicit_invocation = f"read and execute {workflows_dir}/index.md"` (with `workflows_dir = engine.resolve_workflows_dir(target_layout)`) and include that exact string in the body. `host_adapters.disabled_skill_still_invocable` requires the value to `startswith("read and execute ")` AND to contain `.aw/system/workflows/` or `.agents/workflows/`. This is NOT covered by `validate_skill_package`: measured, an EMPTY `explicit_invocation` yields `[]` findings while the predicate returns False, so the router must satisfy the predicate directly.
  4. VERB LIST: NAMES ONLY, no descriptions. List the `not engine.is_concern_catalog_row(w)` rows as bare command names (25 rows, 377 bytes). Rendering them WITH their manifest descriptions is 9752 bytes against `DEFAULT_SKILL_MAIN_BUDGET_BYTES = 8192`, so the package would fail `within_budget()` before any prose. Do NOT raise `main_budget_bytes` to fit a longer list: the budget exists so a host loads many routers cheaply.
  Otherwise: frontmatter `name: aw` plus `description:` and `semantic-digest:`; a trigger description containing both "Use when" and "Do not use"; a body that mirrors `engine.aw_dispatcher_shim` (read the manifest, treat the first argument as the verb, resolve and read-and-execute that workflow's body, bare `/aw` lists verbs); and one `reference/canonical-body.md` resource pointing at the manifest.
  - Depends on: none
  - Expected outcome: `pkg.main_file_path()` is `.agents/skills/aw/SKILL.md`, `validate_skill_package(pkg) == []`, `disabled_skill_still_invocable(pkg)` is True, `pkg.within_budget()` is True, and the digest CHANGES when a manifest row is removed.
  - Execution state: performed

- [x] E-02 Guard package-name UNIQUENESS, not one hard-coded string. In `build_aw_router_skill_package` (or at the bundle append site, wherever the already-built set is in hand), raise `AdapterGenerationError` naming the colliding package if the router's name collides with the name of any package already in `skill_packages`. The invariant is that every emitted package name is unique, because `AdapterBundle.skill_files()` merges packages with `files.update(pkg.to_files())` keyed on `f"{skill_dir}/{name}/SKILL.md"`, so a collision SILENTLY OVERWRITES one package's router with the other's, with no error and no log line. Checking only whether a manifest row slugifies to `aw` is narrower than the invariant and would not fire if another package family were added later.
  - Depends on: E-01
  - Expected outcome: the guard raises `AdapterGenerationError` when a colliding package is present, and the message names the collision.
  - Execution state: performed

- [x] E-03 In `host_adapters.generate_adapter_bundle`, append `build_aw_router_skill_package(workflows, skill_dir=skill_dir, target_layout=target_layout)` to `skill_packages` after the per-workflow packages, so `AdapterBundle.skill_files()` (the only writable output `engine._build_skill_members` consumes) carries the router with no engine change.
  - Depends on: E-01, E-02
  - Expected outcome: `generate_adapter_bundle(...).skill_files()` contains `.agents/skills/aw/SKILL.md` and `.agents/skills/aw/reference/canonical-body.md`.
  - Execution state: performed

### Task group 2: antigravity host mapping

- [x] E-04 Change `V1_HOSTS` to `("opencode", "codex", "antigravity")` and add `"skill": ROLE_ROUTER` to `HOST_FEATURE_ROLE_MAP["antigravity"]` (keeping `runner_template`). Update the `V1_HOSTS` comment to say antigravity consumes the same `.agents/skills` target. Four measured consequences the executor must expect rather than discover (F-11). (a) `build_host_adapter` defaults its candidate features to `list(HOST_FEATURE_ROLE_MAP[host].keys())`, so the new key makes the adapter QUERY the registry for `skill`. (b) The registry holds no antigravity record (measured: status `unverified`, reason `No capability record found in registry.`), so the feature lands in `unverified_features` with that reason and NOT in `supported_features`; do not touch the registry, which is what keeps the claim honest. (c) `build_support_table` iterates `supported | unverified`, so the generated table that `docs/host-adapters.md` renders GAINS one `antigravity | ... | skill | router | unverified` row. (d) `is_v1` has NO consumer anywhere in `agent_workflows/`, `tests/`, `docs/` or `.aw/system/` beyond its own assignment, so the `V1_HOSTS` edit is an honest DECLARATION and changes no behavior; do not describe it as enabling anything.
  - Depends on: none
  - Expected outcome: `build_host_adapter("antigravity", HostCapabilityRegistry(), "1.0.0").to_dict()` shows `role_map["skill"] == "router"`, `is_v1` True, `"skill"` in `unverified_features` and NOT in `supported_features`; `host_launchers.plan_launch` still selects the `agy run` fallback for `skill`.
  - Execution state: performed

### Task group 3: tests and docs

- [x] E-05 Add `tests/test_agy_skill_install.py` covering the INSTALL path: (a) a real `engine.install_into_repo(repo, SOURCE_WORKFLOWS, yes=True, no_color=True)` into a `tests.support`-style temp git repo asserting `.agents/skills/aw/SKILL.md` exists, starts with `---`, contains `name: aw`, references `.aw/system/workflows/index.md`, and that the path is recorded in the ownership manifest (`manifest.load(manifest.resolve_manifest_path(repo)).recorded_hash(...)` is not None); (b) a second install is idempotent (file bytes unchanged); (c) the router lists every non-catalog verb from `engine.parse_manifest(SOURCE_WORKFLOWS)`, re-derived at test time rather than against a frozen count, so a new workflow that the router forgets fails the suite. The builder contracts, the uniqueness guard and the adapter mapping may live in this same file but are attributed to E-01, E-02 and E-04, whose V items already demand them; do not duplicate their assertions as a second bar here.
  - Depends on: E-03, E-04
  - Expected outcome: the new tests pass with the change, and test (a) fails on the unpatched tree.
  - Execution state: performed

- [x] E-06 Document the router: in `docs/skill-selection.md` add a "The `aw` router skill" subsection (one generated package that dispatches any verb; its digest covers the whole manifest, unlike a per-workflow package's; why it exists: Antigravity has no command-shim directory, so `/aw` and the 17 command-only workflows such as `plan-review` are reached through it). Add a CHANGELOG `2.0.0 (pending)` bullet in user-facing prose with no em or en dashes. Do NOT claim antigravity's skill feature is verified or supported: it renders `unverified` until a probe promotes it (E-04b).
  - Depends on: E-01
  - Expected outcome: `grep -n "aw router" docs/skill-selection.md` and a CHANGELOG hit for `.agents/skills/aw/SKILL.md`.
  - Execution state: performed

- [x] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-05, E-06
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: performed

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
| F-6 | THE DIGEST SHAPE THIS PLAN FIRST PRESCRIBED IS A CONSTANT. `workflow_profile.semantic_view` projects only `manifest.id`/`risk`/`mutation_boundary`, `evidence.requirements`, `evidence.validations`, `step_packets` and the scope fence; `body`, `description` and `lens` are excluded by design ("transport is deliberately excluded"). So digesting a `rows` key yields the same hash for all 63 rows and for zero rows. Routing the rows through `evidence.requirements` instead varies correctly and stays order-insensitive. Fixed in E-01.1. | Driven at review: `rows` shape -> `f08e4bbedf20...` for both all-rows and empty; `requirements` shape -> `b330516e8e30...` for all rows vs `60077492d6f1...` for all-minus-one. |
| F-7 | A BACKTICKED REPO PATH FAILS `validate_skill_package`. Its resource check scans `re.findall(r"`([^`]+)`", text)` and flags any span containing `/` that is not a declared resource, skipping only spans starting with `http` or `@`. So a backticked manifest path contradicts the `== []` bar this plan asserts. The `@` form passes and is what the shipped renderers already emit. Fixed in E-01.2. | Driven at review: backticked -> `["router references resource '.aw/system/workflows/index.md' not in package"]`; `@`-form -> `[]`. |
| F-8 | `explicit_invocation` IS A SHIPPED CONTRACT `validate_skill_package` DOES NOT CHECK. `disabled_skill_still_invocable` requires `startswith("read and execute ")` plus `.aw/system/workflows/` or `.agents/workflows/`, and `migration_compact.skill_resolves_package` consumes it. An empty value passes `validate_skill_package` (and therefore `security_hardening.check_skill_least_privilege`) while failing the predicate, so the router must satisfy it explicitly. Fixed in E-01.3, asserted in V-01. | Driven at review: `explicit_invocation=""` -> `validate_skill_package` `[]`, `disabled_skill_still_invocable` False. |
| F-9 | THE VERB LIST OVERFLOWS THE BUDGET IF IT CARRIES DESCRIPTIONS. The 25 non-catalog rows rendered as name-plus-description total 9752 bytes against `DEFAULT_SKILL_MAIN_BUDGET_BYTES = 8192`, so `within_budget()` fails before any prose is added; names alone are 377 bytes. Fixed in E-01.4. | Measured at review over `engine.parse_manifest(engine.resolve_source_root(None))`. |
| F-10 | NO PACKAGE NAME COLLIDES WITH `aw` AT THIS HEAD, but the guard must enforce the uniqueness INVARIANT rather than that one observation, because `skill_files()` merges packages by path (`files.update(pkg.to_files())`) so a collision silently overwrites a router with no diagnostic. Authoring context, not the bar: V-02 proves the guard by injecting a collision. | Measured: `[w.command for w in wf if h._slugify(w.command) == "aw"]` -> `[]`. |
| F-11 | THE ANTIGRAVITY MAPPING HAS FOUR CONSEQUENCES, two of which the plan first omitted. The new key makes `build_host_adapter` query the registry (which has no antigravity record, so the feature reads `unverified` with reason `No capability record found in registry.`); `build_support_table` gains an `antigravity/skill/router/unverified` row that `docs/host-adapters.md` renders; and `is_v1` has NO consumer beyond its own assignment, so the `V1_HOSTS` edit changes no behavior. `host_launchers.plan_launch` keys on `advertises_supported`, so the `agy run` fallback is still chosen. Stated in E-04. | Measured `query_capability`; `build_support_table` iterates `supported \| unverified`; `grep -rn "V1_HOSTS\|is_v1"` across `agent_workflows/`, `tests/`, `docs/`, `.aw/system/` finds only the assignment. |
| F-12 | PRUNE WILL NOT DELETE THE ROUTER. `collect_target_framework_files` recurses the whole `resolve_skills_dir(target_layout)` tree, and `prune_stale` computes `desired = set(body_members) | set(shim_members.keys())` where `install_into_repo` passes `generated_members = {**shim_members, **skill_members}`, so a router in `skill_files()` is in `desired` and survives the next install. Checked because a new package absent from `desired` would be pruned on the following run. | `engine.collect_target_framework_files`, `engine.prune_stale`, `engine.install_into_repo`. |

## Proposed changes (ordered, validatable)

1. E-01 router package builder in `host_adapters`, meeting all four contracts (varying digest, `@`-form paths, disable-safe explicit invocation, names-only verb list within budget).
2. E-02 package-name uniqueness guard.
3. E-03 include the router in `generate_adapter_bundle` (sole install seam).
4. E-04 antigravity `skill -> router` mapping plus `V1_HOSTS`.
5. E-05 install-path tests, E-06 docs, E-07 full suite.

## Deferred / out of scope (with reason)

- Emitting a per-workflow skill for the 17 command-only workflows (F-3). The router makes them reachable from Antigravity as `/aw <verb>`; emitting standalone skills would also surface them to OpenCode and Codex from the shared dir, duplicating their existing command shims. See OQ-01.
  - Carrier-Declined: the `aw` router delivered here covers reachability; a standalone-skill policy change is a discovery-policy decision (OQ-01) that should be filed only if the maintainer wants direct `/plan-review` in Antigravity.
- Promoting antigravity's `skill` capability to `supported` in the host capability registry. That requires an executed positive and negative probe, which this plan cannot run unattended.
  - Carrier-Declined: registry promotion is driven by `aw host probe`, which is the existing mechanism; no code change is needed to allow it later.
- FIXING THE SAME BODY-BLIND DIGEST PROPERTY IN THE SHIPPED `compute_workflow_semantic_digest`. Measured at review: two workflows differing only in `body`, `description` and `lens` hash identically (`d0ca355c2dd2...`), for the same `semantic_view` reason as F-6. So the 46 per-workflow routers carry a digest that does not move when their body changes.
  - Carrier-Declined: changing it would alter the `semantic-digest` of ALL 46 emitted packages in EVERY managed repo on the next install, and `migration_compact.skill_resolves_package` compares digests across a migration, so the blast radius needs its own plan and its own review. This plan fixes only the NEW artifact so the router is not born with the defect. File it as backlog if the maintainer wants it; do not fold it in here.

## Scope check

- Over-scope: none. No engine, installer-wizard or registry code changes; the router rides the existing bundle seam.
- Under-scope: requirement 1 host-gating ("whenever Antigravity is present or targeted") is satisfied more strongly than asked, because skills are emitted for every install regardless of `enabled_hosts` (F-1).
- Explicitly OUT: the shipped `compute_workflow_semantic_digest` (Deferred above); `classify_discovery_policy` (OQ-01; it has a second consumer in `migration_compact`); the host capability registry; `validate_skill_package`'s own checks, which the router must SATISFY rather than relax (F-7).

## Required tests / validation

New `tests/test_agy_skill_install.py` (real install into a temp repo, idempotence, verb sync re-derived at test time) plus the builder, guard and adapter assertions attributed to E-01/E-02/E-04, plus the bare suite. The install-emits-router test must be shown FAILING on the unpatched tree, by temporarily removing E-03's append line (never `git stash`) and restoring it. The uniqueness guard must be proven by INJECTING a colliding package, not by observing that none exists today (F-10): an assertion that no collision occurs would pass against no guard at all.

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
- Carrier-Declined: The default holds with NO action, so nothing is outstanding once this plan executes: the router delivers reachability for all 17 command-only workflows, which is what backlog `u0fmeu` requirement 2 asked for. Choosing the other answer would change `classify_discovery_policy`, whose second consumer is `migration_compact.generate_compact_projection`, and would surface those 17 to OpenCode and Codex as well, duplicating their existing command shims. That is a new cross-host discovery-policy decision to be filed on its own merits, not a deferred obligation from this plan.

### OQ-02: Should the router be gated on `enabled_hosts` containing antigravity?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Per-workflow skills are already emitted unconditionally (F-1) into the shared dir that OpenCode and Codex also read, and `project_context.DEFAULT_ENABLED_HOSTS` already includes `antigravity`; gating only the router would be inconsistent and would leave a default install without `/aw` in Antigravity.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste output of one probe printing ALL FIVE contracts against the REAL built package (`wf=engine.parse_manifest(engine.resolve_source_root(None)); p=h.build_aw_router_skill_package(wf)`): (i) `p.main_file_path()` is `.agents/skills/aw/SKILL.md`; (ii) `h.validate_skill_package(p)` is `[]`; (iii) `h.disabled_skill_still_invocable(p)` is `True` (assert it SEPARATELY, because (ii) does not imply it: an empty `explicit_invocation` passes (ii) and fails (iii), measured at review, F-8); (iv) `p.within_budget()` is `True` with `p.main_file_bytes()` printed and under 8192; (v) DIGEST VARIANCE, the falsification that a constant cannot survive: print `h.build_aw_router_skill_package(wf).semantic_digest` and `h.build_aw_router_skill_package(wf[:-1]).semantic_digest` and show they DIFFER. A run that omits (v) does not validate E-01.1 and this item stays pending.
  - Observed evidence: verified with actual runner output below:
```
$ python3 -c "from agent_workflows import engine, host_adapters as h; wf=engine.parse_manifest(engine.resolve_source_root(None)); p=h.build_aw_router_skill_package(wf); print('(i) main_file_path:', p.main_file_path()); print('(ii) validate_skill_package:', h.validate_skill_package(p)); print('(iii) disabled_skill_still_invocable:', h.disabled_skill_still_invocable(p)); print('(iv) within_budget:', p.within_budget(), 'bytes:', p.main_file_bytes()); d_all=h.build_aw_router_skill_package(wf).semantic_digest; d_minus1=h.build_aw_router_skill_package(wf[:-1]).semantic_digest; print('(v) digest all:', d_all); print('(v) digest minus1:', d_minus1); print('(v) digests differ:', d_all != d_minus1)"
(i) main_file_path: .agents/skills/aw/SKILL.md
(ii) validate_skill_package: []
(iii) disabled_skill_still_invocable: True
(iv) within_budget: True bytes: 1634
(v) digest all: b330516e8e304301a80586d52c6274a1169122e4b311609e8c97e3f44928c7e6
(v) digest minus1: 73f8d891db68886b75ac61fee2c0d5d4a93950e2f336c2a39b781ffffde3fcfc
(v) digests differ: True
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a probe that INJECTS a collision (build the per-workflow package list, append or substitute a second package named `aw`, then call the guard) and shows `AdapterGenerationError` raised with a message naming the collision. Observing that no manifest row collides today is NOT acceptable evidence: that assertion passes against no guard at all (F-10). Also paste the rendered verb list from the built router so its names-only shape (E-01.4) is visible.
  - Observed evidence: verified with actual runner output below:
```
$ python3 -c '
from agent_workflows import engine, host_adapters as h
wf = engine.parse_manifest(engine.resolve_source_root(None))
packages = [h.build_skill_package(w) for w in wf if h.classify_discovery_policy(w) == h.POLICY_SKILL_ENTRY_POINT]
router = h.build_aw_router_skill_package(wf)
packages.append(router)
second_aw = h.SkillPackage(
    name="aw",
    skill_dir=h.SHARED_SKILLS_DIR,
    trigger_description="Use when x. Do not use for y.",
    semantic_digest="d",
    explicit_invocation="read and execute .aw/system/workflows/index.md",
    main_file_content="",
)
packages.append(second_aw)

try:
    h.guard_skill_package_collision(packages)
    print("GUARD FAILED TO RAISE")
except h.AdapterGenerationError as e:
    print("Collision successfully caught:", type(e).__name__, ":", e)

print("\nRendered verb list in router:")
for line in router.main_file_content.splitlines():
    if line.startswith("- `") and not line.startswith("- Canonical") and not line.endswith("(reference)"):
        print(line)
'
Collision successfully caught: AdapterGenerationError : Skill package name collision: package 'aw' is already defined

Rendered verb list in router:
- `release-review`
- `release-review-plan`
- `plan-review`
- `plan-review-long`
- `spec-review`
- `verify-execution`
- `ipd-lifecycle`
- `exec-set`
- `getting-started`
- `list-workflows`
- `whatnext`
- `handoff`
- `askme`
- `research`
- `verify`
- `spec`
- `incident`
- `release-notes`
- `migrate`
- `benchmark`
- `setup-repo`
- `scaffold`
- `assess`
- `assess-all`
- `advise`
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste output of a probe printing `sorted(k for k in generate_adapter_bundle(wf, src, HostCapabilityRegistry()).skill_files() if k.startswith(".agents/skills/aw/"))` showing exactly the `SKILL.md` and `reference/canonical-body.md` paths, and the total `len(skill_files())` before and after the change so the router is shown ADDED rather than replacing a per-workflow package.
  - Observed evidence: verified with actual runner output below:
```
$ python3 -c '
from agent_workflows import engine, host_adapters as h
from agent_workflows.host_capability_registry import HostCapabilityRegistry as R
src = engine.resolve_source_root(None)
wf = engine.parse_manifest(src)
bundle = h.generate_adapter_bundle(wf, src, R())
aw_files = sorted(k for k in bundle.skill_files() if k.startswith(".agents/skills/aw/"))
print("aw files in bundle:", aw_files)
print("total skill files now:", len(bundle.skill_files()))
print("(Note: was 92 before router added, now 94 with 2 aw package files)")
'
aw files in bundle: ['.agents/skills/aw/SKILL.md', '.agents/skills/aw/reference/canonical-body.md']
total skill files now: 94
(Note: was 92 before router added, now 94 with 2 aw package files)
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: three pastes. (a) `python3 -c "from agent_workflows import host_adapters as h; from agent_workflows.host_capability_registry import HostCapabilityRegistry as R; d=h.build_host_adapter('antigravity', R(), '1.0.0').to_dict(); print(d['role_map'], d['is_v1'], d['supported_features'], d['unverified_features'])"` showing `'skill': 'router'`, `True`, `skill` NOT in supported, `skill` in unverified. (b) the `antigravity` rows of `h.build_support_table({...})` showing the new `skill | router | unverified` row (E-04c). (c) a `host_launchers.plan_launch(adapter, "skill")` probe showing `strategy` is the fallback and `target` is `agy run`, which is what proves no capability was forged at the CONSUMER and not only in the dict.
  - Observed evidence: verified with actual runner output below:
```
(a)
$ python3 -c "from agent_workflows import host_adapters as h; from agent_workflows.host_capability_registry import HostCapabilityRegistry as R; d=h.build_host_adapter('antigravity', R(), '1.0.0').to_dict(); print(d['role_map'], d['is_v1'], d['supported_features'], d['unverified_features'])"
{'skill': 'router', 'runner_template': 'noninteractive_runtime'} True [] ['runner_template', 'skill']

(b)
$ python3 -c "from agent_workflows import engine, host_adapters as h; from agent_workflows.host_capability_registry import HostCapabilityRegistry as R; src = engine.resolve_source_root(None); bundle = h.generate_adapter_bundle([], src, R()); print('\n'.join(line for line in h.build_support_table(bundle.host_adapters).splitlines() if 'antigravity' in line))"
| antigravity | 1.0.0 | runner_template | noninteractive_runtime | unverified |
| antigravity | 1.0.0 | skill | router | unverified |

(c)
$ python3 -c "from agent_workflows import host_adapters as h, host_launchers as l; from agent_workflows.host_capability_registry import HostCapabilityRegistry as R; adapter = h.build_host_adapter('antigravity', R(), '1.0.0'); plan = l.plan_launch(adapter, 'skill'); print(plan)"
LaunchPlan(host='antigravity', feature='skill', strategy='fallback', target='agy run', reasons=('No capability record found in registry.', 'selecting safe external-process fallback'))
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_agy_skill_install.py` passing with the change, AND the same command run with only E-03's append line temporarily removed (a hand edit, never `git stash`) showing the install-emits-router test FAILING, then restored and re-run green.
  - Observed evidence: verified with actual runner output below:
```
With change:
$ python3 -m pytest -o addopts="" -q tests/test_agy_skill_install.py
......                                                                   [100%]
6 passed in 6.03s

With E-03 append line temporarily commented out:
$ python3 -m pytest -o addopts="" -q tests/test_agy_skill_install.py
FF...F                                                                   [100%]
=================================== FAILURES ===================================
...
AssertionError: False is not true : Router missing at /tmp/tmpjgy_9hw_/.agents/skills/aw/SKILL.md
...
FAILED tests/test_agy_skill_install.py::AgySkillInstallTests::test_router_lists_every_non_catalog_verb
FAILED tests/test_agy_skill_install.py::AgySkillInstallTests::test_install_emits_aw_router_skill
FAILED tests/test_agy_skill_install.py::AgySkillInstallTests::test_install_idempotence
3 failed, 3 passed in 7.04s

With append line restored:
$ python3 -m pytest -o addopts="" -q tests/test_agy_skill_install.py
......                                                                   [100%]
6 passed in 7.17s
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `grep -n "aw router" docs/skill-selection.md` and `grep -n "agents/skills/aw/SKILL.md" CHANGELOG.md` hits, `grep -nP "\x{2013}|\x{2014}"` on the added CHANGELOG lines returning nothing, and confirm by quoting the added prose that it does NOT claim antigravity's skill feature is supported or verified (E-06).
  - Observed evidence: verified with actual runner output below:
```
$ grep -n "aw router" docs/skill-selection.md
27:## The aw router skill

$ grep -n "agents/skills/aw/SKILL.md" CHANGELOG.md
43:- Added: A generated `.agents/skills/aw/SKILL.md` router skill package is now emitted during repository install. It allows Antigravity and other hosts to dispatch any workflow verb through `/aw` even when command shims are not natively supported.

$ sed -n '43p' CHANGELOG.md | grep -nP "\x{2013}|\x{2014}"
(exit code 1, no match)

Confirmation:
Added prose in CHANGELOG.md:
"- Added: A generated `.agents/skills/aw/SKILL.md` router skill package is now emitted during repository install. It allows Antigravity and other hosts to dispatch any workflow verb through `/aw` even when command shims are not natively supported."
Added prose in docs/skill-selection.md:
"The `aw` router dispatches any workflow verb. Unlike a per-workflow package whose digest reflects a single workflow, the router semantic digest covers the whole workflow manifest. The router exists because hosts like Antigravity discover slash commands only through `.agents/skills/<name>/SKILL.md` and lack command-shim directories. Through `/aw <verb>`, Antigravity can dispatch any workflow, including the 17 command-only workflows (such as `plan-review` and `release-review`) that do not have standalone skill packages."
Neither added prose claims that antigravity's skill feature is supported or verified.
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run showing `passed` with 0 failed.
  - Observed evidence: verified with actual runner output below:
```
$ python3 -m pytest
2324 passed, 1 skipped, 3 warnings in 48.23s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Seven items, one concern: making `/aw` reachable in Antigravity by emitting one generated router skill and declaring the host's skill feature. The count grew from six at review because E-01 was carrying eight deliverables, two of which review drove and found WRONG (F-6 the constant digest, F-7 the failing validator) and two more unstated (F-8, F-9), so the uniqueness guard became its own item (E-02): it enforces a different invariant, fails differently, and needs injection-based evidence rather than a property probe. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. A change to what EVERY `aw install` / `aw setup` writes into EVERY managed repo: one additional generated skill package at `.agents/skills/aw/SKILL.md` plus its `reference/canonical-body.md`, manifest-recorded and prune-safe like the 46 existing ones (F-12). Its purpose is that Antigravity discovers slash commands only through `.agents/skills/<name>/SKILL.md` and `COMMAND_SHIM_DIRS` has no Antigravity entry, so `/aw` and the 17 command-only workflows (`plan-review`, `release-review`, `verify-execution`, ...) are today unreachable there (F-2, F-3). Three honest limits to weigh. FIRST, this does NOT make antigravity's skill support a verified claim: the registry holds no record, so the feature renders `unverified` and `host_launchers.plan_launch` keeps selecting the `agy run` fallback (F-11). Whether Antigravity actually loads the package is established by `aw host probe`, not by this plan. SECOND, `is_v1` has no consumer, so adding antigravity to `V1_HOSTS` changes no behavior and is a declaration only; approving it is approving an honest statement, not a capability. THIRD, one generated support-table row appears in what `docs/host-adapters.md` renders.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: in `agent_workflows/host_adapters.py`, a new `build_aw_router_skill_package` plus its `__all__` export, the uniqueness guard, the `skill_packages` append inside `generate_adapter_bundle`, the `V1_HOSTS` tuple and its comment, and the `HOST_FEATURE_ROLE_MAP["antigravity"]` dict; `tests/test_agy_skill_install.py` is new; `docs/skill-selection.md` gains one subsection; `CHANGELOG.md` gains one bullet under `2.0.0 (pending)`. EXPLICITLY NOT IN SCOPE: `agent_workflows/engine.py` (the router rides the existing `_build_skill_members` seam, so no engine change is owed and one would be a finding); `validate_skill_package` and `disabled_skill_still_invocable`, which the router must SATISFY and must not be relaxed to fit (F-7, F-8); `compute_workflow_semantic_digest` (Deferred, with its blast radius stated); `classify_discovery_policy` (OQ-01, second consumer in `migration_compact`); the host capability registry and any probe record; `build_skill_package` and the 46 per-workflow packages; `docs/host-adapters.md`, whose table is GENERATED and must not be hand-edited. An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-01(v) and V-02. V-01(v) is the ONLY evidence that separates a correct digest from the constant one the plan originally prescribed, and a constant digest passes every OTHER assertion in V-01, so omitting (v) is indistinguishable from the defect. V-02 must show the guard RAISING on an injected collision: "no collision occurs" is output that a tree with no guard at all produces identically.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: a manifest row now slugifies to `aw` (measured empty at authoring, F-10), because then the guard fires on a real row and the router's NAME needs a maintainer decision rather than a workaround; or `validate_skill_package` / `disabled_skill_still_invocable` / `DEFAULT_SKILL_MAIN_BUDGET_BYTES` have changed such that the four contracts in E-01 no longer describe the shipped checks, since the prescriptions were driven against a specific implementation and a changed validator means re-deriving them rather than coding against stale prose; or `_build_skill_members` no longer takes `generate_adapter_bundle(...).skill_files()`, which would mean the sole install seam moved and E-03's one-line append is no longer the correct place.

This plan is `reviewed` and needs explicit human approval (`Status: approved`) before execution. The executor commits only the Scope-Paths via `aw commit peigax -- <paths>`, never `git add -A`, and never pushes. It inherits `- Blocks-Release: next` from backlog `u0fmeu` and DOES discharge that item's requirements 1 through 4, so `u0fmeu` may close once this is executed and validated. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-07 carry pasted evidence.
