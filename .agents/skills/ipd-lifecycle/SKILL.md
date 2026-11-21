---
name: ipd-lifecycle
description: Use when the user asks to ipd-lifecycle (Authoritative execution-and-transition gate for an approved IPD: runs the deterministic `aw ipd lint` at pre-execution, pre-transition, and post-transition and fails closed (exit 1 is a structural finding, exit 2 a hard stop, quarantined/legacy are not conforming). Defines the terminal transaction (workflow-history line, terminal Status, git mv, path-scoped lifecycle commit) as a POST-gate step, never a checklist item, with pre/post-commit recovery. The in-between sibling of plan-review (before building) and verify-execution (after building). Never approves a plan/spec and never tags/releases). Do not use for unrelated requests or when no ipd-lifecycle action was requested.
semantic-digest: 240d1f8bbf476ae10cb9dc6db7b5a7c850b05e37885329eca3223773f6abe607
---

# Skill: ipd-lifecycle

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `240d1f8bbf476ae10cb9dc6db7b5a7c850b05e37885329eca3223773f6abe607`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md

## Package resources

- `reference/canonical-body.md` (reference)
