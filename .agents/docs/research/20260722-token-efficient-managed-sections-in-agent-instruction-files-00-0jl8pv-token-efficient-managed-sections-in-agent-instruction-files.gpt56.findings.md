---
id: 0jl8pv
created: 20260722
set: token-efficient-managed-sections-in-agent-instruction-files
order: 00
topic: []
model: gpt56
kind: findings
status: reference
outcome: informational
summary: Migrated from 20260722-token-efficient-managed-sections-in-agent-instruction-files-00-0jl8pv-token-efficient-managed-sections-in-agent-instruction-files.gpt56.findings.md.
consumed-by: []
---
# Token-Efficient Managed Sections in Agent Instruction Files

**Research finding for:** `agent-workflows` maintainers  
**Research date:** 2026-07-22  
**Scope:** Claude Code, OpenAI Codex, OpenCode, GitHub Copilot, Gemini CLI, Cursor, Windsurf, Kiro, Cline, and the model-provider caching layers most relevant to those hosts  
**Confidence scale:** **High** = official documentation explicitly states the behavior; **Medium** = a direct inference from official documentation or upstream implementation guidance; **Low** = version-sensitive, host-internal, or not independently verified

## Executive summary

### Top recommendations

1. **Use a hybrid delivery architecture, not one universal mechanism.** Keep each directive's full body in a separately owned file. For hosts with native progressive disclosure, generate a host-native skill or conditional rule. Retain a very short, action-bound trigger in the shared always-on file when the behavior must activate at a point that may not be evident from the user's prompt, such as immediately before the agent asks a question. **Confidence: High** for the availability and token behavior of native skills; **Medium** for the relative reliability of the hybrid.

