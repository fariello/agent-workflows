# Spec: external / out-of-repo delivery and host-native skills for agent-workflows

- Date: 2026-07-25
- Status: deferred
- Gate-Kind: artifact
- Gate-Ref: TODO.md
- Gate-Summary: host-native SKILLS delivery-model re-evaluation
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Sources: research `.agents/docs/research/20260722-agent-coding-system-file-discovery-and-write-safety-00-x41kw0-agent-coding-system-file-discovery-and-write-safety.findings.md` and `.agents/docs/research/20260722-token-efficient-managed-sections-in-agent-instruction-files-00-0jl8pv-token-efficient-managed-sections-in-agent-instruction-files.gpt56.findings.md`
- Related: IPD `20260723-instsafe-01-920qnm-install-manifest-and-managed-sections-model` (install manifest / ownership), IPD `20260722-instsafe-06-mv7hw7-deepen-interactive-questions-convention` (interactive-questions trigger)

This spec decides, from evidence, how much of agent-workflows can live OUTSIDE a repo and still be discovered AND followed per host, and defines the probe protocol that produces that evidence. It builds nothing: the delivery build is a separate later IPD, gated on the probe results recorded here.

## 1. Problem and goal

Not every repo should have to carry the full `.agents/workflows/` tree (and pay its footprint) to use agent-workflows. The maintainer wants an out-of-repo option (a packaged data path, a home-dir location, or host-native portable skills) that cuts per-repo footprint without breaking discovery, versioning, or the ownership model. The load-bearing question is empirical and per host: does host X, at version V, actually RESOLVE and then FOLLOW agent-workflows content that does not live in the repo? This spec answers "what may live where" only after that question is answered by the probe protocol in Section 4.

## 2. What is true today (verified from code)

- The pip package ships the workflow tree as importable data; `packaged_source_root()` (`agent_workflows/_compat.py:25`) locates `agent_workflows/_data/.agents/workflows/`, and `resolve_source_root()` (`agent_workflows/engine.py:298-323`) prefers an explicit `--source`, then the packaged data, then the dev checkout. So an out-of-repo SOURCE already exists for the INSTALLER.
- But DISCOVERY and EXECUTION assume an IN-REPO copy:
  - the generated shim body is `Read and execute @.agents/workflows/<...>` (`engine.py:533`);
  - the AGENTS pointer prose points at `.agents/workflows/index.md` (`engine.py:601-617`);
  - `read_installed_version()` reads `.agents/workflows/VERSION` (`engine.py:3896-3904`);
  - the stale/drift check asserts the in-repo `Read and execute @.agents/workflows/` line (`engine.py:2321-2358`).
- There is NO home-dir/global CONTENT location. The user config (`agent_workflows/config.py:43-57`) stores only WHERE repos are (search roots + repo allowlist), lives at `$XDG_CONFIG_HOME/agent-workflows/config.json` (fallback `~/.config/...`), and is never written under `~/` directly.
- `.agents/skills/<name>/SKILL.md` is discussed in the research as an emerging portable path (natively discovered by some hosts) but is implemented NOWHERE in the toolkit; there is no `SKILL.md` template and no skills code.
- Hosts with real code coupling today: OpenCode + Claude (shim dirs `engine.py:96-99`) plus the `CLAUDE.md`/`GEMINI.md` mirror (`engine.py:105`). Codex, Cursor, Antigravity, and GitHub/VS Code Copilot are addressed only via the universal `Read and execute <body path>` fallback, not native adapters.

## 3. Delivery tiers

Each tier is a candidate location for agent-workflows CONTENT (the workflow bodies and the directives), independent of the INSTALLER source (which is already packaged). A tier is adoptable for a given host only if the probe (Section 4) shows the host RESOLVES and FOLLOWS content at that tier.

| Tier | Location | Discovery mechanism | Adopt when | Notes |
|------|----------|---------------------|------------|-------|
| T0 | In-repo `.agents/workflows/` (today) | The installer writes shims + the AGENTS pointer; the host reads the repo. | Always available. The universal fallback. | Highest footprint; the current, proven model. Never removed as the fallback. |
| T1 | Packaged data path (`agent_workflows/_data/.agents/workflows/`, via `packaged_source_root`) | A shim/pointer references the packaged path instead of an in-repo copy. | The host resolves AND follows a reference to a path outside the repo tree (probe R1). | Source already exists; needs a portable way to name it in a shim/pointer, plus VERSION/drift adaptation (Section 5). |
| T2 | Host-native `.agents/skills/<name>/SKILL.md` (in-repo path, host-discovered) | The host natively auto-discovers `SKILL.md` without an explicit pointer. | The host natively discovers AND acts on a `SKILL.md` (probe R2). Only for SKILL-eligible workflows (Section 3.1). | Portable across the hosts that support it; still in-repo (small), but host-understood without the pointer. Keep T0 fallback for non-supporting hosts. |
| T3 | Home-dir / global (e.g. `~/.local/share/agent-workflows/` or an XDG data dir) | A global pointer or host global-config reference. | The host resolves AND follows a home-dir reference (probe R3) AND the user has explicitly consented (Section 5). | Lowest per-repo footprint; HIGHEST consent/ownership risk. Never auto-installed; consent-gated. |

### 3.1 Skill-eligibility classification (do not mechanically convert every `.md`)

