---
id: 9bd3j8
created: 20260823
set: agentadhere
order: 00
topic: [workflow-reliability, process-adherence, agent-harness, enforcement, tooling-ergonomics]
model:
kind: research-prompt
status: reference
outcome: adopted
summary: How to make agent-workflow process steps (aw set, aw ipd begin/finalize, IPD authoring, path-scoped commits) reliably adhered-to by untrained heterogeneous coding agents
consumed-by: [79li67]
---

<!-- aw-prompt: Kind: research | Status: pending | Created: 2026-08-23 | Author: opencode (Claude Opus 4.8) | Targets: GPT-5.6, Claude Opus 4.8/5, Gemini 3.x, and capable successor coding/research models with web access | Concerns: reliable agent process-adherence, behavioral enforcement vs soft prose, tooling ergonomics, detection of process violations, cross-agent portability | Results-go-to: FILED under .aw/records/research/. This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a principal investigator combining the expertise of an agent-harness/tooling engineer, a prompt-and-context engineer, an applied behavioral/HCI researcher, a developer-experience designer, and a skeptical staff software engineer. Produce a rigorous, citation-backed research report for the maintainers of an open-source toolkit called `agent-workflows`. Return your answer as a single downloadable Markdown file named exactly `agent-process-adherence-findings.md`.

# The problem to solve

`agent-workflows` installs a set of processes into a code repository that AI coding agents (Claude Code, OpenAI Codex, OpenCode, Gemini CLI / Antigravity, Cursor, Kiro, and similar) are expected to follow when they do work. The processes are currently communicated mostly through an always-loaded instruction file (`AGENTS.md`) and on-demand workflow documents, i.e. through PROSE DIRECTIVES ("soft means"). Examples of the required process steps:

- Author an Implementation Plan Document (IPD) BEFORE coding, and run a structured plan-review before executing it.
- Use the provided CLI verbs to change artifact lifecycle state (e.g. `aw set <status> <id>`, and a gated `aw ipd begin` / `aw ipd finalize` for terminal transitions) INSTEAD OF hand-editing a `Status:` field or moving files by hand.
- Commit ONLY the files you changed, path-scoped (`git commit -- <paths>`), never `git add -A`; never push unless explicitly authorized.
- When reporting that tests passed, paste the ACTUAL runner output; never claim success you did not run.
- Move a finished plan to its terminal state through the tool, with an attributed history entry; do not fabricate or back-date records.

# The observed failure (the core motivation)

These soft, prose-based directives are NOT reliably obeyed by ANY current agent, including strong frontier models. The maintainer reports that agents across vendors consistently "forget" or skip these steps: they start coding without an IPD, hand-edit a status field instead of using the CLI verb, forget to run the finalize step, forget to move a plan to its terminal state, etc. This is observed as a cross-vendor, cross-model pattern, not a single bad model. The agents were not trained on this specific toolkit's conventions, so they default to their generic habits. Soft enforcement (telling them in `AGENTS.md`) is demonstrably insufficient.

# Your central research question

**How can a toolkit reliably make heterogeneous, untrained AI coding agents actually adhere to a defined set of process steps, given that always-loaded prose instructions do not work well?** Cover both PREVENTION (making the agent do the right thing) and DETECTION/CORRECTION (catching and fixing it when the agent does the wrong thing), and be honest about the limits of each.

# What to investigate and report

1. **Why soft directives fail.** Explain, with evidence from published research and vendor documentation, WHY always-loaded instruction-file directives get dropped: context-window position/attention decay, instruction competition, lack of training on the specific convention, the difference between "knowing" a rule and "acting" on it under task pressure, recency/salience effects, and the gap between an instruction being present and being retrieved at the decision moment. Quantify where you can.

