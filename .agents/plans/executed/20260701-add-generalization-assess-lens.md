# IPD: Add an `assess-generalization` lens (productization / extensibility / configurability)

- Date: 2026-07-01
- Concern: framework capability addition (a new `assess-<concern>` lens)
- Scope: add one lens to the `assess-*` family and wire it in. Touches
  `.agents/workflows/assess/lenses/`, `.agents/workflows/index.md`, the generated
  shims, `README.md`, `ARCHITECTURE.md`, `DECISIONS.md`. Source material: the review
  prompt currently at `tmp/repository_generalization_extensibility_configurability_review_prompt.md`
  (git-ignored scratch; to be discarded after distillation, per maintainer).
- Status: EXECUTED (approved by maintainer 2026-07-01; slug "generalization" confirmed; all steps applied and validated)
- Author: OpenCode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Add a single-concern assessment capability for **generalization / productization**:
reviewing a repository to make it more generic, extensible, configurable, reusable,
administrable, and maintainable across organizations, tenants, and deployment
environments - without over-engineering. This concern is currently unserved by the
26 existing lenses (the `architecture` lens touches "configurability over hardcoding"
and "extensibility" but centers on structural soundness, not productization for reuse
across orgs/tenants/deployments). The source prompt is a strong, detailed statement of
this concern; the goal is to adopt its *substance* in the repo's own idiom - a thin
lens on the shared `assess` harness - rather than importing 721 lines of prose that
would duplicate what the harness already owns.

## Project conventions discovered (Step 0)

- Adding a concern is designed to be cheap and single-sourced: "a new lens file plus a
  manifest row" (`ARCHITECTURE.md` "Assessment workflows" + "Capability layout"). The
  shared harness `.agents/workflows/assess/assess.md` owns the protocol (discover
  conventions, eight personas, Fix Bar as "what to propose", write an IPD, never
  execute); each `lenses/<concern>.md` supplies only focus, lead personas, and rubric.
- Lens file shape (verified against `architecture.md`, `api-design.md`, and peers):
  `# Lens: <name>`, `## Lead personas`, `## Rubric` (bulleted), `## IPD emphasis`.
  Lengths run ~30-40 lines. No lens restates personas, output format, or the IPD
  template - those live in the harness (P8).
- Manifest format (`.agents/workflows/index.md`): a stable-column table
  `command | body | lens | description`; the installer reads it to generate per-tool
  shims. Shared-body commands set the `lens` column; the installer injects the lens
  into each generated shim (`install-workflows.py` `shim_body`, lines 251-286).
- Shim generation is automatic and must not be hand-edited: run
  `install-workflows.py` to (re)generate `.opencode/commands/` and `.claude/commands/`.
- Guiding principles in force here: P6 (KISS / anti-bloat), P7 (solve the general
  case, project-agnostic), P8 (single source of truth), P2 (honest docs). Authoring
  convention: no em dashes in authored Markdown (confirmed 2026-06-30).
- Contributor doc-sync checklist now exists (`CONTRIBUTING.md`); this plan follows it
  (lens + manifest row + installer regen + README/ARCHITECTURE sync + DECISIONS entry).

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Persona = the
reviewer perspective that surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| G1 | Medium | Low | Stakeholder / Architect | Missing capability (under-scope) | The `assess-*` family has no lens for generalization/productization (reuse across orgs/tenants/deployments, config architecture, admin/operability, de-hardcoding org-specific assumptions). The source prompt shows this is a coherent, valuable single concern. Adding it fits the family's purpose and P7 (solve the general case). | `assess/lenses/` (26 files, none productization-centric); source prompt sections 1-8 |
| G2 | Medium | Low | Maintainer (P8/P6) | Adopt-as-lens, not wholesale | Importing the 721-line prompt as-is would duplicate the harness's personas, output format, method, and scope rules (P8 violation) and add bloat (P6). The prompt's unique value is its *rubric and concern framing*, which distills to ~40 lines in the lens idiom. | source prompt lines 390-721 (Method/Output/Constraints) overlap `assess.md` + `templates/ipd.md` |
| G3 | Low | Low | Architect | Overlap boundary with `architecture` lens must be stated | Without a note, users will not know whether to run `assess-architecture` or `assess-generalization`. They are distinct (structure/soundness vs. productization/reuse) but adjacent; the lens and docs should cross-reference to avoid confusion. | `assess/lenses/architecture.md:20-23` (extensibility/config bullets) |
| G4 | Low | Low | Operator | Source prompt lives in ignored scratch (informational) | The source is in `tmp/` (git-ignored). Maintainer decided the distilled lens supersedes it; the `tmp/` copy is simply left to be discarded (not moved into `prompts/`). This produces no repo change and needs no step - it is recorded only so the executor does NOT create a `tmp/`-referencing artifact or try to "remove" an untracked file as if it were a tracked deletion. | `.gitignore` `tmp/`; `tmp/repository_generalization_...md` (untracked) |

