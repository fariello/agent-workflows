<!-- aw-prompt: Kind: research | Status: executed | Created: 2026-08-13 | Author: opencode (Opus 4.8, its_direct/pt3-claude-opus-4.8-1m-us) | Targets: external LLMs with web search (Gemini, Claude, GPT) | Concerns: the future /aw <verb> slash-command family (backlogged in TODO.md; referenced by IPD bsxowq / Set migdispo) | Results-go-to: FILED under .agents/docs/research/ as set 'awnamespace' (reconciliation/deciding doc id 2bodwq, adopted); commit 5c636d3. This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
You are a senior developer-tooling researcher. I need a rigorous, evidence-backed report on how AI coding agents implement user-invoked "slash commands" (e.g. `/review`, `/setup`), specifically whether a NAMESPACED command family under a single prefix is possible, and what the most portable design is.

# Background (what I am building)
I maintain a tool-agnostic framework that installs reusable "workflows" into a repository and generates per-host slash-command shims so a user can invoke a workflow by typing a slash command. Today the commands are FLAT: one file per command, e.g. `.opencode/commands/assess.md` -> `/assess`, `.claude/commands/setup-repo.md` -> `/setup-repo`. I want to move to a single namespaced family, ideally `/aw <verb>` (e.g. `/aw setup`, `/aw assess`, `/aw migrate`), mirroring the `aw <verb>` CLI, without colliding with anything existing.

# The core questions to answer, PER HOST
Cover at least these hosts: **OpenCode**, **Claude Code (Anthropic)**, **Cursor**, **GitHub Copilot (chat/agent)**, **Windsurf**, **Gemini CLI / Gemini Code Assist**, and **Antigravity** if it has a public command mechanism. For EACH host:

1. **Custom slash-command mechanism:** How are user/project custom slash commands defined (file location, format, front-matter, naming)? Cite official docs with URLs and version/date.
2. **Namespacing / subcommands:** Is a true namespaced command supported, i.e. can a user type `/aw migrate` where `aw` is a group and `migrate` is a subcommand? Consider three concrete mechanisms and state which (if any) the host supports:
   a. **Subdirectory namespacing** (e.g. `commands/aw/migrate.md` rendering as `/aw:migrate` or `/aw migrate`),
   b. **Argument-based** (a single `/aw` command that takes `migrate` as an argument and dispatches),
   c. **Flat prefix only** (no real namespace; best achievable is `/aw-migrate` as a plain command name).
   State the EXACT invocation string a user would type for each supported mechanism.
3. **Collision surface:** Does the host reserve `/aw` or have built-in commands that would conflict? How are name collisions between built-in and custom commands resolved?
4. **Arguments & discovery:** Can a namespaced/argument command accept further arguments and flags? How does command autocomplete/discovery present a namespaced family to the user?
5. **Portability verdict:** For THIS host, what is the most user-friendly command shape achievable, and does it match `/aw <verb>`?

# Cross-host synthesis (the decision I actually need)
- A comparison table: host x (subdirectory namespace? / argument dispatch? / flat-prefix only?) x (exact user invocation) x (source URL + date).
- The SINGLE most portable design that gives the closest thing to `/aw <verb>` across the most hosts, and where it degrades (e.g. "true `/aw migrate` on hosts X/Y; falls back to `/aw-migrate` on Z").
- A recommended migration/back-compat approach: how to introduce the `/aw` family while keeping the OLD flat command names working as aliases, and a sane deprecation path. Note anything host-specific that complicates aliasing.
- Explicitly flag any host where namespacing is impossible or ill-advised, and say why.

# Rules for your report
- Prioritize OFFICIAL documentation; cite every nontrivial claim with a URL and the date you accessed it. Clearly separate documented facts from your inference. If a host's behavior is undocumented or you are unsure, say so rather than guessing.
- Prefer current/recent information; note version numbers and dates, since these tools change fast.
- Be concrete: give real file paths, real front-matter, and the literal command string a user types.
- Do not pad with generalities about "what slash commands are"; go straight to the per-host specifics and the comparison.

# Deliverable
Return your entire answer as a single DOWNLOADABLE markdown file named `aw-namespace-research-report.md` (provide it as a downloadable `.md` file, not only inline), structured as:
1. Executive summary + the one recommended portable design (2-3 short paragraphs).
2. Per-host sections (one per host) answering questions 1-5.
3. The cross-host comparison table.
4. Back-compat + deprecation recommendation.
5. Open risks / unknowns / hosts where this is not viable.
6. A references list (every URL with access date).
