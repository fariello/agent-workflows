---
id: 2mpcqb
created: 20260823
set: agentadhere
order: 02
topic: [agent-adherence, enforcement, hooks, ci, lifecycle]
model: gpt56medium
kind: research-report
status: reference
outcome: adopted
summary: Why soft prose fails; defense-in-depth for heterogeneous coding agents (ChatGPT 5.6 Sol Medium)
consumed-by: [79li67]
---

# Reliable Process Adherence for Heterogeneous Coding Agents

**Research report for the maintainers of `agent-workflows`**
**Research current through:** 2026-08-23
**Scope:** Claude Code, OpenAI Codex, OpenCode, Gemini CLI, Google Antigravity, Cursor, Kiro, Git, and host-independent repository controls

## 1. Executive summary

The most effective realistic strategy is to stop treating agent compliance as a memory problem and instead encode every important invariant in the narrowest deterministic boundary that all agents eventually cross. For `agent-workflows`, that means a single `aw` policy engine used by lifecycle commands, a low-friction `aw commit`/`aw finish` path, Git and CI checks over repository evidence, and protected-branch enforcement; host-specific pre-tool and stop hooks should add timely reminders, route agents to those commands, and catch mistakes earlier, but should not be the source of truth. Prose remains useful for orientation and semantic judgment, but it is not an enforcement mechanism: controlled long-context studies find position-dependent retrieval failures, and tool-agent benchmarks show that even strong models following supplied policy documents are inconsistent across repeated trials. Full local prevention is impossible when the agent has unrestricted shell access, writable policy artifacts, Git-hook bypasses, and the same credentials as the user; strong guarantees require moving at least one gate or signing authority outside the agent's authority boundary. The practical target is therefore **easy compliance, deterministic detection, fail-closed integration, and explicit residual risk**, not perfect obedience from the model.

## 2. Root-cause analysis: why soft prose directives fail

### 2.1 Presence in context is not retrieval at the decision point

