# Deep-research prompt: Communication between concurrently running OpenCode agents

- **Created:** 2026-07-13
- **Primary subject:** OpenCode inter-instance and inter-agent communication on one machine
- **Primary upstream:** https://github.com/anomalyco/opencode
- **Intended audience:** OpenCode users, plugin authors, systems programmers, and coding agents
- **Required output:** A rigorous, well-cited Markdown report, optionally accompanied by implementation artifacts

## Role

You are a senior systems researcher, OpenCode source-code analyst, plugin architect, and operating-system IPC/security engineer.

Investigate how an agent in one running OpenCode instance can communicate with an agent in another running OpenCode instance on the same machine. The goal is not merely to list theoretical IPC mechanisms. Determine what OpenCode actually supports, what can be composed safely from existing OpenCode features, what requires a plugin or external coordinator, and what should be avoided.

The final work must be suitable for a technically sophisticated reader who may implement a reliable inter-agent coordination system or an OpenCode plugin.

## Core questions

Answer all of the following thoroughly and precisely.

1. What officially supported methods allow one running OpenCode instance to communicate with another running OpenCode instance on the same machine?
2. What unofficial but technically viable methods exist using OpenCode commands, server APIs, ACP, MCP, plugins, tools, shell commands, files, databases, sockets, named pipes, signals, terminal injection, or other operating-system facilities?
3. Can one instance send a "wake up and check this folder" type notification to another already-running instance?
4. Can one instance send a prompt or message directly into another instance's active session?
5. Can a prompt be queued for later processing if the receiving instance is idle, busy, or waiting for user input?
6. Does the receiving agent know that a message came from another OpenCode instance rather than from the human user?
7. If provenance is detectable, how is it represented in the session, message, part, event, API request, or tool invocation?
8. Does OpenCode treat externally supplied prompts differently from prompts entered through the TUI, CLI, web UI, IDE, attach client, ACP client, or API?
9. Can an external sender select the target project, worktree, session, agent, model, mode, or permission context?
10. What happens when the receiving instance is busy, streaming, executing tools, waiting for permission, disconnected, crashed, or shutting down?
11. What are the best-practice architectures for inter-OpenCode-agent communication?
12. What security risks arise, and how should they be mitigated?
13. Can a plugin implement a safe and ergonomic communication layer?
14. What parts can be implemented entirely as a plugin, and what parts require an external daemon, command wrapper, OpenCode core change, or operating-system service?
15. What would a production-quality protocol and plugin architecture look like?

## Required deliverables

Produce one primary Markdown report. If the environment permits file creation, save it as:

```text
YYYYMMDD-HHMM-opencode-inter-agent-communication-research.md
```

If implementation artifacts materially improve the answer, also create one or more of the following:

- a protocol specification
- a plugin design document
- a threat model
- a proof-of-concept plugin or external coordinator
- test scripts
- sequence diagrams
- a sample configuration

Place multiple files in a clearly named directory and provide a ZIP archive when practical.

If filesystem access is unavailable, provide the complete Markdown content directly in the response.

Do not modify a user's real OpenCode configuration, session data, credentials, repositories, or running instances. Use isolated test environments and disposable data.

## Version discipline

At the beginning of the report, record:

1. Research date and timezone.
2. Latest stable OpenCode version at research time.
3. Exact stable Git tag and commit inspected.
4. Exact default or development branch commit inspected, if different.
5. Installed OpenCode version used for experiments.
6. Operating systems and environments actually tested.
7. Any behavior found only in unreleased source.
8. Any relevant historical behavior that differs by OpenCode version.

Use the latest stable release as the primary behavioral baseline. Analyze unreleased behavior separately and label it clearly.

Use immutable source links tied to a tag or commit whenever possible.

## Evidence hierarchy

Prefer evidence in this order:

1. OpenCode source code at a pinned stable release.
2. OpenCode tests and schemas at that release.
3. Official OpenCode documentation.
4. Reproducible runtime experiments in isolated environments.
5. OpenCode release notes, issues, and pull requests.
6. Maintainer comments.
7. Community reports, only when clearly labeled as anecdotal.

