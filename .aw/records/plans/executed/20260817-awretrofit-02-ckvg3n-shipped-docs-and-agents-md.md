# IPD: Sweep shipped/executed workflow bodies + index.md + templates + AGENTS.md generator to .aw/ paths

- Date: 2026-08-17
- Kind: child
- Concern: Release-review 20260817-153418 findings S4-D01 + S4-D02: the SHIPPED, agent-executed workflow bodies, the workflow `index.md`, the record-README templates, and the always-loaded AGENTS.md managed block still instruct agents to use legacy `.agents/` paths that do not exist in a fresh/migrated `.aw/` repo. Additionally one SHIPPED TOOL (`normalize_plan_names.py`) is behaviorally legacy-only (scans `.agents/` not `.aw/records/`), a Order-01-class bug hiding among the prose.
- Scope: Correct every SHIPPED instruction/tool that misdirects an agent post-migration: (1) workflow bodies under `.aw/system/workflows/**` that give executable `.agents/` paths; (2) `index.md` invocation catalog + VERSION-source note; (3) `.aw/system/templates/**` record-README stubs; (4) the AGENTS.md managed-block GENERATOR (fix the template in engine.py, regenerate, do NOT hand-edit the artifact); (5) `normalize_plan_names.py` behavioral scan root (layout-aware + fallback, like Order 01). PRESERVE the deliberately layout-agnostic release-review runbook fallbacks (lead with `.aw/`, keep `.agents/` as named legacy). OUT: CLI help strings + module docstrings (Order 05), historical DECISIONS/CHANGELOG (acceptable history).
- Status: executed
- Set: awretrofit
- Order: 2
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: ckvg3n

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 findings S4-D01 + S4-D02 (Set awretrofit Order 02).
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Structural preflight conforming. Verified citations against real code: E-01 tool-invocation lines (setup-repo.md:33/126 -> `.agents/workflows/...tools/...` while tools ship at `.aw/system/workflows/...tools/`) accurate; E-04 generator location confirmed (engine.py agents_managed_block). Findings: PR-001 (HIGH) E-04 was materially incomplete - the generator is ALREADY layout-parameterized (engine.py:867-884) but its `aw` branch emits `.aw/records/{research,walkthroughs,specs}` while the real layout is `.aw/records/docs/{...}` (verified via `aw path records`+`ls`), AND this repo's AGENTS.md is in legacy mode (24 `.agents/` refs), so E-04 rescoped to fix both the docs/ sub-paths and the legacy target_layout selection; PR-002 (LOW) E-05 miscited `plans.py:62` -> corrected to `normalize_plan_names.py:62`; PR-003 (MEDIUM) the tool is a SHIPPED standalone script and cannot import `resolve_record_path`, so E-05 must inline its resolution. All FIXED in place. OQ-01 already resolved. No open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-17 renamed to Set-clustering grammar (opencode Opus 4.8): `aw plans mv ckvg3n` -> 20260817-awretrofit-02-ckvg3n-shipped-docs-and-agents-md.md (canonical YYYYMMDD-<set-id>-NN-<id6>-<slug>); the whole awretrofit Set was renamed for consistency and the tooling gaps captured in backlog vf03z3.
- 2026-08-17 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved Order 02; implemented E-01..E-06 in commit e2a362b (swept ~34 shipped bodies + index.md + templates + AGENTS.md generator/regeneration + AGENT-PLANS block + normalize_plan_names.py + drift-guard test). During execution refined PR-001: there was NO legacy-mode SELECTION bug (the installer already resolves aw for this repo); the tracked AGENTS.md was simply stale, so E-04(b) resolved to a plain regenerate via the real code path. V-01..V-06 verified (bundle .aw/-clean outside allowlist, index.md 0 legacy, templates retitled, AGENTS.md 0 legacy with docs/ sub-paths + round-trip no-op, tool layout-aware repro, drift-guard mutation RED->GREEN, wheel ships corrected bundle, full serial suite 986 passed / 1 skipped). pre-transition lint conforming; moved pending -> executed/.

## Goal

