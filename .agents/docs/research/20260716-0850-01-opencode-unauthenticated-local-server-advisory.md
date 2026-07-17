# Security advisory: OpenCode unauthenticated local control server enables cross-user agent and shell hijack on shared hosts

Status: security advisory (authored analysis, verified against OpenCode source, a same-user self-test, AND a two-account cross-user campaign on this host)
Date: 2026-07-16
Author: agent-workflows session (opencode)
Affected: OpenCode CLI/TUI. Same-user self-test on v1.18.2; cross-user campaign (T1-T5) and the no-listener-on-plain-TUI behavior on a fresh-install v1.18.3 (source refs at commit `70b56a0a9`)
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

## Cross-user verification campaign (two real Unix accounts, 2026-07-16)

The self-test above was same-user. The following was run with TWO real accounts on this host: victim `victim-user` (uid 1002) running the server, attacker `attacker-user` (uid 1000) doing the probing. This is the actual threat model and moves the central claims from PREDICTED to VERIFIED. All payloads were harmless (`id`, `echo`, reading benign world-readable files); test servers were killed afterward. OpenCode versions: fresh-install v1.18.3 on the victim side.

Setup baseline (before any server): a plain `opencode` TUI as `victim-user` owned ZERO listening sockets; `attacker-user` could not read its `/proc/<pid>/cwd` or `/proc/<pid>/environ` (Permission denied, non-root). So a plain TUI is not an attack surface and is not cross-user observable. The tests below all require the victim to run a LISTENING server.

- T1 - Discovery + reachability + session/directory disclosure (UNSECURED `opencode serve`). As `attacker-user`, with no privilege: enumerated `/proc/net/tcp` for state-`0A` sockets owned by uid 1002 and DISCOVERED the victim's port blind (no help). `GET /app` returned HTTP 200 (reachable, unauthenticated, CROSS-USER). `GET /session` returned HTTP 200 and LEAKED the victim's session: id `ses_09311af87...`, working directory `<victim-home>/VC/opencode-tests`, title. `GET /project/current` returned the worktree. RESULT: a cross-user attacker discovers the port unaided, reaches the API unauthenticated, and reads the victim's session ids and working directories. `/session/active` errored on a bare serve (no attended TUI, so no single active session), which is the correct behavior; `/session` is the reliable enumeration source.

- T2 - Secret disclosure via `/config`. `GET /config` returned HTTP 200 unauthenticated cross-user (config readable). On THIS victim it exposed NO key because it was a fresh, unconfigured install (`providers: []`, no `apiKey`). REFINED CLAIM: `/config` is readable cross-user without auth and leaks whatever secrets live in the victim's config, INCLUDING a provider `apiKey` when one is configured (as it was on the maintainer's own account in the same-user self-test, where `/config` returned a live `sk-...`). A fresh/unconfigured account has no key to leak; a real working account typically does.

- T3 - Code execution as the victim via `POST /session/{id}/shell` (model-independent). Because the fresh install had no model provider, the agent path (`/session/{id}/message`) could stall at the model step, so we used `/shell`, which runs a command server-side with no LLM. Request shape (from `/doc`): requires `agent` + `command`. As `attacker-user`: `POST /session` created a NEW (stealth) session on the victim's server, then `POST /session/{id}/shell` with `{"agent":"build","command":"id > /tmp/aw-verify/xuser.txt; pwd >> ...; echo AW-XUSER-OK >> ..."}`. RESULT (the smoking gun): the file was created OWNED BY `victim-user` (`-rw-rw-r-- 1 victim-user victim-user ...`), contents `uid=1002(victim-user) ... <victim-home>/VC/opencode-tests`, and the response reported `providerID: opencode / modelID: big-pickle` and `cwd: <victim-home>/VC/opencode-tests`. So a cross-user attacker executed arbitrary shell AS the victim, in the victim's working directory, with NO permission prompt, on a fresh unconfigured install (a built-in default model exists, so "unconfigured" is not a mitigation). The stealth sessions created this way persist in the victim's session list.

