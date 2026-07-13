# Deep-Research Prompt: Inter-Instance Communication Between OpenCode Agents

- **Created:** 2026-07-13
- **Purpose:** Determine how agents running in separate, concurrent OpenCode instances on the same machine can communicate, signal one another, deliver prompts or work requests, and coordinate safely.
- **Intended audience:** An LLM, chatbot, research agent, coding agent, or other LLM-based system with access to web search, source code, local files, shell tools, or some combination of these.
- **Desired output:** One or more detailed, well-structured Markdown files, optionally packaged as a ZIP archive.

---

## Role

You are a senior software-architecture researcher, operating-systems engineer, security engineer, and OpenCode internals analyst.

Your task is to investigate and explain all practical and technically plausible methods by which an agent running in one live OpenCode instance can communicate with an agent running in another live OpenCode instance on the same machine.

Do not assume that OpenCode natively supports agent-to-agent communication. Determine what is actually supported, what can be accomplished indirectly, what requires plugins or external orchestration, and what would require changes to OpenCode itself.

Your answer must be rigorous, implementation-oriented, security-conscious, and explicit about uncertainty.

---

## Core questions

Answer all of the following.

### 1. Native OpenCode capabilities

Determine whether OpenCode currently provides any native mechanism for one running instance to:

1. Discover another running OpenCode instance.
2. Determine whether another instance is idle, busy, waiting for input, or terminated.
3. Send a message to another instance.
4. Send a prompt to another instance.
5. inject text into another instance's input stream.
6. Trigger another instance to resume processing.
7. Notify another instance that files or directories have changed.
8. Subscribe to events emitted by another instance.
9. Share a session, conversation, task queue, or memory store.
10. Address a specific agent, session, process, terminal, or repository.

For every claimed native mechanism, identify:

- The exact OpenCode version or commit examined.
- The relevant documentation.
- The relevant source files, symbols, APIs, commands, configuration keys, or protocols.
- Whether the mechanism is public, documented, internal, experimental, or inferred.
- Whether it works across:
  - Two terminal UI instances.
  - A terminal UI instance and a headless instance.
  - Two headless instances.
  - Two instances in the same repository.
  - Two instances in different repositories.
  - Two instances running as the same operating-system user.
  - Two instances running as different users.
  - Containers, WSL, SSH sessions, tmux, screen, or remote hosts.

If no native capability exists, say so clearly.

---

### 2. OpenCode process and runtime model

Explain the OpenCode runtime model insofar as it affects inter-instance communication.

Investigate:

- Processes and subprocesses.
- Parent and child process relationships.
- Standard input, standard output, and standard error.
- Pseudoterminals.
- Pipes.
- Unix-domain sockets.
- TCP or HTTP listeners.
- Named pipes on Windows.
- Temporary files.
- Lock files.
- PID files.
- Session databases.
- State directories.
- Cache directories.
- Log files.
- File watchers.
- Event buses.
- RPC mechanisms.
- Language-server or MCP connections.
- Plugin processes.
- Shell processes spawned by an agent.
- Environment variables inherited by child processes.
- Signals handled or ignored by OpenCode.
- Whether a running instance exposes any API or control surface.

Identify all relevant filesystem paths and OS resources on Linux, macOS, Windows, and WSL where applicable.

Distinguish:

- Resources created per process.
- Resources created per session.
- Resources created per repository.
- Resources created per user.
- Resources shared globally.
- Resources that are persistent.
- Resources that are ephemeral.
- Resources that are safe or unsafe to manipulate externally.

---

### 3. "Wake up and check this folder" signaling

Evaluate practical ways to send a signal equivalent to:

> Wake up, inspect this directory, process any pending request, and respond.

Consider at least:

