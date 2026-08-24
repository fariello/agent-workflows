---
id: bu9yij
created: 20260823
set: agentadhere
order: 04
topic: [agent-adherence, enforcement, hooks, ci, lifecycle]
model: reconciliation
kind: findings
status: intake
outcome: none-yet
summary: Aggregate finding: layered defense-in-depth for reliable process adherence (definitive synthesis of the 3 model reports)
consumed-by: []
---

# Aggregate Research Finding: Reliable Process Adherence for Heterogeneous Coding Agents

**Combined sources:** the OpenAI Codex, Gemini 3.1 Pro, and Sonnet 5 research reports
**Research current through:** 2026-08-23
**Scope:** `agent-workflows`, heterogeneous coding agents, host hooks, Git, CI, lifecycle state, test evidence, commit scope, and authorization boundaries

## 1. Executive finding

The three reports independently reach the same central conclusion: **soft prose is useful for orientation, but it is not a dependable enforcement mechanism.** Reliable process adherence requires a layered system that moves important rules out of model memory and into deterministic boundaries that every successful workflow must cross.

The recommended approach is:

1. Define each invariant and the assurance level it needs.
2. Implement one host-independent policy engine, conceptually `aw check`, and use it everywhere.
3. Make the compliant path the easiest path through atomic workflow commands such as `aw work begin`, `aw test`, `aw commit`, `aw finish`, and `aw ipd finalize`.
4. Represent lifecycle state as validated events with derived current state, rather than a freely editable status field.
5. Add local Git hooks and host-specific pre-tool hooks for immediate, self-correcting feedback.
6. Run the same checks in required CI and protect the merge boundary from bypass.
7. Use isolated worktrees, declared file scope, and CI-produced test evidence where attribution matters.
8. Add an external signer, credential broker, or remote transition service only for guarantees that must remain valid against an agent with broad local access.

**Overall confidence in this approach: High.** The confidence is not Very High because no published study directly evaluates this exact toolkit across all named hosts, host APIs change, some semantic requirements remain undecidable from repository artifacts, and an agent with unrestricted local authority can bypass or forge purely local controls. Confidence is nevertheless High because all three reports converge on the architecture, the key design principles are supported by both empirical agent research and mature software-control patterns, and each layer has a clear, testable enforcement boundary.

## 2. Method and equal-treatment rule

This synthesis treats the three reports as equal inputs. No report receives extra weight because of its author, length, confidence of tone, or number of citations. Each report contributes one position to the agreement and divergence analysis.

Equal treatment does not mean that every factual claim is equally reliable. Claims are evaluated independently using:

- **Completeness:** how fully the report answers the requested questions and covers the target mechanisms and hosts.
- **Thoroughness:** depth of causal analysis, implementation detail, failure-mode analysis, and residual-risk treatment.
- **Reliability:** quality and directness of evidence, use of primary sources, currency of host documentation, calibration of inference, and whether the proposed mechanism can actually observe or control the claimed behavior.

Where reports conflict, the synthesis does not resolve the conflict by majority vote. It uses the strongest available primary evidence and labels remaining uncertainty. Current official host documentation was checked where capability claims had changed or conflicted.

### Confidence scale

| Level | Meaning in this report |
|---|---|
| Very low | Mostly speculative; material contradictory evidence or no usable validation path |
| Low | Plausible, but weakly evidenced or easily defeated |
| Med low | Some support, with important untested assumptions or narrow applicability |
| Medium | Reasonable evidence and engineering basis, but meaningful uncertainty remains |
| Med high | Strong support with bounded limitations or environment dependence |
| High | Convergent evidence and a clear validation path; residual limitations are understood |
| Very high | Direct, replicated, highly applicable evidence or a deterministic guarantee under an explicit authority boundary |

## 3. Objective evaluation of the three reports

These assessments describe the reports as research artifacts. They are not weights in the synthesis.

