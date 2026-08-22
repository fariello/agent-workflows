# IPD: Generated Skills Host Adapters and Agy Fresh Verifier

- Date: 2026-08-21
- Kind: child
- Concern: Generate the thinnest native host wrappers from the canonical source without duplicating semantics.
- Scope: Generated Agent Skills + per-host adapter metadata + the agy fresh-session verifier mode + generated-parity/discovery/permission/security tests. Consumes Order 10's registry; marks nothing supported without evidence.
- Status: reviewed
- Set: awoptimize
- Order: 11
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: bmd1ur

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-05 E-04..E-08 into 5 right-sized E-items (generated skills, guarded per-host adapters, skill-authority restriction, agy fresh-verifier, security/parity tests); carries the host-mapping table.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE; GO - PENDING HUMAN APPROVAL. Deps on Order 10 (registry) + Order 08 (verifier packet) are justified (it consumes both). Sound discipline: advertises nothing the Order-10 registry has not marked non-unverified; authoritative behavior never lives only in SKILL.md; agy fresh-verifier replaces same-session audit. V-01..V-05 map 1:1 with falsifiable evidence incl. security (loopback/auth, external-path, redaction). No findings. OQ-01 resolved.
- 2026-08-21 /plan-review re-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Deeper pass found two the first missed: PR-001 (LOW) the generator module was unnamed - FIXED by naming `agent_workflows/host_adapters.py` in E-02 + the scope fence; PR-002 (MEDIUM, rubric C) the repo ALREADY has a host-shim generator (`engine.py` generate_shim_members/shim_body/COMMAND_SHIM_DIRS) and this Order must EXTEND it, not fork a parallel adapter path - FIXED by mandating reuse in E-02, the Findings, and the scope fence (which now names `engine.py`). Re-lint conforming.

## Goal

Generate the smallest native wrapper each host needs - Agent Skills packages + per-host adapter
metadata - from the canonical source, keeping the workflow semantics, state machine, evidence
contract, and verification portable, and marking nothing `supported` without Order-10 evidence. Also
replace the same-session agy audit with a fresh-session verifier mode. This Order consumes the
Order-10 registry; it does not define the registry or run live probes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: skills and adapters

- [ ] E-01 Generate portable Agent Skills packages (`SKILL.md` router with an exact trigger description, the canonical semantic digest, an explicit-invocation option, reference files, templates, and deterministic scripts), each main file within the project context budget, so compatible hosts discover on-demand packages without loading all workflow text up front. Scope v1 to OpenCode + Codex via the shared `.agents/skills/` target (per Order-10 OQ-01).
  - Depends on: none
  - Expected outcome: generated skills pass format validation, trigger descriptions distinguish use vs non-use, resource references resolve within the package, main files meet the budget, and deterministic scripts have direct tests.
  - Execution state: pending
- [ ] E-02 Generate host-specific adapter metadata in `agent_workflows/host_adapters.py`, EXTENDING the existing shim generator in `agent_workflows/engine.py` (`generate_shim_members`/`shim_body`/`COMMAND_SHIM_DIRS`) rather than forking a second adapter-generation path (rubric C, no duplicate paths). Generate ONLY where required and ONLY for capabilities the Order-10 registry marks non-`unverified`: Codex skill metadata + AGENTS pointer; OpenCode command/agent/skill permissions; (deferred, generated-but-flagged-unverified) Kiro `skill://`, Gemini skill/GEMINI pointer/subagent, Claude skill/subagent incl. optional `context: fork`; agy runner templates. Each adapter maps native features to canonical roles and falls back to external runtime coordination when a feature is absent.
  - Depends on: E-01
  - Expected outcome: per-host golden adapters contain ONLY evidence-backed fields/commands (unverified capabilities are not advertised as supported), map roles/permissions correctly, reuse (not duplicate) the existing `engine.py` shim-generation path, and fall back to external runtime coordination when native isolation is unavailable.
  - Execution state: pending
