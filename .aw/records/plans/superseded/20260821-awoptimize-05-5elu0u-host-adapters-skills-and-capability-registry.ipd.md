RETIRED 2026-08-21: superseded by the awoptimize re-scope (right-sizing into smaller child IPDs; see the re-scope proposal and DECISIONS). This old Order is resplit into new Orders 10, 11.

# IPD: Host Adapters Skills and Capability Registry

- Date: 2026-08-21
- Kind: child
- Concern: Deliver canonical workflows through native host mechanisms without inventing unsupported commands or duplicating semantics.
- Scope: Versioned capability evidence registry, probe harness upgrades, adapter generators and thin skill packages for Codex CLI, OpenCode, Kiro CLI, Gemini CLI, Claude Code, and repository `agy` integration; compatibility shims and focused tests. No live benchmark scoring.
- Status: superseded
- Set: awoptimize
- Order: 5
- Highest E allocated: 08
- Author: Codex GPT-5.6 Sol
- Id: 5elu0u

## Workflow history

- 2026-08-21 draft (Codex GPT-5.6 Sol): created after comparing repository claims with current official host documentation.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Design is sound and honest: evidence-keyed capability registry replacing boolean claims, fail-closed 'unverified' default, positive-and-negative isolated host probes, thin generated skills with no runtime semantics in SKILL.md, and the agy fresh-verifier correction. Size assessment standard (correct). Both BLOCKING open questions resolved with the maintainer as SCOPING decisions that preserve the fail-closed probe gate: OQ-01 -> target OpenCode + Codex first via shared `.agents/skills/`, others deferred, nothing marked 'supported' without a live probe; OQ-02 -> installed `agy --version` is 1.1.17, recorded as the TENTATIVE target, still `unverified` until an isolated live probe on that exact version. The live host/agy probes are operator-run (maintainer pastes evidence); the executor generates adapters/skills for the scoped hosts and leaves probe cells unverified/pending. This Order sequences after Orders 01/03/04.

## Goal

Generate the smallest native wrapper each host needs while keeping the workflow source, state machine, evidence contract, and verification semantics portable. Replace the current static host matrix with a claim registry whose support statuses are backed by exact, reproducible evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Capability evidence

- [ ] E-01 Replace boolean host claims with records keyed by host, distribution, exact version, OS, mode, feature, configuration, probe variant, result, evidence artifact, observed date, expiry, and source type; default missing or expired entries to `unverified`.
  - Depends on: none
  - Expected outcome: generated adapters cannot advertise a path, command, skill, subagent, fork, background, worktree, or diagnostic capability without qualifying evidence.
  - Execution state: pending
- [ ] E-02 Upgrade the conformance harness to source command templates from validated adapters, detect installed versions, scaffold isolated HOME/XDG fixtures, capture stdout/stderr/exit/nonce side effects, redact evidence, and refuse real-home targets.
  - Depends on: E-01
  - Expected outcome: probes test resolution and following separately and produce machine-validated durable reports.
  - Execution state: pending
- [ ] E-03 Add negative probes for missing skill, denied permission, no user input, path precedence, stale adapter, malformed frontmatter, external path refusal, server authentication, and background result loss.
  - Depends on: E-02
  - Expected outcome: support means both the positive contract and expected fail-closed behavior are reproduced.
  - Execution state: pending

### Skills and adapters

- [ ] E-04 Generate portable Agent Skills packages with concise `SKILL.md` routers, exact trigger descriptions, canonical semantic digest, explicit invocation option, reference files, templates, and deterministic scripts; keep each main file within the project's selected context budget.
  - Depends on: E-03
  - Expected outcome: Codex, OpenCode, Kiro, Gemini CLI, and compatible hosts discover on-demand packages without loading all workflow text up front.
  - Execution state: pending
