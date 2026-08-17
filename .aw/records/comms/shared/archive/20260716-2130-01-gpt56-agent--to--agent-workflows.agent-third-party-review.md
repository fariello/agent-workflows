# Independent Third-Party Security and Patch Review: OpenCode Shared-Host Server and Agent-to-Agent Findings

## 1. Title and review metadata

| Field | Value |
|---|---|
| Review date | 2026-07-16, completed 2026-07-16 21:51 EDT |
| Reviewer | GPT-5.6 Thinking, acting as an independent application-security and code reviewer |
| Primary repository | `https://github.com/anomalyco/opencode` |
| Current stable release reviewed | `v1.18.3` |
| Stable commit | `127bdb30784d508cc556c71a0f32b508a3061517` |
| Default development branch | `dev` |
| Development commit | `08fb47373509ba64b13441061314eeacf4264f51` |
| Stable-to-dev distance at review time | 9 commits, based on the GitHub compare view |
| Supplied runtime versions | v1.18.2, v1.18.3, and a production deployment on v1.18.1 |
| Actual patch implementation reviewed | None supplied or located |
| Patch material reviewed | Three proposed P0 patch sketches plus UX and triple-check reviews |
| Build environment | Linux container, Node.js v22.16.0, TypeScript v5.8.3; Bun and a local OpenCode checkout were unavailable |
| Evidence convention | Source verified, supplied-runtime verified, independently runtime verified, plausible but unverified, disproved, or changed upstream |

This report is the completed execution of the preserved prompt
`20260716-2130-01-gpt56-agent--to--agent-workflows.agent-third-party-review.prompt.md`.

## 2. Executive summary

The central security findings are real. They are not equally applicable to every OpenCode user, and the most important precondition is narrower than some early wording suggested: **an OpenCode HTTP listener must actually be running**. A plain TUI with no listener is not reachable through this attack surface. On a conventional multi-user Linux host where users share a network namespace, however, `127.0.0.1` is host-local rather than user-local. An unprivileged user can reach another user's loopback listener. The supplied two-account campaign on OpenCode v1.18.3 demonstrated port discovery, unauthenticated session and directory disclosure, API-created sessions, direct shell execution as the victim UID, caller-selected filesystem reads within the victim's OS permissions, and password-based blocking of the chain. I independently reproduced the underlying cross-UID loopback reachability premise with two temporary Unix accounts and a synthetic loopback service.

The current stable release and current development head preserve the load-bearing source behavior:

- `opencode serve` starts without authentication when `OPENCODE_SERVER_PASSWORD` is absent and emits only a warning.
- `GET /config` returns the merged configuration object without a public-response redaction boundary.
- `POST /session/:id/shell` reaches `shellImpl()` and spawns a shell without invoking the permission service.
- workspace routing permits the caller to choose the instance directory through the query string or header, which can make `/` the effective root for file APIs.
- mDNS can change the default bind to `0.0.0.0` when no hostname is explicitly configured.
- native HTTP access logging is disabled.

The issues therefore warrant engineering changes even though OpenCode's current security policy declares unauthenticated opt-in server access out of scope and describes the permission system as a UX control rather than a security sandbox. That policy affects disclosure handling, not the technical facts. In particular, returning configured write-only credentials through a general read API and letting the direct shell endpoint bypass the product's own permission UX are independently undesirable design defects.

The proposed patches are not equally mature:

1. **Patch 1, config redaction: Requires redesign.** Omission is safer than a sentinel because a sentinel is written back over the real key by a GET-edit-update round trip. However, a generic name blacklist is not a complete secret boundary. Provider options are extensible and arbitrary headers can carry credentials under names other than `Authorization`. The right design is a dedicated public configuration DTO or schema transformation with write-only secret fields and an explicit sensitive-header policy. A minimal omission patch can reduce exposure quickly, but it must be described as a partial emergency fix and tested against generated SDK schemas.
2. **Patch 2, shell permission gate: Requires redesign and should be split by caller context.** The corrected insertion scope is inside the inner `Effect.gen`, after agent validation and before session records are created. Merely inserting the proposed `permission.ask` is still insufficient. It can hang forever with no responder, it awaits while inside an uninterruptible region, it uses a raw-command `always` pattern unlike the existing shell tool's normalized approval grammar, it does not reuse external-directory checks, and `Effect.orDie` risks turning denials into defects rather than stable HTTP errors. The TUI's everyday `!command` path also uses this endpoint, so a universal prompt would be a visible regression. Remote/headless API shell should fail fast unless a pre-existing allow rule or explicit trusted-automation policy authorizes it; attended TUI shell can use interactive approval.
3. **Patch 3, fail-closed authentication option: Safe to merge after specified changes, but the actual implementation cannot be judged.** `requireAuth` belongs in startup policy, not in `Server.listen` network options. The schema field is mandatory. The same policy must cover `serve`, `web`, TUI-started listeners, attach-related launch paths, and non-loopback binds. An opt-in flag is backward compatible but does not repair the unsafe default for shared-host operators unless launchers enforce it.

No supplied material contains an actual patch branch, commit, diff, or test run for the proposed changes. Consequently, this report does not claim that any implementation builds or passes tests.

## 3. Bottom-line answers to the four central questions

### 3.1 Are the identified issues real, reproducible, and material?

**Yes, with an important scope qualification.**

- Default unauthenticated HTTP access is **Confirmed with narrower scope**: it requires a live listener. It is not established that every plain TUI exposes one, and supplied v1.18.3 testing found no listener for a default plain TUI.
- Cross-user reachability of another user's loopback listener on a shared Linux network namespace is **Confirmed**.
- `/config` secret disclosure is **Confirmed with broader scope** than only provider `apiKey`: the schema includes MCP `clientSecret`, arbitrary provider options, and arbitrary header maps.
- direct `/shell` execution without a permission check is **Confirmed**.
- caller-selected filesystem confinement root is **Confirmed with narrower scope**: the issue is not `..` traversal; it is that the caller selects the base, including `/`, after which normal containment succeeds.
- non-loopback and mDNS exposure is **Confirmed**.
- lack of native HTTP access logging is **Confirmed**.
- plain-string password comparison is **Confirmed**, but practical severity is low compared with the other findings.

The chain is material on HPC login nodes, shared development hosts, shared CI machines, and any remotely reachable server. It is generally negligible as a cross-user issue on a genuinely single-user laptop bound to loopback.

### 3.2 What threat models make them exploitable?

The highest-risk cases are:

1. another unprivileged Unix user on the same host when the victim runs an unsecured listener in the shared network namespace;
2. any routable host when OpenCode binds a listener to `0.0.0.0` or another non-loopback address without authentication;
3. a hosted service that permits ordinary users to launch their own unsecured OpenCode server processes;
4. headless automation that exposes the API and assumes loopback is a per-user trust boundary.

The chain is broken when no listener exists, when a strong password is reliably injected and required, or when per-user network namespaces or equivalent containers make one user's loopback unreachable to another.

### 3.3 Do the proposed patches safely fix the problems?

**Not as a set, as currently sketched.**

- Patch 1 reduces leakage but its blacklist is incomplete and its original sentinel design corrupts secrets on round trip.
- Patch 2 is not safe to merge as sketched after only correcting the insertion scope. It requires a caller-aware policy, shared shell-permission planning, deterministic no-responder behavior, cancellation semantics, and stable error mapping.
- Patch 3's design is sound if implemented as shared startup policy and covered by tests across every listener-starting command. Threading `requireAuth` through `ListenOptions` is the wrong responsibility boundary.

### 3.4 What should maintainers ship, change, reject, defer, or test?

- Ship an emergency public-config response that omits known secrets and sensitive headers, then replace it with a schema-defined public DTO.
- Add shared startup policy that can require authentication and refuses non-loopback unauthenticated binds by default.
- Redesign direct shell authorization so unattended API calls deny unless pre-approved, while attended TUI calls can prompt.
- Add Unix-domain-socket support or per-user isolation for a durable local trust boundary.
- Constrain file APIs to an authorized project/worktree root using canonicalized paths and an explicit symlink policy.
- Add optional or default access logging at a trustworthy gateway or within the server.
- Run the required build, typecheck, SDK generation, route tests, TUI tests, and two-user integration tests before merge.

## 4. Scope, versions, commits, and artifacts reviewed

### 4.1 Repository versions

| Target | Pinned identifier | Review status | Notes |
|---|---|---|---|
| Latest stable | `v1.18.3` / `127bdb30784d508cc556c71a0f32b508a3061517` | Source paths inspected through GitHub; supplied runtime evidence reviewed | Released 2026-07-16 |
| Current development | `dev` / `08fb47373509ba64b13441061314eeacf4264f51` | Load-bearing source paths inspected | Same commit used by the supplied repository agent; current at review time |
| Historical same-user test | v1.18.2 / source references around `70b56a0a9` | Supplied runtime evidence only | Early tests, later corrected in the advisory |
| Production deployment | v1.18.1 | Supplied same-user and launch-path evidence only | Locally hardened deployment, not representative of upstream defaults |

The current `dev` head was nine commits ahead of the stable commit. The compare view did not show a security change that removed the findings, and direct inspection of the load-bearing `dev` files confirmed that the relevant behavior remains.

### 4.2 Uploaded artifacts

