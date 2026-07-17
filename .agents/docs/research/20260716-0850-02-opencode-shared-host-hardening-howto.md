# Hardening OpenCode on shared / HPC hosts (how-to)

Status: operational how-to (companion to the security advisory `20260716-0850-01`)
Date: 2026-07-16
Author: agent-workflows session (opencode)
Applies to: OpenCode CLI/TUI on any SHARED / MULTI-USER host (HPC login node, shared dev server, multi-tenant CI). On a single-user machine this is not required.

## READ THIS FIRST (loud warning)

On a shared or multi-user host, while `opencode` is running, ANY other local user on the same machine can make your agent do anything, including run shell commands as YOU, read YOUR files, and use YOUR credentials, with no permission prompt, and WITHOUT it showing up in your session. They do this by creating a NEW session against your server, which your TUI does not display; they can also read your provider API key from the unauthenticated `/config` endpoint. You will see no live sign of any of it.

This is because OpenCode's local control server has no authentication by default (see advisory `20260716-0850-01`). The steps below reduce the exposure. Only a per-user network namespace fully closes it.

## Do this every time you run OpenCode on a shared host

### 1. Always set a server password (mandatory)

Set `OPENCODE_SERVER_PASSWORD` before launching OpenCode. The embedded TUI server needs it too, not just `opencode serve`.

    export OPENCODE_SERVER_PASSWORD="$(head -c 24 /dev/urandom | base64)"

Put it in your shell profile if you always want it, but note: environment variables can leak (for example via a debugger or a misconfigured dump), so treat this as better-but-not-sufficient. When you connect a client, use HTTP Basic auth with username `opencode` and this password. Avoid the `?auth_token=` query parameter (it can leak into process listings and logs); use the Authorization header.

### 2. Never use `--mdns` on a shared host

`--mdns` causes the server to advertise and rebind beyond loopback (to `0.0.0.0`), widening exposure from local users to the whole network. Do not pass it on shared systems.

### 3. Best available isolation: a per-user network namespace

Password auth still leaves the port reachable and brute-forceable, and env vars can leak. The only robust local isolation is to run OpenCode inside a network namespace that other users cannot enter.

Option A, unshare (per invocation):

    unshare -rn --map-root-user bash -lc 'ip link set lo up; export OPENCODE_SERVER_PASSWORD=...; opencode'

Option B, systemd user service with `PrivateNetwork=`:

    # ~/.config/systemd/user/opencode.service
    [Service]
    PrivateNetwork=true
    Environment=OPENCODE_SERVER_PASSWORD=...
    ExecStart=%h/.opencode/bin/opencode serve --hostname 127.0.0.1

"Password + netns" is safe. "Password only" is better-but-not-sufficient. "Nothing" is fully exposed.

## Quick self-check: am I exposed right now?

    ss -tlnp | grep opencode        # is my OpenCode server listening?
    # From another shell as the SAME user, verify auth is on (should be 401 without creds):
    curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:<port>/app          # want 401
    curl -s -o /dev/null -w '%{http_code}\n' -u opencode:$OPENCODE_SERVER_PASSWORD http://127.0.0.1:<port>/app  # want 200

If the first curl returns 200, you have NO password set and are exposed to every user on the box. Set `OPENCODE_SERVER_PASSWORD` and restart OpenCode.

## Reference architecture for a hosted / multi-user OpenCode service (operator-side)

If you OPERATE a hosted OpenCode offering (many users, shared infrastructure), the per-user advice above is not enough; harden at the platform level. A real deployment we verified (`opencode.its.uri.aws`) uses a two-layer pattern that both enforces auth and prevents users from creating an unsecured server. Recommended pattern (findings note: `research/opencode-security/20260716-2108-01-...`):

1. Wrap the binary. Ship a wrapper as `opencode` on `PATH` that, for ordinary users (not in a tightly-controlled allow-group, not root), BLOCKS `serve`, `web`, `acp`, `attach`, and `--port`/`--hostname`, and directs them to the managed web interface. Keep the real binary non-world-executable (for example `0750 root:<exec-group>`). This removes the "user starts an unsecured server" path entirely.
2. Inject a per-spawn password. Launch every managed server via a helper that generates a per-spawn random password (for example 32 chars from `/dev/urandom`) and passes it through the ENVIRONMENT (`OPENCODE_SERVER_PASSWORD=...`), NOT on the command line (argv is visible in `ps`/`/proc/<pid>/cmdline`; the environment is owner-readable only). Bind `127.0.0.1` and set a CORS allowlist for the real web origin. Result: every server returns 401 without credentials.
3. Guard the allow-group. Whoever can bypass the wrapper (the allow-group, and root) can start an unauthenticated server. Keep that group EMPTY/minimal, document it, and monitor membership changes; it is the crown jewel.
4. Log at the gateway. OpenCode writes no HTTP access log, so put request logging at the reverse proxy / gateway and record the authenticated principal per request for attribution.
5. Isolate the network for the durable fix. Password auth still leaves loopback ports enumerable (`/proc/net/tcp`) and reachable/brute-forceable and NOT UID-isolated. For true isolation use per-user network namespaces (`PrivateNetwork=` in a per-user systemd unit, `unshare -rn`, or per-user containers), which removes cross-user reachability entirely.

Verified same-user + by launch-path inspection on the production host; the cross-user attack was (correctly) not run on production. The sound safety argument is that the attack chain is broken at step 0 (no unsecured server obtainable, every server authenticated), not that a cross-user exploit was tried and failed.

## What we cannot do

We cannot stop other people on a shared system from running OpenCode unprotected (unless, as above, you control the host and wrap the binary). This how-to protects YOUR sessions and is the guidance to circulate; the durable fix is upstream (UNIX socket / require-auth-by-default), tracked in advisory `20260716-0850-01`.
