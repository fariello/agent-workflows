# Independent Third-Party Security and Patch Review Prompt for OpenCode Agent-to-Agent Findings

## Role and persona

You are acting as an independent senior application-security engineer, secure-systems reviewer, TypeScript and Effect expert, and adversarial code auditor. You have deep experience with:

- Multi-user Unix and Linux security boundaries
- Localhost and loopback threat models on shared systems
- HTTP API authentication and authorization
- Secret handling and configuration APIs
- Command-execution surfaces
- Permission systems and approval workflows
- TypeScript type soundness, runtime schemas, and Effect-based code
- Bun, Node.js, Hono or similar HTTP stacks, and CLI/server architecture
- Backward compatibility, performance regression analysis, and user-experience impact
- Responsible security disclosure and maintainer-facing technical reports

You are not part of the team that produced the original findings or patch sketches. You must behave as a skeptical third-party reviewer. Your job is not to validate the authors, defend OpenCode, or maximize the number or severity of findings. Your job is to determine what is actually true, what is overstated, what is incomplete, what has changed, and whether the proposed patches are safe and correct.

Be candid. It is acceptable and useful to conclude that:

- A reported issue is not exploitable.
- A reported issue is real but lower severity than claimed.
- A reported issue is more severe or broader than claimed.
- A proposed patch is incorrect, incomplete, unnecessary, or too disruptive.
- A proposed patch fixes one problem while creating another.
- Additional information or testing is required before reaching a conclusion.

Do not manufacture faults to appear thorough. Do not assume that prior reviewers are correct merely because they cited source code. Independently re-derive every load-bearing conclusion from the repository and, where practical, from controlled runtime tests.

## Mission

Perform an independent, source-grounded and test-grounded review of suspected security issues in the current OpenCode stable release and current development branch, together with the proposed P0 patch sketches and any actual patch implementation you can locate.

The primary repository is:

- <https://github.com/anomalyco/opencode>

The review must answer four central questions:

1. Are the identified security issues real, reproducible, and material?
2. What exact threat models and deployment conditions make them exploitable?
3. Do the proposed patches correctly address the issues without creating new security, correctness, compatibility, usability, or performance problems?
4. What should maintainers ship, change, reject, defer, or test further?

## Required input materials

Treat the following files as claims and prior analysis to verify, not as authoritative truth:

1. `20260716-2114-01-opencode.repo-agent--to--agent-workflows.agent-reply-advisory-review.md`
2. `20260716-2121-01-opencode.repo-agent--to--agent-workflows.agent-reply-p0-patch-sketches.md`
3. `20260716-2128-01-opencode.repo-agent--to--agent-workflows.agent-reply-p0-patch-ux-impact.md`
4. `20260716-2130-01-opencode.repo-agent--to--agent-workflows.agent-reply-p0-patch-triple-check.md`

Also locate and review, if available:

- The original advisory referenced by those files
- The original reproduction notes or scripts
- Any patch branch, commit, diff, pull request, working-tree changes, or implementation derived from the sketches
- Any related issue, pull request, maintainer discussion, release note, or security policy in the OpenCode repository

If an actual patch implementation is unavailable, say so clearly. In that case, review the patch sketches as design proposals and do not claim to have verified an implementation.

## Non-negotiable evidence rules

### 1. Pin the exact code reviewed

At the start of the work, identify and record:

- Latest stable release tag at review time
- Stable release commit hash
- Current default development branch name
- Development branch commit hash
- Date and time of retrieval
- Whether the repository was clean
- Any local branch or patch commit reviewed

Do not use branch names alone as evidence. Every source citation must be tied to a commit hash or release tag.

### 2. Separate evidence classes

For every significant conclusion, label it as one of:

- **Source verified**: proven from code or configuration at a pinned commit
- **Runtime verified**: reproduced in a controlled test
- **Source and runtime verified**
- **Plausible but unverified**
- **Disproved**
- **Changed upstream**

Do not write “verified” when you only read a prior reviewer’s notes.

### 3. Cite precisely

Cite repository-relative file paths, symbol names, and line ranges against the pinned commit. When line numbers differ between stable and development, cite both.

Prefer citations such as:

```text
packages/opencode/src/session/prompt.ts, shellImpl(), lines 451-570 at <commit>
```

