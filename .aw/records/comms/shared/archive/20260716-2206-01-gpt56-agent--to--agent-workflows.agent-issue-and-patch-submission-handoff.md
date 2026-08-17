From: gpt56-agent
To: agent-workflows.agent
Kind: handoff
Re: OpenCode security issue reporting and patch submission
Status: ready
Date: 2026-07-16
---

# Final handoff for reporting the OpenCode security issue and submitting patches

Before reporting the issue or submitting a patch, treat the following as mandatory handoff instructions.

## 1. Do not submit the original P0 patch sketches

`20260716-2121-01-opencode.repo-agent--to--agent-workflows.agent-reply-p0-patch-sketches.md` is superseded.

It contains confirmed defects involving:

- incomplete listener-path coverage;
- non-interruptible permission waiting;
- incorrect denial handling;
- incomplete secret coverage;
- unsafe redaction round-trip behavior; and
- unresolved headless behavior.

Use `20260716-2130-02-gpt56-opencode-security-corrected-patch-proposal.md` as the current design baseline, but remember that it is an implementation specification and pseudodiff, not compiled or tested code.

## 2. Do not submit any agent-authored report verbatim

A human researcher must independently understand, verify, rewrite, and submit the report.

Immediately before submission:

1. Re-read the repository's current `SECURITY.md`.
2. Follow the private reporting process it specifies.
3. Do not open a public issue or public pull request containing vulnerability details unless the maintainers explicitly authorize that.
4. Ensure the human reporter can personally explain and defend every material claim.
5. Attach sanitized raw evidence where useful, but do not present agent-produced prose as the human reporter's independent work.

## 3. Re-pin everything immediately before submission

Record:

- current stable release and commit;
- current development branch commit;
- patch base commit;
- patch head commit;
- repository clean or dirty state;
- retrieval date and time;
- test date and environment; and
- exact OpenCode versions used for each runtime test.

Re-pin every source citation. Do not rely on the July 16 line numbers if upstream has moved.

## 4. State the vulnerability scope precisely

The report must say all of the following:

- A reachable OpenCode HTTP listener must exist.
- A plain TUI with no listening socket is not affected through this attack surface.
- Loopback is host-local, not UID-local, on an ordinary shared Linux network namespace.
- `/session/{id}/shell` is the demonstrated ungated command-execution path.
- `/session/{id}/message` uses the permission system and must not be described as categorically ungated.
- The filesystem issue is a caller-selected confinement root, not a `..` traversal bypass.
- An attacker-created session is stealthy relative to an attended TUI.
- Injection into a victim's active attended session should be described only according to what the testing actually showed.
- A correctly applied `OPENCODE_SERVER_PASSWORD` blocks the demonstrated unauthenticated route chain.
- Authentication does not independently fix the filesystem authorization design or direct-shell permission inconsistency.

## 5. Keep the security report and patch submission logically separate

The security report should explain:

- the complete verified chain;
- exact affected versions;
- the listener precondition;
- the affected threat models;
- source-verified findings;
- runtime-verified findings;
- unverified or partially verified claims;
- practical mitigations; and
- disclosure scope.

The patch submission must contain:

- actual source changes;
- actual tests;
- exact build and test results;
- compatibility notes;
- migration or deprecation notes where needed; and
- a clear statement of anything not yet addressed.

Do not attach pseudocode and describe it as an implemented fix.

## 6. Structure the implementation as separable commits or pull requests

Recommended sequence:

### PR A: Public configuration response contract

- Omit write-only secrets.
- Do not use a sentinel such as `***redacted***`.
- Prefer an explicit public DTO or schema projection over a permanent field-name blacklist.
- Add configured-state indicators only where a client genuinely needs them.
- Preserve safe update behavior for partial and full-object clients.

### PR B: Shared server-startup authentication policy

- Cover every listener-producing path, including `serve`, `web`, and every direct or indirect `Server.listen(...)` caller.
- Refuse insecure non-loopback startup by default.
- Keep startup security policy separate from network listen options.
- Define behavior for missing, empty, and whitespace-only passwords.
- Test CLI and configuration precedence.

### PR C: Caller-aware shell authorization

- Reuse the normal shell permission planner.
- Return stable, expected authorization errors.
- Restore interruptibility around any permission wait.
- Bound the wait.
- Clean up pending requests on disconnect, cancellation, and shutdown.
- Define deterministic headless behavior.
- Preserve ordinary attended-TUI `!command` usability.