- T4 - Password mitigation (cross-user, from the attacker side). The victim restarted the server WITH `OPENCODE_SERVER_PASSWORD` set (note: it must reach the process environment; the inline `VAR=value opencode serve` form or an `export` both work, but if the variable does not reach the process the server starts UNSECURED with only a one-line stderr warning - see the important gotcha below). Re-run of the T1/T2/T3 probes from `attacker-user` with NO credentials: `GET /app`, `GET /session`, `GET /config`, and `POST /session` all returned HTTP 401; `/session` leaked nothing (empty body). A WRONG password also returned 401. With the CORRECT credentials (`-u opencode:<pw>`) the same calls returned 200. RESULT: the password mechanism, once actually applied, blocks the entire cross-user attack chain (enumeration, config read, stealth-session creation, shell). Same auth middleware gates the filesystem endpoints below.

  GOTCHA (operational, and itself a finding): setting the password is easy to get wrong (wrong shell, stale unsecured server still running, quoting), and when it is wrong it FAILS OPEN - the server runs fully unsecured with only an easily-missed stderr warning and no "refuse to start without auth" option. On a hosted service, do not rely on users/operators to set an env var correctly; enforce it in the launcher (wrapper/systemd unit) and/or use per-user network isolation so a misconfiguration is not cross-user reachable.

- T5 - Network exposure with `--hostname 0.0.0.0` (UNSECURED). The victim ran `opencode serve --hostname 0.0.0.0`. Verified the listener bound `0.0.0.0:PORT` (all interfaces). As `attacker-user`, reached it via the host's ROUTABLE LAN IP (`192.168.1.99:PORT`) and the docker bridge (`172.17.0.1:PORT`), NOT loopback: `GET /app` 200 and `GET /session` 200 (leaked sessions/dirs) over the non-loopback address. `GET /file/content` (below) also worked over the LAN IP. RESULT: `--hostname 0.0.0.0` escalates the blast radius from "any local user" to "any host that can route to this machine" (the LAN/subnet, and potentially beyond if the host has any inbound path). The maintainer killed this server immediately on realizing it was internet-reachable. `--mdns` reaches the same non-loopback exposure by a quieter path (it advertises and rebinds beyond loopback), which is why the guidance is "never `--mdns` / never `0.0.0.0` on a shared or networked host."

