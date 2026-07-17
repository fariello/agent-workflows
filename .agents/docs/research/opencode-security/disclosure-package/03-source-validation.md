# Source validation

IMPORTANT: line numbers below were read from a downstream fork's `dev` at commit `08fb47373509ba64b13441061314eeacf4264f51` (`git describe` = `github-v1.2.25-1295-g08fb47373`), just past a v1.18.3-era bump. They must be RE-PINNED to the exact upstream release the maintainers wish to target before any fix work. Behaviors are expected to hold across the 1.18.x line; the maintainers are best positioned to confirm exact lines. Paths are relative to the OpenCode source package.

## Authentication

- Auth is opt-in via `OPENCODE_SERVER_PASSWORD` only; with no password the authorization middleware is a pass-through (all routes open). `server/auth.ts` (the password is the only auth input); `httpapi/middleware/authorization.ts` (pass-through when no password). `authorized()` compares the credential with `===` (not constant-time) - see the timing-safe recommendation in 04.
- No fail-closed option: `cli/cmd/serve.ts:15-22` prints `Warning: OPENCODE_SERVER_PASSWORD is not set; server is unsecured.` via `console.log` (STDOUT) and proceeds to listen. There is no config key or flag that makes auth mandatory. NOTE: `cli/cmd/web.ts` independently starts a listener and has its own missing-password warning path, so a `serve.ts`-only fix would be incomplete (both must go through a shared startup policy).

## Network binding

- `cli/network.ts` resolves the bind hostname; `--mdns` flips the default from `127.0.0.1` to `0.0.0.0` ONLY when no explicit `--hostname` and no `config.server.hostname` is set. If either is set, mDNS does not override it. The resolved host is passed straight to the Node server (`server/server.ts`, the `NodeHttpServer.layer({ port, host })` construction). `--hostname 0.0.0.0` binds all interfaces with no additional auth requirement (auth still only enforced if a password is set).

## No HTTP request logging

- The HTTP router is constructed with per-request logging disabled (`server/server.ts`: `disableLogger: true`, `disableListenLog: true`). The application log file (`~/.local/share/opencode/log/opencode.log`) is a structured event log, not an access log. There is no native record of inbound requests or source addresses.

## /config secret exposure - CONFIRMED, no redaction

- `handlers/config.ts` returns `configSvc.get()` verbatim; `config/config.ts` returns the merged config `Info` unchanged; the provider schema stores the key as a plain string (`v1/config/provider.ts`: `apiKey: Schema.optional(Schema.String)`). No scrub/redact on the read path (the `omit(...)` calls elsewhere are for building outbound provider request settings, not the `/config` response). The config group is behind the same Authorization middleware, so a set password gates it. Scope: keys supplied via `auth.json`/env (not the config file) do not flow through `/config`; this concerns config-file keys.

## Filesystem read - caller-selected confinement root (NOT traversal)

- `/file/content` resolves the requested path against a base directory and rejects escapes: `handlers/file.ts:96-99` (`path.resolve(directory, ctx.query.path)` then `if (!FSUtil.contains(directory, file)) ... die("Path escapes the location")`). `FSUtil.contains(parent, child)` (`core/src/fs-util.ts:270-274`) returns false for `..`/absolute escapes. So `..` traversal out of the base is blocked - this is NOT a traversal bug.
- The base directory is CALLER-CONTROLLED: workspace routing derives it as `?directory=` OR the `x-opencode-directory` header OR `process.cwd()` (`middleware/workspace-routing.ts:87`). Passing `?directory=/` sets the confinement root to `/`, so `contains("/", "/etc/passwd")` is true and the read proceeds, bounded only by the serving user's OS perms.
- The `list`/`findText`/`findFile` handlers run rooted at the same caller-chosen `directory` and do not apply the `contains` guard. `findSymbol`/`status` were stubbed to `[]` in the reviewed tree (version-specific). The whole `file` group is behind the Authorization middleware (`groups/file.ts:175-177`), so a set password gates these.
- Route-name caveat: the routes confirmed present in the reviewed tree are `/find`, `/find/file`, `/find/symbol`, `/file`, `/file/content`, `/file/status`. The `/api/fs/read|list|find` route names observed on the 1.18.2/1.18.3 binaries were NOT found as separate routes in the reviewed `dev` tree; treat those names as version-dependent - the behavior is the same, the route names may differ by version.

## Permission gate - split by endpoint

- `POST /session/{id}/shell` is effectively UNGATED. The handler calls the shell impl; the impl (`session/prompt.ts` - the `shellImpl` body, roughly `:451-570`, wrapped in `Effect.uninterruptibleMask`) writes the records and spawns via `ChildProcess.make(sh, args, { cwd })` with NO `permission.ask`/`assert` in the path. The thin wrapper is at `session/prompt.ts:1349-1354`; the proof-of-absence is the impl body. The shell runs with `cwd = ctx.directory` (the caller-selected instance directory), i.e. it is not confined to a worktree.
- `POST /session/{id}/message` (agent tool calls) IS gated. The tool path calls `permission.ask({ ... ruleset: merge(agent.permission, session.permission) ... })` (`session/prompt.ts:342-346`); individual tools also assert (e.g. `core/src/tool/bash.ts:132,142`; `tool/shell.ts:270,283`). The default effect when no rule matches is `ask` (`core/src/permission.ts:78-84`), and on `ask` the code BLOCKS on a deferred until answered (`permission.ts:197-217`, `Deferred.await(...)`), rather than auto-proceeding. So a tool call via the message path only runs without a prompt if the effective ruleset resolves to `allow`. This path must NOT be described as categorically ungated.
- Open item for any completeness claim: the `SessionPrompt.command` / config-markdown shell path was only partially traced and should be fully resolved before asserting the command-execution surface is closed.

## Four framing corrections applied during review

The review process (see 05) corrected four points that an earlier draft got wrong; the corrected framing is what appears above and in the report:
1. Filesystem: "caller-selected confinement root," not "no confinement / traversal."
2. Permission: split `/shell` (ungated) from `/message` (gated, blocks on `ask`); do not claim the message path is ungated.
3. `--mdns` -> `0.0.0.0` only when no explicit hostname is set.
4. The fail-open warning is emitted to STDOUT via `console.log`, not stderr.