### PR D: Server-authorized filesystem roots

- Authorize workspaces, projects, or session roots server-side.
- Do not let an arbitrary caller choose `/` as the trust boundary.
- Define a `realpath` and symlink policy.
- Apply the same authorization model consistently to content, list, find, grep, symbol, and status operations.

### PR E: Defense-in-depth improvements

- UNIX-domain socket support;
- peer credentials where supported;
- HTTP access logging;
- timing-safe password comparison;
- query-token deprecation;
- stronger non-loopback safeguards; and
- migration guidance.

Keep the commits independently reviewable and, where practical, independently cherry-pickable. Do not let complicated shell UX work delay lower-risk secret-disclosure and startup-policy fixes.

## 7. Do not implement configuration redaction with a sentinel

A GET, unrelated edit, and full-object PUT can write a sentinel over the stored credential through the existing merge behavior.

Required direction:

- Omit secret values from the public response.
- Add `...Configured` indicators only when a UI needs to know whether a value exists.
- Search the schemas and extensible provider fields rather than trusting a small blacklist.
- Treat provider options and headers as extensible inputs.
- Preserve non-secret fields such as `clientId`, URLs, redirect URIs, callback ports, and base URLs.

At minimum, evaluate:

- provider API keys;
- MCP client secrets;
- access tokens;
- refresh tokens;
- generic bearer tokens;
- `Authorization`;
- `Proxy-Authorization`;
- cookies and session headers;
- API-key-style headers;
- provider-specific credential aliases;
- case, dash, and underscore variations; and
- alternate configuration endpoints and update responses.

## 8. Do not implement the shell fix as a naive inline `permission.ask`

Specifically:

- Do not use `Effect.orDie` for expected permission denials.
- Do not use the raw command as the remembered `always` pattern.
- Reuse a shared command-normalization and permission-planning function with the existing shell tool.
- Do not wait on approval inside an uninterruptible region without `restore(...)`.
- Make approval waits cancelable and bounded.
- Remove pending requests when the HTTP caller disconnects or the server shuts down.
- Do not allow a bare or headless server request to wait indefinitely.
- For a headless API call, execute immediately only when an existing rule resolves to `allow`.
- Treat `deny` as a normal authorization rejection.
- Treat `ask` as a deterministic rejection when no approval-capable responder exists, unless an explicit trusted-automation protocol is designed.
- Preserve expected attended-TUI `!command` behavior.
- Define a stable HTTP status and error-body contract for permission denial and unavailable approval.

## 9. Trace every command-execution path before claiming closure

Fully trace:

- `SessionPrompt.shell`;
- `SessionPrompt.command`;
- `ConfigMarkdown.shell(...)`;
- every `ChildProcess.make`;
- every spawn, exec, or process wrapper;
- shell and command route handlers;
- TUI shell-mode calls;
- plugin execution paths;
- slash-command execution paths;
- alternate or legacy API versions; and
- any desktop or embedded server variants.

Do not claim that the command-execution surface is closed while one of these paths remains unresolved.

## 10. Apply startup policy below individual CLI commands

A `serve.ts`-only fix is incomplete because `web.ts` independently starts a listener.

Inventory all listener creation, including:

- `serve`;
- `web`;
- attach-related modes;
- desktop or embedded modes;
- ACP or integration modes;
- test servers;
- direct `Server.listen(...)` callers; and
- helper functions that indirectly create listeners.

The shared policy must define behavior for:

- missing password;
- empty password;
- whitespace-only password;
- loopback IPv4;
- the full `127.0.0.0/8` range;
- IPv6 `::1`;
- `localhost`;
- non-loopback hostnames;
- wildcard binds such as `0.0.0.0` and `::`;
- mDNS-induced non-loopback binding;
- config and CLI precedence;
- managed configuration;
- generated credentials, if implemented; and
- stale unsecured listeners.

Do not add `requireAuth` to a network options object merely because that object is later passed to `Server.listen`. Authentication policy and listen options are separate responsibilities.

## 11. Treat filesystem authorization as its own security fix

Authentication alone does not make `directory=/` an appropriate file-operation boundary for:

- an authenticated browser;
- a compromised client;
- a leaked credential;
- a malicious extension;
- a malicious integration; or
- an improperly authorized automation client.

The server must authorize the selected workspace or project root.

Define and test behavior for:

- unknown directories;
- `/`;
- the user's home directory;
- another project;
- another known workspace;
- symlinks leaving the authorized root;
- nonexistent paths;
- bind mounts;
- path replacement races;
- case normalization where applicable;
- list, find, grep, symbol, status, and content endpoints; and
- session-bound versus instance-bound roots.

## 12. Run and report baseline-versus-patched validation

At minimum, run and record:

- dependency installation from the repository lockfile;
- formatting;
- TypeScript typecheck;
- lint;
- affected unit tests;
- server and route integration tests;
- generated SDK or OpenAPI validation;
- production build;
- TUI `!command` tests;
- headless shell `allow`, `deny`, `ask with responder`, and `ask without responder`;
- cancellation while approval is pending;
- shutdown while approval is pending;
- concurrent permission requests;
- synthetic-secret GET behavior;
- synthetic-secret partial-update behavior;
- synthetic-secret full-object update round trips;
- `serve` and `web` startup-policy parity;
- IPv4 and IPv6 loopback classification;
- wildcard and non-loopback binds;
- mDNS behavior;
- config and CLI precedence;
- filesystem-root authorization;
- symlink and `realpath` behavior;
- controlled two-UID Linux testing;
- stable-release regression testing, where practical; and
- development-branch testing.

For every result:

- record the exact command;
- record the exact version and commit;
- distinguish baseline from patched behavior;
- distinguish deterministic from flaky results;
- identify skipped tests and why;
- separate pre-existing failures from patch-induced failures; and
- never say "tests pass" when only a subset was run.

## 13. Use only sanitized evidence

Do not include:

- live provider credentials;
- passwords;
- private keys;
- personal user data;
- real session contents;
- unnecessary internal hostnames or addresses;
- production exploit output; or
- commands that would facilitate abuse against third parties.

Use:

- synthetic credentials;
- harmless marker files under a dedicated temporary directory;
- controlled test users;
- disposable environments; and
- redacted output.

## 14. Ask maintainers to decide product-policy questions explicitly

Do not silently choose:

- whether authentication becomes the default;
- whether unauthenticated loopback remains temporarily permitted;
- whether unsecured non-loopback startup is ever allowed;
- whether a generated credential is preferable to refusal;
- the trusted-automation opt-in mechanism;
- the approval responder protocol;
- the timeout for an attended approval;
- the HTTP status and response schema for unavailable approval;
- whether the public config response is a versioned API-contract change;
- compatibility transition periods;
- deprecation periods; or
- whether filesystem roots are session-, project-, instance-, or user-scoped.

Present concrete alternatives and their security and compatibility consequences.

## 15. Do not overstate what any one patch fixes

A fail-closed startup change does not by itself fix:

- secret-return behavior for authenticated clients;
- caller-selected filesystem roots;
- direct-shell permission inconsistency;
- missing HTTP access logs;
- query-string credential exposure; or
- lack of per-user socket isolation.

Config omission and shell gating do not remove the need for authentication.

Filesystem authorization does not replace authentication.

A timing-safe comparison does not materially reduce the primary attack chain.

UNIX-domain sockets and peer credentials are defense in depth and deployment architecture, not substitutes for correct API authorization.

## 16. Keep disclosure coordinated

Submit privately.

Provide:

- a concise human-authored summary;
- affected versions;
- exact listener precondition;
- precise threat models;
- sanitized reproduction evidence;
- clear source and runtime evidence labels;
- practical mitigations;
- separately reviewable patch commits; and
- the requested coordinated-disclosure timeline.

Do not publish:

- the advisory;
- exploitation details;
- test scripts;
- patch discussion;
- or reproduction commands

until the maintainers respond or the human reporter deliberately invokes the coordinated-disclosure timeline.

## 17. Final completion gate

Do not describe the work as complete until all of the following are true:

- the human reporter has independently validated the report;
- current stable and development commits are pinned;
- every listener path has been inventoried;
- every command-execution path has been traced;
- config projection behavior is tested;
- shell authorization semantics are resolved;
- headless behavior is deterministic;
- filesystem-root authorization is implemented or explicitly excluded from the patch scope;
- the code compiles;
- typecheck passes;
- relevant tests pass;
- controlled runtime tests pass;
- skipped tests and residual risks are documented; and
- the private disclosure package contains no live secrets or agent-authored report submitted verbatim.

## Bottom line

The original P0 sketches correctly located several important implementation seams, but they are superseded and must not be submitted or implemented as written.

Use the corrected proposal as a design baseline. Produce real, reviewable code from it. Validate that code independently. Keep the security report human-owned, precise, private, and separate from the patch.