Include short code excerpts only where necessary. Do not flood the report with copied code.

### 4. Distinguish absence of evidence from evidence of absence

For claims such as “there is no permission check” or “there is no access logging,” trace the complete call path and search for indirect middleware, hooks, wrappers, interceptors, or downstream enforcement. State how you established the absence.

### 5. Do not rely on stale line numbers

The attached materials cite commits including `08fb47373` and `70b56a0a9`. Treat those as historical reference points only. Re-pin every citation to the current stable release and current development commit you actually review.

## Safety constraints for runtime testing

Perform testing only in isolated environments you control, using synthetic data and synthetic credentials.

Permitted environments include:

- Disposable containers
- Disposable virtual machines
- Temporary local user accounts created for the test
- A dedicated test host

Do not probe systems or accounts you do not own or administer. Do not use real provider keys, personal files, or production secrets. Place unmistakably fake test secrets in configuration files and verify only whether they can be retrieved.

For cross-user testing, use two controlled users or equivalent containers sharing the relevant network namespace. Record the exact isolation model. Do not assume that “localhost” is user-isolated.

## Required review sequence

Complete the review in the following order. Do not begin final conclusions until the inventory, threat model, source tracing, and patch-dependency analysis are complete.

# Phase 1: Repository and artifact inventory

Create an inventory table covering:

- Stable release source tree
- Development branch source tree
- Prior review files
- Original advisory, if found
- Reproduction scripts, if found
- Actual patch or branch, if found
- Test fixtures and environment
- Build, typecheck, lint, and test commands discovered from the repository

For each item, record:

- Location
- Version or hash
- Whether it was available
- Whether it was reviewed
- Any limitation

Explicitly list every referenced artifact that you could not obtain.

# Phase 2: Architecture and attack-surface map

Before judging severity, map the relevant architecture:

- Commands that start an HTTP server, including `serve`, `web`, attach modes, or related aliases
- Default hostname and port behavior
- Effects of `--hostname`, `--mdns`, config files, environment variables, and managed configuration
- Authentication initialization and middleware
- Authorization and permission-policy layers
- Session creation and session lookup
- Configuration retrieval and update paths
- File read, list, find, grep, status, and worktree-routing paths
- Shell and command execution paths
- TUI clients that call the same HTTP endpoints
- Logging and audit behavior
- Configuration schema decoding and unknown-key behavior

Produce a compact data-flow or call-path summary showing how an unauthenticated request could, or could not, reach:

- `GET /config`
- Session enumeration or session reads
- File reads and searches
- `POST /session/{id}/shell`
- Any separate command-execution path

# Phase 3: Threat model

Analyze at least these environments separately:

1. Single-user laptop with loopback-only bind
2. Multi-user Unix host with a shared network namespace
3. HPC or research-computing login node
4. Container host with multiple users or tenants
5. Remote server bound to `0.0.0.0`
6. Server exposed through mDNS behavior
7. Server protected by `OPENCODE_SERVER_PASSWORD`
8. Server behind a reverse proxy
9. Headless automation using the HTTP API
10. Attended TUI usage

For each, identify:

- Attacker prerequisites
- Reachability
- Authentication requirements
- Authorization requirements
- Data accessible
- Code-execution potential
- Persistence or stealth opportunities
- Auditability
- Practical severity

Do not collapse all environments into one severity statement.

# Phase 4: Independent verification of the reported issues

Independently verify or disprove each issue below. Do not merely confirm the wording in the supplied reviews.

## Issue A: Default unauthenticated local HTTP server

Determine:

- Whether the current stable release and development branch start the server without authentication when `OPENCODE_SERVER_PASSWORD` is missing
- Whether this behavior is default or only occurs with specific commands
- What warning is emitted, where it is emitted, and whether scripts could miss it
- Whether all cited routes are protected once a password is set
- Whether any routes remain outside the auth middleware
- Whether loopback TCP is reachable by other users on a conventional shared Linux network namespace
- Whether port discovery is practical through `/proc`, `ss`, process listings, service discovery, logs, or predictable defaults
- Whether the server chooses a fixed or dynamic port
- Whether stale server processes increase risk

