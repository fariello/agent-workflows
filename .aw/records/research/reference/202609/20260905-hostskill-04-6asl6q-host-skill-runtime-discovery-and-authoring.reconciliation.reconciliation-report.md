---
id: 6asl6q
created: 20260920
set: hostskill
order: 04
topic: [skills, hosts, discovery]
model: reconciliation
kind: reconciliation-report
status: reference
outcome: none-yet
summary: Consolidated finding across GPT-5.6 Sol High, Sonnet 5 High and Gemini 3.1 Pro Deep Think: .agents/skills is a real shipped discovery path in at least seven hosts and is NOT aspirational, the per-package verify_digest.py is called by nothing and should go, and the Antigravity directory name is UNRESOLVED (plural vs singular) pending an empirical test on opencode, codex, agy, claude and hermes
consumed-by: []
---

# What agent skill runtimes actually discover: consolidated finding

Synthesis of the three independent reports answering prompt `sx0cqv`. This is the document an
implementer should read; the three sources stay in the set for provenance.

| Source | id6 | Model | Read the live code or docs? |
|---|---|---|---|
| 01 | `xecyn0` | GPT-5.6 Sol High | YES. Cites a named repo commit (`4763eb8d`), per-host release tags and dated doc fetches; labels every claim VERIFIED / REPORTED / UNKNOWN |
| 02 | `wknvyw` | Sonnet 5 High | PARTLY, and says so up front: fetched vendor docs directly, but could NOT read this repository (GitHub tree/blob returned `ROBOTS_DISALLOWED`, no network egress to clone) |
| 03 | `i5gj61` | Gemini 3.1 Pro Deep Think | NO for primary sources. Its own author's note records that network restrictions prevented reading the repository; several citations carry no version or date |

READ THE EVIDENCE COLUMN BEFORE WEIGHTING AGREEMENT. Two of the three could not verify parts of
what they assert, so on any contested point a 2-versus-1 majority may only mean two models shared
one assumption. That is not a hypothetical caution here; see the Antigravity finding below.

## Finding 1: `.agents/skills` is real and shipped, NOT aspirational

The prompt's decisive question was whether `.agents/skills` is a convention no shipped host reads.
IT IS NOT. All three reports independently answer that it is a genuine, currently-scanned discovery
path, and the two that fetched vendor docs directly each name the hosts and cite the pages.

Hosts that scan it, per the two direct-fetch reports: OpenCode, OpenAI Codex, Cursor,
Windsurf/Devin, GitHub Copilot, Gemini CLI, and Zed. For Zed it is the ONLY documented skills
directory; for Cursor and Codex it is listed first rather than as a compatibility shim.

Hosts that do NOT scan it: Claude Code and Claude.ai (verified negative), Kiro, Cline. Aider and
Continue expose no comparable loader in the sources reviewed.

This VINDICATES the toolkit's existing directory choice (`host_adapters.py:60`
`SHARED_SKILLS_DIR = ".agents/skills"`, `engine.py:174` `SKILLS_DIR`) and RETIRES the hedge in its
own code comments and spec, which described the path only as "an emerging portable path" and so read
as aspirational. It is evidenced now. The mapping of Claude and Kiro to native directories is also
correct and must stay, since those two genuinely do not read the shared path.

Two qualifications that matter. FIRST, there is a published Agent Skills package-format
specification, and it deliberately does NOT define discovery locations; `.agents/skills` is
interoperability guidance in the separate client-implementation guide, not a normative requirement.
So this is a strong de facto convention, not a standard the toolkit can cite as binding. SECOND, it
is RECENT: where introduction could be verified, adoption clusters between 2026-01 and 2026-05
(Codex 0.94.0 on 2026-02-02, OpenCode 1.1.50 on 2026-02-04, Gemini CLI 0.28.0 on 2026-02-10,
Windsurf 1.9552.21 on 2026-02-12, Zed 1.3.5 on 2026-05-20). A convention that young can still move,
so this finding carries a shelf life and should be re-checked rather than treated as settled.

## Finding 2: the Antigravity directory name is UNRESOLVED

THE SOURCES CONTRADICT EACH OTHER, and one character decides whether Antigravity sees anything this
toolkit writes: PLURAL `.agents/skills/` versus SINGULAR `.agent/skills/`.