- A watched directory.
- Sentinel files.
- Atomic file creation or rename.
- A mailbox directory.
- A queue directory.
- JSON or Markdown job files.
- SQLite.
- Unix-domain sockets.
- Named pipes or FIFOs.
- TCP localhost sockets.
- HTTP callbacks.
- Webhooks.
- Operating-system signals.
- `inotify`, `fanotify`, `kqueue`, FSEvents, and Windows file-change notifications.
- tmux or screen input injection.
- Pseudoterminal input injection.
- Clipboard-based approaches.
- Terminal automation.
- Shell wrappers.
- Supervisors and daemons.
- Cron, systemd user services, launchd, or Windows Task Scheduler.
- MCP servers.
- A local broker or coordinator process.
- Git commits, branches, refs, notes, or worktrees.
- Shared issue/task files.
- Message queues such as Redis, NATS, ZeroMQ, or RabbitMQ.
- Local database polling.
- OpenCode plugins.
- Changes to OpenCode core.

For each method, explain:

- Whether it merely notifies the process or can cause the agent to perform work.
- Whether the receiving agent must already be executing a loop that checks for messages.
- Whether the receiving OpenCode instance must be at an input prompt.
- Whether user interaction is required.
- Latency.
- Reliability.
- Failure modes.
- Portability.
- Complexity.
- Security implications.
- Whether it is recommended.

Be precise about the distinction between:

1. Waking an operating-system process.
2. Causing OpenCode to read input.
3. Causing the LLM agent to begin a new inference turn.
4. Causing the agent to invoke tools or inspect files.
5. Delivering a durable work request.
6. Delivering a human-visible notification only.

---

### 4. Sending prompts between OpenCode instances

Determine all feasible ways to send a prompt or task from one OpenCode instance to another.

For each approach, explain:

- The transport.
- The receiving endpoint.
- How the receiving instance learns that a prompt is available.
- How the prompt is inserted into the receiving conversation or session.
- Whether it becomes a user message, system message, tool result, plugin event, terminal input, or some other message type.
- Whether the receiving model sees the sender's identity.
- Whether the receiving model can distinguish:
  - A human-entered prompt.
  - Text injected into a terminal.
  - A prompt delivered through an API.
  - A plugin-generated message.
  - A tool result.
  - A file-based task.
  - A message from another agent.
- Whether OpenCode labels, annotates, sanitizes, or treats externally supplied prompts differently.
- Whether the receiving agent can reliably authenticate the sender.
- Whether the receiving agent can reject or quarantine the prompt.
- Whether the prompt can be delivered to a specific session or only to a new session.
- Whether prompts can be queued while the receiver is busy.
- Whether messages survive crashes or restarts.

Do not infer provenance awareness merely because a transport is external. Establish what metadata the receiving model actually receives.

---

### 5. Provenance and trust semantics

Investigate whether the receiving agent knows that a message came from another OpenCode instance.

Explain:

- What message-role metadata is visible to the model.
- What message-role metadata is retained only by OpenCode.
- Whether plugins can add trusted provenance metadata.
- Whether provenance can be spoofed by prompt text.
- Whether a transport-level identity is propagated into the model context.
- Whether the receiver can distinguish authenticated metadata from untrusted text.
- Whether OpenCode has any concept similar to:
  - Trusted tool output.
  - Untrusted external content.
  - User messages.
  - System or developer messages.
  - Peer-agent messages.
  - Signed requests.
  - Capability-scoped messages.

Recommend a concrete message envelope that clearly separates:

- Transport metadata.
- Authentication metadata.
- Sender identity.
- Repository identity.
- Session identity.
- Task ID.
- Correlation ID.
- Timestamp.
- Expiration.
- Requested action.
- Allowed scope.
- Human approval requirements.
- Untrusted prompt body.
- Attachments or referenced paths.
- Response destination.
- Signature or MAC.
- Schema version.

Explain which fields must never be copied directly into privileged model instructions.

---

### 6. Best-practice architectures

Propose and compare several architectures for inter-OpenCode-agent communication.

At minimum, evaluate:

#### Architecture A: Shared filesystem mailbox

