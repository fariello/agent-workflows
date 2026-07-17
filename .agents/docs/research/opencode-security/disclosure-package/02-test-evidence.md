# Test evidence

Verification methods are labeled: [RUNTIME] = observed live on a controlled host; [SOURCE] = confirmed in the source tree (see 03); [REPORTED] = corroborated by HPC/research-computing colleagues on their own controlled environments (not all re-run by the primary reporter; testers deliberately not individually attributed). Payloads were harmless (`id`, `echo`, marker files under a dedicated temp dir); synthetic credentials only; test servers were torn down.

Environments:
- Primary controlled host: an ordinary multi-user Linux box with two real accounts (victim uid 1002, attacker uid 1000), fresh-install OpenCode v1.18.3 on the victim side; an earlier same-user self-test used v1.18.2.
- HPC corroboration: Slurm-based shared environments at peer research-computing sites (colleague-run; see [REPORTED] items).

## Baseline: a plain TUI is not an attack surface [RUNTIME]

A plain `opencode` TUI (no `serve`, fresh install, non-home cwd) owned ZERO listening sockets (checked via `/proc/net/tcp` state-`0A` entries matched to the user's uid). A non-root other user could not read its `/proc/<pid>/cwd` or `/proc/<pid>/environ` (permission denied). Conclusion: the vulnerability requires an actual listening server; a plain TUI is not reachable cross-user.

## T1 - Discovery, reachability, session and directory disclosure [RUNTIME]

Victim: `opencode serve` (unsecured), which bound `127.0.0.1:<port>`. Attacker (different uid), no privilege:
- Discovery: enumerated `/proc/net/tcp` for a LISTEN socket owned by the victim's uid and found the port with no help.
- Reachability: `GET /app` -> HTTP 200 (unauthenticated, cross-user).
- Disclosure: `GET /session` -> HTTP 200, returning the victim's session id, working directory (`/home/<victim>/...`), and title. `GET /project/current` returned the worktree.
Result: an unprivileged co-tenant discovers the port unaided, reaches the API unauthenticated, and reads the victim's session ids and working directories. [REPORTED] the discovery + reachability step was also reproduced on a Slurm head-node environment by a colleague.

## T2 - Secret disclosure via /config [RUNTIME]

`GET /config` -> HTTP 200 unauthenticated, cross-user, returning the merged config. On a configured account the response included the provider `apiKey` verbatim (a live `sk-...`, not read into any report). On a fresh unconfigured account there was no key to leak (`providers: []`). Refined claim: `/config` discloses whatever secrets are in the config file, including a provider `apiKey` when configured; it does not redact.

## T3 - Code execution as the victim via /session/{id}/shell [RUNTIME]

Because the fresh install had no configured model provider, the agent message path could stall at the model step, so the model-independent `/shell` endpoint was used. Attacker (different uid):
- `POST /session` created a NEW session on the victim's server (a session the victim's TUI does not display).
- `POST /session/{id}/shell` with `{"agent":"build","command":"id > <tmp>/xuser.txt; pwd >> ...; echo <marker> >> ..."}`.
Result (the decisive evidence): the marker file was created OWNED BY the victim uid/gid, its contents showed `uid=1002(<victim>) ...` and the victim's working directory; the response reported the command ran with `cwd` inside the victim's project. So a cross-user attacker executed arbitrary shell AS the victim, with no permission prompt, on a fresh unconfigured install (a built-in default model exists, so "unconfigured" is not a mitigation). [REPORTED] shell execution as the victim was corroborated on an HPC environment by a colleague.

## T4 - Password mitigation, from the attacker side [RUNTIME]

Victim restarted the server with `OPENCODE_SERVER_PASSWORD` set (must reach the process environment; inline `VAR=value opencode serve` or `export` both work; if it does not reach the process the server starts unsecured with only a stdout warning). Attacker re-ran T1/T2/T3 probes:
- No credentials: `GET /app`, `GET /session`, `GET /config`, `POST /session` all -> HTTP 401; `/session` leaked nothing.
- Wrong password: -> HTTP 401.
- Correct credentials (`-u opencode:<pw>`): -> 200.
Result: a correctly applied password blocks the entire unauthenticated chain. Operational caveat (and a finding): setting it is easy to get wrong (wrong shell, stale unsecured server still running, quoting); on failure it FAILS OPEN with only a stdout warning and no "refuse to start without auth" option.