2. **Use one independently marked region per directive.** The recommended portable region is:

   ```markdown
   <!-- aw:ask-user -->
   Before asking the user any question, read and follow `.agents/agent-workflows/directives/ask-user.md`.
   <!-- /aw:ask-user -->
   ```

   The two markers add 43 characters before line endings in this example. They are short, human-readable, robustly parseable, and carry no checksum or release metadata. Claude Code strips block-level HTML comments before injecting `CLAUDE.md`, so these markers cost no Claude context tokens; other hosts do not document equivalent stripping, so their marker cost must be assumed nonzero until tested. [Claude Code explicitly documents HTML-comment stripping.](https://code.claude.com/docs/en/memory) **Confidence: High** for Claude Code; **Low** for comment handling by other hosts.

3. **Put hashes and lifecycle state outside the always-on file.** Store a SHA-256 hash of the last installed normalized section, its stable section ID, template version, consent state, and target file in a toolkit-owned manifest such as `.agents/agent-workflows/managed-sections.json`. Do not put hashes, versions, timestamps, or registries into `AGENTS.md`. **Confidence: High** as an engineering recommendation.

4. **Treat a trigger reference as deferred loading, not free loading.** When the referenced file is read, its content ordinarily enters the conversation or active context and is paid again on later turns, subject to caching and compaction. Claude Code states this explicitly for skills: the body loads only when used, but once loaded it remains in context across turns. [Claude Code skills documentation](https://code.claude.com/docs/en/skills). **Confidence: High** for Claude Code; **Medium** as the normal architecture of the other agent loops.

5. **Do not mistake prompt caching for context reduction.** Caching can cut the metered price and prefill latency of an identical prefix, often to about 10 percent of the ordinary input rate, but the cached tokens still occupy the model's context window, count toward rate limits where documented, and can dilute instruction attention. [Anthropic caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching), and [Gemini caching](https://ai.google.dev/gemini-api/docs/caching). **Confidence: High.**

6. **Persist per-directive consent as a tombstone.** A declined directive must remain `declined` across upgrades until the user explicitly changes it. A manually missing or changed region must be treated as drift, not as permission to reinstall or overwrite. New directives should be offered separately. **Confidence: High** as a lifecycle and consent recommendation.

7. **Never claim that natural-language trigger compliance is guaranteed.** Official documentation consistently describes instruction files as context or guidance, not enforcement. Anthropic expressly says `CLAUDE.md` is context, not enforced configuration, and recommends a hook when an action must be blocked. [Claude Code memory documentation](https://code.claude.com/docs/en/memory). Use hooks or host-enforced policy for safety or compliance boundaries. **Confidence: High.**

8. **Ship a conformance probe.** Trigger-reference efficacy varies by model, host, tool permissions, compaction, and version. The installer should be able to run an opt-in, non-destructive probe that verifies from the tool trace that the owned file was read before the triggering action. **Confidence: High** that probing is necessary; **Medium** on the exact proposed probe design.

### Bottom-line decision

For `agent-workflows`, the best portable baseline is **one minimal comment-delimited trigger region per directive plus one fully owned external directive file and one external lifecycle manifest**. Add **host-native Agent Skills adapters** where supported. Use **conditional or path-scoped host rules** for file-domain behavior. Use **hooks** only where the host supports them and the behavior needs enforcement. Do not use `@import` as a token-saving technique in Claude Code or Gemini CLI because both expand imports into context.

## Key terms and cost model

- **Logical input cost:** tokens presented to the model on a request. These consume context capacity even if served from cache.
- **Metered input cost:** what the provider bills after cache discounts or subscription treatment.
- **Always-on instruction:** content included in every applicable model request or interaction.
- **Trigger reference:** a short always-on instruction that tells the agent to read another file immediately before or when a named condition occurs.
- **Progressive disclosure:** exposing a short name and description first, then loading the full instructions only when selected.
- **Directive:** one independently consented, installed, updated, and removable unit owned by `agent-workflows`.

For a stable instruction block of \(T\) tokens used in \(N\) model calls:

- Without caching, its gross contribution is approximately \(N T\) input tokens.
- With a first write at multiplier \(w\) and \(N-1\) cache reads at multiplier \(r\), its idealized metered cost is \(T(w + (N-1)r)\) base-input-token equivalents.
- At \(w=1.25\), \(r=0.10\), and \(N=20\), the idealized cost is \(3.15T\), 84.25 percent below \(20T\).
- This idealized calculation assumes the block falls inside an eligible identical prefix, the cache stays warm, the host enables caching, the model meets the minimum cacheable-prefix length, and no earlier prompt content changes.

It does **not** mean the block occupies only \(3.15T\) logical tokens. It still appears within the context presented to the model.

---

## 1. Cost mechanics

### 1.1 The common request model

The premise that agent hosts repeatedly provide prior context is correct, but "resend" has two implementations:

1. A stateless API client sends the full system instructions and conversation on each request.
2. A stateful API lets the client pass a prior-response or interaction ID, while the service retrieves the history server-side.

Either way, prior content remains input to the next inference and can remain billable. State storage saves network payload and can improve cache matching; it does not make the model remember without input.

Anthropic explicitly states that its Messages API is stateless and that clients always send the full conversation history. [Anthropic Messages API](https://platform.claude.com/docs/en/build-with-claude/working-with-messages). Claude Code is even more specific: every user message causes a new API request containing the system prompt, project context, prior messages and tool results, and the new message. [Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching). **Confidence: High.**

Google's Interactions API can store history and retrieve it with `previous_interaction_id`, but `system_instruction`, tools, and generation configuration remain interaction-scoped and must be specified again when they should apply. Stateless mode instead sends the full history. [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions-overview). **Confidence: High.**

OpenAI's Responses API similarly supports stateful continuation, while prompt caching operates on exact repeated prefixes. The public Codex documentation establishes how Codex discovers and concatenates `AGENTS.md`, but it does not promise a particular Codex-product billing treatment for those tokens. [Codex `AGENTS.md` documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching). **Confidence: High** for discovery and API caching; **Low** for mapping a given Codex subscription turn to public API token prices.

### 1.2 Host-by-host instruction assembly

| Host | Documented always-on behavior | Scope and on-demand behavior | Caching statement at host level | Confidence |
|---|---|---|---|---|
| Claude Code | Ancestor `CLAUDE.md` and `CLAUDE.local.md` files are concatenated into project context at session start. | Descendant files and path-scoped rules load when matching files are read. Imports expand at launch. | Claude Code automatically manages prompt caching and resends full context each request. | High |
| OpenAI Codex | Builds an instruction chain once per run, concatenating global and project files down to CWD; default combined cap is 32 KiB. | Nested instructions apply by working-directory scope. Skills use progressive disclosure. | OpenAI API caching is documented, but Codex product-level cache and billing details are not publicly guaranteed. | High / Low |
| OpenCode | `AGENTS.md` content is included in LLM context; configured instruction files are combined with it. | Skills load through a native on-demand `skill` tool. Manual lazy file loading is explicitly shown in official guidance. | Depends on selected provider and OpenCode integration; no universal cache guarantee found. | High / Low |
| GitHub Copilot | Relevant custom instructions are automatically added to Copilot requests; agent instructions can use nested `AGENTS.md`. | Path instructions and agent skills are attached when applicable. | No public guarantee found that repository instruction prefixes receive a particular cache discount. | High / Low |
| Gemini CLI | Global, workspace, and parent `GEMINI.md` files are concatenated and sent with every prompt. | Tool access triggers just-in-time discovery of descendant `GEMINI.md`; imports expand content. | Gemini API implicit caching is available, but a Gemini CLI hit is not guaranteed merely because the context file is stable. | High / Medium |
| Cursor | Applied rules are included at the start of model context; root and nested `AGENTS.md` are supported. | Rules can be always, file-glob, model-selected, or manual. | Model/provider and product internals vary; no stable public cache contract found. | High / Low |
| Windsurf | Root `AGENTS.md` is included in Cascade's system prompt on every message. | Descendant `AGENTS.md` uses generated directory globs; skills progressively disclose full content. | No public host-level cache-price contract found. | High / Low |
| Kiro | `AGENTS.md` is always included; default foundational steering is included in every interaction. | Steering supports `fileMatch`, `manual`, and `auto`; skills progressively disclose. | Provider behavior may vary; no Kiro-specific cache guarantee found. | High / Low |
| Cline | Rules are persistent across conversations; without conditionals every rule loads for every request. | Conditional path rules and skills load only when applicable. Cline documents about 100 startup tokens per skill for metadata. | Cline can use different providers, so no universal caching result is possible. | High / High |

Primary host documentation:

- Claude Code: [memory and instruction loading](https://code.claude.com/docs/en/memory) and [prompt caching](https://code.claude.com/docs/en/prompt-caching).
- Codex: [`AGENTS.md` discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md) and [skills](https://learn.chatgpt.com/docs/build-skills).
- OpenCode: [rules](https://opencode.ai/docs/rules/) and [skills](https://opencode.ai/docs/skills/).
- GitHub Copilot: [repository instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions) and [agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).
- Gemini CLI: [`GEMINI.md`](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md).
- Cursor: [rules and `AGENTS.md`](https://cursor.com/docs/rules).
- Windsurf: [`AGENTS.md`](https://docs.windsurf.com/windsurf/cascade/agents-md) and [skills](https://docs.windsurf.com/windsurf/cascade/skills).
- Kiro: [steering](https://kiro.dev/docs/steering/) and [skills](https://kiro.dev/docs/skills/).
- Cline: [rules](https://docs.cline.bot/customization/cline-rules) and [skills](https://docs.cline.bot/customization/skills).

### 1.3 Prompt and context caching

#### Anthropic and Claude Code

Claude Code documents the complete relevant mechanism:

- It makes a new API request on each message and resends full context.
- It orders the stable system prompt and project context before the changing conversation.
- It manages caching automatically unless disabled.
- Project context, including `CLAUDE.md`, is a stable cache layer.
- A normal later turn reads the unchanged prefix from cache and processes the appended exchange.
- On an Anthropic subscription, Claude Code normally requests a one-hour TTL. With API-key or third-party-provider billing, it normally uses the cheaper five-minute TTL.

[Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching). **Confidence: High.**

Anthropic's API rates cache reads at 0.1 times normal input, five-minute writes at 1.25 times, and one-hour writes at 2 times. Minimum cacheable prefix length varies by model from 512 to 4,096 tokens in the current documentation. [Anthropic prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching). **Confidence: High.**

Implication: a 20-token managed trigger may be served inside a much larger cached prefix even though it is below the minimum by itself. The relevant threshold applies to the complete prefix through the cache breakpoint, not to the managed section alone. **Confidence: High.**

#### OpenAI and Codex

OpenAI prompt caching:

- is automatic for eligible prompts on recent models;
- requires an exact prefix match;
- begins at 1,024 tokens;
- reports `cached_tokens` and, for GPT-5.6 and later families, `cache_write_tokens`;
- uses a 1.25 times write rate for GPT-5.6 and later;
- keeps GPT-5.6-family prefixes eligible for at least 30 minutes under the current default TTL;
- does not remove cached tokens from token-per-minute limits.

[OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching). **Confidence: High.**

As of the research date, GPT-5.6 Sol lists ordinary input at $5.00 and cached input at $0.50 per million tokens, a 90 percent cached-input discount, with writes at 1.25 times ordinary input. [GPT-5.6 Sol model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol). **Confidence: High.**

Codex's documented project-instruction cap is 32 KiB by default. At the rough engineering heuristic of 3 to 5 UTF-8 English characters per token, 32 KiB is approximately 6,500 to 10,900 tokens, but this is not an official tokenizer guarantee and code-heavy content can tokenize less favorably. [Codex `AGENTS.md` documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md). **Confidence: High** for 32 KiB; **Low** for the cross-model token estimate.

No official Codex documentation found in this review promises that a stable `AGENTS.md` block will always receive API-style cache pricing in every Codex surface or subscription. Treat that as observable product behavior, not an installer invariant. **Confidence: Medium.**

#### Google and Gemini CLI

The Gemini Interactions API enables implicit caching by default for Gemini 2.5 and newer. Current minimums listed are 2,048 tokens for Gemini 2.5 Flash and Pro and 4,096 for Gemini 3.5 Flash and Gemini 3.1 Pro Preview. Google recommends large common content at the beginning and similar-prefix requests close in time. [Gemini context caching](https://ai.google.dev/gemini-api/docs/caching). **Confidence: High.**

Current Gemini API pricing commonly lists cached context at one-tenth of standard input for the representative current text models, with explicit-cache storage charged separately where explicit cache objects are used. [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing). Interactions API implicit caching does not require manually created cache objects. **Confidence: High.**

Gemini CLI states that it concatenates hierarchical context and sends it with every prompt, which makes a stable prefix possible. It does not state that every CLI request will hit the provider cache. [Gemini CLI context files](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md). **Confidence: High** for repeated inclusion; **Medium** for likely cache eligibility; **Low** for any particular hit rate.

#### Multi-provider hosts

OpenCode and Cline can use different providers. Cursor, Windsurf, Kiro, and Copilot may route across models and commercial plans. Their repository-instruction documentation does not expose a general, version-stable cache-price contract. Therefore:

- count always-on content as recurring logical context on all calls;
- model monetary savings only when the actual host, provider, model, authentication method, and usage telemetry are known;
- measure cache hits where the provider exposes them.

**Confidence: High** as a conservative accounting rule.

### 1.4 Published size guidance is not a "typical size"

No representative, current cross-repository corpus establishing a typical `AGENTS.md` or `CLAUDE.md` token size was found in official sources. Published limits and recommendations are:

- Codex: 32 KiB combined project-document cap by default. [Source](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
- Claude Code: target fewer than 200 lines per `CLAUDE.md`; longer files consume more context and reduce adherence. [Source](https://code.claude.com/docs/en/memory).
- GitHub Copilot's generated repository-instructions prompt says no longer than two pages. [Source](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions).
- Cursor: keep rules under 500 lines and split large rules. [Source](https://cursor.com/docs/rules).
- Cline: rules consume context; avoid lengthy explanations and entire style guides. [Source](https://docs.cline.bot/customization/cline-rules).

These are ceilings or authoring guidance, not measurements of real-world typical files. **Confidence: High.**

---

## 2. Trigger references and just-in-time files

### 2.1 Passive reference versus action-bound trigger

A passive reference is descriptive:

```markdown
Question guidelines: `.agents/agent-workflows/directives/ask-user.md`
```

It does not tell the model when or whether to read the file. Some hosts may render it as a path, some may attach it, and others may leave it as literal text.

An action-bound trigger is operational:

```markdown
Immediately before asking the user any question, read and follow `.agents/agent-workflows/directives/ask-user.md`.
```

It names:

1. an observable precondition;
2. the required action;
3. the exact file;
4. the authority to give the loaded content.

This is more likely to be followed than a passive link, but it remains model-followed guidance unless the host provides enforcement. **Confidence: Medium.**

### 2.2 What official sources establish

#### Claude Code

Claude Code says `CLAUDE.md` and memory are context, not enforced configuration, and that concise, specific instructions are followed more consistently. It recommends a `PreToolUse` hook to block an action regardless of model choice. [Memory documentation](https://code.claude.com/docs/en/memory). **Confidence: High.**

Claude's `@path` syntax is **not lazy**. Imported files are expanded and loaded at launch; the documentation explicitly says imported files still enter the context window at launch. [Memory documentation](https://code.claude.com/docs/en/memory). **Confidence: High.**

Claude skills are genuinely progressive:

- the skill body loads only when used;
- the model can select a skill from its description, or the user can invoke it explicitly;
- supporting files can remain unloaded until needed;
- after the skill loads, its content stays in context across turns.

[Claude Code skills](https://code.claude.com/docs/en/skills). **Confidence: High.**

For "before asking any question," a skill description may not match the user's task because asking a question is an internal phase, not necessarily the user's stated intent. A short always-on action trigger therefore remains useful even when a skill carries the full procedure. **Confidence: Medium.**

#### OpenAI Codex

Codex loads applicable `AGENTS.md` before work. Codex skills begin with name, description, and path, and load full `SKILL.md` only when selected. Selection can be explicit or based on the description. [Codex `AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Codex skills](https://learn.chatgpt.com/docs/build-skills). **Confidence: High.**

The public docs do not promise that a natural-language instruction to read file Y when condition X occurs will always cause the read. The official best practice is to test prompts against skill descriptions. **Confidence: High** that selection is model-mediated; **Low** for a universal trigger success rate.

#### OpenCode

OpenCode does not automatically parse `@file` references in `AGENTS.md`. Its official rules page shows an explicit manual instruction teaching the model to use its Read tool and lazy-load referenced files based on need. This is unusually direct upstream support for the trigger-reference pattern. [OpenCode rules](https://opencode.ai/docs/rules/). **Confidence: High** that the pattern is officially recommended; **Medium** that it will be obeyed on any specific run.

OpenCode also has native skills loaded on demand through the `skill` tool, with only name and description listed until selection. [OpenCode skills](https://opencode.ai/docs/skills/). **Confidence: High.**

#### Gemini CLI

Gemini CLI has two distinct mechanisms:

- `@file.md` imports modularize authoring but expand into the concatenated context. They are not documented as lazy.
- descendant `GEMINI.md` files are discovered just in time when a tool accesses a file or directory, which is true host-controlled conditional loading.

[Gemini CLI context files](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md). **Confidence: High.**

A natural-language trigger to read an arbitrary directive file remains model-mediated. A nested `GEMINI.md` is host-triggered only by filesystem access, not by an abstract event such as "about to ask a question." **Confidence: High.**

#### Cursor

Cursor rules may be always applied, attached by file glob, selected by the agent from a description, or manually mentioned. Cursor recommends referencing files instead of copying them because that keeps rules short and current. It also supports `@filename` in rules. [Cursor rules](https://cursor.com/docs/rules). **Confidence: High.**

The documentation does not establish whether every referenced file is lazy-loaded, nor does it quantify model-selection reliability. Treat `@filename` token behavior as host-version-sensitive and test it. **Confidence: Low.**

#### Windsurf

Windsurf root `AGENTS.md` content is included in every Cascade message. Its skills expose only name and description until Cascade invokes them, while workflows are manual slash-command templates. [Windsurf `AGENTS.md`](https://docs.windsurf.com/windsurf/cascade/agents-md), [Windsurf skills](https://docs.windsurf.com/windsurf/cascade/skills). **Confidence: High.**

For user-intent-aligned tasks, skills are the efficient native choice. For an internal pre-action event, a short always-on trigger remains the more direct reminder. **Confidence: Medium.**

#### Kiro

Kiro supports:

- always, file-match, manual, and description-based auto inclusion for steering files;
- Agent Skills with name/description discovery, full-instruction activation, and reference files loaded as needed.

[Kiro steering](https://kiro.dev/docs/steering/), [Kiro skills](https://kiro.dev/docs/skills/). **Confidence: High.**

Auto selection still depends on matching the user's request to a description. Use a trigger line for action-phase behavior that is not reliably visible in the request. **Confidence: Medium.**

#### Cline

Cline gives unusually concrete token guidance:

- about 100 startup tokens per enabled skill for name and description;
- full `SKILL.md` under 5,000 tokens when triggered;
- supporting resources read only as needed;
- always-active rules consume context, while path conditions avoid unrelated loads.

[Cline skills](https://docs.cline.bot/customization/skills), [Cline rules](https://docs.cline.bot/customization/cline-rules). **Confidence: High.**

#### GitHub Copilot

Copilot automatically adds relevant repository instructions to requests. Its skills are chosen based on the prompt and skill description, after which `SKILL.md` is injected. GitHub recommends custom instructions for short, nearly universal behavior and skills for detailed instructions needed only when relevant. [Copilot instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions), [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills). **Confidence: High.**

The same internal-phase limitation applies: a generic task prompt may not semantically match a skill about how to ask a question. **Confidence: Medium.**

### 2.3 What is not established

No public, controlled, cross-host benchmark was found that measures:

- whether an agent reads a named file immediately before an abstract trigger;
- false negatives across long sessions and after compaction;
- false-positive reads when the trigger never occurs;
- behavior across the named hosts using the same model and prompt set.

Vendor documentation supports progressive disclosure and precise instructions, but it does not supply a universal compliance percentage. Any numerical trigger reliability asserted without a host/version/model test would be false precision. **Confidence: High.**

### 2.4 Reliability ranking

From highest to lowest expected reliability:

1. **Host-enforced hook or policy** that intercepts the relevant tool/action.
2. **Explicit user invocation** of a skill or command.
3. **Host-controlled file/path conditional rule.**
4. **Native skill selected from a precise description matching the user's request.**
5. **Short always-on action-bound trigger telling the model to read a file.**
6. **Passive path reference.**

Items 3 through 5 can change order for a particular host and task. For internal action phases, item 5 can outperform item 4 because the user prompt may not match the skill. **Confidence: Medium.**

### 2.5 Required empirical probe

`agent-workflows` should test each supported host/version with:

- **positive trials:** the task requires the agent to ask a question, but the user's prompt does not mention the directive or its vocabulary;
- **negative trials:** the task is fully specified and should not read the directive;
- **late-trigger trials:** the question occurs after several tool calls;
- **multi-turn trials:** the question occurs on a later user turn;
- **post-compaction trials:** where the host supports compaction;
- **nested-scope trials:** run from the repository root and a subdirectory;
- **permission trials:** file read allowed, denied, and approval-required;
- **subagent trials:** where a child context may not inherit the same loaded material.

Record:

1. whether a read/skill tool call occurred;
2. whether it occurred before the triggering action;
3. whether the final behavior complied with the loaded directive;
4. input, cached-input, and cache-write tokens where exposed;
5. host, host version, model, provider, auth mode, and instruction filename.

A minimum useful release gate is multiple prompt families with repeated runs, not one golden prompt, because model outputs are nondeterministic. **Confidence: High.**

---

## 3. Token-efficient managed-section formats

Token estimates below are approximate because hosts use different tokenizers. Character overhead is deterministic. Scores assume one directive per region and exclude the directive text itself.

| Format | Example | Marker overhead | Human readability | Machine parseability | Main issues |
|---|---|---:|---:|---:|---|
| Short HTML comments | `<!-- aw:x -->` ... `<!-- /aw:x -->` | 27 characters plus line endings for ID `x` | High | High | Some hosts may include comments as tokens; Claude strips block comments |
| Verbose HTML comments | `<!-- agent-workflows:begin id=x -->` ... | Typically 70-110 characters | High | High | Unnecessary recurring metadata |
| Markdown headings | `## agent-workflows:x` ... | One marker unless a terminator convention is added | High | Medium | Section end can be ambiguous when users insert headings |
| XML-like visible tags | `<aw id="x">` ... `</aw>` | Roughly 20-35 characters | Medium | High | Visible prompt syntax may influence model interpretation |
| Fenced region | ```` ```agent-workflows x ```` ... ```` ``` ```` | Roughly 25-40 characters | Medium | High | Makes instructions look like inert code to some models |
| YAML front-matter registry | Top-of-file list of IDs, offsets, versions, hashes | Commonly 100+ characters before content | Medium | Medium | One global structure, merge conflicts, hashes consume tokens, offsets are brittle |
| Inline checksum attributes | Marker contains ID, version, SHA-256 | Commonly 90+ characters per section pair | Medium | High | Solves a non-prompt problem inside the prompt |

### 3.1 Recommended delimiter

Use:

```markdown
<!-- aw:<stable-id> -->
<one short trigger or directive>
<!-- /aw:<stable-id> -->
```

Requirements:

- ASCII only.
- Stable, lowercase, kebab-case ID.
- One marker per line.
- Exact closing marker.
- No nesting.
- No version, hash, timestamp, package version, or consent state inline.
- Installer rejects duplicate IDs and unmatched markers.
- IDs are never reused for a semantically different directive.

This format minimizes overhead while keeping the target visible to maintainers. Claude Code's documented comment stripping makes it especially efficient there. [Claude Code memory documentation](https://code.claude.com/docs/en/memory). **Confidence: High.**

### 3.2 Why not a single monolithic block

A single toolkit block saves only one marker pair. It loses:

- independent consent;
- independent removal;
- per-directive drift detection;
- safe update of unchanged directives while preserving modified ones;
- clean release retirement;
- stable blame and diagnostics.

The few tokens saved by one pair of markers do not justify the lifecycle loss. **Confidence: High** as an engineering tradeoff.

### 3.3 Why not fences

Fences are structurally parseable, but models often interpret fenced content as quoted data or code rather than operative instructions. This is task- and model-dependent, but there is no advantage over HTML comment boundaries for an executable directive. **Confidence: Medium.**

### 3.4 Why not a front-matter registry

Front matter is valuable when a host itself interprets it, as in Cursor rules, Kiro steering, Cline conditional rules, and GitHub path instructions. It is inefficient as a registry for regions inside a shared `AGENTS.md` because:

- it puts machine metadata into always-on context;
- it creates one contention point with user-owned front matter;
- offsets break after unrelated edits;
- hashes and versions provide no behavioral value to the model.

Use host-native front matter in separate host-owned adapter files, not as the shared-file ownership ledger. **Confidence: High.**

---

## 4. Modification and drift detection without heavy tokens

### 4.1 External-manifest design

Recommended manifest:

```json
{
  "schema": 1,
  "package_version": "X.Y.Z",
  "sections": {
    "ask-user": {
      "target": "AGENTS.md",
      "state": "accepted",
      "template_version": 3,
      "installed_sha256": "<hash>",
      "source": ".agents/agent-workflows/directives/ask-user.md",
      "source_installed_sha256": "<hash>"
    }
  }
}
```

This file is not referenced by the always-on instruction file and should not be loaded into model context. It can be richer without recurring token cost.

### 4.2 Hash the managed payload, not the whole shared file

The installer should:

1. locate exactly one opening and closing marker;
2. extract only the bytes between them;
3. normalize line endings;
4. compare SHA-256 with `installed_sha256`.

Do not hash all of `AGENTS.md`; user edits elsewhere are expected. Do not rely on line offsets because unrelated edits move sections. **Confidence: High.**

### 4.3 Normalization

Recommended canonicalization:

1. decode as UTF-8, rejecting or explicitly preserving an unsupported encoding;
2. convert CRLF and bare CR to LF;
3. preserve all other characters, blank lines, indentation, and trailing spaces;
4. define consistently whether the extracted payload ends with one LF, and apply that same rule on install and verification.

Avoid broad whitespace normalization, Markdown reformatting, Unicode compatibility folding, or trimming all trailing spaces. Those can hide meaningful user changes, especially in Markdown code blocks. **Confidence: High.**

Optionally store two hashes:

- an **exact canonical hash** used to detect any edit;
- a **semantic-display hash** used only to suppress noise in a human diff.

The exact hash remains authoritative. **Confidence: Medium.**

### 4.4 Marker integrity states

The parser should return explicit states:

- `absent`: neither marker exists;
- `intact-unchanged`: one matched pair and payload hash equals installed hash;
- `intact-modified`: one matched pair and payload hash differs;
- `duplicate`: more than one opening or closing marker for the ID;
- `orphan-open`;
- `orphan-close`;
- `misordered`;
- `nested-or-overlapping`;
- `wrong-target`: manifest target and discovered location disagree.

Only `intact-unchanged` is safe for unattended replacement or removal. **Confidence: High.**

### 4.5 Handling fully owned external files

The external directive file is toolkit-owned, but users may still edit it. Apply the same three-way logic:

- hash the last installed external content;
- compare it before upgrade;
- update automatically only if unchanged;
- if modified, offer keep, adopt as local customization, replace, or merge.

A "toolkit-owned" label is not permission to destroy user changes. **Confidence: High.**

### 4.6 Inline checksums are not justified

An inline SHA-256 digest costs roughly 64 hexadecimal characters plus syntax per directive and contributes nothing to model behavior. It also changes whenever the directive changes, disrupting prompt-prefix caching earlier than necessary if the metadata is placed before stable content. Keep it external. **Confidence: High.**

---

## 5. Granular consent and cross-release lifecycle

### 5.1 Consent state machine

Use stable per-directive states:

- `accepted`: user allowed installation and standard upgrades;
- `declined`: user explicitly declined; do not offer again on routine upgrades;
- `customized`: installed content differs and user chose to keep/adopt it;
- `pending`: newly available directive not yet decided;
- `retired`: upstream directive removed but lifecycle record retained;
- `blocked-drift`: markers or content are inconsistent and need resolution.

The state belongs in the external manifest or consent store, never in the always-on file. **Confidence: High.**

### 5.2 Decline tombstones

When a user declines a directive:

- store the stable ID, declined state, scope, and optional package version;
- do not create markers or the external directive file solely to represent the decline;
- do not silently re-add on upgrade;
- provide an explicit command to reconsider declined directives;
- preserve the tombstone when uninstalling content unless the user requests a full purge.

If the directive is renamed, release metadata must migrate the tombstone from the old stable ID to the new ID. Never evade a decline by issuing a new ID for materially the same directive. **Confidence: High.**

### 5.3 Team versus local consent

Support two scopes:

- **Repository consent:** tracked with the repository and intended as team policy.
- **Local consent override:** gitignored or stored in toolkit user state, for a user's local host choices.

Define precedence explicitly. A safe default is that a local decline can prevent local installation but cannot delete a repository-owned directive from version control without an explicit edit. **Confidence: Medium**, because repository governance varies.

### 5.4 Release operations

#### Adding a directive

- create a new stable ID;
- mark `pending`;
- ask separately unless the user previously enabled an explicit "accept future directives" policy;
- show the short always-on cost and the full owned file before consent.

#### Updating a directive

- if region and external file are unchanged from their recorded hashes, update atomically;
- if either is modified, perform a three-way comparison using last-installed, local, and new-upstream content;
- offer keep local, replace, merge, or decline future management.

#### Removing a directive upstream

- if unchanged, remove its region and owned file, then retain a retired record;
- if modified, do not delete automatically; explain that upstream retired it and offer keep-unmanaged or remove;
- never reuse its ID.

#### User removes a region manually

- treat absence as drift, not consent to reinstall;
- offer: confirm removal and record `declined`, restore, or leave unresolved;
- do not silently repair during a routine upgrade.

#### Moving a directive

- use release migration metadata mapping old target and ID to the new location;
- verify the old content is unchanged before deleting;
- insert the new form transactionally;
- retain aliases for diagnostics and decline migration.

### 5.5 Atomicity and recovery

Before mutating shared files:

1. parse and validate all target files;
2. compute all changes in memory;
3. show a per-directive plan;
4. write temporary files in the same filesystem;
5. replace atomically where supported;
6. retain a recoverable backup or version-control-friendly patch;
7. update the manifest only after file writes succeed.

This prevents the manifest from claiming a state the shared file never reached. **Confidence: High.**

### 5.6 Why granular blocks beat a monolith

| Lifecycle event | Monolithic block | Per-directive regions |
|---|---|---|
| Decline one directive | Requires editing owned block or rejecting all | Native |
| Upgrade unchanged directive | Whole-block comparison | Independent |
| Preserve one customization | Blocks all automatic updates | Only that directive blocks |
| Retire one directive | Rebuild and replace block | Remove one matched pair |
| Detect drift | Whole-block hash says only "something changed" | Exact affected ID |
| Explain token cost | Aggregate only | Per directive |

**Confidence: High.**

---

## 6. Alternative approaches

### 6.1 Separate files with host-native eager imports

Examples: Claude Code `@path` and Gemini CLI `@file.md`.

**Advantages:** clean ownership, modular files, easy updates and hashing.  
**Disadvantages:** the imported content is expanded into startup context, so token cost is the same as inlining, apart from negligible syntax differences.  
**Use when:** modular maintainability matters and the content truly should be always on.  
**Do not use when:** the goal is just-in-time token savings.

**Confidence: High.**

### 6.2 Agent Skills

As of 2026, progressive-disclosure skills are documented by Claude Code, Codex, OpenCode, GitHub Copilot, Windsurf, Kiro, and Cline. Several support the open Agent Skills format. Host directories still differ:

- Codex: `.agents/skills/`
- OpenCode: `.agents/skills/`, `.opencode/skills/`, and Claude-compatible locations
- GitHub Copilot: `.agents/skills/`, `.github/skills/`, or `.claude/skills/`
- Windsurf: `.windsurf/skills/` and `.agents/skills/`
- Claude Code: `.claude/skills/`
- Kiro: `.kiro/skills/`
- Cline: `.cline/skills/`, `.clinerules/skills/`, or `.claude/skills/`

Sources: [Codex](https://learn.chatgpt.com/docs/build-skills), [OpenCode](https://opencode.ai/docs/skills/), [Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills), [Windsurf](https://docs.windsurf.com/windsurf/cascade/skills), [Claude Code](https://code.claude.com/docs/en/skills), [Kiro](https://kiro.dev/docs/skills/), [Cline](https://docs.cline.bot/customization/skills). **Confidence: High.**

Skills are the strongest broadly available 2026 mechanism for task-level workflows. They are less reliable for an internal action phase unless the description or an always-on trigger makes the need salient. Generate adapters from one canonical directive rather than hand-maintaining divergent copies. **Confidence: Medium.**

### 6.3 Commands and workflows

Manual slash commands are highly reliable once invoked and have little recurring context cost. They are unsuitable for behavior that must happen automatically without the user remembering a command. Windsurf explicitly distinguishes manual workflows from model-selected skills. Claude Code has merged custom commands into skills while preserving manual invocation. [Windsurf skills](https://docs.windsurf.com/windsurf/cascade/skills), [Claude Code skills](https://code.claude.com/docs/en/skills). **Confidence: High.**

### 6.4 Conditional and path-scoped rules

These are preferable for behavior tied to files or directories:

- Claude `.claude/rules/` with `paths`;
- Gemini descendant `GEMINI.md` JIT discovery;
- Cursor globs;
- Windsurf nested `AGENTS.md` and rule globs;
- Kiro `fileMatch`;
- Cline `paths`;
- GitHub `.github/instructions/*.instructions.md` with `applyTo`.

They reduce unrelated recurring context and are host-controlled after file matching. They do not express non-file events such as "before asking a question." **Confidence: High.**

### 6.5 Out-of-repository or user-scope instructions

User/admin scope avoids modifying the repository's shared file and can apply across repositories. It is poor as the default delivery vehicle for a repository-installed toolkit because:

- it is not normally versioned with the repository;
- remote/cloud agents may not see a local user's files;
- uninstall and upgrade need machine-level coordination;
- team consent and reproducibility become harder.

Use it for personal preferences or centrally managed organizational policy, not ordinary `agent-workflows` project directives. **Confidence: High.**

### 6.6 Hooks and enforced policy

Hooks can intercept lifecycle events or tool calls and can enforce a rule independently of model attention. They offer the highest behavioral reliability and near-zero prompt cost, but have poor cross-host portability and may require scripts, permissions, and host-specific event names. Use them for hard safety controls or where a host exposes the exact action, not as the only portable installation strategy. Claude's documentation explicitly contrasts context guidance with `PreToolUse` enforcement. [Claude Code memory documentation](https://code.claude.com/docs/en/memory). **Confidence: High.**

### 6.7 Remote URLs and provider retrieval

OpenCode can load remote instruction URLs through configuration, but remote dependency availability, trust, latency, mutability, and offline behavior make it inappropriate for a core directive that must be release-reproducible. Pinning immutable content improves integrity but not cross-host support. [OpenCode rules](https://opencode.ai/docs/rules/). **Confidence: High.**

---

## Comparison table

Scores are 1 to 5, where 5 is best. "Delivery reliability" means behavioral delivery under its intended trigger, not security enforcement. Scores are reasoned recommendations, not benchmark measurements.

| Approach | Recurring token cost | Delivery reliability | Maintainability / section management | Drift detection | Cross-host portability | Notes |
|---|---:|---:|---:|---:|---:|---|
| Monolithic inline block | 1 | 4 | 1 | 2 | 5 | Always visible but expensive and all-or-nothing |
| Full per-directive inline regions | 2 | 4 | 5 | 5 | 5 | Best inline lifecycle, but full recurring cost |
| Short trigger regions plus owned files | 5 before trigger; 3 after load | 3 | 5 | 5 | 5 | Recommended portable baseline; must be probed |
| Eager native imports | 1 | 4 | 5 | 5 | 2 | Modular, not token-saving |
| Host-native path rules | 5 when unrelated | 4 | 4 | 5 | 2 | Excellent for file-scoped behavior |
| Auto-selected Agent Skills | 5 before trigger | 4 for user-intent tasks; 3 for internal phases | 5 | 5 | 3 | Best 2026 workflow mechanism; adapter paths differ |
| Explicit skills / commands | 5 until invoked | 5 after invocation | 5 | 5 | 3 | Requires user action |
| Hooks / enforced client policy | 5 | 5 | 3 | 4 | 1 | Use for hard guarantees |
| User/admin-scope instruction files | 2-4 | 4 | 3 | 4 | 2 | Good for personal or organizational scope |
| Remote instruction URL | 2-4 | 2 | 4 | 4 | 1 | Network and trust risks |

---

## 7. Concrete recommended architecture for `agent-workflows`

### 7.1 Repository layout

```text
.agents/
└── agent-workflows/
    ├── managed-sections.json
    ├── consent.local.json              # optional, gitignored
    ├── directives/
    │   ├── ask-user.md
    │   ├── planning.md
    │   └── review.md
    ├── skills/
    │   ├── ask-user/
    │   │   └── SKILL.md                # generated adapter
    │   └── review/
    │       └── SKILL.md
    └── generated/
        ├── claude/
        ├── kiro/
        └── cline/
```

The canonical full directive lives in `directives/<id>.md`. Host adapters should be generated deterministically from the canonical directive and host metadata. Avoid maintaining multiple hand-edited copies.

### 7.2 Shared-file region

For behavior that must be considered at an internal action phase:

```markdown
<!-- aw:ask-user -->
Immediately before asking the user any question, read and follow `.agents/agent-workflows/directives/ask-user.md`.
<!-- /aw:ask-user -->
```

For a directive naturally matched by a user's request and supported by a native skill, a still cheaper region may point to the skill:

```markdown
<!-- aw:review -->
For code-review tasks, use the `agent-workflows-review` skill.
<!-- /aw:review -->
```

Do not install a trigger region for every available directive automatically. Ask per directive and omit regions for workflows that are explicitly invoked or reliably path-scoped.

### 7.3 Directive classification

At package build time, classify each directive:

| Class | Example | Preferred delivery |
|---|---|---|
| Universal short invariant | "Do not edit generated files" | Short inline directive |
| Internal action trigger | "Before asking a question..." | Short action-bound trigger plus owned file; optional hook |
| User-intent workflow | "Review this PR" | Agent Skill |
| File/domain rule | TypeScript or docs conventions | Path-scoped native rule |
| Manual operation | Release/deploy runbook | Explicit skill or command |
| Hard safety boundary | Block secret publication | Hook or enforced policy plus concise reminder |

This prevents overusing the trigger-reference pattern.

### 7.4 Manifest record

Each directive record should include:

- stable ID;
- current source version;
- target host and shared instruction filename;
- marker strings;
- canonicalized installed payload hash;
- external-file installed hash;
- consent state and scope;
- adapter paths and hashes;
- predecessor IDs for migrations;
- upstream status: active, deprecated, retired;
- last resolution: accepted, declined, kept-local, replaced, merged.

No field needs to appear in `AGENTS.md`.

### 7.5 Installation algorithm

1. Discover host instruction files without assuming `AGENTS.md` is universal.
2. Parse existing managed regions and manifest.
3. Detect drift before presenting new choices.
4. Show each directive separately with:
   - short always-on text;
   - approximate recurring token range;
   - full referenced file;
   - delivery method per detected host.
5. Record accept or decline per stable ID.
6. Generate canonical files and host adapters.
7. Insert one non-nested region per accepted always-on trigger.
8. Validate marker uniqueness and host adapter syntax.
9. Write atomically.
10. Offer an opt-in conformance probe.

### 7.6 Upgrade algorithm

For each known stable ID:

1. Read consent and retirement state.
2. If declined, do nothing unless the user explicitly requested reconsideration.
3. If accepted and unchanged, update automatically or include it in a concise upgrade summary according to installer policy.
4. If modified, stop automatic replacement for that directive only.
5. If missing, treat as drift and ask whether removal means decline.
6. If retired upstream, remove only unchanged content.
7. Apply ID migration aliases before evaluating whether a directive is new.
8. Continue upgrading unrelated unchanged directives.

This is the principal advantage over a monolithic block.

### 7.7 Host adapters

Recommended adapter priority:

1. **`.agents/skills/` canonical adapter** for Codex, OpenCode, GitHub Copilot, and Windsurf where current versions support it.
2. **Generated `.claude/skills/` adapter** for Claude Code and Cline compatibility.
3. **Generated `.kiro/skills/` adapter** for Kiro.
4. **Host-native conditional rule** only when the directive has a file/path predicate.
5. **Shared-file action trigger** for non-file internal events.

Because host support changes quickly, maintain a capability table keyed by tested minimum version. Detect, do not assume.

### 7.8 Cache-aware placement

Place stable managed regions near other stable project instructions, before volatile or frequently generated content. Exact-prefix caches are invalidated from the first changed point onward. Do not rewrite timestamps, package versions, or hashes inside the prefix on every install. [Anthropic caching prefix behavior](https://platform.claude.com/docs/en/build-with-claude/prompt-caching), [OpenAI exact-prefix behavior](https://developers.openai.com/api/docs/guides/prompt-caching). **Confidence: High.**

### 7.9 Token budget policy

Suggested installer guardrails:

- target 15 to 30 tokens for a trigger sentence;
- target fewer than 15 approximate tokens total for both short marker lines where the tokenizer does not strip them;
- require explicit justification above 50 tokens of always-on content per directive;
- display aggregate installed always-on characters and estimated token range;
- never pad a file merely to cross a provider's cache threshold;
- prefer deterministic scripts for validation or calculation because their source need not enter context.

The token ranges must be labeled estimates unless counted with the exact host model tokenizer. **Confidence: High.**

### 7.10 Security and trust

An instruction to read a toolkit-owned file increases that file's authority. Therefore:

- keep the path inside the repository;
- verify package provenance and content hashes;
- do not follow arbitrary nested references from user-modifiable files without limits;
- do not grant shell permission merely because a skill asks for it;
- treat external directive edits as drift;
- show the file content at consent time.

GitHub warns that skills can contain prompt injection or malicious scripts and recommends previewing them before installation. [Copilot agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills). **Confidence: High.**

---

## 8. Findings requiring empirical validation

The following must not be hard-coded as facts:

1. HTML comments are token-free outside Claude Code.
2. Cursor's `@filename` reference is always lazy.
3. A stable instruction prefix receives a cache hit in Codex, Copilot, Cursor, Windsurf, Kiro, OpenCode, Cline, or Gemini CLI on every later turn.
4. A model-selected skill fires for an internal action trigger not mentioned by the user.
5. A referenced file read remains active across compaction in every host.
6. Subagents inherit root instruction files and already loaded directive content identically.
7. Host subscription usage accounting equals public API token pricing.
8. All supported host versions recognize `.agents/skills/`.

`agent-workflows` should publish the tested host version and date next to each capability rather than describing support as timeless.

---

## Confidence-rated citation list

### High-confidence official and upstream sources

1. **Claude Code, "How Claude remembers your project."** Establishes startup loading, hierarchy, eager `@path` imports, descendant on-demand rules, instruction-length guidance, HTML-comment stripping, and the distinction between guidance and enforcement.  
   https://code.claude.com/docs/en/memory

2. **Claude Code, "How Claude Code uses prompt caching."** Establishes a new request per message, full-context resend, project-context cache layering, automatic host caching, TTL behavior, cache invalidation, and skill injection behavior.  
   https://code.claude.com/docs/en/prompt-caching

3. **Anthropic, "Prompt caching."** Establishes cache-read and write multipliers, cacheable content, TTLs, exact-prefix behavior, and per-model minimum token thresholds.  
   https://platform.claude.com/docs/en/build-with-claude/prompt-caching

4. **Anthropic, "Using the Messages API."** Explicitly states that the Messages API is stateless and the full conversational history is sent.  
   https://platform.claude.com/docs/en/build-with-claude/working-with-messages

5. **Claude Code, "Extend Claude with skills."** Establishes progressive disclosure, automatic and explicit invocation, supporting-file loading, and the fact that loaded skill content remains in context across turns.  
   https://code.claude.com/docs/en/skills

6. **OpenAI, "Custom instructions with AGENTS.md."** Establishes once-per-run discovery, concatenation order, scope, overrides, and the default 32 KiB cap.  
   https://learn.chatgpt.com/docs/agent-configuration/agents-md

7. **OpenAI, "Build skills."** Establishes name/description/path discovery, full-body on-demand loading, explicit and implicit invocation, context-list limits, and supported repository skill locations.  
   https://learn.chatgpt.com/docs/build-skills

8. **OpenAI, "Prompt caching."** Establishes automatic eligibility, 1,024-token minimum, exact-prefix requirement, current GPT-5.6 write behavior, retention, usage fields, and rate-limit treatment.  
   https://developers.openai.com/api/docs/guides/prompt-caching

9. **OpenAI, "GPT-5.6 Sol Model."** Establishes current ordinary and cached input prices and cache-write multiplier for the named model.  
   https://developers.openai.com/api/docs/models/gpt-5.6-sol

10. **OpenCode, "Rules."** Establishes `AGENTS.md` inclusion, instruction-file configuration, lack of automatic reference parsing, and the official manual lazy-loading pattern.  
    https://opencode.ai/docs/rules/

11. **OpenCode, "Agent Skills."** Establishes on-demand loading via the native skill tool and `.agents/skills/` discovery.  
    https://opencode.ai/docs/skills/

12. **GitHub, "Adding repository custom instructions for GitHub Copilot."** Establishes automatic attachment to requests, nested `AGENTS.md`, path-specific instructions, and current precedence.  
    https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions

13. **GitHub, "Adding agent skills for GitHub Copilot."** Establishes skill directories, prompt/description selection, `SKILL.md` injection, `.agents/skills/`, update provenance, and security warnings.  
    https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills

14. **Google Gemini CLI, "Provide context with GEMINI.md files."** Establishes concatenation with every prompt, hierarchical and just-in-time directory discovery, eager imports, and filename customization.  
    https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md

15. **Google, "Interactions API."** Establishes stateful versus stateless conversation handling, repeated `system_instruction`, and cache benefits of stateful continuation.  
    https://ai.google.dev/gemini-api/docs/interactions-overview

16. **Google, "Context caching."** Establishes default implicit caching, minimum token thresholds, similar-prefix guidance, and usage telemetry.  
    https://ai.google.dev/gemini-api/docs/caching

17. **Google, "Gemini Developer API pricing."** Establishes current standard and cached-context prices and explicit-cache storage prices.  
    https://ai.google.dev/gemini-api/docs/pricing

18. **Cursor, "Rules."** Establishes persistent prompt-level context, four rule activation modes, `AGENTS.md`, nested rules, and file references.  
    https://cursor.com/docs/rules

19. **Windsurf, "AGENTS.md."** Establishes per-message root inclusion and directory-glob behavior for nested files.  
    https://docs.windsurf.com/windsurf/cascade/agents-md

20. **Windsurf, "Skills."** Establishes progressive disclosure, automatic/manual invocation, `.agents/skills/` compatibility, and the distinction among skills, rules, and workflows.  
    https://docs.windsurf.com/windsurf/cascade/skills

21. **Kiro, "Steering."** Establishes always, file-match, manual, and auto inclusion modes and always-included `AGENTS.md`.  
    https://kiro.dev/docs/steering/

22. **Kiro, "Agent Skills."** Establishes name/description startup discovery, full-instruction activation, and references loaded as needed.  
    https://kiro.dev/docs/skills/

23. **Cline, "Rules."** Establishes persistent rule loading, supported `AGENTS.md`, per-rule toggles, conditional path activation, and token-cost guidance.  
    https://docs.cline.bot/customization/cline-rules

24. **Cline, "Skills."** Establishes approximately 100 startup metadata tokens per skill, under-5,000-token body guidance, on-demand body loading, and resource loading.  
    https://docs.cline.bot/customization/skills

### Medium-confidence syntheses

1. **Action-bound triggers should outperform passive references.** This follows from vendor guidance favoring specific, actionable instructions and from OpenCode's official lazy-loading example, but no cross-host controlled rate is published.
2. **A hybrid trigger plus native skill is best for internal action phases.** Native skills are documented; the superiority of the hybrid for a pre-question event requires testing.
3. **Loaded read-tool content normally persists in later context outside Claude Code.** This follows from standard agent transcript construction, but only Claude Code's current documentation was found to state the recurring effect with comparable specificity.
4. **Stable always-on regions are likely cacheable inside a larger prefix.** Provider caching rules support this, but an individual commercial host can change the request or decline to enable provider caching.

### Low-confidence or explicitly unverified claims

1. Exact token counts for the proposed markers across all host/model tokenizers.
2. Cache-hit rates for Codex, Copilot, Cursor, Windsurf, Kiro, OpenCode, Cline, and Gemini CLI product sessions.
3. Trigger-reference compliance percentages.
4. Cursor file-reference lazy-loading semantics across versions.
5. HTML-comment stripping outside Claude Code.
6. Exact subscription-dollar savings attributable to one repository instruction section.

---

## Final recommendation

Adopt the following as the `agent-workflows` default:

1. one stable ID per directive;
2. one short HTML-comment-delimited region per accepted always-on trigger;
3. one fully owned canonical external file per directive;
4. native progressive-disclosure skill adapters where supported;
5. native path rules for file-scoped directives;
6. external SHA-256 hashes and consent tombstones;
7. no inline version, checksum, timestamp, or registry metadata;
8. no silent overwrite, repair, re-addition, or ID reuse;
9. host/version capability detection;
10. opt-in behavioral and cache telemetry probes.

This architecture minimizes recurring prompt text without pretending that deferred model behavior is guaranteed. It also makes every directive independently identifiable, consented, addable, removable, editable, updateable, and drift-detectable, which is the central lifecycle requirement.
