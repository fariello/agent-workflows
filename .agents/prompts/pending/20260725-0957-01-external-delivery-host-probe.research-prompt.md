You are a research assistant with web access and, where possible, hands-on access to current AI coding-agent host applications. Produce a rigorous, current, citation-backed report answering one question for each host below: can that host reliably RESOLVE and then FOLLOW agent-workflows instruction/workflow content that does NOT live in the working repository, or that lives in a host-native skill file? Return your answer as a single downloadable Markdown (`.md`) file.

## Background you need

A tool-agnostic framework installs reusable "agent workflows" into a repo. Today it writes, into the repo, a small pointer block in the root `AGENTS.md` and per-command shim files whose body is literally `Read and execute @.agents/workflows/<path>`; the workflow bodies live in the repo under `.agents/workflows/`. The maintainer wants to reduce per-repo footprint by delivering that content from OUTSIDE the repo instead, using one of three tiers:

- T1 (out-of-repo pointer): a shim/pointer references a path OUTSIDE the repo tree (for example a pip-packaged data directory, or an absolute path on disk) rather than an in-repo copy.
- T2 (host-native skill): a file at `.agents/skills/<name>/SKILL.md` that the host AUTO-DISCOVERS and can run as a skill, with NO explicit in-repo pointer to it.
- T3 (home-dir/global): the content lives at a home-dir/global location (for example an XDG data dir) referenced globally.

The load-bearing uncertainty is that the HOST application (not the model) decides file discovery, and behavior varies per host and per host version. A passive out-of-repo pointer may be resolved but not followed; a host may auto-discover `SKILL.md` on one version and not another. The maintainer will not build any tier on an unproven assumption, so this report is the evidence gate.

## Hosts to cover

OpenCode, Claude Code, Codex (OpenAI), GitHub Copilot / VS Code Copilot, Cursor, Google Antigravity, Gemini CLI. Add any other widely used coding-agent host you find relevant, clearly labeled.

## What to determine, per host (and per host version where behavior differs)

For each host, report with explicit version numbers and dates, and cite official docs, changelogs, or reproducible tests:

1. T1 - Out-of-repo pointer. Does the host resolve a reference (in its instruction/rules file or a command/shim) to a path OUTSIDE the working repo (an absolute path, a home-dir path, or a packaged data path)? If it resolves the reference, does it then FOLLOW an instruction that only that out-of-repo content supplied? Distinguish "resolved" (the content was loaded/attached) from "followed" (the host acted on it).
2. T2 - Host-native skills. Does the host natively auto-discover `.agents/skills/<name>/SKILL.md` (or an equivalent skills path) WITHOUT an explicit pointer, and act on it? State the exact path(s) and any setting required to enable it. Note if the host uses a different skills path (for example `.claude/skills/`).
3. T3 - Home-dir/global. Does the host resolve and follow instruction/workflow content placed at a home-dir/global location? What is the exact location, and does enabling it require mutating a user-global config file (a consent concern)?
4. Precedence and shadowing. If both in-repo and out-of-repo/global content exist, which wins? Can an out-of-repo directive be silently overridden by an in-repo file (or vice versa)?
5. Reliability caveats. Note any known cases where discovery is inconsistent across versions, requires a flag, depends on the model, or is documented as best-effort rather than guaranteed.

## How to answer

- Prefer primary sources (official docs, release notes, source) and dated, reproducible tests over blog hearsay; note the date and version of every claim, and flag anything you could not verify.
- Where you can actually run the host, describe the exact fixture you placed (path + a unique side-effect instruction such as "create a file named PROBE-OK.txt") and whether the side effect occurred; report "resolved" and "followed" separately.
- Be explicit about NEGATIVE and UNKNOWN results; "this host does not appear to follow out-of-repo pointers as of version X (date)" is a valuable finding.

## Required deliverable format (return as a downloadable `.md` file)

1. An executive summary: for each host, a one-line verdict per tier (T1/T2/T3): Followed / Resolved-not-followed / Not-resolved / Unknown, with the host version and date.
2. A per-host x per-tier results table with columns: Host, Version, Tier, Resolved?, Followed?, How verified (doc/test), Notes, Date.
3. Per-host detail sections expanding each row with citations.
4. A short "recommendations and caveats" section: which tiers look safe for which hosts today, and where the evidence is too thin to build on.
5. A list of every source with URL and access date.

Return the complete report as one downloadable Markdown (`.md`) file.
