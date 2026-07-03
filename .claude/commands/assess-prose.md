---
description: Assess prose quality/style across ALL prose (docs, comments/docstrings, UI strings, error/help/CLI text, commit messages) against the distilled nonfiction style guide - quiet force, no mechanical fingerprints, modifier restraint, no em dashes. IPD by default; supports an optional author-in-the-loop interactive mode.
argument-hint: "[optional target path or flags]"
---

Read and execute @.agents/workflows/assess/assess.md.

Apply the concern lens @.agents/workflows/assess/lenses/prose.md on top of that harness: it selects the concern, its lead personas, and its rubric. Assess that single concern deeply and write an IPD into the project's pending-plans directory; do not change code and do not execute the plan.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