A durable queue based on directories and atomic files.

#### Architecture B: Local broker or coordinator daemon

A separate process that owns queues, authentication, routing, leases, and acknowledgements.

#### Architecture C: MCP-based coordination service

An MCP server that exposes task-queue and messaging tools to multiple OpenCode agents.

#### Architecture D: OpenCode plugin

A plugin that registers commands, watches for messages, and injects or exposes tasks safely.

#### Architecture E: Headless OpenCode workers

A controller launches or invokes headless OpenCode processes for bounded tasks instead of attempting to wake an interactive TUI.

#### Architecture F: Terminal or PTY injection

Sending keystrokes or text to tmux, screen, or a pseudoterminal.

#### Architecture G: OpenCode core enhancement

A native local RPC, session-control, or peer-agent protocol.

For each architecture, provide:

- A component diagram in Mermaid.
- Control flow.
- Data flow.
- Trust boundaries.
- Authentication method.
- Authorization method.
- Persistence model.
- Queue and retry behavior.
- Concurrency behavior.
- Crash recovery.
- Observability.
- Human-in-the-loop controls.
- Advantages.
- Disadvantages.
- Appropriate use cases.
- Inappropriate use cases.
- Implementation effort.
- Security rating.
- Recommended status:
  - Recommended.
  - Conditionally recommended.
  - Experimental.
  - Discouraged.
  - Do not use.

Conclude with a ranked recommendation for:

1. A simple same-user prototype.
2. A reliable single-machine production workflow.
3. A multi-user workstation.
4. WSL and Windows interoperability.
5. Multiple repositories.
6. Long-running autonomous agents.
7. High-security environments.

---

### 7. Security threat model

Produce a substantive threat model.

Address at least:

- Prompt injection.
- Cross-agent prompt injection.
- Confused-deputy attacks.
- Privilege escalation.
- Unauthorized command execution.
- Repository-boundary violations.
- Path traversal.
- Symlink attacks.
- TOCTOU vulnerabilities.
- Malicious file replacement.
- Queue poisoning.
- Message replay.
- Message duplication.
- Message loss.
- Message reordering.
- Sender spoofing.
- Session spoofing.
- PID reuse.
- Socket hijacking.
- Named-pipe impersonation.
- Insecure temporary files.
- Weak filesystem permissions.
- Shared-user compromise.
- Environment-variable leakage.
- Secret exfiltration.
- Tool-output injection.
- Log injection.
- Denial of service.
- Infinite agent loops.
- Agent amplification or message storms.
- Recursive delegation.
- Deadlocks.
- Livelocks.
- Stale locks and abandoned leases.
- Malicious or malformed attachments.
- Oversized prompts.
- Unicode or control-character attacks.
- Terminal escape injection.
- Shell metacharacter injection.
- Unsafe deserialization.
- SQL injection.
- Insecure plugin updates.
- Dependency compromise.
- Untrusted repositories.
- Cross-worktree contamination.
- Accidental execution of requests intended for another agent.
- Destructive actions performed without human approval.

For each material threat, provide:

- Attack scenario.
- Preconditions.
- Impact.
- Likelihood.
- Detection.
- Mitigation.
- Residual risk.

Include a compact threat matrix.

---

### 8. Required security controls

Recommend concrete controls, including:

- Per-agent identities.
- Per-repository identities.
- Unix file ownership and modes.
- Windows ACLs.
- Secure runtime directories.
- Socket permissions.
- Mutual authentication.
- HMAC or digital signatures.
- Nonces.
- Sequence numbers.
- Expiration timestamps.
- Replay protection.
- Capability-based authorization.
- Allowlisted operations.
- Repository-root confinement.
- Canonical path checking.
- Symlink-safe file handling.
- Atomic writes.
- Safe file ownership verification.
- Least privilege.
- Sandboxing.
- Process isolation.
- Container isolation.
- Secret redaction.
- Schema validation.
- Size limits.
- Rate limits.
- Queue depth limits.
- Timeouts.
- Circuit breakers.
- Idempotency keys.
- Acknowledgements.
- Leases.
- Dead-letter queues.
- Audit logs.
- Tamper-evident logs.
- Human approval gates.
- Emergency stop controls.
- Safe defaults.
- Explicit opt-in.
- Clear UI indications that a task came from another agent.

