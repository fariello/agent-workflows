---
id: sx0cqv
created: 20260905
set: host-skill-runtime-discovery-and-authoring
order: 00
topic: [skills, hosts, discovery]
model:
kind: research-prompt
status: todo
outcome: none-yet
summary: What do real agent/IDE skill runtimes actually discover and reward: does any host require .agents/skills, and what makes a SKILL.md reliable
consumed-by: []
priority: high
---
# Research request: what do agent "skill" runtimes actually discover, and what makes a SKILL.md reliable?

You are researching the real, current behavior of AI coding-agent hosts that consume on-disk
"skill" packages. Answer from primary sources (official docs, changelogs, source code, release
notes, issue trackers) and say plainly when something is undocumented or unverifiable.

RETURN YOUR ANSWER AS A DOWNLOADABLE MARKDOWN (`.md`) FILE. Do not answer only in chat.

## The codebase under discussion

The toolkit asking this question is public and you may read it:

    https://github.com/fariello/agent-workflows

It generates one "skill package" per workflow so that different agent hosts can discover its
workflows on demand. Each package is three files: a `SKILL.md` router carrying YAML frontmatter
(a trigger `description` and a `semantic-digest`) plus an explicit invocation line, a
`reference/canonical-body.md` that POINTS AT the authoritative workflow body rather than copying
it, and a `scripts/verify_digest.py` that compares a supplied digest against a baked-in constant.
The relevant generator is `agent_workflows/host_adapters.py` (`build_skill_package`,
`validate_skill_package`) and the directory decision lives in `agent_workflows/engine.py`
(`SKILLS_DIR`, `resolve_skills_dir`). Read them if useful; do not assume the design is correct.

The toolkit currently writes these packages to `<repo-root>/.agents/skills/<name>/`, and maps
some hosts to native directories instead (`.claude/skills`, `.kiro/skills`, `.gemini/skills`).
Its own code comments justify `.agents/skills` as a "host-consumption location ... discovered by
host tools that scan a fixed directory", and one of its specs describes that path only as "an
emerging portable path", so the justification may be aspirational rather than evidenced. That is
the first thing to check.

## Question 1: which hosts actually discover skills, and from where?

For each of the following, establish what the CURRENT shipped version really does, with a
citation and a date or version for each claim:

- Claude Code / Claude.ai (Anthropic Agent Skills)
- OpenCode
- OpenAI Codex (the CLI/IDE agent, not the deprecated model)
- Cursor
- Windsurf
- GitHub Copilot (agent/workspace features)
- Google Gemini CLI and Antigravity
- Amazon Kiro
- Zed, Cline, Aider, Continue, or any other host with a comparable mechanism

For each host report, as separate facts rather than one blended answer:

1. Does it load repository-local instruction or skill files at all?
2. What EXACT paths does it scan? Give the literal glob or directory.
3. Is `.agents/` or `.agents/skills/` among them? THIS IS THE DECISIVE QUESTION. If any host
   requires or scans that path, name it, cite it, and give the version in which it started.
4. Is discovery automatic, or must the user register or enable each skill?
5. What file format does it require (frontmatter schema, required keys, size limits)?
6. Does it EXECUTE scripts shipped inside a skill package? If so, when, with what working
   directory, and with what permission prompt? If it never executes them, say so explicitly.

If `.agents/skills` turns out to be a convention no shipped host actually reads, say that
directly. A negative finding is the most useful outcome here and must not be softened.

## Question 2: is there a cross-host standard, or competing conventions?

- Is there any real standard for agent skills, or is `AGENTS.md` the only broadly honored
  convention? Distinguish a published spec from a de facto practice from a single vendor's docs.
- Who publishes each convention, how stable is it, and what is its deprecation history?
- If conventions conflict, what do multi-host projects actually do in practice? Cite real
  repositories rather than describing what one could do.

## Question 3: what does the host put in context, and does a POINTER work?

Deliberately narrow, because a companion research prompt covers SKILL.md authoring quality in
depth. Answer only the host-BEHAVIOR half here:

- What does each host actually load into the model's context: the whole `SKILL.md`, only the
  frontmatter, or a summary? Cite the documented or observed behavior.
- Are there enforced size or token limits, and what happens on exceeding them (truncation,
  rejection, silent skip)?
- POINTER VERSUS INLINE, the toolkit's central bet: it refuses to inline instructions, emitting
  `read and execute <path>` and expecting the agent to open that file. Does each host's agent
  reliably FOLLOW such a pointer, or does it answer from the router alone? Any evidence of the
  failure mode matters more than the happy path.
- What safety controls exist around skill files: prompt-injection handling, script-execution
  consent, permission escalation?

## Question 4: is a per-package digest script justified?

The toolkit ships one 20-line `scripts/verify_digest.py` per skill (45 of them), each only
comparing an argument against a baked-in constant. Nothing in the shipped code calls them.

- Do any hosts invoke a script inside a skill package to validate it? If yes, what interface do
  they expect (name, path, arguments, exit codes)?
- Is per-package verification a real convention anywhere, or is a single repository-level
  manifest the normal approach?
- If no host calls them, say so plainly.

## How to answer

- Separate VERIFIED (primary source cited, with version and date) from REPORTED (secondary or
  community) from UNKNOWN. Do not present an inference as a finding.
- Quote the exact path or schema when you cite one; paraphrase loses the detail that matters here.
- Note each host's version or date, since this area changes fast and a stale answer is harmful.
- Where you find nothing, say "no evidence found" rather than filling the gap with plausibility.
- Close with a short ACTIONABLE section: whether `.agents/skills` is justified by evidence, what
  the toolkit should change about its SKILL.md generation, and whether the per-package digest
  script should exist. Keep recommendations traceable to a finding above.
