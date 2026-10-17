# Communication and concise reporting contract (model-authored prose)

terseout Order 01 (`ntf6sx`), askmeplain Order 01 (`er11a0`).

Coding agents invoked directly or through agent-workflows must communicate clearly without
relying on unexplained jargon or internal identifiers, and tend to spend tokens on preambles,
narration of routine actions, praise, recaps, and closing offers. This contract installs
clear, plain-language communication as a default across all authored documents (internal
artifacts included) and makes concise, essential-information-only reporting the portable
default across the hosts this project targets, WITHOUT weakening the work, the tests, or
the evidence.

The contract text itself is owned by ONE module:

```text
agent_workflows/reporting_contract.py
```

Read it there. This page describes WHERE it is delivered, WHAT overrides it, and WHY the
alternatives were rejected. It deliberately does not restate the contract prose, so the two
cannot drift.

## What the default asks for

Write for a capable engineer who has not seen the work: someone who knows the field but not this
repository, this session, or what the agent just found. Say what a thing does before naming it, and
explain each technical term, project name, or identifier the first time it appears.

Explain a failure or a blocker as the steps that happened, in order: what was observed, what caused
it, what that led to, and what fixes it. When the cause is not verified, say so rather than stating a
mechanism. Open with what happened, not with a verdict.

When the user says "plain version" or "I don't understand", the agent rewrites its previous message
in full for that reader, without defending or adding to it. The `/plain` command does the same.

For routine status reports: lead with the outcome, answer a yes/no question with `Yes.` or `No.`,
drop preambles, narration, recaps and closing offers, report only material outcomes, changed files,
verification status and blockers, and keep the report short. The word cap never limits an
explanation of a failure or blocker, a question, a recommendation, or anything the reader needs to
understand or decide.

Why it reads this way: research answering prompt `ng0ga4` (reports `8tcq84`, `o7v25q`, `ky28a9`,
`ne3jy6`, 2026-10-17) found that a list of style adjectives does not change how an agent writes, that
a named reader and a concrete order for explanations are the most useful rules, that the word cap must
explicitly exempt explanations, and that the user's own "plain version" correction is the one remedy
observed to work. None of the four found evidence that any written rule is sufficient on its own.

## What overrides it

1. **An explicit user request.** If the user asks for detail, give detail.
2. **A controlling workflow that specifies a required report.** `plan-review` mandates a full
   findings table and an enumeration it calls the literal final output; `release-review`,
   `plan-review-long`, and `exec-set` carry comparable required reports. Those reports are
   produced IN FULL and the word cap does not apply to them. Be concise only in the prose
   around them.
3. **Completeness obligations.** Required evidence (including actual pasted runner output),
   safety warnings, destructive-action confirmations, structured outcomes and their required
   keys, and durable artifacts (code, tests, plans, specs, docs) stay complete. Concision
   governs reporting, never analysis, implementation, testing, or correctness.

Saying less is not permission to do less.

## Where it is delivered (per host)

| Host | Delivery surface |
| --- | --- |
| OpenCode | the installed `AGENTS.md#aw:reporting` managed section, plus a pointer line in every `.opencode/commands/*.md` shim, plus the `aw oc run` execution and verifier prompts |
| Codex CLI | the installed `AGENTS.md#aw:reporting` managed section |
| Claude Code | a pointer line in every `.claude/commands/*.md` shim, plus the `aw:reporting` section in an EXISTING `CLAUDE.md` |
| Antigravity (Agy) | the `aw agy run` execution and verifier prompts, plus `AGENTS.md` (the host's pointer file) |

`aw:reporting` is a separately owned managed section, so a repository may decline it (a
tombstone in `.aw/system/managed-sections.json`) or hand-edit its body, and the installer will
not clobber the edit. Declining or editing it does not affect the sibling `aw:pointer` section.

### Command shims carry a pointer, not a copy

Generated command shims carry ONE line naming `AGENTS.md#aw:reporting`. They do not embed the
contract prose. The reason is arithmetic: the prose is about 1.7KB and there are 48 generated
shim files totaling about 42.7KB, so copying it into each shim would grow the corpus by roughly
80 percent, and that growth is re-read on EVERY command invocation. A mechanism whose input
cost exceeds the output tokens it saves defeats its own purpose. A size-budget test enforces
this, so the decision cannot silently regress into duplication.

Accepted trade-off, stated plainly: a host that loads a shim without resolving the pointer gets
a weaker signal than embedded prose would give. The pointer line therefore also names the most
important exception (required reports still in full) inline.

### Driver prompts carry the full prose

Both IPD drivers embed the contract in full in their execution and verifier prompts. A fresh
non-interactive worker must not depend on ambient host instructions, which is why those prompts
already embed the other critical safeguards (the concurrent-work rules, the outcome schema, the
never-push rule).

### The review turn inherits it

A review turn's prompt is exactly `/plan-review <path>` and is handed to the host as a single
argument, so anything appended to that string is parsed as additional path arguments. Nothing
is appended. The review session inherits the contract from the command shim's pointer plus the
installed `AGENTS.md` section.

## Rejected alternatives

- **Editing global user configuration** (`~/.config/opencode/AGENTS.md`, `~/.claude/CLAUDE.md`,
  Codex home configuration). A repository installer must not overwrite personal cross-project
  preferences.
- **Provider-specific verbosity fields** (OpenAI `textVerbosity`, temperature, Claude output
  style selection). Not portable across all four hosts, and silently absent where unsupported.
- **A low output-token limit or any truncation.** Truncation can cut off an error, an evidence
  paste, or a JSON outcome. The contract asks for fewer words, never for a severed response.
- **Reducing reasoning effort, tool use, test scope, or verifier rigor.** Out of scope by
  construction; concision applies to reporting only.
- **Reshaping `aw` CLI output.** That is governed separately by
  [CLI Output Mode Contract](cli-output-contract.md). This contract governs model-authored
  communication across all authored documents (internal artifacts included) and user-facing
  prose; neither may be read as licensing fewer JSONL fields.

## Honest limits

Delivery is deterministic and tested: the managed section, the shim pointers, and both drivers'
prompts are asserted byte-wise, and a parity test fails if any surface carries a second
independently maintained copy. Compliance is NOT deterministic. These are probabilistic models,
so the tests prove the instruction arrives, not that it is obeyed. A live smoke matrix across
hosts is a maintainer activity, not a gate: an unavailable host is recorded as not run, never
as pass.