Give implementation examples where useful.

---

### 9. Plugin feasibility

Determine whether an OpenCode plugin can implement this functionality.

Investigate the current plugin API and answer:

1. Can a plugin run background logic?
2. Can it watch files or sockets?
3. Can it expose commands?
4. Can it receive external events?
5. Can it add a message to a session?
6. Can it start a new model turn?
7. Can it create a new session?
8. Can it target an existing session?
9. Can it inspect whether a session is idle or busy?
10. Can it intercept, annotate, accept, reject, or transform inbound messages?
11. Can it register tools available to the agent?
12. Can it persist state?
13. Can it communicate with plugins in other OpenCode processes?
14. Can it display a notification in the TUI?
15. Can it request human approval?
16. Can it safely shut down or unload?
17. What permissions does a plugin inherit?
18. What security boundary, if any, exists between plugin code and OpenCode?

Cite the exact plugin interfaces, hooks, events, types, and source files.

Clearly distinguish:

- What can be implemented entirely as a plugin.
- What requires an external daemon.
- What requires terminal automation.
- What requires OpenCode core changes.
- What is impossible or unsafe with the current API.

---

### 10. Proposed plugin design

If a plugin is feasible, design one.

Use a neutral working name such as `opencode-peer` unless the evidence suggests a better name.

Provide:

- Goals.
- Non-goals.
- User stories.
- Architecture.
- Plugin lifecycle.
- Configuration.
- CLI or TUI commands.
- Message schema.
- Queue layout or socket protocol.
- Authentication.
- Authorization.
- Session selection.
- Idle/busy handling.
- Prompt-injection defenses.
- Human-approval workflow.
- Logging.
- Metrics.
- Error handling.
- Crash recovery.
- Backward compatibility.
- Cross-platform considerations.
- Testing strategy.
- Packaging and installation.
- Upgrade strategy.
- Uninstallation and cleanup.
- Example workflows.
- Example configuration files.
- Example message files.
- Pseudocode or real code skeletons.

Where possible, provide a minimal proof-of-concept implementation or code skeleton consistent with the current OpenCode plugin API.

Do not invent plugin APIs. If the required hook does not exist, show the nearest real API and identify the missing capability.

---

### 11. Proposed core enhancement

If reliable prompt delivery or wake-up behavior cannot be achieved safely through plugins, propose an OpenCode core enhancement.

Consider a local control API with capabilities such as:

- Instance registration.
- Instance discovery.
- Authenticated local RPC.
- Session enumeration.
- Session status.
- Durable inboxes.
- Prompt submission.
- Event subscriptions.
- Task acknowledgement.
- Cancellation.
- Pause and resume.
- Human approval.
- Peer-agent provenance.
- Repository scoping.
- Capability tokens.
- Audit logging.

Provide:

- API sketch.
- Threat model.
- Permission model.
- Example requests and responses.
- Lifecycle.
- Error cases.
- Backward compatibility.
- Minimal viable implementation.
- Future extensions.
- Reasons the feature should or should not be included in OpenCode core.

---

### 12. Practical recommendations

Provide clear recommendations for what a developer should do today.

Include:

- The best no-code or low-code method.
- The best filesystem-based method.
- The best robust local architecture.
- The best plugin-based method.
- The best approach when the receiver is an interactive TUI.
- The best approach when the receiver can be a headless worker.
- Methods that should be avoided.
- A staged implementation roadmap:
  1. Proof of concept.
  2. Safer prototype.
  3. Reliable local service.
  4. Plugin integration.
  5. Potential upstream OpenCode contribution.