- `xecyn0` says PLURAL is the native workspace path and singular is legacy. Cites Antigravity docs,
  IDE build 2.12.2, accessed 2026-09-05.
- `i5gj61` says SINGULAR with plural as an alias. Cites "Google Antigravity GitHub documentation,
  mid-2026" with no version or date, from a report that could not read primary sources.
- `wknvyw` says SINGULAR ONLY, explicitly "not the plural `.agents/skills/` convention", and adds a
  detail neither other source reports: a filed bug (Antigravity 1.19.6) where the agent's own system
  prompt omits the global skills path, so globally installed skills reach the model not at all.

NO RESOLUTION IS RECORDED HERE, and that is deliberate. This is a question about another vendor's
shipped behavior; this repository can prove only what it WRITES, never what Antigravity READS. The
two sources that agree are the two with the weaker evidence, so the majority is not decisive.

MAINTAINER RULING, 2026-09-20: record it unresolved and settle it EMPIRICALLY. The required test is
an actual install checked against at least these five hosts: opencode, codex, agy (Antigravity),
claude, and hermes. Until that test is run and its output recorded, treat BOTH spellings as
possible and do not let either into a design decision as though it were established.

## Finding 3: the per-package digest script is dead, and is already gone

All three reports answer the prompt's Question 4 identically and without hedging: NO host invokes a
script inside a skill package to validate it. Per-package runtime verification is a convention
nowhere; hosts validate by parsing frontmatter, and registries use server-side hashes. A `scripts/`
directory is for AGENT-invoked scripts, which means a script no SKILL.md tells the model to run is
unreachable by construction.

THIS RESEARCH DID NOT DRIVE THE FIX, AND SAYING SO IS THE POINT. Plan `8fhjjc` removed the scripts
on 2026-09-05, BEFORE these answers arrived, on a maintainer ruling that explicitly declined to wait
for `sx0cqv`: a generated file with no caller, no computation, and no read of its own package is not
an interface. Verified at HEAD today: zero `verify_digest.py` files exist, and
`host_adapters.py:369` records that the package "deliberately emits NO per-package verification
script". So this finding CONFIRMS a shipped decision rather than prompting one. That plan's own
instruction for this outcome stands: had the research found a host that DOES invoke package scripts,
the correct response would have been a new plan building a real verifier, never a revert.

## Finding 4: the pointer bet is unproven, and the SECOND hop is the weak link

The toolkit refuses to inline workflow instructions, emitting `read and execute <path>` and relying
on the agent to open it. The honest verdict is UNKNOWN LEANING PLAUSIBLE, not verified.

What the evidence supports: the IN-PACKAGE pointer (a `SKILL.md` referencing a file in its own
directory) is exactly what every host's authoring guidance recommends, and `wknvyw` found a real
tool-call trace confirming an agent following one. No report found evidence of a host FAILING to
follow a well-written pointer.

What nothing supports: this toolkit's pattern is a SECOND hop, out of the package to a body
elsewhere in the repo. No host documentation and no study addresses multi-hop or out-of-package
pointer following. No vendor publishes reliability numbers, so this reduces to general
instruction-following under long context and competing instructions, which is unmeasured.

Also worth carrying: the failure mode reported in practice is not refusal to open the file, it is
that the agent loads the WHOLE file once it does, which is a context-cost problem rather than a
reliability one. And `wknvyw` observed that this repository's real shipped mechanism is
`AGENTS.md` plus `/command` shims pointing into `.agents/workflows/`, with skill packages a second
layer on top; it reached that from the README alone, having been unable to read the tree, so treat
it as a reading of the public description and not a code measurement.

## What an implementer should do

1. KEEP `.agents/skills` and stop hedging about it in code comments and specs (Finding 1).
2. KEEP the native-directory mapping for Claude and Kiro; they really do not read the shared path.
3. DO NOT resolve Antigravity from these reports. Run the five-host empirical test (Finding 2).
4. NOTHING to do on the digest script; already removed by `8fhjjc` (Finding 3).
5. TREAT the two-hop pointer as unproven. If a workflow body is load-bearing, a same-directory copy
   removes an indirection that no evidence covers (Finding 4).
6. RE-CHECK Finding 1 on a cadence. The convention is months old, not years.
