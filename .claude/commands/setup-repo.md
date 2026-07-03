---
description: Guided, wizard-style repo setup for best practices and security: detect state, then ask-before-each-change to install tools and add secret-scanning, .gitignore/CI/pre-commit/hygiene files. Idempotent; stages changes.
argument-hint: "[optional target path or flags]"
---

Read and execute @.agents/workflows/setup-repo/setup-repo.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