| Artifact | SHA-256 | Role in review |
|---|---|---|
| `20260716-0850-01-opencode-unauthenticated-local-server-advisory.md` | `bf3e0e856f1ef7db5d932e433c42f5442c9326b163271bb16f0de98ea4c3e601` | Consolidated advisory and two-account runtime campaign |
| `20260716-0850-02-opencode-shared-host-hardening-howto.md` | `51da5a02bc9fa584e306523f21e06e94fa3312fbb1522e39def039b4edd5e4ca` | Operational mitigation guidance |
| `20260716-1342-01-opencode-cross-user-verification-protocol.md` | `54a72a99a09d819fe57301e663fc67c0cfa7a65bf91929ab502c45c5d2754ffa` | Human verification protocol; contains superseded early assumptions |
| `20260716-1342-02-opencode-cross-user-verification-agent-runbook.md` | `effded3d609f9038ba468b9d106f0f6c182cce66f25da5a96662e861593a3123` | Agent-executable controlled test runbook |
| `20260716-1725-01-opencode-process-listener-session-vulnerability-detection.md` | `1ca3bfaaf8f3d8bb679795136b42ef2a35fbaf86924c9886da75672b76463ea0` | Listener and vulnerability-detection research |
| `20260716-2039-01-opencode.repo-agent--to--agent-workflows.agent-fyi-serve-http-request-logging.md` | `559296bdf5009be57fbe05e801429810b1ad45eaf69d96826aaacfcaff9934b6` | Source review of logging behavior |
| `20260716-2100-01-opencode-db-incident-inspection-checklist.md` | `802d7a30ad889cad2cb9ab8d814b6055e53ba92c40ed00633e443616820afe13` | Forensic limitations and read-only SQLite queries |
| `20260716-2108-01-opencode.repo-agent--to--agent-workflows.agent-reply-validate-security-findings.md` | `e2372eec0804755dbe1343f2c5ba267fd1adc8934c1907d7133d2c105ba7f9c4` | Source validation of five findings |
| `20260716-2108-01-prod-host-mitigation-verified.md` | `35ffac930f46df7b5b19d7dc60d19f38f836652dd93d681a58929f8d798c8b04` | Production mitigation verification |
| `20260716-2114-01-opencode.repo-agent--to--agent-workflows.agent-reply-advisory-review(1).md` | `2d9a283fd1500c4be7b5bfacb1b58d69b935b98c54f521784ff22a9aabbe2221` | Advisory critique and mitigation proposals |
| `20260716-2121-01-opencode.repo-agent--to--agent-workflows.agent-reply-p0-patch-sketches(1).md` | `856424b62c0395dccfa86d9eda65d2ff0b640b2686a7f0144876172fd041bec6` | Proposed P0 patch sketches |
| `20260716-2128-01-opencode.repo-agent--to--agent-workflows.agent-reply-p0-patch-ux-impact(1).md` | `0c6f63191f1d7e534f96b8d25d0eb35c4e42717197de68ce38584c524e880c32` | Compatibility and UX analysis |
| `20260716-2130-01-opencode.repo-agent--to--agent-workflows.agent-reply-p0-patch-triple-check(1).md` | `1aaf58d6f4873d2bd350c29315e4ac3631926b5df8536bd5b330feb8c49a54b6` | Final correction of scope, fields, and type boundary |
| Preserved governing prompt | `f4171a2f5fff9a6eeab951632090d1ed3561d0e51415b7f62884653e756bdccb` | Required review procedure and deliverable contract |

Duplicate uploaded copies had identical hashes and were not counted as separate evidence.

## 5. Missing or unverifiable artifacts

The following were not available and materially limit the patch verdict:

1. no actual patch branch, commit, pull request, or working-tree diff;
2. no line-accurate implementation of the corrected sketches;
3. no CI logs, typecheck output, SDK regeneration output, or test results for a patch;
4. no local clone of stable or `dev` in this execution environment;
5. no OpenCode binary available for an independent end-to-end runtime reproduction here;
6. no confirmed implementation inventory for every TUI, `web`, `attach`, ACP, IDE, or embedded server-starting path;
7. no authoritative maintainer discussion or response to the findings;
8. no proof that the existing OpenAPI schema intentionally promises secret-bearing config round trips;
9. no independent human observation of visibility when an existing attended TUI session is injected;
10. no performance profile of `/config` on realistic large production configuration data.

GitHub source pages were available, but the container could not resolve GitHub for cloning or fetching raw files. Therefore build and test claims are deliberately limited.

## 6. Architecture and attack-surface map

### 6.1 Listener startup and authentication

```text
CLI/TUI/web entry point
  -> resolve network options
     -> hostname, port, mDNS, CORS
  -> read OPENCODE_SERVER_PASSWORD through Flag/ServerAuth configuration
  -> if absent: warn, but continue
  -> Server.listen(...)
     -> Node TCP HTTP listener
     -> route groups
        -> WorkspaceRoutingMiddleware
        -> Authorization middleware
           -> if no configured password: pass through
           -> if configured: require Basic/query token
```

Stable `serve.ts` warns through `console.log` and immediately proceeds to `Server.listen`. The password is therefore optional by default. The current server documentation also tells users to set the environment variable to protect `serve` and `web`, while the security policy states that an unauthenticated opted-in server is expected behavior.

### 6.2 Config disclosure path

```text
GET /config
  -> config route group, behind Authorization when auth is enabled
  -> ConfigHttpApi.get()
  -> configSvc.get()
  -> merged ConfigV1.Info
  -> response serialized without a public/redacted transform
```

The same group is protected when a password is set. The defect is the combination of an open-by-default listener and a response object that includes write-only credentials. Even for authenticated use, least-privilege API design argues against returning those values.

### 6.3 Direct shell path

```text
POST /session/:id/shell
  -> session HTTP handler
  -> SessionPrompt.shell / shellImpl
  -> inner Effect.gen:
       resolve session
       resolve and validate agent
       resolve model
       create user/assistant/tool records marked running
       return message, part, cwd
  -> outer Effect.gen:
       choose configured shell
       construct arguments
       ChildProcess.make(...)
       spawn command with cwd from instance context
       collect output and update records
```

No permission `ask` or assertion occurs in this route-to-spawn path. This differs from the normal agent shell tool, which constructs permission patterns, checks external directories, invokes the permission service, and then spawns.

### 6.4 Filesystem path

```text
request query/header
  -> WorkspaceRoutingMiddleware chooses directory
     query directory OR x-opencode-directory OR process.cwd()
  -> instance context directory
  -> file handlers
     /file/content: resolve path under chosen base and lexical contains check
     /file, /find, /find/file: operate from the same chosen base
```

The containment check is real. The security weakness is that an untrusted caller can choose the containment root. Setting the root to `/` makes any path readable by the victim process fall within that selected root.

### 6.5 Network widening

```text
--hostname explicit value -> passed to listener
--mdns true + no explicit/config hostname -> hostname becomes 0.0.0.0
```

No mandatory-auth coupling is applied to non-loopback binding.

### 6.6 Logging and forensics

The server is built with request/listen logging disabled. Application events and session data exist, but read-only requests such as config, session enumeration, and file reads do not generate a reliable access trail. Shell and message operations may leave database artifacts, but the absence of suspicious rows does not exclude read-only exfiltration.

## 7. Threat model by deployment environment

| Environment | Reachability and prerequisite | Impact if no auth | Practical severity |
|---|---|---|---|
| Single-user laptop, loopback only | Requires listener; attacker is effectively same user or already has local execution | No new cross-user boundary crossed; secrets and shell remain exposed to local processes | Low to Medium, depending on local malware/browser threat model |
| Multi-user Unix host | Other UIDs share loopback namespace and can enumerate/reach ports | Cross-user session disclosure, file reads, and code execution as victim | Critical |
| HPC login node | Same as multi-user host, with valuable SSH keys, tokens, data, schedulers, and shared storage | Lateral execution as victim and credential/data exposure | Critical |
| Shared CI or development host | Any tenant with host networking can reach another listener | Source, build credentials, signing or cloud tokens, and command execution | Critical |
| Per-user network namespace/container | Other tenants cannot reach victim loopback if isolation is correct | Chain blocked at network boundary | Low residual risk |
| `0.0.0.0` or routable bind | Any reachable network peer can connect | Remote unauthenticated API and shell execution | Critical |
| mDNS without explicit loopback hostname | Can silently widen bind to all interfaces | Same as routable bind, plus discoverability | Critical |
| Password-protected listener | Port remains reachable, but routes return 401 without valid credentials | Chain blocked unless password leaks or auth is bypassed | Low to Medium residual risk |
| Reverse proxy with strong auth and logs | Depends on whether backend is separately reachable | Strong mitigation if backend is isolated and credentials are not forwarded insecurely | Low residual risk |
| Headless automation | Listener expected; usually no interactive responder | Direct shell is currently ungated; a naive permission patch can hang indefinitely | High |
| Attended TUI | Depends on whether that TUI actually owns a listener | Direct shell and TUI-control endpoints can affect UX and session integrity | Variable; listener existence must be checked |

## 8. Finding-by-finding verification

### 8.1 Issue A: default unauthenticated local HTTP server

**Verdict: Confirmed with narrower scope.**

**Stable:** Source verified at `v1.18.3`. `serve.ts` warns when the password is missing and still starts the listener. Network defaults are loopback and dynamic port in source, although current public docs list port 4096 and state that a TUI starts a server on a random port. The supplied v1.18.3 plain-TUI test found no listener, creating a documentation/runtime discrepancy that should be resolved.

