<!-- aw-prompt: Kind: research | Status: executed | Created: 2026-08-29 | Author: opencode (Opus 5, its_direct/pt3-claude-opus-5-1m-us) | Targets: GPT-5.6 (web search) | Concerns: session/turn allocation policy for `aw oc run` (agent_workflows/oc_runipd.py, agy_runipd.py) | Basis: measured cost data from .aw/records/runs/ (post rate-card correction); backlog xd9sll (lane session reuse) | Results: .aw/records/research/20260829-sessalloc-00-x0spmh-agent-runner-session-allocation.gpt56.research-report.md (research id6 x0spmh, set `sessalloc`, run by GPT-5.6 extra-high, filed 2026-08-29 via `aw research new`) | Goal: derive an evidence-based session-allocation policy (turns per session, grouping unit, cross-run reuse) . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
# Research task: how should an autonomous agent runner allocate work to LLM sessions?

You are a research analyst with web search. Produce a rigorous, decision-ready design study answering
one question: **when a runner executes many agent turns in sequence, how should those turns be
allocated to conversational sessions so that quality is preserved and cost is minimised?**

Return your answer as a **downloadable markdown (`.md`) file**. Do not answer inline only. The file
must be self-contained and readable by both a maintainer and a coding agent that will implement from it.

---

## 1. The system under study

An open-source tool (`agent-workflows`, CLI `aw`) has a **runner** (`aw oc run`) that executes a queue
of work items autonomously. Nomenclature matters: it is a **runner** that **runs** turns, not a
"driver" that "drives".

Key mechanics:

- Each work item is an **Implementation Plan Document (IPD)**: a structured plan with an execution
  checklist (`E-*` items) and a validation checklist (`V-*` items) in strict bijection. A turn must
  perform the E items, then prove each V item with pasted command output.
- Items are grouped into **Sets**. A Set is a topical cluster, typically an orchestrator item plus
  ordered child phases (`00` orchestrator, `01+` children). Children often have real dependencies:
  phase 3 legitimately builds on phase 2's code.
- Item **actions** differ: `execute` (do the work, edit code, run tests, commit) and `review`
  (critique a plan or spec and rewrite it; produces no code). Reviews are cheap and read-mostly;
  executions are long, tool-heavy, and mutate the repo.
- Each `execute` turn runs **isolated**: its own git worktree on its own branch, so turns cannot see
  each other's uncommitted work. `review` turns are **not** isolated and share the main tree.
- The runner spawns the coding agent as a child process (`opencode run --session <id> --dir <path>
  --format json ...`) and captures a JSONL event log per turn.

**Current allocation policy (the thing to critique):** one session per **Set**, reused across all of
that Set's turns; a fresh session only for an independent verifier turn.

That policy just caused a production incident worth understanding, because it constrains the design
space. Sessions were keyed per Set while worktrees are allocated per item. A session carries its own
project/working-directory binding, which **overrode** the `--dir` the runner passed, so the second and
later turns of a Set silently executed in the *previous* turn's worktree. Every main-repo path then
looked "external", the tool's permission gate asked an unanswerable question, and the turn died at a
600-second stall watchdog. Four consecutive turns were lost.

The fix was: **an isolated turn always gets a fresh session.** This is safe but crude: it throws away
all cross-turn context reuse for exactly the turns that are most expensive. Hence this research.

---

## 2. Ground truth: measured cost data from this system

Do not speculate about the cost model. These are real measurements from the repository's own run
logs, and they contain a trap you must reason about carefully.

### 2.1 The pricing configuration changed mid-history

The gateway is a LiteLLM proxy exposing per-token costs. The tool's config initially declared
`input=$5.00/Mtok, output=$25.00/Mtok` and **no cache-read price**. It was later corrected to the
gateway's actual published rates:

```
input $5.50/Mtok   output $27.50/Mtok   cache_read $0.55/Mtok   cache_write $6.875/Mtok
```

Consequence: **cost figures recorded before and after that edit are not comparable.** A least-squares
fit of per-step `cost` against per-step token counts recovers the rate card in force at the time:

| Run (date) | fitted input | fitted output | fitted cache_read |
|---|---|---|---|
| Aug 24 | $5.000 | $25.000 | **$0.0000** |
| Aug 29 | $5.500 | $27.500 | **$0.5500** |

The Aug 24 zero is a **config artifact** (cache reads were real but priced at zero, so they vanished
from the recorded total), not evidence that cache reads are free. Any analysis that pools those runs
will reach a false conclusion. Treat only the post-edit regime as the live cost model, and treat
`cache_read = $0.55/Mtok` as the real marginal price of carrying context.

### 2.2 What context reuse actually costs, post-correction

One `execute` turn, 154 steps, measured; predicted cost matches recorded cost to the cent:

| component | tokens | rate | cost | share |
|---|---|---|---|---|
| cache_read | 22,038,059 | $0.55 | **$12.12** | **74%** |
| input | 225,435 | $5.50 | $1.24 | 8% |
| output | 110,792 | $27.50 | $3.05 | 19% |
| **total** | | | **$16.41** | (recorded: $16.41) |

