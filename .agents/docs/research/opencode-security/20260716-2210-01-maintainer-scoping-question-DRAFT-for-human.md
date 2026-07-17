# DRAFT scoping question for OpenCode maintainers (for a HUMAN to send)

Status: draft for the maintainer to read, rewrite in his own words, and send himself
Date: 2026-07-16
Purpose: OpenCode's SECURITY.md bans AI-generated reports and requires a human-authored, human-verified submission. This is a SHORT scoping question to ask BEFORE writing any full report, to learn whether two specific items are considered in scope given the "server access when opted-in" exclusion. Do NOT paste this verbatim as if it were your independent work; read it, confirm you can defend each claim yourself, and send it in your own voice.

## Where to send it

Private GitHub Security Advisory "Report a Vulnerability": https://github.com/anomalyco/opencode/security/advisories/new
(Or, per SECURITY.md, escalate to security@anoma.ly if no acknowledgement within 6 business days.)

## Before you send (checklist)

- You have personally reproduced or can explain the two items below.
- Re-pin: confirm current latest released version and its commit on `anomalyco/opencode` (our line numbers came from a fork's `dev` and must be re-verified against the release you cite).
- Use synthetic credentials only; include no live keys, passwords, hostnames, or real session data.
- This is a QUESTION about scope, not a full report; keep it short.

## Suggested text (rewrite in your own words)

Subject: Scope question re: server `/config` secret exposure and `--mdns` default bind

Hi - before I write up anything formally, I want to check scope, since your SECURITY.md notes that server access when server mode is opted-in is expected behavior and that the permission system is not a security boundary. I am NOT reporting the unauthenticated-server access or the permission-prompt behavior; I understand those are by design.

Two narrower things seem like they might be separate from "you opted into server mode," and I wanted to ask whether you consider them in scope before spending your time:

1. `GET /config` returns the configured provider `apiKey` (and similar credential fields) verbatim, with no redaction, over the server API. This is gated by `OPENCODE_SERVER_PASSWORD` when set, but for anyone who can reach the API (including an authenticated web client, a leaked credential, or a malicious extension), the config response discloses the stored secret rather than an existence indicator. Is redacting secrets from the `/config` response something you would consider, or is returning them intended?

2. When `--mdns` is passed without an explicit `--hostname` (and no `server.hostname` in config), the server's default bind changes from `127.0.0.1` to `0.0.0.0`, i.e. enabling discovery silently exposes the server on all interfaces rather than loopback. Is that intended, or would you consider binding loopback by default even with `--mdns` (and requiring an explicit non-loopback hostname to expose it)?

If either is in scope, I will put together a proper private write-up with reproduction and affected versions. If both are considered expected/out of scope, no problem and thanks for the steer.

(Version I looked at: <fill in the exact released version + commit you verified against>.)

## Notes for the maintainer (do not send these)

- Keep it to these two items. The rest of what we investigated (cross-user reach of an unsecured server, `/shell` running without a permission prompt, injection stealth) is explicitly out of scope per their SECURITY.md ("server access when opted-in"; "permission system is not a sandbox"). Leading with out-of-scope items risks the report being dismissed (and the AI-report ban is real).
- #1 (`/config` secret exposure) is the strongest candidate; #2 (`--mdns`) is a weaker "footgun" argument. If you only want to ask one, ask #1.
- If they say both are out of scope, we stop; the internal hardening/ops value is already captured (your hosted host is already mitigated; see `20260716-2108-01`).
- Everything we built stays internal regardless; nothing here is published.