2. **The mechanism landscape.** Enumerate and critically compare the available mechanisms for enforcing agent behavior, from softest to hardest, with concrete pros/cons, portability across the hosts named above, and evidence of effectiveness:
   - Prose instructions (always-loaded vs just-in-time / trigger-referenced).
   - Just-in-time context injection at the decision point (e.g. a hook that injects the relevant rule only when the triggering action is about to happen).
   - Host hook systems (pre-tool-use / pre-commit / pre-edit hooks) where they exist per host, and their portability.
   - Wrapping/replacing the primitive: making the RIGHT action the easy/only path (e.g. the tool that does the terminal transition also does the scope check, so an agent cannot do the transition without the check).
   - Hard gates / fail-closed refusals at the tool boundary (deterministic code that refuses an out-of-process action).
   - Deterministic post-hoc DETECTION (a linter/checker that flags a process step that was skipped or done by hand) plus a correction loop.
   - Environmental affordances: default-safe tools, argument defaults, self-documenting error messages that teach the next step, reducing the number of steps that must be remembered.
   - Verification by a separate fresh-context agent.
   For each, state: does it PREVENT or DETECT; is it deterministic or probabilistic; does it require host cooperation (and which hosts support it); what does it cost the agent in friction; and how does it fail.

3. **The ergonomics/friction trade-off.** A recurring finding in this project is that a gate which fires too often (false positives) trains agents and humans to treat it as noise, which then misses the real violation; and a step an agent must REMEMBER to run will be skipped. Research and recommend design principles for making the correct path the LOW-FRICTION default (single command does the right thing; the tool the agent already reaches for routes into the safe path; errors teach the next action) rather than an extra step to remember. Address how to detect a violation without a high false-positive rate.

4. **Detection without prevention.** Since full prevention across untrained heterogeneous agents may be impossible, investigate the DETECTIVE approach: a deterministic checker (like a `check`/`doctor` command, a pre-commit hook, or CI) that inspects the repository state AFTER the fact and flags process violations - e.g. a lifecycle status that changed with no corresponding tool-authored history entry, a plan marked done without evidence, a commit that touched files outside a declared scope, a terminal record with a generic/unattributed author. What violations are deterministically detectable from repository artifacts alone? Which are not, and why? How should a detector minimize false positives and present an actionable, self-correcting message?

5. **Making it stick across vendors.** The toolkit installs into repos used by many different agent hosts. Which enforcement mechanisms are PORTABLE (work regardless of host), which require per-host adapters (and which hosts support hooks/permissions/pre-tool-use gating today), and how should a toolkit layer portable-deterministic enforcement (git hooks, CLI-boundary gates, post-hoc checkers) UNDER best-effort per-host prevention (hooks, injected context) so that adherence does not depend on any single host's cooperation?

6. **Empirical grounding.** Cite real evidence: published papers on LLM instruction-following degradation and long-context attention, agent-reliability / tool-use evaluations, vendor docs for hook/permission/gating systems (Claude Code hooks, Codex, OpenCode, Gemini/Antigravity, Cursor, Kiro), and any measured results on prompt-adherence vs. hard-gating. Distinguish measured findings from your reasoning. Where you assert something is a known effect, cite it; where you are inferring, say so.

# Required deliverable structure (in the `.md` file)

1. Executive summary: the single most effective realistic strategy, in 3-6 sentences.
2. Root-cause analysis of why soft prose directives fail (evidence-backed).
3. The mechanism landscape table (prevent vs detect; deterministic vs probabilistic; host-portable vs host-specific; friction; failure mode; effectiveness evidence).
4. A concrete recommended architecture for THIS toolkit: a layered model (portable deterministic enforcement at the bottom, best-effort per-host prevention on top, deterministic post-hoc detection as the safety net), naming which layer catches each of the example process steps above, and which steps are NOT reliably enforceable and must be accepted as residual risk.
5. The ergonomics principles (low-friction correct path; false-positive minimization; self-documenting/teaching errors).
6. What is deterministically detectable post-hoc from repo artifacts vs not.
7. Portability analysis across the named hosts (what each supports for hooks/gating today).
8. Open questions and a prioritized, sequenced set of recommendations the maintainers could turn into implementation plans.
9. Full citations.

# Constraints on your method

- Prioritize technical accuracy over reassurance. If full enforcement is impossible for a class of steps, say so plainly and explain the residual risk rather than proposing a mechanism that only appears to work.
- Distinguish measured evidence from inference throughout.
- Favor mechanisms that are DETERMINISTIC and PORTABLE (do not depend on any one model's goodwill or any single host) over ones that rely on the agent choosing to comply.
- Be concrete and implementation-oriented: the maintainers will convert your recommendations into actual CLI/tooling/hook/CI changes.
- Return exactly one downloadable Markdown file named `agent-process-adherence-findings.md`. Do not include anything outside that file.
