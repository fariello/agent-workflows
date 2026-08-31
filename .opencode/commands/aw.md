---
description: Agent Workflows slash-command dispatcher: execute any workflow by verb (`/aw <verb> [args...]`).
agent: build
---

Read the workflow manifest @.aw/system/workflows/index.md.

The first argument names the workflow VERB (e.g. `assess`, `plan-review`, `verify`, `handoff`, `spec`, `whatnext`, `setup-repo`); any remaining arguments are passed through to the resolved workflow. Resolve the verb to its workflow entry in the manifest, then read and execute that workflow's body file. If NO verb was given, consult the manifest or run `/list-workflows` to view available workflows and prompt the user.

If the user provided arguments, treat the first argument as the workflow verb and remaining arguments as its parameters: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
