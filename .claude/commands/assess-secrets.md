---
description: Scan the working tree and git history for committed secrets/keys/PII/PHI (via tools/scan_secrets.py, read-only, redacted) and propose a rotate-first remediation IPD.
agent: build
---

Read and execute @.agents/workflows/assess/assess.md.

Apply the concern lens @.agents/workflows/assess/lenses/secrets.md on top of that harness: it selects the concern, its lead personas, and its rubric. Assess that single concern deeply and write an IPD into the project's pending-plans directory; do not change code and do not execute the plan.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