**Measured evidence.** Liu et al.'s controlled “Lost in the Middle” experiments found a U-shaped use-of-context curve: relevant information was used best near the beginning or end and substantially worse in the middle. In one multi-document setting, GPT-3.5-Turbo performance fell by more than 20 percentage points depending on information position, and at its worst was below the 56.1% closed-book baseline. Merely extending the model's advertised context window did not reliably improve its use of information already fitting in the shorter window ([Liu et al., 2023](https://arxiv.org/html/2307.03172v3)). This is not a direct experiment on `AGENTS.md`, but it establishes the relevant mechanism: inclusion in a prompt is not equivalent to reliable retrieval and application.

**Inference for `agent-workflows`.** An always-loaded instruction such as “run `aw ipd finalize` before marking the plan done” competes with the user's immediate request, tool output, source code, error messages, and the model's learned coding routine. The rule must be retrieved exactly when the agent is about to edit a status, write implementation code, commit, or stop. A rule encountered once at session start is weakly coupled to those later decision points, especially after many turns or context compaction.

### 2.2 Instructions compete with observed patterns and generic learned habits

**Measured evidence.** A controlled 2026 study of instruction-induction conflict placed an explicit target instruction before a growing sequence of assistant turns demonstrating a competing behavior. Across 13 models and 16 instruction types, models increasingly drifted toward the demonstrated pattern. Explicitly warning models to disregard the hardcoded pattern improved mean instruction following by 14 percentage points in one condition and 11 in another, but adherence still reached only 41% and 54%, respectively. The paper also observed “deliberation-output dissociation,” in which a model reasoned toward the instructed behavior and nevertheless emitted the competing pattern ([Do as I Say, Not as I Do, 2026](https://arxiv.org/html/2605.20382v2)).

**Inference for `agent-workflows`.** Models have extensive learned priors for `git add`, direct Markdown edits, coding immediately after receiving a task, and reporting summarized test results. They have little or no training on `aw set`, `aw ipd begin`, or `aw ipd finalize`. The repository instruction competes with a far more frequently reinforced behavior. This explains why an agent may accurately restate the rule when asked yet fail to execute it under task pressure: declarative recognition and action selection are different events.

### 2.3 Long-horizon success is multiplicative, not additive

If a workflow has six independently remembered steps and an agent performs each with 90% probability, the probability of completing all six is only $0.9^6 \approx 53\%$. Independence is an oversimplification, but the calculation illustrates why apparently “high” per-step compliance yields poor end-to-end reliability.

**Measured evidence.** In τ-bench, agents received domain-specific policy documents and API tools, yet the best evaluated function-calling model in the original study achieved about 61% single-run success in retail and 35% in airline tasks. Its probability of succeeding consistently across eight retail trials, `pass^8`, fell to about 25% ([Yao et al., 2024](https://arxiv.org/html/2406.12045)). A broader 2026 reliability study across 14 models concluded that reliability gains lag capability gains; agents often select similar action types while varying execution order, and semantically equivalent prompt reformulations still affect results ([Kapoor et al., 2026](https://arxiv.org/html/2602.16666v2)). These benchmarks do not test this toolkit, but they directly test policy-following and multi-step tool use.

### 2.4 Salience and recency help, but remain probabilistic

Just-in-time context is better positioned than a session-start rule because it makes the relevant instruction recent and directly names the pending action. Host documentation itself reflects this design: Codex, Claude Code, Gemini CLI, Cursor, Kiro, and Antigravity now expose pre-tool events capable of injecting context or blocking a call. This is vendor engineering evidence that lifecycle placement matters, not a controlled cross-host estimate of adherence improvement.

A pre-tool message such as the following is materially better than repeating the entire workflow guide:

> Direct status edits are invalid. Run `aw set <status> <id>`. For a terminal IPD transition, run `aw ipd finalize <id>`; it will validate evidence and write the transition.

It still fails if the host does not expose the action, the agent writes through an unobserved path, the hook is disabled or untrusted, or the model retries with another primitive. A deterministic `deny` plus an actionable alternative is stronger than additional context alone.

### 2.5 Prose has no authority over the environment

An instruction can ask an agent not to hand-edit `Status:`; it cannot make the file unwritable, make an invalid state transition unrepresentable, prevent `git commit --no-verify`, or remove push credentials. The core distinction is therefore not “better wording versus worse wording.” It is **advice versus authority**. A model-controlled choice remains probabilistic. Code that rejects an invalid transition is deterministic for calls that reach it. A remote required check is authoritative for merges when bypass is disabled.

## 3. Mechanism landscape

The effectiveness ratings below distinguish published measurements from engineering judgment. There is little controlled research that compares these exact mechanisms on coding agents, so claims about relative effectiveness are labeled **inference** unless supported by a paper or vendor contract.

| Mechanism | Prevent or detect | Deterministic? | Portable? | Friction | Principal failure mode | Evidence and expected effectiveness |
|---|---|---:|---|---|---|---|
| Always-loaded prose (`AGENTS.md`, `CLAUDE.md`, rules files) | Prevention by persuasion | No | Broad concept, host-specific filenames and loading rules | Low until the file becomes long | Rule is not retrieved; competes with task and learned habits; compaction or scope rules alter loading | **Measured:** long-context position affects retrieval; policy-following agents remain inconsistent. Useful orientation, weak enforcement. Codex documents hierarchical `AGENTS.md` discovery ([OpenAI](https://learn.chatgpt.com/docs/agent-configuration/agents-md)). |
| Trigger-referenced or just-in-time prose | Prevention by salience; can aid correction | No | Requires host adapter or wrapper error | Low if narrow and event-specific | Trigger is absent, incomplete, or bypassed; agent ignores context | **Inference:** better than session-start prose because it is adjacent to the decision, but still model-dependent. |
| Host pre-tool hook returning context only | Prevention by steering | No | Host-specific | Low | Hook misses alternate tool/path; model chooses another primitive | Vendor-supported on several hosts. Treat as an ergonomic aid, not a gate. |
| Host pre-tool hook returning `deny` | Prevention | Deterministic for covered calls | Host-specific adapters | Low when precise; high if broad | Hook disabled/untrusted; unsupported tool path; parser evasion; fail-open crash; agent uses direct process or different host | Strong early gate **within documented coverage**. Codex explicitly warns specialized paths can opt out; Cursor defaults hook failures to fail-open unless configured otherwise. |
| Host command permission rules | Prevention | Deterministic for matched command/tool | Host-specific | Medium if patterns prompt too often | Coarse wildcard matching; shell quoting/wrappers; user grants broad approval; config not loaded | Good for denying raw `git push` or `git commit`, weaker for enforcing complex repository semantics. |
| Replace/wrap the primitive (`aw finalize`, `aw commit`, `aw test`) | Prevention and evidence creation | Yes for calls through wrapper | High: ordinary executable | Lowest when one command completes all required substeps | Agent bypasses wrapper and invokes raw primitive | **Recommended default path.** It eliminates remembered substeps and gives one place for invariants and teaching errors. |
| Make derived state non-editable in the data model | Prevention of malformed states; detection of tampering | Yes when state is computed from validated events | High | Low | Agent directly forges events or edits verifier code unless authority is external | Stronger than a mutable `Status:` field. Cryptographic provenance is only strong if the key is outside agent reach. |
| Local Git `pre-commit` / `pre-push` hook | Prevention before local boundary | Yes when installed and executed | High across Git clients that honor hooks | Low to medium | Hooks are not cloned automatically, may not be installed, and `pre-commit` can be bypassed with `--no-verify`; agent can alter local hooks | Useful fast feedback, not a security boundary ([Git hooks documentation](https://git-scm.com/docs/githooks)). |
| `aw check` / `aw doctor` over repository artifacts | Detection and actionable correction | Yes for encoded invariants | Very high | Low when fast and incremental | Cannot infer invisible intent, authorship, actual test execution, or who owned a dirty file; forged evidence can pass naive checks | Essential common engine. Run inside commands, hooks, and CI rather than relying on agents to remember it. |
| CI required status check / server-side receive gate | Detection plus merge prevention | Yes for decidable checks | Host-independent at repository level; configuration varies by forge | Low after setup | Direct pushes/bypass actors; detector blind spots; workflow/config changes may weaken gate | Strongest practical repository boundary. GitHub can require status checks and disallow bypass ([GitHub Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)). |
| Credential broker or remote transition service | Prevention and trustworthy attribution | Yes | High conceptually; requires infrastructure | Medium | Service unavailable; credential delegation complexity; local work still possible but cannot be accepted/pushed | Required for strong “never push without authorization” or non-forgeable lifecycle attestations. |
| Separate fresh-context agent review | Detection and correction | No | Broad if another agent can inspect the repo | Medium cost/latency | Correlated model blind spots; verifier accepts plausible fabricated evidence; same context or model reduces independence | Useful for semantic completeness and contradiction detection. It must not replace deterministic checks. Current reliability research treats correlated multi-agent failures as an open problem, not a solved guarantee ([Kapoor et al., 2026](https://arxiv.org/html/2602.16666v2)). |
| Human approval at critical boundary | Prevention/detection | Human-dependent | Broad | High if frequent | Automation bias, rushed approval, alert fatigue, unclear evidence | Reserve for high-consequence, low-frequency decisions. Repeated low-value alerts encourage overrides; clinical alert-fatigue literature is domain-specific but supports minimizing noisy interruptions ([Backman et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC10983371/)). |

## 4. Recommended architecture for `agent-workflows`

### 4.1 Design goal and threat model

The architecture should provide three explicitly different assurance levels:

1. **Convenience assurance:** an ordinary, cooperative agent is guided into the correct path.
2. **Repository assurance:** invalid or unsupported artifact states cannot pass `aw check` or required CI.
3. **Authority assurance:** an agent with broad local shell and write access still cannot forge approval, provenance, or a protected remote transition.

The first two are achievable within an open-source repository toolkit. The third requires an authority the agent cannot modify or impersonate, such as protected CI configuration, a server-side app, a signing service, a credential broker, or human approval enforced by the repository host. A local file, hash chain, Git hook, environment variable, or secret readable by the agent is not an independent authority.

### 4.2 One policy engine, many entry points

Implement a single library and CLI command, conceptually `aw check`, with machine-readable findings:

```json
{
  "schema_version": 1,
  "result": "fail",
  "findings": [
    {
      "code": "AW-IPD-TERMINAL-EVIDENCE-MISSING",
      "severity": "error",
      "artifact_id": "abc123",
      "message": "IPD abc123 cannot enter done: no successful test run is bound to the current tree.",
      "next_command": "aw test --for abc123 -- <project-test-command>"
    }
  ]
}
```

Every enforcement surface should call the same engine:

- `aw set`, `aw ipd begin`, `aw ipd finalize`, `aw commit`, and `aw finish` call it internally.
- A repository-installed Git hook calls a fast staged-tree subset.
- Host adapters call it before relevant write or shell tools and at agent stop.
- CI calls the complete comparison against the merge base and fails a required check.
- A fresh verifier consumes its JSON findings instead of re-deriving deterministic facts in prose.

This prevents policy drift among seven host adapters.

### 4.3 Replace editable lifecycle state with validated events

The canonical lifecycle state should be derived from structured transition events, not trusted from a freely editable `Status:` line. A transition event should include at least:

- schema version;
- artifact ID and artifact content digest;
- prior and next state;
- transition kind (`set`, `begin`, `finalize`, `abandon`, and so on);
- tool version;
- actor claim and actor-source type;
- UTC timestamp generated at execution;
- repository HEAD and worktree digest or declared base;
- evidence references and their digests;
- previous-event digest for tamper-evident ordering.

The rendered Markdown `Status:` can be regenerated from the journal for readability. `aw check` should fail if rendered state differs from derived state, a terminal state lacks a valid transition, history is internally inconsistent, an event refers to a later or unrelated tree, or required fields are generic.

**Limit:** A hash chain detects accidental/manual edits but does not prove authenticity when the agent can rewrite the whole chain. Strong attribution requires a signature from a key or remote identity unavailable to the agent. Git commit signatures prove control of a signing key, not that the `aw` CLI rather than a hand edit produced the event.

### 4.4 Make each desired action atomic

Do not require the agent to remember `check`, then update, then write history, then move, then finalize. Each high-level command should perform one transaction:

```text
aw work begin <id> --scope <paths...>
  -> validates an approved/reviewed IPD
  -> records base tree and declared scope
  -> creates or selects an isolated worktree when configured
  -> writes one begin event

aw test --for <id> -- <runner and arguments...>
  -> streams unmodified runner output
  -> stores command, exit code, output digest, timestamp, and tree digest
  -> returns the runner's exit code

aw commit <id> -- <paths...>
  -> rejects undeclared or foreign paths
  -> runs the staged-tree policy check
  -> commits only explicit pathspecs
  -> records the resulting commit digest

aw ipd finalize <id>
  -> checks current state, scope, required evidence, and terminal invariants
  -> writes attributed transition/history event
  -> regenerates the readable artifact
  -> performs the move, if movement is still part of the storage model
  -> revalidates the resulting tree
```

Make `aw finish <id>` a convenience orchestrator that reports exactly what is missing and, when safe, invokes `aw test`, `aw commit`, and `aw ipd finalize` in sequence. It should never fabricate missing evidence.

### 4.5 Layered enforcement

#### Layer A: portable deterministic core

This is the source of truth and should work in a plain terminal without an agent host.

- State-machine library and append-only transition schema.
- `aw check --staged`, `aw check --range <base>..<head>`, and `aw check --worktree`.
- Atomic lifecycle commands.
- Captured test evidence bound to a tree digest.
- Declared task scope and base tree.
- Optional one-task-per-worktree isolation.
- `aw commit` with explicit pathspecs.
- Stable finding codes, JSON output, human explanation, and a next command.

#### Layer B: portable local integration

- Installer-managed `core.hooksPath` or a hook dispatcher, with conflict-safe chaining rather than overwriting user hooks.
- `pre-commit`: run `aw check --staged`; reject lifecycle inconsistencies and files outside declared scope.
- `commit-msg` or `prepare-commit-msg`: bind task/artifact ID without requiring the agent to invent syntax.
- `pre-push`: warn or block when no authorization marker exists.

These improve early feedback, but local Git documentation explicitly states that `pre-commit` can be bypassed with `--no-verify`; local hooks must not be described as non-bypassable ([Git](https://git-scm.com/docs/githooks)). The installer should verify hook activation in `aw doctor`.

#### Layer C: best-effort host prevention

Generate host-native adapters from a common policy manifest:

- Before file write or shell execution, determine whether the action touches protected workflow artifacts, invokes raw Git mutation, or begins implementation without an active reviewed IPD.
- For a precise violation, deny the call and return a single safe alternative command.
- For ambiguous actions, inject concise context or let the portable checker decide later; do not block on a heuristic.
- On stop, run the worktree checker. If violations are mechanically repairable, ask the host to continue with the exact next command.
- Do not inject the full workflow manual at every tool call.

#### Layer D: remote deterministic acceptance

- Run `aw check --range "$merge_base"..HEAD` in CI.
- Require the check before merge and disallow bypass for ordinary contributors/agents.
- Protect the CI workflow and policy files with review or code ownership.
- Where strong provenance matters, have CI or a service sign an attestation over the accepted tree and lifecycle events.
- For strict no-push policy, do not expose push credentials to the agent. Provide a brokered `aw publish` operation that consumes an explicit, short-lived authorization.

### 4.6 Coverage of the motivating examples

| Required process | Early prevention | Deterministic repository check | Remote acceptance | Residual risk |
|---|---|---|---|---|
| IPD before coding and structured plan review | Host write/shell hook denies implementation writes when no active reviewed IPD; `aw work begin` creates active session | Compare declared base, transition order, and implementation diff; require a reviewed-plan event before implementation commits | Required CI validates event/commit ordering | A single local commit can fabricate ordering unless the event is remotely attested; classifying “implementation code” from paths/content is heuristic unless scope conventions are explicit. |
| Use `aw set` / `aw ipd begin` / `aw ipd finalize`, not hand edits | Deny writes to lifecycle fields/journal through covered tools; return exact `aw` command | Derive state from events; reject rendered-state mismatch, missing event, invalid transition, or missing evidence | CI blocks merge | A locally powerful agent can forge both artifact and events unless events are signed externally. |
| Commit only changed files, path-scoped; never `git add -A` | Deny raw `git add -A`; route to `aw commit` | Compare commit paths to predeclared task scope and base; require task ID | CI blocks out-of-scope tree changes | Repository artifacts cannot identify “files this agent changed” in a shared dirty worktree. Use isolated worktrees or accept ambiguity. Command syntax itself is not recoverable from a commit. |
| Never push without authorization | Deny `git push` in host permissions/hooks; local `pre-push` check | None reliable from local repository state alone | Remote credentials/broker or protected branch controls acceptance | If the agent possesses ordinary push credentials, local controls are bypassable. This cannot be solved by prose or repo files. |
| Report tests passed only with actual output | `aw test` is the easy path; stop hook requires evidence reference before completion | Verify captured exit code, output digest, command, time, and exact tree binding | CI reruns tests or validates trusted CI attestation | Repo state cannot prove that chat text was pasted verbatim. Agent-readable output can be copied or fabricated; trusted CI can prove a run, not wording in the final answer. |
| Finalize terminal state with attributed history; no fabrication/backdating | `aw finish`/`aw ipd finalize` atomically validates and transitions | Validate event schema, monotonic ordering, author format, evidence, digests | CI signs or attests accepted transition | Local timestamps and author strings are claims, not proof. Non-forgeable identity/time needs external signing or server time. |

## 5. Ergonomics and friction principles

### 5.1 The correct path must be shorter than the unsafe path

- Prefer one high-level command over a checklist.
- Infer safe, reviewable defaults: active task from the worktree; base from recorded session; candidate paths from the declared scope and current diff.
- Still print the resolved values before consequential actions.
- Provide shell completion and `aw next`, which outputs the next valid lifecycle commands for the current state.
- Make commands idempotent where possible. Re-running `aw ipd finalize` should say “already finalized at event X” rather than create duplicate history.
- Preserve runner exit codes and stream real output so using `aw test` does not degrade the normal development experience.

### 5.2 Do not ask the agent to run the checker

Any necessary check that depends on being remembered will eventually be skipped. Invoke it inside the command already needed, in Git hooks for immediate feedback, at host stop for correction, and in CI for acceptance. `aw check` remains callable for diagnosis, but correctness must not depend on that voluntary call.

### 5.3 Block only deterministic violations

A hard gate should fire only when the toolkit can state a machine-checkable invariant and show the conflicting evidence. Examples:

- Good hard gate: “IPD `abc123` is `draft`; implementation writes require `reviewed`.”
- Good hard gate: “Commit contains `src/billing.ts`, outside declared scope `src/auth/**` and `tests/auth/**`.”
- Bad hard gate: “This edit looks like implementation work.”
- Bad hard gate: “The history author seems generic.”

Use warnings or later review for semantic heuristics. Promote a warning to an error only after measuring its precision on representative repositories.

### 5.4 Treat false positives as reliability defects

Alert-fatigue findings come mostly from healthcare, so direct quantitative transfer to coding agents would be inappropriate. The robust design lesson is nevertheless applicable: repeated low-value interruption increases override behavior and reduces trust. A systematic review found repeated alerts, poor relevance, and workflow disruption among factors associated with alert fatigue ([Backman et al., 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC10983371/)).

For each finding code, collect in opt-in test telemetry or repository-local metrics:

- trigger count;
- block, repair, override, and suppression count;
- time to correction;
- confirmed true/false positive labels from maintainers;
- host and rule version.

Start new rules in audit mode. Require a high measured precision threshold before fail-closed deployment. Permit narrow, expiring suppressions with a reason and reviewer, never a global “ignore all.”

### 5.5 Errors should teach the next valid action

Every failure should contain:

1. stable code;
2. what was observed;
3. violated invariant;
4. exact safe next command;
5. how to inspect details;
6. whether a human decision is actually required.

Example:

```text
AW-SCOPE-003: commit refused
Observed: 2 paths are outside task abc123 scope:
  docs/unrelated.md
  src/other-service.ts
Required: commit only paths declared by this task.
Next: aw scope show abc123
Then: aw commit abc123 -- src/auth.ts tests/auth.test.ts
If the scope is genuinely wrong: aw scope amend abc123 --reason <reason> -- <paths>
```

Do not print a generic “policy violation; read the docs.”

### 5.6 Fail closed selectively

Fail closed for terminal state transitions, protected artifact mutation, commit-scope violations, and remote merge acceptance. Fail open with a visible warning for optional formatting, analytics, or a host adapter crash when the portable CI safety net remains intact. Cursor explicitly defaults hook errors to fail-open but supports `failClosed: true`; this option should be enabled only for small, well-tested, security-critical matchers ([Cursor Hooks](https://cursor.com/docs/hooks.md)).

## 6. What is deterministically detectable post hoc

### 6.1 Detectable from repository artifacts, given an explicit schema

The following are deterministic if the relevant facts are encoded canonically:

- A rendered lifecycle status differs from the state derived from transition events.
- A transition is illegal from the previous state.
- A terminal transition lacks required evidence references.
- A history event lacks required fields, uses a forbidden placeholder author, has invalid syntax, or breaks a hash chain.
- A referenced evidence artifact is missing or its digest does not match.
- A test record applies to a different tree or predates subsequent changes.
- A commit contains paths outside a declared scope.
- An IPD and implementation have an invalid commit/event order.
- A required finalization event is absent.
- A terminal artifact remains in a nonterminal directory, if location remains semantically meaningful.
- Policy/version files were changed in the same range without the required review path.

These checks establish **internal consistency**, not truthfulness of locally supplied claims.

### 6.2 Detectable only with additional trusted evidence

- That tests actually ran: trusted CI can attest to a command, result, tree, and time. A local record is evidence, but forgeable by an agent with write access.
- Who authorized a push or transition: needs a remote identity, approval record, or signature whose key the agent cannot access.
- Reliable creation time: needs a trusted timestamp or server receipt. Filesystem and local event timestamps can be backdated.
- That the CLI authored an event: needs a protected signing service or an execution environment whose attestation is outside the agent's control.
- That a plan was genuinely reviewed by a distinct person: needs identity-bound approval, not an `author:` string.

### 6.3 Not deterministically recoverable from repository artifacts alone

- Whether the agent used `git add -A` versus an explicit pathspec if both produce the same commit tree.
- Whether the final response pasted actual runner output verbatim.
- Whether an uncommitted line was changed by this agent, another agent, or a human in a shared worktree.
- Whether the agent mentally consulted an IPD before coding.
- Whether a plausible history explanation was fabricated.
- Whether a semantic plan review was careful or merely perfunctory.
- Whether a push was authorized in chat unless the authorization is captured in a trusted, bound record.

The design response is to stop checking unobservable behavior and instead check observable outcomes: explicit scope, tree-bound evidence, validated transitions, isolated worktrees, and remote approvals.

### 6.4 Detector implementation guidance

- Compare Git trees and structured events, not file modification times.
- Parse formats with a real parser; do not infer lifecycle changes with loose regular expressions.
- Use merge-base-aware checks for CI and staged-tree-aware checks locally.
- Treat rename/copy detection carefully; rely on object identity and explicit event references where possible.
- Version both schemas and policies; make migrations explicit.
- Separate `error` (definite invariant violation), `warning` (probable issue), and `info` (advice).
- Supply a deterministic repair only when it preserves intent. Never auto-create test evidence, review approval, authorship, or terminal history.
- Keep the checker read-only by default. A separate `aw repair` should show and record each mutation.

## 7. Portability across agent hosts

Capabilities below reflect official documentation available on 2026-08-23. Host behavior changes quickly; adapters need version probes and contract tests.

| Host/surface | Always-loaded/project instructions | Blocking pre-tool gate | Stop/correction loop | Repository-distributable configuration | Important limitations for this design |
|---|---|---|---|---|---|
| Claude Code | `CLAUDE.md` and rule mechanisms | Yes. `PreToolUse` can block Bash, edit/write, MCP, and other matched tools | Yes. `Stop` can prevent completion and return a reason | Yes, `.claude/settings.json`; managed and plugin hooks also exist | Project hooks require trust; alternate/uncovered execution paths and mutable local config remain concerns. Official docs show `PreToolUse` denial and project scopes ([Claude Code Hooks](https://code.claude.com/docs/en/hooks)). |
| OpenAI Codex | Hierarchical `AGENTS.md` | Yes in current Codex hooks for Bash, `apply_patch`, MCP, and most local function tools; can deny or rewrite | Yes, `Stop` and post-tool paths | Yes, `.codex/hooks.json` or `.codex/config.toml`, subject to trust; managed hooks available | Official docs warn some specialized tool paths can opt out, so hooks are a guardrail rather than a complete boundary. Project hooks may be disabled; malformed unsupported PreToolUse fields can fail open. Use the documented deny/exit-2 contract ([OpenAI Hooks](https://learn.chatgpt.com/docs/hooks)). Codex command `rules` primarily govern commands outside the sandbox and are experimental ([OpenAI Rules](https://learn.chatgpt.com/docs/agent-configuration/rules)). |
| OpenCode | `AGENTS.md`/rules support | No general arbitrary repository validator is established by the cited permission documentation, but granular permissions can deterministically allow, ask, or deny Bash and edit patterns | No equivalent portable correction loop established here | Yes, project `opencode.json` permissions | Permissions are pattern-based and most defaults are permissive; excellent for denying raw `git push`/`git commit`, insufficient for stateful lifecycle validation by themselves ([OpenCode Permissions](https://opencode.ai/docs/permissions/)). Use portable Git/CLI/CI as the core. |
| Gemini CLI | `GEMINI.md` project context | Yes. `BeforeTool` can validate/rewrite arguments or deny; exit code 2 blocks | Yes. `AfterAgent` denial forces an automatic retry | Yes via `settings.json` hooks | Hook scripts and settings remain local/repository trust dependencies. `SessionEnd` is best effort and cannot block; use `AfterAgent` for retry ([Gemini CLI Hooks](https://geminicli.com/docs/hooks/reference/)). |
| Google Antigravity IDE | Rules/skills | Yes. `PreToolUse` returns `allow`, `deny`, `ask`, or `force_ask` | Yes. `Stop` can force continuation; invocation hooks can inject steps | Yes, workspace `.agents/hooks.json` | The cited hook contract is for Antigravity IDE. Do not assume identical support in Antigravity CLI merely because the products share branding ([Antigravity IDE Hooks](https://antigravity.google/docs/ide/hooks)). |
| Google Antigravity CLI | CLI project/customization mechanisms | **Not established by the cited IDE-hook page** | **Not established** | Unknown for equivalent blocking hooks | Install the portable core and treat CLI host-hook support as a version-gated adapter only after an official CLI contract test. Gemini CLI's hooks do not automatically prove Antigravity CLI behavior. |
| Cursor | Project rules and attachments | Yes. `preToolUse`, `beforeShellExecution`, `beforeMCPExecution`, and `beforeReadFile` can deny; exit 2 blocks | Yes. `stop` can auto-submit a follow-up within a loop limit | Yes, `.cursor/hooks.json`; cloud agents load supported project hooks | Hook failures are fail-open by default; use `failClosed: true` narrowly. `afterFileEdit` observes but cannot undo the edit ([Cursor Hooks](https://cursor.com/docs/hooks.md)). |
| Kiro IDE/CLI | Steering files | Yes. `Pre Tool Use` supports read/write/shell/web/spec categories and blocks on nonzero shell-action exit | Yes. Agent Stop can run checks and provide instructions | Yes, `.kiro/hooks/*.json`; IDE 1.x and CLI 3.x | Web surface lacks these hooks. An agent-prompt action is probabilistic; a shell-command action is deterministic and blocks pre-tool on nonzero exit ([Kiro Triggers](https://kiro.dev/docs/hooks/types/), [Kiro Actions](https://kiro.dev/docs/hooks/actions/)). |

### 7.1 Adapter policy

Maintain a small capability manifest rather than a least-common-denominator hook file:

```yaml
host: cursor
minimum_version: <tested-version>
events:
  pre_shell: blocking
  pre_edit: blocking
  stop: corrective-loop
failure_mode:
  protected_checks: closed
  advisory_checks: open
contract_tests:
  - blocks_raw_terminal_transition
  - routes_to_aw_finalize
  - blocks_git_add_all
  - stop_detects_unfinalized_ipd
```

The installer should detect hosts, explain what will be installed, avoid clobbering existing configuration, and run a harmless self-test proving that a known forbidden dummy action is blocked. Unsupported or failed adapters must degrade to the portable core with an explicit `aw doctor` warning, not silently claim enforcement.

## 8. Open questions and prioritized recommendations

### Priority 0: define guarantees before implementation

1. Publish a threat model distinguishing cooperative mistakes, accidental bypass, deliberate agent bypass, and a user/admin who can change controls.
2. State which guarantees are local convenience, repository consistency, or externally attested authority.
3. Decide whether the project needs strong provenance. If yes, select the remote identity/signing boundary first; no local event format can create that guarantee alone.

### Priority 1: build the deterministic core

1. Specify the lifecycle state machine and versioned transition-event schema.
2. Make rendered status derived, or at minimum cross-check it against canonical events.
3. Implement `aw check` as a pure, read-only engine with JSON and human output.
4. Add fixture-based tests for every finding code, including maliciously inconsistent histories.
5. Implement `aw ipd begin` and `aw ipd finalize` as atomic transactions using that engine.

**Acceptance experiment:** Create a corpus of valid and invalid repository states with known labels. Require 100% recall for structurally invalid transitions and near-zero false positives on valid historical repositories before enabling CI failure.

### Priority 2: remove remembered steps

1. Add `aw work begin`, `aw test`, `aw commit`, `aw finish`, and `aw next`.
2. Bind test evidence to the exact Git tree/worktree digest and preserve raw output separately from concise metadata.
3. Record declared scope and base before implementation.
4. Strongly recommend one task/agent per Git worktree; make it a one-command option.
5. Make every error return an exact next command.

### Priority 3: add repository acceptance gates

1. Add conflict-safe local Git hook installation and `aw doctor` verification.
2. Add a forge-neutral CI workflow running range-aware checks.
3. Document branch-protection configuration requiring the check and disallowing bypass where appropriate.
4. Protect policy, workflow, and lifecycle-schema files with review requirements.
5. Never describe a local hook as unbypassable; Git documents `--no-verify` bypass for relevant hooks ([Git](https://git-scm.com/docs/githooks)).

### Priority 4: generate and test host adapters

Implement in this order based on documented blocking primitives and likely user value:

1. Claude Code, Codex, Gemini CLI, Cursor, and Kiro pre-tool/stop adapters.
2. Antigravity IDE adapter.
3. OpenCode permissions for coarse denials plus portable `aw`/Git/CI checks.
4. Antigravity CLI only after an official, versioned hook contract is confirmed.

For every adapter, test alternate command spelling, shell wrappers, compound commands, direct edits, MCP tools, subagents, disabled hooks, hook crashes, timeouts, and untrusted-workspace behavior. The goal is measured coverage, not a configuration file that merely looks plausible.

### Priority 5: evaluate with heterogeneous agents

Build a small adherence benchmark using the actual failure cases:

- begin coding without an IPD;
- hand-edit status;
- omit finalization;
- run `git add -A` in a dirty worktree;
- include an unrelated file in a commit;
- claim tests passed without a run;
- fabricate a history entry;
- attempt a push without authorization.

Run each scenario repeatedly across hosts and models. Report at least:

- prevention rate;
- deterministic detection rate;
- correction completion rate;
- false-positive rate on valid work;
- steps and wall-clock overhead;
- bypass rate by alternate primitive;
- `pass^k`, not only single-run success, following τ-bench's consistency framing ([Yao et al., 2024](https://arxiv.org/html/2406.12045)).

Compare four ablations: prose only; prose plus just-in-time context; host gate plus wrapper; full wrapper plus Git/CI. This is the missing empirical evidence needed to quantify how much each layer contributes in this toolkit.

### Priority 6: decide strong-authorization features separately

Open design questions:

1. Is “never push unless authorized” a convenience policy or a hard security guarantee?
2. Can agents run without reusable push credentials and obtain a short-lived capability only through `aw publish`?
3. Who is the authoritative actor for terminal transitions: local Git identity, host account, repository forge, or named human reviewer?
4. Must historical events be merely tamper-evident or non-forgeable?
5. How will offline contributors work if remote attestation is required?

Do not block the deterministic core on these decisions, but do not imply that local hashes or author strings answer them.

### Priority 7: use a fresh-context verifier only for semantic residuals

After deterministic checks pass, a separate agent can review whether the IPD is substantively complete, whether test selection is appropriate, and whether the implementation matches the plan. Give it the task, diff, IPD, and machine findings, not the implementing agent's persuasive narrative. Require citations to files and commands. Treat its result as probabilistic review and measure disagreement rates; do not allow it to mint missing test evidence or approval records.

## 9. Conclusions

The observed cross-vendor failures are consistent with published evidence: long-context retrieval is position-sensitive, demonstrated behavior can overpower explicit instructions, and multi-step tool agents are not reliably consistent even when policy documents are present. The toolkit should retain concise prose for explanation, but move every enforceable invariant into deterministic code and every important acceptance decision into a boundary the agent cannot casually bypass.

The key architectural move is not a stronger reminder. It is to make `aw` the transaction boundary: the command the agent wants to run also performs the checks, records the evidence, and completes the transition. Host hooks make that path timely and obvious; local Git hooks make mistakes cheap to correct; CI and protected branches decide what is accepted. Where repository evidence cannot establish the fact, the report recommends either adding a trusted evidence source or naming the limitation as residual risk.

## 10. References

### Research and empirical evaluations

1. Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., and Liang, P. “Lost in the Middle: How Language Models Use Long Contexts.” 2023. [arXiv:2307.03172](https://arxiv.org/html/2307.03172v3).
2. Yao, S., Shinn, N., Razavi, P., and Narasimhan, K. “τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains.” 2024. [arXiv:2406.12045](https://arxiv.org/html/2406.12045).
3. Lu, J. et al. “ToolSandbox: A Stateful, Conversational, Interactive Evaluation Benchmark for LLM Tool Use Capabilities.” 2024. [arXiv:2408.04682](https://arxiv.org/html/2408.04682).
4. Liu, X. et al. “AgentBench: Evaluating LLMs as Agents.” 2023. [arXiv:2308.03688](https://arxiv.org/abs/2308.03688).
5. “Do as I Say, Not as I Do: Instruction-Induction Conflict in LLMs.” 2026. [arXiv:2605.20382](https://arxiv.org/html/2605.20382v2).
6. Kapoor, S. et al. “Towards a Science of AI Agent Reliability.” 2026. [arXiv:2602.16666](https://arxiv.org/html/2602.16666v2).
7. Backman, R., Bayliss, S., Moore, D., and Litchfield, I. “Clinical reminder alert fatigue in healthcare: a systematic literature review.” *Implementation Science* 17, 2022. [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC10983371/).

### Official product and platform documentation

8. Anthropic. “Hooks reference.” [Claude Code documentation](https://code.claude.com/docs/en/hooks). Accessed 2026-08-23.
9. Cursor. “Hooks.” [Cursor documentation](https://cursor.com/docs/hooks.md). Accessed 2026-08-23.
10. Git Project. “githooks Documentation.” [git-scm.com](https://git-scm.com/docs/githooks). Accessed 2026-08-23.
11. GitHub. “Managing a branch protection rule.” [GitHub Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule). Accessed 2026-08-23.
12. Google. “Hooks reference.” [Gemini CLI documentation](https://geminicli.com/docs/hooks/reference/). Accessed 2026-08-23.
13. Google. “Hooks.” [Antigravity IDE documentation](https://antigravity.google/docs/ide/hooks). Accessed 2026-08-23.
14. Kiro. “Hook triggers.” [Kiro documentation](https://kiro.dev/docs/hooks/types/). Accessed 2026-08-23.
15. Kiro. “Hook actions.” [Kiro documentation](https://kiro.dev/docs/hooks/actions/). Accessed 2026-08-23.
16. OpenAI. “Custom instructions with AGENTS.md.” [OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md). Accessed 2026-08-23.
17. OpenAI. “Hooks.” [OpenAI documentation](https://learn.chatgpt.com/docs/hooks). Accessed 2026-08-23.
18. OpenAI. “Rules.” [OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/rules). Accessed 2026-08-23.
19. OpenCode. “Permissions.” [OpenCode documentation](https://opencode.ai/docs/permissions/). Accessed 2026-08-23.

### Evidence classification note

The papers above measure long-context retrieval, instruction conflict, policy-following, tool use, repeated-run consistency, or alert fatigue; none directly evaluates `agent-workflows`. Statements transferring those results to this toolkit are identified as inference. Host capability statements are vendor-documented contracts, not independent measurements of completeness or bypass resistance. The recommended architecture is an engineering synthesis that should be validated through the proposed cross-host adherence benchmark before its hard gates are enabled by default.
