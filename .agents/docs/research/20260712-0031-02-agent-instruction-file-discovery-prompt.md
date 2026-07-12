# Research prompt: coding-agent instruction-file discovery and precedence

Copy everything below the line into GPT-5.6 (High). It is written to be self-contained.

---

You are a research assistant with web access. I need a rigorous, **current, and citation-backed**
survey of how today's AI coding agents discover and prioritize their "instruction" / "rules" /
"memory" files, and specifically what happens when a repository contains BOTH a cross-tool
`AGENTS.md` AND a tool-specific file (e.g. `CLAUDE.md`, `GEMINI.md`).

## Why I'm asking (context)

I maintain a tool-agnostic framework that installs reusable agent workflows into any repo. Today it
writes a small marker-delimited pointer block into the repo's **root `AGENTS.md`** (creating one at
the root if none exists; it will update an existing `.agents/AGENTS.md` only if that already exists).
I deliberately do NOT generate `CLAUDE.md` or `GEMINI.md`. My open worry: **if a target repo already
has a `CLAUDE.md` or `GEMINI.md`, does that tool then ignore, override, or subordinate `AGENTS.md`?**
If so, rules I place only in `AGENTS.md` could be silently defeated in exactly the repos that have a
tool-specific file. I need facts to decide whether to (a) keep AGENTS.md-only, (b) also write a
managed pointer block into an existing `CLAUDE.md`/`GEMINI.md`, or (c) detect-and-warn on shadowing.

## What to research (be specific and current; note version/date of each claim)

For EACH of these agents/tools, report the exact instruction-file behavior:

1. **Claude Code** (Anthropic CLI): does it read `AGENTS.md`? `CLAUDE.md`? both? If both exist,
   precedence/merge/override behavior? Root vs nested vs `~/.claude` vs project. Import syntax.
2. **Google Gemini CLI / Gemini Code Assist**: `GEMINI.md`? `AGENTS.md`? precedence when both exist?
   config that changes the filename (e.g. contextFileName)? hierarchical/nested loading?
3. **Antigravity IDE (Google, Gemini-based)**: what instruction/rules files does it read, and does it
   also keep a private/internal "brain" or plan directory? Does it honor root `AGENTS.md`/`GEMINI.md`?
4. **OpenAI Codex CLI / Codex**: `AGENTS.md` support? any Codex-specific file? precedence.
5. **Cursor**: `.cursor/rules` (and legacy `.cursorrules`)? does it read `AGENTS.md`? precedence.
6. **GitHub Copilot (VS Code / coding agent)**: `.github/copilot-instructions.md`,
   `AGENTS.md`, `.github/instructions/*.instructions.md`? precedence and scoping.
7. **OpenCode**: `AGENTS.md`? tool-specific files? precedence.
8. Any other widely used agent where the answer differs (e.g. Windsurf, Cline, Aider, Zed, JetBrains
   AI, Amazon Q Developer): brief note + file(s) + whether `AGENTS.md` is honored.

Also cover the **cross-tool standard itself**:

9. The `AGENTS.md` convention (agents.md): what does the spec say about discovery location (root),
   NESTED `AGENTS.md` files in subdirectories, precedence between a nested and a root file, and how it
   expects tool-specific files to coexist? Which tools officially claim `AGENTS.md` support, and as of
   when?

## The specific questions I most need answered (call these out explicitly)

- **A. Coexistence/precedence:** For each tool that has its own file, when BOTH its file and
  `AGENTS.md` are present at the repo root, does it: read only its own file, read only `AGENTS.md`,
  read both and MERGE, or read both with one taking precedence? Give the exact documented behavior,
  with a source.
- **B. Does a tool-specific file SUPPRESS `AGENTS.md`?** i.e. is there any tool where the mere
  presence of `CLAUDE.md`/`GEMINI.md`/etc. causes `AGENTS.md` to be ignored? (This is my core risk.)
- **C. Symlink/import escape hatch:** For tools that do NOT read `AGENTS.md`, is the common
  recommended workaround a symlink (`CLAUDE.md -> AGENTS.md`), an `@import`/include directive, or
  something else? Note any tool where a symlink is discouraged/broken.
- **D. Nested files:** Which tools support nested/di­rectory-scoped instruction files, and does a
  nested file OVERRIDE or ADD-TO the root file?
- **E. `.agents/AGENTS.md`:** Is there ANY agent that looks in a `.agents/` directory for the
  project-level `AGENTS.md` (as opposed to only repo root and true subdirectory nesting)? I currently
  honor `.agents/AGENTS.md` as a fallback and suspect no mainstream agent actually reads it there.

## Output format

1. A **matrix table**: rows = tools; columns = [reads AGENTS.md? | own file name(s) | if both present:
   behavior | does own file suppress AGENTS.md? | nested support | source+date].
2. A short **"answers to A-E"** section, each with a one-line verdict + citation.
3. A **"what this means for an AGENTS.md-first framework"** section: concrete recommendation on
   whether writing rules only to `AGENTS.md` is safe, and if not, the most robust portable pattern
   (managed block in each tool file? symlinks? a generator?).
4. **Confidence + freshness**: flag anything that is fast-moving, version-specific, or that you could
   not verify; prefer official docs/changelogs over blog posts; give dates.

Do not speculate; where behavior is undocumented, say "undocumented / needs empirical test" rather
than guessing. Cite primary sources (official docs, changelogs, repos) with URLs.