| Report | Completeness | Thoroughness | Reliability | Objective assessment |
|---|---|---|---|---|
| OpenAI Codex | High | High | High | Broadest end-to-end assurance and implementation model, including state derivation, bypass analysis, CI, and external authority. It carefully separates measurement from inference and identifies what cannot be observed. Its original host matrix understated current OpenCode plugin interception and was too cautious about whether Antigravity CLI hooks were established; current official documentation corrects both points. |
| Gemini 3.1 Pro | Medium | Medium | Medium | Concise and action-oriented, with useful emphasis on Git hooks, teaching errors, a checksummed ledger, and `aw doctor`. Several quantitative or categorical claims are unsupported or overstated, including a claimed sub-40% compliance figure, near-100% detection, 100% portability, and high-confidence multi-agent verification. It also sometimes attributes command-level knowledge to Git hooks that those hooks do not possess. |
| Sonnet 5 | High | Very high | Med high | Deepest literature-led account of the verbal/behavioral compliance gap, environmental affordances, text-only judging limits, correction, and mechanism failure modes. It appropriately caveats its strongest direct evidence as one recent non-peer-reviewed preprint. Some host claims relied on stale or secondary sources, most notably an outdated description of Codex hooks, and a few local-forensics claims are stronger than the observable evidence permits. |

### Evaluation summary

- **Most complete shared result:** all three identify the same architectural direction, despite taking different causal and implementation routes.
- **Strongest complementary contribution from the Codex report:** explicit threat models, authority boundaries, observability limits, event-derived state, and the distinction between local convenience controls and remote guarantees.
- **Strongest complementary contribution from the Gemini report:** a compact delivery sequence centered on early Git feedback, teaching errors, a ledger, and a doctor command.
- **Strongest complementary contribution from the Sonnet report:** direct empirical evidence about verbal agreement versus behavioral compliance, shortcut removal, correction after detection, and the weakness of text-only process review.
- **Largest cross-report reliability risk:** host-specific capability claims age quickly. They should be generated from capability probes and current official documentation, not hard-coded as permanent facts.

## 4. Where all three agree

### 4.1 Prose alone is insufficient

All three reports agree that an always-loaded file such as `AGENTS.md` can explain the workflow but cannot reliably cause the workflow to occur. They point to overlapping mechanisms:

- relevant instructions may not be retrieved at the decision point;
- an immediate user goal and recent tool output compete with background rules;
- generic learned habits such as direct edits and ordinary Git commands are much stronger than an unfamiliar repository convention;
- verbal knowledge of a rule does not imply procedural execution;
- long workflows compound failure probability across remembered steps; and
- prose has no authority over files, processes, credentials, or remote acceptance.

The underlying causal emphasis differs, but the operational conclusion is unanimous: important invariants must be checked by code.

### 4.2 Defense in depth is necessary

Each report recommends multiple layers rather than a single universal hook. The common shape is:

- prose for orientation;
- just-in-time errors or injected context for correction;
- wrapped commands and CLI refusals for the normal path;
- Git or host hooks for early interception;
- a deterministic doctor/checker for artifact validation; and
- CI or another remote boundary for authoritative acceptance.

The reports also agree that host hooks are useful but fragmented. No host adapter should become the source of truth.

### 4.3 The correct path should require fewer decisions

All three reports favor replacing a sequence of remembered duties with a smaller number of atomic actions. A command such as `aw finish` should perform or invoke validation, evidence capture, state transition, and the permitted commit operation. This reduces both cognitive load and the number of independent failure opportunities.

### 4.4 Errors should teach the recovery path

The reports agree that a refusal should not merely say “invalid.” It should name the violated invariant and give the exact corrective action. This matters because detection without a low-friction repair path can produce loops, workarounds, or broad approval prompts.

Example:

```text
Cannot finalize IPD-142: no test evidence is bound to the current tree.
Run: aw test --ipd IPD-142 -- <test command>
Then run: aw ipd finalize IPD-142
```

### 4.5 Post-hoc validation is indispensable