**Re-reading cached context was 74% of the bill for a single turn.** This is the central economic
fact. Note the mechanism: `cache_read` accumulates *per step within a turn*. A turn with 154 steps
over a context that grows from 44K to 226K tokens re-reads that context on nearly every step, so
cumulative cache reads (22M) vastly exceed the context size (226K).

### 2.3 How context grows across a shared session

Nine consecutive `execute` turns of one Set sharing one session (Aug 24 run; costs are in the
**old** rate card, so use the token columns, not the dollar column):

| pos | steps | ctx at turn start | ctx at turn end | cache_read in turn |
|---|---|---|---|---|
| 1 | 52 | 30,790 | 68,317 | 2,560,392 |
| 2 | 126 | 84,989 | 249,948 | 21,923,435 |
| 3 | 86 | 263,633 | 351,465 | 26,951,113 |
| 4 | 80 | 367,094 | 445,180 | 32,463,344 |
| 5 | 49 | 460,303 | 508,998 | 23,784,819 |
| 6 | 67 | 524,637 | 591,259 | 37,505,950 |
| 7 | 87 | 609,210 | 685,847 | 56,244,818 |
| 8 | 64 | 701,589 | 764,956 | 46,938,290 |
| 9 | 27 | 783,149 | 806,941 | 21,402,857 |

Observations to test, not assume:
- Context grows roughly **monotonically and linearly**, ~85K tokens per turn, reaching 807K after 9
  turns. A 1M-token model limit would be hit at roughly turn 11-12.
- `cache_read` per turn scales with **(context size x steps in turn)**, so late turns are
  quadratically punishing: turn 7 re-read 22x more cached tokens than turn 1.
- At $0.55/Mtok, turn 7's 56.2M cache reads alone cost **$30.93**. Turn 1's cost **$1.41**.
- Yet per-turn *output* stayed roughly flat (~12-68K). The extra context did not buy proportionally
  more work.

### 2.4 Fleet-level context

Across ~59 recorded runs: queue sizes 1-22 items, 1-7 Sets per run. The largest run was 22 items /
4 Sets / 6h45m. Long runs are normal, not exceptional. The maintainer's intuition is that **25 IPDs in
one session is too many**; the data above suggests the ceiling is lower than that, but you should
derive it rather than accept it.

---

## 3. The questions to answer

Answer each with a recommendation, the reasoning, the evidence, and the conditions under which the
answer flips.

### Q1. Is there an optimal number of turns per session, and what determines it?
Derive it, do not guess. Build a cost model with the real rate card that accounts for cache reads
scaling as (context x steps). Identify the crossover point where starting a fresh session (paying to
re-establish context from scratch) becomes cheaper than continuing (paying to re-read an ever-larger
prefix). Express the answer as a rule computable at runtime from observable quantities (context size,
steps taken, marginal cache-read spend), not as a hardcoded turn count. State explicitly whether the
answer is 3 turns, 10, or 25, and show the arithmetic.