A workflow is SKILL-eligible (T2 candidate) only if it is a self-contained, invoked-on-demand capability the host can run as a skill. It is NOT skill-eligible if it is a manual runbook the user reads, an assessor/agent persona, or a lens/catalog row.

- Likely skill-eligible (self-contained, on-demand): `release-review`, `plan-review`, `verify`, `verify-execution`, `scaffold`, `setup-repo`, `spec`, `migrate`, `incident`, `release-notes`, `getting-started`, `list-workflows`, `benchmark`, `handoff`, `whatnext`.
- Not a mechanical skill (persona/assessor/dialogue): `advise` (+ its personas), `assess`/`assess-all` (+ concern lenses) - these are lens/persona-driven and may need a different mapping.
- Catalog rows (`assess-<concern>`, `advise-<persona>`) are NOT separate skills; they are parameters of their parent.

This classification is provisional and MUST be reconciled with the T2 probe outcome before any conversion.

## 4. Per-host probe protocol (operator-run; produces the evidence)

This protocol is run by a human or a host-with-access operator, NOT by the IPD. For each host and version, place the fixtures, run the check, and record the result. "Resolved" = the host loaded/attached the content. "Followed" = the host actually acted on an instruction that ONLY the out-of-repo/skill content could have supplied.

### Fixtures

- R1 (out-of-repo pointer): in a scratch repo, replace the in-repo body reference with a reference to an out-of-repo path (the packaged data path or an absolute path), containing a unique, side-effect-producing instruction (e.g. "create a file `PROBE-R1-OK.txt`").
- R2 (skill): create `.agents/skills/aw-probe/SKILL.md` with a unique instruction (e.g. "create `PROBE-R2-OK.txt`") and NO in-repo pointer to it.
- R3 (home-dir): place the R1 content at a home-dir/global location and reference it globally; unique instruction "create `PROBE-R3-OK.txt`".

### Check (per fixture)

1. Start a fresh session in the scratch repo with the host.
2. Ask the host to perform the task that requires the probe instruction.
3. Record: did the side effect happen (the `PROBE-*-OK.txt` appeared / the instruction was obeyed)? "resolved" and "followed" are recorded separately (a host may resolve but not follow, or vice versa).
4. Note the host version, the exact fixture path used, and any host setting required.

### Results table (fill per host x version x tier)

| Host | Version | Tier (R1/R2/R3) | Resolved? | Followed? | Fixture path | Notes | Date | Operator |
|------|---------|-----------------|-----------|-----------|--------------|-------|------|----------|
| OpenCode |  | R1 |  |  |  |  |  |  |
| OpenCode |  | R2 |  |  |  |  |  |  |
| Claude Code |  | R1 |  |  |  |  |  |  |
| Claude Code |  | R2 |  |  |  |  |  |  |
| Codex |  | R2 |  |  |  |  |  |  |
| GitHub/VS Code Copilot |  | R2 |  |  |  |  |  |  |
| Cursor |  | R1 |  |  |  |  |  |  |
| Antigravity |  | R1 |  |  |  |  |  |  |
| Gemini |  | R1 |  |  |  |  |  |  |

(Add rows per version; a tier is adoptable for a host only when both Resolved AND Followed are yes, reproducibly.)

## 5. Constraints and non-goals any future build MUST respect

- In-repo assumptions to preserve or adapt (verified, Section 2): the shim body reference (`engine.py:533`), the AGENTS pointer prose (`engine.py:601-617`), `read_installed_version` reading `.agents/workflows/VERSION` (`engine.py:3896-3904`), and the stale/drift check asserting the in-repo line (`engine.py:2321-2358`). Any external tier must keep VERSION detection and drift/ownership working (e.g. an external VERSION source and a manifest that records the external path).
- Ownership continuity: any external artifact MUST remain identifiable, versioned, and removable via the IPD-01 manifest. The manifest is path-parameterized and git-independent, so it can record a non-in-repo path; the build must use that, not a new ad-hoc registry.
- Home-dir consent (T3): the installer MUST NOT mutate a user's global/home agent config or install global content without explicit, warned consent. T3 is never auto-installed.
- Universal fallback: T0 (in-repo) MUST remain available; a host for which an external tier is unproven degrades to T0 with no loss of capability.
- Non-goals of THIS spec: it does not build any tier, does not run the probes, and does not convert any workflow to a skill. Those are follow-on work gated on the results table.

## 6. Decision criteria (how the results drive the build)

- If R2 (skill) is Resolved+Followed for a host, that host can receive SKILL-eligible workflows via T2; keep T0 for the rest.
- If R1 (out-of-repo pointer) is Resolved+Followed for a host, that host can receive bodies via T1 (packaged path) with an adapted VERSION/drift path.
- If R3 is Resolved+Followed AND the user consents, T3 becomes available for that user; still never auto-installed.
- Where a tier is unproven or fails Followed, that host stays on T0. No tier is adopted globally on the strength of one host.

## 7. Follow-on work (separate IPDs, gated on this spec's evidence)

1. Run the probe protocol per host/version; record the results table (operator work).
2. A per-tier BUILD IPD (T1/T2/T3) for the hosts the evidence supports, keeping T0 fallback, manifest ownership, and consent gates.
3. A `SKILL.md` mapping IPD for the skill-eligible set, reconciled with the T2 outcome.

## Workflow history
- 2026-08-08 migrated (aw specs): normalized status to `deferred` (was: draft spec (evidence-gated); produced by IPD `20260723-instsafe-05-kemhdg-external-install-and-skills-delivery-research-spec`)