## Proposed changes (ordered, validatable)

Fix by default; all Low Remediation Risk (additive, doc/instruction-only, reversible;
no application code). No em dashes in any authored file.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | G1, G2, G3 | Author `.agents/workflows/assess/lenses/generalization.md` in the standard lens shape (~35-45 lines). `## Lead personas`: productization reviewer / software architect (primary), DevOps/operator, stakeholder (broader-deployment goals), and the novice administrator (clean handoff). `## Rubric` (distilled from the source prompt, ~8 bullets): (a) abstraction candidates - logic/services coupled to one org/tenant/vendor/workflow, with the appropriate pattern (interface/adapter/provider/strategy/policy/plugin/config-schema) and a stated reuse benefit; (b) hard-coded values that should become configuration (names, domains, endpoints, paths, roles, thresholds, fiscal/tz/locale/currency, limits, branding) and the right mechanism (env var / config file / typed setting / tenant / org / admin-editable / secret / documented default / remain concrete); (c) class/service/module extensibility seams and separation of concerns (business logic out of routes/views; injectable deps; adapters for integrations); (d) configuration architecture (required vs optional vs secret vs tenant vs admin vs feature-flag; startup validation; `.env.example`; safe defaults; no env-specific behavior baked in source); (e) administration & operability for clean handoff (setup/bootstrap, migrations safety, seed/demo data separated from prod, health/readiness, structured logs, backup/restore & upgrade docs, admin CLI); (f) organization/deployment-specific assumptions and multi-tenant readiness (decide: remain concrete / rename generic / configurable / tenant-scoped / move to docs / move to seed-demo / extension point); (g) security-as-administrable (centralized default-deny authz, no hard-coded superusers/org-email gating, secrets in a manager, safe prod-vs-dev defaults) - cross-reference the `security` lens; (h) KISS counterweight - flag over-generalization/speculative config as strongly as missing seams. `## IPD emphasis`: apply the "concrete / config / admin / tenant / feature-flag / interface / documented-default / defer" spectrum onto the Fix Bar's Complexity axis; productization refactors can be high Remediation Risk (broad blast radius) so prefer staged changes and route large redesigns to open questions with a sketch, not a big-bang rewrite; do NOT restate personas/output/IPD-template (harness owns them). Add a one-line cross-reference distinguishing this lens from `architecture` (G3). | `.agents/workflows/assess/lenses/generalization.md` (new) | Low | File exists, follows the 4-section lens shape, length comparable to peers (< ~50 lines), references the harness rather than duplicating it, and names the `architecture`/`security` cross-references. |
| 2 | G1 | Add one manifest row to `.agents/workflows/index.md` (inside the WORKFLOWS-MANIFEST block, alongside the other `assess-*` rows): `assess-generalization | .agents/workflows/assess/assess.md | .agents/workflows/assess/lenses/generalization.md | Assess generalization/extensibility/configurability (productization for reuse across orgs/tenants/deployments) and propose an IPD.` Keep column order stable. | `.agents/workflows/index.md` | Low | Row present with correct 4 columns and lens path; the "assess-* family" prose section still reads correctly (optionally mention the new concern in the family description). |
| 3 | G1 | Regenerate the per-tool shims by running the installer against this repo: run `--dry-run` first, then `python3 .agents/workflows/install-workflows.py --repo .`. This creates `/assess-generalization` shims in `.opencode/commands/` and `.claude/commands/`. Do NOT hand-edit shims. **Verified during plan-review (2026-07-01):** a self-install here is idempotent - the installer reports all existing framework files as "already current" and skips them (this installer does NOT refuse the source root, unlike the former release-review installer, and its `is_self` guard at `install-workflows.py:682` only suppresses the legacy-migration step). So a self-install adds exactly the 2 new shims and restages nothing else. It stages with git (`git add`) but does not commit. | `.opencode/commands/assess-generalization.md`, `.claude/commands/assess-generalization.md` (generated) | Low | Both shim files exist; each references `@.agents/workflows/assess/assess.md` and applies `@.agents/workflows/assess/lenses/generalization.md`; `git diff --stat` shows exactly two new shim files and no churn to the other 26x2 existing shims, `AGENTS.md`, or pruned files. |
| 4 | G1, G3 | Sync docs (P8-safe, one-line additions, no duplication): add `generalization` to the engineering-concern enumeration in `README.md:22-23` (the parenthesized list that ends "...compliance, memory-resources"), and mention it in the assess-family description in `ARCHITECTURE.md` (around line 195, the "family includes" sentence). Note once that it is the productization sibling of the `architecture` lens (G3 boundary). Verified no doc hardcodes a lens *count* that would drift (checked during plan-review), so only the by-name enumerations need updating. | `README.md`, `ARCHITECTURE.md` | Low | Both docs name the concern in the right list; the `architecture`-vs-`generalization` boundary is stated once; no rubric/persona content is duplicated from the lens; wording matches existing style. |
| 5 | G2 | Add a dated `DECISIONS.md` entry (next Dxx) recording the *design decision*: adopt the generalization/productization review as a **lens on the shared `assess` harness**, not a standalone multi-hundred-line workflow; rationale (P8 reuse of harness, P6 anti-bloat, P7 general case); and the deliberate boundary with the `architecture` lens (productization/reuse vs. structural soundness). Note in passing that the source was an external review prompt distilled into the lens (do not frame "deleting a git-ignored scratch file" as a repo action - it leaves no artifact and needs no decision record). | `DECISIONS.md` | Low | New dated entry present with Decision / Why / Trade-off; consistent with existing D-entry style; does not alter earlier entries. |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | No finding is deferred on Remediation-Risk grounds. All steps are Low risk and proposed. | - |