- [ ] E-05 Generate host-specific adapter metadata only where required: Codex skill metadata and AGENTS pointer; OpenCode command/agent/skill permissions; Kiro custom-agent and `skill://` resource declarations; Gemini skill, GEMINI pointer, subagent definitions; Claude skill/subagent fields including optional `context: fork`; agy runner command templates.
  - Depends on: E-04
  - Expected outcome: each adapter maps native features to canonical roles and falls back to external runtime coordination when a feature is absent.
  - Execution state: pending
- [ ] E-06 Restrict skills to discoverable on-demand capabilities and deterministic resources: complex workflows become thin skill entry points; simple informational commands may remain generated commands; authoritative runtime behavior never lives only in `SKILL.md` prose.
  - Depends on: E-05
  - Expected outcome: skill activation, explicit invocation, runtime execution, and verification are separately testable.
  - Execution state: pending
- [ ] E-07 Replace same-session agy audit as the completion path with a fresh-session verifier mode that consumes the verifier packet; retain same-session audit only as an optional diagnostic and record its non-authoritative status.
  - Depends on: E-06
  - Expected outcome: repository tooling no longer equates resumed-session skepticism with independent proof.
  - Execution state: pending
- [ ] E-08 Add generated-artifact tests, discovery diagnostics, semantic-digest parity, isolated probe fixtures, unsupported-capability refusal, and security tests for local servers, permissions, external paths, and secret redaction.
  - Depends on: E-07
  - Expected outcome: host integration is measurable, least-privilege, and fail-closed.
  - Execution state: pending

## Initial host mapping to validate, not assume

| Host | Always-loaded pointer | On-demand package | Isolation candidate | Noninteractive candidate |
|---|---|---|---|---|
| Codex CLI | `AGENTS.md` pointer | Agent Skill | configured subagent/fresh `codex exec` | `codex exec` |
| OpenCode | `AGENTS.md` plus generated command | `.agents/skills/` or `.opencode/skills/` | subagent child session; separate run for verifier | `opencode run --format json` |
| Kiro CLI | steering/custom-agent pointer | `.kiro/skills/` with `skill://` | custom subagent | `kiro-cli chat --no-interactive` |
| Gemini CLI | `GEMINI.md` pointer | `.agents/skills/` or `.gemini/skills/` | custom subagent or fresh process; worktree for isolated mutation | `gemini -p --output-format stream-json` |
| Claude Code | `CLAUDE.md` pointer | `.claude/skills/` | subagent or `context: fork`; worktree for mutation | `claude -p` |
| agy/Antigravity | validated project pointer only | evidence-dependent | new conversation/process verifier | repository wrapper after exact CLI probe |

## Project conventions discovered (Step 0)

- Current conformance files call themselves Phase 0 and require live per-host/version proof before shipping a tier.
- The static matrix currently includes commands not established by repository evidence.
- Existing generated OpenCode and Claude command shims are thin dispatchers.
- Official hosts increasingly share the Agent Skills directory convention but differ in discovery, consent, fields, and diagnostics.

## Findings

| Finding | Consequence |
|---|---|
| The static host matrix contains unproven support booleans and command templates. | Treat it as seed data, not evidence, and migrate to claim records. |
| Skill frontmatter extensions differ by host. | Keep portable fields canonical and generate guarded host extensions. |
| Native subagent isolation varies and may still share a filesystem. | Map context and worktree isolation separately. |
| Local headless servers may be unauthenticated by default. | Bind to loopback and require auth before shared-network use. |
| `agy` is repository-local integration with no executable present in the audit environment. | Mark exact behavior pending and provide operator probes. |

## Proposed changes (ordered, validatable)

1. Replace unsupported booleans with versioned evidence claims.
2. Upgrade isolated positive and negative probes.
3. Generate portable skills from canonical packages.
4. Add guarded native metadata per host.
5. Change agy verification to a fresh-session completion path.
6. Gate discovery, parity, permissions, and security with tests.

## Deferred / out of scope (with reason)

