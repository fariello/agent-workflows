# Corrected OpenCode Security Patch Proposal

Status: implementation specification and commit-pinned pseudodiff
Date: 2026-07-16
Reviewer: GPT-5.6 Thinking
Stable basis: OpenCode `v1.18.3`, commit `127bdb30784d508cc556c71a0f32b508a3061517`
Development basis: OpenCode `dev`, commit `08fb47373509ba64b13441061314eeacf4264f51`
Related review: `20260716-2130-01-gpt56-agent--to--agent-workflows.agent-third-party-review.md`

## Important status and limitation

This file proposes a materially different patch sequence from the three original sketches. It is intentionally a **pseudodiff and implementation specification**, not an apply-ready Git patch. No complete OpenCode checkout or Bun environment was available in the review container, and no actual patch implementation was supplied. A coding agent should adapt this proposal against a clean checkout at the exact target commit, then run formatting, type checking, generated-client checks, unit tests, integration tests, and controlled runtime tests.

Do not submit this file verbatim as an AI-generated security report. OpenCode's current security policy states that AI-generated security reports are not accepted. A human researcher should independently validate, author, and submit any disclosure.

## Executive patch decision

The original three-patch set should not be implemented literally.

1. **Config response hardening should ship first**, but use omission and a public-response contract. Do not use a sentinel.
2. **Authentication policy should be shared by every listener-starting path**, including both `serve` and `web`. An opt-in `requireAuth` feature is useful, but a `serve.ts`-only check is incomplete and does not correct the insecure default.
3. **The direct shell route should not receive a naive unconditional `permission.ask` call.** That design can hang headless requests, changes the ordinary TUI `!command` experience, waits inside an uninterruptible region, and can mishandle expected denials. Shell authorization needs caller context, fail-fast headless behavior, cancellation, and reuse of the normal shell tool's permission planner.
4. **Filesystem root authorization remains a separate P0/P1 issue.** Authentication and config redaction do not prevent an authenticated or compromised client from selecting `/` as the file-operation root.

## Recommended PR sequence

| PR | Purpose | Merge order | Compatibility risk |
|---|---|---:|---|
| A | Public config projection and secret omission | 1 | Low to medium |
| B | Shared server startup authentication policy | 2 | Low if opt-in; medium if secure defaults change |
| C | Direct shell authorization redesign | 3 | Medium to high |
| D | Authorized worktree/file root | 4 | Medium |
| E | UDS, peer credentials, and access logging | 5 | Low to medium |

# PR A: public config response and secret omission

## Goal

Prevent `GET /config` from returning configured write-only credentials, without mutating internal configuration and without corrupting secrets when a client reads the config, changes an unrelated field, and submits an update.

## Required design

Create a public configuration response type or projection. The long-term contract should explicitly distinguish:

- ordinary readable configuration;
- write-only secret inputs;
- optional booleans such as `apiKeyConfigured` or `clientSecretConfigured`;
- header names that are safe to expose;
- header values that must be omitted.

A field-name blacklist alone is not a complete security boundary because provider options and headers are extensible. The emergency patch may use a conservative omission helper, but it must be labeled partial and replaced by a schema-defined public DTO.

## Files expected to change

- `packages/opencode/src/server/routes/instance/httpapi/handlers/config.ts`
- the config HTTP group response schema, if the response type changes
- a new public projection module near the config handler or core config schema
- generated SDK/OpenAPI artifacts, if applicable
- config route tests

## Pseudodiff

```diff
--- a/packages/opencode/src/server/routes/instance/httpapi/handlers/config.ts
+++ b/packages/opencode/src/server/routes/instance/httpapi/handlers/config.ts
@@
 import { Effect } from "effect"
+import { ConfigPublicV1 } from "../public/config-public"
@@
 const get = Effect.fn("ConfigHttpApi.get")(function* () {
-  return yield* configSvc.get()
+  const internal = yield* configSvc.get()
+  return ConfigPublicV1.fromInternal(internal)
 })
```

Conceptual public module:

```ts
import type { ConfigV1 } from "@opencode-ai/core/v1/config/config"

export namespace ConfigPublicV1 {
  export type Info = PublicConfigInfo

  export function fromInternal(input: ConfigV1.Info): Info {
    // Prefer explicit schema-based projection.
    // Secret fields are omitted, not replaced by a sentinel.
    // The internal object is never mutated.
    return projectPublicConfig(input)
  }
}
```

## Emergency omission helper

Use only if the full public DTO cannot ship immediately.