## Scope check

- Over-scope (untraceable to a need; propose removal/deferral): explicitly avoided
  importing the source prompt's Method / Output Format / Constraints / persona sections
  (the harness owns them). Avoided creating a standalone workflow directory (the family
  is lens-based by design). Avoided a new top-level concept.
- Under-scope (needed capability missing; propose adding): the generalization/
  productization concern itself (G1) - a real gap in the `assess-*` family, proposed
  for addition as a single lens.

## Required tests / validation

Instruction/doc-only change; validation is verification, not automated tests:

1. Installer dry-run: `python3 .agents/workflows/install-workflows.py --repo . --dry-run`
   lists the new `/assess-generalization` shim and no unexpected churn.
2. After Step 3, confirm both shim files exist and their bodies reference the harness
   body and the generalization lens (matching the format other `assess-*` shims use).
3. `git diff --stat` shows only: the new lens, the manifest row, the two generated
   shims, README, ARCHITECTURE, DECISIONS. No application code or unrelated shims.
4. Lens quality check: 4-section shape, length comparable to peers, no duplicated
   harness content (P8), `architecture`/`security` cross-references present.
5. Authoring style: no em dashes in any changed/added Markdown (convention in force).
6. Smoke test the capability: run `/assess-generalization` (or "read and execute
   assess.md applying lenses/generalization.md") against a small scope and confirm it
   produces an IPD in `.agents/plans/pending/` without changing code. (Optional but
   recommended before relying on it.)

## Spec / documentation sync

The lens + manifest row + regenerated shims + README/ARCHITECTURE mentions + DECISIONS
entry together constitute the doc sync (this is exactly the `CONTRIBUTING.md` doc-sync
checklist). No user-visible application behavior changes outside the framework itself.

## Open questions

1. **Concern name (HARD GATE - resolve before executing Steps 1-5).** `generalization`
   is proposed as the command/lens slug (`/assess-generalization`). Alternatives:
   `productization`, `configurability`, `reusability`. `generalization` aligns with
   GUIDING_PRINCIPLES P7 ("Solve the general case") and the source prompt's title. The
   slug is baked into the lens filename, the manifest `command`/`lens` columns, both
   generated shims, and the docs; it becomes a **public command name**, so renaming
   after release is a breaking change (an old `/assess-<slug>` disappears). Confirm the
   slug first; do not execute Steps 1-5 until it is fixed.
2. **Family bump only, or also mention in the assess honesty/notes prose?** The `index.md`
   "assess-* family" section groups concerns (engineering / cybersecurity / compliance);
   generalization fits the engineering group. Confirm no special note is needed.
3. **Smoke test target:** if you want validation step 6 run before merge, name a target
   (this repo itself, or skip - it is a framework/prompt repo with limited "hard-coded
   org" surface, so a smoke run may produce few findings; that is fine as a wiring test).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. **Prerequisite:** Open Question 1 (the slug) must be
resolved before any step runs, because the slug is baked into filenames, the manifest,
the generated shims, and the docs. Recommended next steps:

1. Review this IPD (plan-review has been run and applied; see the edits log).
2. Confirm the slug (Open Question 1), then execute the ordered changes and run the
   validation.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention
   (this project uses `.agents/plans/done/`).
