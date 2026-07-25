# IPD: external / out-of-repo install and native-skills delivery (research + probe SPEC, no build)

- Date: 2026-07-23
- Concern: reduce per-repo footprint and recurring token cost by delivering agent-workflows from outside the repo and/or via host-native portable skills, WHERE hosts actually support it
- Scope: produce (a) a per-host PROBE PROTOCOL + results table that a human/host operator runs to prove, per host and version, whether out-of-repo / `.agents/skills/SKILL.md` content is discovered AND followed; (b) a written DELIVERY SPEC that maps, from that evidence, what may safely live out-of-repo vs what must stay in-repo, respecting discovery, versioning, and the IPD-01 ownership model; and (c) an upload-ready external-research PROMPT (per the AGENTS.md prompt-authoring rules) to gather the per-host evidence. This IPD produces DOCUMENTS ONLY - no product code. Any actual build (skills tier, home-dir install, external pointer) is a SEPARATE later IPD, gated on the probe results. DEPENDS ON / coordinates with IPD 01 (manifest) and IPD 06 (interactive-questions trigger); it does not depend on 06 being executed first.
- Status: approved
- Set: install-safety-and-ownership
- Order: 5
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-07-23, human ("approved go.") after /plan-review (APPROVE WITH REVISIONS APPLIED; E1-E5, PR-001/PR-002). Document-only; executing the spec + probe protocol + external-research prompt.

## Workflow history