All reports call for an `aw check` or `aw doctor` that inspects durable artifacts. This is the common safety net when prevention is unavailable, incomplete, or bypassed. The same policy implementation should be callable from the CLI, hooks, and CI so that results do not diverge by host.

### 4.6 Local controls are not strong security boundaries

Although the reports differ in how sharply they state this, all recognize bypass risks. An agent with full shell access can use raw tools, modify files, bypass local hooks, or fabricate local records. The aggregate conclusion is stronger and explicit: **a local control is authoritative only against actors that cannot alter or bypass it.** Strong provenance, push authorization, or non-forgeable approval requires an external authority.

### 4.7 Some requirements remain residual risks

The reports agree that artifact checks cannot perfectly determine whether an agent genuinely read a plan, internally considered a rule, or actually ran a test merely because it pasted plausible output. These requirements should be converted into observable events where possible, then honestly labeled probabilistic or unverifiable where they cannot be.

## 5. Where the reports diverge, and the aggregate finding

### 5.1 What primarily causes noncompliance

| Position | Report emphasis | Aggregate assessment |
|---|---|---|
| Codex | Context retrieval, competing learned behavior, and multiplicative long-horizon unreliability | Well supported as contributing mechanisms. The exact contribution of each mechanism to repository-process failures is not directly measured. |
| Gemini | Attention decay, instruction competition, declarative/procedural separation, and path of least resistance | Directionally consistent with the other reports. Some cited quantitative precision is not supported by the referenced studies. |
| Sonnet | A structural “compliance gap” between rewarded text and unobserved tool behavior, amplified by environmental affordances; lost-in-the-middle is secondary | Most directly matched to the target behavior, but central evidence comes from one recent preprint and should not be treated as settled consensus. |

**Aggregate finding:** the failure is multi-causal. There is High confidence that passive prose is an unreliable control. There is Medium confidence about which causal mechanism dominates in real coding repositories. Architecture should not depend on resolving that scientific question because deterministic boundaries mitigate all of the proposed causes.

### 5.2 Which implementation layer should come first

- Gemini recommends Git hooks first as the portable foundation.
- Sonnet prioritizes wrapped primitives, followed by Git/OS gates and a doctor command.
- Codex starts with the threat model, invariant schema, state machine, and shared policy engine, then adds wrapped commands, hooks, and CI.

**Aggregate finding:** begin with the invariant model and shared checker because every later layer depends on its semantics. Implement one or two atomic commands and local Git feedback immediately afterward. Git hooks are an excellent early integration point, but they should not become the authoritative policy implementation because they are local, not cloned automatically, and often bypassable. Required CI should follow as soon as the checker is stable.

### 5.3 Whether a Git hook can detect `git add -A`

Gemini and parts of Sonnet imply that a pre-commit hook can reject the use of `git add -A` or `git commit -a`. Codex distinguishes the typed command from the resulting staged tree.

**Aggregate finding:** a normal pre-commit hook can inspect the index and commit context, not reliably reconstruct the exact command that created them. It can enforce the intended invariant, for example “staged paths must be within declared scope,” which is usually better than banning syntax. If exact command syntax must be blocked, interception must occur at the shell/tool call, a wrapper, or a restricted execution environment. Confidence: High.

### 5.4 How trustworthy an append-only or checksummed ledger is

Gemini and Sonnet place more confidence in hashes, signatures, timestamps, or tool-authored history as evidence of legitimate transitions. Codex emphasizes that an agent able to edit both the record and verifier can recompute a local chain or backdate a plausible entry.

**Aggregate finding:** a local append-only-shaped log and hash chain are valuable for consistency checking, accidental corruption detection, and making unsupported edits conspicuous. They do not provide non-forgeable provenance against an actor with write access to the log, keys, and checker. Strong authenticity requires a key or service outside the agent's authority. Timestamp shape, such as “round” or inconsistent times, may be a heuristic signal but is not deterministic proof. Confidence: High.

### 5.5 Push authorization

Gemini and Sonnet propose pre-push checks and, in places, local environment-based authorization. Codex argues that “never push without authorization” cannot be guaranteed if the agent has the same push credential and can bypass local checks.