```ts
const SECRET_KEY_NORMALIZED = new Set([
  "apikey",
  "authtoken",
  "token",
  "accesstoken",
  "refreshtoken",
  "clientsecret",
  "password",
  "secret",
  "credential",
  "credentials",
])

const SENSITIVE_HEADER_NORMALIZED = new Set([
  "authorization",
  "proxyauthorization",
  "cookie",
  "setcookie",
  "xapikey",
  "apikey",
  "xauthtoken",
  "xaccesstoken",
])

function normalizeName(value: string) {
  return value.toLowerCase().replaceAll("-", "").replaceAll("_", "")
}

function omitSecrets(value: unknown, parentKey?: string): unknown {
  if (Array.isArray(value)) return value.map((item) => omitSecrets(item))
  if (!value || typeof value !== "object") return value

  const isHeaderMap = parentKey?.toLowerCase() === "headers"
  const entries: Array<[string, unknown]> = []

  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
    const normalized = normalizeName(key)

    // Omit secret-looking fields regardless of runtime value type.
    if (SECRET_KEY_NORMALIZED.has(normalized)) continue

    // Header names are case-insensitive. This is still only an emergency policy.
    if (isHeaderMap && SENSITIVE_HEADER_NORMALIZED.has(normalized)) continue

    entries.push([key, omitSecrets(child, key)])
  }

  // Object.fromEntries avoids special assignment behavior for __proto__.
  return Object.fromEntries(entries)
}
```

### Important limitations of the emergency helper

- Arbitrary provider-specific secret names can still evade a blacklist.
- Arbitrary custom headers can carry credentials under unknown names.
- Exposing non-sensitive headers may still reveal internal topology or identifiers.
- A cycle-aware clone is not necessary if config values are schema-decoded JSON-like data. If cycles can exist, the HTTP response needs an explicit cycle policy because preserving cycles still fails JSON serialization.
- Getters and proxies should not be expected in a decoded config object. If they are possible, projection must avoid invoking untrusted accessors.

## Sentinel prohibition

Do not emit `"***redacted***"` unless the update path explicitly treats that exact sentinel as "leave unchanged" at every nesting level. Current merge behavior can write the sentinel over the real secret during a full-object update.

Preferred behavior:

```text
internal:  { apiKey: "REAL", theme: "old" }
GET:       { theme: "old" }
client:    { theme: "new" }
update:    merge(existing, client)
result:    { apiKey: "REAL", theme: "new" }
```

## Required tests

1. Provider `apiKey` omitted.
2. MCP `clientSecret` omitted.
3. `accessToken` and `refreshToken` omitted.
4. Exact `token`, `password`, `secret`, and credential fields omitted.
5. `Authorization` header omitted case-insensitively.
6. `Proxy-Authorization`, cookie, and common API-key headers omitted.
7. `clientId`, URL, redirect URI, callback port, and base URL preserved.
8. Nested records and arrays handled.
9. Original internal config not mutated.
10. GET, unrelated edit, update preserves the internal secret.
11. Public response satisfies its declared schema.
12. Generated clients compile.
13. Alternate config/provider endpoints do not return the same secrets.
14. Error and log paths do not serialize internal config.

# PR B: shared startup authentication policy

## Goal

Provide one startup policy that is enforced immediately before any HTTP listener is created. Do not implement the policy only in `serve.ts`.

At development commit `08fb473...`, both `packages/opencode/src/cli/cmd/serve.ts` and `packages/opencode/src/cli/cmd/web.ts` independently warn and continue when the password is absent. They must use the same policy function.

## Configuration recommendation

Long-term secure-default configuration:

```ts
server: {
  requireAuth?: boolean
  allowUnauthenticatedLoopback?: boolean
  allowUnauthenticatedNonLoopback?: boolean
}
```

Recommended defaults:

- `requireAuth`: false only during a compatibility transition, then true for headless server modes;
- `allowUnauthenticatedLoopback`: false for shared-host-safe defaults, or temporarily true with a deprecation warning;
- `allowUnauthenticatedNonLoopback`: false, with no silent compatibility exception.

A simpler first PR may add only `requireAuth`, but maintainers should not describe an opt-in flag as resolving the default exposure.

## Responsibility boundary

Keep these concepts separate:

```ts
type ResolvedNetworkOptions = {
  readonly port: number
  readonly hostname: string
  readonly mdns: boolean
  readonly mdnsDomain?: string
  readonly cors: readonly string[]
}

type ResolvedStartupPolicy = {
  readonly requireAuth: boolean
  readonly allowUnauthenticatedLoopback: boolean
  readonly allowUnauthenticatedNonLoopback: boolean
}
```

