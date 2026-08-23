---
description: Blameless post-mortem for a production incident: timeline, impact, systemic contributing factors, what went right/wrong, and follow-up actions emitted as IPDs into pending/. Reactive complement to the reliability/logging-audit/intrusion-detection lenses. Repo-scoped and honest about it (operator holds the real monitoring/on-call data).
agent: build
---

<!-- Deprecation notice: `/incident` is deprecated; prefer `/aw incident`. This alias continues to work for now but will eventually be pruned. -->

Read and execute @.aw/system/workflows/incident/incident.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