- 2026-07-23 created as a draft stub (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's original "Item 2" (workflows in ~/.local/agent-workflows so repos are not polluted), reframed after the two research docs as research/spec-first. Preliminary.
- 2026-07-23 fleshed out to a full research/spec IPD (opencode its_direct/pt3-claude-opus-4.8-1m-us): grounded in a fresh read of the current code. Maintainer decisions at authoring: Q1 this IPD produces a research/probe SPEC ONLY (no build; any delivery build is a later IPD gated on probe results); Q2 also produce an upload-ready external-research PROMPT staged under `.agents/prompts/`; Q3 the spec defines a reproducible probe PROTOCOL + results table that human/host operators run - the IPD is "executed" when the spec + protocol + prompt exist and are internally consistent, NOT when every host has been probed (that is ongoing operator work). Verified from code: the packaged out-of-repo source exists (`packaged_source_root` `_compat.py:25`), but discovery/execution assume in-repo copies (shim body `engine.py:533`, pointer prose `engine.py:601-617`, `read_installed_version` reads `.agents/workflows/VERSION` `engine.py:3896-3904`, drift/stale checks assert the in-repo `Read and execute @.agents/workflows/` line `engine.py:2321-2358`); there is NO home-dir/global content location (config stores repo locations only, `config.py:43-57`); `.agents/skills/`/`SKILL.md` is discussed in the research but implemented nowhere.
- 2026-07-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; findings E1-E5 + PR-001/PR-002. Verified every cited code reference against current code (shim body `engine.py:533`, pointer prose `:601`, `read_installed_version` reads `.agents/workflows/VERSION` `:3896-3904`, `packaged_source_root` `_compat.py:25`, `config_dir`/`config_path` `config.py:43/54`) and confirmed the target dirs (`.agents/docs/specs/`, `.agents/prompts/pending/`) and both research docs exist at the cited paths; the IPD is document-only and feasible. Applied: pinned that the spec doc and the research prompt must follow the repo `YYYYMMDD-HHMM-NN-<slug>` naming convention (a real gotcha - the plan-name conformance test enforces it for plans; keep specs/prompts consistent). Confirmed the validation correctly asserts documents-only + no test regression. Author was also reviewer, so claims were verified from code. No open questions remain (Q1/Q2/Q3 + skills-classification resolved); no unfixed BLOCKER/HIGH; the sole discipline this IPD must hold - do NOT build on the unproven per-host assumption - is its explicit core. Readiness: GO - PENDING HUMAN APPROVAL. Status: to-review -> reviewed.

## Goal

Decide, from EVIDENCE rather than assumption, how much of agent-workflows can live OUTSIDE a given repo (the already-packaged data path, a home-dir location, or host-native `.agents/skills/<name>/SKILL.md`) and still be discovered AND followed by each host, then SPEC a delivery model that minimizes per-repo footprint without breaking discovery, versioning, or the ownership model. Produce three durable documents: a per-host probe protocol + results table, a delivery spec keyed to the probe outcomes, and an upload-ready external-research prompt to gather the evidence. Build nothing until the load-bearing "resolve-and-follow" assumption is verified per host.

Why it matters: the maintainer does not want every repo to carry (and pay the footprint for) the full `.agents/workflows/` tree. The research says the HOST (not the model) decides discovery, that Codex/OpenCode/Copilot now natively discover `.agents/skills/SKILL.md` while other `.agents/` content is not auto-understood, and that a passive out-of-repo pointer may not be followed whereas an action-bound trigger is more reliable. Building an external-delivery model on an unproven per-host assumption would silently fail on some hosts and break discovery/versioning/ownership. So the honest first step is a probe + spec, not a build.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| E1 | HIGH | n/a (spec) | maintainer | unproven assumption | Whether a host RESOLVES and FOLLOWS out-of-repo / `SKILL.md` content is per-host, per-version, and unproven; it cannot be determined from this repo. A build on this assumption could silently fail. So the deliverable must be a probe + spec, not code. | research `20260722-2241-01:11,56-72`; `20260722-2317-01:10-38` |
| E2 | MEDIUM | n/a (spec) | maintainer | in-repo coupling | Every discovery/execution path assumes an in-repo copy: the shim body `Read and execute @.agents/workflows/...` (`engine.py:533`), the AGENTS pointer prose (`engine.py:601-617`), `read_installed_version` reading `.agents/workflows/VERSION` (`engine.py:3896-3904`), and the stale/drift check asserting the in-repo line (`engine.py:2321-2358`). The spec must enumerate each as a "must-still-work-or-be-adapted" constraint for any future external delivery. | `engine.py:533,601-617,2321-2358,3896-3904` |
| E3 | MEDIUM | n/a (spec) | adopter/security | home-dir consent | There is NO home-dir/global content location today (config stores repo locations only, `config.py:43-57`), and the research flags that a repo installer must NOT mutate a user's global agent config without clear consent. The spec must treat a home-dir tier as consent-gated and out of scope for auto-install. | `config.py:43-101`; research `20260722-2241-01` user-scope caveats |
| E4 | MEDIUM | n/a (spec) | maintainer | skills reality | `.agents/skills/<name>/SKILL.md` is a portable path some hosts natively discover, but it is implemented NOWHERE in the toolkit today, and not every `.md` workflow is a true "skill" (some are manual workflows / assessors / agents). The spec must classify which workflows are skill-eligible and keep a universal in-repo fallback. | grep: no `.agents/skills`/`SKILL.md` in code/tests; research `20260722-2317-01:602-610` |
| E5 | LOW | n/a (spec) | maintainer | ownership continuity | Any external artifact must remain identifiable, versioned, and removable via the IPD-01 manifest (which is path-parameterized and git-independent, so it can record a non-in-repo path). The spec must state this ownership-continuity requirement for the future build. | `manifest.py` (path-parameterized `save`/`load`); IPD 01 |

## Proposed changes (ordered, validatable; DOCUMENTS ONLY)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | E1,E4 | Write the DELIVERY-TIER SPEC: define the candidate delivery tiers (T0 in-repo, current/fallback; T1 packaged data path already shipped; T2 host-native `.agents/skills/<name>/SKILL.md`; T3 home-dir/global, consent-gated) and, for each, the discovery mechanism, the resolve-and-follow requirement, and the decision criteria for adopting it. Classify which existing workflows are skill-eligible vs manual/assessor/agent (do NOT mechanically convert every `.md`). State the universal in-repo fallback as always-present. | a new spec doc under `.agents/docs/specs/` (`YYYYMMDD-HHMM-NN-external-delivery-and-skills.spec.md`) | Low | tiers + per-tier criteria present; skill-eligibility classification present; fallback stated; no em/en dashes |
| 2 | E1 | Write the per-host PROBE PROTOCOL + results table: an exact, reproducible test a human/host operator runs per host (OpenCode, Claude Code, Codex, GitHub/VS Code Copilot, Cursor, Antigravity, Gemini) and version: fixtures to place (an out-of-repo pointer; a `.agents/skills/probe/SKILL.md`), the resolve-and-follow check (did the host load AND act on it?), and a results table (host, version, tier, resolved?, followed?, notes, date). The protocol yields evidence; it is not run by this IPD. | the same spec doc (a "Probe protocol" section) + a results-table template | Low | protocol is concrete + reproducible; results table has the columns above; states operator-run, not IPD-run |
| 3 | E2,E3,E5 | Write the CONSTRAINTS + ownership section: enumerate every in-repo assumption (E2) any external delivery must preserve or adapt (shim body, pointer, VERSION, drift), the home-dir consent gate (E3), and the manifest ownership-continuity requirement (E5). Explicitly SCOPE OUT the build. | the spec doc (a "Constraints and non-goals" section) | Low | each E2 assumption listed; consent gate stated; ownership continuity stated; build explicitly deferred |
| 4 | E1 | Author the upload-ready EXTERNAL-RESEARCH PROMPT (per AGENTS.md "writing prompts for another AI": prompt only, self-contained, instructs a downloadable `.md` result) that tasks an external AI (with host/web access) to gather the per-host resolve-and-follow + skills-discovery evidence the spec needs, and stage it under `.agents/prompts/pending/`. | a new prompt under `.agents/prompts/pending/` (`YYYYMMDD-HHMM-NN-external-delivery-host-probe.research-prompt.md`) | Low | prompt is self-contained, addressed to the target AI, contains NO instructions to the user, asks for a downloadable `.md`; no em/en dashes |
| 5 | all | Docs/decision sync: a DECISIONS entry (pin at execution) recording the research/spec-first decision (tiers, probe-before-build gate, home-dir consent, skills classification, ownership continuity) and that the build is a separate future IPD gated on probe results; CHANGELOG note (a spec/roadmap artifact, not a user-facing feature). Cross-reference research `20260722-2241-01` and `20260722-2317-01` and IPD 01/06. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| Building any out-of-repo / skills / home-dir delivery | Medium-High | functionality / reliability | The resolve-and-follow assumption is unproven per host (E1); building first risks silent failure. Build is gated on the probe results. | A separate per-tier build IPD after the probe evidence exists. |
| Running the per-host probes | n/a | operator work | Requires the actual host apps, which this IPD cannot drive; the spec defines the protocol for a human/host operator to run. | Operator runs the protocol; records results in the results table. |
| Converting workflows to `SKILL.md` | Medium | complexity | Depends on the skill-eligibility classification + T2 probe outcome. | The build IPD, per the classification. |
| Mutating a user's global/home agent config | Medium | security/consent | Consent-gated; never auto-mutated (E3). | Only with an explicit, warned consent flow in a later IPD. |

## Scope check

- Over-scope: none - this IPD produces ONLY the spec + probe protocol/results-table + the external-research prompt + docs. No product code, no delivery build.
- Under-scope: the spec MUST be evidence-first and MUST NOT recommend building on an unproven per-host assumption (E1); MUST enumerate the in-repo assumptions any external delivery must preserve/adapt (E2); MUST treat a home-dir tier as consent-gated (E3); MUST classify skill-eligibility rather than convert everything (E4); MUST require manifest ownership continuity for external artifacts (E5); MUST keep a universal in-repo fallback; the prompt MUST be upload-ready and self-contained per AGENTS.md.

## Required tests / validation

- This IPD ships DOCUMENTS, not code, so there is no pytest delta. Validation is:
  - The spec doc exists under `.agents/docs/specs/`, named per the repo convention `YYYYMMDD-HHMM-NN-<slug>.md` (research/specs docs follow the same date-prefixed convention as plans/research; use the creating machine's local date-time), contains the tiers (T0-T3) + per-tier criteria, the probe protocol + results-table template, the constraints/ownership section, and an explicit build-deferral.
  - The external-research prompt exists under `.agents/prompts/pending/`, named per the same `YYYYMMDD-HHMM-NN-<slug>` convention, is self-contained and addressed to the target AI (NO user-facing instructions inside), and asks for a downloadable `.md` result (AGENTS.md rules).
  - Internal consistency: every in-repo assumption in E2 appears in the constraints section; every tier has decision criteria; the prompt asks for exactly the evidence the probe protocol needs.
  - Run the full suite `python -m pytest -q` to confirm NO regression (documents only; expect the prior green count unchanged) and paste ACTUAL output. `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- DECISIONS (research/spec-first external-delivery decision + probe-before-build gate), CHANGELOG (spec artifact note), the new spec doc, and the staged research prompt. Cross-reference research `20260722-2241-01` / `20260722-2317-01` and IPD 01/06.

## Open questions

- OQ-Q1 (shape): RESOLVED (maintainer, authoring). Research/probe SPEC only; the delivery build is a separate later IPD gated on probe results.
- OQ-Q2 (external prompt): RESOLVED (maintainer, authoring). Produce an upload-ready external-research prompt staged under `.agents/prompts/`.
- OQ-Q3 (probe execution): RESOLVED (maintainer, authoring). The spec defines a reproducible probe protocol + results table that human/host operators run; the IPD is "executed" when the spec + protocol + prompt exist and are internally consistent, not when every host has been probed.
- OQ-skills-classification: which specific workflows are skill-eligible is itself part of Step 1's classification and will be refined by the T2 probe outcome; not a blocker for the spec.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. It produces DOCUMENTS ONLY; it does NOT build external delivery. Any build IPD that follows MUST pass /plan-review + explicit human approval and MUST NOT build out-of-repo delivery before the per-host resolve-and-follow assumption is verified.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Run the full suite to confirm no regression and paste the ACTUAL output. No em or en dashes in authored Markdown. The research prompt MUST follow the AGENTS.md "writing prompts for another AI" rules (prompt only, self-contained, downloadable `.md` result). STOP and report if execution exceeds this plan's scope (in particular, do NOT start building external delivery). Never create or push a tag / Release / PyPI upload.

CHECKPOINTED EXECUTION: (1) the delivery-tier spec; (2) the probe protocol + results table (same doc); (3) the constraints/ownership section (same doc); (4) the external-research prompt under `.agents/prompts/pending/`; (5) DECISIONS + CHANGELOG. Run the full suite after the doc changes to confirm no regression; pause and report if scope grows toward a build.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute the document steps, validate internal consistency + no test regression; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. The per-host probes and any delivery build are separate follow-on work.
