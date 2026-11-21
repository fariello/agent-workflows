---
name: release-notes
description: Use when the user asks to release-notes (Release discipline: decide the version bump from the actual changes, draft the changelog and human release notes (prose-style guide; breaking changes prominent), and update CHANGELOG/version files with confirmation. Never publishes, tags, pushes, or deploys. Distinct from release-review Section 9 (which executes a release)). Do not use for unrelated requests or when no release-notes action was requested.
semantic-digest: 437725d08143e98478389d7fdf19840ad7bc4b489a0458258d9a4c3306ac8b2d
---

# Skill: release-notes

This skill is a discovery/dispatch router only. The authoritative workflow semantics, state machine, and evidence contract live in the canonical source and runtime, NOT in this file.

## Canonical behavior

Read and execute @.aw/system/workflows/release-notes/release-notes.md. Treat that file as the controlling instruction and follow it fully.

- Canonical semantic digest: `437725d08143e98478389d7fdf19840ad7bc4b489a0458258d9a4c3306ac8b2d`

## Explicit invocation (works even if this skill is disabled)

    read and execute .aw/system/workflows/release-notes/release-notes.md

## Package resources

- `reference/canonical-body.md` (reference)