Do not add `requireAuth` to `Server.ListenOptions`. Authentication requirement is startup policy, not a TCP bind option.

## Shared startup function

```ts
export function enforceServerStartupPolicy(input: {
  readonly network: ResolvedNetworkOptions
  readonly policy: ResolvedStartupPolicy
  readonly auth: ServerAuth.Info
}) {
  return Effect.gen(function* () {
    const authenticated = ServerAuth.required(input.auth)
    const loopback = isLoopbackHostname(input.network.hostname)

    if (input.policy.requireAuth && !authenticated) {
      return yield* fail(
        "Refusing to start: server authentication is required but " +
          "OPENCODE_SERVER_PASSWORD is not set to a non-empty value.",
      )
    }

    if (!loopback && !authenticated && !input.policy.allowUnauthenticatedNonLoopback) {
      return yield* fail(
        "Refusing to bind a non-loopback address without authentication. " +
          "Set OPENCODE_SERVER_PASSWORD or explicitly allow the unsafe bind.",
      )
    }

    if (loopback && !authenticated && !input.policy.allowUnauthenticatedLoopback) {
      return yield* fail(
        "Refusing to start an unauthenticated loopback server. " +
          "Loopback is reachable by other users on a shared host.",
      )
    }

    if (!authenticated) {
      console.error(
        "Warning: OPENCODE_SERVER_PASSWORD is not set; server is unsecured.",
      )
    }
  })
}
```

`isLoopbackHostname` must correctly handle at least:

- `127.0.0.1` and other `127.0.0.0/8` addresses;
- `::1` and bracketed IPv6 forms where relevant;
- `localhost`, with documented resolution assumptions;
- explicit LAN, wildcard, and unspecified addresses;
- hostname values resolved from managed/global/project config and CLI precedence.

## Shared launch path pseudodiff

```diff
 const network = yield* resolveNetworkOptions(args)
+const policy = yield* resolveServerStartupPolicy(args)
+const auth = yield* ServerAuth.Config
+yield* enforceServerStartupPolicy({ network, policy, auth })
 const server = yield* Effect.promise(() => Server.listen(network))
```

Apply through a shared launcher used by:

- `opencode serve`;
- `opencode web`;
- every TUI path that creates a TCP listener;
- ACP or IDE paths that create a listener;
- attach or run fallbacks that create a listener;
- embedded server constructors intended for third-party use.

Do not duplicate the guard in multiple commands if a common listener-start seam is available.

## Ordering requirements

The policy runs:

1. after configuration and final network options are resolved;
2. after the authoritative auth state is available;
3. before `Server.listen`;
4. before mDNS advertisement;
5. before opening a browser;
6. before printing a successful listening URL.

## Required tests

1. `serve --require-auth`, missing password: nonzero exit, stderr, no listener.
2. `web --require-auth`, missing password: same.
3. Config `server.requireAuth: true`, missing password: same.
4. Password present: both commands start normally.
5. Empty password treated as missing.
6. Loopback no-auth follows the chosen compatibility policy.
7. `0.0.0.0` no-auth refused by default.
8. LAN hostname no-auth refused by default.
9. `--mdns` with no explicit hostname and no auth refused because it resolves to non-loopback.
10. Explicit loopback plus mDNS follows the loopback policy.
11. Config and CLI precedence tested.
12. Browser is not opened on a failed `web` startup.
13. mDNS is not advertised on a failed startup.
14. Every `Server.listen` caller is inventoried by a repository-wide test or lint rule.

# PR C: caller-aware direct shell authorization

## Goal

Ensure direct API shell execution follows a deliberate authorization policy without degrading ordinary TUI shell use or hanging unattended requests.

## Do not apply the original sketch literally

The original corrected sketch places `permission.ask` inside the inner `Effect.gen` after agent validation. That fixes variable scope, but the behavior remains unsafe to merge because:

- default `ask` can wait indefinitely when no responder exists;
- the wait occurs inside an uninterruptible region unless interruptibility is restored;
- the TUI `!command` path uses the same endpoint and would gain a visible prompt;
- expected deny/reject outcomes should not be converted to defects with `Effect.orDie`;
- the raw command is not necessarily the same remembered-approval pattern used by the existing shell tool;
- direct shell should reuse external-directory and command-planning logic from the normal tool path;
- session/tool records should not be marked running before authorization succeeds.

## Required request context