- [ ] E-03 Restrict skills to discoverable on-demand capabilities + deterministic resources: complex workflows become thin skill entry points, simple informational commands may remain generated commands, and authoritative runtime behavior NEVER lives only in `SKILL.md` prose (it lives in the canonical source + runtime).
  - Depends on: E-02
  - Expected outcome: the skill/discovery inventory matches policy, simple commands remain compact, authoritative semantic digests live outside the wrappers, and disabling a skill leaves the explicit runtime invocation usable.
  - Execution state: pending

### Task group 2: agy fresh-verifier

- [ ] E-04 Replace the same-session agy audit as the completion path with a fresh-session verifier mode that consumes the Order-08 verifier packet; retain the same-session audit ONLY as an optional diagnostic explicitly recorded as non-authoritative.
  - Depends on: E-03
  - Expected outcome: agy test doubles show execution and the fresh verifier use a different session identity + the verifier packet; the same-session audit is labeled diagnostic and cannot finalize.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_host_adapters_skills.py` (stdlib unittest): generated-artifact + semantic-digest-parity tests; discovery diagnostics; unsupported-capability refusal (a capability `unverified` in the Order-10 registry is not advertised); security tests for local-server loopback/auth, permission denial, external-path refusal, and secret redaction; the agy fresh-verifier doubles. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: generated parity, discovery, unsupported-refusal, permission, external-path, loopback/auth, secret-redaction, and agy-verifier tests pass; each `supported` live claim links an exact Order-10 probe; the full serial suite is green (pasted).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Initial host mapping to validate, not assume

| Host | Always-loaded pointer | On-demand package | Isolation candidate | Noninteractive candidate |
|---|---|---|---|---|
| Codex CLI | `AGENTS.md` pointer | Agent Skill | configured subagent/fresh `codex exec` | `codex exec` |
| OpenCode | `AGENTS.md` plus generated command | `.agents/skills/` or `.opencode/skills/` | subagent child session; separate run for verifier | `opencode run --format json` |
| Kiro CLI | steering/custom-agent pointer | `.kiro/skills/` with `skill://` | custom subagent | `kiro-cli chat --no-interactive` |
| Gemini CLI | `GEMINI.md` pointer | `.agents/skills/` or `.gemini/skills/` | custom subagent or fresh process; worktree for isolated mutation | `gemini -p --output-format stream-json` |
| Claude Code | `CLAUDE.md` pointer | `.claude/skills/` | subagent or `context: fork`; worktree for mutation | `claude -p` |
| agy/Antigravity | validated project pointer only | evidence-dependent | new conversation/process verifier | repository wrapper after exact CLI probe (1.1.17 tentative) |

Every cell is a candidate to VALIDATE via Order 10's probe, not a supported claim. v1 generates OpenCode + Codex; other rows are generated-but-`unverified` until probed.

## Project conventions discovered (Step 0)

- Existing generated OpenCode and Claude command shims are thin dispatchers; official hosts increasingly share the Agent Skills directory convention but differ in discovery, consent, fields, and diagnostics.
- Skill frontmatter extensions differ by host; keep portable fields canonical and generate guarded host extensions.
- Local headless servers may be unauthenticated by default (D86/D87): bind loopback + require auth before shared-network use.
- The Order-10 registry is the gate: this Order advertises a capability as supported ONLY if the registry has non-`unverified` evidence for it. Pure/generation module shape (stdlib-only, D138); the canonical semantic digest comes from Order 01.

## Findings

| Finding | Consequence |
|---|---|
| Skill frontmatter extensions differ by host. | Keep portable fields canonical; generate guarded host extensions only. |
| Authoritative behavior could leak into `SKILL.md` prose. | Skills are discovery/packaging only; the semantic digest + runtime remain authoritative. |
| The same-session agy audit is not independent. | Replace it with a fresh-session verifier consuming the Order-08 packet; keep the old audit as a labeled diagnostic. |
| A capability could be advertised before it is proven. | Generation consults the Order-10 registry; an `unverified` capability is never advertised as supported. |
| The repo ALREADY has a host-shim generator (`engine.py` generate_shim_members/shim_body/COMMAND_SHIM_DIRS). | Adapter generation must EXTEND that canonical generator, not fork a parallel path (rubric C); skills add a new artifact family, but the .opencode/.claude command shims stay on the existing generator. |

