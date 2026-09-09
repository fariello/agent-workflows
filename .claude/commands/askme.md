---
description: Ask the human the decisions that are genuinely theirs, ONE interactive prompt at a time, in plain English with full context and a labelled recommendation, then record each answer in the artifact that raised the question so it survives the session. Sorts open questions into resolve-from-evidence, ask-the-human, and defer-with-an-owner. Composition rules live in GUIDING_PRINCIPLES principle 12 and are referenced, not restated. Non-interactive under a runner: records and defers, never blocks.
argument-hint: "[treat them as the artifact whose open questions to ask about (a path, an id6, or a set id); omit to scan the current session's work]"
---

<!-- Deprecation notice: `/askme` is deprecated; prefer `/aw askme`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/askme/askme.md.

If the user provided arguments, treat them as the artifact whose open questions to ask about (a path, an id6, or a set id); omit to scan the current session's work: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