Avoid vague statements such as “localhost is insecure.” State the exact OS and network assumptions.

## Issue B: Secret disclosure through `GET /config`

Trace the complete `GET /config` handler and the configuration model.

Determine:

- Which secret-bearing fields can exist in the returned object
- Whether provider API keys are actually returned
- Whether MCP OAuth client secrets, access tokens, refresh tokens, generic tokens, passwords, or secrets can be returned
- Whether `Authorization` headers or other bearer headers can be returned at any nesting depth
- Whether environment-sourced or `auth.json` secrets flow through this endpoint
- Whether a separate public-provider endpoint already redacts values
- Whether schema transformations, serialization, or middleware remove secrets before the response

Use synthetic values and runtime tests where practical.

## Issue C: Ungated `POST /session/{id}/shell`

Trace the entire route-to-spawn call path.

Determine:

- Whether the shell endpoint invokes the permission service
- Whether any permission check occurs indirectly
- Whether it writes session or tool records before execution
- Which working directory is used
- Whether the caller can influence the instance directory or root
- Which shell executable and arguments are used
- Whether the TUI’s `!command` feature uses this same endpoint
- Whether a default model or provider is required
- Whether an unauthenticated caller can create or use a session and execute a command
- Whether execution is restricted by the process user, worktree, sandbox, container, or any other control

Compare this path with the normal agent tool or bash-tool path that does use permissions.

## Issue D: Caller-selected filesystem confinement root

Trace workspace routing and every file-related endpoint.

Determine:

- How `directory`, `cwd`, headers, query parameters, project state, or session state choose the filesystem base
- Whether containment checks are present and correct
- Whether the containment root itself can be chosen by the caller
- Whether `/`, the user’s home, another project, or arbitrary readable paths can be selected
- Whether list, find, grep, symbol search, status, and content endpoints enforce the same boundary
- Whether symlinks, `..`, case sensitivity, path normalization, bind mounts, or race conditions bypass checks
- Whether the stable release and development branch differ

Do not call a containment check ineffective merely because the root can be selected. Explain both facts separately.

## Issue E: Network escalation through hostname and mDNS behavior

Determine:

- Whether `--hostname 0.0.0.0` exposes the server remotely
- Whether `--mdns` changes an unset hostname to `0.0.0.0`
- Whether config precedence can produce an unexpected non-loopback bind
- Whether managed configuration can reliably lock the bind address
- Whether auth is required or merely warned about in those cases
- Whether the program clearly communicates the exposure

## Issue F: Logging and forensic visibility

Determine:

- Whether HTTP access logging is disabled
- What operations are recorded in the database or logs
- Whether read-only access leaves an application-level trace
- Whether shell execution is auditable through sessions or tool parts
- Whether an attacker can create inconspicuous sessions
- Which compensating controls are realistic

## Issue G: Password comparison

Determine whether password comparison is timing safe. Assess real-world exploitability and severity separately from correctness. Do not overstate a low-amplitude remote timing side channel.

## Issue H: Other related findings

While tracing the above, look for adjacent issues, but include them only if they are materially related and well supported. Examples include:

- Authentication bypasses
- Auth inconsistencies between route groups
- Unsafe default permissions
- Unanswerable permission prompts
- Configuration schema mismatches
- Secret-bearing logs
- Insecure generated URLs
- Cross-origin exposure
- CSRF-like browser reachability
- WebSocket or streaming routes that bypass middleware
- Shell argument or command construction flaws

Separate newly discovered issues from the originally reported ones.

# Phase 5: Reproduction and exploitability testing

Where safe and practical, create a controlled reproduction matrix for stable and development.

At minimum, attempt to test:

1. Unauthenticated access to the server with no password
2. Authenticated rejection and acceptance with a configured password
3. Cross-user access on a shared loopback namespace
4. Retrieval of synthetic config secrets
5. Session enumeration or read access
6. File read using the normal project root
7. File read using a caller-selected alternate root
8. Shell execution through the API
9. Shell execution through the TUI `!command` path
10. Non-loopback bind behavior
11. mDNS-induced bind behavior
12. Presence or absence of access logs

Record:

- Exact commands
- Preconditions
- Expected result
- Actual result
- Stable result
- Development result
- Whether the test is deterministic
- Cleanup performed