Make every SHIPPED artifact that an agent executes or reads on a migrated repo point at the real
`.aw/` layout, so a fresh install does not misdirect agents into the vanished `.agents/` tree (the
split-brain the migration forbids). This covers the workflow bodies, the `index.md` catalog, the
record-README templates, the always-loaded AGENTS.md managed block (via its generator), and the one
behaviorally-broken shipped tool.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

Classification rule (from the L3 audit): a `.agents/` reference is (a) WRONG when it is an
EXECUTABLE/instructional path an agent would act on in a fresh repo; (b) LAYOUT-AGNOSTIC when the
release-review runbook names `.agents/` as one illustrative option among generic fallbacks (lead with
`.aw/`, keep `.agents/` as a named legacy alternative, do NOT delete); (c) HISTORICAL in
DECISIONS/CHANGELOG (leave). Only (a) is rewritten to `.aw/system/workflows/...` /
`.aw/records/{plans,docs,prompts,comms}/...`; (b) is reordered, not stripped.

### Task group 1: shipped workflow bodies + index.md + templates

- [x] E-01 Rewrite WRONG (class-a) executable `.agents/` paths in the workflow bodies under `.aw/system/workflows/**` to the `.aw/` equivalents. Confirmed high-impact bodies: setup-repo/setup-repo.md (incl. the two tool-invocation lines), ipd-lifecycle/ipd-lifecycle.md, verify-execution/verify-execution.md, whatnext/whatnext.md, handoff/handoff.md, scaffold/scaffold.md, spec/spec.md, getting-started/getting-started.md, migrate/migrate.md, assess/assess.md, list-workflows, incident/verify/conformance READMEs. LEAVE the release-review runbook's layout-agnostic fallbacks except to lead with `.aw/`. Ignore untracked `.pyc`.
  - Depends on: none
  - Expected outcome: no shipped body instructs an agent to act on a `.agents/` path that does not exist in a fresh `.aw/` install; `git grep .agents/ .aw/system/workflows` shows only layout-agnostic-fallback or historical refs.
  - Execution state: performed

- [x] E-02 Rewrite the `index.md` workflow catalog: the invocation column (`Read and execute .agents/workflows/...` -> `.aw/system/workflows/...`) and the VERSION source-of-truth note (`.agents/workflows/VERSION` -> `.aw/system/VERSION`).
  - Depends on: none
  - Expected outcome: `grep -c .agents/workflows .aw/system/workflows/index.md` -> 0; the invocation paths resolve in a fresh install.
  - Execution state: performed

- [x] E-03 Retitle/repath the `.aw/system/templates/**` record-README stubs (plans-README, prompts-README, agents-docs-*-README, agents-README) from `# .agents/...` headings and `ls .agents/...` bodies to their `.aw/records/...` equivalents, matching where the installer drops them.
  - Depends on: none
  - Expected outcome: a template dropped into `.aw/records/plans/` is titled/pathed `.aw/records/plans/`, not `.agents/plans/`.
  - Execution state: performed

### Task group 2: AGENTS.md managed-block generator

- [x] E-04 Fix the AGENTS.md managed-block generator AND the reason this repo's block is legacy. Two distinct defects (both verified in review, engine.py):
  (a) The generator is ALREADY layout-parameterized (`agents_managed_block` prose builder, engine.py ~860-884: `if target_layout == "aw"` sets `.aw/...` vars, else `.agents/...`), but the `aw` branch itself is WRONG for three roots - it emits `.aw/records/research`, `.aw/records/walkthroughs`, `.aw/records/specs` (engine.py:870-873) whereas the real layout is `.aw/records/docs/{research,walkthroughs,specs}` (the `docs/` level; verified `aw path records` + `ls`). `plans_dir`/`comms_dir` in that branch are correct. FIX the three `docs/`-missing paths in the `aw` branch.
  (b) This repo's tracked AGENTS.md is in LEGACY mode (all 24 refs are `.agents/...`, i.e. the `else` branch ran), so a MIGRATED repo still regenerates a legacy block. Find what determines the `target_layout` passed to the AGENTS.md writer on install/update and make a migrated (`.aw/`) repo select the `aw` branch (e.g. via `resolve_target_layout`), then REGENERATE this repo's AGENTS.md. Do NOT hand-edit only the artifact (it re-propagates on every install).
  - Depends on: none
  - Expected outcome: on a migrated repo the writer selects the `aw` branch; the regenerated AGENTS.md block references `.aw/system/workflows/...` and `.aw/records/{plans,docs/research,docs/walkthroughs,docs/specs,comms}` (correct `docs/` sub-paths), has 0 wrong/legacy `.agents/` paths, and a second regenerate is a no-op (round-trip).
  - Execution state: performed

