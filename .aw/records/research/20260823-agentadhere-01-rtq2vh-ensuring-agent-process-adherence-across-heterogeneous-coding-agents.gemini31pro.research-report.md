---
id: rtq2vh
created: 20260823
set: agentadhere
order: 01
topic: [agent-adherence, enforcement, hooks, ci, lifecycle]
model: gemini31pro
kind: research-report
status: intake
outcome: none-yet
summary: Why soft prose fails; defense-in-depth for heterogeneous coding agents (Gemini 3.1 Pro)
consumed-by: []
---

# Research Report: Enforcing Process Adherence in Heterogeneous AI Coding Agents

**Prepared for:** Maintainers of `agent-workflows`
**Date:** August 2026
**Subject:** Strategies for Reliable Agent Process Adherence and Behavioral Enforcement

---

## 1. Executive Summary

To reliably force heterogeneous, untrained AI coding agents to adhere to defined repository processes, `agent-workflows` must shift from a paradigm of **soft instruction (prose)** to a **defense-in-depth architecture rooted in hard constraints and deterministic post-hoc detection**. Always-loaded instructions fail due to well-documented limitations in LLM attention mechanisms, instruction competition, and the fundamental gap between declarative memory and procedural execution under task pressure. The single most effective realistic strategy is to implement a layered model: portable, deterministic constraints at the tool boundary (fail-closed CLIs and Git hooks) that make the "wrong" path impossible, paired with "teaching errors" that inject the correct process directly into the agent's short-term context upon failure, all backed by a deterministic CI/CD state-checker that catches out-of-band manual edits.

---

## 2. Root-Cause Analysis: Why Soft Prose Directives Fail

The observation that agents "forget" or ignore always-loaded instructions like `AGENTS.md` is not an anomaly; it is a predictable outcome of current LLM architectures.

1.  **Context-Window Attention Decay ("Lost in the Middle"):**
    Research consistently demonstrates that LLMs struggle to retrieve and act upon information located in the middle of long context windows (Liu et al., 2023). An instruction file loaded at the beginning of a session is pushed into the "middle" as the agent accumulates conversational history, tool outputs, and file reads. By the time a commit decision is made, the `AGENTS.md` directive is attention-starved.
2.  **Instruction Competition and Salience:**
    Agents are subjected to multiple layers of instructions: their system prompt, user requests, tool schemas, and workspace files. When a user says, "Fix the bug in auth.py," this goal is highly salient. The instruction "write an IPD first" is background context. Models optimizing for task completion heavily weight the immediate user directive over passive constraints (Wang et al., 2023).
3.  **Declarative vs. Procedural Knowledge:**
    Frontier models "know" the rule (if asked directly, they can recite the IPD requirement) but fail to execute it. This is because standard RLHF trains models to be helpful and immediate. Unless the model was fine-tuned specifically to pause, reflect, and invoke a bespoke workflow CLI before coding (procedural training), it defaults to its base habit: writing code immediately (Schick et al., 2023).
4.  **The "Path of Least Resistance" Bias:**
    Without hard barriers, agents use standard primitives (e.g., standard Git commands or direct file I/O) rather than bespoke tools (e.g., `aw ipd begin`), because the standard primitives are overwhelmingly represented in their pre-training data.

---

## 3. The Mechanism Landscape

The table below evaluates mechanisms for enforcing behavior, ordered roughly from softest to hardest.

