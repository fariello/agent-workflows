---
description: Research prompt producer: turns a research topic into a house-conformant, upload-ready research handoff prompt (a `.prompt.md`) staged in `.aw/records/prompts/pending/`.
agent: build
---

<!-- Deprecation notice: `/research` is deprecated; prefer `/aw research`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/research-prompt/research-prompt.md.

If the user provided arguments, treat them as the research topic and optional scope; omit to be prompted for the topic: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
