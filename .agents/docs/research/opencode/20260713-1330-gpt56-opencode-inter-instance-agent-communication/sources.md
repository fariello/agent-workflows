<!--
Research baseline: OpenCode v1.17.18, tag commit b1fc811, released 2026-07-09.
Research date: 2026-07-13, America/New_York.
Evidence labels: VERIFIED-SOURCE, DOCUMENTED, OBSERVED-EXTERNAL-REPORT, INFERRED, PROPOSED.
No live OpenCode binary was available in the execution sandbox, so runtime claims are source-derived unless explicitly labeled otherwise.
-->
# Sources and Evidence Index

Access date for all web sources: **2026-07-13**.

## OpenCode release and official documentation

1. **OpenCode releases**, anomalyco/opencode. Latest observed release v1.17.18, commit `b1fc811`, released 2026-07-09.
   https://github.com/anomalyco/opencode/releases/tag/v1.17.18

2. **Server documentation**, OpenCode. TUI/server architecture, host/port, authentication, OpenAPI, session APIs, SSE, and TUI control.
   https://opencode.ai/docs/server/

3. **SDK documentation**, OpenCode. Typed client, server creation, session APIs, prompt behavior, and structured output.
   https://opencode.ai/docs/sdk/

4. **CLI documentation**, OpenCode. `run --attach`, `serve`, `web`, and ACP stdin/stdout nd-JSON behavior.
   https://opencode.ai/docs/cli/

5. **Plugin documentation**, OpenCode. Plugin load paths, SDK client context, events, tools, dependency installation, and examples.
   https://opencode.ai/docs/plugins/

6. **Permissions documentation**, OpenCode. Allow/ask/deny, external directory controls, auto mode, and agent overrides.
   https://opencode.ai/docs/permissions/

7. **Agents documentation**, OpenCode. Primary and subagent model, permissions, and task behavior.
   https://opencode.ai/docs/agents/

8. **IDE documentation**, OpenCode. IDE integration and multiple terminal sessions.
   https://opencode.ai/docs/ide/

## Immutable tagged source, v1.17.18

9. **HTTP server listener**, `packages/opencode/src/server/server.ts`. Node HTTP server, port fallback, mDNS condition, shutdown, WebSocket tracking.
   https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/server.ts

10. **Session API definitions**, `packages/opencode/src/server/routes/instance/httpapi/groups/session.ts`. Session paths, prompt and async prompt descriptions.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/routes/instance/httpapi/groups/session.ts

11. **Session API handlers**, `packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts`. `prompt` and `promptAsync` call paths, status, abort, commands, shell.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/routes/instance/httpapi/handlers/session.ts

12. **Prompt service**, `packages/opencode/src/session/prompt.ts`. User-message construction, `chat.message` hook, `noReply`, run loop, prompt input schema.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/session/prompt.ts

13. **Session run state**, `packages/opencode/src/session/run-state.ts`. Process-local runner map, busy/idle, cancellation, background job cancellation.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/session/run-state.ts

14. **Generic runner**, `packages/opencode/src/effect/runner.ts`. Idle/running/shell states and `ensureRunning` behavior.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/effect/runner.ts

15. **Session status**, `packages/opencode/src/session/status.ts`. In-memory map, missing status defaults to idle, status/idle event publication.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/session/status.ts

16. **Event API definition and handler**, SSE filtering, heartbeat, connected/disposed events.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/routes/instance/httpapi/groups/event.ts
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/routes/instance/httpapi/handlers/event.ts

17. **TUI handlers**, append, submit, clear, select session, command, toast.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/routes/instance/httpapi/handlers/tui.ts

18. **Server authentication**, environment variables and Basic Auth header generation.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/auth.ts

19. **Authorization middleware**, Basic Auth validation and public UI exceptions.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/routes/instance/httpapi/middleware/authorization.ts

20. **mDNS implementation**, Bonjour service naming and publication.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/mdns.ts

21. **Server route composition**, CORS, SSE, PTY WebSockets, API and UI routes.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/server/routes/instance/httpapi/server.ts

22. **Plugin type definitions**, plugin input, `dispose`, events, `chat.message`, tools, permission and shell hooks.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/plugin/src/index.ts

23. **Plugin loader/runtime**, SDK client creation, server URL, event subscription, sequential hook execution, finalizers.
    https://github.com/anomalyco/opencode/blob/v1.17.18/packages/opencode/src/plugin/index.ts

## Upstream issue reports used only as regression warnings

24. **`prompt_async` does not wake idle sessions**, issue report from an earlier release window. Current tagged source differs and explicitly starts the prompt path.
    https://github.com/anomalyco/opencode/issues/21524

25. **API/TUI rendering and event-related reports**, examples showing the need for exact-version integration tests and API reconciliation.
    https://github.com/anomalyco/opencode/issues/11424

26. **Session/subagent API hang report**, useful operational warning for controller timeouts and abort logic.
    https://github.com/anomalyco/opencode/issues/6573

## Evidence limitations

- The research sandbox did not contain an OpenCode executable.
- Network access for shell-based cloning was unavailable, but official pages and immutable raw/tagged source were inspected through web retrieval.
- Linux, macOS, Windows, WSL, tmux, PTY, and two-live-instance experiments were not executed.
- The proposed prototype is architectural scaffolding, not a validated OpenCode integration package.
- Every production claim about a target OpenCode version should be confirmed against that version's runtime `/doc` specification and integration tests.