**Aggregate finding:** use pre-push hooks for convenience and immediate feedback, but withhold or broker push credentials when authorization must be a hard guarantee. A protected remote branch, required check, narrowly scoped bot credential, or approval service is the relevant authority boundary. A local environment variable visible to the agent is not independent authorization. Confidence: High.

### 5.6 Fresh-agent or multi-agent verification

Gemini rates fresh-context verification highly because it avoids accumulated context. Sonnet presents evidence that text-only human and LLM judges can miss behavioral noncompliance, while tool-log inspection performs much better. Codex warns that model failures may be correlated and that plausible evidence can be accepted without verification.

**Aggregate finding:** a fresh verifier is useful for semantic questions that deterministic rules cannot decide, but it should receive repository state, structured tool events, and CI evidence rather than only a narrative transcript. It is an additional detector, not an enforcement boundary. Confidence: Medium.

### 5.7 Current host capabilities

The reports disagree partly because host APIs changed. Current official documentation supports this corrected view:

| Host | Current practical capability | Aggregate implication |
|---|---|---|
| Claude Code | Pre-tool and lifecycle hooks can allow, deny, ask, or provide context across documented events | Strong adapter opportunity, still local and configurable. |
| OpenAI Codex | Current `PreToolUse` covers Bash, `apply_patch`, MCP, and most local function tools; it can block or rewrite input and inject context. Specialized paths may opt out | Sonnet's shell-only description is stale. Treat coverage as broad but not absolute. |
| Gemini CLI | Documented hook system with pre-tool decisions and lifecycle events | Suitable for prevention and teaching feedback through an adapter. |
| Google Antigravity CLI | Current official CLI documentation establishes `PreToolUse`, `PostToolUse`, invocation, and stop hooks under its own CLI configuration | Codex's earlier caution that CLI support was not established is now obsolete. Continue version-probing because product boundaries can change. |
| Cursor | Hooks can intercept relevant actions, with behavior dependent on hook configuration and failure policy | Useful adapter; ensure security-sensitive hooks fail closed where supported. |
| Kiro | Agent hooks and actions support event-triggered automation, but exact blocking semantics and coverage differ from other hosts | Use for guidance and checks only after capability probing; do not assume parity from similar event names. |
| OpenCode | Official JS/TS plugins expose `tool.execute.before`; plugins can mutate arguments or throw to block. Granular permissions provide another layer | Sonnet's “full but via code” characterization is closer to current behavior than a permissions-only description. Adapter tests must verify coverage. |

**Aggregate finding:** maintain a versioned capability matrix generated by executable probes. Similar event names do not imply equivalent interception, rewrite, stop, or fail-closed semantics. Confidence: High.

## 6. Consolidated mechanism assessment

| Mechanism | Role | Determinism and authority | Portability | Aggregate confidence | Finding |
|---|---|---|---|---|---|
| Always-loaded prose | Orientation | Probabilistic | Broad in concept | Low as enforcement; Medium as orientation | Keep concise and point to commands. Do not use as proof of compliance. |
| Just-in-time instruction | Correction and salience | Probabilistic unless paired with denial | Medium | Medium | More useful than repeated background prose, especially after a precise violation. |
| Host pre-tool hook | Early prevention | Deterministic only for covered, enabled calls | Medium | Med high for UX; Medium for cross-host enforcement | Deny unsafe raw actions and route to `aw`; capability-probe every adapter. |
| Atomic `aw` command | Prevention and evidence production | Deterministic when used | High | High | Make it shorter and easier than the raw sequence. Validate before mutation. |
| Derived lifecycle state | Invalid-state prevention and tamper detection | Deterministic over trusted events | High | Med high | Prefer event-derived state; authenticity depends on who can write/sign events. |
| Local Git hook | Early repository feedback | Deterministic when installed and not bypassed | High | High as feedback; Med low as a hard boundary | Enforce staged result and run shared checks. Never treat it as the only gate. |
| `aw check` / `aw doctor` | Artifact detection and guided repair | Deterministic for encoded invariants | Very high | High | This is the portable core. Emit stable machine codes plus exact fixes. |
| Required CI / protected branch | Remote acceptance gate | Deterministic for decidable checks when bypass is disabled | High at repository level | Very high | Strongest practical enforcement for repository invariants. Protect workflow changes too. |
| Test execution in trusted CI | Evidence of actual execution on a tree | Deterministic within runner assumptions | High | High | Bind command, environment, result, logs, and commit/tree identity. |
| Local hash chain | Consistency and accidental-tamper detection | Locally forgeable with broad access | High | Medium | Useful evidence structure, not independent attestation. |
| External signing/transition service | Provenance and protected authorization | Strong if key/service is outside agent authority | Medium | High technically; Medium on cost/fit | Add only for invariants whose consequence justifies infrastructure. |
| Fresh-context verifier | Semantic review | Probabilistic | Broad | Medium | Feed it primary artifacts and tool events; measure disagreement and false acceptance. |
| Human approval | High-consequence judgment | Depends on evidence and attention | Broad | Med high for selected boundaries | Use sparingly with concise evidence to avoid routine override and alert fatigue. |

