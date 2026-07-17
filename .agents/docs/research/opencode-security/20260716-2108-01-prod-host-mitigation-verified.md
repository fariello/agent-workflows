# Production host is mitigated: verified deployment pattern (opencode.its.uri.aws)

Status: findings note (from a Part-A verification run by a colleague on the production host; same-user + launch-path inspection only)
Date: 2026-07-16
Author: agent-workflows session (opencode), recording a run performed by the hosted-service owner's delegate
Related: advisory `20260716-0850-01`, hardening how-to `20260716-0850-02`, agent runbook `.agents/prompts/reusable/20260716-1342-02`.

## What was run and by whom

The hosted-service owner's delegate ran the agent verification runbook on the PRODUCTION shared OpenCode Web host `opencode.its.uri.aws` (aarch64, OpenCode v1.18.1; runbook targeted 1.18.2, minor drift noted). The runbook's preflight gate worked as designed: the operator selected "Part A only (same-user, safe)"; Part B (cross-user attack simulation) was correctly DECLINED under the production-safety guardrail because the host carries real users' live sessions (account `cshen` shows supplementary groups `opencode-users`, `opencode-exec`, and per-user groups for other real users). So all results below are same-user Part A plus read-only launch-path inspection; NO cross-user exploitation was attempted.

## Headline: the host is already mitigated, with defense in depth beyond the advisory's baseline

The specific cross-user exposure the advisory describes is NOT present on this deployment, for two independent reasons:

1. Per-spawn server password (the advisory's primary mitigation, already live). Every web-TUI server is launched by a helper `/usr/local/bin/opencode-serve-as` that generates a per-spawn random 32-char password from `/dev/urandom`, exports it as `OPENCODE_SERVER_PASSWORD` via the ENVIRONMENT (not argv, so it does not appear in `ps`/`/proc/<pid>/cmdline`), and execs the real binary bound to `127.0.0.1` with a CORS allowlist of `https://opencode.its.uri.edu`. Verified same-user against the account's own live server on `127.0.0.1:14002`: `GET /app` and `GET /config` both returned HTTP 401 without credentials, and 401 with WRONG credentials. The password's PRESENCE (not value) was confirmed in `/proc/<pid>/environ`.

2. A wrapper blocks ordinary users from starting an unsecured server at all. `/usr/local/bin/opencode` is a bash wrapper that, for any user NOT in group `opencode-serve-allowed` (and not root), blocks the subcommands `serve`, `web`, `acp`, `attach` and the flags `--port`/`--hostname`. Attempting `opencode serve ...` as the ordinary account returned `'serve' is not permitted on this host` (exit 3, no listener started). The real binary is `/usr/local/libexec/opencode-real`, mode `0750 root:opencode-exec` (no world execute). So the default-insecure no-password server could not even be established on this host by an ordinary user; the A2/A3 "no-auth" predictions are therefore NOT REPRODUCED (mitigation in place), not a refutation of the upstream default.

This is a stronger posture than "set a password": it both enforces auth on every server AND removes the ability for ordinary users to create an unsecured one. It is a good reference architecture for other operators.

## Verified vs not (scope honesty)

- VERIFIED (same-user + launch-path inspection): auth is enforced on the running server (401 without/with-wrong creds); the password is per-spawn random and env-injected; ordinary users cannot start `serve`/`web`/`acp`/`attach`.
- NOT tested (production safety): the cross-user attack chain (B0/B1/B2/B3). It was correctly not attempted on a host with real users. The sound argument for cross-user safety here is that the chain is broken at step 0 (an ordinary user cannot obtain an unsecured server, and every server enforces auth), not that a cross-user exploit was run and failed. To PROVE/REFUTE the cross-user predictions, run Part A + Part B on a dedicated NON-PRODUCTION node with two throwaway accounts (as we did on the dev box: see advisory T1-T6).

## Residual risks the run correctly flagged

- Password is not isolation. Loopback ports remain enumerable by any local user via `/proc/net/tcp` (the run observed several: 14002, 8765, 8429, 7681, 8888, ...). A 32-char random password makes online brute force impractical, but the port is not UID-isolated. Durable fix remains per-user network isolation (netns / `PrivateNetwork=` / per-user container), which removes reachability entirely.
- `opencode-serve-allowed` is the new crown jewel. Anyone in that group (or root) can start an unauthenticated server via the wrapper's allowlist path. It was observed EMPTY (good). Keep it empty/minimal, document it, and monitor membership changes.
- Gateway per-principal logging unverified. OpenCode itself writes no HTTP access log (advisory). Whether the web gateway in front records the authenticated principal per request (for attribution) was not evaluated; recommend confirming it does and retains it.
- Provider API key was NOT exposed to the unauthenticated probe (`/config` returned 401). The key value was never read or recorded. Standard hygiene: rotate any key you believe may have been readable in a shared context at any time.

## Recommended next steps for the operator (from the run)

1. Keep `opencode-serve-allowed` empty/minimal; document and monitor it.
2. Confirm the web gateway attributes and retains requests per authenticated user.
3. Pursue per-user network isolation as the durable fix (password-only leaves the port reachable).
4. Continue coordinated disclosure upstream for the default-insecure behavior (the deployment mitigates it locally; the upstream default is still the class risk).

## Provenance

Results produced by the hosted-service owner's delegate running `.agents/prompts/reusable/20260716-1342-02` (agent runbook) on `opencode.its.uri.aws`, Part A only, 2026-07-16. Recorded here as durable analysis; the raw run output was provided to the agent-workflows maintainer. Cross-user facts elsewhere in this directory (advisory T1-T6) were established on a separate dev box with two real accounts.
