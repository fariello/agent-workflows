---
description: Ask or rewrite one decision question at a time with plain language and all context needed to answer. Accept a current question, conversational instructions such as "that question again", or project records to examine. Wait for answers and record project decisions. Explicitly noninteractive runs preserve unanswered decisions without guessing.
agent: build
---

<!-- Supported alias: `/askme` and `/aw askme` are equivalent; this alias is retained as a supported command. -->

Read and execute @.aw/system/workflows/askme/askme.md.

If the user provided arguments, interpret them as a question, instructions to rewrite the previous question, or a file/record/set to examine; without arguments use the outstanding question in the current conversation, otherwise this session's unanswered project questions: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