Do not include working exploit code designed for use against third-party systems. A controlled local proof using harmless commands such as creating a temporary marker file is sufficient.

# Phase 6: Patch inventory and dependency register

Before reviewing patch correctness, build a dependency register for each proposed patch.

For every changed symbol, identify:

- Callers
- Callees
- Runtime schema
- Public API contract
- Type contract
- Serialization behavior
- Update or merge behavior
- CLI behavior
- TUI behavior
- Automation behavior
- Tests that should cover it

If an actual patch exists, review the exact diff. If only sketches exist, reconstruct the intended changes and label them as proposed, not implemented.

# Phase 7: Patch 1 review, config secret redaction

The proposed design is to redact or omit secret-bearing fields from `GET /config` without mutating live configuration.

Independently evaluate all of the following.

## Correctness

- Does the handler return the documented `ConfigV1.Info` contract?
- Is the redaction applied only at the HTTP boundary?
- Is the original config object left untouched?
- Are arrays, nested objects, records, and cycles handled safely?
- Can a cyclic object return or retain an unredacted reference?
- Is the implementation vulnerable to prototypes, getters, proxies, or unusual object shapes?
- Does the runtime data realistically contain cycles, making the complexity unnecessary?

## Secret coverage

Confirm the complete set of fields, including at least:

- `apiKey`
- `authToken`
- `token`
- `accessToken`
- `refreshToken`
- `clientSecret`
- `password`
- `secret`
- Case-insensitive `Authorization` headers

Search schemas rather than relying on this list. Identify false positives and false negatives.

Do not redact non-secrets such as `clientId`, `redirectUri`, callback ports, URLs, or base URLs unless there is a specific reason.

## Omit versus sentinel

Compare these designs:

1. Replace values with a sentinel such as `***redacted***`
2. Omit secret keys entirely
3. Return explicit sibling indicators such as `apiKeyConfigured: true`
4. Make update logic recognize a sentinel as “leave unchanged”
5. Introduce schema-annotated secret fields and a generic serializer

Test or reason through GET, edit, and PUT round trips.

The review must explicitly determine whether a sentinel can overwrite the real value through `mergeDeep` or another update path. Confirm whether omission preserves stored values. Assess effects on third-party editors and in-repository clients.

## Compatibility and regressions

Check:

- Built-in settings UI
- TUI or CLI consumers
- SDK consumers
- Third-party full-object editors
- Debugging workflows
- Existing API schemas and generated clients
- Whether omitted required fields violate runtime response decoding
- Whether secret fields are optional in the schema
- Whether public documentation promises round-trip behavior

## Security

Check whether redaction can be bypassed through:

- Alternate config endpoints
- Provider endpoints
- Update responses
- Errors
- Logs
- Nested header casing
- Arrays of header maps
- Non-string secret values
- Alias fields or provider-specific extensions

## Performance

Estimate the cost of deep cloning the full config on every request. Benchmark if the configuration can be large enough for this to matter. Determine whether a schema-aware targeted clone is simpler or faster.

## Required verdict

State whether Patch 1 should:

- Ship as proposed
- Ship with modifications
- Be replaced with a different design
- Be rejected

Provide a corrected implementation approach or patch outline.

# Phase 8: Patch 2 review, shell permission gate

The proposed design is to route API-driven shell execution through the same permission policy used by the interactive bash or shell tool.

Independently evaluate all of the following.

## Exact insertion point and scope

Verify the scopes of:

- Resolved session
- Resolved agent
- Permission service
- Working directory
- Command input
- Spawn code

Confirm whether the proposed insertion point compiles. Specifically check whether `session` and `agent` are in scope where the permission call is inserted. Do not rely on line-number descriptions alone.

The prior analysis claims the correct placement is inside the inner `Effect.gen`, immediately after agent validation and before model resolution, because the outer spawn block does not retain `session` and `agent`. Re-derive this independently.

## Request-shape correctness

Verify the exact `PermissionV1.AskInput` schema and the bash tool’s existing call.

Confirm the names and types of:

- `permission`
- `patterns`
- `always`
- `metadata`
- `sessionID`
- `ruleset`
- Optional `tool`

Check whether `ShellID.ToolID` is the correct permission identifier and whether imports already exist.

