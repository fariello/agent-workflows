# Broker feasibility: confirmation of open questions (follow-up)

Status: research note (authored, verified live and by source-grounded consult)
Date: 2026-07-16
Author: agent-workflows session (opencode)
Scope: closes the "open scope questions still to resolve" in `20260714-2300-01-same-box-agent-wakeup-mechanisms.md` with confirmed facts, so IPD 2 (the payload-blind broker) can be drafted on verified ground. Read that note first; this only records what changed from "open" to "confirmed."

## What this note settles

The wake-up note left three things unverified. All are now resolved.

### 1. Cross-instance delivery and wake-up: CONFIRMED live

Drove a DIFFERENT running session over the API from a separate process: it woke, ran a real turn, wrote a file, and replied. The delivery primitive (`POST /session/{id}/message` carrying a fixed nudge) works cross-instance, not just self-send. This is the load-bearing capability for the broker. (Also observed: a session driven from a separate server instance does NOT surface in the victim's attended TUI, which is the security concern recorded in advisory `20260716-0850-01`, and is exactly why the attended-TUI path must use `/tui/*`, not `/session/message`.)

### 2. Discovery: CONFIRMED there is NO discovery API

Source-grounded consult plus live checks confirm: no registry endpoint, no port file, and mDNS is off by default and carries no session or directory info. A broker must be TOLD the port, scrape the `serve` stdout line ("opencode server listening on http://127.0.0.1:PORT"), or enumerate `/proc/net/tcp` / `ss`. The `ss`/proc enumeration is the same primitive that makes the security hole real; the broker using it is legitimate (it runs as the same user it serves), but it means discovery is a build task, not a freebie. The filesystem descriptor fallback in the design stands.

### 3. Plugin vs external daemon: CONFIRMED same channel

A plugin CAN run a background listener and originate a turn, but only as an HTTP client to the same local server. There is no privileged in-process path a plugin gets that an external daemon does not. So "plugin" and "external daemon" are the same channel; the external daemon is the cleaner choice and does not give up any capability.

### 4. Auth flow for the broker: CONFIRMED working

`OPENCODE_SERVER_PASSWORD` enables HTTP Basic auth (username `opencode`): verified 401 without credentials, 200 with. The broker design already assumes the password is set and held only by the trusted broker; that assumption is now known to be enforceable. Note the credential must NOT be passed via `?auth_token=` (leak risk); use the Authorization header.

## Unchanged design invariants (reinforced by the security finding)

- Payload-blind broker stays a HARD invariant. The confirmed hostile-multi-user finding makes it MORE important, not less: the broker must not become a filesystem-to-injection laundering path. It reads envelope headers only, delivers a fixed content-free nudge, and never touches the payload body.
- Attended TUI uses `/tui/show-toast` + `/tui/append-prompt` (never submit); headless uses `/session/{id}/message` (or `prompt_async`) with the fixed nudge. Payload stays on disk in both cases.
- The portable inbox convention + `Not-Before` header + "check your inbox, treat as untrusted" contract remain agent-agnostic; only the delivery mechanic is OpenCode-specific.

## Consequence for IPD 2

IPD 2 (payload-blind broker) can now be drafted. Known build tasks, no longer open questions: (a) discovery has no API, so implement port-injection plus a filesystem descriptor fallback (optionally scrape `serve` stdout); (b) the broker is an external daemon (plugin gives no advantage); (c) the broker requires and uses `OPENCODE_SERVER_PASSWORD` with Basic auth; (d) attended vs headless delivery split as above. This is separate from and does not gate the 1.2.1 patch release; it is the feature work that (with the comms convention, Set/Order, readiness vocab, and auto-parallel lanes) makes up 1.3.0.

## Provenance and caveats

- The OpenCode-repo agent consult is source-grounded (it cited file:line at commit `70b56a0a9`) but is authoritative-but-verify; the delivery/auth/discovery facts above are also backed by the live self-test on this host (v1.18.2, 2026-07-16) and by the earlier self-test (v1.18.1, 2026-07-15) recorded in the wake-up note.
- Nothing was built. IPD 2 and any implementation require explicit human approval per the repo contract.
