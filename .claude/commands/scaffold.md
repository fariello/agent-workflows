---
description: Guided, wizard-style creation of a new assess-* lens, standalone workflow, or command: generate from the existing patterns, wire the manifest, and regenerate shims. Authoring/meta workflow.
argument-hint: "[optional target path or flags]"
---

<!-- Deprecation notice: `/scaffold` is deprecated; prefer `/aw scaffold`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/scaffold/scaffold.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