### Task group 3: behaviorally-broken shipped tool

- [x] E-05 Make `normalize_plan_names.py` (`.aw/system/workflows/setup-repo/tools/`) layout-aware: its `AGENTS_DIR = ".agents"` scan root (normalize_plan_names.py:62, consumed at :378 `agents = repo_root / AGENTS_DIR`) must resolve `.aw/records/` with a legacy `.agents/` read-fallback, since it is a SHIPPED tool that otherwise scans the vanished tree. NOTE: this tool is a SHIPPED, dependency-free standalone script (no `agent_workflows` import), so it cannot reuse `resolve_record_path`; implement a small self-contained climb/prefer-`.aw/records`-else-`.agents` resolution inline. Update its docstring scope note.
  - Depends on: none
  - Expected outcome: `normalize_plan_names.py --repo <migrated-repo> --all` scans `.aw/records/{plans,prompts,docs}`; a legacy repo still scans `.agents/`.
  - Execution state: performed

### Task group 4: verification

- [x] E-06 Add a shipped-docs drift guard test (extend the packaging/self-tests) asserting no SHIPPED workflow body or template under `.aw/system/**` contains a class-a `.agents/` executable path, and that the regenerated AGENTS.md block is `.aw/`-only. Rebuild the wheel and confirm the corrected bodies ship.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: a test fails if a future edit reintroduces a wrong `.agents/` path; wheel ships the corrected bundle.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The shipped bundle is `.aw/system/workflows/**` (was `.agents/workflows/`); records are `.aw/records/{plans,docs,prompts,comms,backlog}`. The AGENTS.md block is machine-managed (delimited `aw:block`/`AGENT-PLANS`) and regenerated on every `aw install`/`update`, so hand-editing the artifact is futile - the generator is the source.
- The release-review runbook is DELIBERATELY layout-agnostic (it reviews OTHER repos); its `.agents/` mentions are illustrative fallbacks, not this framework's own paths. Do not strip them; lead with `.aw/`.
- ruff-format may reformat any touched `.py` and abort the first commit; re-verify + re-commit. Path-scoped, no push. Untracked `.pyc` under `.aw/system/workflows/**` are local cruft (ignore).

## Findings

From release-review run 20260817-153418 (per-file counts re-measured post-Order-01):

