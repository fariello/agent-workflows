# OpenCode shared-host security analysis: executive summary and report

## Executive summary

On a shared multi-user host, when a user runs a reachable OpenCode HTTP server (`opencode serve`/`web`, or a tool/config that opens one) without `OPENCODE_SERVER_PASSWORD`, any other unprivileged local user on the same host can, with no privilege and no credentials:

- discover the listener's port (via `/proc/net/tcp`; loopback is host-local, not UID-local),
- enumerate the victim's sessions, their working directories, and read the server config (which discloses a configured provider `apiKey` verbatim),
- read files the victim can read, by selecting the filesystem root the server operates against, and
- execute arbitrary shell commands as the victim via `POST /session/{id}/shell`.

We verified this end to end across two real Unix accounts on a controlled multi-user host, and colleagues corroborated key parts on HPC/Slurm environments. A correctly applied `OPENCODE_SERVER_PASSWORD` blocks the entire unauthenticated chain (confirmed). The server writes no HTTP access log, so read-only abuse is non-auditable from OpenCode itself.

We recognize much of this may be considered out of scope under the project's SECURITY.md ("server access when opted-in" is expected; the permission system "is not a sandbox"). We are raising it because of the shared-infrastructure blast radius and because a few contained changes can reduce risk while preserving legitimate use.

## Why this matters on shared / HPC infrastructure (context)

Our institutions have been encouraging OpenCode for complex HPC and research-computing work. On a Slurm head node or shared login node, an inexperienced user can unintentionally start a listener (directly, or indirectly via a tool that embeds the server) without realizing another unprivileged tenant can then act as them. On HPC that can expose credentials, research data, project storage, scheduler access, and very large compute allocations; at consortium scale the misuse potential (third-party attacks, data theft) is significant.

A blanket "prohibit TCP/IP listeners" policy is not workable in HPC: many legitimate scientific tools and pipelines depend on TCP/IP-based IPC, and several popular packages use the OpenCode server for IPC without necessarily enforcing auth or isolation. That is precisely why we would prefer contained upstream improvements over an institutional ban. HPC and research-computing colleagues have discussed raising this through CASC, NERCOMP, NEREN, Internet2, and related communities; we would much rather help address it collaboratively.

## Threat model and precondition

- Precondition (necessary): a reachable OpenCode HTTP listener exists for the victim. A plain TUI opens no listening socket and is not affected via this surface (verified on a fresh install). The listener may be started by `opencode serve`/`web`, or indirectly by a tool/integration/config that opens a server.
- Attacker: any unprivileged local user on the same host (no root, no shared group).
- Isolation reality: loopback (`127.0.0.1`) is host-local, not UID-local, in an ordinary shared Linux network namespace, so a co-tenant can reach another user's loopback listener. `/proc/net/tcp` lists all local listeners regardless of owner, enabling blind discovery.
- Network escalation: if the listener is bound to a non-loopback address (`--hostname 0.0.0.0`, or `--mdns` with no explicit hostname, which silently defaults the bind to `0.0.0.0`), the same chain is reachable from the network, not just local users.

## The verified chain (summary; full evidence in 02)

1. Discovery: enumerate `/proc/net/tcp` for a listener owned by the victim's uid. Blind, no privilege. VERIFIED cross-user.
2. Reachability: `GET /app` returns 200 with no credentials on an unsecured server, cross-user. VERIFIED.
3. Disclosure: `GET /session` lists the victim's sessions, ids, and working directories; `GET /config` returns config including a configured provider `apiKey` verbatim (no redaction). VERIFIED (session/dir cross-user; apiKey confirmed present on a configured account, absent only on a fresh unconfigured one).
4. File read: `GET /file/content?directory=/&path=<rel>` reads files bounded only by the victim's OS permissions. This is achieved by selecting the confinement root (down to `/`), NOT by path traversal (the `contains` guard is present and correct). VERIFIED (read world-readable and victim-owned files; correctly denied root-only and other-user 0600 files).
5. Code execution as the victim: `POST /session` (a new session the victim's TUI does not display) then `POST /session/{id}/shell` runs a command as the victim, in the victim's working directory, with no permission prompt. VERIFIED by file ownership (`id` output and a marker file owned by the victim uid).
6. Mitigation: with `OPENCODE_SERVER_PASSWORD` set, every step returns HTTP 401 without valid Basic credentials, and 401 with wrong credentials. VERIFIED cross-user. Caveat: the server fails OPEN if the variable does not reach the process (only a stdout warning; no "refuse to start" option).
7. Non-auditable: `opencode serve` emits no HTTP access log (source-confirmed). Read-only calls (`/file/content`, `/session`, `/config`) leave no trace; only session-creating / `/shell` actions persist in the local session DB.

## Scope honesty (what IS and is NOT claimed)

- IN (demonstrated): unauthenticated cross-user reach of an opted-in unsecured server; session/dir/config disclosure; `apiKey` disclosure via `/config`; caller-selected-root arbitrary file read within the victim's perms; `/shell` command execution as the victim; network escalation with non-loopback bind; mitigation via server password; absence of access logging.
- NARROWED / NOT claimed: `/session/{id}/message` (agent tool calls) is permission-gated and is NOT categorically ungated - only `/shell` is the demonstrated ungated path. The file-read is a caller-selected root, not `..` traversal. An attacker-created session is stealthy to an attended TUI; injecting into a victim's ACTIVE attended session was observed to be VISIBLE (rendered live), so we do not claim attended-session stealth.
- OUT (per the project's own SECURITY.md, acknowledged): that an opted-in server is reachable at all, and that the permission system is not a security sandbox. We do not dispute these; we focus remediation on the items that appear separable from "you opted into server mode" (secret disclosure over `/config`, caller-selected filesystem root, direct-shell permission inconsistency, silent non-loopback bind, absence of logging).

## Severity framing

- On a single-user machine: negligible (attacker and victim are the same user).
- On a shared/multi-user host running an unsecured listener: high (unauthenticated cross-user file read and shell execution as the victim, plus secret disclosure), escalating toward critical when bound non-loopback on a routable or internet-reachable host.
- Mitigated deployments (enforced per-server password; users blocked from starting unsecured servers) close the demonstrated unauthenticated chain; residual risk is that a password-protected loopback port is still reachable/brute-forceable and not UID-isolated, and that authentication alone does not fix the `/config` secret return, the caller-selected filesystem root, or the direct-shell permission inconsistency.

## Requested remediation posture (detail in 04)

Contained changes that preserve legitimate server/IPC use:
- Omit secrets from the `/config` response (public projection, not a sentinel).
- Authorize filesystem roots server-side rather than trusting a caller-supplied `directory` (including `/`).
- Route `/session/{id}/shell` through the same permission planner the shell tool uses, with deterministic headless behavior.
- A shared server-startup policy across every listener path (serve/web/attach/embedded) that can fail closed and refuse insecure non-loopback startup by default.
- Defense in depth: UNIX-domain socket + peer credentials, HTTP access logging, timing-safe password comparison, and deprecating the query-string auth token.

We are glad to help produce real, tested patches if the maintainers wish, and we will follow whatever format and disclosure timeline they prefer.