Include explicit guidance on whether it is better to:

- Attempt to wake an existing interactive agent.
- Ask an existing agent to poll a durable inbox.
- Start a new bounded OpenCode process for each task.
- Use a coordinator that owns state and delegates work.
- Treat agents as disposable workers rather than persistent conversational entities.

---

## Research requirements

### Source quality

Prioritize:

1. Current OpenCode source code.
2. Current official OpenCode documentation.
3. OpenCode plugin examples and type definitions.
4. OpenCode issue tracker and pull requests.
5. Release notes and changelogs.
6. Operating-system documentation.
7. tmux, screen, systemd, launchd, Windows, WSL, MCP, and relevant IPC documentation.
8. High-quality security references.

Do not rely solely on blog posts, forum posts, generated summaries, or stale documentation.

### Freshness

OpenCode changes quickly. Verify the current version, repository default branch, release date, and commit examined.

Record:

- Date accessed.
- OpenCode version.
- Commit hash.
- Documentation version.
- Plugin API version, if any.

If sources conflict, explain the conflict.

### Source inspection

When source access is available:

- Search the codebase for session handling, plugin hooks, event emission, process spawning, IPC, sockets, HTTP servers, TUI input, prompt submission, and message roles.
- Cite exact file paths and symbols.
- Include stable source links with line anchors when possible.
- Do not claim that an API exists merely because a type or unused symbol exists.
- Trace the actual call path from external input to model invocation.

### Experiments

When a safe test environment is available, perform controlled experiments.

Possible experiments include:

- Run two OpenCode instances in separate terminals.
- Observe processes and file descriptors.
- Inspect listening sockets.
- Inspect temporary and state directories.
- Send operating-system signals.
- Test FIFO or socket input.
- Test tmux `send-keys`.
- Test whether injected text is indistinguishable from keyboard input.
- Test file watchers.
- Test plugin hooks.
- Test headless invocation.
- Test queued prompts while the receiver is busy.
- Test crash and restart behavior.
- Test same-repository and different-repository cases.

Document:

- Exact commands.
- Environment.
- Expected result.
- Actual result.
- Interpretation.
- Limitations.

Do not run destructive tests on a user's real repositories or sessions.

---

## Analytical rules

1. **Separate fact from proposal.** Label findings as:
   - Verified.
   - Documented but not tested.
   - Observed experimentally.
   - Inferred from source.
   - Plausible but unverified.
   - Proposed design.

2. **Do not conflate process signaling with agent execution.** A Unix signal, file event, or terminal notification does not necessarily cause an LLM turn.

3. **Do not conflate text injection with authenticated peer messaging.** Text entered through a PTY may look exactly like human input.

4. **Do not assume provenance.** Show what metadata actually reaches the model.

5. **Do not assume safety because communication is localhost-only.** Same-machine attackers, compromised repositories, plugins, and processes remain relevant.

6. **Do not recommend polling without discussing latency, resource use, race conditions, durability, and shutdown behavior.**

7. **Do not recommend shared files without discussing atomicity, locking, ownership, symlinks, and replay protection.**

8. **Do not recommend terminal injection as a primary production architecture without strong warnings.**

9. **Prefer bounded, inspectable, durable workflows over magical or implicit behavior.**

10. **Prefer explicit task envelopes, acknowledgements, leases, and audit logs.**

11. **Treat all peer-supplied prompt content as untrusted input.**

12. **Preserve user control.** High-risk or destructive actions should require explicit approval.

---

## Required deliverables

Create the following Markdown files where practical.

### 1. `00-executive-summary.md`

A concise summary covering:

- What OpenCode supports natively.
- Whether an existing instance can truly be "woken."
- Whether prompts can be sent.
- Whether provenance is preserved.
- Best current architecture.
- Main security risks.
- Plugin feasibility.
- Recommended next step.

### 2. `01-native-capabilities-and-runtime.md`