## Proposed changes (ordered, validatable)

1. Generate portable Agent Skills packages (OpenCode + Codex v1) (E-01).
2. Generate guarded, evidence-gated per-host adapter metadata (E-02).
3. Restrict skills to discovery + deterministic resources; keep authority in the source/runtime (E-03).
4. Replace the same-session agy audit with a fresh-session verifier mode (E-04).
5. Generated-parity + discovery + unsupported-refusal + security + agy-verifier tests + full suite (E-05).

## Deferred / out of scope (with reason)

- The capability-evidence REGISTRY + isolated probes: Order 10 (this Order consumes the registry).
- RUNNING the live host/agy probes: operator-run (Order 10); this Order leaves probe cells `unverified`/pending.
- Behavioral quality/cost comparison across hosts: Orders 12/13.
- Workflow-content migration: Orders 14-16. Removing legacy shims: Order 17. Secondary hosts (Gemini/Claude/Kiro) beyond generated-but-unverified: deferred until probed.

## Scope check

- Over-scope: no registry definition, no live probe runs, no shim deletion, no provider credentials, no workflow-content migration.
- Under-scope: none - skill generation, guarded adapter metadata, the skill-authority restriction, the agy fresh-verifier, and the security/parity tests are covered.

## Required tests / validation

- `tests/test_host_adapters_skills.py`: generated-artifact + semantic-digest parity; discovery diagnostics; unsupported-capability refusal (registry `unverified` -> not advertised); security (loopback/auth, permission denial, external-path refusal, secret redaction); agy fresh-verifier doubles (distinct session + packet; same-session audit cannot finalize).
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan + generated-drift check clean; machine-output validation.

## Spec / documentation sync

- Publish the skill packaging rules and host-by-host adapter limitations; generate support tables FROM the Order-10 evidence records so documented prose cannot exceed a recorded claim.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The skill-directory target (OpenCode + Codex via `.agents/skills/` v1) and the agy version (1.1.17 tentative) were resolved in Order 10 (the registry that gates support); this Order simply consumes those decisions and advertises nothing the Order-10 registry has not marked non-`unverified`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted test output showing generated skills pass format validation, trigger descriptions distinguish use vs non-use, resource references resolve within the package, main files meet the budget, and deterministic scripts have direct tests.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted per-host golden-adapter output containing only evidence-backed fields/commands (no `unverified` capability advertised as supported), correct role/permission mapping, and external-runtime fallback when native isolation is absent.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted test output showing the skill/discovery inventory matches policy, simple commands stay compact, authoritative semantic digests live OUTSIDE the wrappers, and disabling a skill leaves the explicit runtime invocation usable.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted agy test-double output showing execution and the fresh verifier use a different session identity + the Order-08 verifier packet, and the same-session audit is labeled diagnostic and cannot finalize.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: `tests/test_host_adapters_skills.py` exists and passes (generated parity, discovery, unsupported refusal, permission, external path, loopback/auth, secret redaction, agy verifier); each `supported` live claim links an exact Order-10 probe; pasted full serial-suite tail showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 10 (capability registry + probes), Order 08 (verifier packet), and Orders 01-07 upstream. Scope fence: touch only `agent_workflows/host_adapters.py` (the new skill/adapter generator), `agent_workflows/engine.py` (EXTEND the existing shim generator - do not fork a parallel path), the agy fresh-verifier mode module, generated skill/adapter fixtures, and `tests/test_host_adapters_skills.py`; do NOT define the registry or run live probes (Order 10), migrate workflow content (Orders 14-16), or delete legacy shims (Order 17) - if it seems to need more, STOP and report. No host status may be advertised as supported without non-`unverified` Order-10 evidence; never access the real user HOME or credentials; bind local servers to loopback + require auth. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