Add a trusted, server-derived request source. Do not trust a caller-supplied string without authentication and validation.

```ts
type ShellRequestSource =
  | "attended-tui"
  | "remote-api"
  | "trusted-automation"
```

Possible derivation mechanisms include:

- an in-process TUI call path that invokes a non-public service directly;
- a per-client capability established during authenticated attachment;
- an authenticated internal-client identity;
- a separate endpoint for attended shell behavior;
- an explicit trusted automation profile configured by the server operator.

## Shared shell planner

Refactor the existing shell tool permission preparation into a reusable planner. It should produce exactly the command, cwd, shell, arguments, permission identifier, patterns, remembered-approval patterns, metadata, and external-directory checks that will be executed.

```ts
type ShellExecutionPlan = {
  readonly sessionID: string
  readonly agentID: string
  readonly source: ShellRequestSource
  readonly command: string
  readonly cwd: string
  readonly shell: string
  readonly args: readonly string[]
  readonly permissionInput: PermissionV1.AskInput
}
```

Authorization must bind to the exact plan that is later executed. Do not approve one string and reconstruct a different command afterward.

## Required no-responder policy

Use this policy:

1. If the effective ruleset evaluates to `allow`, execute.
2. If it evaluates to `deny`, return a structured 403 and do not create running execution records.
3. If it evaluates to `ask` and the source is `remote-api`, fail fast with 403 or a documented 409 unless a responder protocol is explicitly attached.
4. If it evaluates to `ask` and the source is `trusted-automation`, deny unless the automation profile explicitly pre-approves the command.
5. If it evaluates to `ask` and the source is `attended-tui`, create an interactive permission request, wait interruptibly, and remove it on cancellation, disconnect, timeout, or shutdown.

Do not let a bare `serve` request hang indefinitely.

## Pseudocode

```ts
function authorizeShell(plan: ShellExecutionPlan) {
  return Effect.gen(function* () {
    const decision = yield* permission.evaluate(plan.permissionInput)

    if (decision === "allow") return
    if (decision === "deny") return yield* ShellDenied

    if (plan.source !== "attended-tui") {
      return yield* ShellApprovalUnavailable
    }

    // The outer shell implementation uses uninterruptibleMask. Restore
    // interruptibility around a human wait and bind cleanup to request lifetime.
    return yield* restore(
      permission.ask(plan.permissionInput).pipe(
        Effect.timeout(permissionTimeout),
        Effect.ensuring(permission.removePending(plan.permissionInput)),
      ),
    )
  })
}
```

Conceptual insertion order:

```diff
 const session = yield* sessions.get(input.sessionID)
 const agent = yield* agents.get(input.agent)
 if (!agent) { ... }
+
+const plan = yield* ShellPermission.plan({
+  session,
+  agent,
+  command: input.command,
+  cwd: ctx.directory,
+  source: requestContext.shellSource,
+})
+yield* authorizeShell(plan)
+
+// Create user, assistant, and running tool records only after authorization.
 const model = ...
 const msg = ...
 const part = ...
```

Execution later uses `plan.shell`, `plan.args`, and `plan.cwd` without reconstructing them.

## HTTP behavior

| Outcome | Recommended response |
|---|---|
| Explicit permission deny | 403 |
| Ask but no responder/preapproval | 403 or documented 409 |
| Human rejection | 403 |
| Invalid session/agent | existing 4xx behavior |
| Client disconnect | cancel request and remove pending approval |
| Approval timeout | 408 or documented 409; no execution |
| Server shutdown | interrupt and clean pending approval |

Do not use `Effect.orDie` for normal authorization outcomes.

## Completeness audit

Before merge, inventory every direct process creation path, including:

- `shellImpl`;
- the normal shell/bash tool;
- `SessionPrompt.command` and `ConfigMarkdown.shell(...)`;
- command definitions that execute configured shell snippets;
- plugin or MCP process launchers;
- terminal/PTY endpoints;
- any legacy or alternate session APIs.

Not every process launcher should use user-command permissions, but every one must have an explicit trust model.

## Required tests

1. Explicit allow executes exact planned command.
2. Explicit deny never spawns.
3. Attended ask executes only after approval.
4. Attended rejection never spawns.
5. Remote/headless ask fails fast.
6. Trusted automation requires explicit preapproval.
7. TUI `!command` remains usable under documented rules.
8. Request disconnect cancels pending approval.
9. Timeout removes pending approval.
10. Shutdown with pending approvals completes.
11. Multiple pending approvals do not cross sessions.
12. Remembered patterns match existing shell tool semantics.
13. External-directory checks are reused.
14. Records are not marked running before authorization.
15. The executed command, cwd, shell, and args exactly match the approved plan.
16. Alternate command path cannot bypass policy.