**Dev:** Source verified at `08fb473...`; the load-bearing behavior remains.

**Runtime:** Supplied two-account testing verified an unsecured `serve` listener was discoverable and reachable by another UID. I independently verified the OS premise by running a synthetic HTTP listener as one temporary UID and fetching it as another temporary UID through `127.0.0.1`.

**Qualification:** “OpenCode is running” is not enough. “An OpenCode listener is running” is the required precondition.

### 8.2 Issue B: secret disclosure through `GET /config`

**Verdict: Confirmed with broader scope.**

The handler returns `configSvc.get()` without a public projection. The provider schema includes `apiKey`, extensible options, model options, and header records. The MCP schema includes OAuth `clientSecret` and remote headers. Keys supplied only through environment variables or separate auth storage may not appear in this object, so the endpoint does not necessarily expose every credential OpenCode uses.

The supplied runtime evidence showed a configured provider key returned in cleartext during a same-user test and showed cross-user readability of the endpoint on a fresh account that happened to contain no key.

Because provider options are extensible, a finite exact-name blacklist cannot prove completeness. Possible secret names include case variants, snake_case names, vendor-specific credentials, `X-Api-Key`, `Proxy-Authorization`, cookies, and custom bearer headers.

### 8.3 Issue C: ungated `POST /session/:id/shell`

**Verdict: Confirmed.**

The route reaches `shellImpl`, creates records, and spawns through `ChildProcess.make` without a permission call. No model invocation is needed for the command itself. Execution is bounded by the OS authority, namespace, container, and resource limits of the OpenCode process, not by a worktree sandbox.

The supplied cross-user campaign created a marker owned by the victim UID and recorded the victim working directory. This is direct evidence of cross-user code execution under the stated listener/no-auth preconditions.

### 8.4 Issue D: caller-selected filesystem confinement root

**Verdict: Confirmed with narrower scope.**

`/file/content` performs a lexical containment check, so the issue should not be described as a naive traversal bypass. Workspace routing accepts a caller-supplied directory, including `/`; with that choice, a path such as `etc/passwd` correctly resolves inside the selected root. The result is arbitrary reading within the server process's OS permissions.

List and search surfaces use the same selected instance directory and need an endpoint-by-endpoint root review. Any future root restriction must canonicalize paths and define symlink behavior. A purely lexical `contains` check can be bypassed by a symlink inside an allowed tree that targets outside it.

### 8.5 Issue E: network escalation through hostname and mDNS

**Verdict: Confirmed.**

Explicit non-loopback hostnames are passed to the listener. mDNS changes the default hostname to `0.0.0.0` when neither CLI nor config explicitly sets a hostname. No password requirement is coupled to this widening. Supplied runtime evidence reached the listener over a LAN address and Docker bridge.

### 8.6 Issue F: logging and forensic visibility

**Verdict: Confirmed.**

Native HTTP request logging is disabled. The application log is not an access log. Session creation, prompts, and shell/tool parts can leave database records, while read-only config, session, and file reads can leave no application-level evidence. Gateway, firewall, eBPF, or reverse-proxy telemetry is required for reliable connection attribution.

### 8.7 Issue G: password comparison

**Verdict: Confirmed.**

The current comparison is ordinary equality rather than a timing-safe comparison. This is correctness hardening and should be fixed, but the practical signal-to-noise ratio of a remote timing attack is likely poor. Severity is Low and should not distract from unauthenticated access, secret disclosure, direct shell execution, and root selection.

### 8.8 Issue H: adjacent command-execution and authorization paths

**Verdict: Partially confirmed.**

The supplied source review identifies `SessionPrompt.command` and `ConfigMarkdown.shell(...)` as another possible shell-capable route. I did not independently complete the entire command-path trace from the GitHub-rendered source in this environment. It must be treated as a merge blocker for a claim that Patch 2 comprehensively gates direct command execution. Maintainers should inventory all `ChildProcess.make`, spawn, exec, shell, slash-command, and plugin execution paths.

### 8.9 Summary table

| Item | Stable | Dev | Runtime reproduced | Severity | Patch status | Regression risk | Recommendation |
|---|---|---|---|---|---|---|---|
| Listener starts without required auth | Confirmed with narrower scope | Confirmed with narrower scope | Supplied runtime; OS premise independently reproduced | Critical on shared/remote hosts | Patch 3: Safe after specified changes | Low if opt-in; medium if default changes | Shared startup policy; refuse unauthenticated non-loopback binds |
| `/config` returns secret-bearing config | Confirmed with broader scope | Confirmed with broader scope | Supplied runtime with configured key | High | Patch 1: Requires redesign | Medium | Public DTO, write-only secrets, omission, header allowlist |
| Direct `/shell` bypasses permission service | Confirmed | Confirmed | Supplied two-account runtime | Critical | Patch 2: Requires redesign; should be split | High | API deny/pre-allow; attended TUI prompt; shared shell planner |
| Caller chooses filesystem base | Confirmed with narrower scope | Confirmed with narrower scope | Supplied runtime | High | No P0 patch supplied | Medium | Authorized canonical project root and symlink-safe resolution |
| `--mdns`/hostname widens exposure | Confirmed | Confirmed | Supplied runtime for `0.0.0.0` | Critical without auth | Partly addressed by Patch 3 | Low | Mandatory auth or refusal for non-loopback |
| No HTTP access log | Confirmed | Confirmed | Supplied black-box and source evidence | Medium | No patch supplied | Low to Medium | Gateway or optional native access log |
| Non-timing-safe compare | Confirmed | Confirmed | Not separately exploited | Low | Small hardening patch | Low | Length-checked timing-safe compare |
| Additional command path bypass | Partially confirmed | Partially confirmed | Not reproduced | High if present | Patch 2 incomplete | High | Complete spawn-path inventory before merge |

## 9. Reproduction matrix

| Test | Preconditions | Expected | Evidence and result | Classification |
|---|---|---|---|---|
| Unsecured `/app` | `serve`, no password | 200 | Supplied v1.18.2/v1.18.3 tests returned 200 | Supplied-runtime verified |
| Password enforcement | password reaches process | 401 without, 200 with valid Basic auth | Supplied same-user and cross-user tests matched | Supplied-runtime verified |
| Cross-UID loopback reachability | two UIDs, shared network namespace, listener on 127.0.0.1 | attacker reaches victim listener | OpenCode campaign reproduced; synthetic Python service independently reproduced | Source and runtime verified premise |
| Port discovery | other UID, `/proc/net/tcp` readable | listener port visible | Supplied OpenCode campaign and independent synthetic test matched | Runtime verified |
| Synthetic config secret | secret in config object | returned by `/config` | Supplied configured-key test matched; source confirms raw return | Source and supplied-runtime verified |
| Session enumeration | unsecured listener | session IDs/directories visible | Supplied T1 matched | Supplied-runtime verified |
| Alternate root file read | `directory=/`, readable file | content returned | Supplied T5 matched; source mechanism confirmed | Source and supplied-runtime verified |
| Direct shell | unsecured listener and session | marker created as victim | Supplied T3 matched | Supplied-runtime verified |
| Plain default TUI listener | default v1.18.3 TUI | early protocol predicted listener | Supplied test found zero listener | Disproved for tested configuration; docs conflict |
| `0.0.0.0` reachability | explicit non-loopback bind | LAN/bridge access | Supplied T5 matched | Supplied-runtime verified |
| mDNS bind | mDNS, no explicit/config hostname | bind becomes 0.0.0.0 | Source verified; not independently runtime tested here | Source verified |
| HTTP access log | DEBUG/print logs | requests logged | Supplied test found no request lines; source disables logger | Source and supplied-runtime verified |
| Sentinel config round trip | GET returns sentinel; full-object update | stored key overwritten | Independently reproduced with equivalent merge semantics | Independently runtime verified |
| Omitted config round trip | GET omits secret; deep merge update | stored key preserved | Independently reproduced | Independently runtime verified |
| TypeScript extra property | variable includes `requireAuth`, passed as `ListenOptions` | may compile | TS 5.8.3 accepted variable; rejected literal | Independently runtime verified |

No OpenCode process was started in this execution environment. The supplied authorized campaign is therefore the only OpenCode-specific runtime evidence, and this report clearly labels it as such.

## 10. Patch dependency register

### 10.1 Patch 1: public config response

| Dependency | Current behavior | Patch concern |
|---|---|---|
| `ConfigHttpApi.get` | Returns `configSvc.get()` | Public boundary must transform the object |
| `ConfigV1.Info` response schema | Represents internal merged configuration | Omitting optional secrets may decode; adding indicator fields may require a new schema |
| Provider schema | `apiKey` plus extensible `options` and headers | Exact-key blacklist cannot cover arbitrary extensions |
| MCP schema | OAuth `clientSecret`; remote headers | Original sketch missed at least `clientSecret` |
| `Config.update` | Deep-merges submitted object into writable existing config | Sentinel values overwrite real credentials |
| `writable()` | Removes `plugin_origins`, not secrets | Does not protect against sentinel clobber |
| SDK/OpenAPI generation | Generated from response schema | Changing shape requires regeneration and compatibility review |
| TUI/CLI consumers | No supplied evidence of reading API keys back | Must still search all generated and third-party clients |
| Serialization | JSON requires acyclic data | Cycle-preserving clone is unnecessary or actively problematic for serialization |