## 7. Recommended architecture

### 7.1 Start with explicit assurance levels

Classify every rule before implementing it:

1. **Guidance:** cooperative agents should normally follow it.
2. **Repository invariant:** noncompliant artifacts must fail checks and merge.
3. **Authority invariant:** even an agent with broad local access must not be able to forge or authorize it.

This prevents local hooks, hashes, or files from being described as stronger than they are.

### 7.2 Build one policy engine

Implement all decidable rules in a single library surfaced as `aw check --format json`. Each finding should include:

- a stable rule ID;
- severity and assurance class;
- affected artifact and location;
- observed versus required state;
- the exact recovery command when one exists; and
- whether the result is deterministic, heuristic, or externally attested.

The CLI, Git hooks, host adapters, CI, and any verifier should call this engine rather than duplicate policy.

### 7.3 Use event-derived lifecycle state

Replace freely mutable status fields with validated transitions, for example:

```text
IPD_CREATED -> WORK_STARTED -> TEST_EVIDENCE_RECORDED -> REVIEWED -> FINALIZED
```

The visible status should be derived from versioned events. The transition function must reject missing predecessors, stale tree identifiers, invalid actors, malformed evidence, and unauthorized terminal transitions. For ordinary repository assurance, versioned local events plus CI validation are sufficient. For authority assurance, have an external service countersign protected events.

### 7.4 Provide atomic workflow primitives

Recommended public commands:

- `aw work begin <ipd>`: validates the plan and creates or associates an isolated worktree.
- `aw test <ipd> -- <command>`: executes the test, captures stdout/stderr and exit status, records environment metadata, and binds evidence to a tree or commit.
- `aw commit <ipd> -- <paths...>`: calculates allowed paths, refuses out-of-scope staged changes, runs the checker, and commits only the declared scope.
- `aw finish <ipd>`: checks required evidence and performs all valid non-authoritative transitions.
- `aw ipd finalize <ipd>`: validates the complete transition and requests external approval when the selected assurance level requires it.
- `aw doctor`: reports drift, missing setup, bypass-prone configuration, and exact repairs.

Raw actions should either be blocked where interception is reliable or produce a later deterministic failure. The wrapper must remain the faster path.

### 7.5 Enforce file scope from state, not command syntax

Record an explicit task scope and compare it with the Git index and final diff. Use isolated worktrees for concurrent agents or unrelated user changes. A shared dirty worktree cannot reliably reveal who owns each modification, so do not infer authorship from file timestamps or the agent's narrative.

### 7.6 Bind test evidence to the artifact being accepted

A transcript containing “tests passed” is a claim. Better evidence is created by executing tests in a controlled runner and recording:

- exact command and arguments;
- exit code;
- complete or content-addressed stdout/stderr;
- relevant environment and dependency identity;
- start/end time;
- source tree or commit hash; and
- runner identity or attestation.

