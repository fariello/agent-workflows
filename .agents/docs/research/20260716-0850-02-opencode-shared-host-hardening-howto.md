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

## What we cannot do

We cannot stop other people on a shared system from running OpenCode unprotected. This how-to protects YOUR sessions and is the guidance to circulate; the durable fix is upstream (UNIX socket / require-auth-by-default), tracked in advisory `20260716-0850-01`.
