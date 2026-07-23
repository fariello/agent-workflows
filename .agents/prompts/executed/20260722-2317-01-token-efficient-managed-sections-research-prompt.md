You are a research analyst with web-search access. Produce a rigorous, citation-backed research report for the maintainers of an open-source toolkit called `agent-workflows`. Return your answer as a single downloadable Markdown file named exactly:

`20260722-2317-01-token-efficient-managed-sections-in-agent-instruction-files.gpt-56.research.finding.md`

## Background you need

Agentic coding hosts (Claude Code, OpenAI Codex, OpenCode, GitHub Copilot, Gemini CLI, Cursor, Windsurf, Kiro, Cline, and similar) load an "always-on" project instruction file at session start, most commonly `AGENTS.md` (or `CLAUDE.md`, `GEMINI.md`). The host injects that file's text into the model's context as system/instruction content. Because chat models are stateless per turn, the host resends the assembled context on every turn, so the instruction file's content is effectively present on every interaction of the session. Its token cost is therefore paid repeatedly: for short sessions it can dominate cost; for long sessions it is dwarfed by the transcript.

`agent-workflows` installs into many repositories. It needs to place its own managed content into these shared instruction files (which the user and other tools also own) in a way that is: (a) cheap in recurring tokens, (b) reliably obeyed when needed, and (c) safely maintainable across releases: each managed section must be individually identifiable, addable, removable, and editable, and the installer must be able to detect whether a section it owns was modified by the user, all without bloating the always-on file.

A specific pattern under consideration is a "trigger reference": instead of inlining a full directive, place a short conditional line in the always-on file such as "when you are about to ask the user a question, first read and execute `.agents/<owned-file>.md`", so the bulk of the directive lives in a file the toolkit fully owns and is only read just-in-time when the triggering action occurs.

## What to research and report

1. **Cost mechanics.** How each major host assembles and resends context per turn; whether always-on instruction files are cached (e.g. prompt caching / context caching on Anthropic, OpenAI, Google) and how caching changes the recurring token cost of a stable instruction block. Quantify where you can (typical instruction-file sizes, caching discounts, per-turn vs per-session cost).

2. **Trigger-reference / just-in-time reference files.** Do hosts actually follow a "when X, read and execute file Y" instruction reliably? Distinguish passive references (a link that may only be displayed) from action-bound triggers. Report any documented behavior, vendor guidance, or credible community/benchmark evidence on efficacy, and how reliability differs for always-on behavioral directives versus on-demand workflow loads. Note `@import`/file-embed features (e.g. Claude Code `@path`) and whether they inline (cost paid every turn) or lazy-load.

3. **Token-efficient managed-section formats.** Ways to delimit and identify sections a tool owns inside a shared Markdown file using minimal tokens: comment markers, fenced regions, front-matter registries, ID conventions. For each, assess token overhead, human readability, and machine parseability.

4. **Modification / drift detection without heavy tokens.** How to tell if a user edited a tool-owned section, cheaply: content hashing recorded in an external manifest vs inline checksums, marker-pair integrity, normalization concerns (whitespace, line endings). Which approaches avoid putting hashes or bulky metadata into the always-on file itself.

5. **Granular consent and cross-release lifecycle.** Patterns for letting a user accept some managed directives and decline others, persisting a per-section decline so upgrades do not silently re-add it, and cleanly updating or removing an individual section in a later release, contrasted with a monolithic all-or-nothing block.

6. **Alternative approaches** beyond trigger references and inline sections: separate per-directive files with host-native import, host-native skills/commands as the delivery vehicle, out-of-repo/user-scope instruction files, conditional or path-scoped rules, and any 2026-era mechanisms. Compare on recurring token cost, delivery reliability, maintainability, and cross-host portability.

## Constraints and quality bar

- Use current official vendor documentation and upstream sources; cite them inline with URLs. Mark each claim High / Medium / Low confidence, where High means official docs explicitly state the behavior and Low means version-sensitive or unverified.
- Be explicit about behavior that varies by host or host version, and about anything that must be empirically probed rather than assumed.
- Prefer concrete, quantified findings and clear recommendations over generalities. Where you make a recommendation, state its main factual basis.
- Do not assume a single host; cover the representative set named above.

## Required output

A single downloadable Markdown file named exactly `20260722-2317-01-token-efficient-managed-sections-in-agent-instruction-files.gpt-56.research.finding.md`, containing: an executive summary with the top recommendations; one section per numbered research area above; a comparison table of approaches scored on recurring token cost, delivery reliability, maintainability/section-management, drift detection, and cross-host portability; a concrete recommended architecture for `agent-workflows` (how to deliver managed directives cheaply and reliably while keeping each section individually identifiable, addable, removable, editable, and drift-detectable); and a confidence-rated citation list.
