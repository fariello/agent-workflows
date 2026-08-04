---
description: Authoritative execution-and-transition gate for an approved IPD: runs the deterministic `aw ipd lint` at pre-execution, pre-transition, and post-transition and fails closed (exit 1 is a structural finding, exit 2 a hard stop, quarantined/legacy are not conforming). Defines the terminal transaction (workflow-history line, terminal Status, git mv, path-scoped lifecycle commit) as a POST-gate step, never a checklist item, with pre/post-commit recovery. The in-between sibling of plan-review (before building) and verify-execution (after building). Never approves a plan/spec and never tags/releases.
argument-hint: "[optional target path or flags]"
---

Read and execute @.agents/workflows/ipd-lifecycle/ipd-lifecycle.md.

If the user provided arguments, treat them as the target path(s) and/or flags for this workflow: $ARGUMENTS

Treat the referenced file as the controlling instruction and follow it fully.
