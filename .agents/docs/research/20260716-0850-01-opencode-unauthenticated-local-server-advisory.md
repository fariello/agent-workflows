# Security advisory: OpenCode unauthenticated local control server enables cross-user agent and shell hijack on shared hosts

Status: security advisory (authored analysis, verified against OpenCode source and a live self-test on this host)
Date: 2026-07-16
Author: agent-workflows session (opencode)
Affected: OpenCode CLI/TUI, verified on v1.18.2; the no-listener-on-plain-TUI behavior re-confirmed on a fresh-install v1.18.3 (source refs at commit `70b56a0a9`)
Scope: SHARED / MULTI-USER hosts (HPC login nodes, shared dev servers, multi-tenant CI) WHERE A USER RUNS A LISTENING OPENCODE SERVER. NEGLIGIBLE on a single-user machine (the attacker and victim are the same user), and NOT APPLICABLE to a plain attended TUI that runs no server (see "Precondition" below).
Disclosure posture: COORDINATED. Notify OpenCode maintainers privately first with this repro and a fix proposal; hold public disclosure until they respond or a 30-45 day deadline elapses. This file is an internal record, not a public post.

## Summary

On a shared host, while a user is running a LISTENING OpenCode server (`opencode serve`, `opencode web`, or a TUI/config that opens a server) with no password, any OTHER local user on the same machine can take full control of that user's agent, including running arbitrary shell commands as the victim, with:

- no authentication (OpenCode does not require a password by default),
- no permission prompt (a tool call injected over the API executes without the interactive approval gate), and
- no visibility for the victim (the attacker creates a NEW session, which the victim's TUI does not display; demonstrated same-user).

This is a cross-user, stealth, remote-code-execution-as-the-victim condition on any multi-user box WHEN THE PRECONDITION (a listening server) holds. It is mitigable today (see the companion hardening how-to) but the default posture of a server is unsafe on shared systems. (One NARROWER sub-claim - invisibility of injecting into the victim's OWN attended session - is left unproven and is called out precisely below; it is not needed for the finding.)

## Precondition: a LISTENING server must exist (verified cross-user 2026-07-16)

The exposure requires an actual listening HTTP server. This is NOT automatic for the interactive tool. Verified by a real two-account test on this host: a second user (`victim-user`) running a fresh-install v1.18.3 plain `opencode` TUI (no config, launched from a non-home directory) owned ZERO listening sockets, was not reachable on any port, and its `/proc/<pid>/cwd` and `/proc/<pid>/environ` were Permission-denied to another non-root user. So a plain attended TUI is NOT cross-user reachable and cannot be probed or driven by another local user. The attack surface appears specifically when a user runs a server: `opencode serve` / `opencode web` (or a configuration that opens one). Earlier wording in this advisory that "the TUI itself embeds the server, so running the tool IS opening the port" was an over-generalization from same-user serve tests and is corrected here: the embedded-server code path exists, but a default interactive TUI does not open a listening TCP port.

For contrast, on the same test host the Antigravity IDE server and VS Code remote servers both enforce a connection token / CSRF token. OpenCode's no-auth-by-default (for the server it DOES open) is a specific design choice, not a platform norm.

## Verified facts

Auth is opt-in only, via the `OPENCODE_SERVER_PASSWORD` environment variable. With no password set, the authorization middleware is a complete pass-through: every route is open, including `POST /session/:id/message` (drive the agent) and `POST /session/:id/shell` (run a shell command in the session). Source: `server/auth.ts:19,24-26`, `httpapi/middleware/authorization.ts:106-107,122,139`.

There is no UNIX-domain-socket listener option, no per-session token, no UID / peer-credential check, and no `opencode.json` config key to require auth. The server config surface exposes only port, hostname, mdns, and cors. Source: `cli/network.ts:12-15`, `server/server.ts:200,214`, and the `serve` command flags (`--port`, `--hostname`, `--mdns`, `--cors` only).

Loopback binding (`127.0.0.1`) does NOT isolate by user. Any local user can connect to another user's loopback port, and `/proc/net/tcp` enumerates all local listening ports, so an attacker can discover the target port with no privileges.

Credentials may also be passed as an `?auth_token=<base64>` query parameter, which risks leaking into process listings and logs. Prefer the HTTP Basic header (username `opencode`).

## Live self-test (this host, v1.18.2, 2026-07-16)

Performed against a dedicated `OPENCODE_SERVER_PASSWORD`-protected `opencode serve` on `127.0.0.1:47811`, then torn down. All artifacts removed afterward.

1. Auth enforcement: `GET /app` returned HTTP 401 with no credentials, and HTTP 200 with `-u opencode:<password>`. So the password mechanism works when set.
2. Permission bypass: created a NEW session via `POST /session`, then `POST /session/{id}/message` instructing the agent to create `~/test/directory`. The directory was created with NO permission prompt and NO approval step (the small model fumbled the tool-call JSON a few times before emitting a valid `mkdir`, but no permission gate ever appeared). Default config carries no `permission` key (`agent.build.permission: {}`), so out of the box, API-driven tool calls are not gated. NOTE ON SCOPE: this was a session we created ourselves on our own throwaway server; it demonstrates the missing permission gate on API-driven tool calls, NOT anything about what an attached human would or would not see (see the "What we did NOT prove" section).
3. Credential leak: unauthenticated `GET /config` (i.e. reachable by any local user when no password is set) returns the configured provider `apiKey` in cleartext.

Item 1 is the mitigation working. Items 2 and 3 are the finding: with no password (the default), any local user can drive the agent AND read its provider API key.

## Impact and severity

- Cross-user code execution as the victim. Via `POST /session/:id/shell` (or by driving the agent to call its bash tool), an attacker runs commands with the victim's authority: their files, their credentials, their compute allocation.
- No permission gate. Under the default config, an API-injected tool call is not gated by the interactive approval a human sees in the TUI (verified on a session we drove). So an attacker driving the agent is not stopped by the permission prompt.
- Secret disclosure. The provider API key is readable over the unauthenticated `/config` endpoint.
- Stealth via attacker-created session (DEMONSTRATED, and this is the more relevant stealth vector). An attacker does not need to inject into the session the victim is watching. `POST /session` creates a BRAND-NEW session; a victim's TUI only displays the session(s) it launched, so an attacker-created session is by construction NOT in the victim's view. We demonstrated exactly this: the session we created (`ses_097117fc4...`) ran a real turn and created a file, and it never appeared in the maintainer's TUI. On a shared host an attacker can therefore create an invisible session and run code as the victim with no live indication to them. This is arguably CLEANER for an attacker than injecting into the attended session (no risk of the human seeing an unexpected turn scroll by).

Severity is HIGH specifically on shared / multi-user hosts (unauthenticated cross-user agent + shell control with no permission gate, plus API-key disclosure, plus attacker-created sessions the victim cannot see). On a single-user machine the finding is negligible (same-user).

## Precise scope of the stealth claim (what IS and is NOT proven)

Two distinct stealth claims must not be conflated:

- PROVEN and load-bearing: an attacker-CREATED session (or any session the victim's TUI did not launch) does not appear in the victim's attended TUI. This is inherent to how the TUI scopes what it displays, and we observed it directly. This alone supports "stealth cross-user code execution on a shared host."
- NOT proven (and less important): whether injecting a turn into the EXACT session the human is actively attached to, on the SAME embedded server their TUI talks to, is invisible to that human. Our earlier "no TUI indication" observations do NOT establish this, because that activity was in a different session and/or a different embedded-server instance (OpenCode runs one embedded server per TUI process; a dropped/reconnected TUI yields a new server). This sub-claim is not needed for the finding and should not be asserted without the test below.

### Test that would settle the remaining (narrower) sub-claim

On a single machine, one user: start `opencode` in the TUI, identify the exact `ses_...` that TUI is driving and the port of that TUI's own embedded server, then from another shell `POST /session/{that-exact-id}/message` THROUGH THAT SAME SERVER and watch whether the turn appears in the live TUI. This only settles the attended-session sub-claim; it does not affect the proven attacker-created-session stealth above.

## Reproduction (minimal)

On a host where a victim is running OpenCode with no `OPENCODE_SERVER_PASSWORD`:

1. Enumerate local listeners to find the victim's OpenCode port (`/proc/net/tcp` or `ss -tlnp`).
2. `curl http://127.0.0.1:<port>/config` reads the provider API key.
3. `POST /session` to create a NEW session (the victim's TUI will not display it), then `POST /session/{id}/message` or `POST /session/{id}/shell` to run commands as the victim. Under the default config no permission gate stops the tool call, and the victim sees no live indication because the session is not one their TUI launched.

## Proposed upstream fixes (for the maintainers)

1. A UNIX-domain-socket listener option with `0700` socket permissions, so the OS enforces per-user isolation (the only robust local isolation).
2. A config key to REQUIRE auth (fail closed) rather than defaulting to open, and ideally auth-on-by-default with a generated per-instance token written to a `0600` file.
3. A peer-credential (UID) check on the loopback listener.
4. Do not return secrets (provider `apiKey`) over `/config`; redact.
5. Ensure API-injected tool calls honor the same permission policy as interactive turns (fail closed).

## Recorded decisions from this investigation

- Use stance (hosts we control): OpenCode is forbidden on shared / HPC hosts unless `OPENCODE_SERVER_PASSWORD` is set, and `--mdns` is never used on a shared host. Single-user use is unaffected.
- We cannot stop others from running OpenCode on shared systems, so the mitigation is loud warning plus upstream pressure, not enforcement.
- Disclosure is coordinated (private notice + fix proposal first, public later on a deadline).

## Source references

- `server/auth.ts:19,24-26` (password is the only auth input)
- `httpapi/middleware/authorization.ts:106-107,122,139` (pass-through when no password)
- `cli/network.ts:12-15`, `server/server.ts:200,214` (loopback bind, no socket/UID option)
- `serve` command flags: `--port`, `--hostname`, `--mdns`, `--cors` (no `--auth`, no `--socket`)

Corroborated by the OpenCode-repo agent consulted over the API (source-grounded, but treat as authoritative-but-verify), and by the live self-test recorded above.