Local evidence is useful but forgeable by a fully privileged local agent. Required CI should reproduce or independently run the tests for High-confidence acceptance.

### 7.7 Add early gates without confusing them with authority

- A pre-commit hook calls the shared checker against the index and declared scope.
- A pre-push hook explains missing authorization and prevents accidental pushes.
- Host pre-tool hooks block direct status edits, unscoped Git commands, or raw terminal transitions when their documented coverage permits.
- Hook failures for security-sensitive rules should fail closed where the host supports that behavior.
- Every adapter has contract tests for coverage, alternate tool paths, malformed input, disablement, and fail-open behavior.

### 7.8 Put the final repository gate in CI

Required CI runs the same policy engine in a clean environment, validates the committed workflow artifacts, reproduces required tests, checks that protected policy and workflow files were not weakened without approval, and publishes machine-readable evidence. Branch protection should require the check and disallow ordinary bypass actors.

### 7.9 Add external authority selectively

Use a remote transition service, protected signing key, repository app, or credential broker for requirements such as:

- “only an approved reviewer may finalize”;
- “the agent must never push directly”;
- “this evidence must be non-forgeable by the local worker”; or
- “the actor identity must be independently attributable.”

Do not incur this complexity for low-consequence guidance rules.

## 8. Recommended delivery sequence and confidence

| Phase | Deliverable | Confidence | Why |
|---|---|---|---|
| 0 | Threat model, assurance classes, invariant catalog, and definition of observable evidence | High | Prevents false guarantees and gives every later control a precise target. |
| 1 | Versioned policy schema and shared `aw check --format json`, with positive and adversarial fixtures | High | All three reports require a host-independent deterministic core. |
| 2 | Atomic `aw work`, `aw test`, `aw commit`, and `aw finish/finalize` paths | High | Removes remembered steps and creates evidence at the action boundary. |
| 3 | Event-derived lifecycle state and declared file scope | Med high | Strong design, but migration and concurrent-work semantics require careful testing. |
| 4 | Local Git hooks that call the checker and emit teaching errors | High for early feedback; Med low for hard security | Portable and useful, but installation and bypass limit authority. |
| 5 | Required CI and protected-branch enforcement | Very high for encoded repository invariants | A clean, remote, non-bypassable acceptance boundary is the strongest practical control. |
| 6 | Host adapters for Claude, Codex, Gemini CLI, Antigravity CLI, Cursor, Kiro, and OpenCode | Med high | Improves prevention and UX, but APIs and coverage vary and change. |
| 7 | Trusted test runner and tree-bound evidence | High | Directly replaces unverifiable narrative test claims with observable execution. |
| 8 | External signing, approval, or push broker where required | High technically; Medium on product fit | Necessary for authority invariants, but introduces operational cost and availability concerns. |
| 9 | Fresh-context semantic verifier for residual questions | Medium | Valuable as a secondary detector, but probabilistic and subject to correlated failures. |
| 10 | Cross-host, cross-model adherence benchmark and regression dashboard | High | Needed to measure real improvement, false positives, bypasses, and host drift. |

## 9. Validation plan

The reports are strongest when converted into falsifiable tests. Build a benchmark containing at least these cases:

- code is edited before an IPD is started;
- a lifecycle status is hand-edited;
- a terminal transition is attempted without review evidence;
- `git add -A`, `git commit -a`, pathspec tricks, renames, deletions, submodules, and nested repositories produce in-scope and out-of-scope staged trees;
- tests are claimed without an execution event;
- test evidence references a stale tree;
- local history is edited and its hash chain recomputed;
- a hook is missing, disabled, crashes, times out, or returns malformed output;
- a host uses an alternate edit or shell path outside the expected hook;
- concurrent agents work in one checkout versus isolated worktrees;
- the agent attempts `--no-verify`, a raw Git binary, or direct push;
- policy, hooks, or CI definitions are modified in the same change; and
- a fresh verifier receives narrative-only evidence versus tool logs and repository artifacts.

