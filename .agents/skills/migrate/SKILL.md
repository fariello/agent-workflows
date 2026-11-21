---
name: migrate
description: Use when the user asks to migrate (Assess-and-plan a high-risk migration (framework/DB/dependency-major/layout): inventory the blast radius, name the invariants that must survive, and propose a staged, reversible plan with characterization tests first and per-stage rollback + verify checks. Emits an IPD; does not execute). Do not use for unrelated requests or when no migrate action was requested.
semantic-digest: dc2c18a4217635cd6c314f52ebb7af819c5167e43c1106a9e640d42d52cf7236
---

# Skill: migrate

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/migrate/migrate.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `dc2c18a4217635cd6c314f52ebb7af819c5167e43c1106a9e640d42d52cf7236`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/migrate/migrate.md

## Package resources

- `reference/canonical-body.md` (reference)