Classify important findings as:

- **Officially supported**
- **Source-supported but undocumented**
- **Empirically observed**
- **Possible through composition**
- **Requires a plugin**
- **Requires an external coordinator**
- **Requires an OpenCode core change**
- **Unsafe or not recommended**
- **Unknown or version-dependent**

Every nontrivial factual claim must include a citation or reproducible experiment.

## Research method

### 1. Inspect OpenCode architecture and source

Trace all code relevant to:

- process startup and instance lifecycle
- CLI, TUI, web, server, attach, ACP, and IDE modes
- local HTTP APIs
- event streams, SSE, WebSocket, or other streaming channels
- session creation and session mutation
- prompt submission
- message and part creation
- session status and busy state
- tool execution
- permission requests and approvals
- plugins and hooks
- custom tools and commands
- MCP clients and servers
- ACP transport
- local sockets, named pipes, TCP listeners, UDP listeners, and mDNS
- PTYs and stdin/stdout transports
- OpenCode databases and session persistence
- file watchers
- shell execution
- process signaling and shutdown
- authentication for local servers
- CORS and bind-address behavior
- server discovery
- instance IDs, session IDs, project IDs, and worktree IDs
- concurrent access to the same project and database

Search for all endpoints, RPC methods, event types, session methods, prompt-related functions, and plugin hooks that could permit one process to affect another.

### 2. Enumerate communication classes

Investigate at least the following classes independently.

#### A. Official OpenCode client/server methods

Examples to verify rather than assume:

- `opencode serve`
- `opencode web`
- `opencode attach`
- local API clients
- SDK clients
- ACP
- IDE integrations
- session APIs
- event subscriptions

Determine whether one OpenCode instance can act as a client of another and whether that constitutes agent-to-agent communication or only UI-to-server communication.

#### B. Plugin-mediated communication

Determine whether plugins can:

- open a socket or HTTP listener
- connect to another listener
- subscribe to session events
- create a new user message
- append a system, assistant, or tool message
- invoke a command or tool
- create or select a session
- discover the current session and project
- identify the sender
- add metadata indicating message provenance
- persist a queue
- wake the receiving instance
- request human approval
- reject unauthenticated messages
- operate while no model request is active

Identify exact hooks, APIs, context objects, lifecycle events, and restrictions.

#### C. MCP-mediated communication

Assess whether MCP can safely serve as a broker or message bus between agents.

Clarify:

- whether MCP permits server-initiated prompts or notifications
- whether an OpenCode MCP client can receive unsolicited work
- whether MCP sampling or elicitation is supported
- whether one OpenCode instance can expose itself as an MCP server to another
- whether MCP messages become user prompts, tool results, resources, or notifications
- whether provenance is preserved
- whether MCP is appropriate for wake-up semantics

Do not conflate MCP tool calls with direct injection into another agent's conversation.

#### D. ACP-mediated communication

Determine whether ACP supports:

- creating or resuming sessions
- sending prompts
- streaming responses
- cancellation
- session discovery
- metadata or sender identity
- concurrent clients
- authentication
- unsolicited server-to-client messages

Explain whether ACP is a viable inter-instance transport or only an editor-to-agent protocol.

#### E. Filesystem mailbox or watched-folder patterns

Analyze architectures based on:

- inbox directories
- atomic file creation or rename
- append-only logs
- JSON or MessagePack envelopes
- SQLite queues
- lock files
- `inotify`, FSEvents, ReadDirectoryChangesW, or polling
- completion receipts and acknowledgments

Determine whether OpenCode itself watches arbitrary folders or whether a plugin or daemon must do so.

Explain robust wake-up semantics, atomicity, duplicate handling, replay, ordering, and crash recovery.

#### F. OS-native IPC

Analyze suitability and support for:

- Unix-domain sockets
- Windows named pipes
- TCP loopback sockets
- UDP loopback
- POSIX signals
- Windows events or mailslots
- anonymous pipes
- FIFOs
- shared memory
- local message queues
- process stdin injection
- PTY or terminal keystroke injection
- `tmux` or `screen` command injection
- desktop automation or accessibility APIs

