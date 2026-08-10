---
description: Post-execution cross-check: verify an EXECUTED plan (IPD) was actually done as written AND in spirit. Runs a 5-dimension Intent & Spirit Audit (explicit requirements, implicit intent, empirical validation, scope, artifacts) against the real diff, MANDATES re-running the repo's real validation with captured output (no un-run "tests pass" claims), and rates execution fidelity (FIDELITY_EXEMPLARY..DIVERGED) mapped onto the verdict. Always writes a run record and EMITS a corrective IPD for any gap (never fixes in place; commits only its own files path-scoped, safe to run while another agent works). Verdict MATCHES/DIVERGES/INCOMPLETE + GO/NO-GO on "truly executed?". Used to cross-check another agent's or a past session's work.
argument-hint: "[optional target path or flags]"
---

Read and execute @.agents/workflows/verify-execution/verify-execution.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