### 10.2 Patch 2: shell authorization

| Dependency | Current behavior | Patch concern |
|---|---|---|
| Session shell route | Calls `shellImpl` | Same route is used by API and TUI shell mode |
| `shellImpl` inner scope | Has session and agent | Correct place for ruleset-aware authorization |
| `shellImpl` outer scope | Has returned cwd and spawn logic | Session and agent no longer in scope |
| `PermissionV1.AskInput` | Requires permission, patterns, always, metadata, sessionID, ruleset | Correct field shape is necessary but not sufficient |
| Permission service | Allow, deny, or deferred ask | Ask can wait indefinitely without a responder |
| Existing shell tool | Parses commands, builds normalized patterns, checks external directories | Proposed raw-command call is behaviorally inconsistent |
| `Effect.uninterruptibleMask` | Wraps shell implementation | Awaiting permission without `restore` may make the wait non-interruptible |
| Session/tool records | Created before spawn | Authorization should happen before records are marked running |
| HTTP error mapping | Needs stable denial/unavailable response | `Effect.orDie` can convert expected denial into a defect |
| TUI `!command` | Uses session shell endpoint according to supplied source review | Universal ask creates visible UX regression |
| Headless clients | May use shell as unattended primitive | Must not hang; needs explicit trusted automation path |
| Slash-command/other spawns | Potential separate execution path | Incomplete coverage can leave a bypass |

### 10.3 Patch 3: require-auth startup policy

| Dependency | Current behavior | Patch concern |
|---|---|---|
| Server config schema | No `requireAuth` field | Schema addition is mandatory |
| CLI network options | Host/port/mDNS/CORS | Auth policy should not become a listen option |
| `Server.listen` | Accepts network/listen concerns | Extra variable properties may compile while violating the abstraction |
| `serve` handler | Reads password flag, warns, starts | Guard must run before listener side effects |
| `web` and TUI launch | May create or attach to servers | Must share the same startup policy |
| Flag/auth configuration | May be initialized once | Policy should use the same authoritative auth source as middleware |
| Config precedence | CLI, global, project, managed config | Managed operators need enforceable precedence |
| Non-loopback bind | Allowed without auth | Startup policy should refuse or require explicit unsafe override |
| Failure helper | Project-specific CLI error handling | Must produce stderr and nonzero exit status |

## 11. Patch 1 detailed review: config secret redaction

### 11.1 Verdict

- **Issue verdict:** Confirmed with broader scope.
- **Patch verdict:** Requires redesign.
- **Emergency mitigation status:** A narrowly scoped omission patch can ship after specified changes, but it must not be presented as complete secret classification.

### 11.2 Correctness of the proposed deep redactor

The revised `WeakMap` approach avoids returning an unredacted original object when a reference is revisited. That is better than a simple `WeakSet`. However, it preserves cycles in the cloned graph. JSON serialization of the result still throws on a cycle. If runtime `ConfigV1.Info` is expected to be JSON serializable, cycles should not be admitted in the first place. If cycles can arise through plugins or arbitrary objects, the HTTP boundary needs explicit cycle handling rather than a clone that remains unserializable.

The generic object walk also has subtle behavior that was not addressed in the sketch:

- getters can execute while enumerating or reading values;
- class instances, dates, maps, sets, proxies, and objects with custom prototypes are flattened or mishandled;
- symbol keys are ignored;
- non-enumerable values are ignored;
- arrays can contain secret-bearing scalar values whose field context is lost;
- non-string credential values are retained;
- a key blacklist is case-sensitive unless normalized;
- a special case only for a property literally named `headers` misses `httpHeaders`, provider-specific header containers, and cookie-like structures.

Most of these do not matter if the config is strictly decoded into plain JSON data. That is another reason to use the schema as the trust boundary rather than a generic recursive JavaScript sanitizer.

### 11.3 Secret coverage

The original set omitted `clientSecret`. Adding `accessToken` and `refreshToken` is prudent, but still does not make a blacklist complete. I independently exercised an equivalent redactor and observed that it retained:

```json
{
  "ApiKey": "LEAK1",
  "api_key": "LEAK2",
  "credential": "LEAK3",
  "token": ["LEAK4"],
  "headers": {"X-Api-Key": "SECRET2"},
  "httpHeaders": {"authorization": "Bearer SECRET3"}
}
```

The schema's extensible provider options mean those are not merely theoretical naming styles. A complete public response should begin from an allowlist of safe fields or from schema annotations that mark write-only/secret fields. Header maps should ideally be excluded or projected through an allowlist of known non-sensitive headers. Blacklisting `Authorization` alone misses `Proxy-Authorization`, cookies, `X-Api-Key`, vendor-specific token headers, and signed headers.

### 11.4 Omit versus sentinel

The sentinel design has a demonstrated correctness bug:

```text
existing apiKey = REAL
GET public config = ***redacted***
client edits unrelated field and PATCHes full object
mergeDeep(existing, submitted) -> apiKey becomes ***redacted***
```

I independently reproduced this semantic behavior. Omitting the key preserved `REAL` under equivalent deep-merge logic.

Therefore:

- do not return a replacement string through a response shape that clients may write back;
- omit optional secret fields from the public response;
- if the UI needs state, return non-secret metadata such as `apiKeyConfigured: true` in a dedicated public DTO;
- do not make update logic silently recognize a magic string unless backward compatibility makes that unavoidable. Magic sentinels become permanent API vocabulary and can collide with a legitimate value.

### 11.5 API contract and generated clients

Casting an omitted object back to `ConfigV1.Info` may satisfy TypeScript but does not create an honest API contract. If the secret fields are optional, runtime decoding may accept omission, but generated clients still believe they receive the internal configuration model. A better contract is:

```text
ConfigV1.Info              internal read/write model
ConfigPublicV1.Info        safe HTTP read model
ConfigPatchV1.Input        write model with optional write-only secrets
```

This separation prevents future secret fields from accidentally becoming readable merely because they were added to the internal schema.

### 11.6 Alternate leakage paths to test

A complete fix must test:

1. `GET /config`;
2. config update responses;
3. config validation and decode errors;
4. provider-list and provider-info endpoints;
5. model/provider options exposed through session or diagnostic APIs;
6. logs and debug dumps;
7. plugin-supplied config extensions;
8. headers nested in arrays or provider-specific structures;
9. OAuth callback/status endpoints;
10. generated OpenAPI examples and snapshots.

The supplied review states that `/config/providers` already uses a public provider projection. That is a useful pattern to reuse.

### 11.7 Performance

The operation is linear in the size of the config and occurs only on config reads. In a synthetic extreme object with 10,000 provider-like entries, an equivalent redactor took about 47.68 ms per run on Node.js v22.16.0. A normal user configuration should be far smaller, so typical cost is likely sub-millisecond to a few milliseconds.

Performance is not the main objection. Correctness, future completeness, and API honesty are. A schema-driven projection is also likely faster because it copies only fields intended for exposure.

### 11.8 Corrected design recommendation

1. Define a public config response schema.
2. Omit all write-only secret fields.
3. Replace header maps with either no headers or an allowlisted public subset.
4. Preserve non-secret fields such as client ID, redirect URI, URLs, callback port, and base URL.
5. Optionally expose boolean configured-state fields.
6. Generate SDKs and update docs.
7. Add round-trip tests proving an unrelated update does not alter stored secrets.
8. Add a schema test that fails when a new field is annotated secret but lacks a public projection rule.

## 12. Patch 2 detailed review: shell permission gate

### 12.1 Verdict

- **Issue verdict:** Confirmed.
- **Patch verdict:** Requires redesign and should be split.
- **Merge recommendation:** Do not merge a single unconditional `permission.ask` into `shellImpl` without resolving caller context, no-responder behavior, cancellation, pattern semantics, error mapping, and bypass coverage.

### 12.2 Exact insertion point and scope

The prior triple-check correctly identified that `session` and `agent` exist only inside the inner `Effect.gen`. Inserting the request near the outer spawn block does not compile because those values are out of scope.

The earliest semantically sound insertion point is inside the inner block:

1. fetch session;
2. resolve and validate agent;
3. compute an authorization plan;
4. authorize or deny;
5. only then create user, assistant, and tool records;
6. return the approved immutable execution plan to the outer spawn block.

Placing authorization after records are created can leave pending or denied shell requests represented as a tool part already marked `running`. Placing it before agent validation prevents constructing the intended ruleset. The proposed “after agent validation, before model resolution” anchor is therefore reasonable, subject to the redesign below.

### 12.3 Request shape

The corrected field names match `PermissionV1.AskInput`:

- `permission`;
- `patterns`;
- `always`;
- `metadata`;
- `sessionID`;
- `ruleset`;
- optional `tool`.

`ShellID.ToolID` is the natural identifier if the endpoint is deliberately treated as the same logical bash/shell permission.

Field-shape correctness does not establish semantic equivalence. The existing shell tool parses commands and creates a list of patterns for the actual commands plus normalized prefix wildcard patterns for remembered approval. The sketch uses the full raw command for both `patterns` and `always`. That creates at least three inconsistencies:

1. remembered approval may apply only to one exact full command, degrading the “always allow” UX;
2. shell parsing and command-chain semantics differ from the normal tool path;
3. external-directory access checks performed by the existing shell tool are not reused.