# PR D: authorized filesystem root

## Goal

Do not let an HTTP caller choose an arbitrary instance root such as `/` for file read, list, find, or grep operations.

## Required design

- Resolve a root from an authorized project, worktree, or session association.
- Treat the query/header directory only as a selector among authorized roots, not as authorization by itself.
- Canonicalize root and target.
- Define symlink behavior explicitly.
- Apply the same boundary to content, list, find, grep, symbol, and status operations.
- Reject `/` unless the server operator explicitly configured it as an authorized workspace.

Conceptual flow:

```ts
const requested = WorkspaceRouting.requestedDirectory(request)
const authorized = yield* WorkspaceAuthorization.resolve({ principal, sessionID, requested })
const rootReal = yield* fs.realpath(authorized.root)
const target = yield* SafePath.resolveWithin(rootReal, relativePath)
```

A lexical `path.resolve` plus prefix/relative check is insufficient when an in-tree symlink points outside the root. Use canonicalization or a descriptor-based safe-open strategy and test replacement races where the platform permits.

# PR E: transport and audit hardening

Recommended follow-on changes:

1. Add Unix-domain-socket listener support in a mode-0700 directory with a mode-0600 socket.
2. On supported Unix platforms, validate peer UID on the Unix socket.
3. Deprecate query-string authentication tokens.
4. Use timing-safe password comparison after length normalization.
5. Add structured access logging or document a reverse-proxy requirement.
6. Redact query strings and authorization material from logs.
7. Add request IDs and authenticated-principal attribution.
8. Document that TCP loopback is not a per-user boundary.

# Validation checklist for the coding agent

## Repository preparation

```sh
git status --short
git rev-parse HEAD
git describe --tags --always --dirty
```

Confirm the exact target is either:

- stable `v1.18.3` at `127bdb30784d508cc556c71a0f32b508a3061517`; or
- dev `08fb47373509ba64b13441061314eeacf4264f51`;

or explicitly record a newer target and re-derive every line reference.

## Search inventory

```sh
rg -n "Server\.listen|NodeHttpServer\.layer|createServer\(" packages
rg -n "OPENCODE_SERVER_PASSWORD|ServerAuth|required\(" packages
rg -n "session\.shell|shellImpl|ChildProcess\.make|spawn\(" packages/opencode/src
rg -n "ConfigMarkdown\.shell|SessionPrompt\.command" packages/opencode/src
rg -n "configSvc\.get|Config\.update|mergeDeep" packages
rg -n "x-opencode-directory|searchParams\.get\(\"directory\"" packages
```

## Minimum build and test gates

Use the repository's documented Bun version and lockfile.

```sh
bun install --frozen-lockfile
bun run typecheck
bun run lint
bun test
```

Also run package-specific and generated-artifact commands discovered in `package.json`, CI workflows, and contributor documentation. At minimum cover:

- opencode server route tests;
- config schema and generated SDK tests;
- CLI `serve` and `web` tests;
- TUI shell tests;
- permission service tests;
- production build;
- formatting check.

Record baseline failures separately from patch-induced failures.

## Controlled runtime matrix

Use disposable synthetic users, data, and credentials only.

1. no-password loopback server behavior;
2. password-protected rejection and acceptance;
3. `serve` and `web` consistency;
4. non-loopback no-auth refusal;
5. mDNS-derived bind behavior;
6. synthetic config secrets absent from GET;
7. unrelated config update preserves secrets;
8. direct shell allow, deny, attended ask, and headless ask;
9. TUI `!command` UX;
10. alternate command path;
11. file root and symlink tests;
12. access-log and credential-redaction behavior;
13. two controlled Unix accounts in one network namespace;
14. teardown proof showing no test listener remains.

# Merge recommendation

- **PR A:** implement now, after finalizing the public response contract and tests.
- **PR B:** implement now as shared policy. At minimum, add opt-in `requireAuth` consistently and refuse unauthenticated non-loopback binds by default. Plan a secure-default migration for loopback server mode.
- **PR C:** do not merge the original `permission.ask(...).pipe(Effect.orDie)` sketch. Implement the caller-aware planner and fail-fast no-responder policy first.
- **PR D:** treat as high priority because read-only exfiltration remains possible even if direct shell is gated.
- **PR E:** schedule immediately after the highest-impact controls.