- Behavioral quality and cost comparison belongs to Order 06.
- Workflow-content migration belongs to Order 07.
- Removing legacy shims belongs to Order 08.
- Unsupported IDE-only or remote/cloud behaviors remain pending until exact probes exist.

## Scope check

- Over-scope: no provider credential setup, live paid model calls, releases, or deletions of compatibility shims.
- Under-scope: evidence registry, probes, skills, adapters, agy correction, security, and tests are covered.

## Required tests / validation

- Exact adapter golden tests and semantic-digest parity.
- Isolated fake-host fixtures for every probe variant.
- At least one operator-run live probe per advertised host/version/mode before status becomes supported.
- Discovery test and outcome test kept separate for every skill.
- Server loopback/auth, permission-denied, and redaction tests.
- Full suite, leak scan, generated drift check, and machine-output validation.

## Spec / documentation sync

- Publish the capability-claim schema, evidence expiry rules, exact probe runbook, skill packaging rules, and host-by-host adapter limitations.
- Generate support tables from evidence records so prose cannot exceed recorded claims.

## Open questions

### OQ-01: Which cross-host skill directory is the primary generated target?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED (2026-08-21, /plan-review with the maintainer): scope v1 to OPENCODE and CODEX FIRST (the maintainer's daily-driver hosts), generating to the shared `.agents/skills/` convention as the PRIMARY target where each host discovers it, with per-host directories only where a host requires its own. Gemini CLI, Claude Code, and Kiro CLI are secondary targets deferred until probed. This is a SCOPING decision only; it does NOT mark any host capability "supported" - every generated adapter/skill stays `unverified` in the capability registry (E-01) until the maintainer runs the isolated live probe (E-02/E-03) on the exact host version and pastes the result. The executor generates for OpenCode + Codex, records the target directories, and leaves the live-probe cells `unverified`/pending for the operator to fill.

### OQ-02: What is the exact supported `agy` version and vendor documentation?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED (2026-08-21, /plan-review with the maintainer): the maintainer's installed `agy --version` is `1.1.17`, recorded as the TENTATIVE supported target. Per the fail-closed capability discipline (E-01), `1.1.17` is NOT marked "supported" on documentation or version alone; it stays `unverified` until an isolated live probe (E-02/E-03) reproduces the positive contract AND the expected fail-closed behavior on that exact version and the maintainer pastes the evidence. The existing agy runner remains an unverified compatibility integration until then. Vendor documentation for that exact version is to be cited by the operator with the probe.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: migration fixture proves every old matrix claim becomes a versioned claim, missing evidence yields unverified, stale evidence expires, and generators reject unsupported claims.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: isolated fixture tests prove version detection, real-HOME refusal, adapter-derived commands, complete capture/redaction, nonce verification, and valid durable report output.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: every negative variant yields its declared fail-closed result and cannot promote a capability claim; positive and negative outcomes remain separate records.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: generated skills pass format validation, trigger descriptions distinguish use/non-use, resource references resolve within package, main files meet budget, and deterministic scripts have direct tests.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: per-host golden adapters contain only evidence-backed fields/commands, map roles and permissions correctly, and fall back to external runtime coordination when native isolation is unavailable.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: skill/discovery inventory matches policy, simple commands remain compact, authoritative semantic digests live outside wrappers, and disabling a skill leaves explicit runtime invocation usable.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: agy test doubles show execution and fresh verifier use different session identity and verifier packet; same-session audit is labeled diagnostic and cannot finalize.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: generated parity, discovery, unsupported refusal, permissions, external path, loopback/auth, secret redaction, and full-suite tests pass; each supported live claim links an exact probe.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: capability evidence and generated host delivery must share one fail-closed boundary.

Requires executed Orders 01, 03, and 04. No host status may be promoted from documentation alone; a positive isolated live probe is required. Do not access real user HOME or credentials in tests.

Execution contract: path-scoped commits, no push or broad staging, raw redacted probe evidence retained. Unsupported combinations remain pending. Terminal transition requires independent validation.