Separate mechanisms that can signal a process from mechanisms that can safely submit a prompt into OpenCode.

#### G. Database manipulation

Determine whether directly inserting or modifying OpenCode session database rows could create a message for a running instance.

Analyze:

- schema constraints
- event generation
- caches
- transaction behavior
- WAL concurrency
- message ordering
- runtime synchronization
- corruption risk
- unsupported invariants

Unless proven safe and supported, treat direct database mutation as unsafe and explain why.

#### H. Shell and command-based methods

Assess patterns such as:

- launching `opencode run` from another agent
- starting a second noninteractive OpenCode subprocess
- using a shared output folder
- invoking a command that calls a local server API
- handing work to another session rather than another live TUI

Explain when orchestration through fresh subprocesses is preferable to injecting work into an existing interactive instance.

### 3. Perform controlled runtime experiments

Where feasible, run two or more isolated OpenCode instances on the same machine with disposable configuration and data directories.

Test:

1. Two TUI instances in the same repository.
2. Two TUI instances in different repositories.
3. One server plus one attach client.
4. One server plus an API or SDK client.
5. One ACP endpoint plus a test client.
6. Two instances using the same OpenCode database.
7. Sending a prompt while the receiver is idle.
8. Sending a prompt while the receiver is streaming a model response.
9. Sending a prompt while the receiver is executing a tool.
10. Sending a prompt while the receiver awaits permission approval.
11. Sending multiple prompts concurrently.
12. Canceling or interrupting a remotely submitted prompt.
13. Restarting the receiver with queued work pending.
14. Detecting the receiver's project and session.
15. Authenticating and rejecting an unauthorized sender.
16. Preserving sender provenance through the session and model context.
17. Watching a mailbox directory with a proof-of-concept plugin or helper.
18. Operating across Linux and Windows or WSL boundaries, if available.

Record exact commands, versions, environment variables, ports, paths, and observed behavior.

Never use the user's real sessions or credentials.

## Mandatory analysis topics

### A. What is an "OpenCode instance"?

Define and distinguish:

- an OpenCode process
- a TUI client
- an OpenCode server
- an attached client
- an ACP process
- a project
- a worktree
- a session
- an agent configuration
- an active model turn
- a plugin instance

Explain why communication between two processes, two sessions, and two agents are not necessarily the same problem.

### B. Wake-up semantics

Define at least these wake-up levels:

1. Notify an OS process that something changed.
2. Cause a plugin or event loop to inspect a folder or queue.
3. Cause OpenCode to display a notification.
4. Cause OpenCode to create a pending message.
5. Cause the model to begin a new turn automatically.
6. Interrupt a running turn and redirect it.

For each communication method, state which levels it can achieve.

Explain whether OpenCode has a native notion of an idle agent waiting for work, or whether an agent exists only during model turns.

### C. Prompt submission and provenance

Determine exactly how prompts are represented internally.

Answer:

- Is every submitted prompt stored as a user-role message?
- Can a plugin create a different role or metadata field?
- Can a sender ID, origin, transport, or signature be preserved?
- Does the model see this provenance automatically?
- Can the receiving agent distinguish a human prompt from another agent's prompt without an explicit protocol envelope?
- Are prompts submitted through different frontends normalized to the same internal form?
- Can an external message bypass normal permission checks or instruction hierarchy?
- Can a remote sender set system instructions, agent selection, model, or permissions?

Create a provenance matrix covering TUI, web, attach, API, ACP, plugin, MCP, filesystem mailbox, and direct database manipulation.

### D. Busy-state and concurrency behavior

Document behavior when a target session is:

- idle
- processing a prompt
- streaming
- executing a tool
- waiting for permission
- compacting
- reverting
- disconnected from its UI
- shared by multiple clients
- shutting down
- crashed

Determine whether prompts are rejected, queued, merged, serialized, or allowed concurrently.

Explain race conditions and how a coordinator should use idempotency keys, sequence numbers, session locks, leases, or acknowledgments.

### E. Agent identity and routing