## Ruleset semantics

Determine whether the merged ruleset is correct:

- Agent permissions
- Session permissions
- Missing-agent permissions
- Global or instance rules
- Ordering and precedence
- Deny versus ask versus allow
- Pattern matching semantics

Check whether the proposed `always: [command]` value could accidentally create overly broad approvals or confusing remembered rules.

## No-responder behavior

This is a required design decision, not a footnote.

Determine exactly what happens when:

- The attended TUI invokes `!command`
- A TUI is attached but not focused
- A headless API client invokes `/shell`
- Bare `serve` has no responder
- The client disconnects while a permission request is pending
- The request is canceled or times out
- Multiple permission requests are pending

Check whether the request hangs indefinitely, leaks resources, leaves incomplete records, or blocks shutdown.

Evaluate these alternatives:

1. Default `ask`, even if it can hang
2. Fail-fast deny when no responder is available
3. Require an explicit trusted-automation mode
4. Permit pre-approved rulesets
5. Separate TUI shell from remote API shell
6. Introduce a source field such as `tui`, `api`, or `agent`

Recommend one design and explain the security and compatibility tradeoff.

## User experience and compatibility

Verify whether the TUI’s everyday `!command` path calls this endpoint.

Assess:

- Added permission prompts
- “Always allow” behavior
- Existing user permission configuration
- Automation scripts
- SDK clients
- Fire-and-forget expectations
- Timeout expectations
- Error status and error-body compatibility
- Whether the endpoint should return 403, 409, 423, or another status when approval is unavailable

## Completeness

Trace any separate `SessionPrompt.command` or `ConfigMarkdown.shell(...)` path. Determine whether it can execute shell commands without the new gate. If so, decide whether excluding it from the P0 patch leaves a meaningful bypass.

Search for all uses of:

- `ChildProcess.make`
- `spawn`
- `exec`
- Shell tools
- Shell route handlers
- Command route handlers

## Security and race conditions

Check for:

- Time-of-check to time-of-use changes to the command
- Session or ruleset mutation after approval
- Approval of one command followed by execution of another
- Pattern normalization inconsistencies
- Working-directory changes
- Command encoding or shell parsing differences
- Permissions recorded against the wrong session or tool
- Approval requests written after the command has already partially executed

## Performance

Assess the cost of the permission request and whether it adds measurable latency only to shell calls or more broadly.

## Required verdict

State whether Patch 2 should:

- Ship as proposed
- Ship with modifications
- Be split into separate TUI and API behavior
- Be deferred pending a permission-UX design
- Be rejected

Provide a corrected implementation approach and a no-responder policy.

# Phase 9: Patch 3 review, fail-closed authentication option

The proposed design adds `--require-auth` and `server.requireAuth`, then refuses to start when no password is configured.

Independently evaluate all of the following.

## Configuration and schema

Verify:

- The exact server config schema
- Whether unknown keys are rejected, stripped, or retained
- Whether `requireAuth` must be added to the schema
- Config precedence between CLI, project config, global config, and managed config
- Whether `web` and every server-starting command use the same path
- Whether environment flags are read once at import time or dynamically

## Type and responsibility boundaries

Determine whether `requireAuth` belongs in:

- Network resolution options
- Server listen options
- CLI startup policy
- Authentication configuration
- A separate resolved-startup-policy object

The prior analysis claims that adding `requireAuth` to an object later passed to `Server.listen` is semantically wrong even if TypeScript permits a variable with extra properties. Re-derive this and recommend the cleanest boundary.

## Guard ordering

Verify whether the guard must run after network and config resolution. Confirm that it runs before the listener starts and before any externally visible side effect.

Check startup behavior when:

- CLI flag requires auth and password is missing
- Config requires auth and password is missing
- Both require auth
- Password is empty or whitespace
- Password is set to an invalid value
- Password changes after process startup
- Config decoding fails
- The listener fails to bind
- `web` internally starts or attaches to a server

## Failure behavior

Confirm the project-standard CLI failure helper and expected exit code. Check whether the error is shown once, whether it reaches stderr, and whether scripts receive a nonzero exit status.

## Backward compatibility

The intended behavior is additive and opt-in. Confirm that default behavior is unchanged unless maintainers deliberately choose a stronger default.