The safest implementation factors a shared, side-effect-free `ShellPermission.plan()` used by both the tool and direct session-shell endpoint.

### 12.4 Ruleset semantics

The merged agent/session ruleset must be verified against actual precedence. The supplied patch uses `Permission.merge(agent.permission, session.permission ?? [])`, matching an existing message-path idiom. Maintainers still need tests for:

- explicit deny overriding broad allow;
- session overrides versus agent defaults;
- missing-agent fallback permissions;
- persisted remembered rules;
- wildcard normalization;
- path-specific external-directory permissions;
- mutations to a session ruleset while a request is pending.

The execution plan should capture the command, cwd, shell, and ruleset identity used for authorization. The spawned command must be exactly the approved command in exactly the approved directory.

### 12.5 No-responder behavior

The current permission service creates a deferred request and waits until a reply arrives. A bare server may have no client capable of answering. The proposed patch can therefore turn a formerly immediate API into an indefinitely pending request.

That is safer than silent execution but operationally defective. It can retain request state, consume connections, leave partial records if placement is wrong, complicate shutdown, and break automation without a useful error.

**Recommended policy:**

- **Remote/headless API source:** evaluate pre-existing rules. Execute only on explicit allow. Return a deterministic authorization error when the result is ask or deny. Do not create an unanswerable prompt.
- **Attended TUI source:** allow an interactive ask through a registered responder. Apply a bounded timeout or cancellation tied to request/client lifecycle.
- **Trusted automation:** require an explicit configuration or scoped credential that supplies pre-approved rules. Do not use a global “YOLO” default.

A server should know whether an approval responder is registered. If the architecture cannot currently express that, separate endpoints or an explicit request source are preferable to guessing.

### 12.6 Interruptibility and resource behavior

`shellImpl` is wrapped in `Effect.uninterruptibleMask`. Waiting on a permission deferred inside the masked region without applying the provided `restore` function risks making the wait non-interruptible. That could prevent HTTP cancellation or shutdown from cleaning up promptly.

The permission wait should be interruptible and scoped. A conceptual pattern is:

```ts
Effect.uninterruptibleMask((restore) =>
  Effect.gen(function* () {
    // validate immutable execution inputs
    yield* restore(authorize(plan))
    // commit records and spawn after authorization
  }),
)
```

Exact Effect v4 syntax must be validated in the real tree. This report does not claim the pseudocode compiles.

### 12.7 Error mapping

The sketch ends the permission call with `Effect.orDie`. Denial, rejection, timeout, or missing responder are expected authorization outcomes, not defects. At the HTTP boundary they should map to a stable structured response. A direct `403 Forbidden` is appropriate for deny or no pre-approval. A separate conflict or locked response could represent an attended approval that is unavailable, but adding multiple statuses is less important than deterministic behavior and SDK documentation.

### 12.8 TUI compatibility

The supplied source review identifies the TUI `!command` composer as a caller of `sdk.client.session.shell(...)`. Consequently, a universal new prompt affects a normal interactive feature, not only an attacker-facing API.

A user who has explicitly allowed shell in their ruleset should retain immediate execution. A user with `ask` should receive an ordinary TUI approval request. A remote API caller with `ask` but no responder should receive a fast denial. This is why caller context or responder availability must be part of the design.

### 12.9 Completeness and bypasses

Before claiming closure, maintainers must inventory:

- `SessionPrompt.command` and `ConfigMarkdown.shell(...)`;
- all uses of `ChildProcess.make`;
- shell-tool spawn sites;
- slash commands;
- plugin/custom-tool execution;
- LSP/formatter commands exposed through server routes;
- terminal or PTY endpoints;
- legacy v1/v2 route aliases;
- experimental tool endpoints.

Gating only `/session/:id/shell` is worthwhile defense in depth, but it is not a complete command-execution boundary if another route directly spawns from caller-controlled input.

### 12.10 Corrected design recommendation

1. Factor a shared shell authorization planner.
2. Parse the command exactly once and bind authorization to the immutable parsed/raw command and cwd.
3. Reuse external-directory checks and normalized permission patterns.
4. Distinguish attended TUI, authenticated remote API, and trusted automation.
5. For headless API, treat `ask` as deny unless an explicit responder protocol is present.
6. Make waits interruptible and bounded.
7. Authorize before creating running records.
8. Map denial and unavailability to structured HTTP errors.
9. Add integration tests for TUI, API, allow, deny, ask, disconnect, timeout, and shutdown.
10. Audit other spawn paths in the same PR series.

## 13. Patch 3 detailed review: fail-closed authentication option

### 13.1 Verdict

- **Issue verdict:** Confirmed with narrower scope.
- **Patch design verdict:** Safe to merge after specified changes.
- **Actual implementation verdict:** Cannot be judged without the actual implementation.

### 13.2 Schema and responsibility boundary

`server.requireAuth` does not exist in the current server schema. It must be added for a config value to decode and remain available. The field should be startup policy, not a property of the network listener.

The proposed intermediate design put `requireAuth` on the object later passed to `Server.listen`. TypeScript can accept a variable with extra properties when assigning it to a narrower interface even though it rejects the equivalent object literal. I independently reproduced that behavior with TypeScript 5.8.3. Compilation is therefore not enough to validate architectural placement.

Prefer one of these boundaries:

```text
ResolvedNetworkOptions  -> host, port, mDNS, CORS
ResolvedStartupPolicy   -> requireAuth, allowUnsecuredLoopback, allowUnauthenticatedNonLoopback
ResolvedServerStart     -> { network, policy }
```

or read startup policy directly in a shared launcher function. `Server.listen` should receive only values it needs to bind and serve.

### 13.3 Authoritative auth state

The guard should use the same authoritative auth configuration as the middleware, not a parallel test that could drift. It must distinguish absent and empty passwords. Whitespace should be treated deliberately; accepting a one-character or whitespace password may meet “set” semantics but not security expectations. The product can either enforce minimum entropy/length or document that `requireAuth` only requires a non-empty value.

Changing the environment after process startup should not be expected to reconfigure a listener unless the current architecture explicitly supports it.

### 13.4 Coverage of all server-starting paths

A `serve.ts`-only change is incomplete. The shared policy must be invoked by:

- `opencode serve`;
- `opencode web`;
- any TUI path that starts a listener;
- IDE or ACP launch paths that create a listener;
- attach/run modes that fall back to starting a server;
- tests and embedded server constructors used by third parties.

Current public documentation says the TUI starts a server and that the password applies to `serve` and `web`; supplied v1.18.3 runtime evidence found no listener for one plain TUI configuration. The implementation should be driven by actual server creation rather than command names alone.

### 13.5 Guard order and failure behavior

The policy needs resolved configuration and final network binding information, so it should run after config/network resolution but before `Server.listen`, mDNS advertisement, browser launch, or any externally visible side effect.

Expected behavior:

| Case | Result |
|---|---|
| `--require-auth`, password absent/empty | stderr diagnostic, nonzero exit, no listener |
| config `server.requireAuth: true`, password absent/empty | same |
| password present | start normally |
| default false, loopback bind | current behavior may remain for compatibility, with stderr warning |
| non-loopback bind, no password | refuse by default or require an explicit dangerous override |
| config decode error | fail before listener |
| bind failure | ordinary bind error after policy passes |

The unsecured warning belongs on stderr. The project-standard CLI failure helper should be used so scripts receive the normal error formatting and nonzero status.

### 13.6 Backward compatibility

An opt-in `requireAuth` field is additive and low risk. It does not solve the default shared-host exposure unless operators set or enforce it. A stronger default would be:

- loopback: generate a per-instance credential automatically or require explicit `--allow-unsecured` for headless server mode;
- non-loopback: refuse without authentication by default.

That stronger default is a behavior change but is more aligned with secure server products.

### 13.7 Corrected design recommendation

1. Add `requireAuth` to the server config schema and docs.
2. Add `--require-auth` to common server-start options.
3. Resolve startup policy separately from listen options.
4. Use the auth subsystem's authoritative configured state.
5. Invoke one shared guard immediately before any listener is created.
6. Refuse unauthenticated non-loopback binds unless a conspicuous unsafe override is supplied.
7. Cover `serve`, `web`, TUI/IDE server launch, and attach fallbacks.
8. Add CLI tests for exit status, stderr, and absence of a listener.

## 14. Cross-patch interaction review

The patches mitigate different layers and should not be treated as substitutes:

- Authentication blocks unauthenticated callers but does not justify returning secrets to every authenticated API client.
- Config redaction limits disclosure but does not prevent session enumeration, file reads, or shell execution.
- Shell permission policy limits one integrity primitive but does not prevent read-only exfiltration.
- File-root confinement is still needed even after auth because authenticated clients, compromised tokens, proxies, and multi-client deployments should receive least privilege.

Important interactions:

1. **Patch 1 plus Patch 3:** good defense in depth. Config must remain redacted even when auth is enabled.
2. **Patch 2 plus Patch 3:** authenticated shell should still honor a defined execution policy. Authentication establishes identity/credential possession, not authorization to execute any command.
3. **Patch 2 plus TUI:** a shared route means caller-sensitive behavior is required to avoid breaking normal shell mode.
4. **Patch 1 sentinel plus update path:** causes data corruption; omission removes that interaction.
5. **Patch 3 in network options:** leaks policy across abstraction boundaries and risks inconsistent coverage.
6. **Pending permission plus shutdown:** a naive Patch 2 can create an availability regression and prevent clean termination.
7. **File root plus symlinks:** simply changing the base to project root is not sufficient unless canonicalization and symlink policy are included.