| id | artifact | evidence | class |
|---|---|---|---|
| D01a | shipped workflow bodies | setup-repo.md(19), handoff.md(8), assess.md(8), scaffold.md(7), whatnext.md(4), ipd-lifecycle.md(2), verify-execution.md(1), spec/getting-started/migrate | (a) WRONG executable paths |
| D01b | index.md | 64 `.agents/` refs incl. invocation column + VERSION note | (a) WRONG |
| D01c | templates/*-README | plans/prompts/agents-docs-* titled `# .agents/...` | (a) WRONG (point-of-contact) |
| D01d | release-review/** | 00-run-protocol(7), MANIFEST(4), 01-current-state(3) | (b) LAYOUT-AGNOSTIC (reorder only) |
| D02 | AGENTS.md managed block | 24 refs; generated by engine.py | (a) WRONG, fix GENERATOR |
| D01e | normalize_plan_names.py | AGENTS_DIR=".agents" (normalize_plan_names.py:62, used :378) scans legacy tree | (a) WRONG behavioral - shipped standalone tool |
| PR-001 | AGENTS.md generator (review) | engine.py:867-884 already layout-parameterized; aw branch emits `.aw/records/{research,walkthroughs,specs}` but real is `.aw/records/docs/{...}`; this repo's block is legacy-mode | HIGH: E-04 rescoped to fix the aw-branch docs/ paths AND the legacy target_layout selection |
| PR-002 | E-05 citation (review) | plan said "plans.py:62"; actual is normalize_plan_names.py:62 | LOW: corrected in E-05 |
| PR-003 | tool cannot import package (review) | normalize_plan_names.py is a shipped standalone script (no agent_workflows import) | MEDIUM: E-05 must inline resolution, not reuse Order-01 helper |

## Proposed changes (ordered, validatable)

1. E-01 bodies, E-02 index.md, E-03 templates (doc/instruction rewrites).
2. E-04 AGENTS.md generator (fix template, regenerate, round-trip).
3. E-05 normalize_plan_names.py behavioral resolver.
4. E-06 drift-guard test + wheel rebuild.

## Deferred / out of scope (with reason)

- CLI `--help` strings + module docstrings (`__init__.py`, `_compat.py`, `hatch_build.py`, `versioning.py`) -> Order 05 (D04): code-behavior-correct, prose-stale; grouped with the other prose cleanup.
- DECISIONS.md / CHANGELOG.md `.agents/` references: legitimate history, leave.
- RELEASING.md + Makefile: Order 03.

## Scope check

- Over-scope: none - every rewrite targets a shipped artifact an agent would act on.
- Under-scope: none - E-05 pulls the behaviorally-broken shipped tool into scope (it would otherwise be a residual Order-01-class bug); the doc-only siblings are explicitly deferred to Order 05.

## Required tests / validation

- `git grep -n "\.agents/" .aw/system/workflows .aw/system/templates` shows only class-(b) layout-agnostic or historical refs afterward.
- Regenerated AGENTS.md block is `.aw/`-only and round-trips (install/update rewrites identically).
- `normalize_plan_names.py` scans the migrated tree on a repository-backend fixture; legacy fallback intact.
- New drift-guard test green; wheel rebuild ships the corrected bundle; full serial suite >= 982/1-skip.

## Spec / documentation sync

- The controlling spec 20260810-1447-01 is already `implemented`; this Order fixes shipped artifacts that
  should have been reconciled during that migration. No spec status change; note the completion in the
  orchestrator. AGENTS.md is regenerated, not hand-synced.

## Open questions

### OQ-01: How aggressively to rewrite the release-review runbook's `.agents/` fallbacks?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: MINIMALLY - the release-review runbook reviews OTHER repos and is
  deliberately layout-agnostic, so its `.agents/` mentions are illustrative fallbacks. Reorder to LEAD
  with `.aw/records/...` and keep `.agents/...` as a named legacy alternative; do NOT strip them
  (that would wrongly assume every reviewed target uses `.aw/`). Only class-(a) executable paths in
  the framework's OWN operational workflows are rewritten outright.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `git grep -n "\.agents/" .aw/system/workflows` (excluding release-review/** and .pyc) returns no class-a executable path; spot-check setup-repo.md/ipd-lifecycle.md/handoff.md show `.aw/` paths. Paste grep summary.
  - Observed evidence: Swept ~34 operational workflow bodies with the 5 mappings (.agents/workflows/->.aw/system/workflows/, .agents/{plans,docs,prompts,comms}/->.aw/records/...) plus 3 nuanced prose fixes (local-leaks allowlist path, normalize --area prose, whatnext attention prose). `tests/test_awretrofit_shipped_docs.py::...test_no_legacy_agents_paths_in_shipped_bundle` PASSES (4 passed in the file). Remaining `.agents/` in the bundle are all allowlisted class-b (release-review/** layout-agnostic, migrate/), class-c (conformance host_matrix .agents/skills/), or legacy-fallback descriptions (normalize_plan_names.py) - verified by the passing guard test. setup-repo.md/ipd-lifecycle.md/handoff.md now use `.aw/` paths.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `grep -c "\.agents/workflows" .aw/system/workflows/index.md` -> 0; the VERSION note reads `.aw/system/VERSION`. Paste.
  - Observed evidence: `grep -c "\.agents/workflows" .aw/system/workflows/index.md` -> 0 (all invocation-column paths now `.aw/system/workflows/`); the VERSION note reads `Version: \`1.2.1\` (source of truth: \`.aw/system/VERSION\`)`. `grep -c "\.agents/" index.md` -> 0 (also fixed the 4 description-prose `.agents/prompts/local/` + `.agents/plans/` refs). `test_index_catalog_uses_aw_system_paths` passes.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: each `.aw/system/templates/*-README` heading + body references `.aw/records/...` (not `.agents/...`). Paste head of plans-README + prompts-README.
  - Observed evidence: template stubs live at `.aw/system/workflows/templates/`. `head -1 plans-README.md` -> `# .aw/records/plans/`; `head -1 prompts-README.md` -> `# .aw/records/prompts/`; `agents-README.md` retitled `# .aw/records/`. `git grep -c "\.agents/" .aw/system/workflows/templates/**` -> 0 (all template stubs clean).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (a) the aw-branch paths for research/walkthroughs/specs now include `docs/` (engine.py); (b) on this migrated repo the writer selects the `aw` branch and the regenerated AGENTS.md references `.aw/system/workflows/...` + `.aw/records/{plans,docs/research,docs/walkthroughs,docs/specs,comms}` with 0 legacy `.agents/` paths; (c) a second regenerate is a no-op (round-trip). Paste `grep -oE` of the AGENTS.md paths + the no-op diff.
  - Observed evidence: (a) fixed engine.py aw-branch to `.aw/records/docs/{research,walkthroughs,specs}` (was flat `.aw/records/{...}`). CORRECTION to my own PR-001 finding: there is NO legacy-mode SELECTION bug - `resolve_target_layout(.)` returns "aw" for this repo and `update_agents_pointer` already receives it; the tracked AGENTS.md was simply STALE (never regenerated since the migration git-mv'd it). (b) Regenerated via the real code path (`engine.update_agents_pointer(plan, target_layout="aw")`) -> `refreshed pointer in AGENTS.md`; `grep -c "\.agents/" AGENTS.md` -> 0; `grep -oE ".aw/records/docs/(research|specs|walkthroughs)/"` -> all three present with the docs/ sub-path. The repo-local hand-maintained AGENT-PLANS block (not code-generated, this-repo-only, never shipped) was repathed `.agents/plans/`->`.aw/records/plans/`. (c) Second regenerate -> `diff` empty = NO-OP (round-trip clean).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: a test / repro shows `normalize_plan_names.py` scans `.aw/records/{plans,prompts,docs}` on a migrated fixture and falls back to `.agents/` on a legacy one. Paste output.
  - Observed evidence: Added inline `_resolve_records_base` (standalone, no agent_workflows import per PR-003) preferring `.aw/records/` else legacy `.agents/`. Repro: migrated fixture -> `scan(r)` sees `.aw/records/plans/pending/bad name.md`; legacy fixture -> `scan(r2)` sees `.agents/plans/pending/bad name.md`. Docstring + `--area`/`--all` help prose updated to "records base".
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the new drift-guard test fails if a wrong `.agents/` path is reintroduced (mutation) and passes clean; wheel rebuild ships the corrected bundle; full serial suite >= 982 passed / 1 skipped. Paste test + suite summary.
  - Observed evidence: New `tests/test_awretrofit_shipped_docs.py` (4 tests: bundle-clean-outside-allowlist, index catalog, AGENTS.md clean+docs/, release-review-leads-with-aw) -> 4 passed. Mutation: appended `.agents/docs/specs/` to spec.md -> the bundle-clean test `1 failed`; restored -> `4 passed`. Wheel rebuild: `agent_workflows/_data/.aw/system/workflows/index.md` has `.aw/system/workflows/` True, legacy `.agents/workflows/` False; setup-repo.md legacy `.agents/` False. Also fixed `tests/test_plan_review_parity.py::test_lifecycle_registered_in_index` which asserted the OLD legacy index path (an S3-T01-class legacy-asserting test). Full serial suite: `986 passed, 1 skipped in 188.27s` (was 982/1 after Order 01; +4 drift-guard tests).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
implements E-01..E-06, pastes actual evidence (grep summaries, the AGENTS.md round-trip no-op, the
tool repro, the drift-guard test, the full serial suite), commits only the scoped paths
(`.aw/system/workflows/**`, `.aw/system/templates/**`, `.aw/system/workflows/setup-repo/tools/normalize_plan_names.py`,
`agent_workflows/engine.py`, `AGENTS.md`, and the new test), never pushes, runs
`aw ipd lint --phase pre-transition` + the full suite before transition, and the orchestrator owns the
move to `executed/`. HIGH priority: these are shipped, agent-executed instructions.