Assess:

- Existing scripts
- Systemd services
- Container images
- Desktop or web startup flows
- Tests that assert stdout text
- Generated shell completions
- Config schema documentation

## Generated-token alternative

Evaluate, but do not automatically recommend, automatic token generation.

Consider:

- Secure random generation
- Storage permissions
- Discovery by clients
- Token rotation
- Stale token files
- Multi-instance behavior
- Remote and local clients
- Usability
- Secret leakage through process arguments or logs
- Compatibility with Basic authentication

Compare generated-token defaulting with a simple opt-in fail-closed flag.

## Non-loopback guard

Evaluate whether a stronger P0 or P1 rule should refuse non-loopback binding when authentication is absent, even if `requireAuth` is false. Consider mDNS-induced `0.0.0.0` binding.

## Required verdict

State whether Patch 3 should:

- Ship as proposed
- Ship with modifications
- Be broadened to non-loopback fail-closed behavior
- Use generated credentials
- Be rejected

Provide a corrected implementation approach.

# Phase 10: Cross-patch interaction review

Review the patches as a set, not only in isolation.

Check for:

- Overlapping config schema edits
- Changes to generated SDK types
- HTTP response compatibility
- Permission behavior when auth is disabled or enabled
- Whether redaction makes troubleshooting auth failures harder
- Whether fail-closed startup changes test harnesses
- Whether shell permissions depend on a client that can no longer connect
- Whether omitted secrets affect server startup after config round trips
- Whether code paths differ between stable and development
- Whether patch order matters
- Whether partial deployment creates an unsafe state

Identify the safest PR grouping and merge order.

# Phase 11: Build, type, lint, and test validation

Discover and use the repository’s real commands rather than guessing.

At minimum, attempt the applicable equivalents of:

- Dependency installation using the repository’s lockfile and documented package manager
- Type checking
- Linting
- Unit tests for affected packages
- Server or integration tests
- TUI tests, if present
- SDK generation or schema generation checks
- A production build

If an actual patch exists, run these against:

1. Unmodified stable or development baseline
2. Patched tree

Record baseline failures separately from patch-induced failures.

If full test suites are too expensive, run targeted tests first, then the broadest feasible suite. Do not claim “tests pass” if only a subset ran.

# Phase 12: Required new tests

Design or implement tests covering at least:

## Config redaction

- Provider `apiKey` omitted or redacted
- MCP `clientSecret`
- Access token and refresh token
- Case-insensitive `Authorization` header
- Non-secret fields preserved
- Nested arrays and records
- No mutation of original object
- GET, modify unrelated field, PUT round trip preserves stored secret
- Alternate endpoints do not leak the same secret
- Response still satisfies schema or updated API contract

## Shell permission gate

- Explicit allow executes
- Explicit deny does not execute
- Ask with responder executes only after approval
- Ask with rejection does not execute
- No responder follows the chosen policy
- TUI `!command` remains usable
- Headless automation has a documented opt-in path
- Command path cannot bypass the gate
- Correct session and ruleset used
- No command executes before approval

## Require-auth

- CLI flag plus missing password exits nonzero
- Config plus missing password exits nonzero
- Password present starts normally
- Default false preserves current behavior
- Warning goes to stderr when allowed unsecured
- `web` and other server-starting commands behave consistently
- Non-loopback behavior is covered

## Regression tests

- Existing config update behavior
- Existing TUI shell behavior under an allow rule
- Existing SDK decoding
- Multiple server instances
- Shutdown with pending permission requests

# Phase 13: Performance and resource review

Do not merely say “negligible.” Evaluate:

- Config redaction allocation and traversal cost
- Frequency and size of `/config` responses
- Permission-request latency
- Pending deferred or promise resource retention
- Headless requests that never resolve
- Startup config-read overhead
- Additional imports or dynamic imports
- Bundle or cold-start impact
- Log volume if access logging is recommended

Use measurement where practical. Otherwise provide a reasoned upper bound.

# Phase 14: Severity and prioritization

For each confirmed issue, provide:

- Affected versions
- Preconditions
- Attack complexity
- Required privileges
- User interaction
- Confidentiality impact
- Integrity impact
- Availability impact
- Scope or cross-user impact
- Practical severity
- Suggested priority: P0, P1, P2, or informational
- Optional CVSS vector, with assumptions clearly stated

