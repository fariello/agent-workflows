---
description: Guided in-agent tour and router for newcomers: detect repo/toolkit context, explain the mental model briefly, ask the user's goal, and route to the right workflow (offering to run it with consent) with the exact invocation for their tool. Orients and routes; references `/list-workflows` for the full catalog. Read-only by default.
agent: build
---

<!-- Deprecation notice: `/getting-started` is deprecated; prefer `/aw getting-started`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/getting-started/getting-started.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