Measure:

- single-run adherence and repeated-run `pass^k`;
- prevention rate, detection rate, repair rate, and silent false acceptance;
- false positives and time to recovery;
- number of approval prompts and override rate;
- host/version coverage;
- effect of removing raw shortcuts;
- effect of teaching errors after a denial; and
- agreement between deterministic checks, CI, semantic verifiers, and human review.

Run the same scenarios across models and hosts without changing the underlying invariants. This is the only reliable way to determine whether a mechanism transfers beyond the environment in which it was designed.

## 10. Residual risks and non-goals

The proposed architecture does not prove:

- that an agent cognitively read or understood an IPD;
- that a locally privileged agent did not forge locally held evidence;
- who authored a change in a shared dirty worktree;
- the exact shell command used when only the resulting Git index is observable;
- that a semantic review is correct;
- that every host hook observes every tool path; or
- that a protected boundary remains protected if administrators or bypass actors can override it.

It can instead require observable preparatory artifacts, isolate work, validate resulting state, run tests independently, and make acceptance depend on an authority outside the local agent. That is the appropriate engineering substitute for trying to infer private cognition.

## 11. Final recommendation

Adopt the layered architecture, beginning with a single invariant model and policy checker, then make atomic `aw` commands the default path, add event-derived state and declared scope, integrate local Git and host hooks for immediate feedback, and require the same checks in protected CI. Use trusted CI for test evidence. Introduce external signing or credential brokering only for transitions whose authenticity or authorization must survive a fully privileged local agent.

**Confidence: High.**

The recommendation earns High confidence because the three independently produced reports agree on its core, the controls rely on observable behavior rather than model self-report, and the architecture degrades honestly from prevention to detection when a host lacks an interception point. It does not earn Very High confidence because exact effect sizes are not established for `agent-workflows`, one important empirical source is a recent unreplicated preprint, host APIs are moving targets, and semantic process requirements retain irreducible probabilistic components.

## 12. Source notes

### The three input reports

1. OpenAI Codex, *Reliable Process Adherence for Heterogeneous Coding Agents* (2026-08-23).
2. Gemini 3.1 Pro, *Research Report: Enforcing Process Adherence in Heterogeneous AI Coding Agents* (August 2026).
3. Sonnet 5, *Agent Process Adherence: Why Soft Directives Fail and What Actually Works* (August 2026).

### Primary and official sources most material to the aggregate conclusions

- Liu et al., [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/html/2307.03172v3).
- Yao et al., [τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains](https://arxiv.org/html/2406.12045).
- Kapoor et al., [The Science of Agent Reliability](https://arxiv.org/html/2602.16666v2).
- [Do as I Say, Not as I Do: Instruction-Induction Conflict in Language Models](https://arxiv.org/html/2605.20382v2).
- [The Compliance Gap in Tool-Using Language Models](https://arxiv.org/pdf/2605.01771), a recent preprint whose direct relevance is high but whose reliability should remain provisional pending replication and peer review.
- [Git hooks documentation](https://git-scm.com/docs/githooks).
- [GitHub protected branch and required-check documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule).
- [Claude Code hooks documentation](https://code.claude.com/docs/en/hooks).
- [OpenAI Codex hooks documentation](https://learn.chatgpt.com/docs/hooks).
- [Gemini CLI hooks reference](https://geminicli.com/docs/hooks/reference/).
- [Google Antigravity CLI hooks documentation](https://antigravity.google/docs/hooks?app=cli).
- [Cursor hooks documentation](https://cursor.com/docs/hooks.md).
- [Kiro hook types](https://kiro.dev/docs/hooks/types/) and [hook actions](https://kiro.dev/docs/hooks/actions/).
- [OpenCode plugins documentation](https://opencode.ai/docs/plugins/).
- Backman et al., [alert-fatigue systematic review](https://pmc.ncbi.nlm.nih.gov/articles/PMC10983371/), used only as cross-domain support for minimizing noisy human approvals.