Detailed findings on:

- Native features.
- Runtime model.
- Processes.
- IPC.
- Files.
- Sessions.
- APIs.
- Signals.
- File watchers.
- Cross-platform behavior.

### 3. `02-communication-methods-comparison.md`

A comprehensive comparison of all practical approaches.

Include a decision matrix with columns such as:

| Method | Can notify | Can trigger LLM turn | Durable | Authenticated | Targets existing session | Cross-platform | Reliability | Security | Complexity | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|

### 4. `03-provenance-and-security.md`

Include:

- Provenance analysis.
- Trust model.
- Threat model.
- Threat matrix.
- Required controls.
- Secure message envelope.

### 5. `04-plugin-feasibility-and-design.md`

Include:

- Current plugin API findings.
- Feasibility assessment.
- Plugin architecture.
- Missing hooks.
- Code skeletons.
- Configuration examples.
- Test plan.

### 6. `05-core-enhancement-proposal.md`

Include a proposed native OpenCode local-control or peer-agent protocol if warranted.

### 7. `06-implementation-roadmap.md`

Include:

- Recommended architecture.
- Phased roadmap.
- Proof-of-concept steps.
- Production-hardening steps.
- Testing.
- Operational guidance.
- Upstream contribution plan.

### 8. `sources.md`

Provide a complete bibliography with:

- Title.
- Author or project.
- URL.
- Version or commit.
- Access date.
- Notes on relevance.

### 9. Optional code directory

When filesystem access is available, include:

```text
prototype/
├── README.md
├── schemas/
│   └── peer-message.schema.json
├── examples/
│   ├── message.request.json
│   └── message.response.json
├── plugin/
│   └── ...
├── broker/
│   └── ...
└── tests/
    └── ...
```

The code may be a proof of concept, but it must clearly state what is functional, mocked, or blocked by missing OpenCode APIs.

---

## Output and file-handling instructions

When the environment provides filesystem access:

1. Create a new output directory named:

   `YYYYMMDD-HHMM-opencode-inter-instance-agent-communication`

2. Save all Markdown files and optional code beneath that directory.

3. Create a ZIP archive named:

   `YYYYMMDD-HHMM-opencode-inter-instance-agent-communication.zip`

4. Preserve readable filenames and relative links between files.

5. Validate:
   - All Markdown links.
   - Mermaid syntax where possible.
   - JSON examples.
   - JSON Schema syntax.
   - Code formatting.
   - ZIP contents.

6. Provide the user with direct paths or downloadable links to:
   - The main output directory, if supported.
   - The ZIP archive.
   - `00-executive-summary.md`.

When the environment does not provide filesystem access:

- Return the files as clearly separated Markdown sections.
- Use a heading naming each intended file.
- Keep internal cross-references consistent.
- Do not omit content merely because a ZIP cannot be created.

---

## Desired tone and quality

The deliverable should be:

- Technically precise.
- Skeptical of unsupported claims.
- Detailed enough for implementation.
- Clear about current limitations.
- Security-first.
- Useful to both an OpenCode user and an OpenCode contributor.
- Structured for easy consumption by another coding agent.
- Free of marketing language.
- Free of vague claims such as "should work" unless uncertainty is explicitly explained.

---

## Final completion checklist

Before finishing, verify that the work:

- Answers every core question.
- Distinguishes native support from workarounds.
- Explains whether a receiving model recognizes an external prompt.
- Separates wake-up, notification, input delivery, and LLM execution.
- Compares filesystem, IPC, terminal, MCP, plugin, broker, and core-change approaches.
- Includes a security threat model.
- Includes concrete mitigations.
- Evaluates plugin feasibility using current OpenCode APIs.
- Provides a recommended architecture.
- Provides a phased implementation roadmap.
- Includes source citations.
- Includes version and commit information.
- Clearly labels unverified claims.
- Produces the requested Markdown files or a ZIP archive.
