# Proposed remediation (design specification)

STATUS: DESIGN SPECIFICATION AND PSEUDODIFF ONLY. None of this is compiled, typechecked, or tested. Effect-style method names (for example an interruptible/bounded permission wait) are illustrative of intent and must be validated against the real tree. We are glad to produce real, reviewed, tested patches if the maintainers want them; this section exists to show the changes are concrete and mapped to source, and to let the maintainers decide the product-policy questions listed at the end.

These are contained changes intended to reduce the shared-infrastructure risk while preserving legitimate server and IPC use. We defer to the maintainers on which (if any) are in scope.

## Sequencing (independently reviewable PRs)

Ordered so lower-risk secret/startup fixes are not blocked by the more involved shell-UX work.

### PR A - Public configuration response contract (secret non-disclosure)

Problem: `GET /config` returns provider `apiKey` (and similar credential fields) verbatim (`handlers/config.ts`, `config/config.ts`, `v1/config/provider.ts`).
Direction:
- Return a PUBLIC projection of the config that OMITS secret values (do not use a `***redacted***` sentinel: a subsequent full-object PUT could write the sentinel over the stored credential via existing merge behavior).
- Prefer a schema-defined public DTO / write-only secret fields over a finite field-name blacklist, because provider `options` and `headers` are extensible `Record<string,string>` (a blacklist cannot be a durable boundary).
- Add `...Configured` boolean indicators only where a UI genuinely needs to know a value exists.
- Preserve non-secret fields (`clientId`, URLs, redirect URIs, base URLs, callback ports).
- Cover at minimum: provider API keys, MCP client secrets, access/refresh/bearer tokens, `Authorization`, `Proxy-Authorization`, cookies/session headers, API-key-style headers, provider-specific credential aliases, and case/dash/underscore variants; and any alternate config or update-response endpoints.
Note: this is potentially an API-contract change; the maintainers should decide whether it is versioned.

### PR B - Shared server-startup authentication policy

Problem: startup fails open on missing password, and `web.ts` starts a listener independently of `serve.ts` (`cli/cmd/serve.ts:15-22`, `cli/cmd/web.ts`).
Direction:
- Factor a single startup policy applied by EVERY listener-producing path (serve, web, attach-related, desktop/embedded, ACP/integration, test servers, direct `Server.listen(...)` callers, helpers).
- Define behavior for missing / empty / whitespace-only passwords; loopback IPv4, the full `127.0.0.0/8`, IPv6 `::1`, `localhost`; non-loopback and wildcard binds (`0.0.0.0`, `::`); the mDNS-induced non-loopback case; config vs CLI precedence; managed config; and stale unsecured listeners.
- Optionally support fail-closed (refuse to start without auth) and/or a generated per-instance token written `0600`, as a maintainer-chosen default.
- Keep startup security policy SEPARATE from network listen options (do not bolt `requireAuth` onto the options object merely because it is later passed to `listen`).

### PR C - Caller-aware shell authorization

Problem: `POST /session/{id}/shell` spawns with no permission check (`shellImpl` in `session/prompt.ts`), inconsistent with the agent tool path.
Direction:
- Route `/shell` through the SAME normalized command planner + permission model the shell tool uses (factor a shared `ShellPermission.plan()` reused by tool and endpoint); do not use the raw command as the remembered `always` pattern.
- Return stable, expected authorization errors (a defined HTTP status/body for deny and for unavailable-approval); do NOT convert an expected denial into a defect (no `Effect.orDie` on the permission call).
- Restore interruptibility around any approval wait (the impl is inside `Effect.uninterruptibleMask`; a blocking wait must be wrapped in `restore(...)`), bound the wait, and clean up pending requests on client disconnect, cancellation, and shutdown.
- Deterministic headless behavior: for a remote/headless API call, execute immediately only when an existing rule resolves to `allow`; treat `deny` as rejection; treat `ask` with no approval-capable responder as a deterministic rejection (not an indefinite hang), unless an explicit trusted-automation protocol is designed.
- Preserve ordinary attended-TUI `!command` usability.
- Also trace and cover `SessionPrompt.command` / config-markdown shell and every other spawn path before claiming the command surface is closed.

### PR D - Server-authorized filesystem roots

Problem: file endpoints operate against a caller-supplied `directory` (down to `/`) (`handlers/file.ts`, `middleware/workspace-routing.ts`).
Direction:
- Authorize the workspace/project/session root SERVER-SIDE; do not let an arbitrary caller choose `/` (or any unrelated path) as the trust boundary.
- Apply the same authorization consistently to content, list, find, grep, symbol, and status.
- Define a `realpath`/symlink policy (reject symlinks leaving the authorized root) and behavior for unknown dirs, `/`, home, other projects/workspaces, nonexistent paths, bind mounts, path-replacement races, and case normalization.
- This converts "arbitrary read as the serving user" into "read within the authorized project."

### PR E - Defense in depth

- UNIX-domain socket listener option (`server.socket` / `--socket`) creating the socket in a `0700` dir; when set, skip the TCP bind. This gives OS-enforced per-user isolation (the only robust local boundary). Update SDK/CLI client and attach modes to accept a socket path.
- Peer-credential (UID) check where supported (portable only on the UDS; effectively paired with the socket option, not independent).
- Optional HTTP access log (`--access-log` / `server.accessLog`) recording method, path, status, remote, and auth-subject, so abuse is auditable from opencode itself.
- Timing-safe password comparison (replace `===` in `authorized()` with a constant-time compare on equal-length buffers).
- Deprecate the `?auth_token=` query parameter in favor of the `Authorization: Basic` header (query tokens leak into `cmdline`, history, proxy logs).
- Stronger non-loopback safeguards: refuse (or require an explicit acknowledgement flag for) a non-loopback bind with no auth; escalate the warning.

