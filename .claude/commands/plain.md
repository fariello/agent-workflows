---
description: Rewrite your previous message for a capable engineer who has not seen this work: explain each term, tell a failure as the steps that happened, mark an unverified cause as unverified, keep every fact, and send only the rewrite. Use when the user says the message was unclear or asks for the plain version.
argument-hint: "[treat them as which part of the previous message to rewrite or what was unclear; omit to rewrite the whole previous message]"
---

<!-- Supported alias: `/plain` and `/aw plain` are equivalent; this alias is retained as a supported command. -->

Read and execute @.aw/system/workflows/plain/plain.md.

If the user provided arguments, treat them as which part of the previous message to rewrite or what was unclear; omit to rewrite the whole previous message: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
Reporting: follow `AGENTS.md#aw:reporting` (concise prose; required reports still in full).
