---
name: setup-repo
description: Use when the user asks to setup-repo (Guided, idempotent, drift-aware repo setup AND conformance check: detect state, classify each area (conformant/partial/missing/outdated), then ask-before-each-change to install tools and add secret-scanning, the plan/IPD lifecycle (dirs + documented contract), .gitignore/CI/pre-commit/hygiene files. Safe to re-run after updates; stages changes). Do not use for unrelated requests or when no setup-repo action was requested.
semantic-digest: fac485e34c21786995c88292034e1b922d815bbde538d0628bd4859715288275
---

# Skill: setup-repo

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/setup-repo/setup-repo.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `fac485e34c21786995c88292034e1b922d815bbde538d0628bd4859715288275`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/setup-repo/setup-repo.md

## Package resources

- `reference/canonical-body.md` (reference)