## 15. Build, typecheck, lint, and test results

### 15.1 OpenCode repository checks

| Check | Result | Reason |
|---|---|---|
| Repository clone and clean-state confirmation | Not run | No local checkout; container DNS could not resolve GitHub |
| Bun install | Not run | Bun unavailable and no repository |
| Full typecheck | Not run | No patch implementation or repository |
| Lint/format | Not run | No patch implementation or repository |
| Unit tests | Not run | No patch implementation or repository |
| SDK/OpenAPI generation | Not run | No patch implementation or repository |
| Stable binary runtime tests | Not run independently | No OpenCode binary in the environment |
| Dev binary runtime tests | Not run independently | No OpenCode binary/build |

This is a meaningful limitation. Source-level confidence is high for the load-bearing findings, but merge confidence is intentionally lower because no actual diff was built.

### 15.2 Independent focused tests

The following focused tests were run locally:

- sentinel versus omission under equivalent deep-merge update semantics;
- blacklist bypass variants for config redaction;
- cycle serialization after WeakMap cloning;
- synthetic large-config redaction timing;
- TypeScript excess-property behavior for variables versus literals;
- cross-UID reachability of a loopback TCP listener and visibility in `/proc/net/tcp` using two temporary Unix accounts.

All temporary test users, processes, and files created for the loopback test were removed.

## 16. Performance and resource impact

### 16.1 Config redaction

Complexity is O(n) in config object size with O(n) allocation. Normal configurations are unlikely to make this material, but a public projection is more efficient and predictable than generic deep cloning. The synthetic extreme benchmark measured roughly 47.68 ms for a 10,000-provider-like object. This is not representative of normal use and should not be used to claim a production regression.

### 16.2 Shell authorization

Rule evaluation itself should be small relative to process startup. Interactive approval adds human latency by design. The serious resource concern is an indefinite deferred wait in headless mode. Each unresolved request can retain HTTP state, permission entries, and related fibers. A disconnect or server shutdown must interrupt and clean up the request.

### 16.3 Require-auth startup policy

One additional config/policy read at startup is negligible. Dynamic imports can slightly affect cold start, but responsibility clarity is more important. If config is already resolved for network options, a shared resolved-start structure avoids duplicate reads without polluting `ListenOptions`.

### 16.4 Access logging

Native access logging can generate significant volume for streaming/event endpoints. A structured policy should exclude or sample health checks and long-lived event noise, redact query credentials, and retain method, normalized route, status, principal, source address, request ID, and latency. A reverse proxy may be the cleaner operational layer.

## 17. Compatibility and UX impact

### 17.1 Patch 1

Expected normal-user impact is low. Users and support tools can no longer read a secret back through the API, which is desirable. A correct public schema may require generated client updates. Full-object third-party editors must tolerate omitted optional fields. Configured-state booleans can preserve useful UI feedback without revealing values.

### 17.2 Patch 2

This has the highest compatibility risk:

- attended `!command` may begin prompting;
- unattended shell callers may hang under a naive design;
- fire-and-forget clients may need error handling or explicit authorization configuration;
- remembered approval behavior can change if pattern grammar differs;
- scripts may need a trusted automation profile;
- denial errors must be documented in generated clients.

Splitting caller behavior and honoring existing explicit allow rules minimizes disruption.

### 17.3 Patch 3

An opt-in flag/config has low compatibility impact. Moving a warning from stdout to stderr is correct but could affect niche scripts that scrape stdout. A default refusal for non-loopback no-auth binds is a deliberate breaking security improvement and should have clear release notes.

### 17.4 Documentation discrepancy

Current server documentation says a normal `opencode` invocation starts a TUI and a server and randomly assigns a port. Supplied v1.18.3 testing found no listening socket for a plain TUI. The docs, implementation, or test context may distinguish in-process HTTP handling from a TCP listener. Maintainers should state precisely which commands and configurations create a reachable listener.

## 18. Newly discovered or independently emphasized related issues

### 18.1 Generic secret blacklist is structurally incomplete

**Verdict: Confirmed with broader scope.** Provider configuration supports arbitrary option keys and headers. A field-name blacklist cannot be a durable public-data boundary.

### 18.2 Cycle-safe clone is not JSON-safe

**Verdict: Confirmed.** The WeakMap clone can preserve cycles, after which JSON serialization still fails. Either cycles are impossible and the machinery is unnecessary, or cycles are possible and need an explicit serialization policy.

### 18.3 Permission wait inside uninterruptible shell scope

**Verdict: Plausible but unverified against a compiled patch.** The intended insertion is inside an `uninterruptibleMask`; a deferred wait should use restored interruptibility. This is a likely availability/cancellation defect in a naive implementation.

### 18.4 Raw `always` semantics differ from the existing shell tool

**Verdict: Confirmed from source.** The tool normalizes remembered approval patterns; the sketch uses the full raw command. Reusing the tool's planner is safer and more consistent.

### 18.5 `Effect.orDie` is inappropriate for expected authorization outcomes

**Verdict: Plausible but unverified against HTTP error layers.** Denial, rejection, timeout, and missing responder should not be converted to defects. The actual error mapper must be traced in an implementation review.

### 18.6 Symlink handling in a future file-root fix

**Verdict: Plausible and important.** Lexical containment of a canonical-looking path does not prevent following an in-tree symlink to an out-of-tree target. The proposed worktree confinement needs `realpath` or a descriptor-based safe-open strategy and tests for races.

### 18.7 Query-string authentication token

**Verdict: Confirmed as a risky interface choice.** Query credentials can leak through browser history, proxy logs, referrers, diagnostics, and process arguments used to construct requests. Basic authorization headers or a safer local transport should be preferred, and query-token support should be deprecated.

### 18.8 Security-report process risk

The repository security policy explicitly states that AI-generated security reports are not accepted and may trigger a ban. Any disclosure should therefore be authored and submitted by a human who independently understands and verifies the findings. This report is useful as internal analysis and evidence organization, not as text to submit verbatim.

## 19. Severity and prioritization table

| Finding | Affected versions reviewed | Preconditions | C | I | A | Practical severity | Priority |
|---|---|---|---|---|---|---|---|
| Unauthenticated shared-host listener plus direct shell | v1.18.3 and current dev; historical evidence v1.18.2 | Victim runs listener without password; attacker can reach host loopback | High | High | High | Critical on multi-user hosts | P0 |
| Unauthenticated remotely bound listener | v1.18.3 and current dev | Non-loopback bind, no password, network route | High | High | High | Critical | P0 |
| Secret-bearing `/config` response | v1.18.3 and current dev | Reachable endpoint; secret configured in returned config | High | Medium | Low | High | P0 |
| Caller-selected file root | v1.18.3 and current dev | Reachable endpoint; victim can read target | High | Low | Low to Medium | High | P0/P1 |
| mDNS silently widening default bind | v1.18.3 and current dev | mDNS enabled; no explicit/config hostname | High as chain enabler | High as chain enabler | Medium | High to Critical with no auth | P0 |
| Fail-open missing-password behavior | v1.18.3 and current dev | Operator misconfiguration or absent env var | High as chain enabler | High as chain enabler | Medium | High | P0 |
| No HTTP access log | v1.18.3 and current dev | Abuse occurs | High forensic blind spot | Medium | Low | Medium | P1/P2 |
| Query-string credential support | v1.18.3 and current dev | Client uses query token | Medium | Medium | Low | Medium | P1/P2 |
| Plain equality for password | v1.18.3 and current dev | Auth enabled; many precise remote measurements | Low | Low | Low | Low | P2 |
| Naive permission patch indefinite wait | Proposed only | Headless caller; rules evaluate to ask | None | None | High | High regression risk | Merge blocker |

`C`, `I`, and `A` denote confidentiality, integrity, and availability impact. No CVSS score is assigned because the attack vector changes materially between local shared-host and remotely exposed deployments. A local attacker on a multi-user host crosses a real user boundary even though the traffic targets loopback.

## 20. Required changes before merge

### 20.1 Patch 1 blockers

1. Replace sentinel output with omission.
2. Add at least `clientSecret`, access/refresh tokens, and case-normalized handling in the emergency patch.
3. Do not claim the blacklist is complete.
4. Introduce or commit to a dedicated public config schema.
5. Decide an explicit public-header policy, preferably an allowlist.
6. Add GET-edit-update round-trip tests proving secrets remain unchanged.
7. Add generated SDK/OpenAPI compatibility tests.
8. Test update responses, provider endpoints, logs, and errors for alternate leakage.

### 20.2 Patch 2 blockers

1. Use the correct inner scope and authorize before records are marked running.
2. Do not use raw command as an unexamined `always` policy.
3. Reuse the shell tool's command planning and external-directory checks.
4. Define caller context or responder availability.
5. For headless API, fail fast on `ask` unless explicitly pre-authorized.
6. Make interactive waits interruptible, cancellable, and bounded.
7. Map expected permission outcomes to stable HTTP errors, not `orDie` defects.
8. Inventory and gate all alternate direct-spawn paths.
9. Add TUI and headless regression tests.

### 20.3 Patch 3 blockers

