# Concept: filesystem-based inter-project agent communication

Status: concept note (durable). Trial in progress. NOT yet a framework feature.
Related spec: `.agents/docs/specs/20260715-1722-01-agent-comms-convention.md` (the canonical convention; the earlier `-2133-02-` draft it grew from has been removed).

## Problem

Independent coding agents increasingly run in parallel across separate projects (for example, one
agent working in `agent-workflows`, another in a sibling repo, a third under a different tool or
model). They frequently need to hand each other structured work: a question and its answer, a task, a
handoff, a heads-up. Today there is no shared channel between two independent agent sessions:

- A subagent spawned inside one session is a child of that session, not a peer running elsewhere.
- Two separate tool instances (for example two OpenCode sessions) have no built-in agent-to-agent
  message channel. There is no shared bus or "send to session X" primitive available by default.
- Not every agent has an API, an MCP server, or any other formal communication mechanism.

So cross-agent coordination has been ad hoc: a human relays a prompt from one session to another,
and the reply comes back the same way. That works but loses routing (who is it for), threading (what
does it answer), read-state (has it been consumed), and durability (decision-grade reasoning dies in
ephemeral scratch).

## Core thesis: the filesystem is the universal substrate

A shared filesystem is the lowest common denominator that ANY file-capable agent can use, regardless
of runtime, model, or vendor, with no additional infrastructure. Therefore we treat a small,
convention-driven filesystem protocol as the GUARANTEED-UNIVERSAL transport for inter-agent
communication, and treat every richer channel as an optional upgrade layered on top.

Transport hierarchy (universal floor first; upgrades are optional and situational):

1. **Filesystem (universal floor).** Messages are files in a shared directory convention. Works for
   any agent that can read/write files; requires nothing else. This is the standard we are specifying.
2. **Git as transport (durable, cross-machine variant of the filesystem).** Commit/push messages to a
   branch; the other agent pulls. Async, auditable, survives across machines. Same file convention,
   different sync layer.
3. **Formal channels (optional upgrades).** An MCP server, an HTTP/session API, or a message broker,
   for agents that have them. Faster and richer, but not universally available, so never assumed.

The protocol is designed so that an agent lacking every formal channel can still participate fully via
the filesystem, and an agent that has a richer channel can use it without breaking interoperability
with file-only agents.

## Why this belongs (eventually) in agent-workflows

"How independent agents hand each other structured work" is itself an agent workflow. This repository
already governs agent behavior (plan lifecycle, execution contract, verify-execution) and ships those
conventions to installed repos. A portable inter-agent comms convention is a natural sibling. However,
per P6 (KISS / do not over-engineer an unproven abstraction), we are NOT formalizing it into the
framework yet: we capture the concept and a draft spec, run it across a few real exchanges, learn the
real friction, and only then consider an IPD that would make it an installed convention (and perhaps an
`aw comms` helper).

## What is captured now vs. deferred

- Captured now (this note + the draft spec): the problem, the universal-substrate thesis, the transport
  hierarchy, and the concrete v0 file convention to trial.
- Deferred: making it a framework feature (installer scaffolding, tooling, a documented standard that
  ships to downstream repos). That is a future IPD, raised only after the trial proves the shape.

## Provenance

Developed 2026-07-12 in conversation between the maintainer and the agent-workflows agent (opencode,
Opus 4.8) while coordinating a cross-project exchange with a peer agent in a sibling project. First
live trial: that same cross-project exchange, conducted under the draft spec.