### PR F - Operator-enforced auth via the EXISTING managed-config tier (the strongest lever for shared/HPC)

This is the highest-value item for operators and, importantly, it EXTENDS an admin mechanism OpenCode already ships rather than introducing a new philosophy. It was source-validated (fork `dev` `08fb47373`); re-pin before disclosure.

Established facts (source):
- OpenCode ALREADY has a cross-platform, admin-authoritative config tier that overrides user/project config on scalar keys: the managed directory `/etc/opencode` on Linux (and any non-darwin/win32), `%ProgramData%\opencode` on Windows, `/Library/Application Support/opencode` on macOS, plus a macOS MDM `.mobileconfig` plist whose own code comment says it "override[s] everything" (`config/managed.ts:20-69`, merged last in `config/config.ts:516-534`). So "operator overrides user" is an existing, in-code stance - NOT a new philosophy, and consistent with SECURITY.md's coexistence of "users control their own config" with the MDM override.
- THE GAP (identical on every OS): the server startup/network path does NOT read the managed tier. `serve`/`web` resolve options via `Config.getGlobal()` -> `loadGlobal`, which merges ONLY `~/.config/opencode/*` (`cli/network.ts:56-60`, `config.ts:246-260`); the managed tier is merged only in `loadInstanceState` (`config.ts:516-534`), which startup does not use (`serve`/`web` run `instance: false`). And there is NO `server.requireAuth`/`server.password` key in the schema (`core/src/v1/config/server.ts:6-18` is `port`/`hostname`/`mdns`/`mdnsDomain`/`cors` only); the password is env-var-only (`server/auth.ts:18`). Net: today a sysadmin CANNOT, via config alone, set/require a password, lock the bind address, or disable mDNS - the exposure-relevant controls are exactly the ones `/etc/opencode` cannot currently constrain.

Direction (small-to-medium, ~1 focused PR; mostly wiring):
- Add `server.require_server_password: boolean` (and optionally `server.allow_non_loopback_bind: boolean`) to the server schema (`core/src/v1/config/server.ts`) - small, mandatory (unknown keys drop on decode until added).
- Make the startup path READ the operator tier: a dedicated `resolveStartupPolicy()` beside `resolveNetworkOptions` that reads global + managed (`/etc/opencode` etc.) + MDM (reuse `ConfigManaged.managedConfigDir()`/`readManagedPreferences()` as `config.ts:516-534` does), returning the resolved policy. Preferred over merging managed into `getGlobal` (which would change global-config semantics everywhere).
- Enforce in ONE shared pre-listen guard at the `Server.listen()` choke point (`server/server.ts:73`), which every listener path (`serve`, `web`, TUI/attach) passes through - this is also the clean fix for the "serve.ts-only patch misses web.ts" gap. Refuse to start when the operator has locked `require_server_password` and `OPENCODE_SERVER_PASSWORD` is empty (and, with the bind key, when a non-loopback bind is locked off).
- Interim stopgap (service/launcher only, NOT multi-user enforcement): an `OPENCODE_REQUIRE_SERVER_PASSWORD` env flag checked at the same seam - trivial, but a shell user can `unset` it, so it is not enforcement on a shared host. Ship both, OR-ed at the guard, so the interim keeps working after the key lands.
- Policy decision for maintainers (the only genuinely new bit): whether a managed lock should also beat explicit CLI flags (`cli/network.ts:62-79` currently has CLI flags override config). Without that, `--hostname 0.0.0.0`/`--mdns`/`--port` on the command line still win. A true operator "lock" needs managed values to take precedence over CLI for the locked keys.

Why this is the compelling ask: it lets an operator centrally enforce "no unsecured (or non-loopback) OpenCode server on this cluster," which directly answers the shared/HPC concern and removes reliance on every user setting an env var correctly (which fails open silently). And it is a small extension of OpenCode's OWN existing cross-platform admin-config tier, not a new concept.

## What no single change fixes (do not overstate)

- A fail-closed startup change does not fix secret return to authenticated clients, caller-selected filesystem roots, the direct-shell permission inconsistency, missing access logs, query-string credential exposure, or per-user socket isolation.
- Config omission and shell gating do not remove the need for authentication; filesystem authorization does not replace authentication; timing-safe compare does not materially reduce the primary chain; UDS + peer creds are deployment architecture, not a substitute for correct API authorization.

## Product-policy questions for the maintainers to decide (we will not choose these silently)

Whether authentication becomes the default; whether unauthenticated loopback remains temporarily permitted; whether unsecured non-loopback startup is ever allowed; generated credential vs refusal; the trusted-automation opt-in and approval-responder protocol; attended-approval timeout; the HTTP status/schema for unavailable approval; whether the public `/config` contract is a versioned change; compatibility/deprecation periods; and whether filesystem roots are session-, project-, instance-, or user-scoped. For each, we can present concrete alternatives with their security and compatibility consequences.

## Validation that real patches would require (not yet performed)

Dependency install from lockfile; format; typecheck; lint; affected unit + route/integration tests; SDK/OpenAPI validation; production build; TUI `!command`; headless shell allow/deny/ask-with-responder/ask-without-responder; cancellation and shutdown while approval pending; concurrent permission requests; synthetic-secret GET / partial-update / full-object round-trip; serve vs web startup-policy parity; IPv4/IPv6 loopback classification; wildcard/non-loopback binds; mDNS; filesystem-root authorization; symlink/realpath; controlled two-UID Linux testing; and both stable-release and dev-branch runs - recording exact commands, versions/commits, baseline-vs-patched, deterministic-vs-flaky, skipped tests, and pre-existing vs patch-induced failures.