Determine how a sender can reliably target:

- a process
- a listening server
- a project
- a worktree
- a session
- a configured agent
- a named role such as planner, implementer, or reviewer

Analyze discovery options:

- static configuration
- registry file
- per-instance heartbeat
- mDNS
- local port file
- Unix socket path
- named pipe path
- process table inspection
- OpenCode server APIs

Recommend a stable routing model that does not depend solely on process IDs.

### F. Best-practice architecture comparison

Compare at least these architectures:

1. **Shared-folder mailbox plus plugin watcher**
2. **Local authenticated broker daemon**
3. **One OpenCode server with multiple API clients**
4. **ACP-based coordinator**
5. **MCP-based task exchange**
6. **Fresh `opencode run` subprocesses managed by an orchestrator**
7. **Direct peer-to-peer sockets between plugins**
8. **Database-backed durable queue**
9. **Human-mediated file handoff only**

Score each on:

- official support
- reliability
- durability
- latency
- provenance
- security
- cross-platform support
- implementation effort
- observability
- failure recovery
- compatibility with interactive TUI sessions
- compatibility with unattended agents
- ability to queue work
- ability to wake a receiver
- risk of OpenCode version breakage

Make a clear recommendation for:

- simplest safe local coordination
- robust production coordination
- interactive human-supervised workflows
- unattended multi-agent workflows
- cross-platform Windows, WSL, Linux, and macOS use

### G. Security threat model

Create a structured threat model covering:

- unauthorized prompt injection
- local privilege escalation
- confused deputy attacks
- prompt provenance spoofing
- replay attacks
- duplicate task execution
- symlink attacks on mailbox directories
- path traversal
- malicious file contents
- poisoned shared repositories
- arbitrary command execution
- plugin supply-chain compromise
- socket exposure beyond loopback
- weak or absent server authentication
- token leakage
- session hijacking
- cross-user access on a multi-user machine
- race conditions and TOCTOU
- denial of service
- resource exhaustion
- maliciously large messages or attachments
- database corruption
- stale registry entries
- PID reuse
- terminal injection
- log and audit leakage
- prompt content leaking secrets to another agent or provider

For every threat, provide:

- attack scenario
- affected architecture
- likelihood
- impact
- detection
- mitigation
- residual risk

At minimum, consider these controls:

- loopback-only binding
- Unix socket or named pipe ACLs
- per-user runtime directories
- restrictive filesystem permissions
- mutual authentication
- short-lived capability tokens
- message signing or HMAC
- nonce and timestamp validation
- idempotency keys
- schema validation
- size limits
- allowlisted commands and folders
- explicit sender identity
- explicit provenance shown to the model
- human approval policies
- audit logs
- rate limiting
- queue quotas
- process ownership checks
- secure secret storage
- version negotiation
- safe shutdown and drain behavior

### H. Plugin feasibility

Design a concrete OpenCode plugin or plugin-plus-daemon architecture.

The design must address:

1. Plugin lifecycle and registration.
2. Discovery of current project, worktree, session, and agent.
3. Receiving local messages.
4. Durable queueing.
5. Wake-up behavior.
6. Prompt submission into a session.
7. Sender provenance.
8. Busy-session serialization.
9. Permission and approval behavior.
10. Authentication and authorization.
11. Cross-platform transport abstraction.
12. Logging and auditing.
13. Crash recovery.
14. Backpressure.
15. Version compatibility.
16. Installation and configuration.
17. Test strategy.

Evaluate at least these implementation variants:

- plugin-only with a loopback HTTP listener
- plugin-only with Unix socket or named pipe
- plugin watching a filesystem mailbox
- shared local broker daemon plus lightweight plugins
- external coordinator using OpenCode's official server API

For each variant, identify exact OpenCode APIs or hooks required. Clearly state when the necessary hook does not exist.

### I. Proposed protocol

Specify a minimal interoperable protocol for agent-to-agent messages.

Include an example envelope with fields such as:

```json
{
  "protocol": "opencode-agent-ipc/1",
  "message_id": "uuid",
  "idempotency_key": "uuid-or-stable-key",
  "created_at": "RFC3339 timestamp",
  "expires_at": "RFC3339 timestamp or null",
  "sender": {
    "instance_id": "...",
    "project_id": "...",
    "session_id": "...",
    "agent": "..."
  },
  "recipient": {
    "instance_id": "... or null",
    "project_id": "... or null",
    "session_id": "... or null",
    "agent": "... or null"
  },
  "type": "prompt | notify | inspect_path | cancel | status_request | response",
  "payload": {
    "text": "...",
    "paths": ["..."],
    "metadata": {}
  },
  "delivery": {
    "requires_ack": true,
    "auto_execute": false,
    "human_approval_required": true
  },
  "security": {
    "key_id": "...",
    "nonce": "...",
    "signature": "..."
  }
}
```

Define:

- routing
- authentication
- authorization
- acknowledgment
- retries
- deduplication
- ordering
- expiration
- cancellation
- response correlation
- error codes
- version negotiation
- path handling
- attachment handling
- audit fields

Explain how the envelope should be rendered into model-visible context so the receiving agent knows the request is external.

### J. Human and model trust boundaries

Explain how a receiving agent should treat another agent's message.

Address:

- external messages should not automatically be considered human authorization
- another agent should not be able to grant permissions on behalf of the human
- another agent's instructions should normally be treated as untrusted task input
- repository content and mailbox content can contain prompt injection
- destructive actions should require explicit policy or human approval
- identity and provenance should be visible in the prompt
- external messages should not silently replace system or developer instructions

Recommend a trust policy and a default safe mode.

## Required report structure

Use this exact top-level structure:

```text
# Communication Between Concurrent OpenCode Agents on One Machine

## 1. Executive summary
## 2. Scope, terminology, versions, and evidence
## 3. OpenCode process, server, session, and agent architecture
## 4. Officially supported communication mechanisms
## 5. Source-supported but undocumented mechanisms
## 6. Wake-up and notification semantics
## 7. Direct prompt submission and session targeting
## 8. Prompt provenance and receiving-agent behavior
## 9. Busy-state, concurrency, queueing, and cancellation
## 10. Filesystem mailbox and watched-folder approaches
## 11. HTTP, sockets, named pipes, signals, PTYs, and other OS IPC
## 12. ACP as an inter-instance transport
## 13. MCP as an inter-agent transport
## 14. Server API, SDK, attach, web, and IDE options
## 15. Database manipulation and why it is or is not safe
## 16. Architecture comparison and recommendations
## 17. Security threat model and mitigations
## 18. Plugin feasibility and OpenCode hook analysis
## 19. Proposed plugin and broker architecture
## 20. Proposed message protocol
## 21. Proof-of-concept implementation plan
## 22. Testing strategy
## 23. Operational guidance and best practices
## 24. Limitations, unknowns, and OpenCode core gaps
## 25. Conclusions
## 26. Source and evidence index
```

## Mandatory tables

### Communication mechanism matrix

| Mechanism | Official support | Can notify | Can wake plugin/event loop | Can queue | Can submit prompt | Can interrupt | Provenance preserved | Authentication | Durable | Cross-platform | Main risks | Recommendation |

### Prompt provenance matrix

| Input path | Internal message role/type | Metadata preserved | Model sees origin | Permission behavior | Distinguishable from human input | Evidence |

### Busy-state behavior matrix

| Receiver state | Submission result | Queued or rejected | Concurrency behavior | Cancellation | Data-loss risk | Recommended sender behavior |

### Architecture comparison

| Architecture | Reliability | Security | Durability | Latency | Complexity | TUI compatibility | Unattended use | Version stability | Overall fit |

### Threat model

| Threat | Attack scenario | Affected methods | Likelihood | Impact | Detection | Mitigation | Residual risk |

### Plugin hook inventory

| Required capability | OpenCode API or hook | Available? | Stable? | Limitations | Workaround | Evidence |

## Required diagrams

Use Mermaid diagrams and accompanying prose for:

1. OpenCode process, client, server, and session topology.
2. Recommended local broker architecture.
3. Filesystem mailbox delivery and acknowledgment flow.
4. Prompt submission, provenance wrapping, and execution flow.
5. Authentication and authorization sequence.
6. Busy-session queue and cancellation state machine.

The report must remain understandable if Mermaid is not rendered.

## Proof-of-concept expectations

If the environment permits implementation, create a minimal, safe proof of concept that demonstrates one recommended architecture without modifying OpenCode core.

Prefer one of:

- a local broker plus OpenCode plugin
- a filesystem mailbox plus plugin watcher
- an external coordinator using an official OpenCode server API

The proof of concept should:

- bind only to loopback or use a per-user local IPC endpoint
- authenticate messages
- preserve sender provenance
- use idempotency keys
- validate message schemas
- queue when the target is busy
- require explicit opt-in before automatically initiating a model turn
- log delivery and acknowledgment without logging secrets
- fail closed
- include cleanup instructions
- include tests

Do not present terminal keystroke injection, direct database writes, unauthenticated sockets, or world-writable mailbox directories as recommended designs.

## Best-practice decision criteria

The conclusions must explicitly answer:

1. What is the safest method available today without modifying OpenCode?
2. What is the simplest method that works reliably?
3. What is the best method for unattended coordination?
4. What is the best method for two interactive TUI instances?
5. What is the best cross-platform method?
6. What method best preserves sender identity and provenance?
7. What method is least likely to break after an OpenCode upgrade?
8. When should a fresh `opencode run` subprocess be used instead of contacting an existing instance?
9. Which methods should never be used in production?
10. What OpenCode core enhancements would materially improve safe inter-agent communication?

## Citation and reproducibility requirements

For source citations, link to immutable tag- or commit-specific GitHub URLs and include the file, symbol, and line range where possible.

For runtime observations, record:

- operating system
- OpenCode version
- invocation command
- relevant environment variables
- transport and port or path
- result
- expected versus observed behavior

For official documentation, cite the exact page and access date.

Do not use uncited claims such as "OpenCode probably" or "this should work." Verify the behavior or label it unresolved.

## Safety rules

- Do not expose real tokens, credentials, prompts, or session content.
- Do not test against the user's real OpenCode data directory.
- Do not modify the user's real session database.
- Do not inject keystrokes into a real terminal.
- Do not bind experimental servers to non-loopback interfaces.
- Do not use world-readable or world-writable IPC endpoints.
- Do not assume another agent is trusted merely because it runs under the same user account.
- Do not allow an external agent to satisfy human approval requirements.
- Do not claim a plugin can inject prompts unless the exact supported API or hook is identified and tested.
- Do not conflate signaling, notification, message persistence, and actual model execution.

## Quality bar

The work is complete only if a reader can use it to decide and implement all of the following without substantial additional research:

1. Whether two running OpenCode instances can communicate natively.
2. How to notify a receiving instance that work is available.
3. How to submit a prompt, if supported.
4. How the receiving session and model perceive that prompt.
5. How to preserve and expose sender provenance.
6. How to route to the correct project, session, and agent.
7. How to queue, acknowledge, retry, cancel, and deduplicate work.
8. How to avoid corrupting OpenCode state.
9. How to secure the transport and trust boundary.
10. Whether a plugin is sufficient or an external broker is needed.
11. Which architecture should be chosen for interactive and unattended use.
12. What changes to OpenCode core would be required for capabilities that do not currently exist.

## Final validation checklist

Before finishing:

- Verify that every core question is answered directly.
- Separate official features from workarounds and speculative designs.
- Separate process signaling from actual prompt delivery.
- Distinguish an OpenCode process, server, client, session, and agent.
- Verify all prompt-provenance claims from source or experiments.
- Verify all busy-state and concurrency claims.
- Include the required tables and diagrams.
- Include a concrete recommended architecture.
- Include a security threat model.
- Include a plugin feasibility determination.
- Include a protocol proposal.
- Include implementation and testing guidance.
- Identify unresolved gaps honestly.
- Provide the exact output file paths and downloadable links or ZIP archive when the environment supports them.