- Unauthenticated direct filesystem read/search (discovered during T5). The API exposes filesystem endpoints that need no agent and no model: `GET /file/content?directory=/&path=<relative>` returned file contents unauthenticated. Verified scope (reads run as the victim's process, so ordinary Unix permissions apply): `etc/hostname` and `etc/passwd` (world-readable) were READ successfully; `etc/shadow` (root-only) and another user's `0600` SSH key were NOT (permission-bounded, returned error or empty). Related endpoints present: `/file`, `/file/content`, `/find/file`, `/find/symbol`, `/api/fs/read/*`, `/api/fs/list`, `/api/fs/find`. RESULT: an unsecured server is a direct, model-independent, unauthenticated file read + search primitive rooted at the worktree (which was `/`), bounded only by the serving user's file permissions - i.e. an attacker can read EVERYTHING the victim can read (their whole home, source, `.env`, credentials, tokens, plus all world-readable files), and over the LAN when bound to `0.0.0.0`. This is the primary exfiltration path and is cleaner for an attacker than driving the agent.

- No request logging / non-auditable (verified two ways). `opencode serve` emits NO HTTP access log. Verified black-box: a serve run at `--log-level DEBUG --print-logs` recorded only its startup line, nothing per-request. Verified white-box: the OpenCode-repo agent confirmed from source that the HTTP router is built with `disableLogger: true` and `disableListenLog: true` (`packages/opencode/src/server/server.ts:103-104`); the `~/.local/share/opencode/log/opencode.log` file is the app's structured event log, not an access log. RESULT: there is no native record of who connected or what files were read. Read-only calls (`/file/content`, `/session`, `/config`) leave ZERO trace; only session-creating / `/shell` actions persist as session data in the victim's `~/.local/share/opencode/opencode.db`. The vulnerability is therefore not just exploitable but NON-AUDITABLE from OpenCode itself - detection/forensics must come from the network/proxy layer.

Net: T1-T3 and the filesystem-read finding jointly demonstrate, across real Unix accounts, unauthenticated cross-user read of the victim's files + session data and arbitrary code execution as the victim; T5 shows this extends to the network with `0.0.0.0`/`--mdns`; T4 shows a correctly-applied `OPENCODE_SERVER_PASSWORD` blocks all of it; and the logging finding shows abuse is undetectable from OpenCode.

## Impact and severity

- Cross-user code execution as the victim (VERIFIED cross-user, T3). Via `POST /session/:id/shell` (or by driving the agent), an attacker runs commands with the victim's authority: their files, their credentials, their compute allocation. Confirmed by file ownership: a command we sent produced a file owned by `victim-user` in the victim's working directory.
- Unauthenticated filesystem read + search (VERIFIED cross-user, T5). `GET /file/content` and the `/find`/`/api/fs` endpoints read and search files with no auth and no agent/model, bounded only by the serving user's permissions - i.e. everything the victim can read. This is the primary exfiltration path.
- No permission gate. Under the default config, an API-injected tool call is not gated by the interactive approval a human sees in the TUI. So an attacker driving the agent is not stopped by the permission prompt.
- Secret disclosure. The unauthenticated `/config` endpoint is readable cross-user and leaks whatever secrets are in the victim's config, including a provider `apiKey` when configured (verified present on a configured account; absent only on a fresh unconfigured one).
- Network reach with `0.0.0.0`/`--mdns` (VERIFIED, T5). Binding non-loopback exposes all of the above to any host that can route to the machine, not just local users.
- Non-auditable. `opencode serve` writes no HTTP access log (verified black-box and from source: `disableLogger`/`disableListenLog`). Read-only exfiltration leaves no trace; only session/`shell` actions persist in the victim's local DB. Abuse cannot be detected or proven from OpenCode itself.
- Stealth via attacker-created session (DEMONSTRATED). `POST /session` creates a BRAND-NEW session; a victim's TUI only displays the session(s) it launched, so an attacker-created session is by construction NOT in the victim's view. On a shared host an attacker can create an invisible session and run code as the victim with no live indication.
- Mitigation confirmed (T4). A correctly-applied `OPENCODE_SERVER_PASSWORD` returns 401 to every unauthenticated/wrong-credential probe and blocks the entire chain; but it fails OPEN if misapplied and has no "require auth" enforcement.

Severity is HIGH specifically on shared / multi-user hosts running an unsecured server (unauthenticated cross-user file read + shell execution as the victim, API-key disclosure when configured, network-reachable with `0.0.0.0`/`--mdns`, and non-auditable), escalating toward CRITICAL when bound non-loopback on a routable/internet-reachable host. On a single-user machine the finding is negligible (same-user); a plain TUI that opens no server is not affected.

## Precise scope of the stealth claim (both cases now verified)

Two distinct stealth claims, BOTH now resolved (T6, 2026-07-16):

- STEALTHY - attacker-CREATED session: a session the victim's TUI did not launch does NOT appear in the victim's attended TUI. Inherent to how the TUI scopes what it displays; observed directly. This is the load-bearing stealth vector and supports "stealth cross-user code execution on a shared host."
- NOT stealthy - injection into the victim's ACTIVE attended session: VERIFIED VISIBLE. In T6 the victim (`victim-user`) attached a TUI to a serve via `opencode attach http://127.0.0.1:4096`, opened a session ("Greeting request", `ses_09271ec3...`), and watched. The attacker (`attacker-user`) POSTed both a `/message` and a `/shell` (harmless echo) to that exact session id through the same server. BOTH rendered LIVE in the victim's TUI with no keypress: the injected prompt appeared, the agent's turn appeared, and the shell command showed as `$ echo AW-T6-INJECTED-SHELL-...` with its output. NO permission prompt appeared. The shell action was attributed to "the user" in both the on-screen render and the stored message history. CONCLUSION: injecting into the attended session is observable to an attentive human, so a real attacker prefers a NEW session (silent). The stealth claim is thus correctly bounded: new session = invisible; attended session = visible.

Incidental confirmations from T6: no permission gate even with a live human attached; injected actions are attributed to the victim in storage and on screen; the injected turns are recorded in the session history (verified via `GET /session/{id}/message`).

## Reproduction (minimal)

On a host where a victim runs a LISTENING OpenCode server (`opencode serve`/`web`) with no `OPENCODE_SERVER_PASSWORD` (all steps verified cross-user 2026-07-16):

1. Discover the victim's port unaided: read `/proc/net/tcp` for state-`0A` (LISTEN) sockets and match the uid column to the victim's uid (or `ss -tlnp`). No privilege needed.
2. Enumerate + disclose: `curl http://127.0.0.1:<port>/session` lists the victim's sessions, ids, and working directories; `curl .../config` reads config (and the provider `apiKey` if configured).
3. Exfiltrate files: `curl "http://127.0.0.1:<port>/file/content?directory=/&path=<relative-path>"` reads any file the victim can read (no agent, no model, no trace).
4. Execute as the victim: `POST /session` (a NEW, TUI-invisible session), then `POST /session/{id}/shell` with `{"agent":"build","command":"<cmd>"}`. Runs as the victim, no permission prompt.
5. If the server is bound `0.0.0.0` (or started with `--mdns`), all of the above also work from the host's LAN IP, not just loopback.

Mitigation check: with `OPENCODE_SERVER_PASSWORD` correctly set, steps 2-4 return HTTP 401 without valid `-u opencode:<pw>` credentials.

## Proposed upstream fixes (for the maintainers)

1. A UNIX-domain-socket listener option with `0700` socket permissions, so the OS enforces per-user isolation (the only robust local isolation).
2. A config key to REQUIRE auth (fail closed) rather than defaulting to open, and ideally auth-on-by-default with a generated per-instance token written to a `0600` file. This directly addresses the verified fail-open gotcha (a missing env var silently yields a fully open server).
3. A peer-credential (UID) check on the loopback listener.
4. Do not return secrets (provider `apiKey`) over `/config`; redact.
5. Ensure API-injected tool calls honor the same permission policy as interactive turns (fail closed).
6. Gate the filesystem endpoints (`/file/content`, `/file`, `/find/*`, `/api/fs/*`) behind auth and consider constraining them to the worktree rather than allowing absolute/`/`-rooted reads (verified as an unauthenticated file-read primitive bounded only by the serving user's permissions).
7. Provide an HTTP access log option (or log per-request at DEBUG). Request logging is currently disabled by design (`disableLogger`/`disableListenLog`), making abuse non-auditable from OpenCode.
8. Refuse `--hostname 0.0.0.0` / `--mdns` without auth, or at least warn loudly, since non-loopback binding turns a local issue into a network-reachable one.

## Recorded decisions from this investigation

- Use stance (hosts we control): OpenCode is forbidden on shared / HPC hosts unless `OPENCODE_SERVER_PASSWORD` is set, and `--mdns` is never used on a shared host. Single-user use is unaffected.
- We cannot stop others from running OpenCode on shared systems, so the mitigation is loud warning plus upstream pressure, not enforcement.
- Disclosure is coordinated (private notice + fix proposal first, public later on a deadline).

## Source references

- `server/auth.ts:19,24-26` (password is the only auth input)
- `httpapi/middleware/authorization.ts:106-107,122,139` (pass-through when no password)
- `cli/network.ts:12-15`, `server/server.ts:200,214` (loopback bind, no socket/UID option)
- `serve` command flags: `--port`, `--hostname`, `--mdns`, `--cors` (no `--auth`, no `--socket`)
- `server/server.ts:103-104` (`disableLogger: true`, `disableListenLog: true` - no HTTP request log; confirmed by the OpenCode-repo agent from source, archived at `.agents/comms/shared/archive/20260716-2039-01-...`)

Corroborated three ways: source review (the OpenCode-repo agent, source-grounded, authoritative-but-verify), the same-user self-test, AND the two-account cross-user campaign (T1-T5) recorded above with victim `victim-user` and attacker `attacker-user`. Companion documents: hardening how-to `20260716-0850-02`; verification protocol `.agents/prompts/reusable/20260716-1342-01`; agent runbook `.agents/prompts/reusable/20260716-1342-02`; detection findings `.agents/docs/research/opencode-security/20260716-1725-01`.