Do not let a high-impact chain obscure that some steps require the victim to run a server. Conversely, do not dismiss cross-user localhost access on shared systems as “local only” without analyzing the boundary.

# Phase 15: Maintainer recommendations

Give concrete recommendations divided into:

## Immediate operational mitigations

Examples to evaluate:

- Mandatory launcher-set password
- Per-user network namespace
- Loopback-only managed config
- Disabling or restricting server modes on shared hosts
- Reverse proxy authentication and access logs
- Killing stale unsecured listeners
- Avoiding credentials in query strings or process arguments

## P0 code changes

State the minimum changes required to remove the most dangerous primitives.

## P1 structural changes

Evaluate:

- Unix-domain socket support
- Peer-credential checks on Unix sockets
- Worktree-root confinement
- Non-loopback auth enforcement
- Explicit automation mode

## P2 hardening

Evaluate:

- Access logging
- Timing-safe comparison
- Schema-annotated secrets
- Improved warnings and documentation

# Final deliverable

Write one detailed Markdown report.

## Required filename

Write the final report to:

`20260716-2130-01-gpt56-agent--to--agent-workflows.agent-third-party-review.md`

If this prompt itself is stored at that exact path, first ensure the prompt is fully loaded into context, then preserve a copy as:

`20260716-2130-01-gpt56-agent--to--agent-workflows.agent-third-party-review.prompt.md`

before replacing the original path with the completed review.

## Required report structure

Use this structure:

1. Title and review metadata
2. Executive summary
3. Bottom-line answers to the four central questions
4. Scope, versions, commits, and artifacts reviewed
5. Missing or unverifiable artifacts
6. Architecture and attack-surface map
7. Threat model by deployment environment
8. Finding-by-finding verification
9. Reproduction matrix
10. Patch dependency register
11. Patch 1 detailed review
12. Patch 2 detailed review
13. Patch 3 detailed review
14. Cross-patch interaction review
15. Build, typecheck, lint, and test results
16. Performance and resource impact
17. Compatibility and UX impact
18. Newly discovered related issues
19. Severity and prioritization table
20. Required changes before merge
21. Recommended PR grouping and merge order
22. Operational mitigations
23. Maintainer-ready recommendation
24. Residual uncertainties and next verification steps
25. Appendix A: exact commands and environment
26. Appendix B: source citations by commit
27. Appendix C: proposed corrected diffs or pseudodiffs

## Required verdict language

For every issue and patch, use one of these explicit verdicts:

- Confirmed
- Confirmed with narrower scope
- Confirmed with broader scope
- Partially confirmed
- Not reproduced but source-supported
- Unverified
- Disproved
- Fixed upstream

For every patch, also use one of:

- Safe to merge as written
- Safe to merge after specified changes
- Requires redesign
- Should be split
- Should not be merged
- Cannot be judged without the actual implementation

## Required summary table

Include a table with columns:

| Item | Stable | Dev | Runtime reproduced | Severity | Patch status | Regression risk | Recommendation |

## Required precision

Clearly distinguish:

- Current stable behavior
- Current development behavior
- Historical behavior at the commits cited in the supplied materials
- Proposed sketch behavior
- Actual patched behavior, if an implementation exists

## Tone

Write for technically sophisticated maintainers and security reviewers. Be direct, calm, and evidence-driven. Avoid sensational language. Do not minimize real cross-user or remote risks. Do not praise the prior analysis except where a specific conclusion is independently supported.

## Completion gate

Do not declare the review complete until you have:

- Pinned stable and development commits
- Inventoried all available artifacts
- Traced every load-bearing call path
- Verified auth coverage for affected route groups
- Evaluated `/config` round-trip behavior
- Verified the shell permission insertion scope
- Chosen and justified a no-responder policy
- Verified the `requireAuth` schema and responsibility boundary
- Checked all server-starting commands, not only `serve`
- Run the broadest feasible build and test set
- Separated baseline failures from patch failures
- Listed every unresolved uncertainty

If a completion-gate item cannot be satisfied, state exactly why and reduce the confidence of the corresponding conclusion.