| Mechanism | Prevent / Detect | Deterministic? | Portability | Agent Friction | Failure Modes | Evidence / Effectiveness |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Prose Instructions** (e.g., `AGENTS.md`) | Prevent | Probabilistic (Low) | High (All hosts can read files) | Low | Attention decay; overridden by user prompt; ignored under task pressure. | Poor. LLMs exhibit <40% compliance on complex negative constraints in long contexts (Liu et al., 2023). |
| **JIT Context Injection** (Hooking triggers) | Prevent | Probabilistic (Medium) | Medium (Requires host extension/MCP support) | Low | Hook might not fire; agent may still choose to ignore the injected context. | Better than static prose. Recency effect boosts attention to injected rules significantly. |
| **Host-Level Hooks** (Pre-edit/Pre-tool) | Prevent | Deterministic | Low (Highly fragmented across Cursor, Claude Code, Gemini CLI) | High | Host bypasses; API changes break adapters. | High within supported hosts. Fails completely on unsupported CLIs/agents. |
| **Primitive Wrapping** (Replacing generic tools) | Prevent | Deterministic | High (If standard tools like `git` are aliased/shimmed in the workspace) | Medium | Agent attempts absolute paths to bypass shim; environment setup complexity. | Very high. If the agent cannot access raw `git`, it must use the wrapper. |
| **Hard Gates at Tool Boundary** (CLI validations) | Prevent | Deterministic | High (Runs in the shell regardless of the agent) | Medium | Agent gets stuck in an error loop if error messages aren't self-documenting. | Exceptional. Fails closed. Forces compliance if the agent wants to proceed. |
| **Post-Hoc Detection** (Checkers, CI, Linters) | Detect | Deterministic | High (Standard scripts/CI) | High (Context switch required to fix) | Doesn't stop the initial bad action; relies on agent to self-correct post-flagging. | Near 100% detection for state violations. Standard practice in SWE (SWE-bench). |
| **Multi-Agent Verification** (Fresh context) | Detect | Probabilistic (High) | High (Can run as a CI step or separate script) | High (Cost and time) | Verifier agent hallucinates or rubber-stamps due to prompt phrasing. | High. Breaks the "lost in the middle" cycle by starting fresh (Kinniment et al., 2023). |

---

## 4. Recommended Architecture for `agent-workflows`

Because no single host dominates and LLM behavior is non-deterministic, `agent-workflows` must adopt a **Layered Architecture**.

### Layer 1: Portable Deterministic Enforcement (The Foundation)
This layer does not trust the agent. It enforces constraints using standard POSIX/Git mechanisms.
*   **Git Hooks (Pre-commit/Pre-push):** Block `git add -A` equivalents by verifying the commit scope against the active IPD via a pre-commit hook. Reject pushes unless `aw set status` indicates authorization.
*   **CLI Hard Gates:** `aw ipd finalize` must deterministically refuse to run if the required structured plan-review artifact does not exist. `aw set <status>` must reject invalid state transitions (e.g., jumping from 'draft' directly to 'terminal').
*   **Shims:** Alias standard commands where safely possible within the agent's PTY/shell environment, redirecting to `aw` equivalents with teaching error messages.

### Layer 2: Deterministic Post-Hoc Detection (The Safety Net)
A `aw doctor` or `aw check` command (run locally and enforced in CI) that inspects artifact states.
*   Catches manual edits to `Status:` fields by verifying cryptographic or historical traces in the tool's log.
*   Flags un-attributed or manually back-dated state changes.

### Layer 3: Best-Effort Per-Host Prevention (The UX Layer)
This layer maps the hard constraints into the agent's preferred UI to prevent error loops.
*   `.cursorrules` / `.clauderules`: Lightweight pointers telling the agent *which tool to use* (relying on Layer 1 to enforce *how* to use it).
*   **Model Context Protocol (MCP):** Expose `aw` actions as native tools for Claude Code and Cursor, bypassing the need for shell execution guessing.

### Enforceability Mapping for Example Processes:
*   **Author IPD before coding:** *Layer 1 (Pre-commit hook).* Reject code commits if an active IPD is not registered in the tool.
*   **Use CLI verbs instead of hand-editing:** *Layer 2 (Detection).* The CLI generates an invisible hash or append-only log entry. If the file status changes without a log entry, CI fails.
*   **Commit ONLY changed files (path-scoped):** *Layer 1 (Pre-commit hook).* Fails the commit if files outside the declared IPD scope are staged.
*   **Paste ACTUAL test runner output:** *Residual Risk / Multi-agent.* Highly difficult to enforce deterministically. An agent can fabricate a passing test string. Best mitigated by running tests in an isolated CI sandbox where the agent *cannot* provide the output, only the code.
*   **Move plan to terminal state via tool:** *Layer 1 (CLI Hard Gate).* Require the transition tool to run the final checks; block PR creation otherwise.

---

## 5. Ergonomics Principles: Making the Right Path the Easy Path

Hard gates fail if they trap the agent in an infinite loop of confusing errors.

1.  **Error Messages as Prompt Engineering (Self-Teaching Errors):**
    When an agent violates a constraint (e.g., running `git commit -a`), the pre-commit hook must not just output `Error: Scope violation.` It must output an LLM-optimized teaching string:
    > `ERROR (Process Violation): You attempted to commit files outside your declared scope. DO NOT use 'git commit -a'. Instead, explicitly scope your commit using: 'git commit -- <file1> <file2>'. To update your scope, run 'aw ipd update --add <file>'.`