## T5 - Network exposure with non-loopback bind [RUNTIME]

Victim ran `opencode serve --hostname 0.0.0.0`; the listener bound all interfaces. Attacker reached it via the host's routable LAN IP (not loopback): `GET /app` 200, `GET /session` 200 (sessions/dirs leaked), and `GET /file/content` (below) worked over the LAN IP. Result: non-loopback bind escalates the blast radius from local users to any host that can route to the machine. The server was killed immediately upon realizing it was network-reachable. `--mdns` reaches the same exposure by a quieter path (it defaults the bind to `0.0.0.0` when no explicit hostname is set). [REPORTED] colleagues flagged the `--mdns`/non-loopback footgun as the most likely accidental exposure in HPC, where users enable discovery.

## Unauthenticated filesystem read via caller-selected root [RUNTIME] [SOURCE]

`GET /file/content?directory=/&path=etc/passwd` returned the file unauthenticated. Mechanism (source-confirmed, see 03): the handler DOES confine reads to a base directory and rejects `..`/absolute escapes; the exposure is that the base directory is CALLER-CONTROLLED (via `?directory=` / `x-opencode-directory` / cwd). Passing `directory=/` sets the confinement root to `/`, so the read proceeds, bounded only by the victim's OS permissions. Verified scope: `etc/passwd`/`etc/hostname` (world-readable) READ; `etc/shadow` (root-only) and another user's `0600` key NOT (permission-bounded). The list/find/grep handlers run rooted at the same caller-chosen directory. This is the primary exfiltration path and needs no agent or model.

## T6 - Attended-TUI visibility [RUNTIME]

Victim attached a TUI to a running server (`opencode attach http://127.0.0.1:<port>`), opened a session, and watched. Attacker injected both a `/message` and a `/shell` into that exact active session through the same server. Both rendered LIVE in the victim's TUI (the injected prompt, the agent turn, and `$ echo <marker>` with its output); no permission prompt appeared for the `/shell`; the shell action was attributed to "the user" in the on-screen render and stored history. Conclusion: injecting into a victim's ACTIVE attended session is VISIBLE (not stealthy). The stealth vector is specifically an attacker-CREATED new session, which the victim's TUI does not display. We therefore do not claim attended-session stealth.

## Non-auditability [RUNTIME] [SOURCE]

`opencode serve` emits no HTTP access log: a serve run at `--log-level DEBUG --print-logs` recorded only its startup line; source confirms the HTTP router is built with per-request logging disabled. The application log is a structured event log, not an access log. Read-only calls (`/file/content`, `/session`, `/config`) leave no trace; only session-creating / `/shell` actions persist in the local session store. Consequence: read-only exfiltration is undetectable from OpenCode itself; forensics must come from the network/proxy layer.

## Mitigated production deployment (existence proof) [RUNTIME, same-user + launch-path inspection]

On a production shared OpenCode Web host, a Part-A-only run (cross-user attack correctly NOT attempted on production) found the deployment already mitigated: every web-TUI server is launched by a helper that generates a per-spawn random 32-char password and injects it via the environment (not argv), so `/app` and `/config` return 401 without credentials; and a wrapper blocks ordinary users from `serve`/`web`/`acp`/`attach`/`--port`/`--hostname` (the real binary is `0750 root:<exec-group>`). This demonstrates the risk is deployable-mitigable today. Residuals: loopback still enumerable/not UID-isolated; the allow-group that can bypass the wrapper must be kept minimal; gateway per-principal logging should be confirmed.

## Evidence hygiene

All runtime tests used synthetic credentials, harmless commands (`id`, `echo`, `pwd`), and marker files under a dedicated temporary directory, which was removed afterward. No live secret value was recorded in any artifact. Test servers were torn down and confirmed not listening.