1. Add `requireAuth` to the schema.
2. Keep it out of `ListenOptions`.
3. Use shared startup policy invoked by every path that creates a listener.
4. Use the same authoritative auth state as middleware.
5. Run the guard after config/network resolution and before listener/mDNS/browser side effects.
6. Refuse unauthenticated non-loopback binding by default or require an explicit dangerous override.
7. Verify stderr and nonzero exit behavior.

### 20.4 Cross-cutting blockers

- produce an actual diff;
- run format, lint, typecheck, unit tests, integration tests, and SDK generation;
- run stable and dev controlled two-user tests;
- document exact behavior changes;
- resolve the TUI-listener documentation discrepancy.

## 21. Recommended PR grouping and merge order

### PR 1: Public config boundary and secret non-disclosure

Ship first because it has limited UX impact and reduces confidentiality exposure regardless of caller authentication. Include omission, public response schema, configured-state indicators where needed, round-trip tests, and leakage tests.

### PR 2: Shared startup authentication policy

Add `server.requireAuth`, common CLI support, shared pre-listen guard, stderr failure, non-loopback refusal, and tests across `serve`, `web`, TUI/IDE launch, and attach fallback. This can proceed in parallel with PR 1 if both are independently tested.

### PR 3: Direct shell authorization redesign

Keep separate because it affects everyday TUI behavior and headless automation. Include shared shell-permission planning, caller-aware policy, cancellation, error mapping, and broad execution-path inventory.

### PR 4: Filesystem authorization boundary

Bind file APIs to an authorized project/worktree root, canonicalize, define symlink behavior, and test list/find/content consistently.

### PR 5: Transport and audit hardening

Unix-domain socket support, per-user socket permissions, optional peer credentials where supported, access logging, query-token deprecation, and timing-safe comparison.

This order reduces immediate disclosure and exposure without forcing the more complex shell UX decision into the first emergency change.

## 22. Operational mitigations

### 22.1 Immediate operator actions

1. Enforce a strong, randomly generated `OPENCODE_SERVER_PASSWORD` for every listener through the launcher, not user convention.
2. Verify unauthenticated `GET /app` returns 401 after every launch.
3. Bind to `127.0.0.1`; forbid `0.0.0.0`, routable hostnames, and mDNS on shared systems.
4. Prevent ordinary users from bypassing the managed launcher or executing the real binary directly.
5. Kill stale listeners before starting a replacement.
6. Keep any bypass/serve-allowed group empty or tightly controlled and monitor membership.
7. Put authenticated request logging at the reverse proxy or gateway.
8. Rotate provider/API credentials that may have been present in readable config during an exposure window.
9. Inspect `opencode.db` read-only for unfamiliar sessions, prompts, and shell/tool commands, while recognizing that read-only exfiltration leaves no database evidence.
10. Treat every file readable by an exposed process as potentially disclosed if a listener was network reachable and no network logs exist.

### 22.2 Durable isolation

Use per-user network namespaces, per-user containers, or VMs so each user's loopback is actually private. Password authentication is strong mitigation, but it does not remove cross-user reachability or port discovery. A Unix-domain socket in a user-private `0700` directory with `0600` permissions is a strong upstream local transport option.

### 22.3 Assessment of the supplied production deployment

The supplied `opencode.its.uri.aws` note describes two effective controls:

- per-spawn random password injected through the environment;
- a wrapper preventing ordinary users from starting `serve`, `web`, ACP, attach, or arbitrary hostname/port modes, with the real binary restricted.

That deployment appears mitigated against the demonstrated default chain, based on same-user auth checks and launch-path inspection. Cross-user exploitation was correctly not attempted on production. Residual priorities are per-user network isolation, gateway attribution, and monitoring the privileged bypass group.

## 23. Maintainer-ready recommendation

The following is the concise technical recommendation I would give maintainers:

> OpenCode's current stable release and development head allow an opted-in HTTP listener to run without authentication. On a conventional shared Linux host, loopback is not isolated by UID. Supplied controlled testing with two Unix accounts demonstrated that another user could discover an unsecured OpenCode listener, enumerate sessions, select filesystem roots readable by the victim process, and execute `POST /session/:id/shell` as the victim UID. A configured password blocked the tested chain.
>
> Three independent defects should be addressed even if unauthenticated server mode remains an explicit product option: the public config endpoint returns write-only secret-bearing configuration; the direct session-shell path bypasses the product's permission UX; and non-loopback/mDNS binding is not coupled to authentication. The file APIs also accept a caller-selected confinement root.
>
> The submitted patch sketches should not be merged as-is. Config secrets should be omitted through a dedicated public schema rather than replaced with a sentinel or filtered by a finite name blacklist. Direct shell authorization needs separate attended-TUI and headless-API behavior, reuse of the existing shell permission planner, fail-fast handling when no responder exists, cancellation, and stable HTTP errors. `requireAuth` should be shared startup policy, not a network listen option, and must cover every code path that creates a listener.
>
> Immediate safe changes are: public config omission, a shared require-auth/non-loopback guard, and operational documentation. The shell permission change should be reviewed in its own PR because it has meaningful TUI and automation compatibility impact.

Because the repository rejects AI-generated security reports, this recommendation should be rewritten and submitted by a human reviewer who has personally confirmed the evidence. The private GitHub Security Advisory channel is the stated reporting route.

## 24. Residual uncertainties and next verification steps

1. Clone stable and dev in a network-enabled environment and record clean hashes.
2. Locate or create the actual patch implementation.
3. Run repository-prescribed install, format, lint, typecheck, tests, and SDK generation.
4. Diff all relevant files between stable and dev rather than only the load-bearing paths.
5. Trace every command and process-spawn route, especially `SessionPrompt.command`.
6. Verify whether current plain TUI configurations create TCP listeners and reconcile the docs.
7. Test TUI `!command` under allow, deny, ask, disconnect, and shutdown.
8. Test bare `serve` behavior with no permission responder.
9. Verify the exact Effect v4 interruptibility semantics for the proposed insertion.
10. Test public config decoding in generated TypeScript clients after omission.
11. Test provider-specific option/header variants against the final public projection.
12. Test file-root fixes with symlinks, races, bind mounts, case normalization, and deleted/replaced paths.
13. Run a fresh two-user campaign on both v1.18.3 and a built dev binary using only synthetic secrets and harmless `/tmp` markers.
14. Capture gateway/network logs to validate forensic recommendations.
15. Obtain maintainer intent for unauthenticated loopback server mode and define an explicit supported shared-host posture.

## 25. Appendix A: exact commands and environment

### 25.1 Review environment

```text
Review time: 2026-07-16 21:51:42 EDT
Node.js: v22.16.0
TypeScript: 5.8.3
OpenCode checkout: unavailable
Bun: unavailable
```

### 25.2 Artifact integrity

```sh
sha256sum /mnt/data/20260716-*.md | sort
```

Hashes are recorded in Section 4.2.

### 25.3 Independent cross-UID loopback premise test

The test used two temporary Unix accounts and a synthetic Python HTTP service. The essential sequence was equivalent to:

```sh
useradd --create-home ocreview_victim
useradd --create-home ocreview_attacker

# Run a harmless HTTP service as victim on loopback.
runuser -u ocreview_victim -- \
  python3 -m http.server 48761 --bind 127.0.0.1 --directory /tmp/ocreview-www &
SERVER_PID=$!

# Fetch as a distinct UID.
runuser -u ocreview_attacker -- \
  curl -fsS http://127.0.0.1:48761/marker.txt

# Confirm the listener is visible in the shared kernel socket table.
runuser -u ocreview_attacker -- \
  awk '$4 == "0A" { print $2 }' /proc/net/tcp

kill "$SERVER_PID"
userdel --remove ocreview_attacker
userdel --remove ocreview_victim
rm -rf /tmp/ocreview-www
```

Observed result: the attacker UID retrieved the synthetic marker and could see the listening port in `/proc/net/tcp`.

### 25.4 Config round-trip and redactor tests

The focused test implemented equivalent deep-merge and redactor semantics, then checked:

```text
sentinel_roundtrip_apiKey=***redacted***
omit_roundtrip_apiKey=REAL
redactor_variant_output retained ApiKey, api_key, credential,
array-valued token, X-Api-Key, and httpHeaders.authorization
cycle_json=throws TypeError
```

### 25.5 Synthetic redaction benchmark

```text
10,000 provider-like entries
20 redaction runs
Total: 953.55 ms
Mean: 47.68 ms/run
Runtime: Node.js v22.16.0
```

This was an intentionally extreme synthetic input and is not a production estimate.

### 25.6 TypeScript responsibility-boundary test

Equivalent test:

```ts
type ListenOptions = { port: number; hostname: string }
const resolved = { port: 1, hostname: "127.0.0.1", requireAuth: true }
const accepted: ListenOptions = resolved // accepted
const rejected: ListenOptions = {
  port: 1,
  hostname: "127.0.0.1",
  requireAuth: true, // TS2353 on object literal
}
```

Observed result: TypeScript 5.8.3 accepted the variable with the extra property and rejected the object literal, confirming that a successful typecheck would not validate the responsibility boundary.

### 25.7 OpenCode runtime commands represented in supplied evidence

Representative harmless probes included:

```sh
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:PORT/app
curl -s http://127.0.0.1:PORT/session
curl -s http://127.0.0.1:PORT/config
curl -s 'http://127.0.0.1:PORT/file/content?directory=/&path=etc/passwd'

SID=$(curl -s -X POST http://127.0.0.1:PORT/session \
  -H 'Content-Type: application/json' -d '{}' |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')

curl -s -X POST "http://127.0.0.1:PORT/session/$SID/shell" \
  -H 'Content-Type: application/json' \
  -d '{"agent":"build","command":"id > /tmp/aw-verify/marker.txt"}'
```

These commands are documented for controlled local reproduction only. They should not be used against systems or users without explicit authorization.

## 26. Appendix B: source citations by commit

### 26.1 Current stable v1.18.3

- Release: `https://github.com/anomalyco/opencode/releases/tag/v1.18.3`
- Commit: `127bdb30784d508cc556c71a0f32b508a3061517`
- Fail-open startup: `packages/opencode/src/cli/cmd/serve.ts` and `packages/opencode/src/cli/cmd/web.ts`
- Network and mDNS resolution: `packages/opencode/src/cli/network.ts`
- Authentication comparison/config: `packages/opencode/src/server/auth.ts`
- HTTP listener and logging flags: `packages/opencode/src/server/server.ts`
- Config handler: `packages/opencode/src/server/routes/instance/httpapi/handlers/config.ts`
- Shell implementation: `packages/opencode/src/session/prompt.ts`, `shellImpl()`
- Workspace root selection: `packages/opencode/src/server/routes/instance/httpapi/middleware/workspace-routing.ts`
- File handlers: `packages/opencode/src/server/routes/instance/httpapi/handlers/file.ts`

Permalink prefix:

```text
https://github.com/anomalyco/opencode/blob/127bdb30784d508cc556c71a0f32b508a3061517/
```

### 26.2 Current development head

- Commit: `08fb47373509ba64b13441061314eeacf4264f51`
- Compare from stable:
  `https://github.com/anomalyco/opencode/compare/127bdb30784d508cc556c71a0f32b508a3061517...08fb47373509ba64b13441061314eeacf4264f51`
- Server launch paths: `packages/opencode/src/cli/cmd/serve.ts` and `packages/opencode/src/cli/cmd/web.ts`
- Shell route and record/spawn path: `packages/opencode/src/session/prompt.ts`
- Existing shell permission planning: `packages/opencode/src/tool/shell.ts`
- Permission request schema: `packages/schema/src/v1/permission.ts`
- Permission service and deferred behavior: relevant permission service implementation under `packages/opencode/src`
- Provider config schema: `packages/core/src/v1/config/provider.ts`
- MCP config schema: `packages/core/src/v1/config/mcp.ts`
- Server config schema: `packages/core/src/v1/config/server.ts`
- Workspace routing: `packages/opencode/src/server/routes/instance/httpapi/middleware/workspace-routing.ts`
- Server listener/logging: `packages/opencode/src/server/server.ts`

Permalink prefix:

```text
https://github.com/anomalyco/opencode/blob/08fb47373509ba64b13441061314eeacf4264f51/
```

### 26.3 Official documentation and policy

- Server documentation: `https://opencode.ai/docs/server/`
- Security policy: `https://github.com/anomalyco/opencode/security/policy`

The security policy states that server mode without a password is unauthenticated by design, that the permission system is not a sandbox, and that AI-generated reports are not accepted. Those positions are important context but do not alter the source and runtime findings in this report.

## 27. Appendix C: proposed corrected diffs or pseudodiffs

The following are design-level pseudodiffs. They are not compile-tested patches.

### 27.1 Public config response

```diff
--- a/packages/opencode/src/server/routes/instance/httpapi/handlers/config.ts
+++ b/packages/opencode/src/server/routes/instance/httpapi/handlers/config.ts
@@
 const get = Effect.fn("ConfigHttpApi.get")(function* () {
-  return yield* configSvc.get()
+  const internal = yield* configSvc.get()
+  return ConfigPublicV1.fromInternal(internal)
 })
```

Conceptual public projection:

```ts
namespace ConfigPublicV1 {
  export const Info = Schema.Struct({
    // safe ordinary config fields
    provider: Schema.optional(
      Schema.Record({
        key: Schema.String,
        value: ProviderPublicConfig,
      }),
    ),
    mcp: Schema.optional(
      Schema.Record({ key: Schema.String, value: McpPublicConfig }),
    ),
  })

  export function fromInternal(input: ConfigV1.Info): Info {
    return projectSafeFields(input, {
      omitWriteOnly: true,
      headerPolicy: "allowlist",
      configuredIndicators: true,
    })
  }
}
```

Emergency partial variant, if a full DTO cannot ship immediately:

```ts
const SECRET_NAMES = new Set([
  "apikey",
  "api_key",
  "authtoken",
  "access_token",
  "accesstoken",
  "refresh_token",
  "refreshtoken",
  "clientsecret",
  "client_secret",
  "password",
  "secret",
  "token",
  "credential",
  "credentials",
])

// Omit rather than replace. Treat all header maps as sensitive unless a header
// name is explicitly safe. Document this as an emergency reduction, not a
// complete long-term classification mechanism.
```

Required test:

```ts
it("does not overwrite an existing secret on GET-edit-update round trip", async () => {
  await setConfig({ provider: { p: { options: { apiKey: "REAL" } } } })
  const publicConfig = await client.config.get()
  expect(publicConfig.provider?.p.options?.apiKey).toBeUndefined()
  await client.config.patch({ ...publicConfig, theme: "new-theme" })
  expect(await readInternalApiKey()).toBe("REAL")
})
```

### 27.2 Shared shell authorization plan

```ts
type ShellRequestSource = "attended-tui" | "remote-api" | "trusted-automation"

type ShellExecutionPlan = {
  readonly sessionID: string
  readonly agentID: string
  readonly command: string
  readonly cwd: string
  readonly shell: string
  readonly args: readonly string[]
  readonly permission: PermissionV1.AskInput
  readonly source: ShellRequestSource
}

function authorizeShell(plan: ShellExecutionPlan) {
  return Effect.gen(function* () {
    const decision = yield* permission.evaluate(plan.permission)
    if (decision === "allow") return
    if (decision === "deny") return yield* ShellDenied

    if (plan.source === "remote-api") {
      return yield* ShellApprovalUnavailable
    }

    // Attended path only. Tie lifetime to request/client and restore
    // interruptibility around the wait.
    return yield* permission.askInterruptibly(plan.permission)
  })
}
```

Conceptual insertion:

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
+  source: ctx.requestSource,
+})
+yield* restore(authorizeShell(plan))
+
+// Only after authorization succeeds:
 const model = ...
 const msg = ...
 const part = ...
```

HTTP mapping:

```text
explicit deny -> 403
ask with no responder/preapproval -> 403 or documented 409
interactive rejection -> 403
cancellation/disconnect -> request canceled; pending permission removed
```

### 27.3 Shared startup policy

```ts
type ResolvedNetworkOptions = {
  port: number
  hostname: string
  mdns: boolean
  mdnsDomain?: string
  cors: string[]
}

type ResolvedStartupPolicy = {
  requireAuth: boolean
  allowUnauthenticatedNonLoopback: boolean
}

function enforceStartupPolicy(
  network: ResolvedNetworkOptions,
  policy: ResolvedStartupPolicy,
  auth: ServerAuthState,
) {
  return Effect.gen(function* () {
    if (policy.requireAuth && !auth.required) {
      return yield* fail("Refusing to start: server authentication is required")
    }
    if (!isLoopback(network.hostname) && !auth.required && !policy.allowUnauthenticatedNonLoopback) {
      return yield* fail(
        "Refusing to bind a non-loopback address without authentication; " +
        "set OPENCODE_SERVER_PASSWORD or explicitly allow the unsafe bind",
      )
    }
    if (!auth.required) {
      console.error("Warning: OPENCODE_SERVER_PASSWORD is not set; server is unsecured.")
    }
  })
}
```

Shared launch path:

```diff
 const network = yield* resolveNetworkOptions(args)
+const policy = yield* resolveStartupPolicy(args)
+const auth = yield* ServerAuth.current()
+yield* enforceStartupPolicy(network, policy, auth)
 const server = yield* Effect.promise(() => Server.listen(network))
```

### 27.4 File-root authorization

```ts
const requestedRoot = yield* WorkspaceRouting.requestedDirectory(request)
const authorizedRoot = yield* ProjectAuthorization.resolveRoot({
  principal,
  sessionID,
  requestedRoot,
})

const rootReal = yield* fs.realpath(authorizedRoot)
const targetReal = yield* resolveTargetWithoutSymlinkEscape(rootReal, relativePath)
```

Required cases include symlinks to outside the root, parent traversal, absolute paths, deleted/replaced components, bind mounts where relevant, and consistent behavior for content, list, find, grep, symbol, and status endpoints.

---

## Final reviewer conclusion

The reported shared-host and network-exposure issues are technically real under the stated listener precondition and should be addressed. The supplied analysis became materially stronger as it corrected the plain-TUI assumption, separated the message permission path from direct `/shell`, and described the filesystem issue as caller-selected root rather than traversal.

The proposed patch set is not ready to merge as written. Patch 1 needs an honest public schema and omission semantics. Patch 2 needs a caller-aware authorization redesign and broad execution-path audit. Patch 3 is the closest to mergeable but must be implemented as shared startup policy across every listener path. No final implementation has been built or tested in the materials reviewed.
