---
id: 8it88r
created: 20260823
set: actorenv
order: 00
topic: [actor-attribution, environment-detection, host-identity, model-identity, provenance, workflow-reliability]
model:
kind: research-prompt
status: intake
outcome: none-yet
summary: How to auto-derive a trustworthy actor (host + model) from the environment across coding hosts so aw attribution does not depend on the agent remembering --actor
consumed-by: []
---

<!-- aw-prompt: Kind: research | Status: pending | Created: 2026-08-23 | Author: opencode (Claude Opus 4.8) | Targets: GPT-5.6, Claude Opus 4.8/5, Gemini 3.x, and capable successor coding/research models with web access | Concerns: auto-deriving actor identity (host + model) from the environment across coding agent hosts, trust/spoofability, portable fallback ladder, provenance/attribution reliability | Results-go-to: FILED under .aw/records/research/. This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a principal investigator combining the expertise of a developer-tools / agent-harness engineer, a systems/process-environment engineer, a security engineer focused on provenance and trust boundaries, and a skeptical staff software engineer. Produce a rigorous, citation-backed research report for the maintainers of an open-source toolkit called `agent-workflows`. Return your answer as a single downloadable Markdown file named exactly `actor-identity-from-environment-findings.md`.

# The problem to solve

`agent-workflows` records WHO performed each action in its artifacts - e.g. a lifecycle-status change writes a `## Workflow history` line `- <date> <status> (<actor>): <message>`, where `<actor>` is meant to identify the acting agent, ideally as `host + model` (for example `opencode Opus 4.8`, `Claude Code / claude-opus-5`, `codex / gpt-5.6`). Today the CLI accepts an explicit `--actor` argument; when it is omitted, the code falls back to a generic literal `"aw set"`, so the record says `executed (aw set)` and carries NO real attribution.

The observed failure: AI coding agents (across vendors and models) consistently FORGET to pass `--actor`, so the honest fallback is the useless generic string. Relying on the agent to self-declare its identity every time does not work in practice. The maintainers want to AUTO-DERIVE the actor (host, and if possible model) FROM THE ENVIRONMENT so honest attribution happens without the agent having to remember anything.

# Your central research question

**Across the common AI coding-agent hosts, what identity signals about the running HOST and the running MODEL are reliably derivable from the execution environment (environment variables, process ancestry, config files, host-provided context, filesystem markers), how trustworthy is each, and what is the best PORTABLE strategy for a CLI tool to auto-populate an `actor` string as `host + model` - degrading gracefully when a signal is unavailable, and being honest that self-reported identity is attribution, not authentication?**

# The hosts to cover

For each of these hosts (and note any others you find relevant), investigate what the environment exposes at the moment a shell command / CLI tool runs inside an agent session:

- OpenCode
- Claude Code (Anthropic)
- OpenAI Codex / Codex CLI
- Gemini CLI / Google Antigravity IDE
- Cursor
- Kiro
- GitHub Copilot (CLI / agent modes), and Windsurf/Cline or others if signals exist

# What to investigate and report

1. **Per-host environment signals.** For each host, enumerate concretely what is (and is not) available to a subprocess the agent spawns:
   - Environment variables the host sets that reveal the host name/version and/or the model (name them exactly, with values/patterns where known; cite vendor docs).
   - Process/parentage signals (parent process name, argv, cwd markers) that identify the host.
   - Config/marker files in the repo or home dir (`.opencode/`, `.claude/`, `.cursor/`, `.kiro/`, `AGENTS.md` variants, session state) that indicate the host.
   - Whether the MODEL identity is exposed to the environment AT ALL, and if so how (many hosts do NOT expose the model to a subprocess - state this plainly per host).
   For each signal give: what it identifies (host? model? version?), how stable/documented it is, and how it is obtained.

2. **Trust and spoofability (mandatory).** Analyze the trust boundary honestly: any environment-derived or self-reported actor is ATTRIBUTION, not AUTHENTICATION - it can be absent, wrong, or forged. Classify each signal as: documented-and-stable, undocumented-but-observed (fragile), or self-asserted (spoofable). State clearly what an auto-derived actor CAN be trusted for (a good-faith audit trail / "who most likely did this") and what it CANNOT (a security control / non-repudiation). Recommend how the toolkit should LABEL a derived actor so a reader knows its provenance/confidence (e.g. `opencode Opus 4.8 (env-derived)` vs `(self-declared)` vs `(explicit --actor)`).

4. **Model identity when the environment is silent.** Since the model is frequently NOT in the environment, enumerate the fallbacks and their honesty: an operator-set `AW_ACTOR`/config value; a host adapter that knows its host and asks the agent to fill only the model; leaving model unknown (`opencode / model-unknown`) rather than guessing; or a just-in-time capture at session start. Be explicit that fabricating a model name is worse than recording it as unknown.

5. **A portable derivation ladder.** Design a concrete, deterministic precedence ladder a CLI can implement, from most to least authoritative, that works regardless of host and degrades gracefully. Something like (refine it): explicit `--actor` > operator-configured `AW_ACTOR` env var / config key > host auto-detection (from the per-host signals in #1) combined with any exposed model > host-only with `model-unknown` > the generic `aw set` last-resort. Specify the exact precedence, what each rung yields, how to detect the host deterministically, and how to compose the final `host + model[ + provenance-tag]` string. Note which rungs are portable (work everywhere) vs which need a per-host adapter.

6. **Implementation guidance for a Python stdlib CLI.** The toolkit is a zero-heavy-dependency Python CLI. Recommend how to read the signals with the standard library (os.environ, process inspection), where the detection logic should live (a single `actor`/identity resolver reused by every verb that records an actor), and how to keep it fast and side-effect-free. Note any cross-platform (Linux/macOS/Windows) caveats.

7. **Relationship to reliability and detection.** Explain how auto-derived attribution complements two sibling efforts: making agents adhere to process (auto-attribution removes one thing the agent must remember), and post-hoc detection of unattributed/hand-edited records (a derived actor makes the "generic-actor" fingerprint rarer and the provenance tag makes forgery/omission more visible). Do not overstate: auto-derivation improves the DEFAULT, it does not authenticate.

# Required deliverable structure (in the `.md` file)

1. Executive summary: the recommended portable strategy in 3-6 sentences.
2. Per-host signal table (host | host-identity signal(s) | model-identity signal (or "not exposed") | signal type: documented/observed/self-asserted | how obtained).
3. Trust/spoofability analysis and the recommended provenance labeling.
4. Model-identity fallback analysis (including "record unknown, never fabricate").
5. The concrete derivation ladder with exact precedence and the composed actor-string format.
6. Python-stdlib implementation guidance (single resolver, portability caveats).
7. How it complements adherence + post-hoc detection (honest limits).
8. Open questions and a prioritized, sequenced set of recommendations the maintainers could turn into implementation plans.
9. Full citations.

# Constraints on your method

- Prioritize technical accuracy over reassurance. If a host does not expose the model to a subprocess, say so plainly; do not invent an env var.
- Distinguish DOCUMENTED signals (cite the vendor doc) from OBSERVED-BUT-UNDOCUMENTED ones (mark as fragile) from SELF-ASSERTED ones (spoofable).
- Treat any derived actor as attribution, never authentication; make the honesty of the label a first-class part of the recommendation.
- Never recommend fabricating a host or model identity; "unknown" is the correct value when the signal is absent.
- Be concrete and implementation-oriented: the maintainers will convert your recommendations into an actual actor-resolver in a Python CLI.
- Return exactly one downloadable Markdown file named `actor-identity-from-environment-findings.md`. Do not include anything outside that file.