### Q2. Should Sets be the unit of session sharing?
Sets are topical, which is a proxy for shared context, but the proxy may be poor. Consider whether the
right unit is instead: declared **dependency edges** between items (phase 3 depends on phase 2, so it
benefits from phase 2's session; two unrelated items in the same Set do not); overlapping
**Scope-Paths** (the files each plan declares it will touch); or a measured similarity signal.
Evaluate whether a dependency-aware or scope-overlap-aware grouping beats Set-based grouping, and say
what data would settle it.

### Q3. Should `review` turns pool differently from `execute` turns?
Reviews are short, read-mostly, non-isolated, and share heavy common context (the same repository
conventions, the same spec documents). Executions are long, tool-heavy, isolated, and mutate state.
Assess whether reviews should aggregate aggressively into one long-lived session (maximising prefix
reuse of the shared convention corpus) while executions stay short or singleton. Include the risk that
a long review session accumulates opinions from earlier reviews and stops evaluating each plan
independently, which would be a **correctness** regression, not merely a cost one.

### Q4. What is the safe interaction between session reuse and worktree isolation?
This is the incident above, generalised. Establish the invariant. Candidates: a session must never be
reused across different working directories; a session may be reused only if the tool's session state
carries no directory binding; or directory binding must be explicitly overridable per turn. Determine
whether context reuse across isolated turns is achievable **at all** without reintroducing the
wrong-tree bug, and if so how. If the honest answer is that per-tree sessions are the only safe design
and cross-turn reuse must be obtained another way (see Q6), say so plainly.

### Q5. Should sessions be shared across runs, and how would that be made safe?
Cross-run reuse offers the largest prefix-reuse win and the largest blast radius. Address: staleness
(the repository has moved; cached context describes code that no longer exists, actively misleading
the agent); concurrency (multiple runners in one checkout, plus humans - this is a shared checkout
where other agents work simultaneously); provider-side cache TTL and whether a cached prefix even
survives between runs; and auditability (a run's log should explain its own cost and behaviour).
Recommend for or against, and if for, specify the invalidation rule (e.g. keyed on base commit,
config digest, and rate card).

### Q6. Is session allocation even the right lever?
Steelman the alternative: instead of managing session boundaries, reduce the context each turn needs.
Options include a compiled per-turn context pack (only the plan, its dependencies' *outcomes*, and the
relevant file slices); explicit context compaction/summarisation between turns; provider-side prompt
caching of a stable shared prefix (repository conventions, runbook) with per-turn variable content
appended; or retrieval instead of accumulation. Compare against session-sharing on cost, complexity,
and failure modes. It is a legitimate conclusion that session allocation is the wrong primitive and
context construction is the real answer - if the evidence supports it, argue that.

### Q7. What mechanism should decide allocation?
Propose the actual decision procedure, at the level of detail an implementer can build: what is
measured, when the decision is made (queue-planning time vs adaptively mid-run), what the policy
knobs are, what the defaults are, and what the operator override looks like. Prefer a rule that
degrades safely when signals are missing. State how the policy is **observable and testable** after
the fact: what the run record must capture so a maintainer can verify the policy behaved and quantify
what it saved. Include the fallback when a session must be abandoned mid-Set (stall, crash, context
limit) so a session split never loses work.

---

## 4. Cross-tool applicability

The primary target is **opencode** (session addressed by `--session <id>`, working directory by
`--dir`, JSONL event stream with per-step token/cost records). Where a recommendation can be made
tool-agnostic without weakening it, do so, and note where each tool forces a divergence:

- **Antigravity (`agy`)**: sessions are "conversations" (`--conversation <id>`), plus a `--continue`
  flag that resumes the previous conversation implicitly. The implicit-resume flag is an extra hazard:
  clearing an explicit session id is not sufficient if `--continue` silently restores it.
- **Claude Code**: session resumption semantics, `--resume`/`--continue`, and its own compaction
  behaviour.
- **Codex** and comparable CLI agents.

For each, state whether the recommended policy is expressible, and if not, what the minimum upstream
capability would be. Explicitly cover: whether the tool exposes context size and cache-read counts
per step (needed for an adaptive rule), and whether a session's working directory can be rebound.

---

## 5. Method and evidence requirements

1. **Search for current, dated information.** Provider prompt-caching semantics and prices change
   frequently. Cite provider documentation for cache-read/cache-write pricing, minimum cacheable
   prefix length, and cache TTL for the relevant model families (Anthropic Claude in particular,
   since the measured data is Claude via a LiteLLM proxy), plus OpenAI and Google equivalents for
   contrast. Date every price and note that prices in this brief may be stale by the time you read it.
2. **Look for prior art.** Multi-agent orchestration frameworks, batch LLM job schedulers, and
   agent frameworks that manage conversation lifetime. Report what they actually do about session
   lifetime and context growth, with sources. If the honest finding is that few systems address this
   deliberately, say so.
3. **Show the model.** Give the cost model as explicit formulas with defined variables, then a worked
   numeric example reproducing the measured $16.41 turn, then a sensitivity analysis over turn count,
   steps per turn, and cache-read price. Make clear which conclusions are robust to price changes and
   which invert.
4. **Separate evidence tiers.** Label each claim: measured (from the data above), cited (with source
   and date), or inferred (your reasoning). Do not blur them.
5. **Report conflicts.** Where sources disagree, or where a source contradicts the measured data
   above, surface the conflict rather than silently choosing.
6. **State falsifiers.** For each recommendation, give the experiment that would refute it and the
   metric it would move.

## 6. Deliverable

A single `.md` file containing:

1. **Executive summary** - the recommended policy in under 200 words, including the specific numbers.
2. **Cost model** - formulas, variables, worked example, sensitivity analysis.
3. **Findings per question** (Q1-Q7), each with recommendation, evidence tier, reasoning, and
   flip conditions.
4. **Recommended design** - the allocation mechanism, its defaults, its knobs, its observability
   requirements, and its failure/fallback behaviour.
5. **Cross-tool matrix** - opencode / agy / Claude Code / Codex: expressible or not, and the gap.
6. **Phased adoption plan** - what to implement first for the largest verified win at the lowest
   risk, with a measurable acceptance criterion per phase.
7. **Open questions and conflicts** - what remains genuinely unresolved, and what experiment or data
   would resolve each.
8. **Sources** - with access dates.

Constraints on the recommendation: it must be safe under **concurrent runners in a shared checkout**;
it must not reintroduce the wrong-working-directory failure; it must **fail closed** (an unavailable
or ambiguous signal yields a safe, correct-but-costlier choice rather than a silently wrong one); and
correctness must dominate cost wherever the two conflict. Say so explicitly if any recommendation
trades correctness for savings, and quantify the trade.