2.  **Stateful Defaults (Low-Friction):**
    If the agent is actively working on IPD `auth-fix-123`, the command `aw set in-progress` should default to `auth-fix-123` rather than requiring the agent to remember and pass the ID.
3.  **Minimize False Positives:**
    If a gate fires erroneously, human developers will uninstall the toolkit, and agents will hallucinate workarounds. Ensure scope checks accommodate automatically generated files (e.g., compiled assets) cleanly.

---

## 6. Post-Hoc Detection: What is Deterministically Detectable?

**Deterministically Detectable (from repository artifacts):**
*   **Manual Status Edits:** Detectable if the CLI appends a signed/timestamped entry to an `.aw/history.log` file whenever a status is changed. A mismatch between the file's current status and the latest log entry indicates a manual/unauthorized edit.
*   **Unauthorized Scopes:** Detectable via `git diff` against the active IPD manifest.
*   **Terminal Records lacking Attribution:** Detectable by parsing the final artifact schema for required author/timestamp metadata injected by the `aw` tool (which human/manual edits usually omit).

**NOT Deterministically Detectable (Residual Risk):**
*   **"Did the agent actually run the tests?"** If the process asks the agent to run tests and paste output into a Markdown file, you cannot reliably distinguish between real pasted output and perfectly hallucinated test output. **Solution:** Delegate test execution to the toolkit (`aw test`), not the agent.
*   **"Did the agent author the IPD *before* coding?"** If an agent writes the code locally, then writes the IPD, then runs `aw ipd begin`, then commits the code, the artifact timeline looks identical to the correct process.

---

## 7. Portability Analysis Across Agent Hosts

*   **Claude Code:** Supports native CLI tool execution and exposes `.clauderules`. High compatibility with CLI hard gates. Supports MCP, making it ideal for native tool wrapping.
*   **Cursor:** Heavy reliance on `.cursorrules`. Tends to prefer direct file edits over CLI commands. Hard Git hooks are highly effective here because Cursor utilizes standard git underlying mechanisms.
*   **OpenAI Codex / OpenCode:** Standard terminal access. High compatibility with POSIX shims and shell-level gating.
*   **Gemini CLI / Antigravity:** Follows workspace conventions but can aggressively parallelize actions. Requires robust concurrency handling in the `.aw/` state files.
*   **Kiro:** Heavily relies on CI feedback. Post-hoc detection (Layer 2) is highly effective as Kiro parses CI logs accurately to self-correct.

*Conclusion on Portability:* Do not rely on any single host's proprietary pre-edit hooks. The lowest common denominator is the **file system, standard standard out (stdout/stderr) from CLI tools, and Git**. Building constraints here ensures 100% portability.

---

## 8. Open Questions & Prioritized Recommendations

**Open Questions:**
*   How to handle an agent legitimately discovering an out-of-scope bug that needs an immediate fix without creating heavy friction via the IPD scope-lock?
*   Should `agent-workflows` provide a standard isolated test-runner to prevent hallucinated test outputs?

**Prioritized Implementation Plan:**
1.  **Implement Git Hooks First:** Build a script that installs a `pre-commit` hook to enforce path-scoping based on the active IPD. This immediately solves the most common scope-creep violations.
2.  **Audit CLI Error Messages:** Rewrite all standard out/standard error messages in the `aw` CLI to explicitly state the *next required command* to recover from the error.
3.  **Implement the State Ledger:** Modify `aw set` and `aw ipd begin/finalize` to write to an append-only, checksummed `.aw/history.log`.
4.  **Create `aw doctor`:** Build the post-hoc deterministic checker that verifies artifact status against the history log, ready to be wired into CI/CD pipelines.

---

## 9. References

*   Kinniment, M., et al. (2023). "Evaluating Language-Model Agents on Realistic Autonomous Tasks." *arXiv preprint arXiv:2312.11671*.
*   Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). "Lost in the Middle: How Language Models Use Long Contexts." *arXiv preprint arXiv:2307.03172*.
*   Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Zettlemoyer, L., ... & Scialom, T. (2023). "Toolformer: Language Models Can Teach Themselves to Use Tools." *arXiv preprint arXiv:2302.04761*.
*   Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., ... & Wen, J. R. (2023). "A Survey on Large Language Model based Autonomous Agents." *Frontiers of Computer Science*.
